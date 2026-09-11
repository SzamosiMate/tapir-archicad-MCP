import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.mcpserver import MCPServer
from multiconn_archicad.multi_conn import MultiConn

from tapir_archicad_mcp.context import mcp_instance, multi_conn_instance

@asynccontextmanager
async def app_lifespan(server: MCPServer) -> AsyncIterator[None]:
    from tapir_archicad_mcp.tools.registration import register_all_tools

    logging.info("MCP Server Lifespan: Initializing...")
    multi_conn = MultiConn()
    mcp_instance.set(server)
    multi_conn_instance.set(multi_conn)

    register_all_tools()
    logging.info("All dispatchable tools have been registered.")

    try:
        yield
    finally:
        logging.info("MCP Server Lifespan: Shutting down...")

mcp = MCPServer(
    "Archicad Tapir MCP Server",
    lifespan=app_lifespan
)