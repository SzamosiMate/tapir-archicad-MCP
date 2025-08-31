import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP
from multiconn_archicad.multi_conn import MultiConn

from tapir_archicad_mcp.context import mcp_instance, multi_conn_instance
# REMOVE the imports from here

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    # --- ADD the imports here, inside the function ---
    from tapir_archicad_mcp.tools.registration import register_all_tools
    from tapir_archicad_mcp.tools.search_index import create_or_load_index

    logging.info("MCP Server Lifespan: Initializing...")

    # Initialize MultiConn and set context variables
    multi_conn = MultiConn()
    mcp_instance.set(mcp)
    multi_conn_instance.set(multi_conn)

    # Register all tools, which populates the TOOL_DISCOVERY_CATALOG
    register_all_tools()
    logging.info("All dispatchable tools have been registered.")

    # Now, create or load the semantic search index using the registered tools
    create_or_load_index()

    try:
        yield
    finally:
        logging.info("MCP Server Lifespan: Shutting down...")


mcp = FastMCP(
    "ArchicadTapir",
    title="Archicad Tapir MCP Server",
    description="A server to control multiple Archicad instances via the Tapir API.",
    lifespan=app_lifespan
)