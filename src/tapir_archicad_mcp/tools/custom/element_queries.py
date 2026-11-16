"""Handwritten element queries backed by multiconn's executable query model."""

from mcp.server.mcpserver.exceptions import ToolError
from multiconn_archicad import ConnHeader
from multiconn_archicad.models.tapir.types import ElementIdArrayItem
from multiconn_archicad.utilities.queries import Query
from pydantic import BaseModel, ConfigDict, Field

from tapir_archicad_mcp.tools.tool_registry import register_tool_for_dispatch


class SerializedQuery(Query):
    """Require an explicit version at the MCP boundary, including in its schema."""

    schema_version: str = Field(description="Multiconn query schema version, currently '1.0'.")


class ElementQueryParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: SerializedQuery = Field(description="Executable multiconn query expression with an explicit schema_version.")
    elements: list[ElementIdArrayItem] | None = Field(
        default=None,
        description=(
            "Optional candidate elements to filter instead of searching the floor plan. "
            "Omit or use null to search; an empty array returns no matches. "
            "Supplied order and duplicate matches are preserved."
        ),
    )


def query_elements(conn_header: ConnHeader, params: ElementQueryParameters) -> dict:
    """Return matching IDs using multiconn's search or supplied-element filtering."""
    utilities = conn_header.unified.utilities.element
    try:
        if params.elements is None:
            elements = utilities.find_elements(params.query)
        else:
            elements = utilities.filter_elements_by_query_result(params.elements, params.query).successes
    except ValueError as error:
        # Query versions, metadata references and compatible tests are validated
        # by multiconn. Preserve its actionable message in the normal MCP error.
        raise ToolError(str(error)) from error
    return {"elements": [element.model_dump(mode="json", by_alias=True) for element in elements]}


register_tool_for_dispatch(
    query_elements,
    name="elements_query",
    title="Query Elements",
    description=(
        "Find elements matching a serialized multiconn query: nested AND/OR conditions on element types, "
        "properties and classifications. Searches the floor plan, or filters supplied elements. "
        "Discover property GUIDs and metadata with properties_search_properties; discover classification systems "
        "and items with classification commands. Use the command schema for test kinds, operators and operands. "
        "Numeric quantities use SI units, except angles use degrees. Requires Tapir 2.0.0 or newer. "
        "Returns matching element IDs; per-element evaluation errors are omitted. "
        "Invalid queries and query-wide failures fail the command. Does not change selection."
    ),
    params_model=ElementQueryParameters,
    pagination_field="elements",
)
