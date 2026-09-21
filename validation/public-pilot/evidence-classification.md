# ABIS Public Pilot — Evidence Classification Guide

**Type:** Reviewer guidance for Public Validation evidence — **not** normative ABIS semantics  
**Use with:** [questionnaire.md](questionnaire.md) · [evidence-report-template.md](../evidence-report-template.md) · [VALIDATION.md](../../VALIDATION.md)

This guide helps reviewers classify submitted evidence. It does **not** certify implementations or establish conformance.

---

## Primary classification

| Class | Meaning |
| --- | --- |
| **VALID** | Evidence is internally consistent, scope-appropriate, and reviewable for the claimed validation path |
| **PARTIAL** | Useful evidence with gaps, ambiguities, or incomplete execution granularity |
| **INVALID** | Evidence is not reviewable, materially contradicts public repository facts, or misrepresents execution |

`VALID = 3` in a paid pilot is **not** a "10% success rate" for Live Runtime validation. Public pilots measure discoverability and evidence quality — not certification yield.

---

## Review flags (non-exclusive)

Flags are **review signals**, not automatic verdicts.

| Flag | When to consider |
| --- | --- |
| REPOSITORY_ACCESS_FAILURE | Q1 = NO/PARTIAL/UNCERTAIN; access blocker dominates |
| VALIDATION_DISCOVERY_FAILURE | Q2 = NO/UNCERTAIN; public entry not found |
| ENVIRONMENT_LIMITATION | Network, DNS, AI web access, terminal/Python limits |
| PARTICIPANT_REPORTED_EXECUTION | Execution claimed without sanitized live evidence |
| EXECUTION_EVIDENCE_MISSING | Q4 = YES but Q6 empty or non-reviewable |
| SURVEY_EVIDENCE_MISMATCH | Survey says discovery/access NO but evidence contains repo-specific detail as direct observation |
| CONTRADICTORY_RESPONSE | Survey and evidence materially conflict (e.g. Q4 NO + explicit HTTP execution claim) |
| POSSIBLE_HALLUCINATION | Major mismatch with public repository — **review flag only; not an accusation** |
| CONCLUSION_OVERCLAIM | Repository-only or incomplete session concludes conformant / certified / 完全に仕様を満たす |
| SEMANTIC_LAYER_CONFUSION | NOT_IMPLEMENTED (Profile) treated as interchangeable with NOT_EVALUATED (disposition), or Native Result → Business Outcome |

---

## Consistency check

Compare questionnaire (Q1–Q4) with evidence (Q5–Q6 / Issue / template).

| Result | Meaning |
| --- | --- |
| **CONSISTENT** | Survey and evidence align on access, discovery, execution scope |
| **MISMATCH** | Minor or explainable divergence |
| **CONTRADICTORY** | Material conflict (e.g. access NO + repo-specific "direct observation") |
| **INSUFFICIENT_INFORMATION** | Cannot compare — missing Q5, Q6, or scope labels |

### Example patterns (from public pilot review)

| Pattern | Survey | Evidence | Suggested handling |
| --- | --- | --- | --- |
| P04-style | Access YES, Discovery YES | Claims README/docs "do not exist" | CONTRADICTORY · POSSIBLE_HALLUCINATION flag · INVALID candidate |
| P12-style | Discovery NO | Detailed repo-derived terms in AI output | SURVEY_EVIDENCE_MISMATCH · do not auto-label INVALID |
| P13-style | Tests executed | HTTP "to be done next" | Tests ≠ HTTP complete · PARTIAL |
| P29/P30-style | Execution NO | "Fully compliant" conclusion | CONCLUSION_OVERCLAIM · scope REPOSITORY_ONLY or INCOMPLETE |
| P02/P10-style | Execution YES | Plausible but no sanitized evidence | PARTICIPANT_REPORTED_EXECUTION · EVIDENCE_REVIEWABLE = NO |

---

## Validation scope (session level)

| Scope | Review expectation |
| --- | --- |
| **REPOSITORY_ONLY** | No live HTTP claims without DIRECTLY_OBSERVED provenance; fixtures = REPOSITORY_DESCRIBED |
| **LIVE_RUNTIME** | Sanitized request/response or trace fields for executed operations; NOT_EXECUTED listed |
| **INCOMPLETE** | Valid finding; classify blockers; do not treat as failure of Public Validation program |

---

## Execution claim vs independent verification

| Execution claim | Meaning |
| --- | --- |
| NONE | No execution claimed |
| PARTICIPANT_REPORTED | Stated in survey or narrative only |
| EVIDENCE_SUPPORTED | Sanitized artifacts support the claim |

| Independent verification | Meaning |
| --- | --- |
| YES | Third party can reproduce or verify from sanitized public evidence |
| NO | Claim or artifacts insufficient for independent verification |

**Rule:** EVIDENCE_SUPPORTED ≠ automatically Independent verification YES.

---

## Evidence provenance (review)

| Provenance | Reviewer check |
| --- | --- |
| DIRECTLY_OBSERVED | Matches this session's execution/retrieval |
| REPOSITORY_DESCRIBED | Traceable to README, docs, source, fixtures |
| PARTICIPANT_REPORTED | Self-report only |
| AI_INFERRED | Marked as inference; not execution proof |
| NOT_EXECUTED | Operation correctly excluded from live claims |
| NOT_OBSERVED | Field absent from response — not fabricated |
| NOT_PROVIDED | Missing evidence — flag, do not fill in |

---

## Completion states (operational)

Distinguish:

- SURVEY_SUBMITTED
- PROCEDURE_COMPLETED
- REPOSITORY_ONLY_VALIDATION_COMPLETED
- LIVE_RUNTIME_VALIDATION_COMPLETED
- EVIDENCE_REVIEWABLE

"Survey completed" ≠ "Live Runtime validation completed" ≠ "Evidence reviewable".

---

## Paid participation disclosure (when citing pilot results)

When describing paid public pilots in documentation or reports, preserve:

> Participants were recruited through a paid Lancers microtask.  
> Payment was for completing the procedure, not for producing a positive result.

Do **not** characterize results as:

- 30 independent validators
- 30 Runtime validations succeeded
- 30 conformant results

---

## Conclusion guard (reviewer)

Reject or flag reports that conclude beyond evidence:

- conformant / certified / fully compliant
- complete specification compliance
- 仕様を完全に満たす

Validation ≠ Certification · Validation ≠ Conformance

---

## Semantic boundaries (unchanged)

- Interaction ≠ Execution
- Native Result ≠ Business Outcome
- Technical Status ≠ Business Outcome
- Observe ≠ Completion Determination
- Validation ≠ Certification · Validation ≠ Conformance
- Repository fixture ≠ observed execution evidence
- Participant report ≠ independently verified execution
- AI output ≠ AI provider endorsement

---

## Related documents

| Document | Purpose |
| --- | --- |
| [VALIDATION.md](../../VALIDATION.md) | Full public validation guide |
| [QUICK-VALIDATION.md](../../QUICK-VALIDATION.md) | No-code entry |
| [evidence-report-template.md](../evidence-report-template.md) | Structured evidence submission |
