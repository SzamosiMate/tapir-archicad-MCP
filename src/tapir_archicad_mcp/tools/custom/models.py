from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ProjectType = Literal["teamwork", "solo", "untitled"]
UnavailableReason = Literal["missing_tapir", "unresponsive"]


class ReadyInstance(BaseModel):
    """Information about an active Archicad instance ready to execute commands."""

    model_config = ConfigDict(populate_by_name=True)

    port: int = Field(description="The communication port of the Archicad instance. Pass this to archicad_call_tool.")
    project_name: str = Field(alias="projectName", description="The name of the currently open project.")
    project_type: ProjectType = Field(
        alias="projectType",
        description="The type of the project: 'teamwork', 'solo', or 'untitled'.",
    )
    archicad_version: str = Field(
        alias="archicadVersion",
        description="The major version of Archicad (e.g. '27', '28').",
    )
    tapir_version: str = Field(
        alias="tapirVersion",
        description="The version of the Tapir Add-On installed on this instance.",
    )
    project_path: str | None = Field(
        default=None,
        alias="projectPath",
        description="The full file path or teamwork server location of the project.",
    )
    warning: str | None = Field(
        default=None,
        description="Warning regarding Tapir version differences (e.g., outdated or newer version).",
    )


class UnavailableInstance(BaseModel):
    """Diagnostic information about an Archicad instance that cannot be automated."""

    model_config = ConfigDict(populate_by_name=True)

    reason: UnavailableReason = Field(description="Why the instance is unavailable: 'missing_tapir' or 'unresponsive'.")
    message: str = Field(description="Explanation and actionable troubleshooting advice.")


class DiscoveryResult(BaseModel):
    """The result of scanning for Archicad instances."""

    model_config = ConfigDict(populate_by_name=True)

    active: list[ReadyInstance] = Field(
        default_factory=list,
        alias="activeInstances",
        description="List of ready Archicad instances that can be targeted by commands.",
    )
    unavailable: list[UnavailableInstance] = Field(
        default_factory=list,
        alias="unavailableInstances",
        description="List of detected instances that cannot be targeted, along with diagnostic reasons.",
    )


class CommandOverview(BaseModel):
    """A brief overview of an available Archicad command."""

    name: str = Field(description="The unique, snake-cased name of the tool (e.g., 'elements_get_all_elements').")
    description: str = Field(description="A brief explanation of the tool's function.")


class CommandSchema(BaseModel):
    """The detailed JSON schema required to execute a specific Archicad command."""

    name: str = Field(description="The name of the command.")
    input_schema: dict[str, Any] = Field(description="The JSON schema outlining the required arguments for archicad_call_tool.")


class SetReceipt(BaseModel):
    """Compact summary receipt returned by element queries instead of raw GUID arrays."""

    model_config = ConfigDict(populate_by_name=True)

    set_id: str = Field(alias="setId", description="Opaque token handle referencing the stored element set.")
    count: int = Field(description="The number of elements in the set.")
    element_type: str = Field(alias="elementType", description="The type or category of elements in the set.")


class HighlightElementsInput(BaseModel):
    """Parameters for highlighting elements, supporting targetSetId or explicit elements."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    target_set_id: str | None = Field(
        default=None,
        alias="targetSetId",
        description="Optional target set ID handle referencing an active element collection in ResultRegistry.",
    )
    elements: list[Any] | None = Field(
        default=None,
        description="Explicit list of element IDs to highlight (alternative to targetSetId).",
    )
    highlighted_colors: list[Any] | None = Field(
        default=None,
        alias="highlightedColors",
        description="Colors used for highlighted elements.",
    )
    wireframe_3d: bool | None = Field(
        default=None,
        alias="wireframe3D",
        description="If true, non-highlighted elements will appear as wireframe in 3D.",
    )
    non_highlighted_color: Any | None = Field(
        default=None,
        alias="nonHighlightedColor",
        description="Color used for non-highlighted elements.",
    )


class DeleteElementsInput(BaseModel):
    """Parameters for deleting elements, supporting targetSetId or explicit elements."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    target_set_id: str | None = Field(
        default=None,
        alias="targetSetId",
        description="Optional target set ID handle referencing an active element collection in ResultRegistry.",
    )
    elements: list[Any] | None = Field(
        default=None,
        description="Explicit list of element IDs to delete (alternative to targetSetId).",
    )


class SetPropertyValuesOfElementsInput(BaseModel):
    """Parameters for setting element property values, supporting targetSetId or explicit elementPropertyValues."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    target_set_id: str | None = Field(
        default=None,
        alias="targetSetId",
        description="Optional target set ID handle referencing an active element collection in ResultRegistry.",
    )
    element_property_values: list[Any] | None = Field(
        default=None,
        alias="elementPropertyValues",
        description="Explicit list of element property values to set.",
    )
    property_id: Any | None = Field(
        default=None,
        alias="propertyId",
        description="Property ID to set across all elements in targetSetId.",
    )
    property_value: Any | None = Field(
        default=None,
        alias="propertyValue",
        description="Property value to set across all elements in targetSetId.",
    )
    property_values: list[Any] | None = Field(
        default=None,
        alias="propertyValues",
        description="List of property values to set across all elements in targetSetId.",
    )


class GetDetailsOfElementsInput(BaseModel):
    """Parameters for GetDetailsOfElements with optional field projection."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    elements: list[Any] = Field(
        description="A list of elements.",
    )
    fields: list[str] | None = Field(
        default=None,
        description="Optional filter for fields to return for each element (client-side projection).",
    )


class GetDetailsOfPropertiesInput(BaseModel):
    """Parameters for GetDetailsOfProperties with optional field projection."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    property_ids: list[Any] = Field(
        alias="propertyIds",
        description="A list of property identifiers.",
    )
    fields: list[str] | None = Field(
        default=None,
        description="Optional filter for fields to return for each property.",
    )
