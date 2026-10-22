"""Return base64 images from Archicad as MCP image content, so the model can see them and its context stays small."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from mcp.types import CallToolResult, ImageContent, TextContent

if TYPE_CHECKING:
    # The tools package imports this module while it loads.
    from tapir_archicad_mcp.tools.tool_registry import ToolRegistryEntry


def _reference(number: int) -> str:
    return f"returned as MCP image content #{number}"


def extract_images(entry: ToolRegistryEntry, result: Any) -> tuple[Any, list[str]]:
    """Split an image command's result into the JSON without the images and the base64 image data, in order."""
    if not isinstance(result, dict):
        return result, []

    field = entry.image_field
    if field is not None and isinstance(result.get(field), str):
        return {**result, field: _reference(1)}, [result[field]]

    # Items of an image list are {"image": {"content": <base64>}} or {"error": ...}.
    list_field = entry.image_list_field
    if list_field is not None and isinstance(result.get(list_field), list):
        images: list[str] = []
        items = []
        for item in result[list_field]:
            image = item.get("image") if isinstance(item, dict) else None
            if isinstance(image, dict) and isinstance(image.get("content"), str):
                images.append(image["content"])
                item = {**item, "image": {**image, "content": _reference(len(images))}}
            items.append(item)
        if images:
            return {**result, list_field: items}, images

    return result, []


def image_content(data: str) -> ImageContent:
    # The image commands offer png and jpg (png by default); a JPEG's base64 starts with `/9j/`.
    mime_type = "image/jpeg" if data.startswith("/9j/") else "image/png"
    return ImageContent(type="image", data=data, mime_type=mime_type)


def build_image_result(stripped: Any, images: list[str]) -> CallToolResult:
    """The JSON as text and structured content, followed by one image block per image."""
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(stripped, indent=2)), *map(image_content, images)],
        structured_content=stripped,
    )


def to_tool_result(entry: ToolRegistryEntry, result: Any) -> Any:
    """Wrap an image command's result as a CallToolResult with image content; other results pass through."""
    stripped, images = extract_images(entry, result)
    return build_image_result(stripped, images) if images else result
