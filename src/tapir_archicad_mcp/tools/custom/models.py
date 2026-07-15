from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

ProjectType = Literal["teamwork", "solo", "untitled"]

class ArchicadInstanceInfo(BaseModel):
    """A curated model to hold key information about a running Archicad instance."""
    port: int = Field(description="The communication port of the Archicad instance. Use this to target commands.")
    project_name: str = Field(alias="projectName", description="The name of the project file currently open in the instance.")
    project_type: ProjectType = Field(alias="projectType", description="The type of the project: 'teamwork', 'solo', or 'untitled'.")
    archicad_version: str = Field(alias="archicadVersion", description="The major version of the Archicad application (e.g., '27').")
    project_path: Optional[str] = Field(None, alias="projectPath", description="The full file path of the project, if it is a saved solo or teamwork project.")

    class Config:
        validate_by_name = True


class CommandOverview(BaseModel):
    """A brief overview of an available Archicad command."""
    name: str = Field(description="The unique, snake-cased name of the tool (e.g., 'elements_get_all_elements'). Use this in archicad_get_command_schema.")
    description: str = Field(description="A brief explanation of the tool's function.")


class CommandSchema(BaseModel):
    """The detailed JSON schema required to execute a specific Archicad command."""
    name: str = Field(description="The name of the command.")
    input_schema: dict[str, Any] = Field(description="The JSON schema outlining the required arguments for archicad_call_tool.")