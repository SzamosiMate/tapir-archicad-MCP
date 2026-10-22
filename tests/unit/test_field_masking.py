from __future__ import annotations

import pytest

from caracara_archicad_mcp.field_masking import project_element, prune_payload
from caracara_archicad_mcp.tools.custom.functions import archicad_call_tool


def test_project_element_strips_polygon_vertices_and_internal_memos():
    """Confirms that specifying fields=['id', 'storyIndex'] strips polygon vertices and internal memos."""
    element = {
        "id": "SW-001",
        "storyIndex": 2,
        "polygonVertices": [[0.0, 0.0], [10.0, 0.0], [10.0, 3.0], [0.0, 3.0]],
        "rawCoordinates": [0.0, 0.0, 0.0],
        "internalMemos": "Internal memo data for debug and calculation",
        "floorPlanPolygons": [{"vertices": [[0.0, 0.0], [1.0, 1.0]]}],
        "details": {"geometryType": "Straight", "thickness": 0.25},
    }

    projected = project_element(element, fields=["id", "storyIndex"])

    assert projected == {
        "id": "SW-001",
        "storyIndex": 2,
    }
    assert "polygonVertices" not in projected
    assert "internalMemos" not in projected
    assert "rawCoordinates" not in projected
    assert "floorPlanPolygons" not in projected
    assert "details" not in projected


def test_project_element_resolves_floor_index_alias():
    """Confirms floorIndex is mapped to storyIndex when storyIndex is requested."""
    element = {
        "id": "COL-042",
        "floorIndex": 1,
        "polygonVertices": [[1.0, 1.0]],
        "internalMemos": "memo",
    }

    projected = project_element(element, fields=["id", "storyIndex"])

    assert projected == {
        "id": "COL-042",
        "storyIndex": 1,
    }
    assert "polygonVertices" not in projected
    assert "internalMemos" not in projected


def test_project_element_case_insensitivity_and_snake_case():
    """Confirms field matching works across snake_case and camelCase."""
    element = {
        "layerIndex": 12,
        "drawIndex": 5,
        "polygonVertices": [[0, 0]],
    }

    projected = project_element(element, fields=["layer_index", "drawIndex"])

    assert projected == {
        "layer_index": 12,
        "drawIndex": 5,
    }
    assert "polygonVertices" not in projected


def test_project_element_nested_dot_notation():
    """Confirms dot notation extracts nested properties into structured output."""
    element = {
        "id": "SLAB-01",
        "polygonVertices": [[0, 0], [5, 5]],
        "details": {
            "geometryType": "Polygon",
            "thickness": 0.3,
        },
    }

    projected = project_element(element, fields=["id", "details.thickness"])

    assert projected == {
        "id": "SLAB-01",
        "details": {
            "thickness": 0.3,
        },
    }
    assert "polygonVertices" not in projected


def test_project_element_sub_details_fallback():
    """Confirms un-nested field names can extract directly from details dictionary."""
    element = {
        "id": "WALL-02",
        "polygonVertices": [[0, 0]],
        "details": {
            "geometryType": "Straight",
            "structureType": "Composite",
        },
    }

    projected = project_element(element, fields=["id", "geometryType"])

    assert projected == {
        "id": "WALL-02",
        "geometryType": "Straight",
    }
    assert "polygonVertices" not in projected


def test_prune_payload_preserves_metadata():
    """Confirms prune_payload prunes items in list while preserving top-level metadata."""
    payload = {
        "detailsOfElements": [
            {
                "id": "SW-01",
                "storyIndex": 0,
                "polygonVertices": [[0, 0]],
                "internalMemos": "memo 1",
            },
            {
                "id": "SW-02",
                "storyIndex": 1,
                "polygonVertices": [[5, 5]],
                "internalMemos": "memo 2",
            },
        ],
        "next_page_token": "token-offset-100",
    }

    result = prune_payload(payload, fields=["id", "storyIndex"])

    assert result["next_page_token"] == "token-offset-100"
    assert len(result["detailsOfElements"]) == 2
    assert result["detailsOfElements"][0] == {"id": "SW-01", "storyIndex": 0}
    assert result["detailsOfElements"][1] == {"id": "SW-02", "storyIndex": 1}
    assert "polygonVertices" not in result["detailsOfElements"][0]
    assert "internalMemos" not in result["detailsOfElements"][0]


def test_prune_payload_none_or_empty_returns_unchanged():
    """Confirms prune_payload with None or empty fields leaves payload unchanged."""
    payload = {"detailsOfElements": [{"id": "1", "polygonVertices": [[0, 0]]}]}

    assert prune_payload(payload, None) == payload
    assert prune_payload(payload, []) == payload


@pytest.mark.asyncio
async def test_get_details_of_elements_end_to_end_field_masking(fake_archicad):
    """End-to-end verification that GetDetailsOfElements strips polygon vertices and internal memos."""
    canned_element = {
        "id": "SW - 001",
        "storyIndex": 3,
        "floorIndex": 3,
        "type": "Wall",
        "polygonVertices": [
            {"x": 0.0, "y": 0.0, "z": 0.0},
            {"x": 10.0, "y": 0.0, "z": 0.0},
            {"x": 10.0, "y": 5.0, "z": 0.0},
        ],
        "rawCoordinates": [0.0, 0.0, 0.0, 10.0, 0.0, 0.0],
        "internalMemos": "Internal memory offset table #0x4A2F",
        "floorPlanPolygons": [{"loop": [1, 2, 3]}],
        "details": {
            "geometryType": "Straight",
            "thickness": 0.2,
        },
    }

    fake_archicad.on_tapir_command(
        "GetDetailsOfElements",
        {"detailsOfElements": [canned_element]},
    )

    result = await archicad_call_tool(
        "elements_get_details_of_elements",
        {
            "port": fake_archicad.port,
            "params": {
                "elements": [{"elementId": {"guid": "00000000-0000-0000-0000-000000000001"}}],
                "fields": ["id", "storyIndex"],
            },
        },
    )

    assert "detailsOfElements" in result
    element_result = result["detailsOfElements"][0]

    # Verify exact projection: only requested fields are present
    assert element_result == {
        "id": "SW - 001",
        "storyIndex": 3,
    }

    # Verify unrequested heavy columns are stripped
    assert "polygonVertices" not in element_result
    assert "internalMemos" not in element_result
    assert "rawCoordinates" not in element_result
    assert "floorPlanPolygons" not in element_result
    assert "details" not in element_result


@pytest.mark.asyncio
async def test_get_details_of_elements_top_level_fields_argument(fake_archicad):
    """Verifies that 'fields' specified at top level of arguments is applied."""
    canned_element = {
        "id": "BEAM-01",
        "storyIndex": 1,
        "polygonVertices": [[0, 0], [1, 1]],
        "internalMemos": "memo info",
    }
    fake_archicad.on_tapir_command(
        "GetDetailsOfElements",
        {"detailsOfElements": [canned_element]},
    )

    result = await archicad_call_tool(
        "elements_get_details_of_elements",
        {
            "port": fake_archicad.port,
            "fields": ["id", "storyIndex"],
            "params": {
                "elements": [{"elementId": {"guid": "00000000-0000-0000-0000-000000000002"}}],
            },
        },
    )

    element_result = result["detailsOfElements"][0]
    assert element_result == {
        "id": "BEAM-01",
        "storyIndex": 1,
    }
    assert "polygonVertices" not in element_result
    assert "internalMemos" not in element_result
