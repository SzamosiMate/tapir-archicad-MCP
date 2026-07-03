import sys
import pytest
import httpx
from unittest.mock import MagicMock

# ==========================================
# SPEED OPTIMIZATION: Mock search_index in sys.modules
# to prevent heavy ML imports (PyTorch/Faiss) from slowing down test startup
# ==========================================
mock_search_index = MagicMock()
mock_search_index.create_or_load_index = lambda: None
mock_search_index.search_tools = lambda query: []
sys.modules["tapir_archicad_mcp.tools.search_index"] = mock_search_index

from tapir_archicad_mcp.server import BearerTokenMiddleware


async def plain_app(scope, receive, send):
    """Minimal ASGI app that always answers 200 OK."""
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/plain")],
        }
    )
    await send({"type": "http.response.body", "body": b"ok"})


def make_client(token: str) -> httpx.AsyncClient:
    app = BearerTokenMiddleware(plain_app, token)
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


@pytest.mark.asyncio
async def test_request_without_token_is_rejected():
    """
    A request without an Authorization header must be answered with 401
    and must never reach the wrapped application.
    """
    async with make_client("secret") as client:
        response = await client.get("/mcp")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.text != "ok"


@pytest.mark.asyncio
async def test_request_with_wrong_token_is_rejected():
    """
    A request with an invalid bearer token must be answered with 401.
    """
    async with make_client("secret") as client:
        response = await client.get("/mcp", headers={"Authorization": "Bearer wrong"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_request_with_valid_token_passes_through():
    """
    A request presenting the configured bearer token must reach the
    wrapped application unchanged.
    """
    async with make_client("secret") as client:
        response = await client.get("/mcp", headers={"Authorization": "Bearer secret"})

    assert response.status_code == 200
    assert response.text == "ok"


# ==========================================
# CLI wiring: --token / TAPIR_MCP_TOKEN
# ==========================================

@pytest.fixture
def mock_run_targets(monkeypatch):
    """
    Mocks mcp.run and uvicorn.run so main() can be exercised without
    starting a real server, and replaces the HTTP app factories with
    a plain sentinel app.
    """
    import tapir_archicad_mcp.server as server_module
    from tapir_archicad_mcp.app import mcp

    mock_mcp_run = MagicMock()
    mock_uvicorn_run = MagicMock()
    monkeypatch.setattr(mcp, "run", mock_mcp_run)
    monkeypatch.setattr(server_module.uvicorn, "run", mock_uvicorn_run)
    monkeypatch.setattr(mcp, "streamable_http_app", lambda: plain_app)
    monkeypatch.setattr(mcp, "sse_app", lambda: plain_app)
    return mock_mcp_run, mock_uvicorn_run


def test_http_transport_with_token_wraps_app(monkeypatch, mock_run_targets):
    """
    With --token and an HTTP transport, main() must serve the app through
    BearerTokenMiddleware via uvicorn instead of the unprotected mcp.run.
    """
    mock_mcp_run, mock_uvicorn_run = mock_run_targets
    monkeypatch.delenv("TAPIR_MCP_TOKEN", raising=False)
    monkeypatch.setattr(
        sys, "argv",
        ["server.py", "--transport", "streamable-http", "--token", "secret"],
    )

    from tapir_archicad_mcp.server import main
    main()

    mock_mcp_run.assert_not_called()
    mock_uvicorn_run.assert_called_once()
    served_app = mock_uvicorn_run.call_args.args[0]
    assert isinstance(served_app, BearerTokenMiddleware)
    assert served_app.token == "secret"


def test_token_env_fallback(monkeypatch, mock_run_targets):
    """
    Without --token, the TAPIR_MCP_TOKEN environment variable must be used.
    """
    mock_mcp_run, mock_uvicorn_run = mock_run_targets
    monkeypatch.setenv("TAPIR_MCP_TOKEN", "env-secret")
    monkeypatch.setattr(sys, "argv", ["server.py", "--transport", "sse"])

    from tapir_archicad_mcp.server import main
    main()

    mock_mcp_run.assert_not_called()
    served_app = mock_uvicorn_run.call_args.args[0]
    assert isinstance(served_app, BearerTokenMiddleware)
    assert served_app.token == "env-secret"


def test_stdio_transport_ignores_token(monkeypatch, mock_run_targets):
    """
    stdio does not go through HTTP, so a configured token must not change
    the default mcp.run code path.
    """
    mock_mcp_run, mock_uvicorn_run = mock_run_targets
    monkeypatch.setattr(sys, "argv", ["server.py", "--token", "secret"])

    from tapir_archicad_mcp.server import main
    main()

    mock_mcp_run.assert_called_once_with(transport="stdio")
    mock_uvicorn_run.assert_not_called()


def test_http_transport_without_token_stays_unwrapped(monkeypatch, mock_run_targets):
    """
    Without a token the behaviour of PR #13 must be unchanged: mcp.run
    serves the HTTP transport directly.
    """
    mock_mcp_run, mock_uvicorn_run = mock_run_targets
    monkeypatch.delenv("TAPIR_MCP_TOKEN", raising=False)
    monkeypatch.setattr(sys, "argv", ["server.py", "--transport", "streamable-http"])

    from tapir_archicad_mcp.server import main
    main()

    mock_mcp_run.assert_called_once_with(transport="streamable-http")
    mock_uvicorn_run.assert_not_called()
