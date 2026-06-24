# Kuksa MCP Server Documentation

Welcome to the Kuksa MCP Server documentation. This project provides a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) interface to the [Eclipse Kuksa Databroker](https://eclipse.dev/kuksa/), enabling LLMs to interact with vehicle data in real time.

## Overview

The Kuksa Databroker is an in-vehicle data broker that implements the [COVESA Vehicle Signal Specification (VSS)](https://covesa.github.io/vehicle_signal_specification/). It exposes vehicle signals (sensors, actuators, attributes) via a gRPC API. This MCP server wraps that API into tools and resources that LLMs can call through any MCP-compatible client.

```
┌──────────────┐     stdio/json-rpc     ┌──────────────────┐     gRPC     ┌──────────────────┐
│  LLM / MCP   │ ◄───────────────────► │  kuksa-mcp-server │ ◄──────────► │  Kuksa Databroker │
│  Client      │                        │  (Python)         │              │  (port 55555)     │
└──────────────┘                        └──────────────────┘              └──────────────────┘
```

## Quick Reference

| Feature | Details |
|---------|---------|
| **Protocol** | MCP (Model Context Protocol) |
| **Transport** | stdio (default) or SSE |
| **Target API** | Kuksa Databroker v2 (with v1 fallback for some endpoints) |
| **Python** | 3.11+ |
| **License** | Apache 2.0 |

## Tools (9 total)

| Tool | API | Description |
|------|-----|-------------|
| `get_signal(path)` | Kuksa V2 | Read one current value |
| `get_signals(paths)` | Kuksa V2 | Batch read current values |
| `set_signal(path, value, datatype)` | Kuksa V2 | Set actuator target |
| `publish_value(path, value, datatype)` | Kuksa V2 | Publish sensor reading |
| `list_signals(branch, query)` | V1 | Browse signal catalog |
| `count_signals(branch, query)` | V1 | Count matching signals |
| `get_target_values(paths)` | V1 | Read actuator targets |
| `get_value_types(paths)` | V1 | Query data types |
| `server_info()` | V1 | Server name/version |

## Documentation Sections

- **[Getting Started](getting-started.md)** — Installation, Docker, configuration, and MCP client setup
- **[Architecture](architecture.md)** — Module descriptions, data flow, API versioning, error handling
- **[Example Prompts](../examples/prompts.md)** — Ready-to-use prompts for the LLM

## Supported VSS Signals

The Kuksa Databroker supports any VSS signal. Common examples:

| Path | Type | Description |
|------|------|-------------|
| `Vehicle.Speed` | Sensor | Current vehicle speed |
| `Vehicle.Cabin.Door.Row1.Left.IsOpen` | Sensor | Door open/closed state |
| `Vehicle.Body.Windshield.Front.Wiping.System.TargetPosition` | Actuator | Wiper position control |
| `Vehicle.Powertrain.CombustionEngine.Engine.Speed` | Sensor | Engine RPM |
| `Vehicle.Exhaust.NOx.Sensor1.AmbientHumidity` | Sensor | Ambient humidity |
