import pytest
import asyncio
import socket
import sys
import httpx
import uvicorn
from unittest.mock import MagicMock

# ==========================================
# SPEED OPTIMIZATION: Mock search_index in sys.modules
# before importing app or mcp to prevent heavy ML imports (PyTorch/Faiss) from slowing down test startup
# ==========================================
mock_search_index = MagicMock()
mock_search_index.create_or_load_index = lambda: None
mock_search_index.search_tools = lambda query: []
sys.modules["tapir_archicad_mcp.tools.search_index"] = mock_search_index

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.server import BearerTokenMiddleware


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
    fake_multi_conn = MagicMock()
    fake_multi_conn.active = {}
    monkeypatch.setattr("tapir_archicad_mcp.app.MultiConn", lambda: fake_multi_conn)


@pytest.mark.asyncio
async def test_live_sse_server_enforces_token():
    """
    Launches a real Uvicorn server with BearerTokenMiddleware and verifies
    that requests are rejected without the token and accepted with it.

    Uses the SSE app because the streamable-http session manager can only
    be started once per FastMCP instance across the test session.
    """
    port = get_free_port()
    token = "integration-secret"

    if hasattr(mcp, "sse_app"):
        app = mcp.sse_app()
    else:
        from fastmcp.server.http import create_sse_app
        app = create_sse_app(mcp)

    config = uvicorn.Config(
        app=BearerTokenMiddleware(app, token),
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    server_task = asyncio.create_task(server.serve())
    await asyncio.sleep(0.5)

    try:
        async with httpx.AsyncClient() as client:
            url = f"http://127.0.0.1:{port}/sse"

            # Without a token the middleware must block the request
            response = await client.get(url)
            assert response.status_code == 401
            assert response.headers.get("www-authenticate") == "Bearer"

            # With the token the request must reach the SSE endpoint
            async with client.stream(
                "GET", url, headers={"Authorization": f"Bearer {token}"}
            ) as response:
                assert response.status_code == 200
                assert "text/event-stream" in response.headers.get("content-type", "")
    finally:
        server.should_exit = True
        await server_task
