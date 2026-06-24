# API Coverage: MCP Tools vs. Kuksa Databroker API v2

This document maps the Eclipse Kuksa Databroker gRPC API surface to the MCP tools exposed by this server. Methods are grouped by functional category.

## Legend

| Icon | Meaning |
|------|---------|
| ✅ | Exposed as an MCP tool |
| ⚠️ | Used internally but not directly exposed |
| ❌ | Not wrapped in `client.py` or `tools.py` |

## Coverage Table

| Category | Kuksa API Method | API Ver | Wrapped in `client.py` | MCP Tool / Resource | Notes |
|---|---|---|---|---|---|
| **Info** | `GetServerInfo` | v1 | `get_server_info()` | `server_info()` | ✅ |
| **Read** | `GetCurrentValues` | v1 | `get_value()`, `get_values()` | `get_signal()`, `get_signals()` | ✅ |
| **Read** | `GetTargetValues` | v1 | ❌ | ❌ | Cannot read actuator targets |
| **Write** | `Set` / `PublishValue` (current) | v1/v2 | ❌ | ❌ | Cannot publish sensor/attribute values |
| **Write** | `Set` (target) | v1 | `set_value()` | `set_signal()` | ✅ Uses `set_target_values` internally |
| **Write** | `Set` (metadata) | v1 | ❌ | ❌ | Cannot update metadata |
| **Metadata** | `GetMetadata` | v1 | `list_signals()` | `list_signals()` | ⚠️ Used internally for tree browsing; no raw metadata tool |
| **Metadata** | `ListMetadata` | v2 | ❌ | ❌ | No v2 metadata listing exposed |
| **Subscribe** | `Subscribe` (current values) | v1/v2 | ❌ | ❌ | ❌ |
| **Subscribe** | `Subscribe` / `OpenProviderStream` (target) | v1/v2 | ❌ | ❌ | ❌ |
| **Subscribe** | `Subscribe` (metadata) | v1 | ❌ | ❌ | ❌ |
| **Auth** | `GetServerInfo` (token update) | v1 | ❌ | ❌ | `authorize()` not wrapped |
| **Internal** | `get_value_types` | v1 | ❌ | ❌ | Low-level type resolution |
| **Internal** | `ensure_id_mapping` | v2 | ❌ | ❌ | v2 path-to-ID mapping |

## Summary

| Status | Count | Details |
|--------|-------|---------|
| ✅ MCP tools | 5 | `get_signal`, `get_signals`, `set_signal`, `list_signals`, `server_info` |
| ⚠️ Internal use | 1 | `get_metadata` used by `list_signals` |
| ❌ Not exposed | 10+ | All subscribe/streaming, target reads, metadata writes, v2-specific APIs |

## Key Gaps

### 1. Streaming / Subscriptions (❌)

The Kuksa API supports real-time subscriptions for current values, target values, and metadata changes. None are exposed via MCP — MCP has no native streaming tool primitive, so these would need a polling workaround or an SSE-based resource.

- `Subscribe` (current values, v1+v2)
- `OpenProviderStream` / `Subscribe` (target/actuation, v1+v2)
- `Subscribe` (metadata, v1-only)

### 2. Read Actuator Targets (❌)

`GetTargetValues` lets you read the currently-set target for an actuator. Only `GetCurrentValues` is wrapped.

### 3. Publish Sensor Values (❌)

`SetCurrentValues` (which tries v2 `PublishValue` then falls back to v1 `Set`) is not exposed. The existing `set_signal` tool calls `set_target_values`, so it only works for actuators/attributes, not for feeding sensor data into the broker.

### 4. Metadata Mutation (❌)

`SetMetadata` is not wrapped, so programmatic metadata updates (e.g. changing descriptions, units, or data types at runtime) are not possible.

### 5. Authorization (❌)

`authorize(token)` allows runtime token rotation. Not exposed — authorization is only possible at startup via the `KUKSA_TOKEN` environment variable.

### 6. v2-Specific Methods (❌)

Direct access to v2-only methods (`ListMetadata`, `Subscribe`, `OpenProviderStream`, `PublishValue`) is not available through the MCP interface.
