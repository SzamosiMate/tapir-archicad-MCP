import pytest
from tapir_archicad_mcp.tools.custom.functions import archicad_call_tool
from tapir_archicad_mcp import pagination
from tapir_archicad_mcp.context import multi_conn_instance
from multiconn_archicad.basic_types import Port


GUID = "12345678-1234-1234-1234-123456789012"


def _elements(count: int, prefix: str = "element") -> list[dict]:
    return [
        {"elementId": {"guid": f"{prefix}-{index:03d}"}}
        for index in range(count)
    ]


@pytest.fixture(autouse=True)
def clear_pagination_cache():
    pagination.PAGINATION_CACHE.clear()
    yield
    pagination.PAGINATION_CACHE.clear()


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

def test_paginated_read_tool_returns_pages_from_one_transport_snapshot(fake_archicad):
    fake_archicad.on_tapir_command(
        "GetSelectedElements",
        {
            "elements": _elements(201),
            "futureField": None,
        },
    )

    first_page = archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    token = first_page["next_page_token"]

    second_page = archicad_call_tool(
        "elements_get_selected_elements",
        {"port": fake_archicad.port, "page_token": token},
    )
    final_page = archicad_call_tool(
        "elements_get_selected_elements",
        {"port": fake_archicad.port, "page_token": second_page["next_page_token"]},
    )

    assert len(first_page["elements"]) == 100
    assert len(second_page["elements"]) == 100
    assert len(final_page["elements"]) == 1
    assert "next_page_token" not in final_page
    assert first_page["futureField"] is None
    assert fake_archicad.calls == [("GetSelectedElements", {})]


def test_replaying_page_token_returns_same_page_and_does_not_call_archicad(fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(150)})

    first_page = archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    token = first_page["next_page_token"]

    page = archicad_call_tool(
        "elements_get_selected_elements",
        {"port": fake_archicad.port, "page_token": token},
    )
    replay = archicad_call_tool(
        "elements_get_selected_elements",
        {"port": fake_archicad.port, "page_token": token},
    )

    assert replay == page
    assert len(fake_archicad.calls) == 1


def test_new_initial_request_does_not_replace_an_existing_snapshot(fake_archicad):
    fake_archicad.on_tapir_command(
        "GetSelectedElements", {"elements": _elements(150, prefix="first")}
    )
    first_page = archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    first_token = first_page["next_page_token"]

    fake_archicad.on_tapir_command(
        "GetSelectedElements", {"elements": _elements(150, prefix="second")}
    )
    second_page = archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    second_token = second_page["next_page_token"]

    first_remainder = archicad_call_tool(
        "elements_get_selected_elements",
        {"port": fake_archicad.port, "page_token": first_token},
    )
    second_remainder = archicad_call_tool(
        "elements_get_selected_elements",
        {"port": fake_archicad.port, "page_token": second_token},
    )

    assert first_token != second_token
    assert first_remainder["elements"][0]["elementId"]["guid"] == "first-100"
    assert second_remainder["elements"][0]["elementId"]["guid"] == "second-100"
    assert len(fake_archicad.calls) == 2


@pytest.mark.parametrize("page_token", ["", "forged"])
def test_invalid_page_token_is_rejected_before_transport(fake_archicad, page_token):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(150)})

    with pytest.raises(ValueError, match="page_token"):
        archicad_call_tool(
            "elements_get_selected_elements",
            {"port": fake_archicad.port, "page_token": page_token},
        )

    assert fake_archicad.calls == []


@pytest.mark.parametrize("offset", ["-1", "1", "200"])
def test_invalid_page_offset_is_rejected_before_transport(fake_archicad, offset):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(150)})
    first_page = archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    session, separator, _ = first_page["next_page_token"].partition(":")
    assert separator
    forged_offset_token = f"{session}:{offset}"

    with pytest.raises(ValueError, match="page_token"):
        archicad_call_tool(
            "elements_get_selected_elements",
            {"port": fake_archicad.port, "page_token": forged_offset_token},
        )

    assert len(fake_archicad.calls) == 1


def test_page_token_is_bound_to_command(fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(150)})
    first_page = archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    token = first_page["next_page_token"]

    fake_archicad.on_tapir_command("GetAllProperties", {"properties": _elements(150)})
    with pytest.raises(ValueError, match="page_token"):
        archicad_call_tool(
            "properties_get_all_properties",
            {"port": fake_archicad.port, "page_token": token},
        )

    assert len(fake_archicad.calls) == 1


def test_page_token_is_bound_to_serialized_parameters(fake_archicad):
    fake_archicad.on_tapir_command("GetAllElements", {"elements": _elements(150)})
    first_page = archicad_call_tool(
        "elements_get_all_elements",
        {"port": fake_archicad.port, "params": {}},
    )
    token = first_page["next_page_token"]

    with pytest.raises(ValueError, match="page_token"):
        archicad_call_tool(
            "elements_get_all_elements",
            {
                "port": fake_archicad.port,
                "params": {"filters": ["IsVisibleIn3D"]},
                "page_token": token,
            },
        )

    assert fake_archicad.calls == [("GetAllElements", {})]


def test_page_token_is_bound_to_connection_identity(fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(150)})
    first_page = archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    token = first_page["next_page_token"]

    multi_conn = multi_conn_instance.get()
    multi_conn.active[Port(fake_archicad.port)] = object()
    with pytest.raises(ValueError, match="page_token"):
        archicad_call_tool(
            "elements_get_selected_elements",
            {"port": fake_archicad.port, "page_token": token},
        )

    assert len(fake_archicad.calls) == 1


def test_expired_page_token_is_rejected_without_transport(monkeypatch, fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(150)})
    now = [1000.0]
    monkeypatch.setattr(pagination.time, "monotonic", lambda: now[0])
    first_page = archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )
    token = first_page["next_page_token"]
    now[0] += pagination.CACHE_LIFETIME_SECONDS + 1

    with pytest.raises(ValueError, match="page_token"):
        archicad_call_tool(
            "elements_get_selected_elements",
            {"port": fake_archicad.port, "page_token": token},
        )

    assert fake_archicad.calls == [("GetSelectedElements", {})]


def test_pagination_cache_is_bounded(monkeypatch, fake_archicad):
    monkeypatch.setattr(pagination, "MAX_CACHE_ENTRIES", 2)
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(150)})

    for _ in range(3):
        archicad_call_tool(
            "elements_get_selected_elements", {"port": fake_archicad.port}
        )

    assert len(pagination.PAGINATION_CACHE) <= 2


def test_response_of_page_size_or_less_is_returned_without_caching(fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": _elements(100)})

    result = archicad_call_tool(
        "elements_get_selected_elements", {"port": fake_archicad.port}
    )

    assert len(result["elements"]) == 100
    assert "next_page_token" not in result
    assert pagination.PAGINATION_CACHE == {}


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
