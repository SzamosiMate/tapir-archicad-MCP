"""The Archicad call and job tools return a CallToolResult; these wrappers hand tests its JSON payload."""

from tapir_archicad_mcp.tools.custom import functions


async def archicad_call_tool(name: str, arguments: dict) -> dict:
    return (await functions.archicad_call_tool(name, arguments)).structured_content


async def archicad_get_job(job_handle: str | None = None) -> dict:
    return (await functions.archicad_get_job(job_handle)).structured_content
