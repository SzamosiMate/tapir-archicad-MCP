import logging
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from mcp.server.fastmcp import FastMCP
from multiconn_archicad.multi_conn import MultiConn

from tapir_archicad_mcp import constants
from tapir_archicad_mcp.context import mcp_instance, multi_conn_instance

log = logging.getLogger()

group_name = os.environ.get(constants.TAPIR_MCP_GROUP_ENV_VAR, constants.DEFAULT_GROUP_NAME)

if group_name == constants.DEFAULT_GROUP_NAME:
    log.warning(f"{constants.TAPIR_MCP_GROUP_ENV_VAR} environment variable not set. Using '{constants.DEFAULT_GROUP_NAME}' as server name.")

capitalized_group_name = group_name.capitalize()
server_name = constants.SERVER_NAME_TEMPLATE.format(group_name=capitalized_group_name)
server_title = constants.SERVER_TITLE_TEMPLATE.format(group_name=capitalized_group_name)
server_description = constants.SERVER_DESCRIPTION_TEMPLATE.format(group_name=group_name)

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    log.info(f"[{server.name}] Lifespan: Initializing...")
    multi_conn = MultiConn()
    mcp_instance.set(mcp)
    multi_conn_instance.set(multi_conn)
    try:
        yield
    finally:
        log.info(f"[{server.name}] Lifespan: Shutting down...")

mcp = FastMCP(
name=server_name,
title=server_title,
description=server_description,
lifespan=app_lifespan
)

log.info(f"Initialized MCP Server instance with name: '{mcp.name}'")