from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class AppTransportConfigTests(unittest.TestCase):
    def test_fastmcp_http_binding_is_configurable_via_environment(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "TAPIR_MCP_HOST": "0.0.0.0",
                    "TAPIR_MCP_PORT": "18791",
                    "TAPIR_MCP_STREAMABLE_HTTP_PATH": "/archicad-mcp",
                },
                clear=False,
            ),
            patch("mcp.server.fastmcp.FastMCP") as fastmcp_cls,
        ):
            import tapir_archicad_mcp.app as app_module

            importlib.reload(app_module)

        _, kwargs = fastmcp_cls.call_args
        self.assertEqual(kwargs["host"], "0.0.0.0")
        self.assertEqual(kwargs["port"], 18791)
        self.assertEqual(kwargs["streamable_http_path"], "/archicad-mcp")


if __name__ == "__main__":
    unittest.main()
