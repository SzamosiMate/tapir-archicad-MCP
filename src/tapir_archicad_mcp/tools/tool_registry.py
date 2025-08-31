import logging
import inspect
from typing import Dict, Callable, Any, List, Type, Optional
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class ToolRegistryEntry(BaseModel):
    """Internal metadata for tool dispatch."""
    callable: Callable
    params_model: Optional[Type[BaseModel]] = None
    result_model: Optional[Type[BaseModel]] = None


TOOL_CALLABLE_REGISTRY: Dict[str, ToolRegistryEntry] = {}
TOOL_DISCOVERY_CATALOG: List[Dict[str, Any]] = []


def register_tool_for_dispatch(
        func: Callable,
        name: str,
        title: str,
        description: str,
        params_model: Optional[Type[BaseModel]] = None,
        result_model: Optional[Type[BaseModel]] = None
):
    """
    Registers the tool function and its associated Pydantic models for direct call dispatch.
    This is called implicitly when generated modules are imported.
    """
    if name in TOOL_CALLABLE_REGISTRY:
        log.warning(f"Tool {name} already registered. Overwriting.")

    # 1. Register callable and models
    TOOL_CALLABLE_REGISTRY[name] = ToolRegistryEntry(
        callable=func,
        params_model=params_model,
        result_model=result_model
    )

    # 2. Build a complete and accurate JSON schema for the 'arguments' of archicad_call_tool
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

    # If the tool has parameters, add their full schema
    if params_model:
        params_schema = params_model.model_json_schema()
        input_schema["properties"]["params"] = params_schema
        input_schema["required"].append("params")

    # If the function signature includes 'page_token', add it to the schema
    sig = inspect.signature(func)
    if 'page_token' in sig.parameters:
        input_schema['properties']['page_token'] = {
            "type": "string",
            "description": "Token for the next page of results (for paginated responses)."
        }

    TOOL_DISCOVERY_CATALOG.append({
        "name": name,
        "title": title,
        "description": description,
        "input_schema": input_schema,
    })
    log.debug(f"Registered tool: {name}")


def get_tool_entry(name: str) -> ToolRegistryEntry:
    """Retrieves the registered function and its models."""
    if name not in TOOL_CALLABLE_REGISTRY:
        raise ValueError(f"Tool '{name}' not found in registry.")
    return TOOL_CALLABLE_REGISTRY[name]
