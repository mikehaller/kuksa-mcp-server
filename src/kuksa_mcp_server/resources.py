from __future__ import annotations

from typing import Any


def register_resources(mcp: Any) -> None:
    @mcp.resource("kuksa://info")
    async def info_resource() -> str:
        """Information about the Kuksa Databroker MCP Server."""
        return """# Kuksa Databroker MCP Server

## Available Tools
- **get_signal** — Read a vehicle signal value
- **get_signals** — Read multiple signal values
- **set_signal** — Set an actuator/attribute value
- **list_signals** — Browse VSS signals under a branch
- **server_info** — Get server information

## Configuration
Set environment variables:
- `KUKSA_HOST` — Databroker host (default: 127.0.0.1)
- `KUKSA_PORT` — gRPC port (default: 55555)
- `KUKSA_INSECURE` — Allow insecure (default: true)
"""

    @mcp.resource("kuksa://signals/{path}")
    async def signal_resource(path: str) -> str:
        """Read the current value of a VSS signal.

        URI format: kuksa://signals/{vss_path}
        Example: kuksa://signals/Vehicle.Speed
        """
        return f"Use `get_signal` tool to read `{path}`"

    @mcp.resource("kuksa://branches/{path}")
    async def branch_resource(path: str) -> str:
        """List signals under a VSS branch.

        URI format: kuksa://branches/{vss_branch}
        Example: kuksa://branches/Vehicle.Cabin
        """
        return f"Use `list_signals` tool to browse `{path}`"
