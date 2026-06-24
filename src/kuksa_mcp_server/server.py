from __future__ import annotations

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import __build_date__, __version__
from .client import KuksaDatabrokerClient, KuksaDatabrokerError
from .config import KuksaConfig
from .resources import register_resources
from .tools import register_tools

logger = logging.getLogger("kuksa-mcp-server")


@dataclass
class AppContext:
    _kuksa_client: KuksaDatabrokerClient | None


def create_server(
    config: KuksaConfig | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> FastMCP:
    if config is None:
        config = KuksaConfig()

    @asynccontextmanager
    async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
        _print_startup_banner()
        client = KuksaDatabrokerClient(config)
        try:
            await client.connect()
            _print_databroker_info(await client.get_server_info())
            _print_catalog_stats(await client.get_signal_stats())
        except Exception:
            logger.warning("Could not connect to Kuksa Databroker at %s", config.address)
            client = None
        yield AppContext(_kuksa_client=client)
        if client:
            await client.disconnect()

    mcp = FastMCP(
        "Kuksa Databroker MCP Server",
        host=host,
        port=port,
        lifespan=app_lifespan,
    )

    register_tools(mcp)
    register_resources(mcp)

    return mcp


def run_server(
    transport: str = "stdio",
    host: str = "127.0.0.1",
    port: int = 8765,
    config: KuksaConfig | None = None,
) -> None:
    mcp = create_server(config, host=host, port=port)
    mcp.run(transport=transport)


def _print_startup_banner() -> None:
    sep = "=" * 54
    _log(sep)
    _log(f"  Kuksa Databroker MCP Server")
    _log(f"  Version : {__version__}")
    _log(f"  Built   : {__build_date__}")
    _log(sep)


def _print_databroker_info(info: dict[str, Any]) -> None:
    _log(f"  Backend : {info.get('name', '?')}")
    _log(f"  Address : {info.get('address', '?')}")
    if info.get("version"):
        _log(f"  Version : {info['version']}")
    _log(f"  Status  : connected")


def _print_catalog_stats(stats: dict[str, Any]) -> None:
    total = stats.get("total_signals", 0)
    _log(f"  Signals : {total} total")
    entry_types = stats.get("entry_types", {})
    if entry_types:
        parts = [f"{k}={v}" for k, v in sorted(entry_types.items())]
        _log(f"  Types   : {', '.join(parts)}")
    _log("=" * 54)


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)
