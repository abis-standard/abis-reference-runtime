# External integration example — `shopping` / `submit_order`

**Synthetic products and orders only.** No payment. No real purchase.  
**Native Result ≠ Business Outcome.**  
**Observe is not supported** for this interaction in v0.6.0 — do not report Observe for shopping.

---

## 1. External Sandbox / Mock (your environment)

Illustrative non-production catalog/order API (your system — not part of this repository):

```http
POST https://mock-commerce.example.invalid/v1/carts/CART-DEMO-001/submit
Content-Type: application/json

{
  "lines": [
    { "sku": "SKU-DEMO-001", "qty": 1 }
  ],
  "payment_mode": "NONE_SYNTHETIC"
}
```

Hypothetical Mock response (synthetic):

```json
{
  "mock_order_id": "MOCK-ORD-0001",
  "mock_fulfillment": "SIMULATED"
}
```

**Mapping notes (Integrator → ABIS Reference Runtime Invoke `input`):**

| External (Mock) | Runtime Invoke `input` |
| --- | --- |
| `lines[].sku` | `sku_id` (single-SKU demo path) |
| `lines[].qty` | `quantity` |
| (your idempotency policy) | `idempotency_key` |
| — | `test_scenario`: `NORMAL_SUCCESS` |

The Reference Runtime invokes the **Controlled Commerce Simulator** — not your Mock URL.

---

## 2. ABIS interaction mapping

| ABIS-facing | Value |
| --- | --- |
| Vertical | `shopping` |
| Operation | `submit_order` |
| Execution class | `CONTROLLED_SIMULATOR` |
| Business system (Profile) | `abis-demo-commerce-simulator` / `EXTERNAL_BUSINESS_SYSTEM_TEST_DOUBLE` |

```bash
curl -s http://127.0.0.1:9080/v1/reference-profile | python3 -m json.tool
curl -s http://127.0.0.1:9080/v1/reference-profile/interactions/shopping/submit_order | python3 -m json.tool
```

---

## 3. Preflight

```bash
curl -s -X POST http://127.0.0.1:9080/v1/demo/shopping/preflight \
  -H "Content-Type: application/json" \
  -d @examples/shopping_submit_order_preflight.json | python3 -m json.tool
```

Request fixture: `examples/shopping_submit_order_preflight.json`

---

## 4. Invoke

Local demo token and gateway — same as [README Quick Start](../../README.md#quick-start):

```bash
curl -s -X POST http://127.0.0.1:9080/v1/demo/shopping/invoke \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ABIS_DEMO_GATEWAY_TOKEN}" \
  -d @examples/shopping_submit_order_normal.json | python3 -m json.tool
```

Request fixture: `examples/shopping_submit_order_normal.json`  
Example response shape: `examples/shopping_submit_order_normal.json` is request-only; capture **your** Invoke response as evidence.

Record when executed:

- `native_result` (technical/native fields)
- `execution_provenance`, `trace_reference` when present
- `outcome_disposition.disposition` → expect **`NOT_EVALUATED`**

---

## 5. Observe

| Status | v0.6.0 |
| --- | --- |
| `shopping` / `submit_order` | **NOT_ADVERTISED** — Profile `technical_observation` covers **restaurant** only |
| Integrator evidence | Mark Observe as **NOT_EXECUTED** / **NOT_APPLICABLE** |

---

## 6. Evidence checklist

Report via [Integration Report Issue](../../.github/ISSUE_TEMPLATE/integration-report.yml):

- [ ] Mapping table (Mock fields → Invoke `input`)
- [ ] Preflight + Invoke labeled `ACTUALLY_EXECUTED` or `NOT_EXECUTED`
- [ ] Observe explicitly **NOT_EXECUTED** / **NOT_APPLICABLE** for shopping
- [ ] Native Result without Business Outcome claims
- [ ] No payment payloads, production credentials, or PII
