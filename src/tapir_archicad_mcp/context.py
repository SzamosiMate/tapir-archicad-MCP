from contextvars import ContextVar
from mcp.server.fastmcp import FastMCP
from multiconn_archicad.multi_conn import MultiConn

mcp_instance: ContextVar[FastMCP] = ContextVar("mcp_instance")
multi_conn_instance: ContextVar[MultiConn] = ContextVar("multi_conn_instance")