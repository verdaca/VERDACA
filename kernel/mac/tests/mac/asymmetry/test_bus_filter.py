"""Layer 2 bus filter tests — mac/test-strategy.md v0.3 §5.3.

Covers MAC-T-ASYM-BUS-01..03. Layer 2 communication-bus filtering is
Runtime's responsibility per runtime/architecture.md §7.5 — MAC
consumes filtered events without re-implementing the filter.

Citation per v0.3 §5.3 (repaired from v0.1 ``arch §7.3`` drift):
  - runtime/architecture.md §7.5 Layer 2 communication-bus filtering
  - mac/architecture.md §7.5 Symmetric Asymmetry Boundary
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from praxis.kernel.mac.testing.fakes.fake_memory_proxies import (
    FakeProducerProxy,
    FakeReviewerProxy,
)


_MAC_SRC = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "praxis"
    / "kernel"
    / "mac"
)


@pytest.mark.critical
@pytest.mark.asymmetry_structural
def test_mac_t_asym_bus_01_producer_has_full_proxy_surface() -> None:
    """MAC-T-ASYM-BUS-01 — producer proxy exposes full memory surface.

    Layer 2 filtering applies at the proxy seam: producers see full
    layers, reviewers see a filtered subset. Step 5 verifies the
    proxy shapes match the arch §7.3 information-hiding table via the
    FakeProducerProxy / FakeReviewerProxy attribute sets.
    """
    producer = FakeProducerProxy()
    # Producer has full R/W.
    producer_methods = [m for m in dir(producer) if not m.startswith("_")]
    assert "retrieve_similar_tasks" in producer_methods
    assert "store_task_outcome" in producer_methods
    assert "store_decision" in producer_methods


@pytest.mark.critical
@pytest.mark.asymmetry_structural
def test_mac_t_asym_bus_02_reviewer_cannot_publish_retrieval_calls() -> None:
    """MAC-T-ASYM-BUS-02 — reviewer proxy write-only surface.

    Per runtime §7.5 Layer 2 filter: reviewer can write (store_decision,
    flag_and_quarantine) but cannot read retrieval events. This maps
    to the proxy attribute set: retrieve_similar_tasks is absent.
    """
    reviewer = FakeReviewerProxy()
    reviewer_methods = [m for m in dir(reviewer) if not m.startswith("_")]
    assert "store_decision" in reviewer_methods
    assert "flag_and_quarantine" in reviewer_methods
    # The retrieval method MUST be absent.
    assert "retrieve_similar_tasks" not in reviewer_methods


@pytest.mark.critical
@pytest.mark.asymmetry_structural
@pytest.mark.static
def test_mac_t_asym_bus_03_filter_applied_at_proxy_construction_not_router() -> None:
    """MAC-T-ASYM-BUS-03 — MAC does NOT re-implement bus filtering.

    The Layer 2 bus filter is Runtime's responsibility. MAC's
    asymmetry router composes proxies through MacRuntimeAdapter; it
    does NOT inspect or filter bus events itself. Verify by grepping
    MAC source for bus-filter implementation keywords — there should
    be none.
    """
    # MAC source should not define a bus filter class or function.
    forbidden_patterns = [
        re.compile(r"class\s+Layer2BusFilter"),
        re.compile(r"def\s+filter_bus_events"),
        re.compile(r"class\s+BusEventFilter"),
    ]
    violations: list[tuple[Path, int, str]] = []
    for py_file in _MAC_SRC.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pat in forbidden_patterns:
                if pat.search(line):
                    violations.append((py_file, lineno, line.strip()))

    assert not violations, (
        "MAC must NOT re-implement Layer 2 bus filtering — it is "
        f"Runtime §7.5's responsibility. Found: {violations}"
    )
