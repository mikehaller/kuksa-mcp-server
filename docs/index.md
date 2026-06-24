# Kuksa MCP Server Documentation

Welcome to the Kuksa MCP Server documentation. This project provides a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) interface to the [Eclipse Kuksa Databroker](https://eclipse.dev/kuksa/), enabling LLMs to interact with vehicle data in real time.

## Overview

The Kuksa Databroker is an in-vehicle data broker that implements the [COVESA Vehicle Signal Specification (VSS)](https://covesa.github.io/vehicle_signal_specification/). It exposes vehicle signals (sensors, actuators, attributes) via a gRPC API. This MCP server wraps that API into tools and resources that LLMs can call through any MCP-compatible client (Claude Desktop, Cursor, custom clients).

### How it works

```
┌──────────────┐     stdio/json-rpc     ┌──────────────────┐     gRPC     ┌──────────────────┐
│  LLM / MCP   │ ◄───────────────────► │  kuksa-mcp-server │ ◄──────────► │  Kuksa Databroker │
│  Client      │                        │  (Python)         │              │  (port 55555)     │
└──────────────┘                        └──────────────────┘              └──────────────────┘
```

## Documentation Sections

- **[Getting Started](getting-started.md)** — Installation, configuration, and quick start
- **[Architecture](architecture.md)** — Project architecture, data flow, and design decisions
- **[API Coverage](api-coverage.md)** — MCP tool coverage vs. Kuksa Databroker gRPC API

## Supported VSS Signals

The Kuksa Databroker supports any VSS signal. Common examples:

| Path | Type | Description |
|------|------|-------------|
| `Vehicle.Speed` | Sensor | Current vehicle speed |
| `Vehicle.Cabin.Door.Row1.Left.IsOpen` | Sensor | Door open/closed state |
| `Vehicle.Body.Windshield.Front.Wiping.System.TargetPosition` | Actuator | Wiper position control |
| `Vehicle.Powertrain.CombustionEngine.Engine.Speed` | Sensor | Engine RPM |
| `Vehicle.Exhaust.NOx.Sensor1.AmbientHumidity` | Sensor | Ambient humidity |
