#!/usr/bin/env bash
# M-229D.1 — Maintainer pre-push disclosure check (opt-in via install script)
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${DIR}/../.." && pwd)"

echo "=== ABIS Pre-Push Disclosure Check ==="

"${DIR}/run-disclosure-gate.sh"

FIREWALL_ROOT="${ABIS_DISCLOSURE_FIREWALL_ROOT:-}"
if [[ -n "${FIREWALL_ROOT}" ]] && [[ -f "${FIREWALL_ROOT}/scripts/run-private-disclosure-gate.sh" ]]; then
  "${FIREWALL_ROOT}/scripts/run-private-disclosure-gate.sh" "${ROOT}"
  "${FIREWALL_ROOT}/scripts/generate-disclosure-approval.sh" "${ROOT}"
  "${DIR}/verify-private-approval.sh"
else
  echo "M229D-PRIVATE-APPROVAL REVIEW_REQUIRED: set ABIS_DISCLOSURE_FIREWALL_ROOT for private gate"
  echo "Continuing with public checks only."
fi

echo "PRE-PUSH CHECK: PASS"
