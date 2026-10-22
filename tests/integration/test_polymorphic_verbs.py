from __future__ import annotations

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from caracara_archicad_mcp.app import mcp
from caracara_archicad_mcp.result_registry import ResultRegistry
from caracara_archicad_mcp.tools.custom.meta_verbs import archicad_mutate, archicad_query


@pytest.fixture(autouse=True)
def clean_registry():
    """Ensure ResultRegistry is clean before and after each test."""
    ResultRegistry.clear()
    yield
    ResultRegistry.clear()


@pytest.mark.asyncio
async def test_archicad_query_discovery_by_type_returns_set_receipt(fake_archicad):
    """Verifies archicad_query discovers elements by type and returns a compact set receipt."""
    walls = [
        {"elementId": {"guid": "00000000-0000-0000-0000-000000000001"}},
        {"elementId": {"guid": "00000000-0000-0000-0000-000000000002"}},
    ]
    fake_archicad.on_tapir_command("GetElementsByType", {"elements": walls})

    res = await archicad_query(target="Wall", port=fake_archicad.port)

    assert res == {
        "setId": "set_walls_01",
        "count": 2,
        "elementType": "Wall",
    }
    assert ResultRegistry.has("set_walls_01")
    assert ResultRegistry.get("set_walls_01") == walls
    assert fake_archicad.calls[-1] == ("GetElementsByType", {"elementType": "Wall"})


@pytest.mark.asyncio
async def test_archicad_query_metadata_extraction_with_field_projection(fake_archicad):
    """Verifies archicad_query chains discovery and metadata extraction, pruning unrequested columns."""
    slabs = [{"elementId": {"guid": "00000000-0000-0000-0000-000000000003"}}]
    fake_archicad.on_tapir_command("GetElementsByType", {"elements": slabs})

    canned_details = [
        {
            "id": "SLAB-101",
            "storyIndex": 2,
            "polygonVertices": [[0, 0], [10, 0], [10, 10], [0, 10]],
            "rawCoordinates": [0.0, 0.0, 0.0],
            "internalMemos": "Internal polygon triangulation cache memo",
            "details": {"geometryType": "Polygon", "thickness": 0.3},
        }
    ]
    fake_archicad.on_tapir_command("GetDetailsOfElements", {"detailsOfElements": canned_details})

    res = await archicad_query(
        target="Slab",
        output=["id", "storyIndex"],
        port=fake_archicad.port,
    )

    assert res["setId"] == "set_slabs_01"
    assert res["count"] == 1
    assert res["elementType"] == "Slab"
    assert len(res["details"]) == 1

    detail = res["details"][0]
    assert detail == {"id": "SLAB-101", "storyIndex": 2}
    assert "polygonVertices" not in detail
    assert "internalMemos" not in detail
    assert "rawCoordinates" not in detail
    assert "details" not in detail


@pytest.mark.asyncio
async def test_archicad_query_selected_elements(fake_archicad):
    """Verifies archicad_query discovers GUI selected elements."""
    selected = [{"elementId": {"guid": "00000000-0000-0000-0000-000000000004"}}]
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": selected})

    res = await archicad_query(target="selected", port=fake_archicad.port)

    assert res["count"] == 1
    assert res["elementType"] == "Selected"
    assert ResultRegistry.has(res["setId"])


@pytest.mark.asyncio
async def test_archicad_query_all_elements_with_filters(fake_archicad):
    """Verifies archicad_query discovers all elements matching filters."""
    all_elems = [{"elementId": {"guid": "00000000-0000-0000-0000-000000000005"}}]
    fake_archicad.on_tapir_command("GetAllElements", {"elements": all_elems})

    res = await archicad_query(
        target="all",
        filter={"filters": ["IsVisibleIn3D"]},
        output="ids",
        port=fake_archicad.port,
    )

    assert res["count"] == 1
    assert res["elements"] == all_elems
    assert fake_archicad.calls[-1] == ("GetAllElements", {"filters": ["IsVisibleIn3D"]})


@pytest.mark.asyncio
async def test_archicad_mutate_delete_via_target_set(fake_archicad):
    """Verifies archicad_mutate routes delete action for a target_set."""
    elements = [{"elementId": {"guid": "del-1"}}]
    set_id = ResultRegistry.register(elements, element_type="Wall")
    fake_archicad.on_tapir_command("DeleteElements", {"executionResults": [{"success": True}]})

    res = await archicad_mutate(target_set=set_id, action="delete", port=fake_archicad.port)

    assert res == {"executionResults": [{"success": True}]}
    assert fake_archicad.calls[-1] == ("DeleteElements", {"elements": elements})


@pytest.mark.asyncio
async def test_archicad_mutate_highlight_via_target_set(fake_archicad):
    """Verifies archicad_mutate routes highlight action with optional display options."""
    elements = [{"elementId": {"guid": "high-1"}}]
    set_id = ResultRegistry.register(elements, element_type="Column")
    fake_archicad.on_tapir_command("HighlightElements", {"executionResults": [{"success": True}]})

    res = await archicad_mutate(
        target_set=set_id,
        action="highlight",
        payload={"wireframe3D": True},
        port=fake_archicad.port,
    )

    assert res == {"executionResults": [{"success": True}]}
    assert fake_archicad.calls[-1] == (
        "HighlightElements",
        {"elements": elements, "wireframe3D": True},
    )


@pytest.mark.asyncio
async def test_archicad_mutate_set_property_via_target_set(fake_archicad):
    """Verifies archicad_mutate routes property updates across all elements in a target_set."""
    elements = [{"elementId": {"guid": "p-1"}}, {"elementId": {"guid": "p-2"}}]
    set_id = ResultRegistry.register(elements, element_type="Wall")
    fake_archicad.on_tapir_command("SetPropertyValuesOfElements", {"executionResults": [{"success": True}]})

    prop_id = {"type": "BuiltIn", "nonLocalizedName": "Element_ID"}
    prop_val = {"type": "string", "value": "UpdatedWallID"}

    res = await archicad_mutate(
        target_set=set_id,
        action="set_property",
        payload={"propertyId": prop_id, "propertyValue": prop_val},
        port=fake_archicad.port,
    )

    assert res == {"executionResults": [{"success": True}]}
    assert fake_archicad.calls[-1] == (
        "SetPropertyValuesOfElements",
        {
            "elementPropertyValues": [
                {"elementId": {"guid": "p-1"}, "propertyId": prop_id, "propertyValue": prop_val},
                {"elementId": {"guid": "p-2"}, "propertyId": prop_id, "propertyValue": prop_val},
            ]
        },
    )


@pytest.mark.asyncio
async def test_archicad_mutate_move_elements_via_target_set(fake_archicad):
    """Verifies archicad_mutate routes geometric translation to MoveElements."""
    elements = [{"elementId": {"guid": "00000000-0000-0000-0000-000000000021"}}]
    set_id = ResultRegistry.register(elements, element_type="Column")
    fake_archicad.on_tapir_command("MoveElements", {"executionResults": [{"success": True}]})

    res = await archicad_mutate(
        target_set=set_id,
        action="move",
        payload={"x": 2.5, "y": 0.0, "z": 1.0},
        port=fake_archicad.port,
    )

    assert res == {"executionResults": [{"success": True}]}
    assert fake_archicad.calls[-1] == (
        "MoveElements",
        {
            "elementsWithMoveVectors": [
                {
                    "elementId": {"guid": "00000000-0000-0000-0000-000000000021"},
                    "moveVector": {"x": 2.5, "y": 0.0, "z": 1.0},
                    "copy": False,
                }
            ]
        },
    )


@pytest.mark.asyncio
async def test_archicad_mutate_rotate_elements_via_target_set(fake_archicad):
    """Verifies archicad_mutate routes geometric rotation to RotateElements."""
    elements = [{"elementId": {"guid": "00000000-0000-0000-0000-000000000022"}}]
    set_id = ResultRegistry.register(elements, element_type="Wall")
    fake_archicad.on_tapir_command("RotateElements", {"executionResults": [{"success": True}]})

    rotation_params = {
        "beginPoint": {"x": 0.0, "y": 0.0},
        "endPoint": {"x": 1.0, "y": 0.0},
        "origin": {"x": 0.0, "y": 0.0},
    }

    res = await archicad_mutate(
        target_set=set_id,
        action="rotate",
        payload={"rotation": rotation_params},
        port=fake_archicad.port,
    )

    assert res == {"executionResults": [{"success": True}]}
    assert fake_archicad.calls[-1] == (
        "RotateElements",
        {
            "elementsWithRotations": [
                {
                    "elementId": {"guid": "00000000-0000-0000-0000-000000000022"},
                    "rotation": rotation_params,
                    "copy": False,
                }
            ]
        },
    )


@pytest.mark.asyncio
async def test_archicad_mutate_unsupported_action_raises_tool_error(fake_archicad):
    """Verifies archicad_mutate rejects unsupported actions with ToolError."""
    with pytest.raises(ToolError, match="Unsupported action 'unknown_action'"):
        await archicad_mutate(target_set=[{"elementId": {"guid": "00000000-0000-0000-0000-000000000023"}}], action="unknown_action", port=fake_archicad.port)


@pytest.mark.asyncio
async def test_complex_composable_workflow_chaining_both_meta_verbs(fake_archicad):
    """Integration test verifying end-to-end workflow: Query -> Inspect -> Mutate Property -> Move -> Delete."""
    walls = [
        {"elementId": {"guid": "00000000-0000-0000-0000-000000000010"}},
        {"elementId": {"guid": "00000000-0000-0000-0000-000000000011"}},
    ]
    fake_archicad.on_tapir_command("GetElementsByType", {"elements": walls})
    fake_archicad.on_tapir_command(
        "GetDetailsOfElements",
        {
            "detailsOfElements": [
                {"id": "W-1", "storyIndex": 0, "polygonVertices": [[0, 0]], "internalMemos": "m1"},
                {"id": "W-2", "storyIndex": 0, "polygonVertices": [[1, 1]], "internalMemos": "m2"},
            ]
        },
    )
    fake_archicad.on_tapir_command("SetPropertyValuesOfElements", {"executionResults": [{"success": True}]})
    fake_archicad.on_tapir_command("MoveElements", {"executionResults": [{"success": True}]})
    fake_archicad.on_tapir_command("DeleteElements", {"executionResults": [{"success": True}]})

    # Step 1: Query & Extract Pruned Details
    query_res = await archicad_query(
        target="Wall",
        output=["id", "storyIndex"],
        port=fake_archicad.port,
    )
    set_id = query_res["setId"]
    assert set_id == "set_walls_01"
    assert query_res["count"] == 2
    assert len(query_res["details"]) == 2
    assert "polygonVertices" not in query_res["details"][0]
    assert "internalMemos" not in query_res["details"][0]

    # Step 2: Mutate Property on discovered set handle
    prop_res = await archicad_mutate(
        target_set=set_id,
        action="set_property",
        payload={
            "propertyId": {"type": "BuiltIn", "nonLocalizedName": "Element_ID"},
            "propertyValue": {"type": "string", "value": "ProcessedWall"},
        },
        port=fake_archicad.port,
    )
    assert prop_res == {"executionResults": [{"success": True}]}

    # Step 3: Move elements by vector
    move_res = await archicad_mutate(
        target_set=set_id,
        action="move",
        payload={"x": 10.0, "y": 0.0, "z": 0.0},
        port=fake_archicad.port,
    )
    assert move_res == {"executionResults": [{"success": True}]}

    # Step 4: Delete elements in set
    del_res = await archicad_mutate(
        target_set=set_id,
        action="delete",
        port=fake_archicad.port,
    )
    assert del_res == {"executionResults": [{"success": True}]}


def test_granular_tools_deprecated_in_fastmcp():
    """Verifies that granular tool definitions are marked with deprecation notices."""
    tools = {t.name: t for t in mcp._tool_manager.list_tools()}

    # Both meta-verbs must be registered
    assert "archicad_query" in tools
    assert "archicad_mutate" in tools

    # Legacy tools carry [DEPRECATED] indicator in title or description
    for tool_name in ("archicad_list_commands", "archicad_get_command_schema", "archicad_call_tool"):
        assert tool_name in tools
        t = tools[tool_name]
        assert "DEPRECATED" in t.title or "DEPRECATED" in t.description
