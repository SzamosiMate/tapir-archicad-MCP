"""Polymorphic Meta-Verbs for Archicad MCP.

Collapses 80+ granular CRUD endpoints down into two composable MCP tools:
1. archicad_query(target, filter, output): Handles discovery, criteria search, and metadata extraction.
2. archicad_mutate(target_set, action, payload): Handles property updates, geometric transformations, and deletions.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.result_registry import ResultRegistry
from tapir_archicad_mcp.tools.custom.functions import archicad_call_tool

log = logging.getLogger(__name__)


def _normalize_element_type(target: str) -> str:
    """Normalize element type names to standard Archicad capitalization."""
    type_map = {
        "wall": "Wall", "walls": "Wall",
        "column": "Column", "columns": "Column",
        "slab": "Slab", "slabs": "Slab",
        "beam": "Beam", "beams": "Beam",
        "door": "Door", "doors": "Door",
        "window": "Window", "windows": "Window",
        "roof": "Roof", "roofs": "Roof",
        "mesh": "Mesh", "meshes": "Mesh",
        "zone": "Zone", "zones": "Zone",
        "morph": "Morph", "morphs": "Morph",
        "object": "Object", "objects": "Object",
        "stair": "Stair", "stairs": "Stair",
        "railing": "Railing", "railings": "Railing",
        "curtainwall": "CurtainWall", "curtainwalls": "CurtainWall",
        "curtain_wall": "CurtainWall", "curtain_walls": "CurtainWall",
        "hatch": "Hatch", "hatches": "Hatch",
        "line": "Line", "lines": "Line",
        "polyline": "Polyline", "polylines": "Polyline",
        "arc": "Arc", "arcs": "Arc",
        "circle": "Circle", "circles": "Circle",
        "text": "Text", "texts": "Text",
        "label": "Label", "labels": "Label",
        "dimension": "Dimension", "dimensions": "Dimension",
    }
    cleaned = target.strip().lower()
    return type_map.get(cleaned, target.strip())


@mcp.tool(
    name="archicad_query",
    title="Query Archicad Elements & Metadata",
    description=(
        "Polymorphic meta-verb for element discovery, criteria search, and metadata extraction. "
        "Replaces granular element querying commands. "
        "- target: Element type (e.g. 'Wall', 'Column', 'Slab', 'Beam', 'Window', 'Door', 'Roof', 'Zone', 'Morph'), "
        "or 'all', 'selected', 'classified', 'filter'. "
        "- filter: Optional criteria dictionary (e.g. {'filters': ['IsVisibleIn3D']}, {'classificationItemId': ...}). "
        "- output: Desired output: 'set' for opaque virtual set token (default), 'ids' for raw element identifiers, "
        "or a list of field names (e.g. ['id', 'storyIndex']) for pruned metadata extraction."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def archicad_query(
    target: str,
    filter: dict[str, Any] | None = None,
    output: list[str] | str | None = None,
    port: int | None = None,
) -> dict[str, Any]:
    """Execute a polymorphic query in Archicad."""
    target_port = port or 19723
    target_lower = target.strip().lower()
    set_id: str | None = None
    raw_elements: list[dict[str, Any]] = []
    element_type: str = target

    # 1. Routing to appropriate discovery tool
    if target_lower in ("selected", "selection"):
        raw_res = await archicad_call_tool("elements_get_selected_elements", {"port": target_port})
        raw_elements = raw_res.get("elements", [])
        element_type = "Selected"

    elif target_lower in ("all", "all_elements", "elements"):
        params: dict[str, Any] = {}
        if filter and "filters" in filter:
            params["filters"] = filter["filters"]
        raw_res = await archicad_call_tool("elements_get_all_elements", {"port": target_port, "params": params})
        raw_elements = raw_res.get("elements", [])
        element_type = "Element"

    elif target_lower in ("classified", "classification") or (filter and "classificationItemId" in filter):
        if not filter or "classificationItemId" not in filter:
            raise ToolError("When target is 'classified', filter must include 'classificationItemId'.")
        raw_res = await archicad_call_tool(
            "elements_get_elements_by_classification",
            {"port": target_port, "params": {"classificationItemId": filter["classificationItemId"]}},
        )
        set_id = raw_res.get("setId")
        if set_id and ResultRegistry.has(set_id):
            raw_elements = ResultRegistry.get(set_id)
        else:
            raw_elements = raw_res.get("elements", [])
        element_type = "Classified"

    elif target_lower in ("filter", "filtered") or (filter and "criterias" in filter and "elements" in filter):
        if not filter:
            raise ToolError("When target is 'filter', filter dictionary must be provided.")
        raw_res = await archicad_call_tool("elements_filter_elements", {"port": target_port, "params": filter})
        set_id = raw_res.get("setId")
        if set_id and ResultRegistry.has(set_id):
            raw_elements = ResultRegistry.get(set_id)
        else:
            raw_elements = raw_res.get("elements", [])
        element_type = "Filtered"

    else:
        element_type = _normalize_element_type(target)
        params = {"elementType": element_type}
        if filter and "filters" in filter:
            params["filters"] = filter["filters"]
        raw_res = await archicad_call_tool("elements_get_elements_by_type", {"port": target_port, "params": params})
        set_id = raw_res.get("setId")
        if set_id and ResultRegistry.has(set_id):
            raw_elements = ResultRegistry.get(set_id)
        else:
            raw_elements = raw_res.get("elements", [])

    # 2. Ensure stored in ResultRegistry
    if not set_id or not ResultRegistry.has(set_id):
        set_id = ResultRegistry.register(raw_elements, element_type=element_type)

    count = len(raw_elements)

    # 3. Output formatting & metadata projection
    if output == "set" or output is None:
        return {
            "setId": set_id,
            "count": count,
            "elementType": element_type,
        }

    if output == "count":
        return {
            "setId": set_id,
            "count": count,
            "elementType": element_type,
        }

    if output in ("ids", "elements", "guid", "guids"):
        return {
            "setId": set_id,
            "count": count,
            "elementType": element_type,
            "elements": raw_elements,
        }

    if isinstance(output, list) or output in ("details", "full"):
        # Metadata extraction with field projection
        fields = output if isinstance(output, list) else None
        details_params: dict[str, Any] = {"elements": raw_elements}
        if fields:
            details_params["fields"] = fields

        details_res = await archicad_call_tool(
            "elements_get_details_of_elements",
            {"port": target_port, "params": details_params},
        )
        return {
            "setId": set_id,
            "count": count,
            "elementType": element_type,
            "details": details_res.get("detailsOfElements", []),
        }

    raise ToolError(f"Unsupported output specification '{output}'. Supported: 'set', 'count', 'ids', or list of field names.")


@mcp.tool(
    name="archicad_mutate",
    title="Mutate Archicad Elements",
    description=(
        "Polymorphic meta-verb for property updates, geometric transformations, and deletions. "
        "Replaces granular element mutation commands. "
        "- target_set: Set handle token from archicad_query (e.g. 'set_walls_01') or explicit element list. "
        "- action: 'delete', 'highlight', 'set_property' (or 'update_property'), 'move' (or 'translate'), 'rotate', or 'set_details'. "
        "- payload: Action-specific parameter payload: "
        "  * For 'set_property': {'propertyId': ..., 'propertyValue': ...} or {'propertyValues': [...]} "
        "  * For 'highlight': {'highlightedColors': ..., 'wireframe3D': ...} "
        "  * For 'move': {'vector': {'x': ..., 'y': ..., 'z': ...}} or {'x': ..., 'y': ..., 'z': ...} "
        "  * For 'rotate': {'rotation': {'beginPoint': ..., 'endPoint': ..., 'origin': ...}} "
        "  * For 'delete': {} (optional)"
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def archicad_mutate(
    target_set: str | list[Any],
    action: str,
    payload: dict[str, Any] | None = None,
    port: int | None = None,
) -> dict[str, Any]:
    """Execute a polymorphic mutation on Archicad elements."""
    target_port = port or 19723

    # 1. Resolve elements from target_set
    if isinstance(target_set, str):
        elements = ResultRegistry.get_or_tool_error(target_set)
        set_id = target_set
    elif isinstance(target_set, list):
        elements = target_set
        set_id = ResultRegistry.register(elements)
    else:
        raise ToolError("Invalid target_set: must be a set_id handle (str) or a list of element dictionaries.")

    action_lower = action.strip().lower()

    # 2. Route based on action
    if action_lower in ("delete", "destroy", "remove"):
        return await archicad_call_tool(
            "elements_delete_elements",
            {"port": target_port, "params": {"targetSetId": set_id, "elements": elements}},
        )

    if action_lower in ("highlight", "select"):
        highlight_params: dict[str, Any] = {"targetSetId": set_id, "elements": elements}
        if payload:
            for k in ("highlightedColors", "wireframe3D", "nonHighlightedColor"):
                if k in payload:
                    highlight_params[k] = payload[k]
        return await archicad_call_tool(
            "elements_highlight_elements",
            {"port": target_port, "params": highlight_params},
        )

    if action_lower in ("set_property", "set_properties", "update_property", "update_properties", "property_update"):
        if not payload:
            raise ToolError("Payload must be provided for 'set_property' action.")
        prop_params = dict(payload)
        prop_params["targetSetId"] = set_id
        return await archicad_call_tool(
            "properties_set_property_values_of_elements",
            {"port": target_port, "params": prop_params},
        )

    if action_lower in ("move", "translate"):
        if not payload:
            raise ToolError("Payload must be provided for 'move' action (e.g. {'x': 1.0, 'y': 0.0, 'z': 0.0}).")
        vec = payload.get("vector", payload)
        x = float(vec.get("x", 0.0))
        y = float(vec.get("y", 0.0))
        z = float(vec.get("z", 0.0))
        copy_val = payload.get("copy", False)

        move_vectors: list[dict[str, Any]] = []
        for elem in elements:
            elem_id = elem.get("elementId", elem) if isinstance(elem, dict) else elem
            if not isinstance(elem_id, dict) or "guid" not in elem_id:
                elem_id = {"guid": str(getattr(elem_id, "guid", elem_id))}
            move_vectors.append({
                "elementId": elem_id,
                "moveVector": {"x": x, "y": y, "z": z},
                "copy": copy_val,
            })

        return await archicad_call_tool(
            "elements_move_elements",
            {"port": target_port, "params": {"elementsWithMoveVectors": move_vectors}},
        )

    if action_lower in ("rotate",):
        if not payload:
            raise ToolError("Payload must be provided for 'rotate' action.")
        rot = payload.get("rotation", payload)
        copy_val = payload.get("copy", False)

        rotations: list[dict[str, Any]] = []
        for elem in elements:
            elem_id = elem.get("elementId", elem) if isinstance(elem, dict) else elem
            if not isinstance(elem_id, dict) or "guid" not in elem_id:
                elem_id = {"guid": str(getattr(elem_id, "guid", elem_id))}
            rotations.append({
                "elementId": elem_id,
                "rotation": rot,
                "copy": copy_val,
            })

        return await archicad_call_tool(
            "elements_rotate_elements",
            {"port": target_port, "params": {"elementsWithRotations": rotations}},
        )

    if action_lower in ("set_details", "update_details"):
        if not payload:
            raise ToolError("Payload must be provided for 'set_details' action.")
        details = payload.get("details", payload)
        items: list[dict[str, Any]] = []
        for elem in elements:
            elem_id = elem.get("elementId", elem) if isinstance(elem, dict) else elem
            if not isinstance(elem_id, dict) or "guid" not in elem_id:
                elem_id = {"guid": str(getattr(elem_id, "guid", elem_id))}
            items.append({"elementId": elem_id, **details})

        return await archicad_call_tool(
            "elements_set_details_of_elements",
            {"port": target_port, "params": {"elementsWithDetails": items}},
        )

    raise ToolError(
        f"Unsupported action '{action}'. Supported actions: 'delete', 'highlight', 'set_property', 'move', 'rotate', 'set_details'."
    )
