"""Return base64 images from Archicad as MCP image content, so the model can see them and its context stays small."""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING

from mcp.types import CallToolResult, ImageContent, TextContent
from pydantic import JsonValue

if TYPE_CHECKING:
    # The tools package imports this module while it loads.
    from tapir_archicad_mcp.tools.tool_registry import ToolRegistryEntry


def _image_content(data: JsonValue) -> ImageContent | None:
    # Emit recognized PNG/JPEG content; other formats stay in JSON for the caller to handle.
    if not isinstance(data, str):
        return None
    try:
        head = base64.b64decode(data, validate=True)[:8]
    except ValueError:
        # Not base64 at all, or text with non-ASCII characters. binascii.Error is a ValueError too.
        return None
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ImageContent(type="image", data=data, mime_type="image/png")
    if head.startswith(b"\xff\xd8\xff"):
        return ImageContent(type="image", data=data, mime_type="image/jpeg")
    return None


def retain_images(entry: ToolRegistryEntry, result: dict[str, JsonValue]) -> dict:
    """Keep supported images as native media nodes inside the stored result."""
    replacements = {}
    fields = (entry.image_field,) if isinstance(entry.image_field, str) else entry.image_field or ()
    for field in fields:
        if (image := _image_content(result.get(field))) is not None:
            replacements[field] = image

    list_fields = (entry.image_list_field,) if isinstance(entry.image_list_field, str) else entry.image_list_field or ()
    for field in list_fields:
        values = result.get(field)
        if not isinstance(values, list):
            continue
        items = []
        changed = False
        for item in values:
            # Library pictures are strings; converted images and profile previews use wrappers.
            marked = item
            if isinstance(item, str) and (image := _image_content(item)) is not None:
                marked = image
            elif isinstance(item, dict) and (image := _image_content(item.get("image"))) is not None:
                marked = {**item, "image": image}
            elif (
                isinstance(item, dict)
                and isinstance(content := item.get("image"), dict)
                and (image := _image_content(content.get("content"))) is not None
            ):
                marked = {**item, "image": {**content, "content": image}}
            changed = changed or marked is not item
            items.append(marked)
        if changed:
            replacements[field] = items

    return {**result, **replacements} if replacements else result


def build_result(payload: dict[str, JsonValue]) -> CallToolResult:
    """Render a small control response as text and structured content."""
    text = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=payload,
    )
