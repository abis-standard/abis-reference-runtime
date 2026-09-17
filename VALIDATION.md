# ABIS Reference Runtime — Public Validation Guide

**Version:** v0.6.0  
**Repository:** [abis-standard/abis-reference-runtime](https://github.com/abis-standard/abis-reference-runtime)  
**Type:** Public validation intake (evidence gathering) — **not** certification or conformance determination

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

```text
You are independently validating the public ABIS Reference Runtime.

Repository: https://github.com/abis-standard/abis-reference-runtime
Target version: v0.6.0 (unless README states otherwise)

Use the public repository and Runtime-accessible information as the Source of Truth.

Do not assume undocumented endpoints, execution order, request formats, or semantic meaning.

Determine the supported interaction flow yourself from public materials.

For the selected scenario:

1. Inspect the Reference Runtime Profile.
2. Inspect the relevant Interaction Descriptor.
3. Perform Preflight.
4. Perform Invoke if actually possible in your environment.
5. Perform Observe if supported and applicable.
6. Distinguish every ACTUAL HTTP request from planned, inferred, simulated, or unavailable operations.
7. Report Native Result separately from Business Outcome.
8. Do not claim ABIS conformance, certification, Completion Determination, or Business Outcome evaluation.
9. Identify ambiguity, missing information, contradictory information, or unnecessary human assistance.

Return a Validation Report containing:

- REPORTER TYPE (Human / AI Agent / Human + AI Agent)
- AGENT / PROVIDER
- MODEL / RUNTIME (if known; no secrets)
- ABIS RUNTIME VERSION
- SCENARIO (e.g. restaurant / reserve / CONTROLLED_SIMULATOR)
- SOURCE OF TRUTH
- PRIVATE / MANUAL ASSISTANCE REQUIRED
- REPOSITORY UNDERSTANDING (PASS / FAIL / PARTIAL / NOT_ATTEMPTED)
- PROFILE (PASS / FAIL / PARTIAL / NOT_ATTEMPTED)
- DESCRIPTOR (PASS / FAIL / PARTIAL / NOT_ATTEMPTED)
- PREFLIGHT (PASS / FAIL / PARTIAL / NOT_ATTEMPTED)
- INVOKE (PASS / FAIL / PARTIAL / NOT_ATTEMPTED)
- OBSERVE (PASS / FAIL / PARTIAL / NOT_ATTEMPTED / NOT_APPLICABLE)
- ACTUAL HTTP REQUESTS (numbered list; mark ACTUALLY EXECUTED vs NOT EXECUTED with reason)
- NATIVE RESULT (technical/native fields only)
- EVIDENCE / TRACE (sanitized; no Authorization headers or secrets)
- BUSINESS OUTCOME: NOT_EVALUATED
- AMBIGUITIES
- BLOCKERS
- SUGGESTED CLARIFICATIONS (feedback only — not automatic ABIS semantics)
- FINAL VERDICT

Never report an operation as executed unless it was actually executed.
Never expose credentials, tokens, secrets, or PII.
```

---

## Submit a report

| Channel | Link |
| --- | --- |
| **Validation Report** | [Open Validation Report Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-report.yml) |
| **Problem / Ambiguity** | [Open Validation Problem Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-problem.yml) |
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
