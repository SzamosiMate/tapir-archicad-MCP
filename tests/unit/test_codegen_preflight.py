"""Preflight image checks follow the extractor's supported response contracts."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

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


@pytest.mark.parametrize("extra_source", ["custom.element_queries", "generated.tapir.stale"])
def test_generated_check_distinguishes_custom_tools_from_stale_generated_tools(tmp_path, monkeypatch, extra_source):
    output = tmp_path / "tapir"
    output.mkdir()
    module = "tapir_archicad_mcp.tools.generated.tapir.element_commands"
    (output / "__init__.py").write_text(f"from {module} import *\n")
    (output / "element_commands.py").write_text('register_tool_for_dispatch(read, name="elements_read")\n')
    config = SimpleNamespace(name="tapir", output_dir=output, paginated_commands={}, image_fields={}, image_lists={})
    expected = {"elements_read": {"source": "tapir", "title": "Read", "module": "element_commands"}}
    entry = SimpleNamespace(
        callable=SimpleNamespace(__module__=module),
        params_model=None,
        pagination_field=None,
        image_field=None,
        image_list_field=None,
    )
    schemas = []
    registry = SimpleNamespace(
        TOOL_CALLABLE_REGISTRY={
            "elements_read": entry,
            "elements_query": SimpleNamespace(
                callable=SimpleNamespace(__module__=f"tapir_archicad_mcp.tools.{extra_source}")
            ),
        },
        TOOL_DISCOVERY_CATALOG={"elements_read": {"title": "Read"}},
        get_tool_input_schema=schemas.append,
    )
    monkeypatch.setattr(
        preflight.importlib,
        "import_module",
        lambda name: registry if name.endswith("tool_registry") else SimpleNamespace(),
    )

    if extra_source.startswith("generated."):
        with pytest.raises(preflight.PreflightError, match="Runtime registry differs"):
            preflight.validate_generated({"models": {"tapir": []}}, [config], expected)
        assert schemas == []
    else:
        assert preflight.validate_generated({"models": {"tapir": []}}, [config], expected) == 1
        assert schemas == ["elements_read"]
