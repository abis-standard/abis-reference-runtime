# Controlled Reservation Simulator (CRS)

**Reference Business System — MOCK-ONLY test double**

| Field | Value |
| --- | --- |
| Classification | `EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE` |
| `semantic_authority` | **NONE** |
| REAL_BOOKING | **NONE** |
| `business_system` | `abis-demo-restaurant-simulator` |

## What this is

A local restaurant reservation simulator that:

- Emits **Business System Native Result** envelopes only
- Persists synthetic reservations to `<data_dir>/state.json`
- Supports **idempotency** via `idempotency_key`
- Uses synthetic IDs only (`TEST-CUST-*`, `TEST-RSV-*`)

**Native Result ≠ ABIS Outcome.** The ABIS Reference Runtime applies separate reference evaluation; this simulator is not an authority.

## Public v0.1 scenario

Use `test_scenario: NORMAL_SUCCESS` for the documented first-run path.

## What this is NOT

- Not a real restaurant booking system
- Not a normative ABIS API
- Not ABIS Runtime Core
