# D-11C Sanitization Checklist

Mandatory review **before** any evidence leaves controlled storage or moves to a higher publication level.

Default publication: **LEVEL_0_PRIVATE**.  
Default hostname in public artifacts: **REDACTED_TARGET_IDENTITY** until partner approves otherwise.

---

## MUST REMOVE

- [ ] API keys
- [ ] Bearer tokens
- [ ] `Authorization` headers (any scheme)
- [ ] Cookies and session tokens
- [ ] Real customer data
- [ ] Real guest names
- [ ] Real email addresses
- [ ] Real phone numbers
- [ ] Real reservation IDs (when partner treats them as sensitive)
- [ ] Private account IDs
- [ ] Secret query parameters
- [ ] Internal partner secrets (shared keys, HMAC salts, webhook secrets)

---

## MUST VERIFY

- [ ] Invoke `input` uses **synthetic** data only
- [ ] No production venue / customer / account identifiers
- [ ] No credential in Native Result payload
- [ ] No credential in `execution_provenance`
- [ ] No credential in Foundation Trace / `trace_reference` payloads (if captured)
- [ ] No credential in error messages or stack traces in shared artifacts
- [ ] No credential in screenshots or terminal logs attached to package
- [ ] No credential in raw HTTP dumps included in the package
- [ ] Partner declaration matches redacted content

---

## Hostname handling

| Publication level | Hostname in shared artifacts |
| --- | --- |
| **LEVEL_0_PRIVATE** | May remain in private controlled storage only |
| **LEVEL_1_ANONYMIZED** | Default **REDACTED_TARGET_IDENTITY**; use `target_authorization_id` |
| **LEVEL_2_ATTRIBUTED** | **PUBLIC_INTEGRATION_METADATA** only with explicit partner permission |

---

## Second review

Before publication promotion (0 → 1 → 2):

1. Complete this checklist again on the **final** artifact set.
2. Confirm `hashes.txt` matches sanitized files only.
3. Record reviewer and date in `evidence-report.md` (`TEST_OPERATOR_RECORD`).
