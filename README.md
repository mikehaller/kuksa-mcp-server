# Kuksa MCP Server

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](pyproject.toml)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that connects LLMs to vehicle data via the [Eclipse Kuksa Databroker](https://eclipse.dev/kuksa/). Enables AI assistants to read and write vehicle signals using the standardized COVESA Vehicle Signal Specification (VSS).

## Features

- **Read vehicle signals** — Get current values of any VSS signal (speed, doors, battery, etc.)
- **Batch reads** — Fetch multiple signals in a single call
- **Write actuators** — Set target values for actuators and attributes
- **Browse the VSS tree** — List signals and their metadata under any branch
- **Server introspection** — Get connection and server info
- **Dual transport** — stdio (default, for Claude Desktop/Cursor) and SSE (for HTTP clients)

## Quick Start

### 1. Start a Kuksa Databroker

```bash
docker run -d --rm -p 55555:55555 --name kuksa-databroker \
  ghcr.io/eclipse-kuksa/kuksa-databroker:main --insecure
```

### 2. Install & Run

```bash
pip install kuksa-mcp-server
kuksa-mcp
```

Or from source:

```bash
git clone https://github.com/mikehaller/kuksa-mcp-server.git
cd kuksa-mcp-server
pip install -e ".[dev]"
kuksa-mcp
```

### 3. Configure your MCP client

Add to your MCP client configuration (e.g., `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "kuksa": {
      "command": "kuksa-mcp"
    }
  }
}
```

## Configuration

All settings are configurable via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `KUKSA_HOST` | `127.0.0.1` | Kuksa Databroker host |
| `KUKSA_PORT` | `55555` | Kuksa Databroker gRPC port |
| `KUKSA_TOKEN` | *(none)* | JWT token for authorization |

Or via CLI flags:

```bash
kuksa-mcp --transport sse --host 0.0.0.0 --port 8765 \
  --kuksa-host 192.168.1.100 --kuksa-port 55555
```

## Tools

| Tool | Description |
|------|-------------|
| `get_signal(path)` | Get current value of one VSS signal |
| `get_signals(paths)` | Get current values of multiple signals |
| `set_signal(path, value, datatype)` | Set a signal target value |
| `list_signals(branch)` | List signals and metadata under a VSS branch |
| `server_info()` | Get databroker server information |

## Resources

| URI | Description |
|-----|-------------|
| `kuksa://signals/{path}` | Read signal value and metadata |
| `kuksa://branches/{path}` | List signals under a VSS branch |
| `kuksa://info` | Server connection information |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with SSE transport for testing
kuksa-mcp --transport sse

# Run local test against Ollama
python examples/local_test.py
```

## License

Apache 2.0 — see [LICENSE](LICENSE).
