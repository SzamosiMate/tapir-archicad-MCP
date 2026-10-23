"""Return base64 images from Archicad as MCP image content, so the model can see them and its context stays small."""

from __future__ import annotations

import base64
import binascii
import json
from typing import TYPE_CHECKING, Any

from mcp.types import CallToolResult, ImageContent, TextContent

if TYPE_CHECKING:
    # The tools package imports this module while it loads.
    from tapir_archicad_mcp.tools.tool_registry import ToolRegistryEntry


def _reference(number: int) -> str:
    return f"returned as MCP image content #{number}"


def _image_content(data: Any) -> ImageContent | None:
    # The image commands offer png and jpg. Anything else stays in the JSON, so a client never gets a broken image.
    if not isinstance(data, str):
        return None
    try:
        head = base64.b64decode(data, validate=True)[:8]
    except binascii.Error:
        return None
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ImageContent(type="image", data=data, mime_type="image/png")
    if head.startswith(b"\xff\xd8\xff"):
        return ImageContent(type="image", data=data, mime_type="image/jpeg")
    return None


def extract_images(entry: ToolRegistryEntry, result: Any) -> tuple[Any, list[ImageContent]]:
    """Split an image command's result into the JSON without the images and the image blocks, in order."""
    if not isinstance(result, dict):
        return result, []

    field = entry.image_field
    if field is not None and (image := _image_content(result.get(field))) is not None:
        return {**result, field: _reference(1)}, [image]

    # Items of an image list are {"image": {"content": <base64>}} or {"error": ...}.
    list_field = entry.image_list_field
    if list_field is not None and isinstance(result.get(list_field), list):
        images: list[ImageContent] = []
        items = []
        for item in result[list_field]:
            content = item.get("image") if isinstance(item, dict) else None
            if isinstance(content, dict) and (image := _image_content(content.get("content"))) is not None:
                images.append(image)
                item = {**item, "image": {**content, "content": _reference(len(images))}}
            items.append(item)
        if images:
            return {**result, list_field: items}, images

    return result, []


def build_image_result(stripped: Any, images: list[ImageContent]) -> CallToolResult:
    """The JSON as text and structured content, followed by one image block per image."""
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(stripped, indent=2, ensure_ascii=False)), *images],
        structured_content=stripped,
    )


def to_tool_result(entry: ToolRegistryEntry, result: Any) -> Any:
    """Wrap an image command's result as a CallToolResult with image content; other results pass through."""
    stripped, images = extract_images(entry, result)
    return build_image_result(stripped, images) if images else result
