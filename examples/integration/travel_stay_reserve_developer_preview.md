# travel/stay_reserve — Developer Preview (CONTROLLED_SIMULATOR)

Experimental Reference Runtime interaction. **Not** normative ABIS semantics.

## Scope (current phase)

- `execution_class`: `CONTROLLED_SIMULATOR` only
- External provider execution: **not implemented**
- Real hotel booking: **not performed**
- Business Outcome: **NOT_EVALUATED** (Native Result ≠ Business Outcome)

## Invoke

`POST /v1/demo/travel/invoke` with `operation: stay_reserve` and provider-neutral `structured_input`
(`stay`, `occupancy`, `holder`, `guests`, `selected_offer_reference`, `client_reference`).

`selected_offer_reference` is an opaque string; the simulator does not validate provider offer semantics.
