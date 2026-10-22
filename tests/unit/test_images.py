import base64
import json

import pytest
from mcp.types import CallToolResult

from tapir_archicad_mcp.images import to_tool_result
from tapir_archicad_mcp.tools.custom.functions import archicad_call_tool, archicad_get_job
from tapir_archicad_mcp.tools.tool_registry import TOOL_CALLABLE_REGISTRY, get_tool_entry, register_tool_for_dispatch

# 1x1 PNG
PNG_B64 = base64.b64encode(
    bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c6360000002000001e221bc330000000049454e44ae426082"
    )
).decode()
JPG_B64 = base64.b64encode(b"\xff\xd8\xff\xe0" + b"\x00" * 16).decode()
PREVIEW_ARGS = {"port": 19723, "params": {"elementId": {"guid": "00000000-0000-0000-0000-000000000001"}}}
pytestmark = pytest.mark.asyncio


@pytest.fixture
def snapshot_command(fake_archicad):
    register_tool_for_dispatch(
        lambda conn_header: {"snapshot": PNG_B64, "width": 1},
        name="test_snapshot",
        title="TestSnapshot",
        description="Test-only image command.",
        image_field="snapshot",
    )
    yield "test_snapshot"
    TOOL_CALLABLE_REGISTRY.pop("test_snapshot")


async def test_image_mapping_comes_from_the_registry(snapshot_command):
    result = await archicad_call_tool(snapshot_command, {"port": 19723})

    assert isinstance(result, CallToolResult)
    assert [block.type for block in result.content] == ["text", "image"]
    assert result.content[1].data == PNG_B64
    assert result.structured_content == {"snapshot": "returned as MCP image content #1", "width": 1}
    assert PNG_B64 not in result.content[0].text


@pytest.mark.parametrize(("data", "mime_type"), [(PNG_B64, "image/png"), (JPG_B64, "image/jpeg")])
async def test_png_and_jpeg_mime_types(fake_archicad, data, mime_type):
    fake_archicad.on_tapir_command("GetElementPreviewImage", {"previewImage": data})

    result = await archicad_call_tool("elements_get_element_preview_image", PREVIEW_ARGS)

    assert result.content[1].mime_type == mime_type


async def test_profile_previews_keep_errors_and_number_images(fake_archicad):
    result = {
        "previewImages": [
            {"image": {"content": PNG_B64}},
            {"error": {"code": 1, "message": "Not a profile."}},
            {"image": {"content": JPG_B64}},
        ]
    }

    converted = to_tool_result(get_tool_entry("attributes_get_profile_attribute_preview"), result)

    assert [block.type for block in converted.content] == ["text", "image", "image"]
    assert [block.data for block in converted.content[1:]] == [PNG_B64, JPG_B64]
    assert converted.structured_content == {
        "previewImages": [
            {"image": {"content": "returned as MCP image content #1"}},
            {"error": {"code": 1, "message": "Not a profile."}},
            {"image": {"content": "returned as MCP image content #2"}},
        ]
    }


async def test_non_image_results_are_unchanged(fake_archicad):
    fake_archicad.on_tapir_command("GetAddOnVersion", {"version": "1.7.2"})

    result = await archicad_call_tool("app_get_add_on_version", {"port": 19723})

    assert result == {"version": "1.7.2"}


async def test_job_result_of_an_image_command_is_image_content(fake_archicad):
    fake_archicad.on_tapir_command("GetElementPreviewImage", {"previewImage": PNG_B64})
    await archicad_call_tool("elements_get_element_preview_image", PREVIEW_ARGS)
    handle = (await archicad_get_job())["jobs"][0]["jobHandle"]

    result = await archicad_get_job(handle)

    assert isinstance(result, CallToolResult)
    assert result.content[1].data == PNG_B64
    assert result.structured_content["jobHandle"] == handle
    assert result.structured_content["status"] == "completed"
    assert PNG_B64 not in json.dumps(result.structured_content)
