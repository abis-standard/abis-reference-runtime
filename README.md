# ABIS Reference Runtime

**Developer Preview — v0.2.0**

Reference implementation for executing ABIS Business Interactions against a controlled reference business system.

---

## What this is

- An **executable reference implementation** of the ABIS Business Interaction flow
- A **localhost HTTP gateway** for restaurant reservation interactions
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

```text
External Agent
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

---

## Requirements

- **Python 3.9+**
- **stdlib only** — no pip dependencies
- **No external database**
- **No external SaaS**

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
  "profile_version": 1,
  "runtime": { "name": "abis-reference-runtime", "version": "0.2.0" },
  "authority": { "semantic": "NONE", "normative": "NONE" },
  "advertised_interactions": [
    {
      "vertical": "restaurant",
      "operation": "reserve",
      "execution_classes_allowed": ["CONTROLLED_SIMULATOR"],
      "invocation": { "method": "POST", "path": "/v1/demo/restaurant/invoke" }
    }
  ],
  "authorization": { "invoke": { "required": true, "scheme": "bearer" } },
  "execution_boundary": { "real_execution": "PROHIBITED" },
  "outcome_boundary": { "normative_business_outcome_evaluation": "NOT_IMPLEMENTED" }
}
```

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

### 6. Reference Agent Client (Discover Runtime Surface → Preflight → Invoke)

This repository includes a **provider-neutral Reference Agent Client**. It does **not** perform Internet-wide business discovery. It starts from a **known Runtime base URL** and machine-reads the advertised interaction surface before attempting invocation.

```bash
export ABIS_DEMO_GATEWAY_TOKEN="$(
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
)"
python3 scripts/reference_agent_client.py \
  --base-url http://127.0.0.1:9080 \
  --vertical restaurant \
  --operation reserve \
  --execution-class CONTROLLED_SIMULATOR \
  --input examples/restaurant_reserve_normal.json
```

Sequence:

1. **Discover Runtime Surface** — `GET /v1/reference-profile`
2. **Preflight Interaction** — `POST /v1/demo/{vertical}/preflight`
3. **Invoke Interaction** — profile-provided relative path with Bearer auth
4. **Inspect Native Result / Trace** — `native_result.external_status` and `outcome_disposition`

`NATIVE RESULT: CONFIRMED` does **not** mean Business Outcome SUCCESS. The client does not assert conformance, certification, or trust.

See: `examples/reference_agent_request.json`

### 7. Send a Business Interaction (manual curl)

In a second terminal:

```bash
curl -s -X POST http://127.0.0.1:9080/v1/demo/restaurant/invoke \
  -H "Authorization: Bearer $ABIS_DEMO_GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d @examples/restaurant_reserve_normal.json | python3 -m json.tool
```

### 8. Inspect business state

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

The same `reservation_id` is returned. `state.json` retains **one** reservation.

---

## Result semantics

| Field | Example | Meaning |
| --- | --- | --- |
| `native_result.external_status` | `CONFIRMED` | Controlled reference business system returned a confirmed native reservation result |
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
PYTHONPATH=runtime/src:reference-business/controlled-reservation-simulator/src:. \
  python3 -m unittest discover -s tests -v
```

---

## License

Apache-2.0 — see [LICENSE](LICENSE).

---

## Status

**Developer Preview** — v0.2.0. Not for production use.
