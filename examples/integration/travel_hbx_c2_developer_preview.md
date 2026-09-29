# travel/stay_reserve — HBX TEST mTLS adapter (C2, mock-validated only)

Experimental implementation boundary. **Not** live HBX interoperability.

## Scope (D-11S-05C2)

- `AuthorizedMtlsSandboxConnector` and HBX TEST booking mapper implemented
- Validation uses **injected/mock transport only** — **no live HBX request in C2**
- No real booking, no production access, no real credentials in repository
- Public Profile still advertises `CONTROLLED_SIMULATOR` only for travel until C3 proves live controlled interop
- Preflight may evaluate local HBX TEST mTLS configuration for `AUTHORIZED_NON_PRODUCTION` without network I/O
- Business Outcome remains **`NOT_EVALUATED`**; provider-native `CONFIRMED` ≠ Business Outcome success
- HBX publication rights: **NOT_EVALUATED** — this document does not authorize public provider evidence

## Operator configuration (local only)

Certificate paths, encrypted private-key passphrase provider, and API key/secret environment variables are **operator configuration** — not ABIS interaction input, descriptor fields, or evidence fields.

## Provider booking path binding (C2R-B1)

HBX booking execution always targets the explicit operation path constant `HBX_TEST_AUTHORIZED_BOOKING_PATH` (`/hotel-api/1.0/bookings`). The path is verified against the allowlist; **allowlist tuple order does not select the operation**.

No agent interaction field (including `selected_offer_reference`) may select host, port, or URL path.

## Opaque `selected_offer_reference`

The field is opaque at the ABIS boundary: no parsing, decoding, or provider-semantics inference.

Structural validation may treat whitespace-only values as empty. The **exact string value** supplied by the caller is copied into the provider request `rateKey` (byte-for-byte at the Python string level), including harmless leading or trailing whitespace.

## External identifier disclosure surfaces (synthetic)

| Surface | Provider booking reference |
| --- | --- |
| A. Runtime internal `NativeResultEnvelope` | **Present** (e.g. synthetic `SYNTHETIC-HBX-BOOKING-REF-0001` in fixtures only) |
| B. Invoke response to the authorized calling Agent | **Present** in `native_result.external_identifier` (Native Result contract) |
| C. Sanitized gateway evidence (travel + `AUTHORIZED_NON_PRODUCTION`) | **Redacted** — `external_identifier_present: true` only |
| Trace (`FoundationTrace`) | **Absent** for booking reference |

Returning the provider-native identifier to the authorized caller is part of the Native Result contract. It does **not** determine Business Outcome. It must **not** automatically propagate into sanitized evidence or publication-oriented artifacts.

## Preflight boundary (travel `AUTHORIZED_NON_PRODUCTION`)

C2 includes an implementation-level readiness path: trusted/local Preflight may return `PREFLIGHT_READY` when required HBX TEST configuration is structurally present (no network I/O).

The public Profile/Descriptor continues to advertise **`CONTROLLED_SIMULATOR` only** until a later external-interoperability gate (C3+) completes.

`PREFLIGHT_READY` means **local structural/configuration readiness only**. It does **not** mean: HBX accepted credentials, TLS succeeded, offer validity, booking success, interoperability proven, Business Outcome success, production readiness, conformance, or certification.

## Network testing (C2)

HBX unit tests use scoped network tripwires (`socket.create_connection` guard) and injected transport. Full-suite global network isolation is a future defense-in-depth improvement; C2/C3 provider tests remain mock/injected until explicit C3 live execution.
