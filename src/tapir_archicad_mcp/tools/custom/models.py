from typing import Literal, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

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
    project_path: Optional[str] = Field(
        default=None,
        alias="projectPath",
        description="The full file path or teamwork server location of the project.",
    )
    warning: Optional[str] = Field(
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
