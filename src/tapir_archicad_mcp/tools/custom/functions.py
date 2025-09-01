import logging
from typing import Optional, Any, Dict
from pydantic import BaseModel, ValidationError

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.context import multi_conn_instance
from tapir_archicad_mcp.tools.custom.models import ArchicadInstanceInfo, ProjectType, ToolInfo
from tapir_archicad_mcp.tools.tool_registry import get_tool_entry
from tapir_archicad_mcp.tools.search_index import search_tools

from multiconn_archicad.conn_header import is_header_fully_initialized, ConnHeader
from multiconn_archicad.basic_types import TeamworkProjectID, SoloProjectID

log = logging.getLogger()


@mcp.tool(
    name="discovery_list_active_archicads",
    title="List Active Archicad Instances",
    description=(
        "Scans for and lists all running Archicad instances that the server can connect to. "
        "Each instance is identified by a unique 'port' number. This 'port' is required to target any other command."
    )
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
    description=(
        "Performs a semantic search over all available Archicad commands to find the most relevant tools for a task. "
        "The search is more effective with detailed, descriptive queries. For example, instead of a short query like 'selection', "
        "try a more complete, action-oriented query like 'get the currently selected elements' or 'add elements to the current selection'. "
        "Use this to find the correct tool 'name' before using 'archicad_call_tool'."
    ))
def archicad_discover_tools(query: str) -> list[ToolInfo]:
    log.info(f"Executing semantic tool discovery with query: '{query}'")
    return search_tools(query)


@mcp.tool(
    name="archicad_call_tool",
    title="Execute Archicad API Command",
    description=(
        "Executes a specific Archicad API command by its 'name'. This is the primary tool for interacting with Archicad. "
        "The 'arguments' dictionary MUST contain a 'port' number to target a specific Archicad instance. "
        "To get a valid 'port' number, you MUST first call the 'discovery_list_active_archicads' tool. "
        "If a tool's response includes a 'next_page_token', it means the results are paginated. "
        "To get the next page, call this same tool again with the same 'name' and 'arguments', but also add a 'page_token' key to the 'arguments' dictionary with the received token."
    ))
def archicad_call_tool(name: str, arguments: dict) -> dict:
    log.info(f"Executing archicad_call_tool for tool: {name}")

    if 'port' not in arguments:
        raise ValueError("The 'arguments' dictionary must contain the 'port' number.")

    port = arguments['port']
    tool_entry = get_tool_entry(name)
    target_func = tool_entry.callable
    params_model = tool_entry.params_model

    call_args: Dict[str, Any] = {'port': port}

    if params_model:
        # Check if the agent wrapped the params in a 'params' key or flattened them
        raw_params = arguments.get('params', arguments)

        try:
            params_instance = params_model.model_validate(raw_params)
            call_args['params'] = params_instance

        except ValidationError as e:
            log.error(f"Validation error for parameters of {name}: {e}")
            raise ValueError(f"Invalid parameters provided for tool '{name}'. Validation details: {e}")

    if 'page_token' in arguments:
        call_args['page_token'] = arguments['page_token']

    try:
        result = target_func(**call_args)

        if result is None:
            return {}

        if isinstance(result, BaseModel):
            return result.model_dump(mode='json', by_alias=True, exclude_none=True)

        return {"result": result}  # Should only happen for primitives, but safe fallback

    except Exception as e:
        log.error(f"Error executing dispatched tool {name}: {e}")
        raise e