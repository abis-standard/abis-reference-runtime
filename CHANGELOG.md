# Changelog

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
