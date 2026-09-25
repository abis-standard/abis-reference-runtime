# D-11C Operator Checklist

Runbook for ABIS / test operator. D-11C is **interop**, not penetration testing.

---

## BEFORE TEST

- [ ] Read [partner-requirements.md](partner-requirements.md) — partner eligible
- [ ] Collect completed [partner-declaration-template.md](partner-declaration-template.md) → `partner-declaration.md`
- [ ] Prepare partner overlay (see [evidence-template.md](evidence-template.md))
- [ ] Confirm Runtime on known commit SHA (record in evidence)
- [ ] Configure `REMOTE_AUTHORIZED` adapter env (hostname, port, path, classification, credential env var name)
- [ ] Store credentials only in secure env — never in git
- [ ] Create empty `D11C-EVIDENCE/` tree per evidence template
- [ ] Copy [interop-test-plan.md](interop-test-plan.md) snapshot to `test-plan.md` if needed

**Explicit confirmations:**

- [ ] `REAL_EXTERNAL` **not** selected
- [ ] `PRODUCTION` environment classification **not** selected
- [ ] `REMOTE_AUTHORIZED` selected
- [ ] Synthetic data only
- [ ] No payment
- [ ] No real booking intent
- [ ] Correct `target_authorization_id`
- [ ] Correct partner / overlay version
- [ ] Publication level chosen (default **LEVEL_0_PRIVATE**)

---

## GO / NO-GO

Complete [interop-test-plan.md](interop-test-plan.md) gate **before** Invoke.

- [ ] All 12 GO items satisfied → document **GO**
- [ ] Any missing → **NO-GO** (no network Invoke)

---

## POSITIVE INVOKE

- [ ] Capture Profile → `profile.json`
- [ ] Run Preflight → `preflight.json`
- [ ] Execute positive Invoke with synthetic input
- [ ] Save sanitized `invoke-request.sanitized.json`
- [ ] Save `invoke-response.json`, `execution-provenance.json`
- [ ] Save `native-response.sanitized.json`

---

## NEGATIVE CONTROL

- [ ] Execute one documented safe rejection scenario
- [ ] Save `negative-control/negative-preflight-or-invoke.json`
- [ ] Write `negative-control/negative-summary.md`

---

## EVIDENCE CAPTURE

- [ ] Label each file with evidence authority
- [ ] Fill metadata in `evidence-report.md`
- [ ] Rate three axes + overall per [evidence-template.md](evidence-template.md)
- [ ] Map outcomes to PASS criteria A–J

---

## SANITIZATION

- [ ] Complete [sanitization-checklist.md](sanitization-checklist.md)
- [ ] Second review if promoting publication level

---

## HASHING

SHA-256 integrity for **finalized sanitized** artifacts:

1. List each file under `D11C-EVIDENCE/` except `hashes.txt`.
2. Use stable relative paths (e.g. `preflight.json`, `negative-control/negative-summary.md`).
3. Compute SHA-256 of file bytes (UTF-8 for text files as stored).
4. Write `hashes.txt` lines: `<hex>  <relative-path>`
5. Do **not** include unsanitized secret-bearing raw captures in the hashed public set.

Restricted raw evidence (if retained): separate storage, not in public `hashes.txt`.

---

## VERDICT

- [ ] Record axis verdicts: `TRANSPORT_INTEROP`, `SCHEMA_MAPPING_INTEROP`, `SEMANTIC_BOUNDARY_PRESERVATION`
- [ ] Record overall: `PASS` | `PASS_WITH_FINDINGS` | `INCONCLUSIVE` | `FAIL`
- [ ] Do not use `CERTIFIED`, `CONFORMANT`, or `PRODUCTION_READY`
- [ ] State clearly: Native Result ≠ Business Outcome; Invoke disposition expected `NOT_EVALUATED`

---

## PUBLICATION

- [ ] Default **LEVEL_0_PRIVATE** until partner approves higher level
- [ ] LEVEL 1: anonymize partner identity in public copies
- [ ] LEVEL 2: attribution only with written permission
- [ ] Changing publication level does **not** change technical verdict
- [ ] No endorsement language in published materials
