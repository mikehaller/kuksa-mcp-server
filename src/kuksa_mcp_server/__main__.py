"""Entry point for kuksa-mcp-server.

Usage:
    kuksa-mcp                          # stdio transport (default)
    kuksa-mcp --transport sse          # SSE transport
    kuksa-mcp --transport sse --host 0.0.0.0 --port 8765
"""

from __future__ import annotations

import argparse
import sys

from .config import KuksaConfig
from .server import run_server


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MCP server for Eclipse Kuksa Databroker",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind for SSE transport (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for SSE transport (default: 8765)",
    )
    parser.add_argument(
        "--kuksa-host",
        default=None,
        help="Kuksa Databroker host (overrides KUKSA_HOST env)",
    )
    parser.add_argument(
        "--kuksa-port",
        type=int,
        default=None,
        help="Kuksa Databroker port (overrides KUKSA_PORT env)",
    )

    args = parser.parse_args()

    config = KuksaConfig()
    if args.kuksa_host is not None:
        config.host = args.kuksa_host
    if args.kuksa_port is not None:
        config.port = args.kuksa_port

    run_server(
        transport=args.transport,
        host=args.host,
        port=args.port,
        config=config,
    )


if __name__ == "__main__":
    main()
