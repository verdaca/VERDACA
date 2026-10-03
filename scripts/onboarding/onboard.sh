#!/usr/bin/env bash
# Onboarding orchestrator — runs the 5-minute path in order, halting on the
# first failure. Run from the repository root inside the synced uv venv.
#
#   bash scripts/onboarding/onboard.sh
#
# Each step exits non-zero with a specific diagnostic; this wrapper stops there
# so the operator fixes one thing at a time. first-message is skipped unless
# VERDACA_SMOKE_BEARER is set (it needs a live OIDC token for the smoke caller).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python}"

echo "== step 1/4: env-check =="
"$PY" "$HERE/env-check.py"

echo "== step 2/4: vkey-provision =="
"$PY" "$HERE/vkey-provision.py"

echo "== step 3/4: policy-smoke =="
"$PY" "$HERE/policy-smoke.py"

echo "== step 4/4: first-message =="
if [ -n "${VERDACA_SMOKE_BEARER:-}" ]; then
  "$PY" "$HERE/first-message.py"
else
  echo "skipped: set VERDACA_SMOKE_BEARER (an OIDC token) to run the live first-message smoke"
fi

echo "onboarding: all steps completed"
