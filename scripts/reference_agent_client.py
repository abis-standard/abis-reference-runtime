#!/usr/bin/env python3
"""Reference Agent Client CLI — DISCOVERY → PROFILE → PREFLIGHT → INVOKE (provider-neutral)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_SRC = ROOT / "runtime" / "src"
CRS_SRC = ROOT / "reference-business" / "controlled-reservation-simulator" / "src"
CSS_SRC = ROOT / "reference-business" / "controlled-commerce-simulator" / "src"
for path in (RUNTIME_SRC, CRS_SRC, CSS_SRC):
    sys.path.insert(0, str(path))

from abis_grp_runtime.agent.reference_client import (  # noqa: E402
    ReferenceAgentClient,
    ReferenceClientConfig,
    gateway_token_from_env,
)
from abis_grp_runtime.gateway.preflight import PREFLIGHT_READY  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="ABIS Reference Agent Client (provider-neutral)")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Known Reference Runtime base URL (mutually exclusive with --business-origin)",
    )
    parser.add_argument(
        "--business-origin",
        default=None,
        help="Known Business web origin for Reference Runtime Pointer discovery",
    )
    parser.add_argument("--vertical", default="restaurant")
    parser.add_argument("--operation", default="reserve")
    parser.add_argument("--execution-class", default="CONTROLLED_SIMULATOR")
    parser.add_argument(
        "--input",
        default=str(ROOT / "examples" / "restaurant_reserve_normal.json"),
        help="Invoke payload JSON file",
    )
    args = parser.parse_args()

    base_url = args.base_url or os.environ.get("ABIS_DEMO_GATEWAY_BASE_URL")
    business_origin = args.business_origin
    if not base_url and not business_origin:
        base_url = "http://127.0.0.1:9080"

    token = gateway_token_from_env()
    config = ReferenceClientConfig(
        base_url=base_url,
        business_origin=business_origin,
        vertical=args.vertical,
        operation=args.operation,
        execution_class=args.execution_class,
        gateway_token=token,
    )
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    client = ReferenceAgentClient(config)
    result = client.execute(payload)

    if result.business_origin:
        print(f"BUSINESS ORIGIN: {result.business_origin}")
        print(f"RUNTIME DISCOVERY: {'OK' if result.pointer_checked else 'FAIL'}")
    if result.runtime_base_url:
        print(f"RUNTIME: {result.runtime_base_url}")
    print(f"PROFILE: {'OK' if result.profile_checked else 'FAIL'}")
    print(f"DESCRIPTOR: {'OK' if result.descriptor_checked else 'FAIL'}")
    if result.profile_version is not None:
        print(f"PROFILE VERSION: {result.profile_version}")
    if result.runtime_version:
        print(f"RUNTIME VERSION: {result.runtime_version}")
    if result.execution_surface_revision:
        print(f"EXECUTION SURFACE: {result.execution_surface_revision}")
    print(f"PREFLIGHT: {result.preflight_state or 'NOT_RUN'}")
    print(f"INVOKE: {'ATTEMPTED' if result.invoke_attempted else 'NOT_ATTEMPTED'}")
    print(f"NATIVE RESULT: {result.native_external_status or '-'}")
    if result.native_external_identifier:
        print(f"NATIVE ID: {result.native_external_identifier}")
    print(f"OUTCOME: {result.outcome_disposition or '-'}")
    trace_id = (result.trace_reference or {}).get("correlation_id") or result.correlation_id or "-"
    print(f"TRACE: {trace_id}")
    if result.invoke_attempted and result.preflight_state == PREFLIGHT_READY:
        print("FINAL STATUS: PASS")
    else:
        print("FINAL STATUS: FAIL")

    if result.error:
        print(f"ERROR: {result.error}", file=sys.stderr)
    if result.invoke_attempted and result.preflight_state == PREFLIGHT_READY:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
