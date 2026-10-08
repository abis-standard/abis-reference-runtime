# Copilot instructions — ABIS Reference Runtime repository

These instructions are repository-scoped guidance for AI coding assistants working **in this repository only** (`abis-standard/abis-reference-runtime`). They do not apply to other repositories, and they do not change the ABIS specification.

## What this repository is

- The **ABIS Reference Runtime**, a Developer Preview reference implementation for **ABIS — Agent Business Interaction Standard** (singular: "Standard").
- ABIS concepts and normative candidate text are published in [abis-standard/abis](https://github.com/abis-standard/abis). ABIS semantics are defined there, not by this Runtime. Runtime behavior, versions, and docs are not ABIS semantic authority.
- Not production infrastructure, not a real booking or payment service, and not ABIS certification or conformance determination.

## Outcome semantics to preserve

- **Execution success ≠ outcome success.** An HTTP 200, a completed tool call, or a native `CONFIRMED` / `SUCCESS` status is **not** a satisfied Business Outcome.
- **Native Result ≠ Business Outcome.** `native_result` is an opaque observation, not an ABIS Outcome.
- The Runtime does **not** perform normative Business Outcome evaluation. `outcome_disposition.disposition` is `NOT_EVALUATED`. Do not change it, and do not add code, docs, or examples that imply an evaluated outcome, unless a maintainer explicitly asks.
- Keep the per-Invoke disposition (`NOT_EVALUATED`) separate from Profile capability statements such as `outcome_boundary: NOT_IMPLEMENTED`.
- Comparing an observed business result with the intended one requires actual outcome evidence. Never infer it from technical success.
- Preserve evidence provenance (`execution_provenance`, `trace_reference`, execution class). Do not rewrite or upgrade evidence.
- Do not infer whole-job success from individual successful operations. Observed composite cases in published R&D evidence included MATCH + MISMATCH → not satisfied and MATCH + `NOT_EVALUATED` → not evaluable. These are documented observations, not composition rules, and they are not produced by this Runtime.
- Never fabricate provider evidence, API responses, identifiers, tokens, or validation results.

## Scope and safety boundaries

- Execution classes: `CONTROLLED_SIMULATOR` (default), `AUTHORIZED_NON_PRODUCTION` only where documented, and `REAL_EXTERNAL` **DENY**. Do not widen them.
- Use synthetic data only. Never add real credentials, secrets, or PII.
- Python 3.9+, stdlib only. Run tests with `./scripts/run_tests.sh`.
- Changes must pass the disclosure gate in `scripts/disclosure/`. New files must fit [public-release-allowlist.yml](../public-release-allowlist.yml).
- Do not claim production readiness, L3 or real-world validation, certification, conformance, provider endorsement, or official integration with MCP, A2A, or any other protocol. ABIS is designed to complement them.
- Licensing is stated in [LICENSE](../LICENSE). Do not add other license claims.
