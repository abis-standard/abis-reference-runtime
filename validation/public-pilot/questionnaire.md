# ABIS Public Pilot Questionnaire

**Type:** Reusable public validation intake — **not** certification or conformance determination  
**Audience:** Any external participant (developers, students, crowd workers, enterprise validators, etc.)  
**Not** tied to a single platform or provider

Use with [validation/evidence-report-template.md](../evidence-report-template.md) and [validation/public-pilot/evidence-classification.md](evidence-classification.md).

---

## Instructions for participants

Answer from **your actual experience** in this validation session.

Payment or compensation (if any) is for **completing the assigned procedure**, not for:

- validation success
- positive results
- GitHub Stars, Forks, Follows, or favorable reviews

There is no "correct" validation outcome. Incomplete or blocked sessions are valid findings.

Attach or paste your AI validation result and sanitized execution evidence where requested.

**Do not submit:** credentials, tokens, secrets, `Authorization` headers, or PII.

---

## Q1 — Repository access

Could you access the public ABIS Reference Runtime repository?

- [ ] YES
- [ ] NO
- [ ] PARTIAL
- [ ] UNCERTAIN

Optional note (no secrets):

---

## Q2 — Validation entry discovery

Could you find how to validate (Quick Validation, VALIDATION.md, or equivalent public entry)?

- [ ] YES
- [ ] NO
- [ ] UNCERTAIN

Optional note:

---

## Q3 — Procedure progress

How far did you get in this session?

- [ ] Repository investigation completed
- [ ] Runtime execution reached
- [ ] Stopped before completion
- [ ] Unable to determine

Optional note:

---

## Q4 — Runtime execution

Did you **actually execute** the Reference Runtime (not merely read about it)?

- [ ] YES
- [ ] NO
- [ ] UNCERTAIN

### If YES — mark each activity **separately**

- [ ] Tests (e.g. `run_tests.sh`, unit tests)
- [ ] Runtime startup (gateway / server started)
- [ ] HTTP request (any)
- [ ] Preflight
- [ ] Invoke
- [ ] Observe
- [ ] Other: ___________

**Reminder:** Tests successful ≠ Live HTTP validation completed.

---

## Q5 — AI validation result (full text)

Paste the **full** AI validation output from this session.

```text
(paste here)
```

---

## Q6 — Live execution evidence (only if Q4 = YES)

Provide **sanitized** evidence for operations you claim to have executed.

Use `NOT_OBSERVED` or `NOT_PROVIDED` for missing fields — do not invent values.

| Field | Value |
| --- | --- |
| Execution environment | |
| Runtime version (observed) | |
| Executed operation(s) | |
| Endpoint(s) | |
| Sanitized request excerpt | |
| Sanitized response excerpt | |
| `request_id` | |
| `trace_reference` | |
| `external_identifier` | |
| Operations NOT EXECUTED | |

---

## Stop reason (if applicable)

If you stopped before completion, select all that apply:

- [ ] GitHub unavailable
- [ ] Repository content unavailable
- [ ] Validation entry not discovered
- [ ] Starter URL not recognized
- [ ] AI cannot access external web
- [ ] Terminal / Python unavailable
- [ ] Network / DNS limitation
- [ ] Runtime startup failure
- [ ] Procedure unclear
- [ ] Other: ___________

---

## 日本語 — 参加者向け要約

- 報酬は手順完了の対象であり、検証成功・好意的結果・Star/Fork 等の条件ではありません。
- Q4 では **Tests** と **HTTP 実行** を別々に選んでください。
- Q5 に AI の検証結果全文を貼り付けてください。
- Q6 は Q4=YES の場合のみ。トークン・秘密情報・PII は記載しないでください。
- 途中停止も有効な Public Validation Finding です。

---

## Reviewer note

Survey answers alone are not execution evidence. Compare Q1–Q4 with Q5/Q6 using [evidence-classification.md](evidence-classification.md).
