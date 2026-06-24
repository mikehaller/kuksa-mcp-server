from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import KuksaDatabrokerClient, KuksaDatabrokerError
from .config import KuksaConfig
from .resources import register_resources
from .tools import register_tools


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
        client = KuksaDatabrokerClient(config)
        try:
            await client.connect()
        except Exception:
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
