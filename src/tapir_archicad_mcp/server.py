import logging
import argparse
import os
import sys
from pathlib import Path

PACKAGE_SRC = Path(__file__).resolve().parents[1]
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

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
        default=None,
        help="Optional mount path for SSE transport.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    os.environ["TAPIR_MCP_HOST"] = args.host
    os.environ["TAPIR_MCP_PORT"] = str(args.port)
    os.environ["TAPIR_MCP_STREAMABLE_HTTP_PATH"] = args.streamable_http_path
    sys.argv = [sys.argv[0]]

    from tapir_archicad_mcp.app import mcp

    logging.info(
        "Starting Archicad Tapir MCP Server with transport=%s host=%s port=%s path=%s",
        args.transport,
        args.host,
        args.port,
        args.streamable_http_path,
    )
    mcp.run(transport=args.transport, mount_path=args.mount_path)

if __name__ == "__main__":
    main()
