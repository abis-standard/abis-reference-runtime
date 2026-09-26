# D-11C Interoperability Test Plan

**Interaction:** `restaurant` / `reserve`  
**execution_class:** `AUTHORIZED_NON_PRODUCTION`  
**target_mode:** `REMOTE_AUTHORIZED`  
**Tests:** 1 positive controlled Invoke + 1 negative controlled Invoke

All customer-facing values are **synthetic**. Do not use real PII, production IDs, or live payment instruments.

---

## Canonical synthetic Invoke input (ABIS-facing)

Use placeholders; replace dates/times with partner-agreed test values.

```json
{
  "date": "SYNTHETIC-DATE-YYYY-MM-DD",
  "time": "SYNTHETIC-TIME-HH:MM",
  "party_size": 2,
  "seating_type": "SYNTHETIC-SEATING-TYPE",
  "customer_reference": "TEST-CUST-SYNTHETIC-001",
  "idempotency_key": "SYNTHETIC-IDEM-UUID"
}
```

Partner-specific mapping translates these fields into the Sandbox request body (documented in private [partner-overlay-template.md](partner-overlay-template.md)).

---

## Phase A — Partner verification

| Check | Evidence type |
| --- | --- |
| Sandbox ownership | `PARTNER_SUPPLIED_EVIDENCE` |
| Non-production status | Partner declaration + environment description |
| Endpoint identity (hostname, port, path) | Partner overlay (secrets excluded) |
| Authentication model | Partner documentation |
| Test-data policy | Partner declaration |
| Expected positive request/response | Partner documentation |
| Expected negative rejection | Partner documentation |
| No production side effects | Partner declaration |

**Output:** Completed `partner-declaration.md` + partner overlay section.

---

## Phase B — Local configuration

Configure trusted Runtime settings only (never from Invoke URL fields):

| Setting | Source |
| --- | --- |
| `ABIS_RESTAURANT_HTTP_ADAPTER_TARGET_MODE` | `REMOTE_AUTHORIZED` |
| `target_authorization_id` | Operator-assigned stable id |
| `authorized_hostname` | Exact partner Sandbox host |
| `authorized_port` | `443` or explicitly declared TLS port |
| `allowed_paths` | Exact allowlisted path |
| `environment_classification` | Permitted non-production class |
| `credential_env_var` | Isolated test secret (env only) |
| `mapping_version` | e.g. `d11c.restaurant.reserve.<partner-id>.v1` |

**Output:** `environment.json` (no secrets).

---

## Phase C — Preflight

Execute `POST /v1/demo/restaurant/preflight` with `execution_class: AUTHORIZED_NON_PRODUCTION`.

Record `preflight_state` and disclaimer/evidence metadata.

**Preflight proves:** local/configuration readiness for the advertised interaction.  
**Preflight does not prove:** remote reachability, authentication success, reservation availability, business availability, or production readiness.

**Output:** `preflight.json` (`DIRECT_RUNTIME_EVIDENCE`).

---

## GO / NO-GO gate (mandatory before any Invoke network I/O)

**NO-GO** if any item is missing. Do not Invoke.

| # | Requirement |
| --- | --- |
| 1 | Partner declaration complete |
| 2 | Non-production confirmed |
| 3 | Publication level selected |
| 4 | Hostname treatment selected |
| 5 | Credentials isolated (test-only, not production) |
| 6 | Exact hostname configured |
| 7 | Exact port configured |
| 8 | Exact path configured |
| 9 | Environment classification permitted (`SANDBOX` / `MOCK` / `SIMULATOR` / `SYNTHETIC_DEV`) |
| 10 | Sanitization checklist reviewed |
| 11 | Evidence directory `D11C-EVIDENCE/` prepared |
| 12 | Operator confirms no intentional production side effects |

Document GO/NO-GO decision in `TEST_OPERATOR_RECORD`.

---

## Phase D — Controlled positive Invoke

After **GO**, execute one Invoke with synthetic input expected to be **processable** per partner documentation.

Record:

- `transport_status`
- `external_request_attempted` / `external_response_received` (from provenance)
- TLS boundary crossed (HTTPS to configured host)

**Note:** Partner-native status does **not** need to be `SUCCESS` for later interoperability analysis if transport and mapping succeeded.

**Output:** `invoke-response.json`, `execution-provenance.json`, sanitized request/response excerpts.

---

## Phase E — Native result capture

Capture:

- Partner-native response (sanitized)
- Mapped `NativeResultEnvelope` fields (`technical_status`, `external_status`, `external_identifier`, `payload` technical fields)

Preserve partner-native status verbatim in sanitized partner evidence.

**Output:** `native-response.sanitized.json`, relevant sections of `invoke-response.json`.

---

## Phase F — Semantic boundary check

Verify:

- `outcome_disposition.disposition` = **`NOT_EVALUATED`**
- Native Result fields are not described as Business Outcome conclusions
- Provenance does not include credentials or `Authorization`

**Output:** `DERIVED_ANALYSIS` section in `evidence-report.md`.

---

## Phase G — Negative control

One additional Invoke using a **partner-documented safe rejection** condition.

**Preferred:**

- Invalid synthetic field (e.g. out-of-range `party_size`)
- Nonexistent synthetic resource id
- Documented unavailable synthetic slot

**Prohibited:**

- SSRF probes, TLS attacks, credential attacks, rate-limit abuse, production identifiers, security scanning

Purpose: interoperability **error mapping**, not penetration testing.

**Output:** `negative-control/negative-preflight-or-invoke.json`, `negative-control/negative-summary.md`.

---

## Execution flow (reference)

```text
Agent / Test Harness
  → Reference Profile
  → Preflight
  → [GO / NO-GO]
  → Invoke (positive)
  → Runtime Core
  → Restaurant Business Adapter
  → Authorized Remote Sandbox Adapter
  → Partner HTTPS Sandbox
  → Partner Native Response
  → NativeResultEnvelope
  → execution_provenance
  → outcome_disposition (NOT_EVALUATED)
  → Invoke (negative control)
```
