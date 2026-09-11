import sys
import pytest
from unittest.mock import MagicMock
from tapir_archicad_mcp.app import mcp


@pytest.fixture(autouse=True)
def mock_server_run(monkeypatch):
    """
    Mocks mcp.run to prevent the server from actually running
    and blocking during CLI configuration tests.
    """
    mock_run = MagicMock()
    monkeypatch.setattr(mcp, "run", mock_run)
    return mock_run


def _clear_http_env(monkeypatch):
    """Removes every TAPIR_MCP_* override so defaults apply."""
    for name in (
        "TAPIR_MCP_HOST",
        "TAPIR_MCP_PORT",
        "TAPIR_MCP_STREAMABLE_HTTP_PATH",
        "TAPIR_MCP_MOUNT_PATH",
        "TAPIR_MCP_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)


def test_server_defaults_configuration(monkeypatch, mock_server_run):
    """
    Running main() without arguments or environment variables resolves to the
    stdio transport, which takes no host/port options.
    """
    _clear_http_env(monkeypatch)

    # Mock CLI arguments to be empty (just script name)
    monkeypatch.setattr(sys, "argv", ["server.py"])

    # Run main entrypoint
    from tapir_archicad_mcp.server import main
    main()

    mock_server_run.assert_called_once_with(transport="stdio")


def test_http_transport_defaults_configuration(monkeypatch, mock_server_run):
    """
    Without overrides, an HTTP transport binds the documented defaults and
    serves streamable-http on /mcp.
    """
    _clear_http_env(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["server.py", "--transport", "streamable-http"])

    from tapir_archicad_mcp.server import main
    main()

    mock_server_run.assert_called_once_with(
        transport="streamable-http", host="127.0.0.1", port=8000, streamable_http_path="/mcp"
    )


def test_server_env_fallback_configuration(monkeypatch, mock_server_run):
    """
    Tests that environment variables are correctly picked up and forwarded to
    the transport when no CLI overrides are provided.
    """
    monkeypatch.setenv("TAPIR_MCP_HOST", "10.0.0.5")
    monkeypatch.setenv("TAPIR_MCP_PORT", "9999")
    monkeypatch.setenv("TAPIR_MCP_STREAMABLE_HTTP_PATH", "/env-http-path")
    monkeypatch.setenv("TAPIR_MCP_MOUNT_PATH", "/env-sse-path")

    monkeypatch.setattr(sys, "argv", ["server.py", "--transport", "streamable-http"])

    from tapir_archicad_mcp.server import main
    main()

    mock_server_run.assert_called_once_with(
        transport="streamable-http", host="10.0.0.5", port=9999, streamable_http_path="/env-http-path"
    )


def test_server_cli_override_configuration(monkeypatch, mock_server_run):
    """
    Tests that passing CLI flags overrides any existing environment variables
    and resolves correctly on the transport call.
    """
    # Set environment variables that should be overridden
    monkeypatch.setenv("TAPIR_MCP_HOST", "10.0.0.5")
    monkeypatch.setenv("TAPIR_MCP_PORT", "9999")

    # Pass different values via command line flags
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "server.py",
            "--transport",
            "sse",
            "--host",
            "192.168.1.100",
            "--port",
            "7070",
            "--mount-path",
            "/cli-sse-path"
        ]
    )

    from tapir_archicad_mcp.server import main
    main()

    # Assert CLI overrides took precedence over ENVs
    mock_server_run.assert_called_once_with(
        transport="sse", host="192.168.1.100", port=7070, sse_path="/cli-sse-path"
    )