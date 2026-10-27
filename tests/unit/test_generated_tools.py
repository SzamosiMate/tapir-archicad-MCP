import pytest
from mcp.server.mcpserver.exceptions import ToolError
from multiconn_archicad import Port
from payloads import archicad_call_tool, archicad_get_job

from tapir_archicad_mcp.context import multi_conn_instance
from tapir_archicad_mcp.jobs import JobSettings

GUID = "12345678-1234-1234-1234-123456789012"
pytestmark = pytest.mark.asyncio


def _elements(count: int, prefix: str = "element") -> list[dict]:
    return [
        {"elementId": {"guid": f"{prefix}-{index:03d}"}}
        for index in range(count)
    ]


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
        "elements_get_selected_elements", {"port": fake_archicad.port}
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

    result = await archicad_call_tool(name, {"port": fake_archicad.port, "params": params})

    assert result == response
    assert fake_archicad.calls == [(command, params)]


async def test_element_details_pages_raw_results_without_reexecuting(fake_archicad):
    details = [{"details": {"height": index}} for index in range(101)]
    details[-1] = {"error": {"code": 1, "message": "Cannot read element"}}
    fake_archicad.on_tapir_command("GetDetailsOfElements", {"detailsOfElements": details})
    arguments = {"port": fake_archicad.port, "params": {"elements": [{"elementId": {"guid": GUID}}]}}

    first_page = await archicad_call_tool("elements_get_details_of_elements", arguments)
    last_page = await archicad_call_tool(
        "elements_get_details_of_elements", {**arguments, "page_token": first_page["next_page_token"]}
    )

    assert first_page["detailsOfElements"] == details[:100]
    assert last_page["detailsOfElements"] == details[100:]
    assert last_page["pagination"] == {"total": 101, "returned": 1, "truncated": False}
    assert fake_archicad.calls == [("GetDetailsOfElements", arguments["params"])]


async def test_paginated_read_tool_returns_pages_from_one_transport_snapshot(fake_archicad):
    fake_archicad.on_tapir_command(
        "GetSelectedElements",
        {
            "elements": _elements(201),
            "futureField": None,
        },
    )

    first_page = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    token = first_page["next_page_token"]

    second_page = await archicad_call_tool(
        "elements_get_selected_elements",
        {"port": fake_archicad.port, "page_token": token},
    )
    final_page = await archicad_call_tool(
        "elements_get_selected_elements",
        {"port": fake_archicad.port, "page_token": second_page["next_page_token"]},
    )

    assert len(first_page["elements"]) == 100
    assert len(second_page["elements"]) == 100
    assert len(final_page["elements"]) == 1
    assert "next_page_token" not in final_page
    assert first_page["futureField"] is None
    assert fake_archicad.calls == [("GetSelectedElements", {})]


async def test_replaying_page_token_returns_same_page_and_does_not_call_archicad(fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(150)})

    first_page = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    token = first_page["next_page_token"]

    page = await archicad_call_tool(
        "elements_get_selected_elements",
        {"port": fake_archicad.port, "page_token": token},
    )
    replay = await archicad_call_tool(
        "elements_get_selected_elements",
        {"port": fake_archicad.port, "page_token": token},
    )

    assert replay == page
    assert len(fake_archicad.calls) == 1


async def test_new_initial_request_does_not_replace_an_existing_snapshot(fake_archicad):
    fake_archicad.on_tapir_command(
        "GetSelectedElements", {"elements": _elements(150, prefix="first")}
    )
    first_page = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    first_token = first_page["next_page_token"]

    fake_archicad.on_tapir_command(
        "GetSelectedElements", {"elements": _elements(150, prefix="second")}
    )
    second_page = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    second_token = second_page["next_page_token"]

    first_remainder = await archicad_call_tool(
        "elements_get_selected_elements",
        {"port": fake_archicad.port, "page_token": first_token},
    )
    second_remainder = await archicad_call_tool(
        "elements_get_selected_elements",
        {"port": fake_archicad.port, "page_token": second_token},
    )

    assert first_token != second_token
    assert first_remainder["elements"][0]["elementId"]["guid"] == "first-100"
    assert second_remainder["elements"][0]["elementId"]["guid"] == "second-100"
    assert len(fake_archicad.calls) == 2


@pytest.mark.parametrize("page_token", ["", "forged"])
async def test_invalid_page_token_is_rejected_before_transport(fake_archicad, page_token):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(150)})

    with pytest.raises(ToolError, match="page_token"):
        await archicad_call_tool(
            "elements_get_selected_elements",
            {"port": fake_archicad.port, "page_token": page_token},
        )

    assert fake_archicad.calls == []


@pytest.mark.parametrize("offset", ["-1", "1", "200"])
async def test_invalid_page_offset_is_rejected_before_transport(fake_archicad, offset):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(150)})
    first_page = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    session, separator, _ = first_page["next_page_token"].partition(":")
    assert separator
    forged_offset_token = f"{session}:{offset}"

    with pytest.raises(ToolError, match="page_token"):
        await archicad_call_tool(
            "elements_get_selected_elements",
            {"port": fake_archicad.port, "page_token": forged_offset_token},
        )

    assert len(fake_archicad.calls) == 1


async def test_page_token_is_bound_to_command(fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(150)})
    first_page = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    token = first_page["next_page_token"]

    fake_archicad.on_tapir_command("GetAllProperties", {"properties": _elements(150)})
    with pytest.raises(ToolError, match="page_token"):
        await archicad_call_tool(
            "properties_get_all_properties",
            {"port": fake_archicad.port, "page_token": token},
        )

    assert len(fake_archicad.calls) == 1


async def test_page_token_is_bound_to_serialized_parameters(fake_archicad):
    fake_archicad.on_tapir_command("GetAllElements", {"elements": _elements(150)})
    first_page = await archicad_call_tool(
        "elements_get_all_elements",
        {"port": fake_archicad.port, "params": {}},
    )
    token = first_page["next_page_token"]

    with pytest.raises(ToolError, match="page_token"):
        await archicad_call_tool(
            "elements_get_all_elements",
            {
                "port": fake_archicad.port,
                "params": {"filters": ["IsVisibleIn3D"]},
                "page_token": token,
            },
        )

    assert fake_archicad.calls == [("GetAllElements", {})]


async def test_page_token_is_bound_to_connection_identity(fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(150)})
    first_page = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    token = first_page["next_page_token"]

    multi_conn = multi_conn_instance.get()
    multi_conn.active[Port(fake_archicad.port)] = object()
    with pytest.raises(ToolError, match="page_token"):
        await archicad_call_tool(
            "elements_get_selected_elements",
            {"port": fake_archicad.port, "page_token": token},
        )

    assert len(fake_archicad.calls) == 1


async def test_pruned_page_token_is_rejected_without_transport(job_store, job_clock, fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(150)})
    first_page = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    token = first_page["next_page_token"]
    job_clock.now += JobSettings().job_ttl_seconds + 1
    job_store.prune()

    with pytest.raises(ToolError, match="page_token"):
        await archicad_call_tool(
            "elements_get_selected_elements",
            {"port": fake_archicad.port, "page_token": token},
        )

    assert fake_archicad.calls == [("GetSelectedElements", {})]


async def test_response_of_page_size_or_less_is_returned_without_pagination(fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(100)})

    result = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )

    assert len(result["elements"]) == 100
    assert "next_page_token" not in result
    assert result["pagination"] == {"total": 100, "returned": 100, "truncated": False}


async def test_first_page_reports_total_and_truncated(fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(250)})

    first_page = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )

    assert first_page["pagination"] == {"total": 250, "returned": 100, "truncated": True}
    handle = (await archicad_get_job())["jobs"][0]["jobHandle"]
    assert (await archicad_get_job(handle))["result"]["pagination"] == first_page["pagination"]


async def test_last_page_is_not_truncated(fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(250)})
    page = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )

    paginations = []
    for _ in range(2):
        page = await archicad_call_tool(
            "elements_get_selected_elements",
            {"port": fake_archicad.port, "page_token": page["next_page_token"]},
        )
        paginations.append(page["pagination"])

    assert paginations[0] == {"total": 250, "returned": 100, "truncated": True}
    assert len(page["elements"]) == 50
    assert page["pagination"] == {"total": 250, "returned": 50, "truncated": False}
    assert "next_page_token" not in page


async def test_short_list_fits_one_page(fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(30)})

    result = await archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )

    assert result["pagination"] == {"total": 30, "returned": 30, "truncated": False}
    assert "next_page_token" not in result


async def test_unpaginated_commands_have_no_pagination(fake_archicad):
    fake_archicad.on_tapir_command("GetAddOnVersion", {"version": "1.7.2"})

    result = await archicad_call_tool("app_get_add_on_version", {"port": fake_archicad.port})

    assert result == {"version": "1.7.2"}


async def test_generated_create_tool_dispatches_params_and_preserves_raw_result(fake_archicad):
    """
    A generated mutating command (CreateSlabs) must validate its params
    model and forward them to Tapir without validating the result.
    """
    fake_archicad.on_tapir_command("CreateSlabs", {"elements": []})

    result = await archicad_call_tool(
        "elements_create_slabs",
        {"port": fake_archicad.port, "params": {"slabsData": []}},
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
        "elements_get_selected_elements", {"port": fake_archicad.port}
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

    result = await archicad_call_tool(
        "app_get_add_on_version", {"port": str(fake_archicad.port)}
    )

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
