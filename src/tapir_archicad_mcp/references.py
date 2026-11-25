"""Explicit same-process result accessors."""

from collections.abc import Mapping
from typing import Annotated, Any, Literal

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, ConfigDict, Field, StrictStr

from tapir_archicad_mcp.result_data import is_sequence

Index = Annotated[int, Field(strict=True, ge=0)]
Path = Annotated[list[StrictStr | Index], Field(max_length=64)]


class ResultReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    handle: str = Field(alias="$handle", pattern=r"^result:", max_length=100, description="A retained resultHandle.")
    path: Path = Field(default_factory=list, description="Field names and zero-based indices. Omit for the root.")
    view: Literal["output", "inputs"] = Field(
        "output",
        description=(
            "Select output values, or successful originating inputs for a positional result. "
            "Select the positional result field to forward its successful items with their alignment."
        ),
    )


def select(root: Any, path: list[str | int] | tuple) -> Any:
    current = root
    for index, part in enumerate(path):
        if (
            isinstance(part, str)
            and isinstance(current, Mapping)
            and part in current
            or isinstance(part, int)
            and is_sequence(current)
            and part < len(current)
        ):
            current = current[part]
        else:
            raise ToolError(f"No stored value at path {list(path[: index + 1])!r}. Check the field name or index.")
    return current
