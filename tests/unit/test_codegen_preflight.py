"""Preflight image checks follow the extractor's supported response contracts."""

import importlib.util
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "codegen_preflight",
    Path(__file__).resolve().parents[2] / ".agents/skills/tapir-mcp-codegen/scripts/codegen_preflight.py",
)
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)

from generate_tools import _generate_tool_function_code
from generator_config import TAPIR_CONFIG
from metadata_check import review_fingerprint, validate_source

from tapir_archicad_mcp.command_metadata import COMMAND_METADATA
from tapir_archicad_mcp.metadata_types import CommandMetadata, Positional, Presentation
from tapir_archicad_mcp.tools.tool_registry import get_tool_entry


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


def test_metadata_review_detects_added_removed_changed_and_stale_paths():
    commands = {"Example": {"group": "Element Commands", "description": "One ordered result per input."}}
    document = {
        "$defs": {
            "ExampleParameters": {"properties": {"keys": {"type": "array", "items": {"type": "string"}}}},
            "ExampleResult": {"properties": {"items": {"type": "array", "items": {"$ref": "#/$defs/Item"}}}},
            "Item": {"type": "string"},
        }
    }
    contract = CommandMetadata(
        Presentation.HANDLE_PREFERRED,
        positional=Positional("keys", "items", ()),
        reviewed=review_fingerprint("Example", commands["Example"], document),
    )
    table = {("tapir", "Example"): contract}
    validate_source("tapir", commands, document, table)
    with pytest.raises(ValueError, match="Missing.*Added"):
        validate_source("tapir", {**commands, "Added": commands["Example"]}, document, table)
    with pytest.raises(ValueError, match="Stale.*Example"):
        validate_source("tapir", {}, document, table)
    with pytest.raises(ValueError, match="Missing.*Example"):
        validate_source("tapir", commands, document, {})
    changed = deepcopy(document)
    changed["$defs"]["Item"]["type"] = "number"
    with pytest.raises(ValueError, match="referenced models need review"):
        validate_source("tapir", commands, changed, table)
    described = {"Example": {**commands["Example"], "description": "Returns matching items."}}
    with pytest.raises(ValueError, match="description.*need review"):
        validate_source("tapir", described, document, table)
    stale = replace(contract, positional=replace(contract.positional, input_field="missing"))
    with pytest.raises(ValueError, match="list at 'missing'"):
        validate_source("tapir", commands, document, {("tapir", "Example"): stale})


def test_generated_wrapper_registers_result_model_and_shared_reviewed_metadata():
    name = "RefreshElements"
    models = {name + "Parameters", name + "Result"}
    wrapper = _generate_tool_function_code(
        {"name_camel": name, "name_for_api": name, "group": "Element Commands", "description": "Refresh elements."},
        models,
        TAPIR_CONFIG,
    )
    assert 'identity=("tapir", "RefreshElements")' in wrapper
    assert "output_model=RefreshElementsResult" in wrapper
    entry = get_tool_entry("elements_refresh_elements")
    assert entry.metadata is COMMAND_METADATA["tapir", name]
    assert entry.metadata.positional.output_field == "executionResults"
    assert entry.metadata.presentation is Presentation.HANDLE_PREFERRED
