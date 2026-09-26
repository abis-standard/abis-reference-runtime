# D-11C Partner Response Triage

Operational triage after a partner replies to D-11C outreach.  
**Not** a CRM. **Not** interoperability results. **No** vendor-specific status in the public repository.

As of package publication: **no partner is approved**, **no credentials received**, **no external Invoke executed**, **no interoperability verdict exists**. Update operator records privately when facts change.

---

## Response states

| State | Meaning |
| --- | --- |
| **ELIGIBLE** | Enough information to begin [partner-overlay-template.md](partner-overlay-template.md) preparation |
| **NEEDS_CONFIRMATION** | One or more required facts unknown — follow up before overlay work |
| **DECLINED** | Partner declined or environment cannot meet [partner-requirements.md](partner-requirements.md) |

These states are **not** `PASS`, `FAIL`, `CERTIFIED`, or `CONFORMANT`.

### ELIGIBLE does **not** mean

- Interoperability PASS
- Partner endorsement
- API certification
- Production access
- ABIS adoption
- Proof the partner “supports ABIS”

### DECLINED does **not** mean

- Negative judgment of the partner — only that this D-11C run cannot proceed under current protocol requirements

---

## Minimum facts for ELIGIBLE

Align with [partner-requirements.md](partner-requirements.md) and [partner-declaration-template.md](partner-declaration-template.md):

| # | Fact |
| --- | --- |
| 1 | Third-party-managed **HTTPS non-production** Sandbox identified |
| 2 | Reservation-like operation documentable |
| 3 | Synthetic/test-data policy stated |
| 4 | No real booking / payment / production account mutation for the test path |
| 5 | Request/response contract documentable (or reference supplied privately) |
| 6 | Isolated test credential path if auth required |
| 7 | Permission for limited automated requests |
| 8 | Permission to retain **sanitized** evidence |
| 9 | Technical contact for ownership/behavior |
| 10 | Clear separation from production |
| 11 | Publication level and hostname treatment addressable (default **`LEVEL_0_PRIVATE`**) |

If any item is unknown → **NEEDS_CONFIRMATION** (or **DECLINED** if partner confirms impossibility).

---

## NEEDS_CONFIRMATION — minimum follow-up generator

For each unknown below, ask **only** what is missing (no legal escalation language).

| Unknown gap | Example follow-up question |
| --- | --- |
| Non-production unclear | Is the offered endpoint strictly non-production and isolated from live bookings? |
| Test credentials unclear | Can you provide an isolated test credential (not production) and rotation expectations? |
| Real side effects unclear | Will the documented test requests create real reservations, charges, or production account changes? |
| Evidence retention unclear | May we retain sanitized technical logs for internal D-11C evidence under LEVEL_0 private storage? |
| API operation unclear | Which Sandbox operation/path should map to a synthetic hold/reserve attempt, and is schema documentation available? |
| Technical ownership unclear | Who is the technical contact for Sandbox behavior during a short controlled test window? |
| Publication permission unclear | May hostname/partner name appear in public artifacts, or should we use LEVEL_0 / redacted target id only? |

Record answers in private operator storage → refresh triage state.

---

## DECLINED — typical triggers

- Partner declines participation
- Only production endpoint available
- Real booking or payment cannot be isolated
- Evidence retention prohibited
- TLS verification would need to be weakened
- Arbitrary URL / undocumented contract
- Sandbox indistinguishable from production
- Requirements in [partner-requirements.md](partner-requirements.md) exclusion table apply

---

## Next steps by state

| State | Next action |
| --- | --- |
| **ELIGIBLE** | Start private partner overlay; complete declaration; proceed toward operator checklist (still **no Invoke** until GO gates) |
| **NEEDS_CONFIRMATION** | Send minimum follow-ups; remain **NO-GO** for Invoke |
| **DECLINED** | Archive triage record privately; do not configure Runtime for that target |

---

## Boundaries preserved

- `REAL_EXTERNAL` = **DENY** (Runtime — not enabled by triage)
- `PRODUCTION` / `UNKNOWN` environment classification = **not** acceptable for D-11C configuration
- `REMOTE_AUTHORIZED` = trusted config only (no Invoke URL override)
- External Observe = **NOT_SUPPORTED** for this path
- Shopping remote = **NOT_IMPLEMENTED**
- Invoke **Business Outcome** = **`NOT_EVALUATED`**

Triage does not modify Runtime behavior or ABIS normative semantics.
