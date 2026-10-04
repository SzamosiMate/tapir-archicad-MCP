"""Exercise cancellation and recovery through real MCP transports, without Archicad."""

import asyncio
import json
import socket
import sys
from contextlib import AsyncExitStack, asynccontextmanager
from threading import Event
from types import SimpleNamespace

import httpx2
import pytest
import uvicorn
from mcp import Client, ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from multiconn_archicad.errors import AddOnCommandUnavailable, APIConnectionError, TapirCommandError

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.context import job_store_instance
from tapir_archicad_mcp.jobs import JobSettings, JobStore
from tapir_archicad_mcp.middleware import BearerTokenMiddleware
from tapir_archicad_mcp.tools.tool_registry import register_tool_for_dispatch

COMMAND = "test_job_transport_command"
ARGUMENTS = {"name": COMMAND, "arguments": {"port": 19723}}


def payload(result):
    assert not result.is_error
    return json.loads(result.content[0].text)


async def completed_response(session, handle):
    async with asyncio.timeout(3):
        while True:
            response = payload(await session.call_tool("archicad_get_job", {"job_handle": handle}))
            if response["status"] != "running":
                return response


@pytest.fixture
def worker(monkeypatch):
    entered, release = Event(), Event()
    calls = []

    def execute(conn_header):
        calls.append(conn_header)
        entered.set()
        if not release.wait(10):
            raise RuntimeError("Test worker was not released.")
        return {"dispatchCount": len(calls)}

    register_tool_for_dispatch(execute, name=COMMAND, title="Test", description="Test-only blocking command")
    fake = SimpleNamespace(active={19723: object()}, open_port_headers={})
    monkeypatch.setattr("tapir_archicad_mcp.app.MultiConn", lambda: fake)
    monkeypatch.setattr("tapir_archicad_mcp.app.job_settings", JobSettings(async_threshold_seconds=0.5))
    yield entered, release, calls
    release.set()


@asynccontextmanager
async def live_server(transport, token=None):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    app = mcp.sse_app() if transport == "sse" else mcp.streamable_http_app()
    if token:
        app = BearerTokenMiddleware(app, token)
    server = uvicorn.Server(uvicorn.Config(app=app, host="127.0.0.1", port=port, log_level="error"))
    task = asyncio.create_task(server.serve())
    try:
        async with asyncio.timeout(5):
            while not server.started:
                if task.done():
                    await task
                    raise RuntimeError("Server exited before startup")
                await asyncio.sleep(0.01)
        endpoint = "/sse" if transport == "sse" else "/mcp"
        yield f"http://127.0.0.1:{port}{endpoint}"
    finally:
        server.should_exit = True
        await task


@asynccontextmanager
async def connect_session(url, transport, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with AsyncExitStack() as stack:
        if transport == "sse":
            connection = sse_client(url, headers=headers)
        else:
            client = await stack.enter_async_context(httpx2.AsyncClient(headers=headers))
            connection = streamable_http_client(url, http_client=client)
        streams = await stack.enter_async_context(connection)
        session = await stack.enter_async_context(ClientSession(streams[0], streams[1]))
        await session.initialize()
        yield session


@asynccontextmanager
async def live_session(transport):
    async with live_server(transport) as url, connect_session(url, transport) as session:
        yield session


async def exercise_recovery(session, admitted, release):
    request = asyncio.create_task(session.call_tool("archicad_call_tool", arguments=ARGUMENTS))
    try:
        await admitted()
        assert not request.done(), "The initial response must be lost before promotion"
        request.cancel()
        with pytest.raises(asyncio.CancelledError):
            await request
        jobs = payload(await session.call_tool("archicad_get_job", {}))["jobs"]
        assert len(jobs) == 1 and jobs[0]["status"] == "running"
        assert jobs[0]["command"] == COMMAND
        assert jobs[0]["argumentsPreview"] == '{"port":19723}'
        handle = jobs[0]["jobHandle"]
        poll = asyncio.create_task(session.call_tool("archicad_get_job", {"job_handle": handle}))
        await asyncio.sleep(0.02)
        assert not poll.done()
        poll.cancel()
        with pytest.raises(asyncio.CancelledError):
            await poll
        await release()
        completed = await completed_response(session, handle)
        assert completed == {"jobHandle": handle, "status": "completed", "result": {"dispatchCount": 1}}
        assert payload(await session.call_tool("archicad_get_job", {"job_handle": handle})) == completed
        # A subsequent fast execution still returns the raw result and is listed.
        assert payload(await session.call_tool("archicad_call_tool", arguments=ARGUMENTS)) == {"dispatchCount": 2}
        assert len(payload(await session.call_tool("archicad_get_job", {}))["jobs"]) == 2
    finally:
        request.cancel()
        await release()


@pytest.mark.asyncio
@pytest.mark.parametrize("transport", ["sse", "streamable-http"])
async def test_cancelled_execution_and_poll_recover_over_http(worker, transport):
    entered, release_event, calls = worker

    async def admitted():
        assert await asyncio.to_thread(entered.wait, 3)

    async def release():
        release_event.set()

    async with live_session(transport) as session:
        await exercise_recovery(session, admitted, release)
    assert len(calls) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("transport", ["sse", "streamable-http"])
@pytest.mark.parametrize("token", [None, "test-secret"])
async def test_jobs_survive_other_clients_and_reconnect_with_no_clients(worker, monkeypatch, transport, token):
    entered, release, calls = worker
    monkeypatch.setattr("tapir_archicad_mcp.app.job_settings", JobSettings(async_threshold_seconds=0.01))
    async with live_server(transport, token) as url:
        try:
            async with connect_session(url, transport, token) as first:
                promoted = payload(await first.call_tool("archicad_call_tool", ARGUMENTS))
                handle = promoted["jobHandle"]
                assert entered.is_set()
                async with connect_session(url, transport, token) as second:
                    try:
                        for session in (first, second):
                            jobs = payload(await session.call_tool("archicad_get_job", {}))["jobs"]
                            assert [job["jobHandle"] for job in jobs] == [handle]
                            assert jobs[0]["status"] == "running"
                    except BaseException:
                        release.set()
                        raise
                assert payload(await first.call_tool("archicad_get_job", {}))["jobs"][0]["jobHandle"] == handle
            # Finish while the application has no connected clients.
            release.set()
            async with connect_session(url, transport, token) as reconnected:
                assert await completed_response(reconnected, handle) == {
                    "jobHandle": handle,
                    "status": "completed",
                    "result": {"dispatchCount": 1},
                }
        finally:
            release.set()
    assert len(calls) == 1
    with pytest.raises(LookupError):
        job_store_instance.get()


@pytest.mark.asyncio
@pytest.mark.parametrize("transport", ["sse", "streamable-http"])
async def test_expected_job_errors_reach_http_clients(worker, monkeypatch, transport):
    _, release, calls = worker
    now = [1.0]
    monkeypatch.setattr(
        "tapir_archicad_mcp.app.job_settings", JobSettings(async_threshold_seconds=0.01, job_ttl_seconds=1)
    )
    monkeypatch.setattr(
        "tapir_archicad_mcp.app.JobStore",
        lambda settings: JobStore(settings, max_workers=1, clock=lambda: now[0]),
    )
    async with live_session(transport) as session:
        try:
            for name, arguments, expected in [
                ("archicad_get_job", {"job_handle": "job:missing"}, "archicad_get_job()"),
                ("archicad_get_command_schema", {"command_name": "invented"}, "archicad_list_commands"),
                ("archicad_call_tool", {"name": "invented", "arguments": {"port": 19723}}, "not found in registry"),
                (
                    "archicad_call_tool",
                    {"name": COMMAND, "arguments": {"port": 19723, "extra": True}},
                    "Invalid arguments",
                ),
                (
                    "archicad_call_tool",
                    {
                        "name": "elements_get_selected_elements",
                        "arguments": {"port": 19723, "page_token": "forged"},
                    },
                    "Invalid or expired page_token",
                ),
            ]:
                error = await session.call_tool(name, arguments)
                assert error.is_error and expected in error.content[0].text
            promoted = payload(await session.call_tool("archicad_call_tool", ARGUMENTS))
            busy = await session.call_tool("archicad_call_tool", ARGUMENTS)
            assert busy.is_error and "Server busy" in busy.content[0].text
            release.set()
            handle = promoted["jobHandle"]
            await completed_response(session, handle)
            now[0] += 1
            job_store_instance.get().prune()
            expired = await session.call_tool("archicad_get_job", {"job_handle": handle})
            assert expired.is_error and "Unknown or expired job_handle" in expired.content[0].text
        finally:
            release.set()
    assert len(calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error,expected",
    [
        (AddOnCommandUnavailable("Unknown Add-On command."), "upgrade Tapir"),
        (APIConnectionError("Connection lost"), "Connection lost"),
        (TapirCommandError("Rejected", 7), "Rejected"),
        (RuntimeError("private internal detail"), "Error executing tool archicad_call_tool"),
        (ValueError("private internal detail"), "Error executing tool archicad_call_tool"),
    ],
)
async def test_immediate_errors_expose_expected_messages_and_hide_unexpected_details(worker, error, expected):
    def execute(conn_header):
        raise error

    register_tool_for_dispatch(execute, name=COMMAND, title="Test", description="Test-only failing command")
    async with Client(mcp) as client:
        result = await client.call_tool("archicad_call_tool", ARGUMENTS)
        assert result.is_error and expected in result.content[0].text
        assert "private internal detail" not in result.content[0].text
        jobs = payload(await client.call_tool("archicad_get_job", {}))["jobs"]
        failed = payload(await client.call_tool("archicad_get_job", {"job_handle": jobs[0]["jobHandle"]}))
        assert failed["status"] == "failed"
        assert "private internal detail" not in failed["error"]["message"]
        if isinstance(error, APIConnectionError):
            assert "outcome may be unknown" in failed["error"]["message"]
        if isinstance(error, TapirCommandError):
            assert failed["error"]["code"] == 7


@pytest.mark.asyncio
async def test_slow_promotion_and_concurrent_polls_dispatch_once_through_mcp_client(worker, monkeypatch):
    entered, release, calls = worker
    monkeypatch.setattr("tapir_archicad_mcp.app.job_settings", JobSettings(async_threshold_seconds=0.01))
    async with Client(mcp) as client:
        try:
            promoted = payload(await client.call_tool("archicad_call_tool", arguments=ARGUMENTS))
            assert promoted["status"] == "running"
            assert entered.is_set()
            release.set()
            handle = promoted["jobHandle"]
            first, second = await asyncio.gather(completed_response(client, handle), completed_response(client, handle))
            assert first == second == {"jobHandle": handle, "status": "completed", "result": {"dispatchCount": 1}}
        finally:
            release.set()
    assert len(calls) == 1


STDIO_SERVER = """
from threading import Event
from types import SimpleNamespace
import tapir_archicad_mcp.model_configuration
import tapir_archicad_mcp.app as app
from tapir_archicad_mcp.jobs import JobSettings
from tapir_archicad_mcp.tools.tool_registry import register_tool_for_dispatch

release = Event()
calls = []
def execute(conn_header):
    calls.append(conn_header)
    if not release.wait(10):
        raise RuntimeError("Test worker was not released")
    return {"dispatchCount": len(calls)}

register_tool_for_dispatch(execute, name="test_job_transport_command", title="Test", description="Test")
app.MultiConn = lambda: SimpleNamespace(active={19723: object()}, open_port_headers={})
app.job_settings = JobSettings(async_threshold_seconds=2)
@app.mcp.tool(name="test_release_worker")
async def release_worker() -> dict:
    release.set()
    return {}
app.mcp.run(transport="stdio")
"""


@pytest.mark.asyncio
async def test_cancelled_execution_and_poll_recover_over_stdio():
    parameters = StdioServerParameters(command=sys.executable, args=["-c", STDIO_SERVER])
    async with (
        stdio_client(parameters) as streams,
        ClientSession(streams[0], streams[1]) as session,
    ):
        await session.initialize()

        async def admitted():
            async with asyncio.timeout(1.5):
                while not payload(await session.call_tool("archicad_get_job", {}))["jobs"]:
                    await asyncio.sleep(0.01)

        async def release():
            await session.call_tool("test_release_worker", {})

        await exercise_recovery(session, admitted, release)
