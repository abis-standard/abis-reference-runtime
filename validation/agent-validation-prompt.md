# ABIS Reference Runtime — Agent Validation Prompt

Machine-readable copy of the validation prompt in [`VALIDATION.md`](../VALIDATION.md).

## Current validation target

Unless you are intentionally validating a **historical release**, validate the current public validation surface from the repository's **default branch** and confirm the Runtime version from the Reference Runtime Profile before execution.

Do **not** select an older tag merely because it appears in search results, cached pages, release history, or examples.

If validating a historical release, report that explicitly.

When live execution is possible, include the Runtime-reported version from `GET /v1/reference-profile` (`runtime.version`) in your Validation Report.

This is a **validation-target freshness rule** only. It does not make `main` normative ABIS semantics, and Runtime-reported version is not ABIS semantic authority.

---

```text
You are independently validating the public ABIS Reference Runtime.

Repository: https://github.com/abis-standard/abis-reference-runtime

EVIDENCE HONESTY:
- Label each claim with provenance: DIRECTLY_OBSERVED, REPOSITORY_DESCRIBED, PARTICIPANT_REPORTED, AI_INFERRED, NOT_EXECUTED, NOT_OBSERVED, NOT_PROVIDED
- Distinguish information you directly observed, information described in the repository, inferred information, and operations you did not execute
- Repository fixtures (including under examples/) are REPOSITORY_DESCRIBED — not DIRECTLY_OBSERVED execution results
- Report only what you could actually verify in this session
- Tests successful ≠ Live HTTP validation completed

VALIDATION SCOPE (report one):
- REPOSITORY_ONLY — reviewed public repository; no Runtime execution in this session
- LIVE_RUNTIME — actually executed one or more Runtime operations; directly observed responses
- INCOMPLETE — neither path completed; still valid evidence

VALIDATION TARGET (freshness):
- Start from the repository default branch unless historical validation was explicitly requested.
- Confirm the current Runtime version from README and from GET /v1/reference-profile (runtime.version) when live execution is possible.
- Do not silently downgrade to an older tag (e.g. v0.5.0) because of search results, cached pages, or examples.
- If you validate a historical release, report that explicitly and report any version mismatch.

VALIDATION MODE (report one):
- Local Runtime Validation — clone, run local gateway, execute HTTP against localhost
- Remote Authorized Runtime Validation — explicitly authorized hosted endpoint (no credentials in Issues)
- Repository-Only Validation — cannot run or reach Runtime; mark unexecuted operations NOT_EXECUTED

Use the public repository and Runtime-accessible information as the Source of Truth.

Do not assume undocumented endpoints, execution order, request formats, or semantic meaning.

Do not treat files under examples/ as observed HTTP evidence — they are fixtures.

If you must inspect public Runtime source code to resolve a documentation ambiguity, report:
DOCUMENTATION_INSUFFICIENT_SOURCE_INSPECTION_REQUIRED
and specify which public file(s) were required.

Determine the supported interaction flow yourself from public materials.

For the selected scenario:

1. Inspect the Reference Runtime Profile.
2. Inspect the relevant Interaction Descriptor.
3. Perform Preflight.
4. Perform Invoke if actually possible in your environment.
5. Perform Observe if supported and applicable (restaurant: POST /v1/demo/restaurant/observe; see examples/restaurant_observe_request.json).
6. Distinguish every ACTUAL HTTP request from planned, inferred, simulated, fixture, or unavailable operations.
7. Report Native Result separately from Business Outcome.
8. Do not claim ABIS conformance, certification, Completion Determination, or Business Outcome evaluation.
9. Identify ambiguity, missing information, contradictory information, or unnecessary human assistance.

Return a Validation Report containing:

- REPORTER TYPE (Human / AI Agent / Human + AI Agent)
- VALIDATION SCOPE (REPOSITORY_ONLY / LIVE_RUNTIME / INCOMPLETE)
- VALIDATION MODE (Local / Remote Authorized / Repository Only)
- EXECUTION GRANULARITY (Tests / Runtime startup / HTTP / Preflight / Invoke / Observe — mark EXECUTED or NOT_EXECUTED for each)
- EXECUTION CLAIM (NONE / PARTICIPANT_REPORTED / EVIDENCE_SUPPORTED)
- INDEPENDENT VERIFICATION (YES / NO)
- VERSION SELECTION (Current default branch / Historical release intentionally selected)
- SOURCE INSPECTION REQUIRED (No / Yes — public Runtime source required for documentation gap)
- AGENT / PROVIDER
- MODEL / RUNTIME (if known; no secrets)
- ABIS RUNTIME VERSION (from Profile when possible; label provenance)
- SCENARIO (e.g. restaurant / reserve / CONTROLLED_SIMULATOR)
- SOURCE OF TRUTH
- PRIVATE / MANUAL ASSISTANCE REQUIRED
- REPOSITORY UNDERSTANDING (PASS / FAIL / PARTIAL / NOT_ATTEMPTED)
- PROFILE (PASS / FAIL / PARTIAL / NOT_ATTEMPTED)
- DESCRIPTOR (PASS / FAIL / PARTIAL / NOT_ATTEMPTED)
- PREFLIGHT (PASS / FAIL / PARTIAL / NOT_ATTEMPTED)
- INVOKE (PASS / FAIL / PARTIAL / NOT_ATTEMPTED)
- OBSERVE (PASS / FAIL / PARTIAL / NOT_ATTEMPTED / NOT_APPLICABLE)
- ACTUAL HTTP REQUESTS (numbered list; mark ACTUALLY EXECUTED vs NOT EXECUTED with reason; label provenance)
- NATIVE RESULT (technical/native fields only; label provenance)
- EVIDENCE / TRACE (sanitized; no Authorization headers or secrets)
- OBSERVED BUSINESS OUTCOME DISPOSITION (report field as observed with provenance — do not interchange with Profile NOT_IMPLEMENTED)
- AMBIGUITIES
- BLOCKERS
- SUGGESTED CLARIFICATIONS (feedback only — not automatic ABIS semantics)
- FINAL VERDICT (validation scope only — do not claim conformant, certified, or fully compliant)

Never report an operation as executed unless it was actually executed.
Never expose credentials, tokens, secrets, or PII.
Never claim ABIS conformance, certification, complete specification compliance, or AI provider endorsement.
```
