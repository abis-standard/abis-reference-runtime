# D-11C Partner Requirements

Technical eligibility for one controlled interoperability test with the ABIS Reference Runtime (`restaurant` / `reserve`, `AUTHORIZED_NON_PRODUCTION`, `REMOTE_AUTHORIZED`).

This document does **not** request ABIS conformance, certification, production integration, or Business Outcome validation.

---

## Required

| # | Requirement |
| --- | --- |
| 1 | **Third-party-managed HTTPS non-production Sandbox** endpoint |
| 2 | **Reservation-like** operation (create/hold/simulate — partner-defined) |
| 3 | **Synthetic / test data only** in automated requests |
| 4 | **No real booking side effect** from the test scenario |
| 5 | **No payment** capture or charge |
| 6 | **No production account mutation** |
| 7 | **Documented request schema** (fields, types, required/optional) |
| 8 | **Documented response schema** (native status fields, identifiers) |
| 9 | **Isolated test credential** if authentication is required |
| 10 | **Permission** for a small number of controlled automated requests |
| 11 | **Permission** to retain **sanitized** technical evidence |
| 12 | **Technical contact** for Sandbox ownership and expected behavior |
| 13 | **Clear separation from production** (hostname, environment, credentials, data) |

The partner **does not** need to implement ABIS natively. The Reference Runtime maps Invoke `input` → partner request and partner response → `NativeResultEnvelope`.

---

## Not required

- Native ABIS protocol implementation
- ABIS adoption commitment
- Production integration or go-live
- New production infrastructure
- Formal certification process
- Public marketing participation

---

## Exclusion conditions

Do not proceed if any of the following apply:

| Condition | Reason |
| --- | --- |
| Production-only endpoint | Violates non-production boundary |
| Real booking or payment side effect | Outside D-11C safety model |
| TLS verification must be weakened | Runtime rejects insecure TLS contexts |
| Sandbox indistinguishable from production | Cannot evidence non-production status |
| Arbitrary URL / host selection required | Runtime uses trusted config only |
| Secrets must appear in shared evidence | Violates sanitization policy |
| Request/response contract cannot be documented | Cannot evidence schema mapping |
| Evidence retention entirely prohibited | Cannot complete D-11C evidence package |
| Redirects to production | Egress policy denies redirects |
| Penetration-test style probing expected | D-11C is interoperability, not security assessment |

---

## Partner effort (planning estimates)

| Situation | Estimated effort |
| --- | --- |
| Existing suitable Sandbox + docs + test credential | **~0.5–1 person-day** |
| New minimal Mock/Sandbox endpoint + docs | **~2–3 person-days** |

These are **planning estimates**, not guarantees. Actual effort depends on API maturity, auth model, and internal review time.

---

## Event-ready partner ask (~150 words)

ABIS maintains an open **Reference Runtime** (v0.8.0) that can call an **explicitly configured non-production HTTPS Sandbox** for a single synthetic `restaurant/reserve` test—no production traffic, no payment, no real booking, and no ABIS product commitment. We seek **one** technical partner willing to run **two** controlled calls (one expected to be processable, one documented safe rejection) against your Sandbox or Mock API. You provide: HTTPS test endpoint, brief request/response documentation, isolated test credentials if needed, and permission to keep **sanitized** technical logs. You do **not** need to implement ABIS, pass a certification program, or go public; evidence can stay **private (Level 0)** initially. ABIS configures hostname, path, and mapping locally; Invoke input stays synthetic. Outcome: evidence whether the Runtime preserved **Native Result** vs **Business Outcome** boundaries across a real TLS boundary—not a conformance or endorsement claim.
