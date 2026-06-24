from __future__ import annotations

import logging
import os
import signal
import sys
import threading
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
_log_handler_configured = False


def configure_logging(log_file: str | None = None) -> None:
    global _log_handler_configured
    if _log_handler_configured:
        return

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Route FastMCP's internal request logging through our handlers too
    fastmcp_logger = logging.getLogger("mcp.server.lowlevel.server")
    fastmcp_logger.handlers.clear()
    fastmcp_logger.addHandler(handler)
    if log_file:
        fastmcp_logger.addHandler(fh)
    fastmcp_logger.setLevel(logging.INFO)
    fastmcp_logger.propagate = False

    _log_handler_configured = True


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
        try:
            yield AppContext(_kuksa_client=client)
        finally:
            if client:
                logger.info("Shutting down Kuksa Databroker client...")
                await client.disconnect()
                logger.info("Disconnected.")

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
    log_file: str | None = None,
) -> None:
    configure_logging(log_file)
    mcp = create_server(config, host=host, port=port)
    _install_signal_handlers()

    logger.info(
        "Starting Kuksa Databroker MCP Server v%s (built %s) on transport=%s",
        __version__,
        __build_date__,
        transport,
    )

    try:
        mcp.run(transport=transport)
    except KeyboardInterrupt:
        logger.info("Received Ctrl-C, shutting down gracefully...")
        logger.info("Goodbye.")
        os._exit(0)


def _install_signal_handlers() -> None:
    def _force_exit(signum: int, _frame: Any) -> None:
        logger.info("Received signal %d, force exiting.", signum)
        os._exit(1)

    def _handler(signum: int, frame: Any) -> None:
        signal.signal(signal.SIGINT, _force_exit)
        signal.signal(signal.SIGTERM, _force_exit)
        raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


def _print_startup_banner() -> None:
    sep = "=" * 54
    _print_banner(sep)
    _print_banner(f"  Kuksa Databroker MCP Server")
    _print_banner(f"  Version : {__version__}")
    _print_banner(f"  Built   : {__build_date__}")
    _print_banner(sep)


def _print_databroker_info(info: dict[str, Any]) -> None:
    _print_banner(f"  Backend : {info.get('name', '?')}")
    _print_banner(f"  Address : {info.get('address', '?')}")
    if info.get("version"):
        _print_banner(f"  Version : {info['version']}")
    _print_banner(f"  Status  : connected")


def _print_catalog_stats(stats: dict[str, Any]) -> None:
    total = stats.get("total_signals", 0)
    _print_banner(f"  Signals : {total} total")
    entry_types = stats.get("entry_types", {})
    if entry_types:
        parts = [f"{k}={v}" for k, v in sorted(entry_types.items())]
        _print_banner(f"  Types   : {', '.join(parts)}")
    _print_banner("=" * 54)


def _print_banner(msg: str) -> None:
    logger.info("%s", msg)
