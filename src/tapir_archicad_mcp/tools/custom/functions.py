import asyncio
import inspect
import logging
from typing import Annotated, Any

from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult, ToolAnnotations
from multiconn_archicad import (
    APIResponseError,
    ConnHeader,
    Port,
    ProductInfo,
    SoloProjectID,
    TapirInfo,
    TeamworkProjectID,
)
from multiconn_archicad.errors import AddOnCommandUnavailable, APIErrorBase

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.context import job_store_instance, multi_conn_instance
from tapir_archicad_mcp.images import build_result
from tapir_archicad_mcp.jobs import JobStatus, arguments_preview
from tapir_archicad_mcp.request_lifecycle import DispatchLifecycle
from tapir_archicad_mcp.tool_results import ResultMode, complete, deliver
from tapir_archicad_mcp.tools.custom.command_discovery import archicad_list_commands, command_groups
from tapir_archicad_mcp.tools.custom.models import (
    CommandSchema,
    DiscoveryResult,
    ProjectType,
    ReadyInstance,
    UnavailableInstance,
)
from tapir_archicad_mcp.tools.normalization import normalize
from tapir_archicad_mcp.tools.preparation import PreparedCall, prepare_call
from tapir_archicad_mcp.tools.tool_registry import (
    TOOL_DISCOVERY_CATALOG,
    ToolRegistryEntry,
    get_tool_entry,
    get_tool_input_schema,
    get_tool_output_schema,
)

log = logging.getLogger()


@mcp.tool(
    name="discovery_list_active_archicads",
    title="List Active Archicad Instances",
    description=(
        "Scans for and lists running Archicad instances. "
        "Returns 'active' (ready to receive commands with their target 'port') "
        "and 'unavailable' (instances that are unresponsive or missing the Tapir Add-On)."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
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

    active_instances: list[ReadyInstance] = []
    unavailable_instances: list[UnavailableInstance] = []

    for port, header in multi_conn.open_port_headers.items():
        if not isinstance(header.product_info, ProductInfo):
            unavailable_instances.append(_build_unresponsive_instance(header.product_info))
        elif (
            not isinstance(header.tapir_info, TapirInfo)
            or not header.tapir_info.is_installed
            or not header.tapir_info.version
        ):
            unavailable_instances.append(_build_missing_tapir_instance())
        else:
            active_instances.append(_build_ready_instance(int(port), header))

    log.info(f"Discovery complete: {len(active_instances)} ready, {len(unavailable_instances)} unavailable.")
    return DiscoveryResult(
        activeInstances=active_instances,
        unavailableInstances=unavailable_instances,
    )


def _build_unresponsive_instance(error: APIResponseError) -> UnavailableInstance:
    """Builds diagnostic info for an unresponsive Archicad instance."""
    return UnavailableInstance(
        reason="unresponsive",
        message=(
            f"Archicad API error: '{error.message}'. "
            "If the error message is actionable, please prompt the user to resolve it."
        ),
    )


def _build_missing_tapir_instance() -> UnavailableInstance:
    """Builds diagnostic info and installation instructions when Tapir is not installed."""
    return UnavailableInstance(
        reason="missing_tapir",
        message=(
            "Archicad was detected, but the Tapir Add-On is not installed. "
            "The Tapir Add-On is required for AI automation. "
            "Please prompt the user to download and install it from: "
            "https://github.com/ENZYME-APD/tapir-archicad-automation"
        ),
    )


def _build_ready_instance(port: int, header: ConnHeader) -> ReadyInstance:
    """Builds a ready-to-use Archicad instance metadata model."""
    project_id = header.archicad_id
    project_type: ProjectType = "untitled"
    project_path: str | None = None

    if isinstance(project_id, TeamworkProjectID):
        project_type = "teamwork"
        project_path = f"teamwork://{project_id.serverAddress}/{project_id.projectPath}"
    elif isinstance(project_id, SoloProjectID):
        project_type = "solo"
        project_path = project_id.projectPath

    tapir: TapirInfo = header.tapir_info

    return ReadyInstance(
        port=port,
        projectName=getattr(project_id, "projectName", "Untitled"),
        projectType=project_type,
        archicadVersion=str(header.product_info.version),
        tapirVersion=tapir.version,
        projectPath=project_path,
        warning=_get_tapir_version_warning(tapir),
    )


def _get_tapir_version_warning(tapir: TapirInfo) -> str | None:
    """Generates a diagnostic warning if the installed Tapir version differs from supported."""
    if tapir.is_older:
        return (
            f"Installed Tapir version ({tapir.version}) is older than supported ({tapir.requiredVersion}). "
            "Most commands will work, but newer commands or parameters may fail. "
            "If you encounter command errors, prompt the user to upgrade Tapir."
        )
    if tapir.is_newer:
        return (
            f"Installed Tapir version ({tapir.version}) is newer than supported ({tapir.requiredVersion}). "
            "Operations should proceed normally."
        )
    return None


mcp.add_tool(
    archicad_list_commands,
    name="archicad_list_commands",
    title="List Available Archicad Commands",
    description=(
        f"{inspect.getdoc(archicad_list_commands)}\n\n"
        f"Available groups: {', '.join(command_groups())}. "
        "Use archicad_get_command_schema before executing a selected command."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)


@mcp.tool(
    name="archicad_get_command_schema",
    title="Get Archicad Command Schema",
    description=(
        "Retrieves the argument schema and optionally the command data schema for an Archicad command. "
        "Provide the exact 'command_name' obtained from 'archicad_list_commands'. "
        "CRITICAL: You MUST call this tool before executing 'archicad_call_tool' to ensure you provide "
        "the correct parameters. Do NOT guess or hallucinate parameters based on the command name."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def archicad_get_command_schema(command_name: str, include_output: bool = False) -> CommandSchema:
    log.info(f"Executing archicad_get_command_schema for: {command_name}")
    try:
        tool = TOOL_DISCOVERY_CATALOG[command_name]
    except KeyError:
        raise ToolError(
            f"Command '{command_name}' not found. Please use 'archicad_list_commands' "
            f"to verify the exact spelling of the command name."
        ) from None

    return CommandSchema(
        name=tool["name"],
        input_schema=get_tool_input_schema(command_name),
        output_schema=get_tool_output_schema(command_name) if include_output else None,
    )


@mcp.tool(
    name="archicad_call_tool",
    title="Execute Archicad API Command",
    description=(
        "Executes a specific Archicad API command by its 'name'. "
        "CRITICAL WORKFLOW: You MUST use 'archicad_get_command_schema' first to understand the exact "
        "JSON structure required for the 'arguments' parameter. "
        "The 'arguments' dictionary MUST contain a 'port' number (obtained from 'discovery_list_active_archicads'). "
        "Set resultMode='handle' to reuse a result or read it with result_read. In params use "
        '{"$handle":"result:example","path":["field"]} to select retained data. Aligned batches submit successes '
        "only and keep skipped positions. Set view='inputs' to reuse successful originating inputs. "
        "Long executions return status='running' and a jobHandle; retrieve them with archicad_get_job. "
        "If a response is lost or cancelled, list jobs with archicad_get_job() before retrying a write. "
        "Cancelling this request does not cancel an admitted execution."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def archicad_call_tool(
    name: str, arguments: dict, resultMode: ResultMode = ResultMode.AUTO
) -> Annotated[CallToolResult, dict]:
    entry = get_tool_entry(name)
    store = job_store_instance.get()
    mode = ResultMode(resultMode)

    def prepare():
        return prepare_call(name, entry, arguments, store), arguments_preview(arguments)

    prepared, preview = await asyncio.to_thread(prepare)
    budget = store.settings.result_budget
    job = store.submit_prepared(
        name,
        prepared.arguments.port,
        preview,
        lambda handle: complete(_execute_tool(name, entry, prepared, handle), entry.metadata, mode, budget),
    )
    await store.wait(job)
    initial = store.initial_result(job)
    if isinstance(initial, dict):
        return build_result({**initial, "command": name, "next": "Poll with archicad_get_job using this jobHandle."})
    return await asyncio.to_thread(deliver, initial, job.result_handle)


def _execute_tool(name: str, tool_entry: ToolRegistryEntry, prepared: PreparedCall, job_handle: str):
    arguments = prepared.arguments
    port = arguments.port
    axis = prepared.axis
    if axis is not None and not any(slot.is_success for slot in axis.outcomes.slots):
        contract = tool_entry.metadata.positional
        skipped = {field: [] for field in (contract.output_field, *contract.empty_outputs)}
        flag = tool_entry.metadata.inline_if_true
        if flag and getattr(arguments.params, flag, None) is True:
            skipped[flag] = True
        return normalize(tool_entry, skipped, axis)

    call_args: dict[str, Any] = {"conn_header": _get_header(port)}
    if tool_entry.params_model:
        call_args["params"] = arguments.params
    with DispatchLifecycle(name, port, job_handle):
        result = _dispatch_command(name, tool_entry, call_args, port)
    return normalize(tool_entry, result, axis)


def _dispatch_command(name: str, tool_entry: ToolRegistryEntry, call_args: dict, port: int) -> Any:
    try:
        return tool_entry.callable(**call_args)
    except AddOnCommandUnavailable as e:
        raise ToolError(
            f"Command '{name}' is not available in the installed Tapir Add-On on port {port}. "
            f"This indicates that the Tapir Add-On is outdated. "
            f"Please prompt the user to upgrade Tapir from https://github.com/ENZYME-APD/tapir-archicad-automation. "
            f"(Details: {e.message})"
        ) from e
    except APIErrorBase as e:
        raise ToolError(str(e)) from e
    except Exception as e:
        log.error(f"Error executing dispatched tool {name}: {e}")
        raise


def _get_header(port: int) -> ConnHeader:
    try:
        return multi_conn_instance.get().open_port_headers[Port(port)]
    except KeyError:
        raise ToolError(f"Port {port} is not an active Archicad connection.") from None


@mcp.tool(
    name="archicad_get_job",
    title="Get or List Archicad Jobs",
    description=(
        "With no job_handle, immediately lists all retained executions newest first, including fast, completed, "
        "and failed jobs, with command, port, timestamps, and a short argumentsPreview. "
        "Use this to recover after a lost response before retrying a write; similar calls may be ambiguous. "
        "With a job_handle, waits up to the configured threshold and returns running, completed with result, "
        "or failed with error. Polling never redispatches commands."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def archicad_get_job(job_handle: str | None = None) -> Annotated[CallToolResult, dict]:
    store = job_store_instance.get()
    if job_handle is None:
        return build_result(store.list_jobs())
    job = store.get(job_handle)
    await store.wait(job)
    response = store.response(job)
    if response["status"] == JobStatus.COMPLETED:
        return await asyncio.to_thread(deliver, response["result"], job.result_handle, job_handle=job.handle)
    return build_result(response)
