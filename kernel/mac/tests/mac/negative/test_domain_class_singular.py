"""Negative/static tests asserting DomainClass frozen-enum invariants.

Anchors:
  - mac/architecture.md §3.4 DomainClass Enum — SQ-5 Frozen Schema
  - mac/architecture.md §6.5 Domain Guard Conditions (Req-E + SQ-5)
  - mac/test-strategy.md v0.3 §11.4 DomainClass Singular Definition
"""

from __future__ import annotations

import subprocess
from pathlib import Path


_REPO_SRC_ROOT = Path(__file__).resolve().parents[3] / "src" / "praxis" / "kernel" / "mac"


def test_mac_t_neg_domain_class_01_single_definition() -> None:
    """MAC-T-NEG-DOMAIN-CLASS-01

    Per arch §3.4 Structural constraint: grep for ``class DomainClass`` across
    the MAC package must return exactly one match. Duplicate definitions via
    copy-paste into workflow modules would defeat SQ-5's frozen-schema
    guarantee.

    Markers: static, critical.
    """
    hits: list[Path] = []
    for py_file in _REPO_SRC_ROOT.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("class DomainClass") and not stripped.startswith("#"):
                hits.append(py_file)
                break

    assert len(hits) == 1, (
        f"DomainClass must have exactly one definition in praxis/kernel/mac/ "
        f"per arch §3.4 SQ-5 frozen schema; found {len(hits)}: {hits}"
    )


def test_mac_t_neg_domain_class_02_exactly_five_values() -> None:
    """MAC-T-NEG-DOMAIN-CLASS-02

    Per arch §3.4: ``DomainClass`` has exactly 5 values
    ``{CONTESTED, CONSENSUS, DETERMINISTIC, BINARY, DIAGNOSTIC}``.
    Adding a sixth class requires a Stage 5 architecture revision, not a
    workflow YAML change. This test locks the current ratified count.

    Markers: static, critical.
    """
    from praxis.kernel.mac.task import DomainClass

    members = list(DomainClass)
    assert len(members) == 5, (
        f"DomainClass must have exactly 5 values per arch §3.4 SQ-5; "
        f"found {len(members)}: {[m.name for m in members]}"
    )

    expected = {"CONTESTED", "CONSENSUS", "DETERMINISTIC", "BINARY", "DIAGNOSTIC"}
    actual = {m.name for m in members}
    assert actual == expected, (
        f"DomainClass value set must match arch §3.4 exactly; "
        f"expected {sorted(expected)}, got {sorted(actual)}"
    )
