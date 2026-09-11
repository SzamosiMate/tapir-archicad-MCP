from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.tools.custom import functions  # noqa: F401  registers the four MCP tools


# openWorldHint differs across the read-only tools: discovery reaches out to
# whatever Archicad instances happen to be running, while the other two read
# the command catalogue compiled into this package.
READ_ONLY_TOOLS = {
    "discovery_list_active_archicads": True,
    "archicad_list_commands": False,
    "archicad_get_command_schema": False,
}


def _tools_by_name() -> dict:
    return {tool.name: tool for tool in mcp._tool_manager.list_tools()}


def test_discovery_and_schema_tools_are_read_only():
    tools = _tools_by_name()
    for name, open_world in READ_ONLY_TOOLS.items():
        annotations = tools[name].annotations
        assert annotations is not None, f"{name} has no annotations"
        assert annotations.read_only_hint is True, name
        assert annotations.destructive_hint is False, name
        assert annotations.idempotent_hint is True, name
        assert annotations.open_world_hint is open_world, name


def test_call_tool_is_write_delete():
    annotations = _tools_by_name()["archicad_call_tool"].annotations
    assert annotations is not None
    assert annotations.read_only_hint is False
    assert annotations.destructive_hint is True
    assert annotations.idempotent_hint is False
    assert annotations.open_world_hint is True
