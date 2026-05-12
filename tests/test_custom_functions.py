from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tapir_archicad_mcp.context import multi_conn_instance
from tapir_archicad_mcp.tools.custom.functions import list_active_archicads


class DiscoveryEarlyExitTests(unittest.TestCase):
    def test_raises_when_tapir_addon_not_responding(self) -> None:
        header = SimpleNamespace(product_info=SimpleNamespace(version=28))
        multi_conn = SimpleNamespace(
            refresh=SimpleNamespace(all_ports=Mock()),
            connect=SimpleNamespace(all=Mock()),
            active={19723: header},
        )

        token = multi_conn_instance.set(multi_conn)
        try:
            with patch(
                "tapir_archicad_mcp.tools.custom.functions.is_header_fully_initialized",
                return_value=False,
            ):
                with self.assertRaises(RuntimeError) as ctx:
                    list_active_archicads()
        finally:
            multi_conn_instance.reset(token)

        self.assertIn("Tapir Add-On", str(ctx.exception))
        self.assertIn("19723", str(ctx.exception))

    def test_returns_empty_list_when_no_connections(self) -> None:
        multi_conn = SimpleNamespace(
            refresh=SimpleNamespace(all_ports=Mock()),
            connect=SimpleNamespace(all=Mock()),
            active={},
        )

        token = multi_conn_instance.set(multi_conn)
        try:
            results = list_active_archicads()
        finally:
            multi_conn_instance.reset(token)

        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
