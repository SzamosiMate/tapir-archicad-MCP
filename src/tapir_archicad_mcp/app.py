import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any

from mcp.server.mcpserver import Context, MCPServer
from mcp.types import CallToolResult, InputRequiredResult, TextContent
from multiconn_archicad import MultiConn
from starlette.applications import Starlette

from tapir_archicad_mcp.context import job_store_instance, mcp_instance, multi_conn_instance
from tapir_archicad_mcp.jobs import JobSettings, JobStore
from tapir_archicad_mcp.tool_results import compact_json

log = logging.getLogger(__name__)
job_settings = JobSettings()


class ArchicadMCPServer(MCPServer):
    """Serialize compact tool results and give SSE resources an application lifetime."""

    _sse_active = False

    async def call_tool(
        self, name: str, arguments: dict[str, Any], context: Context | None = None
    ) -> CallToolResult | InputRequiredResult:
        result = await super().call_tool(name, arguments, context)
        if isinstance(result, CallToolResult):
            for block in result.content:
                # The SDK pretty-prints model returns, including command schemas and discovery results.
                if isinstance(block, TextContent) and block.text.startswith(("{\n", "[\n")):
                    try:
                        block.text = compact_json(json.loads(block.text))
                    except (ValueError, RecursionError):
                        continue
        return result

    def sse_app(self, **options) -> Starlette:
        app = super().sse_app(**options)
        transport_lifespan = app.router.lifespan_context

        @asynccontextmanager
        async def lifespan(_app):
            async with app_lifespan(self):
                self._sse_active = True
                try:
                    async with transport_lifespan(_app) as state:
                        yield state
                finally:
                    self._sse_active = False

        app.router.lifespan_context = lifespan
        return app


@asynccontextmanager
async def app_lifespan(server: MCPServer) -> AsyncIterator[None]:
    # SSE sessions borrow the application-owned resources.
    if server._sse_active:
        yield
        return

    from tapir_archicad_mcp.tools.registration import register_all_tools

    log.info("MCP Server Lifespan: Initializing...")
    multi_conn = MultiConn()
    mcp_instance.set(server)
    multi_conn_instance.set(multi_conn)
    job_store = JobStore(job_settings)
    job_store_instance.set(job_store)

    cleanup = asyncio.create_task(job_store.cleanup_loop())
    try:
        register_all_tools()
        log.info("All dispatchable tools have been registered.")
        yield
    finally:
        log.info("MCP Server Lifespan: Shutting down...")
        job_store.stop_admission()
        cleanup.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup
        # Keep connection state available until every admitted worker has finished.
        await asyncio.to_thread(job_store.shutdown)
        job_store_instance.clear()
        mcp_instance.clear()
        multi_conn_instance.clear()


mcp = ArchicadMCPServer("Archicad Tapir MCP Server", lifespan=app_lifespan)
