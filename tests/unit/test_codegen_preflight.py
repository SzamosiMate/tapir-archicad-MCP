"""Preflight image checks follow the extractor's supported response contracts."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "codegen_preflight",
    Path(__file__).resolve().parents[2] / ".agents/skills/tapir-mcp-codegen/scripts/codegen_preflight.py",
)
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


@pytest.mark.parametrize(
    ("image", "supported"),
    [
        ({"type": "string"}, True),
        ({"type": "object", "properties": {"content": {"type": "string"}}}, True),
        ({"type": "integer"}, False),
        ({"type": "object", "properties": {"path": {"type": "string"}}}, False),
    ],
)
def test_image_list_wrappers_can_be_extracted(image, supported):
    schema = {
        "type": "array",
        "items": {
            "oneOf": [
                {"type": "object", "properties": {"image": image}},
                {"type": "object", "properties": {"error": {"type": "object"}}},
            ]
        },
    }
    assert bool(preflight.is_image_list(schema, {})) is supported
