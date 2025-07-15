import subprocess
import sys
import logging
from tapir_archicad_mcp.constants import MODULE_NAME_MAPPING

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def launch_all_servers():
    """
    Launches a separate MCP server process for each defined tool group.

    This script provides a convenient way to run all toolsets simultaneously,
    with each toolset appearing as a distinct, named server in the client.
    """

    groups_to_launch = list(MODULE_NAME_MAPPING.keys())

    logging.info(f"Preparing to launch {len(groups_to_launch)} MCP server processes...")
    logging.info(f"Groups: {', '.join(groups_to_launch)}")

    processes = []
    for group in groups_to_launch:
        command = [
            sys.executable,
            "-m", "tapir_archicad_mcp.server",
            "--group", group
        ]

        try:
            proc = subprocess.Popen(command)
            processes.append(proc)
            logging.info(f"Successfully launched server for group '{group}' with PID: {proc.pid}")
        except Exception as e:
            logging.error(f"Failed to launch server for group '{group}': {e}")

    logging.info(f"All {len(processes)} server processes have been launched.")
    logging.info("You can now connect your MCP client (e.g., Claude Desktop).")
    logging.info("To stop all servers, you will need to close the terminal or stop the processes manually.")

if __name__ == "__main__":
    launch_all_servers()