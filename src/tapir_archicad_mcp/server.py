import logging
import argparse
import os
import sys

from tapir_archicad_mcp.app import mcp
from tapir_archicad_mcp.logging_config import setup_logging

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

    mcp.run(transport=args.transport)

if __name__ == "__main__":
    main()