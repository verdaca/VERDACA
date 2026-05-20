#!/usr/bin/env bash
# NR-S-R1 self-test harness.
#
# Copies fixture files into scanned paths, runs both enforcement layers,
# asserts banned_caller is REJECTED and clean_caller is ACCEPTED, then cleans up.
#
# Exit 0 if the enforcement stack behaves correctly; non-zero otherwise.

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="$ROOT/.venv/Scripts/python.exe"
if [[ ! -x "$PY" ]]; then
  PY="$ROOT/.venv/bin/python"
fi

FIXTURE_DIR="tests/tooling/banned_import_fixtures"
SCAN_DIR="src/praxis/app_selftest"
BANNED_DEST="$SCAN_DIR/banned_caller.py"
CLEAN_DEST="$SCAN_DIR/clean_caller.py"
INIT_DEST="$SCAN_DIR/__init__.py"

cleanup() {
  rm -rf "$SCAN_DIR"
}
trap cleanup EXIT

mkdir -p "$SCAN_DIR"
touch "$INIT_DEST"

PASS=0
FAIL=0

check() {
  local name="$1"
  local expected="$2"   # "reject" or "accept"
  local actual="$3"     # "reject" or "accept"
  if [[ "$expected" == "$actual" ]]; then
    echo "  PASS  $name (expected=$expected, got=$actual)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL  $name (expected=$expected, got=$actual)"
    FAIL=$((FAIL + 1))
  fi
}

run_ruff() {
  local file="$1"
  "$PY" -m ruff check --quiet "$file" > /dev/null 2>&1 && echo "accept" || echo "reject"
}

run_grep() {
  bash scripts/check-no-internal-imports.sh > /dev/null 2>&1 && echo "accept" || echo "reject"
}

echo ""
echo "=== NR-S-R1 Self-Test ==="
echo ""

# --- Case 1: banned fixture should be REJECTED by both layers ---
echo "Case 1: banned_caller.py (should be REJECTED)"
cp "$FIXTURE_DIR/banned_caller.py" "$BANNED_DEST"
check "ruff TID251"       "reject" "$(run_ruff "$BANNED_DEST")"
check "grep defense layer" "reject" "$(run_grep)"
rm -f "$BANNED_DEST"

echo ""

# --- Case 2: clean fixture should be ACCEPTED by both layers ---
echo "Case 2: clean_caller.py (should be ACCEPTED)"
cp "$FIXTURE_DIR/clean_caller.py" "$CLEAN_DEST"
check "ruff TID251"       "accept" "$(run_ruff "$CLEAN_DEST")"
check "grep defense layer" "accept" "$(run_grep)"
rm -f "$CLEAN_DEST"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
exit 0
