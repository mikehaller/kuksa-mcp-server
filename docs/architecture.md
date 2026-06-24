# Architecture

## Overview

The Kuksa MCP Server follows a layered architecture that separates concerns between the MCP protocol layer, the application logic, and the Kuksa Databroker communication.

## Layers

```
┌─────────────────────────────────────────────────────┐
│                   MCP Client                         │
│    (Claude Desktop, Cursor, OpenCode, custom)        │
└──────────────────────┬──────────────────────────────┘
                       │  JSON-RPC over stdio / HTTP-SSE
┌──────────────────────▼──────────────────────────────┐
│                  FastMCP Framework                    │
│  ┌─────────────────────────────────────────────────┐ │
│  │  mcp.server.fastmcp.FastMCP                     │ │
│  │  • Request routing                              │ │
│  │  • Lifespan management                          │ │
│  │  • Lifecycle & error handling                   │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Application Layer                        │
│  ┌──────────────┐  ┌──────────────┐                  │
│  │   tools.py   │  │ resources.py │                  │
│  │  9 MCP tools  │  │  3 MCP URIs  │                  │
│  └──────┬───────┘  └──────┬───────┘                  │
└─────────┼──────────────────┼────────────────────────┘
          │                  │
┌─────────▼──────────────────▼────────────────────────┐
│              Client Layer                             │
│  ┌─────────────────────────────────────────────────┐ │
│  │  client.py: KuksaDatabrokerClient               │ │
│  │  • Wraps kuksa_client.grpc.aio.VSSClient       │ │
│  │  • Async connection management                  │ │
│  │  • Error handling & type conversion             │ │
│  │  • Methods: get_value, get_values, set_value,   │ │
│  │    get_target_values, publish_value,            │ │
│  │    get_value_types, list_signals, count_signals, │ │
│  │    get_server_info, get_signal_stats             │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │  gRPC (HTTP/2 + Protobuf)
┌──────────────────────▼──────────────────────────────┐
│            Eclipse Kuksa Databroker                   │
│           (kuksa.val.v2 + sdv.databroker.v1)         │
└─────────────────────────────────────────────────────┘
```

## Module Descriptions

### `config.py`

Uses `pydantic-settings` to load configuration from environment variables (prefixed with `KUKSA_`). Provides a `KuksaConfig` dataclass injected into the client layer.

### `client.py`

Wraps the official `kuksa-client` library (`kuksa_client.grpc.aio.VSSClient`) into an async context manager. Each public method returns plain Python dicts. Errors are mapped to `KuksaDatabrokerError`.

Methods:
- `get_value`, `get_values` — reads via `get_current_values` (Kuksa V2)
- `set_value` — actuator target via `set_target_values` (prefers V2 Actuate)
- `publish_value` — current value via `set_current_values` (prefers V2)
- `get_target_values` — actuator targets via V1 `get` (deprecated)
- `get_value_types` — data types via V1 `get` (deprecated)
- `list_signals`, `count_signals` — metadata via V1 `get` (deprecated)
- `get_server_info` — server name/version via V1 (deprecated)
- `get_signal_stats` — counts and aggregates catalog metadata

### `tools.py`

Registers 9 MCP tools on the FastMCP server. Each tool:
1. Extracts the client from `ctx.request_context.lifespan_context`
2. Calls the corresponding client method
3. Logs the call (name, params, result summary, elapsed time) via the `_log_call` helper
4. Returns structured data or error messages

### `resources.py`

Registers 3 MCP resources:
- `kuksa://info` — static server and tool reference
- `kuksa://signals/{path}` — returns a hint to use the `get_signal` tool
- `kuksa://branches/{path}` — returns a hint to use the `list_signals` tool

### `server.py`

Creates the FastMCP instance with a lifespan context manager that connects/disconnects the Kuksa client. Provides `create_server()` and `run_server()` factory functions. Configures logging (stderr + optional file). Routes FastMCP's internal `Processing request of type` messages through the same handlers so all request activity is visible in logs.

### `__main__.py`

CLI entry point with `argparse` for `--transport`, `--host`, `--port`, `--kuksa-host`, `--kuksa-port`, `--log-file`.

### Startup Sequence

1. `configure_logging()` sets up stderr + optional file handler
2. Signal handlers installed (first Ctrl-C = graceful shutdown, second = force)
3. Lifespan starts: banner printed, databroker connected, catalog stats fetched
4. Server accepts requests (stdio or SSE)
5. Each request logged: `Processing request of type <X>` + tool-specific `_log_call`
6. On shutdown: client disconnected, "Goodbye" logged

## Transport Options

### stdio (default)
- JSON-RPC messages over stdin/stdout
- Used by Claude Desktop, Cursor, OpenCode (`kuksa-local`)
- Low latency, auto-spawned by the MCP client
- No network configuration needed

### SSE (Server-Sent Events)
- HTTP-based transport for remote access
- Server listens on `http://host:port/sse`
- Used by OpenCode (`kuksa-remote`, manual start)
- Useful for multi-user setups, containerized deployments, cross-machine access

## Data Flow

1. **LLM decides to read a signal** → sends `tools/call` with `get_signal({"path": "Vehicle.Speed"})`
2. **Request logged** → `Processing request of type CallToolRequest`
3. **Tool function** calls `client.get_value("Vehicle.Speed")`
4. **Client layer** calls `VSSClient.get_current_values(["Vehicle.Speed"])` via gRPC
5. **Databroker** returns the current datapoint (value + timestamp)
6. **Tool** returns the dict, FastMCP serializes it to JSON-RPC
7. **Result logged** → `get_signal(args={'path': 'Vehicle.Speed'}) -> ok [0.023s]`
8. **LLM receives** the structured data

## API Versioning

Tools are tagged in their descriptions with the underlying Kuksa API version:

| Tag | Tools | Backend |
|-----|-------|---------|
| `[Kuksa V2 API]` | `get_signal`, `get_signals`, `set_signal`, `publish_value` | `kuksa.val.v2` |
| `[V1 (deprecated)]` | `list_signals`, `count_signals`, `get_target_values`, `get_value_types`, `server_info` | `sdv.databroker.v1` |

## Error Handling

- **Connection errors** → `KuksaDatabrokerError` with descriptive message
- **Signal not found** → `KuksaDatabrokerError("Signal 'X' not found")`
- **gRPC errors** → propagated as `KuksaDatabrokerError`
- **Tool errors** → returned as string content (not exceptions) so the LLM can handle them gracefully
- **Not connected** → each tool returns `"Not connected to Kuksa Databroker"` when the lifespan has no client
