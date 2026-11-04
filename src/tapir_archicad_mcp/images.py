"""Return base64 images from Archicad as MCP image content, so the model can see them and its context stays small."""

from __future__ import annotations

import base64
import json
from collections.abc import Sequence
from typing import TYPE_CHECKING

from mcp.types import CallToolResult, ImageContent, TextContent
from pydantic import JsonValue

if TYPE_CHECKING:
    # The tools package imports this module while it loads.
    from tapir_archicad_mcp.tools.tool_registry import ToolRegistryEntry


def _reference(number: int) -> str:
    return f"returned as MCP image content #{number}"


def _image_content(data: JsonValue) -> ImageContent | None:
    # The image commands offer png and jpg. Anything else stays in the JSON, so a client never gets a broken image.
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


def extract_images(
    entry: ToolRegistryEntry, result: dict[str, JsonValue]
) -> tuple[dict[str, JsonValue], list[ImageContent]]:
    """Split an image command's result into the JSON without the images and the image blocks, in order."""
    replacements: dict[str, JsonValue] = {}
    images: list[ImageContent] = []
    fields = (entry.image_field,) if isinstance(entry.image_field, str) else entry.image_field or ()
    for field in fields:
        if (image := _image_content(result.get(field))) is not None:
            images.append(image)
            replacements[field] = _reference(len(images))

    list_fields = (entry.image_list_field,) if isinstance(entry.image_list_field, str) else entry.image_list_field or ()
    for field in list_fields:
        values = result.get(field)
        if not isinstance(values, list):
            continue
        previous_count = len(images)
        items = []
        for item in values:
            # Library pictures are strings. Profile previews also carry metadata and error items.
            if isinstance(item, str) and (image := _image_content(item)) is not None:
                images.append(image)
                item = _reference(len(images))
            elif (
                isinstance(item, dict)
                and isinstance(content := item.get("image"), dict)
                and (image := _image_content(content.get("content"))) is not None
            ):
                images.append(image)
                item = {**item, "image": {**content, "content": _reference(len(images))}}
            items.append(item)
        if len(images) > previous_count:
            replacements[field] = items

    return ({**result, **replacements} if replacements else result), images


def build_result(payload: dict[str, JsonValue], images: Sequence[ImageContent] = ()) -> CallToolResult:
    """Render a JSON object as text and structured content, followed by its image blocks."""
    text = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)
    return CallToolResult(
        content=[TextContent(type="text", text=text), *images],
        structured_content=payload,
    )


def to_tool_result(entry: ToolRegistryEntry, result: dict[str, JsonValue]) -> CallToolResult:
    """Wrap a command's result as a CallToolResult; an image command's images become image content."""
    stripped, images = extract_images(entry, result)
    return build_result(stripped, images)
