#!/usr/bin/env bash
# NR-S-R1 defense-in-depth: grep-based ban on imports from praxis.kernel.memory._internal
# in application code outside the Memory module itself.
#
# Layer 1: ruff TID251 (see pyproject.toml [tool.ruff.lint.flake8-tidy-imports.banned-api])
# Layer 2: this script (catches cases where ruff is not run or is misconfigured)
#
# Policy:
#   - DISALLOWED in: src/praxis/**/*.py (except src/praxis/kernel/memory/**)
#                    tests/**/*.py      (except tests/memory/**, tests/tooling/banned_import_fixtures/**)
#   - ALLOWED   in:  src/praxis/kernel/memory/** (the module owns _internal)
#                    tests/memory/**               (white-box tests)
#                    tests/tooling/banned_import_fixtures/** (self-test fixtures)
#
# Exit 0 on clean, non-zero on any banned import detected.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PATTERN='^\s*(from\s+praxis\.kernel\.memory\._internal|import\s+praxis\.kernel\.memory\._internal)'

# Files to scan: all .py under src/ and tests/
# Excluding: the Memory module itself, whitebox memory tests, and self-test fixtures.
mapfile -t FILES < <(
  {
    find src -type f -name '*.py' 2>/dev/null || true
    find tests -type f -name '*.py' 2>/dev/null || true
  } | grep -Ev '^src/praxis/kernel/memory/' \
    | grep -Ev '^tests/memory/' \
    | grep -Ev '^tests/tooling/banned_import_fixtures/' \
    | sort -u
)

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "check-no-internal-imports: no application files to scan (OK)"
  exit 0
fi

VIOLATIONS=0
for f in "${FILES[@]}"; do
  if grep -nE "$PATTERN" "$f" > /dev/null 2>&1; then
    echo "VIOLATION: $f"
    grep -nE "$PATTERN" "$f" | sed 's/^/  /'
    VIOLATIONS=$((VIOLATIONS + 1))
  fi
done

if [[ $VIOLATIONS -gt 0 ]]; then
  echo ""
  echo "check-no-internal-imports: $VIOLATIONS file(s) violate NR-S-R1 / Req #9."
  echo "Application code must import from the praxis.kernel.memory facade, not _internal.*"
  exit 1
fi

echo "check-no-internal-imports: clean ($((${#FILES[@]})) file(s) scanned)"
exit 0
