# Getting Started

## Prerequisites

- Python 3.11 or later
- A running Kuksa Databroker instance

## Starting a Kuksa Databroker

```bash
docker run -d --rm -p 55555:55555 --name kuksa-databroker \
  ghcr.io/eclipse-kuksa/kuksa-databroker:main --insecure
```

Verify:

```bash
docker logs kuksa-databroker
# Look for: "Kuksa Databroker started on 127.0.0.1:55555"
```

For production, see the [official Kuksa Databroker documentation](https://github.com/eclipse-kuksa/kuksa-databroker).

## Installation

### From PyPI

```bash
pip install kuksa-mcp-server
```

### From Source

```bash
git clone https://github.com/mikehaller/kuksa-mcp-server.git
cd kuksa-mcp-server
pip install -e ".[dev]"
```

## Running the Server

### stdio transport (default)

```bash
kuksa-mcp
```

Spawns as a subprocess — use with Claude Desktop, Cursor, or OpenCode (`kuksa-local`).

### SSE transport

```bash
kuksa-mcp --transport sse --host 0.0.0.0 --port 8765 --log-file kuksa-mcp.log
```

Runs as an HTTP server on `http://0.0.0.0:8765/sse`. Use with OpenCode's `kuksa-remote` variant, or when the server runs on a different machine.

### File logging

```bash
kuksa-mcp --log-file ./kuksa-mcp.log
```

Request logs go to both stderr and the file. Rotate externally (logrotate, etc.).

## CLI Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--transport` | `stdio` | `stdio` or `sse` |
| `--host` | `127.0.0.1` | Bind address for SSE |
| `--port` | `8765` | Port for SSE |
| `--kuksa-host` | env `KUKSA_HOST` | Databroker gRPC host |
| `--kuksa-port` | env `KUKSA_PORT` | Databroker gRPC port |
| `--log-file` | *(none)* | Path to request log file |

## Configuration

Environment variables (also loadable from `.env`):

```env
KUKSA_HOST=127.0.0.1
KUKSA_PORT=55555
KUKSA_TOKEN=
```

## OpenCode Configuration

The repo ships with `opencode.jsonc` in the project root. Two pre-configured entries:

### `kuksa-local` (stdio, auto-spawned)

Enabled by default. OpenCode spawns `kuksa-mcp` as a subprocess and communicates over stdin/stdout.

Edit `opencode.jsonc`:

```jsonc
"kuksa-local": {
  "type": "local",
  "command": [".venv/bin/python", "-m", "kuksa_mcp_server", "--log-file", "./kuksa-mcp.log"],
  "enabled": true,
  "timeout": 10000
}
```

### `kuksa-remote` (SSE, manual start)

Disabled by default. Start the server first:

```bash
kuksa-mcp --transport sse --host 0.0.0.0 --port 8765 --log-file kuksa-mcp.log
```

Then enable in `opencode.jsonc`:

```jsonc
"kuksa-remote": {
  "type": "remote",
  "url": "http://127.0.0.1:8765/sse",
  "enabled": true,
  "timeout": 10000
}
```

## MCP Client Configuration

### Claude Desktop / Cursor

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "kuksa": {
      "command": "kuksa-mcp"
    }
  }
}
```

For SSE:

```json
{
  "mcpServers": {
    "kuksa": {
      "type": "sse",
      "url": "http://127.0.0.1:8765/sse"
    }
  }
}
```

### Custom Python Client

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server = StdioServerParameters(command="kuksa-mcp")

async with stdio_client(server) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("get_signal", {"path": "Vehicle.Speed"})
        print(result.content)
```

## Verifying the Setup

```bash
# Check server info
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"server_info","arguments":{}}}' | kuksa-mcp

# Get a signal value
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_signal","arguments":{"path":"Vehicle.Speed"}}}' | kuksa-mcp
```

The startup banner appears on stderr. Every request (initialize, tools/list, tools/call) is logged with timestamp and latency.
