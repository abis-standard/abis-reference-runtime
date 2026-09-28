# Independent Builder Evidence Protocol (D-12A)

Durable protocol for **independent third-party** ABIS builder experiments submitted against public ABIS materials.

This protocol prepares evidence review for an **Independent Builder Pilot**. It does **not** open recruitment, guarantee review timing, or imply ABIS adoption.

---

## Purpose

Observe whether someone **independent from ABIS maintainers** can, using **public ABIS materials**:

1. Understand an ABIS Business Interaction  
2. Map it to their own implementation, Sandbox, Mock, or system  
3. Implement relevant semantics (where claimed)  
4. Optionally execute and capture evidence  
5. Submit reviewable, sanitized evidence  

This is **experimental developer evidence**. It is **not**:

- ABIS certification  
- conformance determination  
- production readiness proof  
- provider or vendor endorsement  
- proof of Business Outcome success  
- proof of ecosystem-wide interoperability  

**D-11** (Reference Runtime ↔ third-party Sandbox interop) and **D-12** (independent builder semantics) answer different questions. Do not conflate Integration Reports with Independent Builder Reports.

---

## Builder eligibility

**BUILDER_ELIGIBLE** (conceptual rule):

```text
BUILDER_ELIGIBLE =
  independent_from_ABIS_maintainers
  AND uses_public_ABIS_materials
  AND performs_own_implementation_or_mapping_work
  AND submits_evidence
```

| Condition | Meaning |
| --- | --- |
| **independent_from_ABIS_maintainers** | The implementation/mapping work is not performed by ABIS maintainers on the participant’s behalf |
| **uses_public_ABIS_materials** | Relies on publicly available ABIS specification materials, Reference Runtime docs, Profile/Descriptor, etc. |
| **performs_own_implementation_or_mapping_work** | Participant (or their team) produces mapping and/or implementation artifacts |
| **submits_evidence** | Files an [Independent Builder Report](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=independent-builder-report.yml) with required attestations |

### AI-assisted implementation

**AI-assisted coding is allowed** (for example ChatGPT, Claude, Cursor, Codex, or other assistants). Using an assistant does **not** invalidate independence.

- Do **not** treat AI providers as endorsing ABIS or the submission.  
- If an **ABIS maintainer** implements or performs the mapping work **for** the participant, the submission is **not** classified as an Independent Builder implementation.  
- Maintainer **clarification** or links to **public documentation** do **not** invalidate independence.

---

## Progression levels (participant-reported)

Levels describe **progression evidence**, not quality ranking or conformance.

| Level | Definition |
| --- | --- |
| **L0 DISCOVERED** | Builder discovered ABIS / this repository. No implementation evidence. |
| **L1 UNDERSTOOD** | Builder inspected relevant public ABIS materials. No field-level mapping required yet. |
| **L2 MAPPED** | Field-level or operation-level mapping between an ABIS interaction and the builder’s implementation, Sandbox, Mock, simulator, or system. |
| **L3 IMPLEMENTED** | ABIS-related semantics, adapter/client logic, or equivalent independent code/config exists. |
| **L4 EXECUTED** | Implementation or supported Runtime-assisted experiment was **actually executed**; execution evidence captured. |
| **L5 EVIDENCE_COMPLETE** | Package sufficiently complete for review: mapping/implementation artifact, environment, operations executed, sanitized results/logs, explicit NOT_EXECUTED items, blockers/limitations, semantic boundary acknowledgement. |

**Independent Implementation** must **not** be counted below **L3**.

**L0–L2** may still be valid participant/progression evidence.

- No required success percentage is defined here.  
- **L5** does **not** mean conformant, certified, production-ready, or Business Outcome validated.

---

## Implementation tracks

| Track | Description |
| --- | --- |
| **TRACK_A — RUNTIME_ASSISTED** | Reference Runtime participates in the experiment (Profile, Preflight, Invoke, etc.). |
| **TRACK_B — INDEPENDENT_IMPLEMENTATION** | Builder’s own client/adapter/semantic implementation — not relying on Reference Runtime for the relevant implementation work. |

Track B is **not** automatically conformant. Track A is **not** inferior evidence. **No ranking** between tracks.

---

## Evidence authority

| Label | Definition |
| --- | --- |
| **PARTICIPANT_REPORTED** | Builder reports an action/result. **Not** independently verified because an Issue was filed. |
| **ARTIFACT_SUPPORTED** | Reviewable artifacts included (sanitized source, commit, mapping, logs, request/response excerpts, etc.). |
| **REPRODUCED_BY_REVIEWER** | Independent reviewer reproduced the claim from available evidence. |

### `ACTUALLY_EXECUTED` vs authority

**`ACTUALLY_EXECUTED`** is an **execution provenance** label (what the participant ran in their session). It is **not** equivalent to **REPRODUCED_BY_REVIEWER**.

A builder may truthfully label an operation **ACTUALLY_EXECUTED** while evidence authority remains **PARTICIPANT_REPORTED** until artifacts and review support a higher authority.

Participants **must not** self-assign **REPRODUCED_BY_REVIEWER**.

---

## Builder evidence verdict (completeness / eligibility)

Evaluates evidence package only — **not** conformance or Business Outcome.

| Verdict | Meaning |
| --- | --- |
| **EVIDENCE_COMPLETE** | Sufficient for planned review scope at claimed level |
| **EVIDENCE_PARTIAL** | Useful but missing items for claimed level |
| **EVIDENCE_INSUFFICIENT** | Cannot assess claimed level |
| **INELIGIBLE** | Fails BUILDER_ELIGIBLE (for example maintainer-performed implementation) |

These verdicts do **not** mean ABIS conformant, certified, interoperable everywhere, production ready, or Business Outcome successful.

---

## Pilot-level aggregate verdicts (reviewer-assigned)

Available for a future pilot review pass:

| Verdict | Use |
| --- | --- |
| **PASS** | Evidence supports the pilot question at declared scope |
| **PASS_WITH_FINDINGS** | Pass with documented limitations |
| **INCONCLUSIVE** | Cannot decide from evidence |
| **FAIL** | Evidence does not support claims or eligibility failed |

A **future** pilot protocol may establish **pre-declared thresholds** before recruitment. This document does **not** set numerical thresholds or retrospectively derive them from results.

---

## Semantic firewall

| Boundary | Statement |
| --- | --- |
| Interaction ≠ Execution | Advertised interaction ≠ every execution class or external path |
| Native Result ≠ Business Outcome | Native `CONFIRMED` / `SUCCESS` ≠ Business Outcome success |
| Technical Status ≠ Business Outcome | Transport/native technical fields ≠ outcome evaluation |
| Observe ≠ Completion Determination | Observe is technical/native only where supported |
| Validation ≠ Certification | Reference Runtime validation ≠ ABIS certification |
| Validation ≠ Conformance | Tests/docs here ≠ normative conformance |
| Independent Implementation ≠ Conformance | Track B ≠ conformant by default |
| Repository fixture ≠ observed execution | `examples/` ≠ ACTUALLY_EXECUTED |
| Participant report ≠ verified execution | Issue filing ≠ REPRODUCED_BY_REVIEWER |
| AI output ≠ AI provider endorsement | Assistant use ≠ vendor endorsement of ABIS |
| **NOT_IMPLEMENTED** | Capability / implementation boundary |
| **NOT_EVALUATED** | Business Outcome disposition where applicable (Reference Runtime Invoke) |

### Reference Runtime safety (when Track A applies)

- **REAL_EXECUTION PROHIBITED** · **REAL_EXTERNAL DENY**  
- No production execution · no real booking · purchase · payment  
- No arbitrary URL proxy  
- **shopping** / **submit_order** external execution: **NOT_IMPLEMENTED**  
- **AUTHORIZED_NON_PRODUCTION** external adapter: **restaurant / reserve** only where supported and configured  
- External **Observe**: **NOT_SUPPORTED** for authorized external adapter Invoke  
- **Preflight**: configuration/readiness — not remote availability, business acceptance, certification, or conformance  

---

## Submit evidence

[ABIS Independent Builder Report](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=independent-builder-report.yml)

For Reference Runtime integration against your Sandbox/Mock (D-11 path), use the [Integration Report](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=integration-report.yml) instead.

Developer entry: [BUILD_WITH_ABIS.md](../../BUILD_WITH_ABIS.md)
