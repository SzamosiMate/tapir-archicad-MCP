import argparse
import logging
import os
import sys

from tapir_archicad_mcp import constants

def main():
    """
    Parses command-line arguments to launch the MCP server for a specific tool group.

    This script sets an environment variable with the selected group, which is then
    read by the application modules to configure the MCP server instance dynamically
    before any tools are registered.
    """
    parser = argparse.ArgumentParser(
        description="Archicad Tapir MCP Server. Launches a server process for a specific tool group.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--group",
        required=True,
        type=str,
        choices=constants.AVAILABLE_GROUPS,
        help="The tool group to load.\n"
             f"Available groups: {', '.join(constants.AVAILABLE_GROUPS)}"
    )
    args = parser.parse_args()

    os.environ['TAPIR_MCP_GROUP'] = args.group

    from tapir_archicad_mcp.app import mcp
    from tapir_archicad_mcp.tools.registration import register_tool_group

    logging.basicConfig(level=logging.INFO, format=f'%(asctime)s - {args.group.upper()} - %(levelname)s - %(message)s')

    logging.info(f"Attempting to register tool group: '{args.group}'")
    try:
        register_tool_group(args.group)
        logging.info(f"MCP tool group '{args.group}' has been registered successfully.")
    except (ValueError, ImportError) as e:
        logging.critical(f"FATAL: Failed to register tool group '{args.group}'. Reason: {e}")
        sys.exit(1)

    logging.info(f"Starting Archicad Tapir MCP Server for group '{args.group}' with server name '{mcp.name}'...")
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()