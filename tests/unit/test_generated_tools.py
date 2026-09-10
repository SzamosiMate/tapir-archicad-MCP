import pytest
from tapir_archicad_mcp.tools.custom.functions import archicad_call_tool


GUID = "12345678-1234-1234-1234-123456789012"


def test_generated_read_tool_dispatches_and_preserves_raw_result(fake_archicad):
    """
    A generated read command (GetSelectedElements) must dispatch to Tapir
    and return Archicad's result without response-schema validation.
    """
    fake_archicad.on_tapir_command(
        "GetSelectedElements",
        {
            "elements": [{"elementId": {"guid": GUID}}],
            "futureField": {"value": None},
        },
    )

    result = archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )

    assert result["elements"] == [{"elementId": {"guid": GUID}}]
    assert result["futureField"] == {"value": None}
    assert fake_archicad.calls[0][0] == "GetSelectedElements"

    next_page = archicad_call_tool(
        "elements_get_selected_elements",
        {"port": fake_archicad.port, "page_token": "MQ=="},
    )

    assert next_page["elements"] == []
    assert len(fake_archicad.calls) == 1


def test_generated_create_tool_dispatches_params_and_preserves_raw_result(fake_archicad):
    """
    A generated mutating command (CreateSlabs) must validate its params
    model and forward them to Tapir without validating the result.
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


def test_nested_command_parameter_extras_are_rejected_before_transport(fake_archicad):
    with pytest.raises(ValueError, match="Invalid arguments provided"):
        archicad_call_tool(
            "elements_create_slabs",
            {
                "port": fake_archicad.port,
                "params": {"slabsData": [], "inventedField": True},
            },
        )

    assert fake_archicad.calls == []


def test_raw_archicad_error_payload_is_preserved(fake_archicad):
    """
    A fake transport can return an error-shaped payload directly. The MCP
    preserves it; the real Multiconn transport raises command-level errors
    before this point.
    """
    fake_archicad.on_tapir_command(
        "GetSelectedElements",
        {"error": {"code": 4001, "message": "No open project."}},
    )

    result = archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )

    assert result == {"error": {"code": 4001, "message": "No open project."}}


def test_unknown_port_is_rejected(fake_archicad):
    """Targeting a port that is not active must fail with a clear error."""
    with pytest.raises(ValueError, match="19999"):
        archicad_call_tool("elements_get_selected_elements", {"port": 19999})

    assert fake_archicad.calls == []


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("app_get_add_on_version", {"port": 19723, "unexpected": True}),
        ("elements_create_slabs", {"port": 19723, "slabsData": []}),
        ("elements_create_slabs", {"port": 19723}),
        ("app_get_add_on_version", {"port": 19723, "params": {}}),
        ("app_get_add_on_version", {"port": 19723, "page_token": "next"}),
        ("app_get_add_on_version", {"port": True}),
        ("app_get_add_on_version", {"port": 19722}),
        ("app_get_add_on_version", {"port": 19744}),
    ],
)
def test_invalid_command_envelopes_are_rejected_before_transport(fake_archicad, name, arguments):
    with pytest.raises(ValueError, match="Invalid arguments provided"):
        archicad_call_tool(name, arguments)

    assert fake_archicad.calls == []


def test_port_string_is_coerced_and_dispatched(fake_archicad):
    fake_archicad.on_tapir_command("GetAddOnVersion", {"version": "1.0.0"})

    result = archicad_call_tool(
        "app_get_add_on_version", {"port": str(fake_archicad.port)}
    )

    assert result == {"version": "1.0.0"}
    assert fake_archicad.calls[0][0] == "GetAddOnVersion"


def test_inactive_in_range_port_is_rejected_before_transport(fake_archicad):
    with pytest.raises(ValueError, match="19724.*not an active Archicad connection"):
        archicad_call_tool("app_get_add_on_version", {"port": 19724})

    assert fake_archicad.calls == []


def test_aliased_parameter_is_sent_under_its_api_name(fake_archicad):
    """
    Parameters whose name collides with a pydantic BaseModel member are
    generated as '<name>_' with an alias. The request must go out under the
    alias, otherwise Archicad rejects the unknown field (see issue #27).
    """
    fake_archicad.on_tapir_command("MoveElements", {"executionResults": []})

    archicad_call_tool(
        "elements_move_elements",
        {
            "port": fake_archicad.port,
            "params": {
                "elementsWithMoveVectors": [
                    {
                        "elementId": {"guid": GUID},
                        "moveVector": {"x": 1.0, "y": 0.0, "z": 0.0},
                        "copy": True,
                    }
                ]
            },
        },
    )

    _, parameters = fake_archicad.calls[0]
    moved = parameters["elementsWithMoveVectors"][0]
    assert "copy" in moved, f"expected the alias 'copy' in the payload, got {sorted(moved)}"
    assert "copy_" not in moved
    assert moved["copy"] is True
