# Example Prompts

Example prompts to use with the Kuksa MCP server via your LLM client (Claude Desktop, Cursor, opencode, etc.).

## Prerequisites

Make sure your MCP client has the Kuksa server configured and a Kuksa Databroker is running. See [getting-started.md](../docs/getting-started.md).

---

## Reading Signals

### Check current speed

```
What is the current vehicle speed? Use the kuksa tool.
```

### Check multiple signals at once

```
Read the current values of Vehicle.Speed, Vehicle.Cabin.Door.Row1.Left.IsOpen, and Vehicle.Powertrain.CombustionEngine.Engine.Speed.
```

### Check if a door is open

```
Is the driver's door currently open? Check the Vehicle.Cabin.Door.Row1.Left.IsOpen signal.
```

---

## Browsing the Signal Catalog

### List all signals

```
What signals are available under Vehicle.Cabin? Use list_signals.
```

### Search for signals by keyword

```
List all signals related to "Temperature" in the vehicle.
```

### Find signals by type

```
Show me all actuator signals I can control.
```

### Explore a specific subsystem

```
What signals are available under Vehicle.Body.Windshield?
```

---

## Setting Actuator Values

### Control the wipers

```
Set the windshield wiper target position to 90 degrees.
```

### Set a value with specific datatype

```
Set the Vehicle.Cabin.Door.Row1.Left.IsOpen signal to false (it's a boolean).
```

---

## Diagnostics & Info

### Check server status

```
What version of the Kuksa Databroker am I connected to? How many signals are available?
```

### Full vehicle status report

```
Run a full status check: read all the key vehicle signals (speed, doors, lights, wipers, battery) and summarize the current vehicle state.
```

---

## Short Commands (when LLM context is tight)

```
kuksa: read Vehicle.Speed
```

```
kuksa: list signals matching "Door"
```

```
kuksa: set Vehicle.Cabin.Door.Row1.Left.IsOpen = true
```

---

## Troubleshooting

### Not connected

If you see `Not connected to Kuksa Databroker`, the MCP server is running but cannot reach the databroker. Ensure it's running:

```bash
docker ps | grep kuksa-databroker
```

### Signal not found

If a signal returns "not found", it may not exist in this vehicle's VSS catalog. Use `list_signals` with a `query` parameter to discover valid paths.
