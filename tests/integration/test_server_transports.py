import pytest
import asyncio
import socket
import sys
import httpx
import uvicorn
from unittest.mock import MagicMock

from fastmcp import Client
from mcp import ClientSession
from mcp.client.sse import sse_client
from fastmcp.server.http import create_sse_app

# ==========================================
# SPEED OPTIMIZATION: Mock search_index in sys.modules
# before importing app or mcp to prevent heavy ML imports (PyTorch/Faiss) from slowing down test startup
# ==========================================
mock_search_index = MagicMock()
mock_search_index.create_or_load_index = lambda: None
mock_search_index.search_tools = lambda query: []
sys.modules["tapir_archicad_mcp.tools.search_index"] = mock_search_index

from tapir_archicad_mcp.app import mcp




def get_free_port() -> int:
    """Finds an unused ephemeral port dynamically to prevent TCP port collisions."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(autouse=True)
def mock_heavy_dependencies(monkeypatch):
    """
    Automatically mocks out Archicad connections
    so these tests can run safely on headless runner environments.
    """
    # Mock MultiConn so it doesn't try to scan local OS processes
    fake_multi_conn = MagicMock()
    fake_multi_conn.active = {}
    monkeypatch.setattr("tapir_archicad_mcp.app.MultiConn", lambda: fake_multi_conn)


@pytest.mark.asyncio
async def test_tool_execution_in_memory():
    """
    Tests the application logic (tool discovery and execution) without network overhead.
    """
    async with Client(mcp) as client:
        # Check that tools are registered successfully
        tools = await client.list_tools()
        tool_names = [t.name for t in tools]
        assert "discovery_list_active_archicads" in tool_names

        # Execute a tool (hits our mock_heavy_dependencies fixture)
        result = await client.call_tool("discovery_list_active_archicads")
        assert result.structured_content["result"] == []


@pytest.mark.asyncio
async def test_live_tool_call_over_sse():
    """
    Spins up a real, live Uvicorn SSE server on a local TCP port and uses
    the official mcp client library to establish a session and call
    the 'discovery_list_active_archicads' tool over the network.
    """
    port = get_free_port()

    # Configure Uvicorn to run our SSE app
    if hasattr(mcp, "sse_app"):
        app = mcp.sse_app()
    else:
        from fastmcp.server.http import create_sse_app
        app = create_sse_app(mcp)

    config = uvicorn.Config(app=app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    # Start the real server in the background of our current event loop
    server_task = asyncio.create_task(server.serve())
    # Wait briefly for the server to bind to the socket
    await asyncio.sleep(0.5)

    try:
        # Establish a real connection to the running server using the official MCP client SDK
        url = f"http://127.0.0.1:{port}/sse"
        async with sse_client(url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the MCP connection session
                await session.initialize()

                # Execute 'discovery_list_active_archicads' via the live network
                result = await session.call_tool("discovery_list_active_archicads", arguments={})

                # Verify that we successfully received a response matching our mocked state
                assert result.content == []  # Empty list of content blocks
                assert result.isError is False
    finally:
        # Cleanly signal the Uvicorn server to shutdown and wait for the task to exit
        server.should_exit = True
        await server_task


@pytest.mark.asyncio
async def test_live_streamable_http_server():
    """
    Launches a real, live Uvicorn server on a local TCP port and communicates
    with it using HTTP to prove the network stack is functional.
    """
    port = get_free_port()

    # Configure Uvicorn to run our Streamable HTTP app
    if hasattr(mcp, "streamable_http_app"):
        app = mcp.streamable_http_app()
    else:
        app = mcp.http_app()

    config = uvicorn.Config(app=app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    # Start the real server in the background of our current event loop
    server_task = asyncio.create_task(server.serve())
    # Wait briefly for the server to bind to the socket
    await asyncio.sleep(0.5)

    try:
        # Make a real HTTP network call over local loopback
        async with httpx.AsyncClient() as client:
            path = mcp.settings.streamable_http_path or "/mcp"
            response = await client.post(f"http://127.0.0.1:{port}{path}", json={})
            # A 200, 400, or 406 proves the HTTP connection was successful and reached our FastMCP router
            assert response.status_code in [200, 400, 406]
    finally:
        # Cleanly signal the Uvicorn server to shutdown and wait for the task to exit
        server.should_exit = True
        await server_task


@pytest.mark.asyncio
async def test_live_sse_server():
    """
    Launches a real, live Uvicorn server and establishes an actual Server-Sent Events (SSE)
    stream connection over TCP to prove streaming network capability.
    """
    port = get_free_port()

    # Configure Uvicorn to run our SSE app
    if hasattr(mcp, "sse_app"):
        app = mcp.sse_app()
    else:
        from fastmcp.server.http import create_sse_app
        app = create_sse_app(mcp)

    config = uvicorn.Config(app=app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    # Start the real server in the background of our current event loop
    server_task = asyncio.create_task(server.serve())
    # Wait briefly for the server to bind to the socket
    await asyncio.sleep(0.5)

    try:
        # Connect to the real local HTTP socket
        async with httpx.AsyncClient() as client:
            # We use client.stream() to safely connect to the infinite SSE endpoint
            async with client.stream("GET", f"http://127.0.0.1:{port}/sse") as response:
                assert response.status_code == 200
                assert "text/event-stream" in response.headers.get("content-type", "")
    finally:
        # Cleanly signal the Uvicorn server to shutdown and wait for the task to exit
        server.should_exit = True
        await server_task

