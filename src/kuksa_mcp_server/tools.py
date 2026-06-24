from __future__ import annotations

import logging
import time
from typing import Any

from mcp.server.fastmcp import Context

from kuksa_mcp_server.client import KuksaDatabrokerClient, KuksaDatabrokerError

logger = logging.getLogger("kuksa-mcp-server")


def _log_call(name: str, args: dict[str, Any], result: Any, elapsed: float) -> None:
    if isinstance(result, list):
        summary = f"{len(result)} results"
    elif isinstance(result, dict):
        summary = result.get("status", "ok")
    elif isinstance(result, str):
        summary = result
    else:
        summary = "ok"
    logger.info(
        "%s(args=%s) -> %s [%.3fs]",
        name,
        args,
        summary,
        elapsed,
    )


def register_tools(mcp: Any) -> None:
    def _client(ctx: Context) -> KuksaDatabrokerClient | None:
        return ctx.request_context.lifespan_context._kuksa_client

    @mcp.tool()
    async def get_signal(path: str, ctx: Context) -> dict[str, Any] | str:
        """[Kuksa V2 API] Get the current value of a single VSS vehicle signal.

        Args:
            path: VSS signal path (e.g. 'Vehicle.Speed', 'Vehicle.Cabin.Door.Row1.Left.IsOpen').
        """
        t0 = time.perf_counter()
        c = _client(ctx)
        if c is None:
            _log_call("get_signal", {"path": path}, "Not connected", time.perf_counter() - t0)
            return "Not connected to Kuksa Databroker"
        try:
            result = await c.get_value(path)
            _log_call("get_signal", {"path": path}, result, time.perf_counter() - t0)
            return result
        except KuksaDatabrokerError as e:
            _log_call("get_signal", {"path": path}, f"error: {e}", time.perf_counter() - t0)
            return str(e)

    @mcp.tool()
    async def get_signals(paths: list[str], ctx: Context) -> list[dict[str, Any]] | str:
        """[Kuksa V2 API] Get current values of multiple VSS vehicle signals at once.

        Args:
            paths: List of VSS signal paths (e.g. ['Vehicle.Speed', 'Vehicle.Cabin.Door.Row1.Left.IsOpen']).
        """
        t0 = time.perf_counter()
        c = _client(ctx)
        if c is None:
            _log_call("get_signals", {"paths": paths}, "Not connected", time.perf_counter() - t0)
            return "Not connected to Kuksa Databroker"
        result = await c.get_values(paths)
        _log_call("get_signals", {"paths": paths}, result, time.perf_counter() - t0)
        return result

    @mcp.tool()
    async def set_signal(
        path: str,
        value: Any,
        datatype: str = "string",
        ctx: Context = None,
    ) -> dict[str, Any] | str:
        """[Kuksa V2 API] Set the target value of an actuator or attribute signal.

        Internally prefers the kuksa.val.v2 Actuate path; falls back to sdv.databroker.v1 if unavailable.

        Args:
            path: VSS signal path (e.g. 'Vehicle.Body.Windshield.Front.Wiping.System.TargetPosition').
            value: The value to set (as a string representation).
            datatype: The data type of the value ('string', 'bool', 'int32', 'int64', 'uint32', 'uint64', 'float', 'double').
        """
        t0 = time.perf_counter()
        c = _client(ctx)
        if c is None:
            _log_call("set_signal", {"path": path, "datatype": datatype}, "Not connected", time.perf_counter() - t0)
            return "Not connected to Kuksa Databroker"
        try:
            result = await c.set_value(path, value, datatype)
            _log_call("set_signal", {"path": path, "datatype": datatype}, result, time.perf_counter() - t0)
            return result
        except KuksaDatabrokerError as e:
            _log_call("set_signal", {"path": path, "datatype": datatype}, f"error: {e}", time.perf_counter() - t0)
            return str(e)

    @mcp.tool()
    async def list_signals(branch: str = "Vehicle", query: str = "", ctx: Context = None) -> list[dict[str, Any]] | str:
        """[Kuksa V1 / sdv.databroker.v1 API — DEPRECATED] List signals and their metadata under a given VSS branch.

        Use 'branch' to scope the search (e.g. 'Vehicle.Cabin' returns only cabin signals).
        Use 'query' to filter results by substring match on the signal path (case-insensitive).
        Leave both empty or use 'Vehicle' for the full tree.

        Note: This tool internally uses the deprecated sdv.databroker.v1.ListMetadata RPC.
        Prefer browsing signals via get_signal / get_signals with known paths when possible.

        Args:
            branch: VSS branch path (e.g. 'Vehicle', 'Vehicle.Cabin', 'Vehicle.Powertrain').
            query: Optional substring to filter signal paths (e.g. 'Speed', 'Door', 'Temperature').
        """
        t0 = time.perf_counter()
        c = _client(ctx)
        if c is None:
            _log_call("list_signals", {"branch": branch, "query": query}, "Not connected", time.perf_counter() - t0)
            return "Not connected to Kuksa Databroker"
        result = await c.list_signals(branch, query)
        _log_call("list_signals", {"branch": branch, "query": query}, result, time.perf_counter() - t0)
        return result

    @mcp.tool()
    async def count_signals(branch: str = "Vehicle", query: str = "", ctx: Context = None) -> int | str:
        """[Kuksa V1 / sdv.databroker.v1 API — DEPRECATED] Count signals under a VSS branch.

        Same search parameters as list_signals, but returns only the count.
        Useful for quickly checking how many signals exist without fetching details.

        Note: This tool internally uses the deprecated sdv.databroker.v1.ListMetadata RPC.

        Args:
            branch: VSS branch path (e.g. 'Vehicle', 'Vehicle.Cabin', 'Vehicle.Powertrain').
            query: Optional substring to filter signal paths (e.g. 'Speed', 'Door', 'Temperature').
        """
        t0 = time.perf_counter()
        c = _client(ctx)
        if c is None:
            _log_call("count_signals", {"branch": branch, "query": query}, "Not connected", time.perf_counter() - t0)
            return "Not connected to Kuksa Databroker"
        count = await c.count_signals(branch, query)
        _log_call("count_signals", {"branch": branch, "query": query}, f"{count} signals", time.perf_counter() - t0)
        return count

    @mcp.tool()
    async def get_target_values(paths: list[str], ctx: Context = None) -> list[dict[str, Any]] | str:
        """[Kuksa V1 / sdv.databroker.v1 API — DEPRECATED] Get the target (desired) values of actuator signals.

        The target value is the value the actuator *should* assume,
        as opposed to the current (sensed) value returned by get_signal.

        Note: This tool internally uses the deprecated sdv.databroker.v1 VAL.Get RPC with
        View.TARGET_VALUE. For reading actuation targets, prefer the Kuksa V2 Actuate flow
        (set_signal/get_signal) when possible.

        Args:
            paths: List of VSS signal paths (e.g. ['Vehicle.Body.Windshield.Front.Wiping.System.TargetPosition']).
        """
        t0 = time.perf_counter()
        c = _client(ctx)
        if c is None:
            _log_call("get_target_values", {"paths": paths}, "Not connected", time.perf_counter() - t0)
            return "Not connected to Kuksa Databroker"
        result = await c.get_target_values(paths)
        _log_call("get_target_values", {"paths": paths}, result, time.perf_counter() - t0)
        return result

    @mcp.tool()
    async def publish_value(
        path: str,
        value: Any,
        datatype: str = "string",
        ctx: Context = None,
    ) -> dict[str, Any] | str:
        """[Kuksa V2 API] Publish a current value for a signal (provider role).

        Unlike set_signal which sets the *target* for an actuator,
        publish_value directly sets the *current* value as reported
        by a sensor or provider. Use this when you are acting as a
        data provider feeding sensor readings into the databroker.

        Args:
            path: VSS signal path (e.g. 'Vehicle.Speed').
            value: The current value to publish.
            datatype: The data type ('string', 'bool', 'int32', 'int64', 'uint32', 'uint64', 'float', 'double').
        """
        t0 = time.perf_counter()
        c = _client(ctx)
        if c is None:
            _log_call("publish_value", {"path": path, "datatype": datatype}, "Not connected", time.perf_counter() - t0)
            return "Not connected to Kuksa Databroker"
        try:
            result = await c.publish_value(path, value, datatype)
            _log_call("publish_value", {"path": path, "datatype": datatype}, result, time.perf_counter() - t0)
            return result
        except KuksaDatabrokerError as e:
            _log_call("publish_value", {"path": path, "datatype": datatype}, f"error: {e}", time.perf_counter() - t0)
            return str(e)

    @mcp.tool()
    async def get_value_types(paths: list[str], ctx: Context = None) -> list[dict[str, Any]] | str:
        """[Kuksa V1 / sdv.databroker.v1 API — DEPRECATED] Get the data types of one or more VSS signals.

        Useful for determining how to interpret or set a signal value.

        Note: This tool internally uses the deprecated sdv.databroker.v1 VAL.Get RPC.
        Data type information is also available in the metadata returned by list_signals.

        Args:
            paths: List of VSS signal paths (e.g. ['Vehicle.Speed', 'Vehicle.Cabin.Door.Row1.Left.IsOpen']).
        """
        t0 = time.perf_counter()
        c = _client(ctx)
        if c is None:
            _log_call("get_value_types", {"paths": paths}, "Not connected", time.perf_counter() - t0)
            return "Not connected to Kuksa Databroker"
        result = await c.get_value_types(paths)
        _log_call("get_value_types", {"paths": paths}, result, time.perf_counter() - t0)
        return result

    @mcp.tool()
    async def server_info(ctx: Context = None) -> dict[str, Any] | str:
        """[Kuksa V1 / sdv.databroker.v1 API — DEPRECATED] Get information about the connected Kuksa Databroker server.

        Note: This tool internally uses the deprecated sdv.databroker.v1 GetServerInfo RPC.
        """
        t0 = time.perf_counter()
        c = _client(ctx)
        if c is None:
            _log_call("server_info", {}, "Not connected", time.perf_counter() - t0)
            return "Not connected to Kuksa Databroker"
        result = await c.get_server_info()
        _log_call("server_info", {}, result, time.perf_counter() - t0)
        return result
