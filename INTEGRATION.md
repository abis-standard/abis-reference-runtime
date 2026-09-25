# Try an ABIS Integration

**Repository:** [abis-standard/abis-reference-runtime](https://github.com/abis-standard/abis-reference-runtime)  
**Reference Runtime:** v0.6.0 (confirm via `GET /v1/reference-profile` → `runtime.version`)  
**Type:** External adoption / integration evidence — **not** certification, conformance determination, or Business Outcome evaluation

---

## What this entry does

**Map** one Sandbox / Mock interaction to the current ABIS Reference Runtime contract and produce **integration evidence**.

```text
External Sandbox / Mock contract (your environment)
  → mapping documentation
  → Controlled Simulator execution (Reference Runtime)
  → integration evidence
```

The **current v0.6.0** Reference Runtime does **not** invoke your external Sandbox or Mock. Runtime execution on this path remains on the **Controlled Simulator** (`CONTROLLED_SIMULATOR`).

Direct non-production external adapter execution (Reference Runtime → HTTP → authorized Mock) is a **subsequent Runtime capability** — **not** available in v0.6.0. Do not document or report it as available until your target Runtime version advertises it.

---

Have a **Sandbox**, **Mock**, or **simulator** API in your own non-production environment?

Document how **one** ABIS Business Interaction maps to the Runtime contract, run **Controlled Simulator** Preflight / Invoke, and return **sanitized** evidence.

You do **not** need to integrate your production system.  
You do **not** need to implement every ABIS interaction.  
**Start with one interaction.**

| Boundary | Statement |
| --- | --- |
| **NO PRODUCTION ACCESS REQUIRED** | Sandbox / Mock / synthetic dev only |
| **NO REAL BOOKING OR PURCHASE** | Controlled simulators only |
| **NO PAYMENT** | Commerce path is synthetic |
| **NO CERTIFICATION OR CONFORMANCE CLAIM** | Integration reports are participant evidence |

Profile advertises `execution_boundary.real_execution`: **PROHIBITED** — **REAL_EXECUTION PROHIBITED** remains in force.

This path is **separate** from [Quick Validation](QUICK-VALIDATION.md). Quick Validation stays the low-friction entry (including Repository-Only Validation). Use this page when you already have an external test API and want a structured **Integrate → Report Evidence** loop.

---

## Published starting points (v0.6.0)

| Vertical | Operation | Example walkthrough |
| --- | --- | --- |
| `restaurant` | `reserve` | [examples/integration/restaurant_reserve_external.md](examples/integration/restaurant_reserve_external.md) |
| `shopping` | `submit_order` | [examples/integration/shopping_submit_order_external.md](examples/integration/shopping_submit_order_external.md) |

Reuse the **current** Runtime contract (Profile → Descriptor → Preflight → Invoke). Do not invent alternate APIs.

---

## Five-step journey

```text
Choose → Map → Preflight → Invoke → Report
```

| Step | What you do |
| --- | --- |
| **1. Choose** | Pick one interaction (`restaurant/reserve` or `shopping/submit_order`) and `CONTROLLED_SIMULATOR`. |
| **2. Map** | Document how your Sandbox/Mock operation fields map to the Runtime Invoke `input` (synthetic data only). |
| **3. Preflight** | `POST /v1/demo/{vertical}/preflight` — confirms the interaction is **advertised**; not business acceptance. |
| **4. Invoke** | `POST` profile-advertised invoke path with Bearer token (local demo token only — **never** paste production secrets into evidence). |
| **5. Report** | Open an [Integration Report Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=integration-report.yml) with sanitized request/response excerpts. |

**After Invoke (restaurant only):** optional **Observe** — see below.

### Semantic layers (do not collapse)

| Layer | Role |
| --- | --- |
| **Preflight** | Advertisement / readiness check for the requested interaction |
| **Invoke** | Executes against the reference **Controlled Simulator** connector |
| **Native Result** | Technical/native observation (`external_status`, `external_identifier`, `payload`) |
| **Business Outcome** | **Not evaluated** by this Runtime — expect `outcome_disposition.disposition`: `NOT_EVALUATED` on Invoke when present |
| **Observe** | Technical/native snapshot lookup — **not** Business Outcome Evaluation, **not** Completion Determination |

`NOT_IMPLEMENTED` (Profile `outcome_boundary`) describes Runtime capability.  
`NOT_EVALUATED` (Invoke `outcome_disposition`) describes disposition for a specific invocation. Do not interchange them.

A Native Result such as `external_status: CONFIRMED` is **not** a Business Outcome conclusion.

---

## Observe (restaurant / reserve only)

v0.6.0 exposes `POST /v1/demo/restaurant/observe` for native lookup by `external_identifier` (see Profile `technical_observation.restaurant`).

- Supported for **`restaurant` / `reserve`** follow-up in the Developer Preview.
- **Not** advertised for `shopping` / `submit_order` in v0.6.0 — do **not** fabricate Observe evidence for shopping.

Observe performs **technical/native observation only**. It does **not** evaluate Business Outcome or perform Completion Determination.

---

## Minimum integration evidence

When reporting, include sanitized evidence with provenance labels:

| Field | Notes |
| --- | --- |
| Reference Runtime version | From Profile when executed; else document source |
| Selected interaction | e.g. `restaurant / reserve / CONTROLLED_SIMULATOR` |
| Implementation environment | Sandbox / Mock / Simulator / synthetic dev |
| External/mock operation mapped | Name or path of your non-production operation |
| Mapping description | Field-level notes (no secrets) |
| Actually executed operations | Profile, Descriptor, Preflight, Invoke, Observe (if applicable) |
| Preflight request/response | Where executed — label **ACTUALLY_EXECUTED** |
| Invoke request/response | Where executed — redact `Authorization` |
| Native Result | Technical fields only |
| `execution_provenance` | When returned on Invoke |
| `trace_reference` | When returned |
| `external_identifier` | When returned |
| Observe evidence | Restaurant only, when executed |
| Operations **NOT_EXECUTED** | Explicit list |
| Blockers / ambiguity | Required for failed attempts |
| Sanitized environment description | OS, gateway port, synthetic data policy |

### Provenance labels

| Label | Meaning |
| --- | --- |
| **ACTUALLY_EXECUTED** | You ran this operation and observed the response in this session |
| **NOT_EXECUTED** | Deliberately not run or blocked |
| **REPOSITORY_DESCRIBED** | From README, docs, or `examples/` fixtures — not live execution |

Repository fixtures under `examples/` are **REPOSITORY_DESCRIBED**, not proof of HTTP execution.

**Do not submit:** credentials, API keys, bearer tokens, `Authorization` headers, PII, confidential data, or private URLs.

An **unsuccessful** integration attempt is valid evidence.

---

## Run the Reference Runtime locally

Integration experiments target the **same** Developer Preview gateway as validation:

1. Follow [README — Quick Start](README.md#quick-start) (local token, `EXTERNAL_TEST`, port `9080`).
2. Execute Profile → Descriptor → Preflight → Invoke for your chosen interaction.
3. Your external Sandbox/Mock can run **in parallel** — the Reference Runtime still executes the **Controlled Simulator** unless you build a separate adapter outside this repository. This integration path documents **mapping + evidence**; it does not widen the public execution boundary.

---

## Report evidence

| Resource | Link |
| --- | --- |
| Integration Report (GitHub Issue) | [Open Issue — Integration Report](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=integration-report.yml) |
| Public validation (unchanged) | [VALIDATION.md](VALIDATION.md) · [QUICK-VALIDATION.md](QUICK-VALIDATION.md) |
| Validation Report Issue | [validation-report.yml](.github/ISSUE_TEMPLATE/validation-report.yml) |

Integration reports are **participant evidence**. They do **not** determine ABIS certification or conformance.

---

## Related journeys

```text
Learn → Try → Run → Validate → Integrate → Report Evidence
```

| Intent | Entry |
| --- | --- |
| Understand the Runtime | [README.md](README.md) |
| Try ABIS with an AI (no code) | [QUICK-VALIDATION.md](QUICK-VALIDATION.md) |
| Run / validate the Runtime | [VALIDATION.md](VALIDATION.md) |
| Connect a Sandbox / Mock | This page |
| Report validation evidence | [Validation Report Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-report.yml) |
