# ABIS Reference Runtime

**Developer Preview — v0.1.0**

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

### 4. Send a Business Interaction

In a second terminal:

```bash
curl -s -X POST http://127.0.0.1:9080/v1/demo/restaurant/invoke \
  -H "Authorization: Bearer $ABIS_DEMO_GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d @examples/restaurant_reserve_normal.json | python3 -m json.tool
```

### 5. Inspect business state

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

**Developer Preview** — v0.1.0. Not for production use.
