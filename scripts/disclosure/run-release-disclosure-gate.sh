#!/usr/bin/env bash
# M-229D.1 — Release/tag disclosure gate (fail-closed)
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${DIR}/../.." && pwd)"

echo "=== ABIS Release Disclosure Gate (M-229D.1) ==="

"${DIR}/run-disclosure-gate.sh"
"${DIR}/verify-private-approval.sh"

echo "RELEASE DISCLOSURE GATE: PASS"
