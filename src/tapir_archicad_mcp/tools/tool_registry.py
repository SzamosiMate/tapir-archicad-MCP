import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from importlib import import_module
from types import UnionType
from typing import Any, Union

from mcp.server.mcpserver.exceptions import ToolError
from multiconn_archicad.constants import DEFAULT_PORT_RANGE
from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, TypeAdapter, create_model

from tapir_archicad_mcp.command_metadata import COMMAND_METADATA
from tapir_archicad_mcp.metadata_types import CommandMetadata, Presentation
from tapir_archicad_mcp.references import ResultReference
from tapir_archicad_mcp.result_data import Failure, Skipped

log = logging.getLogger(__name__)


ModelOrUnion = type | UnionType | type(Union) | None


@dataclass(frozen=True)
class ToolRegistryEntry:
    """Internal metadata for tool dispatch."""

    callable: Callable
    arguments_model: type[BaseModel]
    metadata: CommandMetadata
    identity: tuple[str, str] | None = None
    params_model: ModelOrUnion = None
    output_model: ModelOrUnion = None
    error_adapters: dict[str, tuple[TypeAdapter, ...]] = field(default_factory=dict)
    image_field: str | tuple[str, ...] | None = None
    image_list_field: str | tuple[str, ...] | None = None


TOOL_CALLABLE_REGISTRY: dict[str, ToolRegistryEntry] = {}
TOOL_DISCOVERY_CATALOG: dict[str, dict[str, Any]] = {}
_TOOL_INPUT_SCHEMA_CACHE: dict[str, dict[str, Any]] = {}
_TOOL_OUTPUT_SCHEMA_CACHE: dict[str, dict[str, Any]] = {}


def _build_tool_arguments_model(name: str, params_model: ModelOrUnion) -> type[BaseModel]:
    """Build the runtime and discovery model for one command's arguments envelope."""
    fields: dict[str, tuple[Any, Any]] = {
        "port": (
            int,
            Field(
                ...,
                ge=DEFAULT_PORT_RANGE.start,
                lt=DEFAULT_PORT_RANGE.stop,
                description="The target Archicad instance port. Find it with 'discovery_list_active_archicads'.",
            ),
        )
    }

    if params_model:
        fields["params"] = (params_model, Field(...))

    return create_model(
        f"{name.title().replace('_', '')}Arguments",
        __config__=ConfigDict(extra="forbid"),
        **fields,
    )


def register_tool_for_dispatch(
    func: Callable,
    name: str,
    title: str,
    description: str,
    params_model: ModelOrUnion = None,
    output_model: ModelOrUnion = None,
    metadata: CommandMetadata | None = None,
    identity: tuple[str, str] | None = None,
    error_adapters: dict[str, tuple[TypeAdapter, ...]] | None = None,
    image_field: str | tuple[str, ...] | None = None,
    image_list_field: str | tuple[str, ...] | None = None,
):
    """
    Orchestrates the registration of a tool, populating both the internal
    callable registry and the searchable discovery catalog.
    """
    if name in TOOL_CALLABLE_REGISTRY:
        log.warning(f"Tool {name} already registered. Overwriting.")

    if identity is not None:
        metadata = COMMAND_METADATA[identity]
        fields = {item.field: item.error_types for item in metadata.outcome_lists}
        if positional := metadata.positional:
            fields[positional.output_field] = positional.error_types
        if fields:
            types = import_module(f"multiconn_archicad.models.{identity[0]}.types")
            error_adapters = {
                field: tuple(TypeAdapter(getattr(types, error)) for error in errors) for field, errors in fields.items()
            }
    arguments_model = _build_tool_arguments_model(name, params_model)
    _TOOL_INPUT_SCHEMA_CACHE.pop(name, None)
    _TOOL_OUTPUT_SCHEMA_CACHE.pop(name, None)
    TOOL_CALLABLE_REGISTRY[name] = ToolRegistryEntry(
        callable=func,
        params_model=params_model,
        arguments_model=arguments_model,
        output_model=output_model,
        metadata=metadata or CommandMetadata(Presentation.SIZE_BASED),
        identity=identity,
        error_adapters=error_adapters or {},
        image_field=image_field,
        image_list_field=image_list_field,
    )

    TOOL_DISCOVERY_CATALOG[name] = {
        "name": name,
        "title": title,
        "description": description,
    }
    log.debug(f"Registered tool: {name}")


def get_tool_input_schema(name: str) -> dict[str, Any]:
    """
    Returns a tool's argument JSON schema, building it on first request.

    The catalog spans hundreds of commands, and generating every schema up
    front costs a measurable slice of server startup while the discovery
    workflow asks for exactly one command's schema at a time; build lazily and
    cache so repeat lookups stay cheap.
    """
    schema = _TOOL_INPUT_SCHEMA_CACHE.get(name)
    if schema is None:
        schema = get_tool_entry(name).arguments_model.model_json_schema()
        if "params" in schema["properties"]:

            def with_reference(node):
                return {"anyOf": [node, {"$ref": "#/$defs/TapirResultReference"}]}

            def add_references(node):
                for item in node.get("properties", {}).values():
                    add_references(item)
                if "properties" in node:
                    node["properties"] = {key: with_reference(item) for key, item in node["properties"].items()}
                for key in ("items", "additionalProperties"):
                    if isinstance(node.get(key), dict):
                        add_references(node[key])
                        node[key] = with_reference(node[key])
                for key in ("anyOf", "oneOf", "allOf", "prefixItems"):
                    for item in node.get(key, ()):
                        add_references(item)
                    if key == "prefixItems" and key in node:
                        node[key] = [with_reference(item) for item in node[key]]

            defs = schema.setdefault("$defs", {})
            for definition in defs.values():
                add_references(definition)
            params = schema["properties"]["params"]
            add_references(params)
            schema["properties"]["params"] = with_reference(params)
            defs["TapirResultReference"] = ResultReference.model_json_schema()
        _TOOL_INPUT_SCHEMA_CACHE[name] = schema
    return schema


def get_tool_output_schema(name: str) -> dict[str, Any]:
    if name in _TOOL_OUTPUT_SCHEMA_CACHE:
        return _TOOL_OUTPUT_SCHEMA_CACHE[name]
    entry = get_tool_entry(name)
    # Upstream wire serializers are annotated Any. Their validation schemas
    # describe the actual raw JSON fields returned by the wrappers.
    schema = (
        TypeAdapter(entry.output_model).json_schema()
        if entry.output_model
        else {
            "type": "object",
            "description": "Command result. The upstream release does not supply a more specific result model.",
        }
    )
    if contract := entry.metadata.positional:
        field = schema["properties"][contract.output_field]
        raw_item = field["items"]
        raw_options = raw_item.get("anyOf", [raw_item])
        successes = [
            item for item in raw_options if item.get("$ref", "").rsplit("/", 1)[-1] not in contract.error_types
        ]
        value = successes[0] if len(successes) == 1 else {"anyOf": successes}
        alternatives = [
            {
                "type": "object",
                "properties": {
                    "coordinate": {"type": "integer", "minimum": 0},
                    "state": {"const": "success"},
                    "value": value,
                },
                "required": ["coordinate", "state", "value"],
            }
        ]
        defs = schema.setdefault("$defs", {})
        for partial in contract.partial_output_types:
            defs[partial].pop("required", None)
        for model in (Failure[NonNegativeInt], Skipped[NonNegativeInt]):
            outcome = model.model_json_schema(ref_template="#/$defs/TapirResult{model}")
            defs.update({"TapirResult" + key: item for key, item in outcome.pop("$defs", {}).items()})
            alternatives.append(outcome)
        field["items"] = {"oneOf": alternatives}
        field["description"] = (
            "One outcome at each original position. Referencing this field forwards successful values. "
            "Use view=inputs to forward successful originating inputs where available."
        )
    _TOOL_OUTPUT_SCHEMA_CACHE[name] = schema
    return schema


def get_tool_entry(name: str) -> ToolRegistryEntry:
    """Retrieves the registered function and its models."""
    if name not in TOOL_CALLABLE_REGISTRY:
        raise ToolError(f"Tool '{name}' not found in registry.")
    return TOOL_CALLABLE_REGISTRY[name]
