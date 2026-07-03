import sys
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

from tapir_archicad_mcp.tools.custom.functions import archicad_call_tool

GUID = "12345678-1234-1234-1234-123456789012"


def test_generated_read_tool_runs_against_fake(fake_archicad):
    """
    A real generated tool must be executable end-to-end (dispatch, Tapir
    call, result validation) against the fake instead of a live Archicad.
    """
    fake_archicad.on_tapir_command(
        "GetSelectedElements", {"elements": [{"elementId": {"guid": GUID}}]}
    )

    result = archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )

    assert result["elements"] == [{"elementId": {"guid": GUID}}]
    assert fake_archicad.calls[0][0] == "GetSelectedElements"


def test_fake_rejects_unexpected_commands(fake_archicad):
    """
    A command without a canned response must fail loudly so tests never
    silently pass against missing expectations.
    """
    with pytest.raises(Exception, match="GetSelectedElements"):
        archicad_call_tool(
            "elements_get_selected_elements", {"port": fake_archicad.port}
        )


def test_archicad_error_response_surfaces_message(fake_archicad):
    """
    When the fake answers with an Archicad error payload, the dispatcher
    must surface the original Archicad message to the client.
    """
    fake_archicad.on_tapir_command(
        "GetSelectedElements",
        {"error": {"code": 4001, "message": "No open project."}},
    )

    with pytest.raises(ValueError, match="No open project."):
        archicad_call_tool(
            "elements_get_selected_elements", {"port": fake_archicad.port}
        )


def test_unknown_port_is_rejected(fake_archicad):
    """Targeting a port that is not active must fail with a clear error."""
    with pytest.raises(ValueError, match="19999"):
        archicad_call_tool("elements_get_selected_elements", {"port": 19999})
