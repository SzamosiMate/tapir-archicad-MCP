import logging

from tapir_archicad_mcp.app import mcp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    logging.info("Starting Archicad Tapir MCP Server...")
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()