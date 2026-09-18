#!/usr/bin/env bash
# M-229D.1 — Opt-in local pre-push hook installer (does not modify global git config)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOK="${ROOT}/.git/hooks/pre-push"
CHECK="${ROOT}/scripts/disclosure/pre-push-check.sh"

if [[ ! -d "${ROOT}/.git" ]]; then
  echo "Not a git repository: ${ROOT}" >&2
  exit 1
fi

cat > "${HOOK}" <<EOF
#!/usr/bin/env bash
# ABIS disclosure pre-push hook (installed by install-pre-push-hook.sh)
exec "${CHECK}"
EOF

chmod +x "${HOOK}" "${CHECK}"
echo "Installed pre-push hook: ${HOOK}"
echo "Optional: export ABIS_DISCLOSURE_FIREWALL_ROOT=\"/path/to/Disclosure Firewall\""
