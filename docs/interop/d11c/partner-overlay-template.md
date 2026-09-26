# D-11C Partner Overlay (Template)

**Purpose:** Operator/evidence preparation document for one controlled interoperability run.  
**Not** a normative ABIS object, Runtime configuration format, or git-committed partner record.

Store completed overlays in **private** `D11C-EVIDENCE/` (or operator-controlled storage).  
**Do not commit** partner-specific overlays, credentials, hostnames, or proprietary schemas to the public repository.

**NO SECRET VALUES IN THIS DOCUMENT** — credential values use the Runtime’s approved environment-variable mechanism only.

Prerequisites: [partner-declaration-template.md](partner-declaration-template.md) completed and [response-triage.md](response-triage.md) disposition **`ELIGIBLE`** (or equivalent confirmed facts).

---

## A. Partner identity

| Field | Value |
| --- | --- |
| **PARTNER_ID** | Stable non-secret slug (feeds `PARTNER_ID` in evidence metadata) |
| **PARTNER_DISPLAY_NAME** | As in partner declaration |
| **TECHNICAL_CONTACT** | Reference only (no secrets) |
| **ENDPOINT_OWNERSHIP_CONFIRMED** | Per partner declaration |
| **PUBLICATION_LEVEL** | `LEVEL_0_PRIVATE` / `LEVEL_1_ANONYMIZED` / `LEVEL_2_ATTRIBUTED` (default **`LEVEL_0_PRIVATE`**) |

---

## B. Test baseline (record at execution time)

Record from the **actual** Runtime deployment used for the test — do not copy static defaults from docs.

| Field | Recorded value |
| --- | --- |
| **RUNTIME_VERSION** | From Profile / `GET /v1/reference-profile` |
| **RUNTIME_COMMIT_SHA** | Git SHA of `abis-reference-runtime` |
| **PROFILE_VERSION** | From Profile |
| **EXECUTION_SURFACE** | e.g. `reference-execution-surface-6` |
| **DESCRIPTOR_VERSION** | From Descriptor |

---

## C. Interaction

| Field | Value |
| --- | --- |
| **interaction_id** | `restaurant` / `reserve` |
| **execution_class** | `AUTHORIZED_NON_PRODUCTION` |
| **target_mode** | `REMOTE_AUTHORIZED` |

Invoke must not supply URL, hostname, port, path, or credentials.

---

## D. Mapping

| Field | Value |
| --- | --- |
| **MAPPING_VERSION** | `d11c.restaurant.reserve.<PARTNER_ID>.v1` (increment when mapping semantics change) |
| **partner_operation** | Partner Sandbox operation name or path reference (document link or private annex — avoid unnecessary proprietary copy in public repos) |
| **request_mapping_reference** | Pointer to field-level ABIS Invoke `input` → partner request (operator-held) |
| **response_mapping_reference** | Pointer to partner response → `NativeResultEnvelope` (operator-held) |

---

## E. Target authorization (safe metadata only)

Trusted Runtime configuration — must match [interop-test-plan.md](interop-test-plan.md) Phase B.

| Field | Value |
| --- | --- |
| **TARGET_AUTHORIZATION_ID** | Stable id (recorded in provenance) |
| **authorized_hostname** | Exact hostname (treatment per publication level — see [sanitization-checklist.md](sanitization-checklist.md)) |
| **HOSTNAME_TREATMENT** | `PUBLIC_INTEGRATION_METADATA` / `REDACTED_TARGET_IDENTITY` |
| **authorized_port** | Typically `443` unless explicitly declared non-default TLS port |
| **authorized_path** | Exact allowlisted path |
| **HTTPS** | Required for `REMOTE_AUTHORIZED` |
| **redirect_policy** | Runtime denies redirects; no redirect expansion |

**Prohibited:** arbitrary Invoke-supplied URL/hostname/path, query-based target switching, redirect-based path expansion.

---

## F. Environment

Confirm facts align with partner declaration and [partner-requirements.md](partner-requirements.md).  
**Unknown → operational NO-GO** (this document does not enforce Runtime policy).

| Confirmation | Partner / operator attestation |
| --- | --- |
| **ENVIRONMENT_CLASSIFICATION** | `SANDBOX` / `MOCK` / `SIMULATOR` / `SYNTHETIC_DEV` — **not** `PRODUCTION` or `UNKNOWN` |
| Non-production Sandbox | |
| Synthetic/test data only | |
| No real booking side effect | |
| No payment | |
| No production account mutation | |

---

## G. Authentication

| Field | Value |
| --- | --- |
| **authentication_type** | e.g. `Bearer` (classification only) |
| **credential_env_var** | **Name only** of env var (e.g. `ABIS_RESTAURANT_HTTP_ADAPTER_CREDENTIAL_ENV` target) — **never the value** |

Credentials must not appear in Profile, Descriptor, Native Result, `execution_provenance`, trace, or evidence package committed to git.

---

## H. Positive control

One Invoke expected to be **processable** per partner documentation.

| Item | Expected behavior |
| --- | --- |
| Transport | HTTPS/TLS to authorized target; egress per Runtime v0.8.0 policy |
| Partner processing | Partner-documented acceptance path |
| Native Result mapping | Fields mapped per `response_mapping_reference` |
| **Business Outcome disposition** | **`NOT_EVALUATED`** (required) |

Partner-native `SUCCESS` / `CONFIRMED` is **not** Business Outcome success.

---

## I. Negative control

Exactly **one** safe, partner-documented rejection (see [interop-test-plan.md](interop-test-plan.md) Phase G).

| Field | Value |
| --- | --- |
| **negative_case** | e.g. invalid synthetic field / documented unavailable slot |
| **expected_partner_native_response** | Partner-documented rejection shape |
| **expected_runtime_mapping** | Transport or mapping outcome (not penetration testing) |
| **Business Outcome disposition** | **`NOT_EVALUATED`** |

Not permitted: SSRF probes, TLS attacks, credential abuse, production identifiers, security scanning.

---

## J. Evidence / publication

| Field | Value |
| --- | --- |
| **sanitization_required** | Yes — [sanitization-checklist.md](sanitization-checklist.md) |
| **hostname_publication** | Per `HOSTNAME_TREATMENT` and `PUBLICATION_LEVEL` |
| **partner_attribution_permission** | Per partner declaration |
| **evidence_retention_permission** | Per partner declaration |

Do not infer publication permission from technical participation alone.

---

## K. GO / NO-GO (overlay readiness)

This section **does not replace** the mandatory Invoke gate in [interop-test-plan.md](interop-test-plan.md) and [operator-checklist.md](operator-checklist.md).  
Complete **both** before any network Invoke.

| Overlay readiness | Check |
| --- | --- |
| Partner permission | Declaration + triage **`ELIGIBLE`** |
| Non-production | Confirmed in Section F |
| Test credentials | Available via approved secret path only (name configured, value not in overlay) |
| Target authorization | Section E complete and matches Runtime env config |
| Schema mapping | Section D references complete |
| Synthetic payload | Reviewed per test plan |
| Negative control | Section I partner-approved |
| Evidence policy | `D11C-EVIDENCE/` prepared; publication level set |
| Sanitization | Checklist reviewed |

**Overlay decision:** `GO` / `NO_GO`

- **`NO_GO`:** Do not Invoke.  
- **`GO`:** Proceed to operator **GO / NO-GO** gate (12 items in interop test plan).  
- Completing this template alone **does not** authorize Invoke.

---

## Storage

| Location | Allowed content |
| --- | --- |
| Private `D11C-EVIDENCE/` | Sanitized overlay copy for this run |
| Public git repository | **Generic templates only** — no partner-filled overlays |
