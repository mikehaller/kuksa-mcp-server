# Getting Started

## Prerequisites

- Python 3.11 or later
- A running Kuksa Databroker instance

## Starting a Kuksa Databroker

The easiest way to get a Databroker for testing:

```bash
docker run -d --rm -p 55555:55555 --name kuksa-databroker \
  ghcr.io/eclipse-kuksa/kuksa-databroker:main --insecure
```

Verify it's running:

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

This is the default transport, suitable for use with Claude Desktop, Cursor, or any MCP client that spawns a subprocess.

### SSE transport

```bash
kuksa-mcp --transport sse --host 127.0.0.1 --port 8765
```

Useful for remote connections or when you need HTTP access.

### Configuration

You can configure the Kuksa Databroker connection via environment variables:

```bash
export KUKSA_HOST=192.168.1.100
export KUKSA_PORT=55555
export KUKSA_INSECURE=true
kuksa-mcp
```

Or via `.env` file in the working directory:

```env
KUKSA_HOST=127.0.0.1
KUKSA_PORT=55555
KUKSA_INSECURE=true
```

## MCP Client Configuration

### Claude Desktop

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

To use SSE instead:

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
