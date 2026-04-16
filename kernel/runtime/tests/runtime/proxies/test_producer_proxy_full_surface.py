"""S4.R-01 Layer 1 — ProducerMemoryProxy full-surface delegation tests.

Test-strategy §6.1.A (producer positive surface) + §11.1.1.
Producer proxy must implement all 10 MemoryProtocol methods and delegate
each one to the underlying Memory instance.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from praxis.kernel.runtime.proxies import ProducerMemoryProxy
from praxis.kernel.runtime.testing import make_fake_memory


@pytest.fixture
def fake_memory():
    return make_fake_memory()


@pytest.fixture
def producer_proxy(fake_memory) -> ProducerMemoryProxy:
    return ProducerMemoryProxy(
        memory=fake_memory,
        tenant_id="test-tenant-p01",
        agent_name="amelia",
        spawn_id=uuid4(),
    )


# ---------------------------------------------------------------------------
# Surface completeness — all 10 methods must be present
# ---------------------------------------------------------------------------


@pytest.mark.critical
class TestProducerProxySurfaceCompleteness:
    """All 10 MemoryProtocol methods must exist and be callable."""

    @pytest.mark.parametrize(
        "method_name",
        [
            "store_task_outcome",
            "store_decision",
            "store_fact",
            "retrieve_similar_tasks",
            "retrieve_decisions",
            "retrieve_facts",
            "delete",
            "export",
            "flag_and_quarantine",
            "health",
        ],
    )
    def test_all_protocol_methods_present(
        self, producer_proxy: ProducerMemoryProxy, method_name: str
    ) -> None:
        assert hasattr(producer_proxy, method_name), (
            f"ProducerMemoryProxy is missing {method_name!r} — full surface broken."
        )
        assert callable(getattr(producer_proxy, method_name))


# ---------------------------------------------------------------------------
# Delegation — each method forwards the call to the wrapped Memory
# ---------------------------------------------------------------------------


@pytest.mark.critical
@pytest.mark.asyncio
class TestProducerProxyDelegation:
    """Each method must delegate to the underlying Memory and record the call."""

    async def test_store_task_outcome_delegates(self, producer_proxy, fake_memory):
        await producer_proxy.store_task_outcome("t", task="task", outcome="out")
        assert fake_memory.calls[-1][0] == "store_task_outcome"

    async def test_store_decision_delegates(self, producer_proxy, fake_memory):
        await producer_proxy.store_decision("t", decision="dec")
        assert fake_memory.calls[-1][0] == "store_decision"

    async def test_store_fact_delegates(self, producer_proxy, fake_memory):
        await producer_proxy.store_fact("t", "agent-1", "run-1", fact="f")
        assert fake_memory.calls[-1][0] == "store_fact"

    async def test_retrieve_similar_tasks_delegates(self, producer_proxy, fake_memory):
        await producer_proxy.retrieve_similar_tasks("t", signature="sig")
        assert fake_memory.calls[-1][0] == "retrieve_similar_tasks"

    async def test_retrieve_decisions_delegates(self, producer_proxy, fake_memory):
        await producer_proxy.retrieve_decisions("t", query="q")
        assert fake_memory.calls[-1][0] == "retrieve_decisions"

    async def test_retrieve_facts_delegates(self, producer_proxy, fake_memory):
        await producer_proxy.retrieve_facts("t", "agent-1", "run-1", "q")
        assert fake_memory.calls[-1][0] == "retrieve_facts"

    async def test_delete_delegates(self, producer_proxy, fake_memory):
        await producer_proxy.delete("t", criteria="c")
        assert fake_memory.calls[-1][0] == "delete"

    async def test_export_delegates(self, producer_proxy, fake_memory):
        await producer_proxy.export("t", criteria="c")
        assert fake_memory.calls[-1][0] == "export"

    async def test_flag_and_quarantine_delegates(self, producer_proxy, fake_memory):
        await producer_proxy.flag_and_quarantine("t", "entry-1", reason="r")
        assert fake_memory.calls[-1][0] == "flag_and_quarantine"

    async def test_health_delegates(self, producer_proxy, fake_memory):
        await producer_proxy.health()
        assert fake_memory.calls[-1][0] == "health"
