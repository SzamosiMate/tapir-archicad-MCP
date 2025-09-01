import logging
import inspect
from typing import Dict, Callable, Any, List, Type, Optional
from pydantic import BaseModel

log = logging.getLogger(__name__)


class ToolRegistryEntry(BaseModel):
    """Internal metadata for tool dispatch."""
    callable: Callable
    params_model: Optional[Type[BaseModel]] = None
    result_model: Optional[Type[BaseModel]] = None


TOOL_CALLABLE_REGISTRY: Dict[str, ToolRegistryEntry] = {}
TOOL_DISCOVERY_CATALOG: List[Dict[str, Any]] = []


def _get_schema_keywords(pydantic_model: Optional[Type[BaseModel]]) -> str:
    """
    Parses a Pydantic model's JSON schema to extract meaningful keywords
    (parameter names and enum values) for better embedding.
    """
    if not pydantic_model:
        return ""
    try:
        schema = pydantic_model.model_json_schema()
        keywords = set()

        def traverse(sub_schema):
            if not isinstance(sub_schema, dict):
                return
            if "properties" in sub_schema:
                for prop_name, prop_details in sub_schema["properties"].items():
                    keywords.add(prop_name)
                    traverse(prop_details)
            if "items" in sub_schema:
                traverse(sub_schema["items"])
            if "enum" in sub_schema:
                for enum_val in sub_schema["enum"]:
                    if isinstance(enum_val, str):
                        keywords.add(enum_val)

        if "$defs" in schema:
            for def_details in schema["$defs"].values():
                traverse(def_details)
        traverse(schema)

        return " ".join(sorted(list(keywords)))
    except Exception as e:
        log.warning(f"Could not generate schema keywords for {pydantic_model.__name__}: {e}")
        return ""


def _build_tool_input_schema(func: Callable, params_model: Optional[Type[BaseModel]]) -> dict:
    """
    Builds the complete JSON schema for the 'arguments' parameter of the
    archicad_call_tool, specific to the tool being registered.
    """
    input_schema = {
        "type": "object",
        "properties": {
            "port": {
                "type": "integer",
                "description": "The target Archicad instance port. Find it with 'discovery_list_active_archicads'."
            }
        },
        "required": ["port"]
    }

    if params_model:
        params_schema = params_model.model_json_schema()
        input_schema["properties"]["params"] = params_schema
        input_schema["required"].append("params")

    sig = inspect.signature(func)
    if 'page_token' in sig.parameters:
        input_schema['properties']['page_token'] = {
            "type": "string",
            "description": "Token for the next page of results (for paginated responses)."
        }

    return input_schema


def register_tool_for_dispatch(
        func: Callable,
        name: str,
        title: str,
        description: str,
        params_model: Optional[Type[BaseModel]] = None,
        result_model: Optional[Type[BaseModel]] = None
):
    """
    Orchestrates the registration of a tool, populating both the internal
    callable registry and the searchable discovery catalog.
    """
    if name in TOOL_CALLABLE_REGISTRY:
        log.warning(f"Tool {name} already registered. Overwriting.")

    TOOL_CALLABLE_REGISTRY[name] = ToolRegistryEntry(
        callable=func,
        params_model=params_model,
        result_model=result_model
    )

    input_schema = _build_tool_input_schema(func, params_model)
    schema_keywords = _get_schema_keywords(params_model)

    TOOL_DISCOVERY_CATALOG.append({
        "name": name,
        "title": title,
        "description": description,
        "input_schema": input_schema,
        "schema_keywords": schema_keywords,
    })
    log.debug(f"Registered tool: {name}")


def get_tool_entry(name: str) -> ToolRegistryEntry:
    """Retrieves the registered function and its models."""
    if name not in TOOL_CALLABLE_REGISTRY:
        raise ValueError(f"Tool '{name}' not found in registry.")
    return TOOL_CALLABLE_REGISTRY[name]