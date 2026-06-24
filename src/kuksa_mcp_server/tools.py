from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context

from kuksa_mcp_server.client import KuksaDatabrokerClient, KuksaDatabrokerError


def register_tools(mcp: Any) -> None:
    def _client(ctx: Context) -> KuksaDatabrokerClient | None:
        return ctx.request_context.lifespan_context._kuksa_client

    @mcp.tool()
    async def get_signal(path: str, ctx: Context) -> dict[str, Any] | str:
        """Get the current value and metadata of a single VSS vehicle signal.

        Args:
            path: VSS signal path (e.g. 'Vehicle.Speed', 'Vehicle.Cabin.Door.Row1.Left.IsOpen').
        """
        c = _client(ctx)
        if c is None:
            return "Not connected to Kuksa Databroker"
        try:
            return await c.get_value(path)
        except KuksaDatabrokerError as e:
            return str(e)

    @mcp.tool()
    async def get_signals(paths: list[str], ctx: Context) -> list[dict[str, Any]] | str:
        """Get current values of multiple VSS vehicle signals at once.

        Args:
            paths: List of VSS signal paths (e.g. ['Vehicle.Speed', 'Vehicle.Cabin.Door.Row1.Left.IsOpen']).
        """
        c = _client(ctx)
        if c is None:
            return "Not connected to Kuksa Databroker"
        return await c.get_values(paths)

    @mcp.tool()
    async def set_signal(
        path: str,
        value: Any,
        datatype: str = "string",
        ctx: Context = None,
    ) -> dict[str, Any] | str:
        """Set the target value of an actuator or attribute signal.

        Args:
            path: VSS signal path (e.g. 'Vehicle.Body.Windshield.Front.Wiping.System.TargetPosition').
            value: The value to set (as a string representation).
            datatype: The data type of the value ('string', 'bool', 'int32', 'int64', 'uint32', 'uint64', 'float', 'double').
        """
        c = _client(ctx)
        if c is None:
            return "Not connected to Kuksa Databroker"
        try:
            return await c.set_value(path, value, datatype)
        except KuksaDatabrokerError as e:
            return str(e)

    @mcp.tool()
    async def list_signals(branch: str = "Vehicle", ctx: Context = None) -> list[dict[str, Any]] | str:
        """List all signals and their metadata under a given VSS branch.

        Args:
            branch: VSS branch path (e.g. 'Vehicle', 'Vehicle.Cabin', 'Vehicle.Powertrain').
        """
        c = _client(ctx)
        if c is None:
            return "Not connected to Kuksa Databroker"
        return await c.list_signals(branch)

    @mcp.tool()
    async def server_info(ctx: Context = None) -> dict[str, Any] | str:
        """Get information about the connected Kuksa Databroker server."""
        c = _client(ctx)
        if c is None:
            return "Not connected to Kuksa Databroker"
        return await c.get_server_info()
