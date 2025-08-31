import logging
from typing import Optional, Any, Dict
from pydantic import BaseModel, ValidationError

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.context import multi_conn_instance
from tapir_archicad_mcp.tools.custom.models import ArchicadInstanceInfo, ProjectType, ToolInfo
from tapir_archicad_mcp.tools.tool_registry import TOOL_DISCOVERY_CATALOG, get_tool_entry

from multiconn_archicad.conn_header import is_header_fully_initialized, ConnHeader
from multiconn_archicad.basic_types import TeamworkProjectID, SoloProjectID

log = logging.getLogger()


@mcp.tool(
    name="discovery_list_active_archicads",
    title="List Active Archicad Instances",
    description="Refreshes connections and lists all actively running and connected Archicad instances."
)
def list_active_archicads() -> list[ArchicadInstanceInfo]:
    log.info("Executing list_active_archicads tool...")
    try:
        multi_conn = multi_conn_instance.get()
    except LookupError:
        log.error("CRITICAL: multi_conn_instance context variable not set. Lifespan manager may have failed.")
        raise RuntimeError("Server configuration error: could not access MultiConn instance.")

    multi_conn.refresh.all_ports()
    multi_conn.connect.all()

    active_instances: list[ArchicadInstanceInfo] = []
    log.info(f"Found {len(multi_conn.active)} active connections.")

    header: ConnHeader
    for port, header in multi_conn.active.items():
        if is_header_fully_initialized(header):
            project_id = header.archicad_id
            project_type: ProjectType
            project_path: Optional[str] = None

            if isinstance(project_id, TeamworkProjectID):
                project_type = "teamwork"
                project_path = f"teamwork://{project_id.serverAddress}/{project_id.projectPath}"
            elif isinstance(project_id, SoloProjectID):
                project_type = "solo"
                project_path = project_id.projectPath
            else:
                project_type = "untitled"

            instance_info = ArchicadInstanceInfo(
                port=port,
                projectName=project_id.projectName,
                projectType=project_type,
                archicadVersion=str(header.product_info.version),
                projectPath=project_path
            )
            active_instances.append(instance_info)
        else:
            log.warning(f"Port {port} is active but its header is not fully initialized. Skipping.")

    if not active_instances:
        log.info("No active and fully initialized Archicad instances found.")

    return active_instances


@mcp.tool(
    name="archicad_discover_tools",
    title="Discover Archicad API Tools",
    description="Performs a search over the available Archicad commands (Tapir/JSON API) and returns relevant tool metadata. Use this before calling archicad_call_tool."
)
def archicad_discover_tools(query: str) -> list[ToolInfo]:
    """
    Searches the tool catalog based on the query.

    NOTE: Currently performs a basic keyword search. This will be replaced by a vector/semantic search index later.
    """
    log.info(f"Executing archicad_discover_tools with query: '{query}'")
    query_lower = query.lower()

    results = []
    for tool_data in TOOL_DISCOVERY_CATALOG:
        desc = tool_data["description"].lower()
        name = tool_data["name"].lower()
        if query_lower in name or query_lower in desc:
            results.append(ToolInfo(**tool_data))

    # Limit results to keep context window clean
    return results[:10]


@mcp.tool(
    name="archicad_call_tool",
    title="Execute Archicad API Command",
    description="Dispatches a call to a specific Archicad API command, using the tool name and arguments discovered via archicad_discover_tools."
)
def archicad_call_tool(name: str, arguments: dict) -> dict:
    """
    Executes a registered tool function.

    The 'arguments' dictionary must contain 'port' (int) and optionally 'params' (dict)
    or 'page_token' (str).
    """
    log.info(f"Executing archicad_call_tool for tool: {name}")

    if 'port' not in arguments:
        raise ValueError("The 'arguments' dictionary must contain the 'port' number.")

    port = arguments['port']
    tool_entry = get_tool_entry(name)
    target_func = tool_entry.callable
    params_model = tool_entry.params_model

    call_args: Dict[str, Any] = {'port': port}

    # 1. Handle Parameters
    if params_model:
        # Check if the agent wrapped the params in a 'params' key or flattened them
        raw_params = arguments.get('params', arguments)

        try:
            # Instantiate the required Pydantic model
            params_instance = params_model.model_validate(raw_params)
            call_args['params'] = params_instance

        except ValidationError as e:
            log.error(f"Validation error for parameters of {name}: {e}")
            # Re-raise as ValueError for cleaner MCP error handling
            raise ValueError(f"Invalid parameters provided for tool '{name}'. Validation details: {e}")

    # 2. Handle Pagination Token
    if 'page_token' in arguments:
        call_args['page_token'] = arguments['page_token']

    try:
        # Execute the underlying generated function
        result = target_func(**call_args)

        # Convert result (which might be a Pydantic model or None) to dictionary for MCP output
        if result is None:
            return {}

        if isinstance(result, BaseModel):
            # Use model_dump to convert the model back to a dictionary suitable for JSON transport
            return result.model_dump(mode='json', by_alias=True, exclude_none=True)

        return {"result": result}  # Should only happen for primitives, but safe fallback

    except Exception as e:
        log.error(f"Error executing dispatched tool {name}: {e}")
        # Re-raise the exception for the MCP server to handle
        raise e