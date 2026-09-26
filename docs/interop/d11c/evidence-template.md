# D-11C Evidence Template

Specification for the evidence package after a live test.  
**Do not populate with fabricated execution results.**

---

## Evidence package layout

```text
D11C-EVIDENCE/
  README.md
  partner-declaration.md
  test-plan.md
  environment.json
  profile.json
  preflight.json
  invoke-request.sanitized.json
  native-response.sanitized.json
  invoke-response.json
  execution-provenance.json
  negative-control/
    negative-preflight-or-invoke.json
    negative-summary.md
  hashes.txt
  evidence-report.md
```

Optional restricted storage (never public): raw HTTP captures **with secrets** — outside this tree.

---

## Report metadata (required)

| Field | Description |
| --- | --- |
| **D11C_TEST_ID** | Unique test run id |
| **PARTNER_ID** | Stable non-secret partner slug |
| **PUBLICATION_LEVEL** | `LEVEL_0_PRIVATE` / `LEVEL_1_ANONYMIZED` / `LEVEL_2_ATTRIBUTED` |
| **RUNTIME_VERSION** | e.g. `0.8.0` |
| **RUNTIME_COMMIT_SHA** | Git SHA of Runtime used |
| **PROFILE_VERSION** | e.g. `5` |
| **EXECUTION_SURFACE** | e.g. `reference-execution-surface-6` |
| **DESCRIPTOR_VERSION** | e.g. `1` |
| **ADAPTER_ID** | From configuration / provenance |
| **MAPPING_VERSION** | e.g. `d11c.restaurant.reserve.<partner-id>.v1` |
| **ENVIRONMENT_CLASSIFICATION** | From configuration |
| **TARGET_AUTHORIZATION_ID** | From configuration / provenance |
| **TEST_TIMESTAMP** | ISO 8601 UTC |

---

## Evidence authority labels

Assign every artifact:

| Label | Examples |
| --- | --- |
| **DIRECT_RUNTIME_EVIDENCE** | Profile, Preflight, Invoke response, provenance from Runtime |
| **PARTNER_SUPPLIED_EVIDENCE** | Declaration, API docs, written Sandbox confirmation |
| **TEST_OPERATOR_RECORD** | GO/NO-GO log, operator notes, mapping overlay |
| **DERIVED_ANALYSIS** | Axis verdicts, overall verdict rationale |

Do not collapse authorities into a single category.

---

## Three-axis evaluation

Rate each axis independently:

| Axis | Question |
| --- | --- |
| **TRANSPORT_INTEROP** | HTTPS/TLS boundary crossed; request/response at transport layer |
| **SCHEMA_MAPPING_INTEROP** | Partner request/response maps to/from Invoke and NativeResultEnvelope as documented |
| **SEMANTIC_BOUNDARY_PRESERVATION** | Business Outcome remains `NOT_EVALUATED`; no authority leakage |

Per-axis verdict (one of):

- `PASS`
- `PASS_WITH_FINDINGS`
- `INCONCLUSIVE`
- `FAIL`
- `NOT_EVALUATED` (axis not applicable / not run)

**Overall verdict** (one of): `PASS` | `PASS_WITH_FINDINGS` | `INCONCLUSIVE` | `FAIL`

**Do not** compute overall PASS by simple majority. All **planned** axes for this test must meet their defined criteria for overall `PASS`.

---

## PASS criteria (A–J)

| ID | Criterion |
| --- | --- |
| **A** | Third-party ownership and non-production status sufficiently evidenced |
| **B** | Preflight returns expected local/configuration disposition |
| **C** | Runtime attempts `AUTHORIZED_NON_PRODUCTION` request |
| **D** | Real HTTPS/TLS network boundary crossed |
| **E** | Partner Sandbox receives/processes the protocol request |
| **F** | Partner-native response returned |
| **G** | Response mapped into existing `NativeResultEnvelope` |
| **H** | Execution provenance emitted without credential leakage |
| **I** | Business Outcome disposition remains **`NOT_EVALUATED`** |
| **J** | Negative control handled without expanding semantic authority |

**Important:** `PARTNER_NATIVE_REJECTION` alone is **not** interoperability failure. A documented rejection with correct exchange and mapping may still yield axis PASS and overall PASS.

---

## Failure classification

| Code | One-line definition |
| --- | --- |
| **PARTNER_ENVIRONMENT_FAILURE** | Sandbox unavailable, wrong environment, or partner-side outage |
| **CONFIGURATION_FAILURE** | Trusted adapter config incomplete or inconsistent |
| **DNS_EGRESS_FAILURE** | Policy DNS/egress denied destination |
| **TLS_FAILURE** | Certificate or TLS verification failure |
| **AUTHENTICATION_FAILURE** | Credential missing, invalid, or rejected |
| **TRANSPORT_FAILURE** | HTTP/network error excluding above |
| **SCHEMA_MAPPING_FAILURE** | Partner payload does not match documented mapping |
| **PARTNER_NATIVE_REJECTION** | Partner returned documented business/validation rejection — **does not by itself mean interoperability failure** |
| **RUNTIME_MAPPING_FAILURE** | Runtime could not map to/from NativeResultEnvelope |
| **EVIDENCE_INSUFFICIENT** | Required artifacts missing or not reviewable |

---

## Mapping version convention

Non-normative, non-secret identifier:

```text
d11c.restaurant.reserve.<partner-id>.v1
```

- **Stable** across a fixed mapping document
- **Recorded** in `environment.json` and evidence metadata
- **Increment** (`v2`, …) when request/response mapping semantics change

Not part of ABIS normative specification. No Runtime Core change required.

---

## Partner-specific overlay (operational)

Use [partner-overlay-template.md](partner-overlay-template.md) for per-run preparation.  
After partner outreach, classify the reply with [response-triage.md](response-triage.md) before filling the overlay.

Store completed overlays in private `D11C-EVIDENCE/` only — not in the public git tree.  
Field names align with `PARTNER_ID`, `MAPPING_VERSION`, `TARGET_AUTHORIZATION_ID`, and `ENVIRONMENT_CLASSIFICATION` in this document.

---

## Hash integrity

See [operator-checklist.md](operator-checklist.md) — SHA-256 over finalized artifacts in `hashes.txt` (excluding `hashes.txt` itself). Do not hash unsanitized secret-bearing originals into a public package.

---

## What PASS does not mean

PASS does **not** mean: independent ABIS implementation, conformance, certification, production readiness, Business Outcome validation, partner endorsement, or ecosystem-wide interoperability.
