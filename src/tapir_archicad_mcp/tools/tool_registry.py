import logging
import inspect
from types import UnionType
from typing import Dict, Callable, Any, Type, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, create_model

from multiconn_archicad.constants import DEFAULT_PORT_RANGE

log = logging.getLogger(__name__)


ModelOrUnion = Optional[type | UnionType | type(Union)]


class ToolRegistryEntry(BaseModel):
    """Internal metadata for tool dispatch."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    callable: Callable
    params_model: ModelOrUnion = None
    arguments_model: Type[BaseModel]


TOOL_CALLABLE_REGISTRY: Dict[str, ToolRegistryEntry] = {}
TOOL_DISCOVERY_CATALOG: dict[str, dict[str, Any]] = {}


def _build_tool_arguments_model(name: str, func: Callable, params_model: ModelOrUnion) -> Type[BaseModel]:
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

    if "page_token" in inspect.signature(func).parameters:
        fields["page_token"] = (
            str | None,
            Field(default=None, description="Token for the next page of results (for paginated responses)."),
        )

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
):
    """
    Orchestrates the registration of a tool, populating both the internal
    callable registry and the searchable discovery catalog.
    """
    if name in TOOL_CALLABLE_REGISTRY:
        log.warning(f"Tool {name} already registered. Overwriting.")

    arguments_model = _build_tool_arguments_model(name, func, params_model)
    TOOL_CALLABLE_REGISTRY[name] = ToolRegistryEntry(
        callable=func,
        params_model=params_model,
        arguments_model=arguments_model,
    )

    TOOL_DISCOVERY_CATALOG[name] = {
        "name": name,
        "title": title,
        "description": description,
        "input_schema": arguments_model.model_json_schema(),
    }
    log.debug(f"Registered tool: {name}")


def get_tool_entry(name: str) -> ToolRegistryEntry:
    """Retrieves the registered function and its models."""
    if name not in TOOL_CALLABLE_REGISTRY:
        raise ValueError(f"Tool '{name}' not found in registry.")
    return TOOL_CALLABLE_REGISTRY[name]
