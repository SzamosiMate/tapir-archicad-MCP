import logging

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.tools.registration import register_all_tools

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

register_all_tools()
logging.info("All MCP tools have been registered.")

def main():
    logging.info("Starting Archicad Tapir MCP Server...")
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()