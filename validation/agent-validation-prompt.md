# ABIS Reference Runtime — Agent Validation Prompt

Machine-readable copy of the validation prompt in [`VALIDATION.md`](../VALIDATION.md).

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
