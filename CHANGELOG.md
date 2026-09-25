# Changelog

## v0.8.0 — Developer Preview (remote authorized Sandbox HTTPS)

### Added

- `TargetMode` (`LOCALHOST_MOCK`, `REMOTE_AUTHORIZED`) and `ValidatedDestination` — single DNS resolution with TCP connect to `selected_ip` (F01 DNS/connection binding)
- `bound_https_transport` / `bound_http_transport` — TLS verification (system trust store) and bound HTTP for localhost mock
- Remote authorized Sandbox HTTPS for `restaurant` / `reserve` under `AUTHORIZED_NON_PRODUCTION` when trusted configuration is complete
- `max_request_body_bytes` outbound bound; extended sanitized `execution_provenance` (`target_authorization_id`, `target_mode`, `transport.tls`)
- D-11B-04 security test matrix (`tests/test_d11b04_remote_sandbox_security.py`)

### Changed

- Runtime `0.8.0`; `execution_surface_revision`: `reference-execution-surface-6`
- Profile **remains v5** — public advertised execution classes unchanged; remote HTTPS is an implementation capability under existing `AUTHORIZED_NON_PRODUCTION` metadata

### Unchanged boundaries

- `REAL_EXECUTION = PROHIBITED`, `REAL_EXTERNAL` denied, production/unknown environment denied
- Native Result ≠ Business Outcome (`NOT_EVALUATED`); no external Observe; shopping remote not implemented
- No automatic fallback to `CONTROLLED_SIMULATOR` on adapter failure

## v0.7.0 — Developer Preview (authorized non-production external adapter)

### Added

- `AUTHORIZED_NON_PRODUCTION` execution class (Reference Runtime implementation metadata — not normative ABIS)
- `NonProductionEgressPolicy` fail-closed egress controls for authorized HTTP adapters
- `AuthorizedHttpSandboxConnector` for `restaurant` / `reserve` against a localhost Mock HTTP server
- `scripts/mock_restaurant_http_server.py` — synthetic reservation endpoint (no real booking)
- Local adapter configuration via environment variables (`ABIS_RESTAURANT_HTTP_ADAPTER_*`)
- Extended `execution_provenance` for connector kind, environment classification, egress decision, external request/response facts
- Preflight states: `PREFLIGHT_ADAPTER_NOT_CONFIGURED`, `PREFLIGHT_ENVIRONMENT_PROHIBITED`

### Changed

- Profile v5 (`profile_version=5`)
- `execution_surface_revision`: `reference-execution-surface-4` → `reference-execution-surface-5`
- `restaurant` / `reserve` advertises `CONTROLLED_SIMULATOR` and `AUTHORIZED_NON_PRODUCTION`
- `shopping` / `submit_order` remains `CONTROLLED_SIMULATOR` only

### Unchanged boundaries

- `REAL_EXECUTION = PROHIBITED`, `REAL_EXTERNAL` denied
- Native Result ≠ Business Outcome (`NOT_EVALUATED`)
- Restaurant `observe` remains Controlled Simulator technical observation only (no external HTTP Observe)
- Descriptor version unchanged

## v0.6.0 — Developer Preview (implementation continuity & technical observation)

### Added

- Optional `implementation_continuity_reference` on Invoke request/response (non-normative implementation correlation)
- Runtime-generated UUID v4 ICR when omitted on initial Invoke
- `POST /v1/demo/restaurant/observe` — technical native observation by `external_identifier`
- ICR, observe, and semantic firewall tests (`tests/test_icr.py`, `tests/test_observe.py`, `tests/test_v06_semantic_firewall.py`)

### Changed

- Profile v4 (`profile_version=4`)
- `execution_surface_revision`: `reference-execution-surface-3` → `reference-execution-surface-4`
- Evidence log may include `implementation_continuity_reference`, `external_identifier`, `observation_kind`

### Unchanged boundaries

- Native Result ≠ Business Outcome (`NOT_EVALUATED`)
- Completion Determination **NOT_IMPLEMENTED**
- Published interactions: `restaurant/reserve`, `shopping/submit_order` only
- `modify` / `cancel` normative binding **NOT** in scope
- `REAL_EXECUTION = PROHIBITED`, `REAL_EXTERNAL` denied
- **Backward compatible:** v0.5 clients omitting ICR behave as before

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
