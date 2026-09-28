# Build with ABIS (Developer Entry)

**ABIS Reference Runtime — Developer Preview v0.8.0**  
This page is a durable entry for developers who want to experiment with ABIS using **one interaction**, **one mapping**, and **one Native Result**.

This is **not** a certification program, conformance program, production integration program, partner program, endorsement program, or proof of Business Outcome.

---

## Start small

You do not need to implement everything.

Enough to begin an experiment:

1. **One** published interaction (for example `restaurant` / `reserve`)
2. **One** Sandbox, Mock, or in-process simulator path — whichever your chosen `execution_class` supports
3. **One** field-level mapping document
4. **One** observed Native Result (or a documented blocked/failed attempt)

External Runtime HTTP support is **interaction-specific**. Do not assume every vertical supports `AUTHORIZED_NON_PRODUCTION` or remote Sandbox HTTPS.

---

## Choose your route

| Goal | Start here |
| --- | --- |
| **A. Understand ABIS without code** | [QUICK-VALIDATION.md](QUICK-VALIDATION.md) |
| **B. Run the Reference Runtime locally** | [README — Quick Start](README.md#quick-start) · [VALIDATION.md](VALIDATION.md) |
| **C. Connect your Sandbox / Mock** | [INTEGRATION.md](INTEGRATION.md) |
| **D. Controlled third-party non-production Sandbox interop** | [docs/interop/d11c/](docs/interop/d11c/) (documentation package; no interoperability result is implied by the docs alone) |
| **E. Independently implement or map ABIS semantics** | This section + normative ABIS materials outside this repository |

### Route E — independent implementation (experimental)

You may build your own client, adapter, or semantic mapping experiment.

An independent implementation is **not** automatically:

- ABIS conformant
- certified
- production ready
- validated by ABIS maintainers
- endorsed by ABIS or any provider

Submit sanitized developer evidence through the appropriate GitHub Issue template when you want to share observations — participant reports are not independently verified execution merely because they are filed.

---

## Minimal experiment (supported paths only)

```text
Choose one published interaction
  → GET /v1/reference-profile and interaction Descriptor
  → document operation mapping (synthetic data)
  → POST Preflight (configuration/readiness — not remote reachability)
  → POST Invoke with an advertised execution_class only
  → capture native_result + execution_provenance + trace_reference
  → record outcome_disposition (expected NOT_EVALUATED on Invoke)
```

**Do not** invent undocumented APIs.  
**Do not** bypass Runtime security controls (arbitrary URLs, `REAL_EXTERNAL`, production targets, credential leakage).

### Execution classes (v0.8.0 summary)

| Class | Typical use |
| --- | --- |
| `CONTROLLED_SIMULATOR` | Default — in-process controlled simulators (all advertised interactions) |
| `AUTHORIZED_NON_PRODUCTION` | Authorized HTTP(S) boundary — **restaurant / `reserve` only** when locally configured (localhost Mock or remote authorized Sandbox HTTPS) |
| `REAL_EXTERNAL` | **DENY** |

`shopping` / `submit_order`: **`CONTROLLED_SIMULATOR` only** — external Sandbox execution is **NOT_IMPLEMENTED**.

---

## Useful evidence (what to record)

Helpful developer evidence may include:

- successful execution
- failed execution
- blocked execution (policy, validation, egress)
- mapping ambiguity
- documentation ambiguity
- environment limitation

### Evidence authority

| Source | Label |
| --- | --- |
| Your live Runtime HTTP responses | **ACTUALLY_EXECUTED** (when you ran them) |
| Files under `examples/` in this repo | **REPOSITORY_DESCRIBED** — not observed execution |
| Your written report | **participant / developer evidence** — not automatic certification |

Distinguish **what you ran** from **what the repository describes**.

---

## Semantic firewall

| Statement | Meaning |
| --- | --- |
| **Interaction ≠ Execution** | Choosing an interaction does not imply every execution class or external path is available |
| **Native Result ≠ Business Outcome** | `external_status` such as `CONFIRMED` is not Business Outcome success |
| **Technical Status ≠ Business Outcome** | Transport acceptance is not outcome evaluation |
| **Observe ≠ Completion Determination** | Restaurant `observe` is technical/native only; not supported for external adapter Invokes |
| **Validation ≠ Certification** | Public validation exercises the Reference Runtime — not ABIS certification |
| **Validation ≠ Conformance** | Passing tests here does not mean normative ABIS conformance |
| **Independent implementation ≠ Conformance** | Building your own stack is experimental, not certified |
| **NOT_IMPLEMENTED** | Capability boundary (for example shopping external HTTP) |
| **NOT_EVALUATED** | Invoke `outcome_disposition` for Business Outcome in this Runtime scope |

**Business Outcome** in Reference Runtime scope: **`NOT_EVALUATED`**.

---

## Safety boundaries (unchanged)

- **REAL_EXECUTION PROHIBITED** · **REAL_EXTERNAL DENY**
- No production execution · no real booking · no real purchase · no real payment
- Remote Sandbox only where **explicitly authorized and configured** (`REMOTE_AUTHORIZED`, trusted config)
- No arbitrary URL proxy

---

## Report and integrate

| Intent | Link |
| --- | --- |
| Validation evidence | [Validation Report Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=validation-report.yml) |
| Integration evidence (Sandbox/Mock + Reference Runtime) | [Integration Report Issue](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=integration-report.yml) |
| Independent implementation / builder evidence | [Independent Builder Report](https://github.com/abis-standard/abis-reference-runtime/issues/new?template=independent-builder-report.yml) |

Independent Builder submissions use a separate **progression** and **evidence-authority** model — see [docs/independent-builders/](docs/independent-builders/README.md). This is experimental developer evidence, not certification or conformance.

See also [INTEGRATION.md](INTEGRATION.md) for execution-class detail and [CHANGELOG.md](CHANGELOG.md) for version history.
