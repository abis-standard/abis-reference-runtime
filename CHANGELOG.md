# Changelog

## v0.5.0 — Developer Preview (invoke provenance & transport neutrality)

### Added

- `execution_provenance` block on Invoke responses (implementation-level audit metadata)
- Result portability tests (`tests/test_result_portability.py`)

### Changed

- **Breaking:** removed HTTP top-level aliases `reservation_id`, `crs_native_result`, `native_external_identifier`
- Canonical external identifier: `native_result.external_identifier`
- Canonical opaque native data: `native_result.payload`
- Profile v3 (`profile_version=3`) — removed ambiguous top-level `business_system`; per-interaction metadata only
- `execution_surface_revision`: `reference-execution-surface-2` → `reference-execution-surface-3`
- Removed unused `SUPPORTED_OPERATIONS` constant (Registry is authoritative)
- Neutralized controlled simulator egress target naming (`controlled-business-simulator`)

### Unchanged boundaries

- Native Result ≠ Business Outcome (`NOT_EVALUATED`)
- `descriptor_version=1` unchanged
- `REAL_EXECUTION = PROHIBITED`, `REAL_EXTERNAL` denied
- Published interactions: `restaurant/reserve`, `shopping/submit_order` only

### Migration (v0.4.0 → v0.5.0)

| Removed (HTTP top-level) | Use instead |
| --- | --- |
| `reservation_id` | `native_result.external_identifier` |
| `native_external_identifier` | `native_result.external_identifier` |
| `crs_native_result` | `native_result.payload` (opaque; may contain vertical-native keys) |

## v0.4.0 — Developer Preview (multi-vertical)

### Added

- Business Adapter Architecture (`restaurant`, `shopping`)
- Runtime Interaction Registry with `published` publication state
- Generic `BusinessConnectorPort.execute(operation, context)`
- Interaction Descriptor (`descriptor_version=1`, `abis-reference-runtime-interaction-descriptor`)
- Descriptor endpoint: `GET /v1/reference-profile/interactions/{vertical}/{operation}`
- Profile v2 (`profile_version=2`) with `descriptor_path` per advertised interaction
- Second vertical: `shopping` / `submit_order` via Controlled Commerce Simulator
- Reference Agent Client Descriptor fetch step in normal flow
- `native_external_identifier` on `ReferenceClientResult` (backward-compatible `reservation_id`)

### Changed

- `execution_surface_revision`: `restaurant-reserve-1` → `reference-execution-surface-2`
- Gateway validation is vertical-neutral; structured input validation delegated to Adapters
- Profile lists two published interactions: `restaurant/reserve`, `shopping/submit_order`

### Unchanged boundaries

- Native Result ≠ Business Outcome (`NOT_EVALUATED`)
- `REAL_EXECUTION = PROHIBITED`, `REAL_EXTERNAL` denied
- No payment, no conformance/certification claims, no Interaction Readiness Catalog

## v0.3.0

- Reference Runtime Pointer discovery from Business Origin
- Preflight evidence portability and correlation binding

## v0.2.0

- Reference Runtime Profile and Interaction Preflight
- Reference Agent Client (Profile → Preflight → Invoke)
