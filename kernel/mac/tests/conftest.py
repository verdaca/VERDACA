"""Root conftest — gates ``nightly_only`` and ``release_gate`` markers.

Tests marked ``nightly_only`` or ``release_gate`` are SKIPPED in the
default (PR-gate) run. Opt-in flags:

  - ``--run-nightly`` enables nightly_only tests
  - ``--run-release`` enables release_gate tests

Anchors:
  - mac/test-strategy.md v0.3 §14.4 CI Budget (Tier 1/2/3/4 tier discipline)
  - mac/test-strategy.md v0.3 §14.7 Mock vs Live Split — PR-gate NEVER runs Tier 3/4
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add ports src to path so praxis.ports.* is importable
_PORTS_SRC = Path(__file__).resolve().parents[3] / "ports" / "src"
if _PORTS_SRC.exists() and str(_PORTS_SRC) not in sys.path:
    sys.path.insert(0, str(_PORTS_SRC))


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-nightly",
        action="store_true",
        default=False,
        help="Run tests marked nightly_only (Tier 3 calibration drift + benchmark harness).",
    )
    parser.addoption(
        "--run-release",
        action="store_true",
        default=False,
        help="Run tests marked release_gate (Tier 4 A4 Spearman replay).",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    run_nightly = config.getoption("--run-nightly", default=False)
    run_release = config.getoption("--run-release", default=False)

    skip_nightly = pytest.mark.skip(
        reason="nightly_only — Tier 3; pass --run-nightly to enable"
    )
    skip_release = pytest.mark.skip(
        reason="release_gate — Tier 4; pass --run-release to enable"
    )

    for item in items:
        if "nightly_only" in item.keywords and not run_nightly:
            item.add_marker(skip_nightly)
        if "release_gate" in item.keywords and not run_release:
            item.add_marker(skip_release)
