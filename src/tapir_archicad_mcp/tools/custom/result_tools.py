"""Direct tools for reading retained command results."""

import asyncio
from typing import Annotated

from mcp.types import CallToolResult, ToolAnnotations
from pydantic import Field

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.context import job_store_instance
from tapir_archicad_mcp.result_reading import ReadSelection, read_result


@mcp.tool(
    name="result_read",
    title="Read Retained Archicad Result",
    description=(
        "Read bounded entries from a resultHandle without contacting Archicad. Select paths, list indices or ranges, "
        "matrix rows/columns, or an outcome view. Entries identify original positions. If truncated, repeat with the "
        "same selection and the continuation. Large text entries include character offsets."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
)
async def result_read(
    resultHandle: str,
    selection: ReadSelection | None = None,
    maxEntries: Annotated[int, Field(ge=1, le=100)] = 25,
    continuation: Annotated[str | None, Field(max_length=110)] = None,
) -> Annotated[CallToolResult, dict]:
    return await asyncio.to_thread(
        read_result, job_store_instance.get(), resultHandle, selection or ReadSelection(), maxEntries, continuation
    )
