import logging
from typing import Optional, Any, Dict
from pydantic import BaseModel, ValidationError

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.context import multi_conn_instance
from tapir_archicad_mcp.tools.custom.models import (
    ArchicadInstanceInfo, UnavailableArchicadInstance, DiscoveryResult,
    ProjectType, ToolInfo,
)
from tapir_archicad_mcp.tools.tool_registry import get_tool_entry
from tapir_archicad_mcp.tools.search_index import search_tools

from multiconn_archicad.conn_header import is_header_fully_initialized, ConnHeader
from multiconn_archicad.basic_types import TeamworkProjectID, SoloProjectID, APIResponseError, ProductInfo

log = logging.getLogger()


def _diagnose_connection_issue(header: ConnHeader, port: int) -> UnavailableArchicadInstance:
    """Inspect a partially-initialized header to determine why it failed.

    Uses structural diagnosis (official API vs Tapir) rather than
    fragile string-matching on undocumented Graphisoft error messages.
    The raw error message is passed through for the AI to interpret.
    """
    ac_version = None
    if isinstance(header.product_info, ProductInfo):
        ac_version = str(header.product_info.version)

    # product_info (official API) failed → Archicad itself is unresponsive
    if isinstance(header.product_info, APIResponseError):
        return UnavailableArchicadInstance(
            port=port, archicadVersion=None,
            issue="archicad_unresponsive",
            message=(
                f"Archicad on port {port} did not respond to the official API. "
                f"Possible causes: a modal dialog is open, no project loaded, or heavy computation. "
                f"Raw error: {header.product_info.message}"
            ),
        )

    # product_info OK but Tapir commands failed
    tapir_error = None
    if isinstance(header.archicad_id, APIResponseError):
        tapir_error = header.archicad_id
    elif isinstance(header.archicad_location, APIResponseError):
        tapir_error = header.archicad_location

    if tapir_error:
        return UnavailableArchicadInstance(
            port=port, archicadVersion=ac_version,
            issue="tapir_unavailable",
            message=(
                f"Archicad {ac_version} on port {port} responds to the official API "
                f"but Tapir commands failed. The Tapir Add-On may not be installed, "
                f"or a dialog may be blocking Tapir responses. "
                f"Raw error: {tapir_error.message}"
            ),
        )

    return UnavailableArchicadInstance(
        port=port, archicadVersion=ac_version,
        issue="unknown",
        message=f"Archicad on port {port} is reachable but not fully initialized.",
    )


def _try_get_tapir_version(header: ConnHeader) -> Optional[str]:
    """Best-effort Tapir version query. Returns None on failure."""
    try:
        result = header.core.post_tapir_command(
            command="GetAddOnVersion", parameters={}
        )
        return result.get("version", None)
    except Exception:
        return None


@mcp.tool(
    name="discovery_list_active_archicads",
    title="List Active Archicad Instances",
    description=(
        "Scans for and lists all running Archicad instances. "
        "Returns two lists: 'active' instances ready for commands (identified by 'port'), "
        "and 'unavailable' instances that were detected but have issues (with diagnostic info). "
        "The 'port' from an active instance is required to target any other command."
    )
)
def list_active_archicads() -> DiscoveryResult:
    log.info("Executing list_active_archicads tool...")
    try:
        multi_conn = multi_conn_instance.get()
    except LookupError:
        log.error("CRITICAL: multi_conn_instance context variable not set. Lifespan manager may have failed.")
        raise RuntimeError("Server configuration error: could not access MultiConn instance.")

    multi_conn.refresh.all_ports()
    multi_conn.connect.all()

    active: list[ArchicadInstanceInfo] = []
    unavailable: list[UnavailableArchicadInstance] = []
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

            tapir_version = _try_get_tapir_version(header)

            instance_info = ArchicadInstanceInfo(
                port=port,
                projectName=project_id.projectName,
                projectType=project_type,
                archicadVersion=str(header.product_info.version),
                projectPath=project_path,
                tapirVersion=tapir_version,
            )
            active.append(instance_info)
        else:
            issue = _diagnose_connection_issue(header, port)
            unavailable.append(issue)
            log.warning("Port %s: %s — %s", port, issue.issue, issue.message)

    if not active:
        log.info("No active and fully initialized Archicad instances found.")

    return DiscoveryResult(active=active, unavailable=unavailable)


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