from __future__ import annotations

import os
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import tapir_archicad_mcp.server as server_module


class ServerTransportTests(unittest.TestCase):
    def test_main_runs_streamable_http_transport_without_leaking_cli_port_to_multiconn(self) -> None:
        fake_run = Mock()
        fake_app_module = types.ModuleType("tapir_archicad_mcp.app")
        fake_app_module.mcp = SimpleNamespace(run=fake_run)

        original_argv = list(sys.argv)
        try:
            sys.argv = ["server.py", "--transport", "streamable-http", "--port", "18892"]
            with (
                patch.object(
                    server_module,
                    "parse_args",
                    return_value=SimpleNamespace(
                        transport="streamable-http",
                        host="127.0.0.1",
                        port=18892,
                        streamable_http_path="/mcp",
                        mount_path=None,
                    ),
                ),
                patch.dict(sys.modules, {"tapir_archicad_mcp.app": fake_app_module}),
            ):
                server_module.main()
        finally:
            sys.argv = original_argv

        self.assertEqual(os.environ["TAPIR_MCP_HOST"], "127.0.0.1")
        self.assertEqual(os.environ["TAPIR_MCP_PORT"], "18892")
        self.assertEqual(os.environ["TAPIR_MCP_STREAMABLE_HTTP_PATH"], "/mcp")
        self.assertEqual(sys.argv, [original_argv[0]])
        fake_run.assert_called_once_with(transport="streamable-http", mount_path=None)

    def test_main_runs_stdio_transport(self) -> None:
        fake_run = Mock()
        fake_app_module = types.ModuleType("tapir_archicad_mcp.app")
        fake_app_module.mcp = SimpleNamespace(run=fake_run)

        with (
            patch.object(
                server_module,
                "parse_args",
                return_value=SimpleNamespace(
                    transport="stdio",
                    host="127.0.0.1",
                    port=8000,
                    streamable_http_path="/mcp",
                    mount_path=None,
                ),
            ),
            patch.dict(sys.modules, {"tapir_archicad_mcp.app": fake_app_module}),
        ):
            server_module.main()

        fake_run.assert_called_once_with(transport="stdio", mount_path=None)


if __name__ == "__main__":
    unittest.main()
