import logging
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP
from multiconn_archicad.multi_conn import MultiConn

from tapir_archicad_mcp.context import mcp_instance, multi_conn_instance


def _env_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip()


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    from tapir_archicad_mcp.tools.registration import register_all_tools

    logging.info("MCP Server Lifespan: Initializing...")
    multi_conn = MultiConn()
    mcp_instance.set(mcp)
    multi_conn_instance.set(multi_conn)

    register_all_tools()
    logging.info("All dispatchable tools have been registered.")
    try:
        from tapir_archicad_mcp.tools.search_index import create_or_load_index
    except ModuleNotFoundError as error:
        logging.warning(
            "Semantic search dependencies are unavailable (%s). "
            "Starting without the search index; dispatch tools remain usable.",
            error,
        )
    else:
        create_or_load_index()

    try:
        yield
    finally:
        logging.info("MCP Server Lifespan: Shutting down...")


mcp = FastMCP(
    "Archicad Tapir MCP Server",
    lifespan=app_lifespan,
    host=_env_str("TAPIR_MCP_HOST", "127.0.0.1"),
    port=_env_int("TAPIR_MCP_PORT", 8000),
    streamable_http_path=_env_str("TAPIR_MCP_STREAMABLE_HTTP_PATH", "/mcp"),
)
