import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

# ==========================================
# SPEED OPTIMIZATION: Mock search_index in sys.modules
# before any test imports app or mcp, to prevent heavy ML imports
# (PyTorch/Faiss) from slowing down test startup
# ==========================================
mock_search_index = MagicMock()
mock_search_index.create_or_load_index = lambda: None
mock_search_index.search_tools = lambda query: []
sys.modules["tapir_archicad_mcp.tools.search_index"] = mock_search_index

from multiconn_archicad.basic_types import Port

from tapir_archicad_mcp.context import multi_conn_instance


class FakeArchicad:
    """
    In-memory stand-in for a running Archicad instance with the Tapir
    Add-On. Generated tools talk to it through the same
    'core.post_tapir_command' interface as a live connection, so they can
    be tested end-to-end (dispatch, Tapir call, result validation) on
    machines without Archicad.
    """

    def __init__(self, port: int = 19723):
        self.port = port
        self.calls: list[tuple[str, dict | None]] = []
        self._canned_responses: dict[str, dict] = {}
        self.core = SimpleNamespace(post_tapir_command=self._post_tapir_command)

    def on_tapir_command(self, command: str, response: dict) -> None:
        """Registers the canned response returned for a Tapir command."""
        self._canned_responses[command] = response

    def _post_tapir_command(self, command: str, parameters: dict | None = None) -> dict:
        self.calls.append((command, parameters))
        if command not in self._canned_responses:
            raise RuntimeError(
                f"FakeArchicad received unexpected Tapir command '{command}'. "
                f"Register a response with on_tapir_command() first."
            )
        return self._canned_responses[command]


@pytest.fixture
def fake_archicad():
    """
    Provides a FakeArchicad wired into the multi_conn_instance ContextVar
    and ensures all generated tools are registered for dispatch.
    """
    from tapir_archicad_mcp.tools.registration import register_all_tools

    register_all_tools()

    fake = FakeArchicad()
    multi_conn = SimpleNamespace(
        refresh=SimpleNamespace(all_ports=Mock()),
        connect=SimpleNamespace(all=Mock()),
        active={Port(fake.port): fake},
    )

    token = multi_conn_instance.set(multi_conn)
    yield fake
    multi_conn_instance.reset(token)
