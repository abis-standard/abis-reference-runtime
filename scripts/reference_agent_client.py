#!/usr/bin/env python3
"""Reference Agent Client CLI — PROFILE → PREFLIGHT → INVOKE (provider-neutral)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SRC = ROOT / "runtime" / "src"
CRS_SRC = ROOT / "reference-business" / "controlled-reservation-simulator" / "src"
for path in (RUNTIME_SRC, CRS_SRC):
    sys.path.insert(0, str(path))

from abis_grp_runtime.agent.reference_client import (  # noqa: E402
    ReferenceAgentClient,
    ReferenceClientConfig,
    gateway_token_from_env,
)
from abis_grp_runtime.gateway.preflight import PREFLIGHT_READY  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="ABIS Reference Agent Client (provider-neutral)")
    parser.add_argument("--base-url", default=os.environ.get("ABIS_DEMO_GATEWAY_BASE_URL", "http://127.0.0.1:9080"))
    parser.add_argument("--vertical", default="restaurant")
    parser.add_argument("--operation", default="reserve")
    parser.add_argument("--execution-class", default="CONTROLLED_SIMULATOR")
    parser.add_argument(
        "--input",
        default=str(ROOT / "examples" / "restaurant_reserve_normal.json"),
        help="Invoke payload JSON file",
    )
    args = parser.parse_args()

    token = gateway_token_from_env()
    config = ReferenceClientConfig(
        base_url=args.base_url,
        vertical=args.vertical,
        operation=args.operation,
        execution_class=args.execution_class,
        gateway_token=token,
    )
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    client = ReferenceAgentClient(config)
    result = client.execute(payload)

    profile_status = "OK" if result.profile_checked else "FAIL"
    preflight_status = result.preflight_state or "NOT_RUN"
    invoke_status = "ATTEMPTED" if result.invoke_attempted else "NOT_ATTEMPTED"
    native_status = result.native_external_status or "-"
    outcome_status = result.outcome_disposition or "-"
    trace_id = (result.trace_reference or {}).get("correlation_id") or "-"

    print(f"PROFILE: {profile_status}")
    print(f"PREFLIGHT: {preflight_status}")
    print(f"INVOKE: {invoke_status}")
    print(f"NATIVE RESULT: {native_status}")
    print(f"OUTCOME: {outcome_status}")
    print(f"TRACE: {trace_id}")

    if result.error:
        print(f"ERROR: {result.error}", file=sys.stderr)
    if result.invoke_attempted and result.preflight_state == PREFLIGHT_READY:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
