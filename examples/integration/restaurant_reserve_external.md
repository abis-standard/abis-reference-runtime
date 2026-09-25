# External integration example — `restaurant` / `reserve`

**Synthetic data only.** No real restaurant reservation occurs.  
**Native Result ≠ Business Outcome.** `external_status: CONFIRMED` is not a Business Outcome determination.

**Default (all versions):** **mapping documentation + `CONTROLLED_SIMULATOR` Invoke** — the Runtime does **not** call your external Sandbox or Mock over HTTP.

**Optional v0.7.0:** `AUTHORIZED_NON_PRODUCTION` may use a **localhost Mock HTTP** server only (`scripts/mock_restaurant_http_server.py`). Remote company-hosted Sandbox URLs remain **prohibited** in the v0.7.0 Reference implementation.

---

## 1. External Sandbox / Mock (your environment)

Illustrative non-production reservation API (your system — not part of this repository):

```http
POST https://sandbox.example.invalid/v1/reservations
Content-Type: application/json

{
  "venue_id": "DEMO-VENUE-001",
  "slot": { "date": "2026-09-12", "time": "20:00" },
  "guests": 4,
  "room_preference": "PRIVATE_ROOM",
  "customer_ref": "TEST-CUST-REFERENCE-001"
}
```

Hypothetical Sandbox response (synthetic):

```json
{
  "mock_reservation_id": "MOCK-RSV-0001",
  "mock_status": "HELD"
}
```

**Mapping notes (Integrator → ABIS Reference Runtime Invoke `input`):**

| External (Sandbox) | Runtime Invoke `input` |
| --- | --- |
| `slot.date` | `date` |
| `slot.time` | `time` |
| `guests` | `party_size` |
| `room_preference` | `seating_type` |
| `customer_ref` | `customer_reference` |
| (your idempotency policy) | `idempotency_key` |
| — | `test_scenario`: `NORMAL_SUCCESS` (simulator scenario) |

Your adapter layer translates Sandbox → Invoke body. The Reference Runtime executes the **Controlled Reservation Simulator**, not your Sandbox URL.

---

## 2. ABIS interaction mapping

| ABIS-facing | Value |
| --- | --- |
| Vertical | `restaurant` |
| Operation | `reserve` |
| Execution class | `CONTROLLED_SIMULATOR` |
| Business system (Profile) | `abis-demo-restaurant-simulator` / `EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE` |

Discover paths from Profile — do not hardcode undocumented URLs:

```bash
curl -s http://127.0.0.1:9080/v1/reference-profile | python3 -m json.tool
```

Descriptor:

```bash
curl -s http://127.0.0.1:9080/v1/reference-profile/interactions/restaurant/reserve | python3 -m json.tool
```

---

## 3. Preflight

```bash
curl -s -X POST http://127.0.0.1:9080/v1/demo/restaurant/preflight \
  -H "Content-Type: application/json" \
  -d @examples/restaurant_reserve_preflight.json | python3 -m json.tool
```

Request fixture: `examples/restaurant_reserve_preflight.json`  
Example response shape: `examples/restaurant_reserve_preflight_response.json` (**REPOSITORY_DESCRIBED** until you execute live)

`PREFLIGHT_READY` means the interaction is **advertised** — not booking availability or Business Outcome.

---

## 4. Invoke (`CONTROLLED_SIMULATOR`)

Set a **local** demo token (not production credentials):

```bash
export ABIS_DEMO_GATEWAY_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABIS_GATEWAY_MODE=EXTERNAL_TEST
```

Start gateway per [README Quick Start](../../README.md#quick-start), then:

```bash
curl -s -X POST http://127.0.0.1:9080/v1/demo/restaurant/invoke \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ABIS_DEMO_GATEWAY_TOKEN}" \
  -d @examples/restaurant_reserve_normal.json | python3 -m json.tool
```

Request fixture: `examples/restaurant_reserve_normal.json`  
Example response shape: `examples/restaurant_reserve_normal_response.json` (**REPOSITORY_DESCRIBED**)

Record from **your** session when executed:

- `native_result.external_status`, `native_result.external_identifier`
- `execution_provenance`, `trace_reference`
- `outcome_disposition.disposition` → expect **`NOT_EVALUATED`** (Business Outcome evaluation is outside Runtime scope)

### Optional: `AUTHORIZED_NON_PRODUCTION` (v0.7.0 · localhost Mock HTTP only)

1. Start `python3 scripts/mock_restaurant_http_server.py --port 9095` (localhost bind only).
2. Configure local env (no URLs in Profile): `ABIS_RESTAURANT_HTTP_ADAPTER_ENABLED=true`, `ABIS_RESTAURANT_HTTP_ADAPTER_BASE_URL=http://127.0.0.1:9095`, `ABIS_RESTAURANT_HTTP_ADAPTER_PATH=/sandbox/v1/reservations`.
3. Invoke with `"execution_class": "AUTHORIZED_NON_PRODUCTION"` and the same structured `input`.

Remote Sandbox hostnames (for example `https://sandbox.company.example`) are **not** permitted by the v0.7.0 Reference egress policy.

---

## 5. Observe (optional, `CONTROLLED_SIMULATOR` only)

After Invoke returns an `external_identifier`, native technical observation:

```bash
curl -s -X POST http://127.0.0.1:9080/v1/demo/restaurant/observe \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ABIS_DEMO_GATEWAY_TOKEN}" \
  -d @examples/restaurant_observe_request.json | python3 -m json.tool
```

Observe is **technical/native observation only** — not Business Outcome Evaluation.

---

## 6. Evidence checklist

Report via [Integration Report Issue](../../.github/ISSUE_TEMPLATE/integration-report.yml):

- [ ] Runtime version from Profile (`ACTUALLY_EXECUTED` or `NOT_EXECUTED`)
- [ ] Mapping table (Sandbox fields → Invoke `input`)
- [ ] Preflight / Invoke / Observe labeled `ACTUALLY_EXECUTED` or `NOT_EXECUTED`
- [ ] Native Result quoted without converting to Business Outcome
- [ ] `outcome_disposition` recorded as `NOT_EVALUATED` when observed
- [ ] No tokens, secrets, or PII in the Issue
