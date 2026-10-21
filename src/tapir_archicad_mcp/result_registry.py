"""Local Virtual Set Registry for Archicad elements.

Holds active element GUID collections in RAM and returns opaque set_id tokens.
Prevents transmitting raw GUID arrays to the LLM context.
Features an LRU cache eviction policy (cap at 50 active sets) and optional TTL limits.
"""

from __future__ import annotations

import re
import time
from typing import Any, ClassVar

from mcp.server.mcpserver.exceptions import ToolError

# Process-wide RAM storage for active element sets
STORAGE_SETS: dict[str, list[dict]] = {}


class ResultRegistry:
    """Registry holding element collections in RAM with opaque token handles and LRU eviction."""

    DEFAULT_MAX_CAPACITY: ClassVar[int] = 50
    MAX_CAPACITY: ClassVar[int] = 50
    DEFAULT_TTL_SECONDS: ClassVar[float | None] = None
    TTL_SECONDS: ClassVar[float | None] = None

    _counters: ClassVar[dict[str, int]] = {}
    _timestamps: ClassVar[dict[str, float]] = {}

    @classmethod
    def set_capacity(cls, capacity: int) -> None:
        """Set the maximum number of active sets retained in RAM."""
        if capacity < 1:
            raise ValueError("Capacity must be at least 1.")
        cls.MAX_CAPACITY = capacity
        cls._evict_excess()

    @classmethod
    def set_ttl(cls, ttl_seconds: float | None) -> None:
        """Set the time-to-live in seconds for sets (None disables TTL expiration)."""
        cls.TTL_SECONDS = ttl_seconds
        if ttl_seconds is not None:
            cls.evict_expired()

    @classmethod
    def reset_limits(cls) -> None:
        """Reset capacity and TTL limits to default values."""
        cls.MAX_CAPACITY = cls.DEFAULT_MAX_CAPACITY
        cls.TTL_SECONDS = cls.DEFAULT_TTL_SECONDS

    @classmethod
    def register(cls, elements: list[dict | Any], element_type: str | None = None) -> str:
        """Register a list of element dictionaries and return an opaque set_id handle.

        Example set_id: 'set_walls_01', 'set_columns_02', 'set_elements_01'.
        Evicts the oldest least-recently-used set if the capacity cap is reached.
        """
        # First, purge any expired entries if TTL is active
        if cls.TTL_SECONDS is not None:
            cls.evict_expired()

        # Enforce LRU capacity cap: evict least recently used set(s) before adding new one
        while len(STORAGE_SETS) >= cls.MAX_CAPACITY and len(STORAGE_SETS) > 0:
            oldest_key = next(iter(STORAGE_SETS))
            cls.delete(oldest_key)

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
        cls._timestamps[set_id] = time.time()
        return set_id

    @classmethod
    def get(cls, set_id: str) -> list[dict]:
        """Retrieve the element collection for a given set_id.

        Marks the set as most recently used (LRU update).
        Raises KeyError if the set_id is not found or has expired.
        """
        if set_id not in STORAGE_SETS:
            raise KeyError(f"Set handle '{set_id}' not found or expired.")

        # Check TTL expiration
        if cls.TTL_SECONDS is not None:
            created_at = cls._timestamps.get(set_id, 0.0)
            if time.time() - created_at > cls.TTL_SECONDS:
                cls.delete(set_id)
                raise KeyError(f"Set handle '{set_id}' not found or expired.")

        # Move key to end to mark as most recently used in O(1)
        value = STORAGE_SETS.pop(set_id)
        STORAGE_SETS[set_id] = value
        cls._timestamps[set_id] = time.time()
        return value

    @classmethod
    def get_or_tool_error(cls, set_id: str) -> list[dict]:
        """Retrieve the element collection for a given set_id, raising ToolError on failure."""
        try:
            return cls.get(set_id)
        except KeyError:
            raise ToolError(f"Set handle '{set_id}' not found or expired.") from None

    @classmethod
    def has(cls, set_id: str) -> bool:
        """Check if a set_id exists in the registry and has not expired."""
        if set_id not in STORAGE_SETS:
            return False
        if cls.TTL_SECONDS is not None:
            created_at = cls._timestamps.get(set_id, 0.0)
            if time.time() - created_at > cls.TTL_SECONDS:
                cls.delete(set_id)
                return False
        return True

    @classmethod
    def delete(cls, set_id: str) -> None:
        """Remove a set_id from the registry."""
        STORAGE_SETS.pop(set_id, None)
        cls._timestamps.pop(set_id, None)

    @classmethod
    def clear(cls) -> None:
        """Clear all active sets and reset counters and timestamps."""
        STORAGE_SETS.clear()
        cls._counters.clear()
        cls._timestamps.clear()

    @classmethod
    def count(cls, set_id: str) -> int:
        """Return the number of elements in a set."""
        return len(cls.get(set_id))

    @classmethod
    def evict_expired(cls) -> int:
        """Evict all sets whose age exceeds TTL_SECONDS. Returns number of evicted sets."""
        if cls.TTL_SECONDS is None:
            return 0
        now = time.time()
        expired_keys = [
            sid for sid, ts in list(cls._timestamps.items())
            if now - ts > cls.TTL_SECONDS
        ]
        for sid in expired_keys:
            cls.delete(sid)
        return len(expired_keys)

    @classmethod
    def _evict_excess(cls) -> int:
        """Evict least recently used sets if current count exceeds MAX_CAPACITY."""
        evicted = 0
        while len(STORAGE_SETS) > cls.MAX_CAPACITY:
            oldest_key = next(iter(STORAGE_SETS))
            cls.delete(oldest_key)
            evicted += 1
        return evicted

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
