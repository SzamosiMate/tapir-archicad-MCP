import asyncio
import json
from pathlib import Path
from threading import Event
from unittest.mock import patch

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from multiconn_archicad.errors import APIConnectionError, TapirCommandError

from tapir_archicad_mcp.context import multi_conn_instance
from tapir_archicad_mcp.jobs import JobSettings, JobStore, arguments_preview
from tapir_archicad_mcp.tools.custom.functions import archicad_call_tool, archicad_get_job


@pytest.fixture
def stores():
    created = []

    def create(settings=None, **kwargs):
        store = JobStore(settings, **kwargs)
        created.append(store)
        return store

    yield create
    for store in created:
        store.shutdown()


def blocking(entered, release, result=None, error=None):
    def execute(_handle):
        entered.set()
        if not release.wait(5):
            raise RuntimeError("Test worker was not released.")
        if error is not None:
            raise error
        return result

    return execute


async def wait_entered(event):
    assert await asyncio.to_thread(event.wait, 2)


@pytest.mark.asyncio
async def test_repeated_and_cancelled_polls_register_one_completion_callback(stores):
    store = stores(JobSettings(async_threshold_seconds=0.001))
    entered, release = Event(), Event()
    job = store.submit("A", 19723, {}, blocking(entered, release, result={"done": True}))
    try:
        await wait_entered(entered)
        with patch.object(job.future, "add_done_callback", wraps=job.future.add_done_callback) as register_callback:
            for _ in range(100):
                await store.wait(job)
            cancelled_poll = asyncio.create_task(store.wait(job))
            await asyncio.sleep(0)
            cancelled_poll.cancel()
            with pytest.raises(asyncio.CancelledError):
                await cancelled_poll
            assert register_callback.call_count == 1
            assert store.response(job)["status"] == "running"
            release.set()
            async with asyncio.timeout(2):
                while store.response(job)["status"] == "running":
                    await store.wait(job)
            assert store.response(job)["result"] == {"done": True}
            await asyncio.gather(*(store.wait(job) for _ in range(10)))
            assert register_callback.call_count == 1
    finally:
        release.set()


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [TapirCommandError("Rejected", 7), APIConnectionError("Connection lost")])
async def test_late_error_is_retained_and_communication_outcome_is_explicit(stores, error):
    store = stores(JobSettings(async_threshold_seconds=0.01))
    entered, release = Event(), Event()
    job = store.submit("write", 19723, {}, blocking(entered, release, error=error))
    try:
        await wait_entered(entered)
        await store.wait(job)
        assert store.initial_result(job)["status"] == "running"
        release.set()
        async with asyncio.timeout(2):
            while store.response(job)["status"] == "running":
                await store.wait(job)
        response = store.response(job)
        assert response["status"] == "failed"
        assert response["error"]["type"] == type(error).__name__
        if isinstance(error, APIConnectionError):
            assert "outcome may be unknown" in response["error"]["message"]
        else:
            assert response["error"]["code"] == 7
        with pytest.raises(type(error)):
            store.initial_result(job)
    finally:
        release.set()


@pytest.mark.asyncio
@pytest.mark.parametrize("error_type", [RuntimeError, ValueError])
async def test_unexpected_error_is_logged_but_not_exposed(stores, caplog, error_type):
    store = stores()

    def execute(_):
        raise error_type("private internal detail")

    job = store.submit("write", 19723, {}, execute)
    await store.wait(job)
    assert "private internal detail" not in store.response(job)["error"]["message"]
    assert "private internal detail" in caplog.text


@pytest.mark.asyncio
async def test_abnormal_worker_exit_is_recorded_instead_of_staying_running(stores):
    store = stores()

    def execute(_):
        raise asyncio.CancelledError()

    job = store.submit("write", 19723, {}, execute)
    await store.wait(job)
    response = store.response(job)
    assert response["status"] == "failed"
    assert response["error"]["type"] == "CancelledError"


@pytest.mark.asyncio
async def test_overlapping_same_port_and_admission_limit(stores):
    store = stores(max_workers=2)
    entered_a, entered_b, release = Event(), Event(), Event()
    first = store.submit("A", 19723, {}, blocking(entered_a, release))
    second = store.submit("B", 19723, {}, blocking(entered_b, release))
    try:
        await wait_entered(entered_a)
        await wait_entered(entered_b)
        called = []
        with pytest.raises(ToolError, match="Server busy"):
            store.submit("C", 19723, {}, lambda _: called.append(True))
        assert called == []
        assert [job["command"] for job in store.list_jobs()["jobs"]] == ["B", "A"]
        release.set()
        await asyncio.gather(store.wait(first), store.wait(second))
        third = store.submit("C", 19723, {}, lambda _: {})
        await store.wait(third)
        assert store.response(third)["status"] == "completed"
    finally:
        release.set()


@pytest.mark.asyncio
@pytest.mark.parametrize("cleanup", ["prune", "completion"])
async def test_ttl_starts_at_completion_and_jobs_remain_until_cleanup(stores, cleanup):
    now = [100.0]
    store = stores(JobSettings(job_ttl_seconds=10), clock=lambda: now[0])
    entered, release = Event(), Event()
    job = store.submit("A", 19723, {}, blocking(entered, release))
    try:
        await wait_entered(entered)
        now[0] = 1000
        store.prune()
        assert store.response(store.get(job.handle))["status"] == "running"
        release.set()
        await store.wait(job)
        now[0] = 1009
        store.prune()
        assert store.response(store.get(job.handle))["status"] == "completed"
        now[0] = 1010
        assert store.response(store.get(job.handle))["status"] == "completed"
        assert store.list_jobs()["jobs"][0]["jobHandle"] == job.handle
        if cleanup == "prune":
            store.prune()
        else:
            next_job = store.submit("B", 19723, {}, lambda _: {})
            await store.wait(next_job)
        with pytest.raises(ToolError, match="expired"):
            store.get(job.handle)
    finally:
        release.set()


@pytest.mark.asyncio
@pytest.mark.parametrize("elapsed", [0, 10**9])
async def test_zero_ttl_keeps_jobs_but_capacity_removes_oldest_completion(stores, elapsed):
    now = [1.0]
    store = stores(JobSettings(job_ttl_seconds=0, max_completed_jobs=1), clock=lambda: now[0])
    entered, release = Event(), Event()
    older_submission = store.submit("slow", 19723, {}, blocking(entered, release))
    try:
        await wait_entered(entered)
        earlier_completion = store.submit("fast", 19723, {}, lambda _: {})
        await store.wait(earlier_completion)
        now[0] += elapsed
        assert store.response(store.get(earlier_completion.handle))["status"] == "completed"
        release.set()
        await store.wait(older_submission)
        assert store.response(store.get(older_submission.handle))["status"] == "completed"
        with pytest.raises(ToolError, match="expired"):
            store.get(earlier_completion.handle)
    finally:
        release.set()


def test_preview_is_compact_and_truncated_only_when_needed():
    assert arguments_preview({"port": 19723, "params": {"name": "Ház"}}) == ('{"port":19723,"params":{"name":"Ház"}}')
    boundary = {"name": "x" * 289}
    preview = arguments_preview(boundary)
    assert len(preview) == 300
    assert json.loads(preview) == boundary
    preview = arguments_preview({"params": {"elements": list(range(2000))}})
    assert len(preview) == 300 and preview.endswith("…")
    assert preview.startswith('{"params":{"elements":[0,1,2,3,')


@pytest.mark.asyncio
@pytest.mark.parametrize("result", [None, {"futureField": None, "executionResults": [{"error": "partial"}]}])
async def test_fast_results_are_preserved_and_listed_with_none_normalized(fake_archicad, result):
    fake_archicad.on_tapir_command("GetAddOnVersion", result)
    expected = {} if result is None else result
    assert await archicad_call_tool("app_get_add_on_version", {"port": fake_archicad.port}) == expected
    listed = await archicad_get_job()
    summary = listed["jobs"][0]
    assert summary["status"] == "completed" and "result" not in summary
    assert summary["submittedAt"].endswith("+00:00")
    assert summary["completedAt"] is not None
    assert summary["argumentsPreview"] == '{"port":19723}'
    assert (await archicad_get_job(summary["jobHandle"]))["result"] == expected
    with pytest.raises(ToolError, match="Unknown"):
        await archicad_get_job("job:missing")


@pytest.mark.asyncio
async def test_validation_does_not_admit_a_job(fake_archicad):
    with pytest.raises(ToolError):
        await archicad_call_tool("invented", {"port": 19723})
    with pytest.raises(ToolError):
        await archicad_call_tool("app_get_add_on_version", {"port": 19723, "extra": True})
    assert (await archicad_get_job())["jobs"] == []


@pytest.mark.asyncio
async def test_job_and_pages_remain_until_cleanup_even_after_instance_closes(job_store, job_clock, fake_archicad):
    job_store.settings = JobSettings(job_ttl_seconds=3600)
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": list(range(250))})
    first = await archicad_call_tool("elements_get_selected_elements", {"port": 19723})
    handle = (await archicad_get_job())["jobs"][0]["jobHandle"]
    job_clock.now += 1800
    multi_conn_instance.get().active.clear()
    assert (await archicad_get_job(handle))["result"] == first
    second = await archicad_call_tool(
        "elements_get_selected_elements",
        {"port": 19723, "page_token": first["next_page_token"]},
    )
    assert second["elements"] == list(range(100, 200))
    assert len(job_store.list_jobs()["jobs"]) == 1
    assert len(fake_archicad.calls) == 1
    job_clock.now += 1800
    assert (await archicad_get_job(handle))["result"] == first
    assert (
        await archicad_call_tool(
            "elements_get_selected_elements",
            {"port": 19723, "page_token": first["next_page_token"]},
        )
        == second
    )
    job_store.prune()
    with pytest.raises(ToolError, match="page_token"):
        await archicad_call_tool(
            "elements_get_selected_elements",
            {"port": 19723, "page_token": first["next_page_token"]},
        )
    with pytest.raises(ToolError, match="expired"):
        await archicad_get_job(handle)
    assert len(fake_archicad.calls) == 1


@pytest.mark.asyncio
async def test_capacity_removes_entire_job_and_its_pages(job_store, fake_archicad):
    job_store.settings = JobSettings(max_completed_jobs=1)
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": list(range(150))})
    first = await archicad_call_tool("elements_get_selected_elements", {"port": 19723})
    handle = job_store.list_jobs()["jobs"][0]["jobHandle"]
    await archicad_call_tool("elements_get_selected_elements", {"port": 19723})
    with pytest.raises(ToolError, match="expired"):
        await archicad_get_job(handle)
    with pytest.raises(ToolError, match="page_token"):
        await archicad_call_tool(
            "elements_get_selected_elements",
            {"port": 19723, "page_token": first["next_page_token"]},
        )


@pytest.mark.asyncio
async def test_page_token_cannot_be_used_on_a_different_port(job_store, fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": list(range(150))})
    first = await archicad_call_tool("elements_get_selected_elements", {"port": 19723})
    with pytest.raises(ToolError, match="page_token"):
        await archicad_call_tool(
            "elements_get_selected_elements",
            {"port": 19724, "page_token": first["next_page_token"]},
        )


@pytest.mark.asyncio
async def test_shutdown_stops_admission_and_drains_before_clearing(stores):
    store = stores()
    entered, release = Event(), Event()
    job = store.submit("A", 19723, {}, blocking(entered, release))
    try:
        await wait_entered(entered)
        store.stop_admission()
        with pytest.raises(ToolError, match="shutting down"):
            store.submit("B", 19723, {}, lambda _: {})
        shutdown = asyncio.create_task(asyncio.to_thread(store.shutdown))
        await asyncio.sleep(0)
        assert not shutdown.done()
        assert store.response(store.get(job.handle))["status"] == "running"
        release.set()
        await shutdown
        assert store.list_jobs() == {"jobs": []}
    finally:
        release.set()


def test_bundle_declares_job_tool():
    manifest = json.loads((Path(__file__).parents[2] / "manifest.json").read_text())
    assert "archicad_get_job" in {tool["name"] for tool in manifest["tools"]}
