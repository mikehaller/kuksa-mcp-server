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
- **Dual transport** — stdio (default, for Claude Desktop/Cursor/OpenCode) and SSE (for HTTP clients)
- **OpenCode ready** — Works out of the box with [OpenCode](https://opencode.ai) CLI

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

Add to your MCP client configuration:

<details>
<summary>Claude Desktop / Cursor (<code>claude_desktop_config.json</code>)</summary>

```json
{
  "mcpServers": {
    "kuksa": {
      "command": "kuksa-mcp"
    }
  }
}
```
</details>

<details>
<summary>OpenCode — stdio variant (<code>opencode.json</code> in project root)</summary>

```json
{
  "mcpServers": {
    "kuksa-local": {
      "type": "local",
      "command": ["kuksa-mcp", "--log-file", "./kuksa-mcp.log"],
      "enabled": true,
      "timeout": 10000
    }
  }
}
```
</details>

<details>
<summary>OpenCode — SSE variant (<code>opencode.json</code> in project root)</summary>

```json
{
  "mcpServers": {
    "kuksa-remote": {
      "type": "remote",
      "url": "http://127.0.0.1:8765/sse",
      "enabled": true,
      "timeout": 10000
    }
  }
}
```
</details>

## OpenCode MCP Server Variants

The project includes two pre-configured MCP server entries in `opencode.jsonc`:

### `kuksa-local` (stdio)

- **Transport**: stdio — the server runs as a subprocess of OpenCode
- **Default**: enabled
- **When to use**: local development, single-user setup, low latency
- **How it works**: OpenCode spawns `kuksa-mcp` directly, communicates over stdin/stdout
- **Pros**: no network ports, auto-start/stop with OpenCode, simplest setup
- **Cons**: only works on the machine where the venv and Kuksa Databroker are running

### `kuksa-remote` (SSE)

- **Transport**: SSE (HTTP Server-Sent Events) — the server runs independently
- **Default**: disabled (enable by setting `"enabled": true`)
- **When to use**: multi-user access, containerized deployment, remote databroker
- **How it works**: start the server manually with `kuksa-mcp --transport sse`, OpenCode connects via HTTP
- **Pros**: can run on a different machine, survives client restarts
- **Cons**: requires manual start/stop, port must be accessible, slightly higher latency

### Choosing between them

| Situation | Use |
|-----------|-----|
| You're developing locally on the same machine | `kuksa-local` |
| You want OpenCode to auto-manage the server | `kuksa-local` |
| The server runs in a Docker/remote host | `kuksa-remote` |
| Multiple clients need the same server | `kuksa-remote` |
| You're testing or debugging the MCP server | `kuksa-local` |

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

| Tool | API | Description |
|------|-----|-------------|
| `get_signal(path)` | Kuksa V2 | Get current value of one VSS signal |
| `get_signals(paths)` | Kuksa V2 | Get current values of multiple signals |
| `set_signal(path, value, datatype)` | Kuksa V2 | Set an actuator target value |
| `publish_value(path, value, datatype)` | Kuksa V2 | Publish a sensor reading (provider role) |
| `list_signals(branch, query)` | V1 (deprecated) | List signals and metadata under a VSS branch |
| `count_signals(branch, query)` | V1 (deprecated) | Count signals under a branch |
| `get_target_values(paths)` | V1 (deprecated) | Read actuator target/desired values |
| `get_value_types(paths)` | V1 (deprecated) | Get data types for signals |
| `server_info()` | V1 (deprecated) | Get databroker server information |

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
