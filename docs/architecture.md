# Architecture

## Overview

The Kuksa MCP Server follows a layered architecture that separates concerns between the MCP protocol layer, the application logic, and the Kuksa Databroker communication.

## Layers

```
┌─────────────────────────────────────────────────────┐
│                   MCP Client                         │
│           (Claude Desktop, Cursor, etc.)             │
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
│  │  5 MCP tools  │  │  3 MCP URIs  │                  │
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
│  └─────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │  gRPC (HTTP/2 + Protobuf)
┌──────────────────────▼──────────────────────────────┐
│            Eclipse Kuksa Databroker                   │
│           (kuksa.val.v2 gRPC API)                    │
└─────────────────────────────────────────────────────┘
```

## Module Descriptions

### `config.py`

Uses `pydantic-settings` to load configuration from environment variables (prefixed with `KUKSA_`). Provides a `KuksaConfig` dataclass that's injected into the client layer.

### `client.py`

Wraps the official `kuksa-client` library (`kuksa_client.grpc.aio.VSSClient`) into an async context manager. Each public method (`get_value`, `get_values`, `set_value`, `list_signals`, `get_server_info`) returns plain Python dicts. Errors are mapped to `KuksaDatabrokerError`.

### `tools.py`

Registers five MCP tools on the FastMCP server. Each tool function:
1. Extracts the client from `ctx.request_context.lifespan_context`
2. Calls the corresponding client method
3. Returns structured data or error messages

### `resources.py`

Registers three MCP resources with URI templates for reading signal values, listing branches, and checking server info. Resources return Markdown-formatted text.

### `server.py`

Creates the FastMCP instance with a lifespan context manager that connects/disconnects the Kuksa client. Provides `create_server()` and `run_server()` factory functions.

### `__main__.py`

CLI entry point with `argparse` for `--transport`, `--host`, `--port`, `--kuksa-host`, `--kuksa-port` flags.

## Transport Options

### stdio (default)
- JSON-RPC messages over stdin/stdout
- Used by Claude Desktop, Cursor, and most MCP clients
- Low latency, no network overhead
- No host/port configuration needed

### SSE (Server-Sent Events)
- HTTP-based transport for remote access
- Server pushes events via SSE, client sends POST requests
- Useful for:
  - Connecting from a different machine
  - Containerized deployments
  - Custom web UIs
- Default endpoint: `http://host:port/sse`

## Data Flow

1. **LLM decides to read a signal** → sends `tools/call` with `get_signal({"path": "Vehicle.Speed"})`
2. **FastMCP routes** the request to the `get_signal` tool function
3. **Tool function** calls `client.get_value("Vehicle.Speed")`
4. **Client layer** calls `VSSClient.get_current_values(["Vehicle.Speed"])` via gRPC
5. **Databroker** returns the current datapoint (value + timestamp)
6. **Client** converts the protobuf response to a Python dict
7. **Tool** returns the dict, FastMCP serializes it to JSON-RPC
8. **LLM receives** the structured data and uses it in its response

## Error Handling

- **Connection errors** → `KuksaDatabrokerError` with descriptive message
- **Signal not found** → `KuksaDatabrokerError("Signal 'X' not found")`
- **gRPC errors** → propagated as `KuksaDatabrokerError`
- **Tool errors** → returned as error content (not exceptions) so the LLM can handle them gracefully
