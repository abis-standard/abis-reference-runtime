# ABIS Reference Runtime — Public Validation Guide

**Version:** v0.6.0  
**Repository:** [abis-standard/abis-reference-runtime](https://github.com/abis-standard/abis-reference-runtime)  
**Type:** Public validation intake (evidence gathering) — **not** certification or conformance determination

---

## Current validation target

Unless you are intentionally validating a **historical release**, validate the current public validation surface from the repository's **default branch** and confirm the Runtime version from the Reference Runtime Profile before execution.

Do **not** select an older tag merely because it appears in search results, cached pages, release history, or examples.

If validating a historical release, report that explicitly.

When live execution is possible, include the Runtime-reported version from `GET /v1/reference-profile` (`runtime.version`) in your Validation Report.

This is a **validation-target freshness rule** only. It does not make `main` normative ABIS semantics, and Runtime-reported version is not ABIS semantic authority.

---

## Purpose

ABIS welcomes **independent validation** from:

- humans (developers, operators, researchers)
- AI agents (ChatGPT, Claude, Grok, custom agents, etc.)
- human + AI agent teams

Validation is **evidence gathering**. It helps ABIS understand whether public materials are sufficient for independent inspection, testing, and reporting.

Validation is **not**:

- ABIS certification
- conformance determination
- Business Outcome evaluation
- Completion Determination
- a substitute for normative ABIS semantics

**Quick entry (no coding required):** [QUICK-VALIDATION.md](QUICK-VALIDATION.md)

---

## What to validate (v0.6.0)

Focus on **publicly documented** Reference Runtime behavior:

| # | Area |
| ---: | --- |
| 1 | Repository understanding (layout, docs, boundaries) |
| 2 | Reference Runtime Profile (`GET /v1/reference-profile`) |
| 3 | Interaction Descriptor (`GET` each `descriptor_path`) |
| 4 | Preflight (`POST /v1/demo/{vertical}/preflight`) |
| 5 | Invoke (`POST` profile-advertised invoke path) |
| 6 | Native Result interpretation (technical/native observation) |
| 7 | `execution_provenance` / `trace_reference` |
| 8 | `implementation_continuity_reference` (optional, non-normative) |
| 9 | Retry correlation (ICR reuse vs `idempotency_key` orthogonality) |
| 10 | Observe (`POST /v1/demo/restaurant/observe`) where applicable |

Published interactions (v0.6.0):

- `restaurant` / `reserve` / `CONTROLLED_SIMULATOR`
- `shopping` / `submit_order` / `CONTROLLED_SIMULATOR`

---

## Source of Truth rule

Validators should **preferably begin** from:

1. Public ABIS materials (specification repository, public documentation)
2. This Reference Runtime repository (`README.md`, `CHANGELOG.md`, examples, profile)

Report whether **additional private or manual explanation** was required. That gap is valuable validation evidence.

---

## Example fixtures vs observed evidence

Files under `examples/` and documented JSON excerpts are **documentation and test fixtures**.

They are **not** evidence that an HTTP request was actually executed.

Validation Reports must distinguish fixture/example content from **actually observed** Runtime responses. Operations not executed must be marked `NOT_EXECUTED` (or equivalent).

Structured template: [`validation/evidence-report-template.md`](validation/evidence-report-template.md)

---

## Validation scope

Report **one** scope per session:

| Scope | Meaning |
| --- | --- |
| **REPOSITORY_ONLY** | Public repository / documentation / examples / source reviewed; Reference Runtime **not** executed in this session |
| **LIVE_RUNTIME** | One or more Runtime operations **actually executed**; responses **directly observed** in this session |
| **INCOMPLETE** | Neither path completed — e.g. GitHub access failure, discovery failure, network/DNS/tool limits |

`INCOMPLETE` sessions are valid Public Validation findings — not worthless evidence.

Runtime execution is **not** required for a useful report. If execution is impossible, continue repository-only validation and mark execution-dependent steps `NOT_EXECUTED`.

---

## Evidence provenance

Label each claim with provenance:

| Provenance | Meaning |
| --- | --- |
| **DIRECTLY_OBSERVED** | From actual execution or retrieval **in this validation session** |
| **REPOSITORY_DESCRIBED** | From README, docs, source, fixtures, or examples |
| **PARTICIPANT_REPORTED** | Self-reported by participant; not independently verified |
| **AI_INFERRED** | Inferred by AI from multiple inputs |
| **NOT_EXECUTED** | Operation was not performed |
| **NOT_OBSERVED** | Field/operation exists but was not observed in the response |
| **NOT_PROVIDED** | No evidence supplied |

**Rule:** Repository fixtures (including `CONFIRMED` in `examples/`) are **REPOSITORY_DESCRIBED** — not **DIRECTLY_OBSERVED** execution results.

When reporting validation results, distinguish:

- information observed during execution;
- information described by repository artifacts;
- participant-reported execution;
- inferred information;
- operations not executed.

---

## Execution granularity

Report these **separately**:

| Activity | Notes |
| --- | --- |
| Tests | e.g. `./scripts/run_tests.sh`, unit tests |
| Runtime startup | Gateway / server started |
| HTTP request | Any HTTP call to the Runtime |
| Preflight | `POST /v1/demo/{vertical}/preflight` |
| Invoke | Profile-advertised invoke path |
| Observe | `POST /v1/demo/restaurant/observe` where applicable |

**Tests successful ≠ Live HTTP validation completed.**

---

## Completion state (operational)

These are **Public Validation operational states** — not normative ABIS statuses:

| State | Meaning |
| --- | --- |
| SURVEY_SUBMITTED | Public pilot questionnaire submitted |
| PROCEDURE_COMPLETED | Assigned procedure followed to completion |
| REPOSITORY_ONLY_VALIDATION_COMPLETED | Repository-only path completed |
| LIVE_RUNTIME_VALIDATION_COMPLETED | Live Runtime path completed |
| EVIDENCE_REVIEWABLE | Third party can review sanitized evidence |

Do not use a single "Completed" to mean all of the above.

Public pilot questionnaire: [`validation/public-pilot/questionnaire.md`](validation/public-pilot/questionnaire.md)

---

## Live execution minimum evidence

Required **only** when claiming **LIVE_RUNTIME** scope for executed operations.

Record sanitized evidence where available. Use **NOT_OBSERVED** or **NOT_PROVIDED** when a field was absent — **do not invent values**.

| Field | Notes |
| --- | --- |
| Execution environment | Sanitized |
| Runtime version | From observed Profile when executed |
| Executed operation | e.g. Preflight, Invoke |
| Endpoint | Public localhost or authorized endpoint only |
| Sanitized request / response excerpt | No secrets |
| `request_id`, `trace_reference`, `external_identifier` | If present in response |
| NOT_EXECUTED items | List operations not performed |

**Never publish:** credentials, tokens, secrets, `Authorization` headers, PII.

---

## Execution claim and independent verification

| Field | Values |
| --- | --- |
| Execution claim | NONE · PARTICIPANT_REPORTED · EVIDENCE_SUPPORTED |
| Independent verification | YES · NO |

Participant report ≠ independently verified execution. Sanitized artifacts may support a claim without enabling independent verification.

---

## NOT_IMPLEMENTED vs NOT_EVALUATED (report observed fields)

Do **not** treat these as interchangeable field values. Report the **field name, value, and source** as observed:

| Layer | Example | Provenance typical |
| --- | --- | --- |
| Capability / implementation boundary | `outcome_boundary.normative_business_outcome_evaluation: NOT_IMPLEMENTED` in Profile | REPOSITORY_DESCRIBED or DIRECTLY_OBSERVED |
| Interaction Business Outcome disposition | `outcome_disposition.disposition: NOT_EVALUATED` on Invoke | DIRECTLY_OBSERVED when Invoke executed |

Do not instruct validators to answer with a specific value — report what the Runtime or repository actually shows.

---

## Consistency check (reviewers)

Compare survey answers with submitted evidence. See [`validation/public-pilot/evidence-classification.md`](validation/public-pilot/evidence-classification.md).

| Result | Meaning |
| --- | --- |
| CONSISTENT | Survey and evidence align |
| MISMATCH | Minor or explainable divergence |
| CONTRADICTORY | Material conflict |
| INSUFFICIENT_INFORMATION | Cannot compare |

Example flags: SURVEY_EVIDENCE_MISMATCH · EXECUTION_CONTRADICTION · CONCLUSION_OVERCLAIM · POSSIBLE_HALLUCINATION (review flag only — not an accusation)

---

## Conclusion guard

A validation result describes what was **actually inspected or executed in this validation session**.

It does **not** by itself establish:

- ABIS conformance
- certification
- implementation completeness
- AI provider endorsement

Do **not** conclude: conformant, certified, fully compliant, complete specification compliance, or 仕様を完全に満たす.

A successful technical or native result does **not** by itself establish a Business Outcome.

Validation does **not** by itself establish certification, conformance, implementation completeness, or AI provider endorsement.

---

## Evidence classification (reviewers)

Primary: **VALID** · **PARTIAL** · **INVALID**

Review flags (non-exclusive): REPOSITORY_ACCESS_FAILURE · VALIDATION_DISCOVERY_FAILURE · ENVIRONMENT_LIMITATION · PARTICIPANT_REPORTED_EXECUTION · EXECUTION_EVIDENCE_MISSING · SURVEY_EVIDENCE_MISMATCH · CONTRADICTORY_RESPONSE · POSSIBLE_HALLUCINATION · CONCLUSION_OVERCLAIM · SEMANTIC_LAYER_CONFUSION

Full guide: [`validation/public-pilot/evidence-classification.md`](validation/public-pilot/evidence-classification.md)

When citing paid public pilots: payment was for completing the procedure, not for producing a positive result. Do not report pilot counts as "30 conformant validations."

---

## Validation modes

### Mode A — Local Runtime Validation

The validator can clone the repository, run the local Reference Runtime, execute HTTP requests against localhost, and record actual evidence.

**Preferred** for complete reproducibility where the environment permits.

### Mode B — Remote Authorized Runtime Validation

The validator has an **explicitly authorized** hosted Runtime endpoint and any required authorization supplied through an appropriate secure channel.

Do **not** publish credentials in GitHub Issues.

This repository does **not** advertise a default public hosted validation endpoint. Do not assume one exists unless separately authorized.

### Mode C — Repository-Only Validation

The validator environment cannot run or reach a Runtime.

Repository-only validation is still useful evidence for documentation discoverability, Profile/Descriptor contract understanding, semantic-boundary interpretation, and ambiguity detection.

**But:** example fixtures must **not** be reported as observed HTTP responses. Unexecuted operations must be marked `NOT_EXECUTED`.

---

## Observe request (restaurant · v0.6.0)

Endpoint: `POST /v1/demo/restaurant/observe` (Bearer auth required)

| Field | Required |
| --- | --- |
| `correlation_id` | yes |
| `external_identifier` | yes |
| `implementation_continuity_reference` | no |

Example fixture: [`examples/restaurant_observe_request.json`](examples/restaurant_observe_request.json)

Flow:

```text
Invoke → Native Result → external_identifier → Observe → later/current Native Result snapshot
```

- Observe ≠ Completion Determination
- Observe ≠ Business Outcome Evaluation
- Observed Native Result ≠ Business Outcome

---

## Semantic boundaries (required)

Preserve these distinctions in every report:

| Concept | Rule |
| --- | --- |
| Interaction | ≠ Execution |
| Native Result | ≠ Business Outcome |
| Technical status (`CONFIRMED`, `PENDING`, etc.) | ≠ Business Outcome |
| Observe | ≠ Completion Determination |
| `implementation_continuity_reference` | ≠ Interaction identity |
| `external_identifier` | ≠ Interaction identity |
| Validation report | ≠ Conformance · ≠ Certification |

Business Outcome in Reference Runtime scope: **`NOT_EVALUATED`**.

---

## Human validation workflow

1. **Inspect** — clone the repository; read `README.md`, `CHANGELOG.md`, and this guide.
2. **Run** — start the local gateway (see README Quick Start) or use another Runtime-accessible endpoint you are authorized to use.
3. **Test** — perform Profile → Descriptor → Preflight → Invoke (and Observe if testing async native observation).
4. **Record** — capture sanitized evidence (commands, response excerpts, `trace_reference`, `request_id`, ICR, `external_identifier`). **Do not** include tokens, secrets, or PII.
5. **Report** — open a [**Validation Report**](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-report.yml) Issue.

If validation cannot complete, open [**Validation Problem / Ambiguity**](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-problem.yml).

---

## AI Agent validation

AI agents are **welcome** to validate independently.

An agent **MAY**:

- inspect the public repository
- identify supported interactions from Profile / Descriptor
- determine the required flow from public materials
- perform network requests **if its environment permits**
- report what it **actually** executed
- produce a structured Validation Report

An agent **MUST NOT**:

- claim a request was executed when the environment prevented execution
- invent undocumented endpoints, field semantics, or execution order
- treat Native Result or technical status as Business Outcome
- claim ABIS conformance, certification, or Completion Determination
- publish credentials, tokens, secrets, or PII

---

## Human + Agent validation

A human may:

1. provide the public repository URL to an agent
2. let the agent inspect materials independently
3. supply Runtime access (localhost gateway, authorized endpoint) only where appropriate
4. supervise execution
5. submit the resulting report (human, agent, or joint attribution)

---

## Validation loop

```text
Inspect
  → Test
  → Record Evidence
  → Open GitHub Issue
  → ABIS Evidence Review
  → Gap Classification
  → (only then) potential documentation or Runtime change
```

Issue submission does **not** constitute certification.

---

## Agent validation prompt (copy-ready)

Use this prompt with any AI agent. A machine-readable copy lives at [`validation/agent-validation-prompt.md`](validation/agent-validation-prompt.md).

See [`validation/agent-validation-prompt.md`](validation/agent-validation-prompt.md) for the full copy-ready prompt (includes validation-target freshness, validation modes, and source-inspection reporting).

---

## Submit a report

| Resource | Link |
| --- | --- |
| **Validation Report** | [Open Validation Report Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-report.yml) |
| **Problem / Ambiguity** | [Open Validation Problem Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-problem.yml) |
| **Evidence report template** | [validation/evidence-report-template.md](validation/evidence-report-template.md) |
| **Public pilot questionnaire** | [validation/public-pilot/questionnaire.md](validation/public-pilot/questionnaire.md) |
| **Evidence classification** | [validation/public-pilot/evidence-classification.md](validation/public-pilot/evidence-classification.md) |
| **Partnership / organizational** | [abis.coaretail.com](https://abis.coaretail.com/) (outside GitHub Issues) |

---

## Privacy and security

**Do not** publish in GitHub Issues:

- Bearer tokens · API keys · passwords · cookies
- `Authorization` headers
- private URLs · credentials · PII · confidential business data

Use sanitized command transcripts and redacted response excerpts only.

---

## Multi-interaction testing

Validators may test **multiple independent** interactions (e.g. `restaurant/reserve` and `shopping/submit_order`).

Report each interaction's Native Result and evidence **independently**.

Do **not** aggregate multiple Native Results into a composite or trip-level Business Outcome. Reference Runtime does not implement composite Business Outcome evaluation.

---

## Validation evidence model (informative)

```text
Reporter
Agent / Provider
Runtime Version
Scenario
Source of Truth
Assistance Required
Actual Requests
Observed Native Results
Trace / Evidence
Ambiguities
Blockers
Suggested Clarifications
```

This metadata is **validation evidence**. It does not automatically become normative ABIS semantics.

---

## Suggested GitHub labels (informative)

If maintainers triage Issues, consider: `validation`, `agent-validation`, `human-validation`, `validation-blocker`, `documentation`. Existing labels such as `documentation` and `question` may also apply. Labels are optional; Issue forms work without them.
