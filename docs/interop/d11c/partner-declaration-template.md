# D-11C Partner Declaration (Template)

Lightweight factual confirmation for a controlled interoperability test.  
**This is not a legal contract** and does not assert ABIS conformance, certification, endorsement, or Business Outcome validity.

---

## Identification

| Field | Value |
| --- | --- |
| **PARTNER_DISPLAY_NAME** | |
| **TECHNICAL_CONTACT** | (name, email or ticket system) |
| **SANDBOX_IDENTIFIER** | (partner-internal label, non-secret) |
| **ENVIRONMENT_CLASSIFICATION** | `SANDBOX` / `MOCK` / `SIMULATOR` / `SYNTHETIC_DEV` (not `PRODUCTION`) |

---

## Factual confirmations

Answer **yes/no** or short factual text. Do **not** use ABIS conformance language.

| Field | Partner response |
| --- | --- |
| **ENDPOINT_OWNERSHIP_CONFIRMED** | Partner controls the declared Sandbox endpoint |
| **NON_PRODUCTION_CONFIRMED** | Endpoint is not production |
| **TEST_CREDENTIAL_CONFIRMED** | Supplied credentials are test-only and isolated from production |
| **NO_INTENTIONAL_PRODUCTION_BOOKING** | Test requests are not intended to create real bookings |
| **NO_PAYMENT** | Test path does not capture payment |
| **AUTOMATED_TEST_PERMISSION** | Partner permits limited automated test requests as described in test plan |
| **EXPECTED_SANDBOX_BEHAVIOR** | (brief: success path + documented rejection path) |
| **EVIDENCE_RETENTION_PERMISSION** | Partner permits ABIS/operator to retain **sanitized** technical evidence per agreed publication level |

---

## Publication and hostname

| Field | Selection |
| --- | --- |
| **PUBLICATION_LEVEL** | `LEVEL_0_PRIVATE` / `LEVEL_1_ANONYMIZED` / `LEVEL_2_ATTRIBUTED` |
| **HOSTNAME_TREATMENT** | `PUBLIC_INTEGRATION_METADATA` / `REDACTED_TARGET_IDENTITY` |

Default before explicit partner permission: **LEVEL_0_PRIVATE** and **REDACTED_TARGET_IDENTITY** in any public artifact.

---

## Confirmation

**PARTNER_CONFIRMATION_DATE:** YYYY-MM-DD

**Confirmed by:**  
Name / role / date

---

## Explicitly out of scope

The partner is **not** asked to declare:

- ABIS compliance or conformant implementation
- ABIS certification
- ABIS endorsement
- Business Outcome validity or verification
- Production readiness
