from typing import Literal, Optional
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
        allow_population_by_field_name = True