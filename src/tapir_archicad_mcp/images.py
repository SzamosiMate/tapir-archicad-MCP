"""Return base64 images from Archicad as MCP image content, so the model can see them and its context stays small."""

from __future__ import annotations

import base64
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import pydantic_core
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
    except ValueError:
        # Not base64 at all, or text with non-ASCII characters. binascii.Error is a ValueError too.
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


def build_result(payload: Any, images: Sequence[ImageContent] = ()) -> CallToolResult:
    """The JSON as text and structured content, followed by one image block per image.

    Text and structured content are made the way the MCP SDK makes them from a returned dict.
    """
    text = pydantic_core.to_json(payload, fallback=str, indent=2).decode()
    return CallToolResult(
        content=[TextContent(type="text", text=text), *images],
        structured_content=pydantic_core.to_jsonable_python(payload, fallback=str),
    )


def to_tool_result(entry: ToolRegistryEntry, result: Any) -> CallToolResult:
    """Wrap a command's result as a CallToolResult; an image command's images become image content."""
    stripped, images = extract_images(entry, result)
    return build_result(stripped, images)
