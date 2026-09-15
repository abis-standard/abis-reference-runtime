#!/usr/bin/env bash
# Clean-room E2E — run outside repository data directory (stdlib-only, synthetic token).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLEAN_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/abis-clean-room.XXXXXX")"
DATA_DIR="${CLEAN_ROOT}/data"
PORT="${ABIS_CLEAN_ROOM_PORT:-0}"
TOKEN="clean-room-synthetic-token-do-not-commit"

cleanup() {
  if [[ -n "${GATEWAY_PID:-}" ]] && kill -0 "${GATEWAY_PID}" 2>/dev/null; then
    kill "${GATEWAY_PID}" 2>/dev/null || true
    wait "${GATEWAY_PID}" 2>/dev/null || true
  fi
  rm -rf "${CLEAN_ROOT}"
}
trap cleanup EXIT

mkdir -p "${DATA_DIR}"
export PYTHONPATH="${ROOT}/runtime/src:${ROOT}/reference-business/controlled-reservation-simulator/src:${ROOT}"
export PYTHONUNBUFFERED=1
export ABIS_DEMO_GATEWAY_TOKEN="${TOKEN}"
export ABIS_GATEWAY_MODE=EXTERNAL_TEST

python3 "${ROOT}/scripts/external_demo_gateway.py" --data-dir "${DATA_DIR}" --port "${PORT}" >"${CLEAN_ROOT}/gateway.log" 2>&1 &
GATEWAY_PID=$!

for _ in $(seq 1 100); do
  if grep -qi "listening on" "${CLEAN_ROOT}/gateway.log" 2>/dev/null; then
    break
  fi
  sleep 0.2
done

BASE_URL="$(grep -Eo 'http://127\.0\.0\.1:[0-9]+' "${CLEAN_ROOT}/gateway.log" | head -1)"
if [[ -z "${BASE_URL}" ]]; then
  echo "clean-room: gateway failed to start" >&2
  cat "${CLEAN_ROOT}/gateway.log" >&2
  exit 1
fi

curl -sf "${BASE_URL}/v1/reference-profile" >/dev/null
curl -sf -X POST "${BASE_URL}/v1/demo/restaurant/preflight" \
  -H "Content-Type: application/json" \
  -d '{"operation":"reserve","execution_class":"CONTROLLED_SIMULATOR"}' >/dev/null

python3 "${ROOT}/scripts/reference_agent_client.py" \
  --base-url "${BASE_URL}" \
  --vertical restaurant \
  --operation reserve \
  --execution-class CONTROLLED_SIMULATOR \
  --input "${ROOT}/examples/restaurant_reserve_normal.json" \
  >"${CLEAN_ROOT}/client-run-1.txt"

python3 "${ROOT}/scripts/reference_agent_client.py" \
  --base-url "${BASE_URL}" \
  --vertical restaurant \
  --operation reserve \
  --execution-class CONTROLLED_SIMULATOR \
  --input "${ROOT}/examples/restaurant_reserve_normal.json" \
  >"${CLEAN_ROOT}/client-run-2.txt"

RES_COUNT="$(python3 - <<PY
import json
from pathlib import Path
state = json.loads(Path("${DATA_DIR}/state.json").read_text())
print(len(state.get("reservations") or {}))
PY
)"

grep -q "PROFILE: OK" "${CLEAN_ROOT}/client-run-1.txt"
grep -q "PREFLIGHT: PREFLIGHT_READY" "${CLEAN_ROOT}/client-run-1.txt"
grep -q "INVOKE: ATTEMPTED" "${CLEAN_ROOT}/client-run-1.txt"
grep -q "NATIVE RESULT: CONFIRMED" "${CLEAN_ROOT}/client-run-1.txt"
grep -q "OUTCOME: NOT_EVALUATED" "${CLEAN_ROOT}/client-run-1.txt"

if [[ "${RES_COUNT}" != "1" ]]; then
  echo "clean-room: expected one reservation, got ${RES_COUNT}" >&2
  exit 1
fi

echo "CLEAN_ROOM_E2E: PASS"
echo "CLEAN_ROOT: ${CLEAN_ROOT}"
echo "BASE_URL: ${BASE_URL}"
