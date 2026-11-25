import pytest
from mcp.server.mcpserver.exceptions import ToolError
from payloads import archicad_call_tool

from tapir_archicad_mcp.result_reading import ReadSelection
from tapir_archicad_mcp.tools.custom.result_tools import result_read

GUID = "12345678-1234-1234-1234-123456789012"
pytestmark = pytest.mark.asyncio


def _elements(count: int, prefix: str = "element") -> list[dict]:
    return [{"elementId": {"guid": f"{prefix}-{index:03d}"}} for index in range(count)]


async def test_generated_read_tool_dispatches_and_preserves_raw_result(fake_archicad):
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

    result = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}, resultMode="inline"
    )

    assert result["elements"] == [{"elementId": {"guid": GUID}}]
    assert result["futureField"] == {"value": None}
    assert fake_archicad.calls[0][0] == "GetSelectedElements"


@pytest.mark.parametrize(
    ("name", "command", "params", "response"),
    [
        (
            "attributes_create_attribute_folders",
            "CreateAttributeFolders",
            {"attributeFolders": [{"attributeType": "MEPSystem", "path": ["Services"]}]},
            {"executionResults": [{"success": True}]},
        ),
        (
            "attributes_move_attributes_and_folders",
            "MoveAttributesAndFolders",
            {"attributeIds": [{"attributeId": {"guid": GUID}}], "targetFolder": {"attributeType": "Layer", "path": []}},
            {"attributeExecutionResults": [{"success": True}], "folderExecutionResults": []},
        ),
    ],
)
async def test_attribute_folder_tools_use_tapir_contracts(fake_archicad, name, command, params, response):
    fake_archicad.on_tapir_command(command, response)

    result = await archicad_call_tool(name, {"port": fake_archicad.port, "params": params}, resultMode="inline")

    assert result == response
    assert fake_archicad.calls == [(command, params)]


@pytest.mark.parametrize(
    ("name", "command", "params"),
    [
        (
            "attributes_delete_attributes",
            "DeleteAttributes",
            {"attributesToDelete": [{"attributeType": "Layer", "attributeId": {"attributeId": {"guid": GUID}}}]},
        ),
        (
            "attributes_delete_attribute_folders",
            "DeleteAttributeFolders",
            {"attributeFolders": [{"attributeType": "Layer", "path": ["Unused"]}]},
        ),
        (
            "navigator_delete_navigator_items",
            "DeleteNavigatorItems",
            {"navigatorItemIds": [{"navigatorItemId": {"guid": GUID}}]},
        ),
    ],
)
async def test_deletion_tools_dispatch_dry_run_to_tapir(fake_archicad, name, command, params):
    params = {**params, "dryRun": True}
    response = {"executionResults": [{"success": True, "wouldDelete": True}], "dryRun": True}
    fake_archicad.on_tapir_command(command, response)

    mode = "inline" if command == "DeleteNavigatorItems" else "auto"
    result = await archicad_call_tool(name, {"port": fake_archicad.port, "params": params}, resultMode=mode)

    assert result.get("dryRun") is True
    assert result["executionResults"] == (
        [{"coordinate": 0, "state": "success", "value": response["executionResults"][0]}]
        if command == "DeleteAttributes"
        else response["executionResults"]
    )
    assert fake_archicad.calls == [(command, params)]


async def test_2d_bounding_boxes_use_tapir_for_drawing_elements(fake_archicad):
    response = {"boundingBoxes2D": [{"boundingBox2D": {"xMin": 0, "yMin": 0, "xMax": 1, "yMax": 1}}]}
    fake_archicad.on_tapir_command("Get2DBoundingBoxes", response)
    params = {"elements": [{"elementId": {"guid": GUID}}]}

    result = await archicad_call_tool("elements_get2_d_bounding_boxes", {"port": fake_archicad.port, "params": params})

    assert result == response
    assert fake_archicad.calls == [("Get2DBoundingBoxes", params)]


async def test_library_primitives_are_inline_without_an_item_limit(fake_archicad):
    primitives = [
        {"type": "Line", "begCoordinate": {"x": index, "y": 0}, "endCoordinate": {"x": index, "y": 1}}
        for index in range(101)
    ]
    fake_archicad.on_tapir_command("GetLibraryPart2DPrimitives", {"primitives": primitives})
    params = {"name": "Door"}
    result = await archicad_call_tool("library_get_library_part2_d_primitives", {"port": 19723, "params": params})
    assert result == {"primitives": primitives}
    assert fake_archicad.calls == [("GetLibraryPart2DPrimitives", params)]


async def test_component_property_values_keep_their_two_axes(fake_archicad):
    values = [{"propertyValues": [{"value": str(index)}]} for index in range(3)]
    field = "propertyValuesForElementComponents"
    fake_archicad.on_tapir_command("GetPropertyValuesOfElementComponents", {field: values})
    params = {
        "elementComponents": [{"elementComponentId": {"elementId": {"guid": GUID}, "componentId": {"guid": GUID}}}] * 3,
        "properties": [{"propertyId": {"guid": GUID}}] * 2,
    }
    result = await archicad_call_tool(
        "properties_get_property_values_of_element_components", {"port": 19723, "params": params}
    )
    assert result[field] == [{"coordinate": i, "state": "success", "value": value} for i, value in enumerate(values)]
    assert fake_archicad.calls == [("GetPropertyValuesOfElementComponents", params)]


async def test_upstream_command_catalog_is_not_discoverable(fake_archicad):
    from tapir_archicad_mcp.tools.custom.functions import archicad_get_command_schema, archicad_list_commands

    page = archicad_list_commands(keywords=["app_get_commands"]).result
    assert page.exact_matches[0].exact_status == "missing"
    assert "app_get_commands" not in {match.name for match in page.matches}
    with pytest.raises(ToolError, match="not found"):
        archicad_get_command_schema("app_get_commands")


async def test_result_reads_pin_the_snapshot_without_reexecuting(fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(250)})
    first = await archicad_call_tool("elements_get_selected_elements", {"port": 19723})
    selection = ReadSelection(paths=[["elements"]], indices={"start": 100, "stop": 102})
    handle = first["resultHandle"]
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(2, "other")})
    second = await archicad_call_tool("elements_get_selected_elements", {"port": 19723})
    assert handle != second["resultHandle"]
    read = await result_read(handle, selection, maxEntries=1)
    page = read.structured_content
    assert page["entries"] == [{"path": ["elements", 100], "value": _elements(250)[100]}]
    for _ in range(2):
        last = (await result_read(handle, selection, continuation=page["continuation"])).structured_content
        assert last["entries"][0]["value"] == _elements(250)[101]
        assert not last["truncated"]
    assert len(fake_archicad.calls) == 2


async def test_generated_create_tool_dispatches_params_and_preserves_raw_result(fake_archicad):
    """
    A generated mutating command (CreateSlabs) must validate its params
    model and forward them to Tapir without validating the result.
    """
    fake_archicad.on_tapir_command("CreateSlabs", {"elements": []})

    result = await archicad_call_tool(
        "elements_create_slabs",
        {"port": fake_archicad.port, "params": {"slabsData": []}},
        resultMode="inline",
    )

    assert result == {"elements": []}
    command, parameters = fake_archicad.calls[0]
    assert command == "CreateSlabs"
    assert parameters == {"slabsData": []}


async def test_nested_command_parameter_extras_are_rejected_before_transport(fake_archicad):
    with pytest.raises(ToolError, match="Invalid arguments provided"):
        await archicad_call_tool(
            "elements_create_slabs",
            {
                "port": fake_archicad.port,
                "params": {"slabsData": [], "inventedField": True},
            },
        )

    assert fake_archicad.calls == []


async def test_bulk_validation_error_is_grouped_and_omits_input(fake_archicad, caplog):
    slabs = [{"level": "secret-level"} for _ in range(500)]

    with pytest.raises(ToolError) as raised:
        await archicad_call_tool("elements_create_slabs", {"port": fake_archicad.port, "params": {"slabsData": slabs}})

    message = str(raised.value)
    assert "secret-level" not in message
    assert "secret-level" not in caplog.text
    assert len(message.splitlines()) <= 8
    assert fake_archicad.calls == []


async def test_raw_archicad_error_payload_is_preserved(fake_archicad):
    """
    A fake transport can return an error-shaped payload directly. The MCP
    preserves it; the real Multiconn transport raises command-level errors
    before this point.
    """
    fake_archicad.on_tapir_command(
        "GetSelectedElements",
        {"error": {"code": 4001, "message": "No open project."}},
    )

    result = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}, resultMode="inline"
    )

    assert result == {"error": {"code": 4001, "message": "No open project."}}


async def test_unknown_port_is_rejected(fake_archicad):
    """Targeting a port that is not active must fail with a clear error."""
    with pytest.raises(ToolError, match="at port") as raised:
        await archicad_call_tool("elements_get_selected_elements", {"port": 19999})

    assert "19999" not in str(raised.value)
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
async def test_invalid_command_envelopes_are_rejected_before_transport(fake_archicad, name, arguments):
    with pytest.raises(ToolError, match="Invalid arguments provided"):
        await archicad_call_tool(name, arguments)

    assert fake_archicad.calls == []


async def test_port_string_is_coerced_and_dispatched(fake_archicad):
    fake_archicad.on_tapir_command("GetAddOnVersion", {"version": "1.0.0"})

    result = await archicad_call_tool("app_get_add_on_version", {"port": str(fake_archicad.port)})

    assert result == {"version": "1.0.0"}
    assert fake_archicad.calls[0][0] == "GetAddOnVersion"


async def test_inactive_in_range_port_is_rejected_before_transport(fake_archicad):
    with pytest.raises(ToolError, match="19724.*not an active Archicad connection"):
        await archicad_call_tool("app_get_add_on_version", {"port": 19724})

    assert fake_archicad.calls == []


async def test_aliased_parameter_is_sent_under_its_api_name(fake_archicad):
    """
    Parameters whose name collides with a pydantic BaseModel member are
    generated as '<name>_' with an alias. The request must go out under the
    alias, otherwise Archicad rejects the unknown field (see issue #27).
    """
    fake_archicad.on_tapir_command("MoveElements", {"executionResults": []})

    await archicad_call_tool(
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
