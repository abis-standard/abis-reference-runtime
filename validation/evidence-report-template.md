# ABIS Reference Runtime — Validation Evidence Report Template

**Type:** Public validation evidence — **not** certification or conformance determination  
**Use with:** [VALIDATION.md](../VALIDATION.md) · [QUICK-VALIDATION.md](../QUICK-VALIDATION.md) · [GitHub Validation Report Issue](../.github/ISSUE_TEMPLATE/validation-report.yml)

Copy this template when preparing structured evidence outside the GitHub Issue form, or paste completed sections into an Issue.

---

## Conclusion guard (read first)

A validation result describes what was **actually inspected or executed in this validation session**.

It does **not** by itself establish:

- ABIS conformance
- certification
- implementation completeness
- AI provider endorsement

Do **not** conclude that the Runtime or public materials are "fully compliant", "certified", or "完全に仕様を満たす" based on validation evidence alone.

Report only what you observed, read, executed, or could not execute — with provenance labels.

---

## Session metadata

| Field | Value |
| --- | --- |
| Reporter type | Human / AI Agent / Human + AI Agent |
| Agent / Provider | (no secrets) |
| Model / runtime | (optional, sanitized) |
| Runtime version tested | (from Profile when live execution occurred; else from README/docs if REPOSITORY_DESCRIBED) |
| Scenario | e.g. `restaurant / reserve / CONTROLLED_SIMULATOR` |
| Source of truth | Public repository only / Public + human assistance / Other |
| Private / manual assistance required | (describe gap; no secrets) |

---

## Validation scope

Report **one** scope for this session:

| Scope | Meaning |
| --- | --- |
| **REPOSITORY_ONLY** | Public repository / docs / examples / source were reviewed; Reference Runtime execution was **not** performed in this session |
| **LIVE_RUNTIME** | One or more Runtime operations were **actually executed** in this session and responses were **directly observed** |
| **INCOMPLETE** | Neither path completed — e.g. access failure, discovery failure, environment stop. Still useful evidence |

`INCOMPLETE` is **not** worthless evidence.

---

## Completion state (operational — not normative ABIS status)

Mark all that apply. These are **Public Validation operational states**, not ABIS normative statuses.

| State | Apply when |
| --- | --- |
| SURVEY_SUBMITTED | A public pilot questionnaire was submitted |
| PROCEDURE_COMPLETED | Participant followed the assigned procedure to its end |
| REPOSITORY_ONLY_VALIDATION_COMPLETED | Repository-only validation path completed for this session |
| LIVE_RUNTIME_VALIDATION_COMPLETED | Live Runtime validation path completed for this session |
| EVIDENCE_REVIEWABLE | A third party can review sanitized evidence without guessing execution |

---

## Execution granularity

Report each **separately**. Do not collapse into a single "Completed".

| Activity | Status |
| --- | --- |
| Tests (`run_tests.sh` / unit tests) | EXECUTED / NOT_EXECUTED / NOT_APPLICABLE |
| Runtime startup (gateway / server) | EXECUTED / NOT_EXECUTED / NOT_APPLICABLE |
| HTTP request (any) | EXECUTED / NOT_EXECUTED / NOT_APPLICABLE |
| Preflight | EXECUTED / NOT_EXECUTED / NOT_APPLICABLE |
| Invoke | EXECUTED / NOT_EXECUTED / NOT_APPLICABLE |
| Observe | EXECUTED / NOT_EXECUTED / NOT_APPLICABLE |

**Rule:** Tests successful ≠ Live HTTP validation completed.

---

## Evidence provenance

Label claims using one provenance per item:

| Provenance | Meaning |
| --- | --- |
| **DIRECTLY_OBSERVED** | Obtained from actual execution or retrieval **in this session** |
| **REPOSITORY_DESCRIBED** | Stated in README, docs, source, fixtures, or examples |
| **PARTICIPANT_REPORTED** | Self-reported by participant; not independently verified |
| **AI_INFERRED** | Inferred by AI from multiple inputs |
| **NOT_EXECUTED** | Operation was not performed |
| **NOT_OBSERVED** | Operation may exist; this field was not observed in the response |
| **NOT_PROVIDED** | No evidence supplied for this item |

**Rule:** A `CONFIRMED` value in `examples/` is **REPOSITORY_DESCRIBED** — not **DIRECTLY_OBSERVED** execution evidence.

---

## Execution claim and independent verification

| Field | Value |
| --- | --- |
| Execution claim | NONE / PARTICIPANT_REPORTED / EVIDENCE_SUPPORTED |
| Independent verification | YES / NO |

Sanitized request/response excerpts may support **EVIDENCE_SUPPORTED** but do **not** automatically mean **Independent verification = YES**.

Participant report ≠ independently verified execution.

---

## Phase results (what you actually validated)

Use PASS / FAIL / PARTIAL / NOT_ATTEMPTED / NOT_APPLICABLE.

| Phase | Result | Primary provenance |
| --- | --- | --- |
| Repository understanding | | |
| Profile | | |
| Descriptor | | |
| Preflight | | |
| Invoke | | |
| Observe | | |

---

## Live execution minimum evidence (only if LIVE_RUNTIME)

Complete only for operations **actually executed**. Use `NOT_OBSERVED` or `NOT_PROVIDED` when a field was not present — **do not invent values**.

| Field | Value | Provenance |
| --- | --- | --- |
| Execution environment | | |
| Runtime version (observed) | | |
| Executed operation | | |
| Endpoint | | |
| Sanitized request excerpt | | |
| Sanitized response excerpt | | |
| `request_id` | | |
| `trace_reference` | | |
| `external_identifier` | | |
| NOT_EXECUTED operations | | |

**Never include:** credentials, tokens, secrets, `Authorization` headers, PII.

---

## NOT_IMPLEMENTED vs NOT_EVALUATED (report observed fields — do not interchange)

These are **different layers**. Report the **field name and value as observed** with provenance.

| Layer | Example field / value | Meaning (informative) |
| --- | --- | --- |
| Capability / implementation boundary | `normative_business_outcome_evaluation: NOT_IMPLEMENTED` (Profile) | Implementation boundary in Profile |
| Interaction Business Outcome disposition | `outcome_disposition.disposition: NOT_EVALUATED` (Invoke response) | Per-interaction disposition |

Do not treat them as interchangeable synonyms.

---

## Actual HTTP requests

Number each operation. Mark **ACTUALLY EXECUTED** or **NOT EXECUTED** with reason.

```text
1. GET /v1/reference-profile — NOT EXECUTED (repository-only session)
2. POST /v1/demo/restaurant/preflight — ACTUALLY EXECUTED (example)
```

---

## Native result (technical only)

Report technical/native fields with provenance. Do **not** convert to Business Outcome.

| Field | Value | Provenance |
| --- | --- | --- |
| `external_status` | | |
| `external_identifier` | | |
| Other native fields | | |

Business Outcome disposition (if observed): report field as seen — typically `NOT_EVALUATED` in Reference Runtime scope.

---

## Ambiguities, blockers, suggested clarifications

**Ambiguities:**

**Blockers:**

**Suggested clarifications:** (feedback only — not automatic ABIS semantics)

---

## Final verdict (validation scope only)

Short summary of **what was inspected or executed** — e.g. `REPOSITORY_ONLY — PASS WITH AMBIGUITIES`, `INCOMPLETE — BLOCKED AT REPOSITORY ACCESS`.

Do **not** use: conformant, certified, fully compliant, complete specification compliance, 仕様を完全に満たす.

---

## Attestations

- [ ] I distinguished executed operations from planned, inferred, or fixture-derived claims.
- [ ] I labeled provenance (observed / repository-described / inferred / not executed).
- [ ] I did not treat Native Result or technical status as Business Outcome.
- [ ] I did not claim ABIS certification, conformance, or AI provider endorsement.
- [ ] I removed credentials, tokens, PII, and secrets from this report.
