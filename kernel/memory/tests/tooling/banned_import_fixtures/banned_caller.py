# Self-test fixture (BANNED) — NR-S-R1.
# This file intentionally contains a banned import. It lives under
# tests/tooling/banned_import_fixtures/ which is excluded from CI-level enforcement
# via ruff per-file-ignores and the grep script's path filter. The fixture is only
# used by the banned-import self-test harness, which COPIES it to a scanned location
# and then asserts both layers reject it.
from praxis.kernel.memory._internal import something  # noqa: F401
