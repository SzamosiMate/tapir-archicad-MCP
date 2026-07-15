import pytest
from tapir_archicad_mcp.tools.custom.functions import archicad_call_tool


GUID = "12345678-1234-1234-1234-123456789012"


def test_generated_read_tool_dispatches_and_validates(fake_archicad):
    """
    A generated read command (GetSelectedElements) must dispatch to Tapir
    and validate its result into the expected shape.
    """
    fake_archicad.on_tapir_command(
        "GetSelectedElements", {"elements": [{"elementId": {"guid": GUID}}]}
    )

    result = archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )

    assert result["elements"] == [{"elementId": {"guid": GUID}}]
    assert fake_archicad.calls[0][0] == "GetSelectedElements"


def test_generated_create_tool_dispatches_params_and_validates(fake_archicad):
    """
    A generated mutating command (CreateSlabs) must validate its params
    model, forward them to Tapir, and validate the result.
    """
    fake_archicad.on_tapir_command("CreateSlabs", {"elements": []})

    result = archicad_call_tool(
        "elements_create_slabs",
        {"port": fake_archicad.port, "params": {"slabsData": []}},
    )

    assert result == {"elements": []}
    command, parameters = fake_archicad.calls[0]
    assert command == "CreateSlabs"
    assert parameters == {"slabsData": []}


def test_archicad_error_is_surfaced_to_client(fake_archicad):
    """
    When Archicad answers with an error payload, the dispatcher must
    surface the original message instead of a raw validation traceback.
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
