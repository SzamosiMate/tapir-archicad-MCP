"""Client-side field masking and projection for element detail inspection.

Filters out raw coordinates, polygon arrays, or unrequested properties before
building the return payload, eliminating column bloat in LLM context.
"""

from __future__ import annotations

import re
from typing import Any


def _to_snake_case(s: str) -> str:
    """Convert camelCase or PascalCase to snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()


def project_element(item: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """Project an element dictionary to only include requested fields.

    Strips polygon arrays, raw coordinates, internal memos, and any other
    unrequested properties.
    """
    if not fields:
        return item

    projected: dict[str, Any] = {}
    lower_to_key = {k.lower(): k for k in item}
    snake_to_key = {_to_snake_case(k): k for k in item}

    for field in fields:
        # 1. Exact match
        if field in item:
            projected[field] = item[field]
            continue

        # 2. Case-insensitive or snake_case match
        field_lower = field.lower()
        if field_lower in lower_to_key:
            matched_key = lower_to_key[field_lower]
            projected[field] = item[matched_key]
            continue

        field_snake = _to_snake_case(field)
        if field_snake in snake_to_key:
            matched_key = snake_to_key[field_snake]
            projected[field] = item[matched_key]
            continue

        # 3. Known domain aliases: storyIndex <-> floorIndex
        if field in ("storyIndex", "story_index"):
            if "floorIndex" in item:
                projected["storyIndex"] = item["floorIndex"]
                continue
            if "floor_index" in item:
                projected["storyIndex"] = item["floor_index"]
                continue

        if field in ("floorIndex", "floor_index"):
            if "storyIndex" in item:
                projected["floorIndex"] = item["storyIndex"]
                continue
            if "story_index" in item:
                projected["floorIndex"] = item["story_index"]
                continue

        # 4. Dot-notation (e.g. 'details.geometryType')
        if "." in field:
            parts = field.split(".")
            curr = item
            found = True
            for part in parts:
                if isinstance(curr, dict) and part in curr:
                    curr = curr[part]
                else:
                    found = False
                    break
            if found:
                # Nest structure in projected output
                curr_target = projected
                for part in parts[:-1]:
                    curr_target = curr_target.setdefault(part, {})
                curr_target[parts[-1]] = curr
            continue

        # 5. Fallback lookup inside nested 'details' sub-dictionary
        if "details" in item and isinstance(item["details"], dict):
            details_dict = item["details"]
            if field in details_dict:
                projected[field] = details_dict[field]
                continue
            details_lower = {k.lower(): k for k in details_dict}
            if field_lower in details_lower:
                projected[field] = details_dict[details_lower[field_lower]]
                continue

    return projected


def prune_payload(
    payload: Any,
    fields: list[str] | None,
    list_keys: tuple[str, ...] = (
        "detailsOfElements",
        "elements",
        "properties",
        "classificationItems",
        "geometries3D",
    ),
) -> Any:
    """Prune an Archicad command payload according to the requested fields.

    Works on responses containing lists of element details (e.g. 'detailsOfElements'),
    preserving top-level metadata like pagination tokens.
    """
    if not fields:
        return payload

    if isinstance(payload, dict):
        result = dict(payload)
        found_target_list = False
        for key in list_keys:
            if key in payload and isinstance(payload[key], list):
                found_target_list = True
                result[key] = [
                    project_element(elem, fields) if isinstance(elem, dict) else elem
                    for elem in payload[key]
                ]

        if not found_target_list:
            # If no known list key is present, check if payload itself is a single element dictionary
            return project_element(payload, fields)

        return result

    if isinstance(payload, list):
        return [
            project_element(elem, fields) if isinstance(elem, dict) else elem
            for elem in payload
        ]

    return payload
