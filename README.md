# Kuksa MCP Server

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](pyproject.toml)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that connects LLMs to vehicle data via the [Eclipse Kuksa Databroker](https://eclipse.dev/kuksa/). Enables AI assistants to read and write vehicle signals using the standardized COVESA Vehicle Signal Specification (VSS).

## Features

- **Read signals** — Get current or target values of any VSS signal
- **Batch reads** — Fetch multiple signals in a single call
- **Write actuators** — Set actuator targets or publish sensor readings
- **Browse the VSS tree** — List or count signals under any branch, with substring filtering
- **Inspect types** — Query data types for any signal path
- **Server introspection** — Name, version, signal count at startup
- **Per-request logging** — Every tool call logged with params, timing, and result summary
- **Dual transport** — stdio (default) and SSE (HTTP)
- **OpenCode ready** — Pre-configured `opencode.jsonc` for local and remote variants

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
<summary>OpenCode — stdio variant (<code>opencode.jsonc</code> in project root)</summary>

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
<summary>OpenCode — SSE variant (<code>opencode.jsonc</code> in project root)</summary>

```json
{
  "mcpServers": {
    "kuksa-remote": {
      "type": "remote",
      "url": "http://127.0.0.1:8765/sse",
      "enabled": false,
      "timeout": 10000
    }
  }
}
```
</details>

## OpenCode MCP Server Variants

The project ships with two entries in `opencode.jsonc`:

| Variant | Transport | Default | Use case |
|---------|-----------|---------|----------|
| `kuksa-local` | stdio (subprocess) | enabled | Local dev, single-user, auto-managed |
| `kuksa-remote` | SSE (HTTP) | disabled | Multi-user, containerized, remote databroker |

Start the remote variant manually:
```bash
kuksa-mcp --transport sse --host 0.0.0.0 --port 8765
```

## CLI Reference

```
kuksa-mcp [options]

Options:
  --transport <stdio|sse>   Transport protocol (default: stdio)
  --host <ip>               Bind address for SSE (default: 127.0.0.1)
  --port <port>             Port for SSE (default: 8765)
  --kuksa-host <host>       Databroker host (overrides KUKSA_HOST env)
  --kuksa-port <port>       Databroker port (overrides KUKSA_PORT env)
  --log-file <path>         File path for request logging (also written to stderr)
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KUKSA_HOST` | `127.0.0.1` | Kuksa Databroker host |
| `KUKSA_PORT` | `55555` | Kuksa Databroker gRPC port |
| `KUKSA_TOKEN` | *(none)* | JWT token for authorization |

## Tools

| Tool | API | Description |
|------|-----|-------------|
| `get_signal(path)` | Kuksa V2 | Get current value of one VSS signal |
| `get_signals(paths)` | Kuksa V2 | Get current values of multiple signals |
| `set_signal(path, value, datatype)` | Kuksa V2 | Set an actuator target value |
| `publish_value(path, value, datatype)` | Kuksa V2 | Publish a sensor reading (provider role) |
| `list_signals(branch, query)` | V1 (deprecated) | List signals and metadata under a branch |
| `count_signals(branch, query)` | V1 (deprecated) | Count signals matching a filter |
| `get_target_values(paths)` | V1 (deprecated) | Read actuator target/desired values |
| `get_value_types(paths)` | V1 (deprecated) | Get data types for one or more signals |
| `server_info()` | V1 (deprecated) | Get databroker name, version, address |

## Resources

| URI | Description |
|-----|-------------|
| `kuksa://info` | Server and tool reference |
| `kuksa://signals/{path}` | Signal info (redirects to tool) |
| `kuksa://branches/{path}` | Branch listing (redirects to tool) |

## Startup Output

On startup the server prints a banner with version, databroker info, and catalog stats:

```
======================================================
  Kuksa Databroker MCP Server
  Version : 0.1.0
  Built   : 2026-06-24
======================================================
  Backend : databroker
  Address : 127.0.0.1:55555
  Version : 0.7.0-dev.0
  Status  : connected
  Signals : 1263 total
  Types   : ACTUATOR=643, ATTRIBUTE=130, SENSOR=490
======================================================
```

Every tool call is logged:

```
09:45:12 [INFO] Processing request of type ListToolsRequest
09:45:12 [INFO] Processing request of type CallToolRequest
09:45:12 [INFO] get_signal(args={'path': 'Vehicle.Speed'}) -> ok [0.023s]
09:45:15 [INFO] list_signals(args={'branch': 'Vehicle.Cabin', 'query': ''}) -> 490 results [0.045s]
```

## Development

```bash
pip install -e ".[dev]"
pytest
kuksa-mcp --transport sse
python examples/local_test.py
```

## License

Apache 2.0 — see [LICENSE](LICENSE).
