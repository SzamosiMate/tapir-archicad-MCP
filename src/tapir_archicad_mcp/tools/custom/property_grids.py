"""Property grid reads and sparse writes using multiconn's result utilities."""

from mcp.server.mcpserver.exceptions import ToolError
from multiconn_archicad import ConnHeader
from multiconn_archicad.errors import MulticonnArchicadError
from multiconn_archicad.models.tapir.types import ElementIdArrayItem, PropertyIdArrayItem, SuccessfulExecutionResult
from multiconn_archicad.utilities.identifiers import normalize_element_ids, normalize_property_ids
from multiconn_archicad.utilities.results.batch_results import BatchGrid
from pydantic import BaseModel, ConfigDict, Field, InstanceOf
from pydantic.json_schema import SkipJsonSchema

from tapir_archicad_mcp.result_data import MatrixData, MatrixResult
from tapir_archicad_mcp.tools.tool_registry import register_tool_for_dispatch


class PropertyAxes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    elements: list[ElementIdArrayItem] = Field(description="Ordered element IDs, including duplicates, for the rows.")
    properties: list[PropertyIdArrayItem] = Field(min_length=1, description="Ordered property IDs for the columns.")


class ReadPropertyGrid(PropertyAxes):
    useSIUnits: bool = Field(False, description="Return SI-formatted quantity strings, with angles in degrees.")


class LiteralGrid(PropertyAxes):
    values: list[list[str | int | float | bool | None]] = Field(
        description="Values by element row and property column. Null writes an empty string."
    )


class WritePropertyGrid(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grid: LiteralGrid | SkipJsonSchema[InstanceOf[MatrixResult]] = Field(
        description="A literal values grid or a reference to the root of a retained property read grid."
    )


class PropertyReadData(MatrixData[ElementIdArrayItem, PropertyIdArrayItem, str]):
    useSIUnits: bool = Field(description="SI quantities use degrees for angles. Property values remain strings.")


def read_property_grid(conn_header: ConnHeader, params: ReadPropertyGrid) -> MatrixResult:
    elements = normalize_element_ids(params.elements)
    properties = normalize_property_ids(params.properties)
    try:
        grid = (
            conn_header.unified.utilities.property.get_property_values_per_element_result(
                elements, properties, use_si_units=params.useSIUnits
            )
            if elements
            else BatchGrid.from_rows([], width=len(properties))
        )
    except MulticonnArchicadError as exc:
        if type(exc) is MulticonnArchicadError:
            raise ToolError(str(exc)) from None
        raise
    return MatrixResult(elements, properties, grid, params.useSIUnits)


def write_property_grid(conn_header: ConnHeader, params: WritePropertyGrid) -> MatrixResult:
    source = params.grid
    elements = normalize_element_ids(source.elements)
    properties = normalize_property_ids(source.properties)
    values = source.grid if isinstance(source, MatrixResult) else source.values
    try:
        grid = conn_header.unified.utilities.property.set_property_values_per_element_sparse_result(
            elements, properties, values
        )
    except ValueError as exc:
        raise ToolError(str(exc)) from None
    return MatrixResult(elements, properties, grid)


register_tool_for_dispatch(
    read_property_grid,
    name="properties_read_grid",
    title="Read Property Grid",
    description=(
        "Read property strings as a grid with ordered element rows and property columns. Keeps failed rows and cells, "
        "including undefined and unavailable values. SI formatting is optional. Request resultMode='handle' to pass "
        "the grid to properties_write_grid or inspect it using result_read."
    ),
    params_model=ReadPropertyGrid,
    output_model=PropertyReadData,
    identity=("custom", "ReadPropertyGrid"),
)

register_tool_for_dispatch(
    write_property_grid,
    name="properties_write_grid",
    title="Write Property Grid",
    description=(
        "Write a literal property grid, or pass the root of a retained properties_read_grid result as grid. "
        "Attempts successful cells only, retains both axes and aligns write acknowledgements and errors to "
        "the source cells. Successful writes are kept when another cell fails."
    ),
    params_model=WritePropertyGrid,
    output_model=MatrixData[ElementIdArrayItem, PropertyIdArrayItem, SuccessfulExecutionResult],
    identity=("custom", "WritePropertyGrid"),
)
