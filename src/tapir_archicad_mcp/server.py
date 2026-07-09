import logging
import argparse
import os
import sys

import uvicorn

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.logging_config import setup_logging
from tapir_archicad_mcp.middleware import BearerTokenMiddleware

setup_logging()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Archicad Tapir MCP server.")
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default="stdio",
        help="MCP transport to use. Defaults to stdio.",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("TAPIR_MCP_HOST", "127.0.0.1"),
        help="Host to bind for HTTP-based transports.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("TAPIR_MCP_PORT", "8000")),
        help="Port to bind for HTTP-based transports.",
    )
    parser.add_argument(
        "--streamable-http-path",
        default=os.getenv("TAPIR_MCP_STREAMABLE_HTTP_PATH", "/mcp"),
        help="HTTP path for the streamable-http transport.",
    )
    parser.add_argument(
        "--mount-path",
        default=os.getenv("TAPIR_MCP_MOUNT_PATH", None),
        help="Optional mount path for SSE transport.",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("TAPIR_MCP_TOKEN", None),
        help="Bearer token required for HTTP-based transports. Ignored for stdio.",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    sys.argv = [sys.argv[0]]

    logging.info(
        "Starting Archicad Tapir MCP Server with transport=%s host=%s port=%s streamable_path=%s mount_path=%s",
        args.transport,
        args.host,
        args.port,
        args.streamable_http_path,
        args.mount_path
    )

    mcp.settings.host = args.host
    mcp.settings.port = args.port
    if args.streamable_http_path:
        mcp.settings.streamable_http_path = args.streamable_http_path
    if args.mount_path:
        mcp.settings.mount_path = args.mount_path

    if args.token and args.transport != "stdio":
        app = mcp.sse_app() if args.transport == "sse" else mcp.streamable_http_app()
        uvicorn.run(BearerTokenMiddleware(app, args.token), host=args.host, port=args.port)
        return

    if args.token:
        logging.warning("--token is only used for HTTP-based transports and is ignored for stdio.")

    mcp.run(transport=args.transport)

if __name__ == "__main__":
    main()