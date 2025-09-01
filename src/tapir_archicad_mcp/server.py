import logging

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.logging_config import setup_logging

setup_logging()


def main():
    logging.info("Starting Archicad Tapir MCP Server...")
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()