# travel/stay_reserve — HBX TEST mTLS adapter (C2, mock-validated only)

Experimental implementation boundary. **Not** live HBX interoperability.

## Scope (D-11S-05C2)

- `AuthorizedMtlsSandboxConnector` and HBX TEST booking mapper implemented
- Validation uses **injected/mock transport only** — **no live HBX request in C2**
- No real booking, no production access, no real credentials in repository
- Public Profile still advertises `CONTROLLED_SIMULATOR` only for travel until C3 proves live controlled interop
- Preflight may evaluate local HBX TEST mTLS configuration for `AUTHORIZED_NON_PRODUCTION` without network I/O
- Business Outcome remains **`NOT_EVALUATED`**; provider-native `CONFIRMED` ≠ Business Outcome success

## Operator configuration (local only)

Certificate paths, encrypted private-key passphrase provider, and API key/secret environment variables are **operator configuration** — not ABIS interaction input, descriptor fields, or evidence fields.
