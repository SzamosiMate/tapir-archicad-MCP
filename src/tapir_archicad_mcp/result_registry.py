"""Local Virtual Set Registry for Archicad elements.

Holds active element GUID collections in RAM and returns opaque set_id tokens.
Prevents transmitting raw GUID arrays to the LLM context.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from mcp.server.mcpserver.exceptions import ToolError

# Process-wide RAM storage for active element sets
STORAGE_SETS: dict[str, list[dict]] = {}


class ResultRegistry:
    """Registry holding element collections in RAM with opaque token handles."""

    _counters: ClassVar[dict[str, int]] = {}

    @classmethod
    def register(cls, elements: list[dict | Any], element_type: str | None = None) -> str:
        """Register a list of element dictionaries and return an opaque set_id handle.

        Example set_id: 'set_walls_01', 'set_columns_02', 'set_elements_01'.
        """
        prefix = cls._format_prefix(element_type)
        count = cls._counters.get(prefix, 0) + 1
        cls._counters[prefix] = count
        set_id = f"set_{prefix}_{count:02d}"

        # Ensure elements are normalized dicts
        normalized: list[dict] = []
        for elem in elements:
            if isinstance(elem, dict):
                normalized.append(elem)
            elif hasattr(elem, "model_dump"):
                d = elem.model_dump(by_alias=True)
                if "element_id" in d and "elementId" not in d:
                    d["elementId"] = d.pop("element_id")
                normalized.append(d)
            else:
                normalized.append({"elementId": {"guid": str(elem)}})

        STORAGE_SETS[set_id] = normalized
        return set_id

    @classmethod
    def get(cls, set_id: str) -> list[dict]:
        """Retrieve the element collection for a given set_id.

        Raises KeyError if the set_id is not found or has expired.
        """
        if set_id not in STORAGE_SETS:
            raise KeyError(f"Set handle '{set_id}' not found or expired.")
        return STORAGE_SETS[set_id]

    @classmethod
    def get_or_tool_error(cls, set_id: str) -> list[dict]:
        """Retrieve the element collection for a given set_id, raising ToolError on failure."""
        try:
            return cls.get(set_id)
        except KeyError:
            raise ToolError(f"Set handle '{set_id}' not found or expired.") from None

    @classmethod
    def has(cls, set_id: str) -> bool:
        """Check if a set_id exists in the registry."""
        return set_id in STORAGE_SETS

    @classmethod
    def delete(cls, set_id: str) -> None:
        """Remove a set_id from the registry."""
        STORAGE_SETS.pop(set_id, None)

    @classmethod
    def clear(cls) -> None:
        """Clear all active sets and reset counters."""
        STORAGE_SETS.clear()
        cls._counters.clear()

    @classmethod
    def count(cls, set_id: str) -> int:
        """Return the number of elements in a set."""
        return len(cls.get(set_id))

    @classmethod
    def _format_prefix(cls, element_type: Any | None) -> str:
        """Normalize an element type name into a clean pluralized snake_case token prefix."""
        if element_type is None:
            return "elements"
        if hasattr(element_type, "value"):
            raw_str = str(element_type.value)
        else:
            raw_str = str(element_type)
        cleaned = re.sub(r"[^a-zA-Z0-9_]", "", raw_str).lower()
        if not cleaned:
            return "elements"
        if cleaned in ("selected", "filtered", "classified", "all"):
            return "elements" if cleaned == "all" else cleaned
        if not cleaned.endswith("s"):
            return f"{cleaned}s"
        return cleaned
