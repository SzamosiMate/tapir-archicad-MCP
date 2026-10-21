from __future__ import annotations

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from tapir_archicad_mcp.result_registry import STORAGE_SETS, ResultRegistry
from tapir_archicad_mcp.tools.custom.functions import archicad_call_tool


@pytest.fixture(autouse=True)
def clean_storage():
    """Ensure ResultRegistry is clean before and after each test."""
    ResultRegistry.clear()
    yield
    ResultRegistry.clear()


class DummyElem(BaseModel):
    element_id: dict[str, str] = Field(default_factory=lambda: {"guid": "dummy-guid"}, alias="elementId")


def test_result_registry_registration_and_naming():
    """Verifies that ResultRegistry returns opaque set_id tokens with clean type prefixes."""
    set1 = ResultRegistry.register([{"elementId": {"guid": "guid-1"}}], element_type="Wall")
    assert set1 == "set_walls_01"
    assert ResultRegistry.has("set_walls_01")
    assert ResultRegistry.count("set_walls_01") == 1

    set2 = ResultRegistry.register([{"elementId": {"guid": "guid-2"}}], element_type="Wall")
    assert set2 == "set_walls_02"

    set_col = ResultRegistry.register([{"elementId": {"guid": "guid-3"}}], element_type="Column")
    assert set_col == "set_columns_01"

    set_default = ResultRegistry.register([{"elementId": {"guid": "guid-4"}}])
    assert set_default == "set_elements_01"


def test_result_registry_element_normalization():
    """Verifies elements are normalized into dictionaries regardless of input shape."""
    raw_guid = "11111111-2222-3333-4444-555555555555"
    pydantic_obj = DummyElem()
    dict_elem = {"elementId": {"guid": "dict-guid"}}

    set_id = ResultRegistry.register([raw_guid, pydantic_obj, dict_elem], element_type="Beam")
    stored = ResultRegistry.get(set_id)

    assert len(stored) == 3
    assert stored[0] == {"elementId": {"guid": raw_guid}}
    assert stored[1] == {"elementId": {"guid": "dummy-guid"}}
    assert stored[2] == {"elementId": {"guid": "dict-guid"}}
    assert STORAGE_SETS[set_id] == stored


def test_result_registry_error_handling_for_missing_or_expired_handle():
    """Verifies KeyError and ToolError handling for non-existent set IDs."""
    with pytest.raises(KeyError, match="not found or expired"):
        ResultRegistry.get("set_nonexistent_99")

    with pytest.raises(ToolError, match="not found or expired"):
        ResultRegistry.get_or_tool_error("set_nonexistent_99")


def test_result_registry_deletion_and_clear():
    """Verifies deletion and full clear operations."""
    set_id = ResultRegistry.register([{"elementId": {"guid": "g1"}}], element_type="Slab")
    assert ResultRegistry.has(set_id)

    ResultRegistry.delete(set_id)
    assert not ResultRegistry.has(set_id)
    assert set_id not in STORAGE_SETS

    set_id2 = ResultRegistry.register([{"elementId": {"guid": "g2"}}], element_type="Roof")
    assert ResultRegistry.has(set_id2)
    ResultRegistry.clear()
    assert not ResultRegistry.has(set_id2)
    assert len(STORAGE_SETS) == 0


@pytest.mark.asyncio
async def test_element_query_registers_set_and_returns_receipt(fake_archicad):
    """Element queries must cache GUIDs in ResultRegistry and return a compact summary receipt."""
    wall_elements = [
        {"elementId": {"guid": "00000000-0000-0000-0000-000000000001"}},
        {"elementId": {"guid": "00000000-0000-0000-0000-000000000002"}},
    ]
    fake_archicad.on_tapir_command("GetElementsByType", {"elements": wall_elements})

    result = await archicad_call_tool(
        "elements_get_elements_by_type",
        {"port": fake_archicad.port, "params": {"elementType": "Wall"}},
    )

    assert result == {
        "setId": "set_walls_01",
        "count": 2,
        "elementType": "Wall",
    }
    assert ResultRegistry.has("set_walls_01")
    assert ResultRegistry.get("set_walls_01") == wall_elements


@pytest.mark.asyncio
async def test_filter_elements_registers_set_and_returns_receipt(fake_archicad):
    """Filter elements query must cache GUIDs in ResultRegistry and return a compact receipt."""
    filtered = [{"elementId": {"guid": "00000000-0000-0000-0000-000000000001"}}]
    fake_archicad.on_tapir_command("FilterElements", {"elements": filtered})

    result = await archicad_call_tool(
        "elements_filter_elements",
        {
            "port": fake_archicad.port,
            "params": {"elements": filtered, "filters": ["IsVisibleIn3D"]},
        },
    )

    assert result == {
        "setId": "set_filtered_01",
        "count": 1,
        "elementType": "Filtered",
    }
    assert ResultRegistry.has("set_filtered_01")


@pytest.mark.asyncio
async def test_mutation_highlight_elements_with_target_set_id(fake_archicad):
    """HighlightElements must resolve elements from targetSetId."""
    elements = [{"elementId": {"guid": "elem-1"}}, {"elementId": {"guid": "elem-2"}}]
    set_id = ResultRegistry.register(elements, element_type="Wall")

    fake_archicad.on_tapir_command("HighlightElements", {"executionResults": [{"success": True}]})

    result = await archicad_call_tool(
        "elements_highlight_elements",
        {"port": fake_archicad.port, "params": {"targetSetId": set_id}},
    )

    assert result == {"executionResults": [{"success": True}]}
    assert fake_archicad.calls[-1] == (
        "HighlightElements",
        {"elements": elements},
    )


@pytest.mark.asyncio
async def test_mutation_highlight_elements_with_top_level_target_set_id(fake_archicad):
    """HighlightElements must accept targetSetId at the top level of arguments."""
    elements = [{"elementId": {"guid": "elem-1"}}]
    set_id = ResultRegistry.register(elements, element_type="Column")

    fake_archicad.on_tapir_command("HighlightElements", {"executionResults": [{"success": True}]})

    result = await archicad_call_tool(
        "elements_highlight_elements",
        {"port": fake_archicad.port, "targetSetId": set_id},
    )

    assert result == {"executionResults": [{"success": True}]}
    assert fake_archicad.calls[-1] == (
        "HighlightElements",
        {"elements": elements},
    )


@pytest.mark.asyncio
async def test_mutation_delete_elements_with_target_set_id(fake_archicad):
    """DeleteElements must resolve elements from targetSetId."""
    elements = [{"elementId": {"guid": "del-1"}}, {"elementId": {"guid": "del-2"}}]
    set_id = ResultRegistry.register(elements, element_type="Wall")

    fake_archicad.on_tapir_command("DeleteElements", {"executionResults": [{"success": True}]})

    result = await archicad_call_tool(
        "elements_delete_elements",
        {"port": fake_archicad.port, "params": {"targetSetId": set_id}},
    )

    assert result == {"executionResults": [{"success": True}]}
    assert fake_archicad.calls[-1] == (
        "DeleteElements",
        {"elements": elements},
    )


@pytest.mark.asyncio
async def test_mutation_delete_elements_with_invalid_target_set_id(fake_archicad):
    """DeleteElements with an invalid targetSetId must raise ToolError."""
    with pytest.raises(ToolError, match="not found or expired"):
        await archicad_call_tool(
            "elements_delete_elements",
            {"port": fake_archicad.port, "params": {"targetSetId": "set_expired_99"}},
        )


@pytest.mark.asyncio
async def test_mutation_delete_elements_missing_parameters_raises_tool_error(fake_archicad):
    """DeleteElements without elements or targetSetId must raise ToolError."""
    with pytest.raises(ToolError, match="Either 'targetSetId' or 'elements' must be provided"):
        await archicad_call_tool(
            "elements_delete_elements",
            {"port": fake_archicad.port, "params": {}},
        )


@pytest.mark.asyncio
async def test_mutation_set_property_values_with_target_set_id(fake_archicad):
    """SetPropertyValuesOfElements must expand property updates across all elements in targetSetId."""
    elements = [{"elementId": {"guid": "prop-1"}}, {"elementId": {"guid": "prop-2"}}]
    set_id = ResultRegistry.register(elements, element_type="Wall")

    prop_id = {"type": "BuiltIn", "nonLocalizedName": "Element_ID"}
    prop_val = {"type": "string", "value": "NewWallID"}

    fake_archicad.on_tapir_command("SetPropertyValuesOfElements", {"executionResults": [{"success": True}]})

    result = await archicad_call_tool(
        "properties_set_property_values_of_elements",
        {
            "port": fake_archicad.port,
            "params": {
                "targetSetId": set_id,
                "propertyId": prop_id,
                "propertyValue": prop_val,
            },
        },
    )

    assert result == {"executionResults": [{"success": True}]}
    assert fake_archicad.calls[-1] == (
        "SetPropertyValuesOfElements",
        {
            "elementPropertyValues": [
                {
                    "elementId": {"guid": "prop-1"},
                    "propertyId": prop_id,
                    "propertyValue": prop_val,
                },
                {
                    "elementId": {"guid": "prop-2"},
                    "propertyId": prop_id,
                    "propertyValue": prop_val,
                },
            ]
        },
    )


@pytest.mark.asyncio
async def test_mutation_set_property_values_with_invalid_target_set_id(fake_archicad):
    """SetPropertyValuesOfElements with an invalid targetSetId must raise ToolError."""
    with pytest.raises(ToolError, match="not found or expired"):
        await archicad_call_tool(
            "properties_set_property_values_of_elements",
            {
                "port": fake_archicad.port,
                "params": {
                    "targetSetId": "set_missing_01",
                    "propertyId": {"type": "BuiltIn"},
                    "propertyValue": {"value": 1},
                },
            },
        )
