"""Proxy asymmetry tests — mac/test-strategy.md v0.3 §5.2.

Covers MAC-T-ASYM-PROXY-01..05. Verifies the arch §7.2 + runtime §9.0
"AttributeError punchline" structural guarantee: reviewer proxies do
NOT carry ``retrieve_similar_tasks``; calling it raises AttributeError
at the Python interpreter level.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from praxis.kernel.mac.asymmetry import AsymmetryRouter
from praxis.kernel.mac.budget import DEFAULT_MAC_BUDGET
from praxis.kernel.mac.integrations.runtime import (
    AgentRole,
    FakeAgentSpawner,
    MacRuntimeAdapter,
)
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
def test_mac_t_asym_proxy_01_reviewer_proxy_lacks_retrieve_similar_tasks() -> None:
    """MAC-T-ASYM-PROXY-01 — reviewer proxy has no ``retrieve_similar_tasks``.

    Arch §9.0 "the punchline": a reviewer agent that calls
    ``retrieve_similar_tasks`` raises ``AttributeError`` at the Python
    interpreter level. No fallback, no allowlist exception, no
    "trusted reviewer" mode.
    """
    proxy = FakeReviewerProxy()
    assert not hasattr(proxy, "retrieve_similar_tasks")

    with pytest.raises(AttributeError):
        proxy.retrieve_similar_tasks()  # type: ignore[attr-defined]


@pytest.mark.critical
@pytest.mark.asymmetry_structural
def test_mac_t_asym_proxy_02_producer_proxy_has_retrieve_similar_tasks() -> None:
    """MAC-T-ASYM-PROXY-02 — producer proxy has full R/W access."""
    proxy = FakeProducerProxy()
    assert hasattr(proxy, "retrieve_similar_tasks")
    assert hasattr(proxy, "store_task_outcome")
    assert hasattr(proxy, "store_decision")

    # Calls succeed and log.
    proxy.retrieve_similar_tasks("task_sig_123")
    proxy.store_task_outcome("outcome_1")
    proxy.store_decision("decision_1")
    assert len(proxy.call_log) == 3


@pytest.mark.critical
@pytest.mark.asymmetry_structural
def test_mac_t_asym_proxy_03_reviewer_proxy_has_write_methods_only() -> None:
    """MAC-T-ASYM-PROXY-03 — reviewer proxy exposes ``store_decision`` and
    ``flag_and_quarantine`` but NO retrieval.
    """
    proxy = FakeReviewerProxy()
    assert hasattr(proxy, "store_decision")
    assert hasattr(proxy, "flag_and_quarantine")
    assert not hasattr(proxy, "retrieve_similar_tasks")
    assert not hasattr(proxy, "store_task_outcome")


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.asymmetry_structural
async def test_mac_t_asym_proxy_04_all_spawns_route_through_runtime_adapter() -> None:
    """MAC-T-ASYM-PROXY-04 — every MAC spawn goes through :class:`MacRuntimeAdapter`.

    Arch §7.2: MAC NEVER directly imports ``ProducerMemoryProxy`` or
    ``ReviewerMemoryProxy`` from ``runtime.spawner``. The
    :class:`AsymmetryRouter` composes through
    :class:`MacRuntimeAdapter`, which uses :class:`AgentRole` dispatch.

    Test asserts the spawn log captures the correct role for each
    producer / reviewer call.
    """
    spawner = FakeAgentSpawner()
    adapter = MacRuntimeAdapter(
        spawner=spawner,
        shape_guard=lambda: None,
        tenant_id="asym-test",
    )
    router = AsymmetryRouter(runtime_adapter=adapter)

    await router.spawn_producer(agent_id="mac-producer")
    await router.spawn_reviewer_pool(count=2, agent_id_prefix="mac-reviewer")

    # 1 producer + 2 reviewers = 3 spawn entries.
    assert len(spawner.spawn_log) == 3
    roles = [entry[1] for entry in spawner.spawn_log]
    assert roles == [AgentRole.PRODUCER, AgentRole.REVIEWER, AgentRole.REVIEWER]


@pytest.mark.critical
@pytest.mark.asymmetry_structural
@pytest.mark.static
def test_mac_t_asym_proxy_05_s4_r_01_invariant_no_direct_proxy_imports() -> None:
    """MAC-T-ASYM-PROXY-05 — S4.R-01 inherited invariant.

    Arch §7.2 static grep: no file under ``praxis/kernel/mac/`` imports
    ``ProducerMemoryProxy`` or ``ReviewerMemoryProxy`` directly from
    ``praxis.kernel.runtime.spawner``. The AgentRole enum is the only
    legal dispatch. Step 3 already enforces this in
    ``tests/mac/negative/test_pinning.py::test_no_direct_memory_proxy_imports_in_mac``;
    this §5 test is the asymmetry-family companion.
    """
    forbidden = re.compile(
        r"from\s+praxis\.kernel\.runtime\.spawner\s+import\s+.*MemoryProxy",
        re.IGNORECASE,
    )
    violations: list[tuple[Path, int, str]] = []
    for py_file in _MAC_SRC.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if forbidden.search(line):
                violations.append((py_file, lineno, line.strip()))

    assert not violations, (
        f"S4.R-01 violated: direct MemoryProxy imports in MAC source: {violations}"
    )
