# D-11C — Controlled External Interoperability (Execution Package)

**Status:** Operational documentation and evidence templates only.  
**Runtime baseline:** v0.8.0 · Profile 5 · `reference-execution-surface-6` · Descriptor 1.

This package supports a **single** controlled interoperability exercise:

- **Interaction:** `restaurant` / `reserve`
- **execution_class:** `AUTHORIZED_NON_PRODUCTION`
- **target_mode:** `REMOTE_AUTHORIZED`
- **Scope:** One positive controlled Invoke + one negative controlled Invoke against a **third-party-managed non-production HTTPS Sandbox**

## What D-11C demonstrates

Controlled **technical interoperability** between the ABIS Reference Runtime and a partner Sandbox while preserving Runtime semantic boundaries.

## What D-11C does not demonstrate

- Independent ABIS implementation (see D-12)
- ABIS conformance or certification
- Production readiness
- Business Outcome validation (`NOT_EVALUATED` remains expected on Invoke)
- Partner or provider endorsement
- General ecosystem interoperability

**Native Result ≠ Business Outcome.** Partner-native `CONFIRMED` or `SUCCESS` is not a Business Outcome success.

## Package contents

| File | Purpose |
| --- | --- |
| [partner-requirements.md](partner-requirements.md) | Partner eligibility and exclusions |
| [partner-declaration-template.md](partner-declaration-template.md) | Lightweight factual confirmation |
| [interop-test-plan.md](interop-test-plan.md) | Phases A–G and GO/NO-GO gate |
| [evidence-template.md](evidence-template.md) | Evidence report, axes, PASS A–J, package layout |
| [sanitization-checklist.md](sanitization-checklist.md) | Mandatory redaction before publication |
| [operator-checklist.md](operator-checklist.md) | Operator runbook |
| [partner-overlay-template.md](partner-overlay-template.md) | Per-run operator overlay (private storage; not normative) |
| [response-triage.md](response-triage.md) | Partner reply triage before overlay preparation |

**Status note:** No controlled external interoperability test has been executed yet. No partner is approved in repository artifacts.

Evidence from a live test is stored under `D11C-EVIDENCE/` per [evidence-template.md](evidence-template.md) — **do not commit secrets, partner-filled overlays, or unsanitized partner credentials.**
