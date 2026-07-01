import sys
import os
import pytest
from unittest.mock import MagicMock

# ==========================================
# SPEED OPTIMIZATION: Mock search_index in sys.modules
# to prevent heavy ML imports (PyTorch/Faiss) from slowing down test startup
# ==========================================
mock_search_index = MagicMock()
mock_search_index.create_or_load_index = lambda: None
mock_search_index.search_tools = lambda query: []
sys.modules["tapir_archicad_mcp.tools.search_index"] = mock_search_index

# Now safely import mcp and main
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


def test_server_defaults_configuration(monkeypatch, mock_server_run):
    """
    Tests that running main() without arguments or environment variables
    resolves mcp.settings to the standard default values.
    """
    # Clear any active environment variables
    monkeypatch.delenv("TAPIR_MCP_HOST", raising=False)
    monkeypatch.delenv("TAPIR_MCP_PORT", raising=False)
    monkeypatch.delenv("TAPIR_MCP_STREAMABLE_HTTP_PATH", raising=False)
    monkeypatch.delenv("TAPIR_MCP_MOUNT_PATH", raising=False)

    # Mock CLI arguments to be empty (just script name)
    monkeypatch.setattr(sys, "argv", ["server.py"])

    # Run main entrypoint
    from tapir_archicad_mcp.server import main
    main()

    # Assert mcp.settings resolved correctly
    assert mcp.settings.host == "127.0.0.1"
    assert mcp.settings.port == 8000
    assert mcp.settings.streamable_http_path == "/mcp"
    assert getattr(mcp.settings, "mount_path", None) == "/"

    # Assert run was called with the default stdio transport
    mock_server_run.assert_called_once_with(transport="stdio")


def test_server_env_fallback_configuration(monkeypatch, mock_server_run):
    """
    Tests that environment variables are correctly picked up and
    resolved into mcp.settings when no CLI overrides are provided.
    """
    monkeypatch.setenv("TAPIR_MCP_HOST", "10.0.0.5")
    monkeypatch.setenv("TAPIR_MCP_PORT", "9999")
    monkeypatch.setenv("TAPIR_MCP_STREAMABLE_HTTP_PATH", "/env-http-path")
    monkeypatch.setenv("TAPIR_MCP_MOUNT_PATH", "/env-sse-path")

    monkeypatch.setattr(sys, "argv", ["server.py", "--transport", "streamable-http"])

    from tapir_archicad_mcp.server import main
    main()

    assert mcp.settings.host == "10.0.0.5"
    assert mcp.settings.port == 9999
    assert mcp.settings.streamable_http_path == "/env-http-path"

    mock_server_run.assert_called_once_with(transport="streamable-http")


def test_server_cli_override_configuration(monkeypatch, mock_server_run):
    """
    Tests that passing CLI flags overrides any existing environment variables
    and resolves correctly in mcp.settings.
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
    assert mcp.settings.host == "192.168.1.100"
    assert mcp.settings.port == 7070
    assert mcp.settings.mount_path == "/cli-sse-path"

    mock_server_run.assert_called_once_with(transport="sse")