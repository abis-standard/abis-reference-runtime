#!/usr/bin/env bash
# M-229F.1 — Verify content-tree-bound disclosure approval (public-safe)
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${DIR}/../.." && pwd)"
APPROVAL_FILE="${ROOT}/.abis/disclosure-approval.json"
HASH_SCRIPT="${DIR}/compute-content-tree-hash.py"

if [[ ! -f "${APPROVAL_FILE}" ]]; then
  echo "M229D-PRIVATE-APPROVAL BLOCK: Disclosure policy violation." >&2
  exit 1
fi

CURRENT_HASH="$(python3 "${HASH_SCRIPT}" "${ROOT}" --source head)"

python3 - "${APPROVAL_FILE}" "${CURRENT_HASH}" <<'PY'
import json
import sys
from datetime import datetime, timezone

path, current_hash = sys.argv[1], sys.argv[2]
try:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
except (OSError, json.JSONDecodeError):
    fail()

def fail() -> None:
    print(
        "M229D-PRIVATE-APPROVAL BLOCK: "
        "approved content does not match current repository content.",
        file=sys.stderr,
    )
    sys.exit(1)

schema = data.get("schema_version")
if schema != "1.1":
    fail()

if data.get("binding_type") != "content_tree":
    fail()

if data.get("status") != "PASS":
    fail()

approved = data.get("approved_content_hash")
if not approved or approved != current_hash:
    fail()

required = {"M229D-003", "M229D-005", "M229D-009", "M229D-010"}
passed = set(data.get("controls_passed") or [])
if not required.issubset(passed):
    fail()

issued = data.get("issued_at")
if issued:
    try:
        datetime.fromisoformat(issued.replace("Z", "+00:00"))
    except ValueError:
        fail()

expires = data.get("expires_at")
if expires:
    try:
        exp = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        if exp <= datetime.now(timezone.utc):
            fail()
    except ValueError:
        fail()

approval_id = data.get("approval_id", "unknown")
issued_at = data.get("issued_at", "")
print(f"M229D-PRIVATE-APPROVAL PASS: approval_id={approval_id} issued_at={issued_at}")
PY
