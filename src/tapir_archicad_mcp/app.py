import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP
from multiconn_archicad.multi_conn import MultiConn

from tapir_archicad_mcp.context import mcp_instance, multi_conn_instance

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    logging.info("MCP Server Lifespan: Initializing...")
    multi_conn = MultiConn()
    mcp_instance.set(mcp)
    multi_conn_instance.set(multi_conn)
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