# ABIS Reference Runtime

**Developer Preview — v0.6.0**

Reference implementation for executing ABIS Business Interactions against controlled reference business systems.

---

## Start here

| Intent | Where to go |
| --- | --- |
| Understand the Runtime | This README (architecture, Quick Start, boundaries) |
| Try ABIS with an AI (no code) | [QUICK-VALIDATION.md](QUICK-VALIDATION.md) |
| Run the Reference Runtime | [Quick Start](#quick-start) below |
| Validate the Runtime | [VALIDATION.md](VALIDATION.md) |
| Connect a Sandbox / Mock | [INTEGRATION.md](INTEGRATION.md) |
| Report validation evidence | [Validation Report Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-report.yml) |
| Report integration evidence | [Integration Report Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=integration-report.yml) |

Quick Validation remains the fastest public path when you do not need an external Sandbox or Mock.

---

## Current validation target

Unless you are intentionally validating a **historical release**, validate the current public validation surface from the repository's **default branch** and confirm the Runtime version from the Reference Runtime Profile before execution.

Do **not** select an older tag merely because it appears in search results, cached pages, release history, or examples.

If validating a historical release, report that explicitly in your Validation Report.

When live execution is possible, include the Runtime-reported version from `GET /v1/reference-profile` (`runtime.version`) in your report. This is a validation-target freshness rule — not a normative ABIS semantic authority claim.

---

## What's new in v0.6.0 (vs v0.5.0)

| Area | v0.5.0 | v0.6.0 |
| --- | --- | --- |
| Implementation continuity | — | Optional `implementation_continuity_reference` (non-normative implementation metadata) |
| Retry correlation | `idempotency_key` only | ICR may link retries/recovery Invokes (orthogonal to idempotency) |
| Technical observation | — | `POST /v1/demo/restaurant/observe` (native lookup by `external_identifier`) |
| Profile | `profile_version=3` | `profile_version=4` |
| Execution surface | `reference-execution-surface-3` | `reference-execution-surface-4` |

**Boundary reminders:**

- `implementation_continuity_reference` is **not** ABIS Interaction identity, Business Interaction identity, Decision identity, or Outcome identity.
- `native_result.external_identifier` identifies an **external/native object**, not an ABIS Interaction.
- `observe` performs **technical/native observation only** — not Business Outcome Evaluation, not Completion Determination.
- `modify` / `cancel` normative Interaction binding remains **outside v0.6**.

**Unchanged limitations (still apply):** Developer Preview · not production · not real booking/payment · not ABIS certification · not conformance determination · no normative Business Outcome evaluation · **no Internet-wide business discovery** · **REAL_EXECUTION PROHIBITED** · Native Result ≠ Business Outcome (`NOT_EVALUATED`).

---

## What's new in v0.5.0 (vs v0.4.0)

| Area | v0.4.0 | v0.5.0 |
| --- | --- | --- |
| Invoke response | Top-level `reservation_id` / `crs_native_result` aliases | **Vertical-neutral** — canonical `native_result` only |
| Execution evidence | Preflight `evidence` only | **`execution_provenance`** on Invoke (minimal audit metadata) |
| Profile | `profile_version=2` with top-level `business_system` | `profile_version=3` — **per-interaction** `business_system` only |
| Execution surface | `reference-execution-surface-2` | `reference-execution-surface-3` |
| Descriptor | `descriptor_version=1` | unchanged (`descriptor_version=1`) |

**Breaking Developer Preview change:** removed HTTP top-level aliases `reservation_id`, `crs_native_result`, and `native_external_identifier`. Use `native_result.external_identifier` and opaque `native_result.payload` instead.

**Unchanged limitations (still apply):** Developer Preview · not production · not real booking/payment · not ABIS certification · not conformance determination · no normative Business Outcome evaluation · **no Internet-wide business discovery** · **REAL_EXECUTION PROHIBITED** · Native Result ≠ Business Outcome (`NOT_EVALUATED`).

---

## What's new in v0.4.0 (vs v0.3.0)

| Area | v0.3.0 | v0.4.0 |
| --- | --- | --- |
| Verticals | `restaurant/reserve` only | `restaurant/reserve` + `shopping/submit_order` |
| Architecture | Restaurant-specific gateway paths | Business Adapter + Runtime Interaction Registry |
| Profile | `profile_version=1` | `profile_version=2` with `descriptor_path` per interaction |
| Interaction contract | Profile only | Profile → **Interaction Descriptor** → Preflight → Invoke |
| Execution surface | `restaurant-reserve-1` | `reference-execution-surface-2` |
| Commerce | — | Controlled Commerce Simulator (synthetic orders, no payment) |
| Connector port | Operation-specific helpers | Generic `execute(operation, context)` |

**Unchanged limitations (still apply):** Developer Preview · not production · not real booking/payment · not ABIS certification · not conformance determination · no normative Business Outcome evaluation · **no Internet-wide business discovery** · **REAL_EXECUTION PROHIBITED** · Native Result ≠ Business Outcome (`NOT_EVALUATED`).

Interaction Descriptors are **implementation metadata only** — not ABIS Capability, not ABIS Intent, not conformance.

---

## What's new in v0.3.0 (vs v0.2.0)

| Area | v0.2.0 | v0.3.0 |
| --- | --- | --- |
| Business → Runtime discovery | Runtime Base URL required | Reference Runtime Pointer from a **known Business Origin** |
| Pointer path | — | `/.well-known/abis-reference-runtime` (reference-implementation scoped) |
| Agent flow | Base URL → Profile → Preflight → Invoke | Business Origin → Pointer → Runtime → Profile → Preflight → Invoke |
| Evidence portability | `trace_reference` on invoke only | Preflight `evidence` metadata + cross-phase correlation binding |
| Execution surface revision | — | `execution_surface_revision` in Profile and Preflight evidence |

**Unchanged limitations (still apply):** Developer Preview · not production · not real booking/payment · not ABIS certification · not conformance determination · no normative Business Outcome evaluation · **no Internet-wide business discovery**.

The Reference Runtime Pointer is an **implementation-level, informative, reference-only** locator. It is **not** a normative ABIS discovery protocol and **not** `/.well-known/abis`.

---

## What's new in v0.2.0 (vs v0.1.0)

| Area | v0.1.0 | v0.2.0 |
| --- | --- | --- |
| Runtime surface discovery | Manual curl / README | `GET /v1/reference-profile` (Reference Runtime Profile) |
| Pre-invoke check | None | `POST /v1/demo/{vertical}/preflight` (Interaction Preflight) |
| Agent-side flow | Manual steps | Reference Agent Client (Profile → Preflight → Invoke) |
| Inspect Runtime Surface | Not machine-readable | From a **known Runtime base URL** — not Internet-wide discovery |
| Public execution truth | Scattered gateway constants | Single `ReferenceExecutionSurface` drives Profile, Preflight, Invoke validation, and Health |

**Unchanged limitations (still apply):** Developer Preview · not production · not real booking/payment · not ABIS certification · not conformance determination · no normative Business Outcome evaluation · no Internet-wide business discovery.

---

## What this is

- An **executable reference implementation** of the ABIS Business Interaction flow
- A **localhost HTTP gateway** for multi-vertical reference interactions (`restaurant`, `shopping`)
- An **ABIS Runtime Core** pipeline (authorization → execution → connector → trace)
- A **Controlled Reservation Simulator** with persistent `state.json`
- **Native Business Result** return, **idempotency**, and **execution trace** (`trace_reference`)

## What this is not

- **Not production infrastructure**
- **Not a real booking service** or payment system
- **Not ABIS certification** or conformance determination
- **Does not implement normative Business Outcome evaluation**
- **No external SaaS**, database, or paid services required

> Some internal prototype-era class names remain in source code (for example, integration service classes). These names do not imply provider-specific behavior.

---

## Architecture

### Discovery flow (v0.6.0)

```text
Known Business Origin
      ↓
GET /.well-known/abis-reference-runtime
      ↓
Reference Runtime Pointer
      ↓
Runtime Base URL
      ↓
GET /v1/reference-profile
      ↓
GET descriptor_path (Interaction Descriptor)
      ↓
POST /v1/demo/{vertical}/preflight
      ↓
POST profile-advertised invoke path (Bearer)
      ↓
Native Business Result + execution_provenance + trace_reference
      ↓
Outcome: NOT_EVALUATED
```

Published interactions (v0.6.0):

- `restaurant` / `reserve` / `CONTROLLED_SIMULATOR`
- `shopping` / `submit_order` / `CONTROLLED_SIMULATOR`

### Direct Runtime flow (v0.2.0+, still supported)

```text
Known Runtime Base URL
      ↓
GET /v1/reference-profile
      ↓
POST /v1/demo/{vertical}/preflight
      ↓
POST profile-advertised invoke path (Bearer)
      ↓
External Demo Gateway
      ↓
ExternalAgentAdapter
      ↓
RuntimeCore
      ↓
Authorization / Execution / Control Plane
      ↓
RestaurantSimulatorConnector
      ↓
Controlled Reservation Simulator
      ↓
ReservationEngine
      ↓
state.json
      ↓
Native Business Result
      ↓
FoundationTrace
      ↓
HTTP Response
```

The Reference Agent Client automates discovery (optional) → Profile → Preflight → Invoke. It begins from a **known Business Origin** or **known Runtime Base URL**. It does **not** perform Internet-wide business search or registry lookup.

---

## Requirements

- **Python 3.9+**
- **stdlib only** — no pip dependencies
- **No external database**
- **No external SaaS**

---

## Validate ABIS

ABIS Reference Runtime welcomes **independent validation** by humans, AI agents, and human+agent teams.

Validation is evidence gathering — **not** certification or conformance determination.

```text
Inspect → Test → Record Evidence → Open Issue → Improve ABIS
```

| Stage | Link |
| --- | --- |
| **Try ABIS** — Quick Validation (no coding required) | [QUICK-VALIDATION.md](QUICK-VALIDATION.md) |
| **Run ABIS** — full validation guide | [VALIDATION.md](VALIDATION.md) |
| **Integrate** — Sandbox / Mock → Runtime evidence | [INTEGRATION.md](INTEGRATION.md) |

Quick Validation can produce useful evidence even when your environment cannot execute the Reference Runtime.

| Resource | Link |
| --- | --- |
| Quick Validation (starter prompt · ~1–3 min) | [QUICK-VALIDATION.md](QUICK-VALIDATION.md) |
| Validation guide | [VALIDATION.md](VALIDATION.md) |
| Evidence report template | [validation/evidence-report-template.md](validation/evidence-report-template.md) |
| Public pilot questionnaire | [validation/public-pilot/questionnaire.md](validation/public-pilot/questionnaire.md) |
| Evidence classification (reviewers) | [validation/public-pilot/evidence-classification.md](validation/public-pilot/evidence-classification.md) |
| Agent prompt (copy-ready) | [validation/agent-validation-prompt.md](validation/agent-validation-prompt.md) |
| Submit Validation Report | [Open Issue — Validation Report](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-report.yml) |
| Report problem / ambiguity | [Open Issue — Validation Problem](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-problem.yml) |

---

## Quick Start

### 1. Clone and enter the repository

```bash
git clone https://github.com/abis-standard/abis-reference-runtime.git
cd abis-reference-runtime
```

### 2. Generate a local gateway token

```bash
export ABIS_DEMO_GATEWAY_TOKEN="$(
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
)"
export ABIS_GATEWAY_MODE=EXTERNAL_TEST
```

### 3. Start the gateway

```bash
mkdir -p data
python3 scripts/external_demo_gateway.py --data-dir ./data --port 9080
```

Leave this terminal running.

### 4. Inspect the Reference Runtime Profile

```bash
curl -s http://127.0.0.1:9080/v1/reference-profile | python3 -m json.tool
```

The Reference Runtime Profile describes the execution surface advertised by this reference implementation. It is **not** an ABIS conformance statement, certification, trust assertion, or normative ABIS Capability definition.

Example (abbreviated):

```json
{
  "profile_kind": "abis-reference-runtime-profile",
  "profile_version": 4,
  "execution_surface_revision": "reference-execution-surface-4",
  "runtime": { "name": "abis-reference-runtime", "version": "0.6.0" },
  "authority": { "semantic": "NONE", "normative": "NONE" },
  "advertised_interactions": [
    {
      "vertical": "restaurant",
      "operation": "reserve",
      "execution_classes_allowed": ["CONTROLLED_SIMULATOR"],
      "descriptor_path": "/v1/reference-profile/interactions/restaurant/reserve",
      "invocation": { "method": "POST", "path": "/v1/demo/restaurant/invoke" },
      "business_system": {
        "identifier": "abis-demo-restaurant-simulator",
        "classification": "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE"
      }
    },
    {
      "vertical": "shopping",
      "operation": "submit_order",
      "execution_classes_allowed": ["CONTROLLED_SIMULATOR"],
      "descriptor_path": "/v1/reference-profile/interactions/shopping/submit_order",
      "invocation": { "method": "POST", "path": "/v1/demo/shopping/invoke" },
      "business_system": {
        "identifier": "abis-demo-commerce-simulator",
        "classification": "EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE"
      }
    }
  ],
  "authorization": { "invoke": { "required": true, "scheme": "bearer" } },
  "execution_boundary": { "real_execution": "PROHIBITED" },
  "outcome_boundary": { "normative_business_outcome_evaluation": "NOT_IMPLEMENTED" }
}
```

> **Example fixture warning:** Files under `examples/` are documentation and test fixtures. They are **not** evidence that an HTTP request was actually executed. Validation Reports must distinguish fixture content from actually observed Runtime responses.

See also: `examples/reference_runtime_profile.json`

### 5. Preflight the Interaction

Before invoking, check whether the requested interaction is advertised by this Reference Runtime:

```bash
curl -s -X POST http://127.0.0.1:9080/v1/demo/restaurant/preflight \
  -H "Content-Type: application/json" \
  -d @examples/restaurant_reserve_preflight.json | python3 -m json.tool
```

`PREFLIGHT_READY` means the requested `vertical` / `operation` / `execution_class` is present in the Reference Runtime Profile and may be attempted via invoke. It does **not** predict booking availability, business acceptance, execution success, or Business Outcome.

Example response: `examples/restaurant_reserve_preflight_response.json`

### 6. Fetch an Interaction Descriptor (v0.4.0)

```bash
curl -s http://127.0.0.1:9080/v1/reference-profile/interactions/restaurant/reserve | python3 -m json.tool
```

Descriptors are **implementation metadata only** — not ABIS Capability, not conformance, not outcome prediction. Use `descriptor_path` from the Profile; do not guess URLs.

### 7. Serve a synthetic Reference Business Origin

In a second terminal (after the gateway is running):

```bash
export ABIS_ORIGIN_QUIET=1
python3 scripts/serve_reference_business_origin.py \
  --runtime-base-url http://127.0.0.1:9080 \
  --port 9081
```

This serves an implementation-level **Reference Runtime Pointer** at:

`http://127.0.0.1:9081/.well-known/abis-reference-runtime`

See: `examples/reference_runtime_pointer.json`

### 8. Reference Agent Client (Business Origin or Base URL → Descriptor → Preflight → Invoke)

This repository includes a **provider-neutral Reference Agent Client**. It does **not** perform Internet-wide business discovery.

**Discovery flow (no manual Runtime Base URL):**

```bash
export ABIS_DEMO_GATEWAY_TOKEN="$(
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
)"
python3 scripts/reference_agent_client.py \
  --business-origin http://127.0.0.1:9081 \
  --vertical restaurant \
  --operation reserve \
  --execution-class CONTROLLED_SIMULATOR \
  --input examples/restaurant_reserve_normal.json
```

**Direct Runtime flow (backward compatible):**

```bash
python3 scripts/reference_agent_client.py \
  --base-url http://127.0.0.1:9080 \
  --vertical restaurant \
  --operation reserve \
  --execution-class CONTROLLED_SIMULATOR \
  --input examples/restaurant_reserve_normal.json
```

Sequence:

1. **Business Origin discovery (optional)** — `GET /.well-known/abis-reference-runtime`
2. **Inspect Runtime Surface** — `GET /v1/reference-profile`
3. **Fetch Interaction Descriptor** — `GET` each interaction's `descriptor_path`
4. **Preflight Interaction** — `POST /v1/demo/{vertical}/preflight`
5. **Invoke Interaction** — profile/descriptor-provided relative path with Bearer auth
6. **Inspect Native Result / Provenance / Trace** — `native_result`, `execution_provenance`, `outcome_disposition`, `trace_reference`

`NATIVE RESULT: CONFIRMED` does **not** mean Business Outcome SUCCESS. The client does not assert conformance, certification, or trust.

See: `examples/reference_agent_request.json`

### 9. Send a Business Interaction (manual curl)

In a second terminal:

```bash
curl -s -X POST http://127.0.0.1:9080/v1/demo/restaurant/invoke \
  -H "Authorization: Bearer $ABIS_DEMO_GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d @examples/restaurant_reserve_normal.json | python3 -m json.tool
```

### 10. Inspect business state

```bash
cat ./data/state.json | python3 -m json.tool
```

---

## Idempotency

Resend the same request (same `idempotency_key`):

```bash
curl -s -X POST http://127.0.0.1:9080/v1/demo/restaurant/invoke \
  -H "Authorization: Bearer $ABIS_DEMO_GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d @examples/restaurant_reserve_normal.json
```

The same `native_result.external_identifier` is returned. `state.json` retains **one** reservation.

`idempotency_key` and `implementation_continuity_reference` are **orthogonal**. ICR links implementation Invokes; idempotency deduplicates simulator submissions.

---

## Implementation Continuity Reference

Optional non-normative field: `implementation_continuity_reference` (top-level on Invoke requests).

- Generated as UUID v4 when omitted on initial Invoke
- May be reused across retry/recovery Invokes and linked Observe requests
- **Not** ABIS Interaction identity · **not** Business Interaction identity · **not** Decision identity · **not** Outcome identity
- **Not** `external_identifier` · **not** `idempotency_key`
- Implementation-scoped correlation only — not semantic sameness, transaction identity, workflow continuity, or business outcome continuity

Worked example (fixture): `examples/restaurant_reserve_with_icr.json`

---

## Technical observation (restaurant)

Technical flow (implementation observation only):

```text
Invoke → Native Result → external_identifier → Observe → later/current Native Result snapshot
```

Boundaries:

- Observe ≠ Completion Determination
- Observe ≠ Business Outcome Evaluation
- Observed Native Result ≠ Business Outcome

After a `PENDING` Invoke, poll native state with `POST /v1/demo/restaurant/observe`.

**Request body** (restaurant only; Bearer auth required):

| Field | Required | Notes |
| --- | --- | --- |
| `correlation_id` | yes | Per-observe request correlation |
| `external_identifier` | yes | From prior Invoke `native_result.external_identifier` |
| `implementation_continuity_reference` | no | Optional implementation correlation |

```bash
curl -s -X POST http://127.0.0.1:9080/v1/demo/restaurant/observe \
  -H "Authorization: Bearer $ABIS_DEMO_GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d @examples/restaurant_observe_request.json
```

Example request fixture: `examples/restaurant_observe_request.json`

`observe` returns a Native Result snapshot only. It does **not** evaluate Business Outcome or perform Completion Determination.

---

## Result semantics

| Field | Example | Meaning |
| --- | --- | --- |
| `native_result.external_status` | `CONFIRMED` | Opaque native business-system observation (not ABIS Outcome) |
| `native_result.external_identifier` | `TEST-RSV-…` | Opaque native reference (vertical-neutral envelope field) |
| `execution_provenance` | `{ … }` | Implementation-level invoke audit metadata (not conformance) |
| `outcome_disposition.disposition` | `NOT_EVALUATED` | Runtime does **not** perform normative ABIS Business Outcome evaluation |

`CONFIRMED` does **not** mean ABIS Outcome Evaluation `SUCCESS`. These are separate layers.

---

## Security / Scope

- **localhost-first** (gateway binds to `127.0.0.1` by default)
- **synthetic data only** — no real PII or production credentials
- **controlled simulator** — no real booking or payment
- **Bearer authentication** required (`ABIS_DEMO_GATEWAY_TOKEN`)
- **CONTROLLED_SIMULATOR** execution class only

---

## Tests

```bash
chmod +x scripts/run_tests.sh
./scripts/run_tests.sh
```

Or:

```bash
PYTHONPATH=runtime/src:reference-business/controlled-reservation-simulator/src:reference-business/controlled-commerce-simulator/src:. \
  python3 -m unittest discover -s tests -v
python3 -m unittest discover -s reference-business/controlled-commerce-simulator/tests -v
```

Clean-room E2E (isolated temp data directory, synthetic token):

```bash
chmod +x scripts/clean_room_e2e.sh
./scripts/clean_room_e2e.sh
```

---

## License

Apache-2.0 — see [LICENSE](LICENSE).

---

## Status

**Developer Preview** — v0.6.0. Not for production use.
