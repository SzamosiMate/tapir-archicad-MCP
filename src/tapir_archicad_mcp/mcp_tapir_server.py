import logging
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from mcp.server.fastmcp import FastMCP
from multiconn_archicad.multi_conn import MultiConn
from multiconn_archicad.conn_header import is_header_fully_initialized, ConnHeader
from multiconn_archicad.basic_types import TeamworkProjectID, SoloProjectID

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger()

# --- MCP Server and Archicad Connection Setup ---
log.info("Initializing MCP Server for Archicad Tapir...")
mcp = FastMCP(
    "ArchicadTapir",
    title="Archicad Tapir MCP Server",
    description="A server to control multiple Archicad instances via the Tapir API."
)

log.info("Initializing MultiConn for Archicad...")
multi_conn = MultiConn()
log.info("MultiConn initialized.")

# --- Pydantic Models for Structured Tool Output ---

# Use a Literal type for strong typing of the project type
ProjectType = Literal["teamwork", "solo", "untitled"]


class ArchicadInstanceInfo(BaseModel):
    """A curated model to hold key information about a running Archicad instance."""
    port: int = Field(description="The communication port of the Archicad instance. Use this to target commands.")
    projectName: str = Field(description="The name of the project file currently open in the instance.")
    projectType: ProjectType = Field(description="The type of the project: 'teamwork', 'solo', or 'untitled'.")
    archicadVersion: str = Field(description="The major version of the Archicad application (e.g., '27').")
    projectPath: Optional[str] = Field(None,
                                       description="The full file path of the project, if it is a saved solo or teamwork project.")


# --- Core MCP Tools ---
@mcp.tool(
    name="tapir_discovery_list_active_archicads",
    title="List Active Archicad Instances",
    description="Refreshes connections and lists all actively running and connected Archicad instances that the server can communicate with."
)
def list_active_archicads() -> List[ArchicadInstanceInfo]:
    """
    Scans for running Archicad instances, attempts to connect,
    and returns a list of successfully connected instances with key project details.
    This tool is essential for discovering which 'port' to use for other commands.
    """
    log.info("Executing list_active_archicads tool...")

    multi_conn.refresh.all_ports()
    multi_conn.connect.all()

    active_instances: List[ArchicadInstanceInfo] = []
    log.info(f"Found {len(multi_conn.active)} active connections.")

    header: ConnHeader
    for port, header in multi_conn.active.items():
        if is_header_fully_initialized(header):
            project_id = header.archicad_id
            project_type: ProjectType
            project_path: Optional[str] = None

            if isinstance(project_id, TeamworkProjectID):
                project_type = "teamwork"
                # For security, we get a user/pass-less representation
                project_path = f"teamwork://{project_id.serverAddress}/{project_id.projectPath}"
            elif isinstance(project_id, SoloProjectID):
                project_type = "solo"
                project_path = project_id.projectPath
            else:  # isinstance(project_id, UntitledProjectID)
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


# --- Server Runner ---
if __name__ == "__main__":
    log.info("Starting Archicad Tapir MCP Server...")
    mcp.run(transport='stdio')