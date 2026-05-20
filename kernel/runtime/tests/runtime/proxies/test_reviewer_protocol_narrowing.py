"""S4.R-01 Layer 1 — ReviewerMemoryProxy type-level asymmetry enforcement.

Architecture §9.1.1: forbidden methods MUST NOT exist on the class.
This is the Python-interpreter-level structural enforcement claim.
A reviewer agent CANNOT call retrieve_similar_tasks — not because of
a runtime check, but because the method is literally not present.

Test-strategy §6.1.A (hasattr battery) + §6.1.B (AttributeError battery)
+ §11.1.1 / §11.1.2.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from praxis.kernel.runtime.proxies import ReviewerMemoryProxy
from praxis.kernel.runtime.testing import make_fake_memory


@pytest.fixture
def reviewer_proxy() -> ReviewerMemoryProxy:
    return ReviewerMemoryProxy(
        memory=make_fake_memory(),
        tenant_id="test-tenant-r01",
        agent_name="quinn",
        spawn_id=uuid4(),
    )


# ---------------------------------------------------------------------------
# §11.1.1 — Layer 1 hasattr battery
# ---------------------------------------------------------------------------


@pytest.mark.critical
@pytest.mark.asyncio_structural
class TestReviewerProxyMethodPresence:
    """Forbidden methods MUST NOT exist; allowed methods MUST exist."""

    def test_allowed_methods_present(self, reviewer_proxy: ReviewerMemoryProxy) -> None:
        """The 2 allowed methods must be present and callable."""
        assert hasattr(reviewer_proxy, "store_decision")
        assert hasattr(reviewer_proxy, "flag_and_quarantine")
        assert callable(reviewer_proxy.store_decision)
        assert callable(reviewer_proxy.flag_and_quarantine)

    @pytest.mark.parametrize(
        "forbidden_method",
        [
            "retrieve_similar_tasks",
            "retrieve_decisions",
            "retrieve_facts",
            "store_task_outcome",
            "store_fact",
            "delete",
            "export",
            "health",
        ],
    )
    def test_forbidden_methods_absent(
        self, reviewer_proxy: ReviewerMemoryProxy, forbidden_method: str
    ) -> None:
        """Each of the 8 forbidden methods MUST NOT be on ReviewerMemoryProxy.

        A regression here means someone added a method that should not exist.
        The structural claim (arch.md §9.1.1) is violated.
        """
        assert not hasattr(reviewer_proxy, forbidden_method), (
            f"ReviewerMemoryProxy exposes forbidden method {forbidden_method!r} — "
            f"structural enforcement regression. Arch §9.1.1 violated."
        )


# ---------------------------------------------------------------------------
# §11.1.2 — AttributeError battery (error TYPE is load-bearing)
# ---------------------------------------------------------------------------


@pytest.mark.critical
@pytest.mark.asyncio
class TestReviewerProxyForbiddenMethodRaises:
    """Calling a forbidden method raises AttributeError — NOT PermissionError.

    Architecture §9.1.1: 'AttributeError at Python interpreter level, NOT a
    runtime allowlist PermissionError.' The raw AttributeError IS the feature.
    Re-wrapping in PermissionError hides the structural claim.
    """

    async def test_retrieve_similar_tasks_raises_attribute_error(
        self, reviewer_proxy: ReviewerMemoryProxy
    ) -> None:
        with pytest.raises(AttributeError):
            await reviewer_proxy.retrieve_similar_tasks(  # type: ignore[attr-defined]
                tenant_id="test-tenant-r01", signature=None
            )

    async def test_retrieve_decisions_raises_attribute_error(
        self, reviewer_proxy: ReviewerMemoryProxy
    ) -> None:
        with pytest.raises(AttributeError):
            await reviewer_proxy.retrieve_decisions(  # type: ignore[attr-defined]
                tenant_id="test-tenant-r01", query="test"
            )

    async def test_retrieve_facts_raises_attribute_error(
        self, reviewer_proxy: ReviewerMemoryProxy
    ) -> None:
        with pytest.raises(AttributeError):
            await reviewer_proxy.retrieve_facts(  # type: ignore[attr-defined]
                tenant_id="test-tenant-r01", agent_id="a", run_id="r", query="q"
            )

    async def test_store_task_outcome_raises_attribute_error(
        self, reviewer_proxy: ReviewerMemoryProxy
    ) -> None:
        with pytest.raises(AttributeError):
            await reviewer_proxy.store_task_outcome(  # type: ignore[attr-defined]
                tenant_id="test-tenant-r01", task=None, outcome=None
            )

    async def test_store_fact_raises_attribute_error(
        self, reviewer_proxy: ReviewerMemoryProxy
    ) -> None:
        with pytest.raises(AttributeError):
            await reviewer_proxy.store_fact(  # type: ignore[attr-defined]
                tenant_id="test-tenant-r01", agent_id="a", run_id="r", fact=None
            )

    async def test_delete_raises_attribute_error(self, reviewer_proxy: ReviewerMemoryProxy) -> None:
        with pytest.raises(AttributeError):
            await reviewer_proxy.delete(  # type: ignore[attr-defined]
                tenant_id="test-tenant-r01", criteria=None
            )

    async def test_export_raises_attribute_error(self, reviewer_proxy: ReviewerMemoryProxy) -> None:
        with pytest.raises(AttributeError):
            await reviewer_proxy.export(  # type: ignore[attr-defined]
                tenant_id="test-tenant-r01", criteria=None
            )

    async def test_health_raises_attribute_error(self, reviewer_proxy: ReviewerMemoryProxy) -> None:
        with pytest.raises(AttributeError):
            await reviewer_proxy.health()  # type: ignore[attr-defined]

    async def test_does_not_raise_permission_error(
        self, reviewer_proxy: ReviewerMemoryProxy
    ) -> None:
        """Regression guard: AttributeError must not be wrapped in PermissionError."""
        with pytest.raises(AttributeError):
            await reviewer_proxy.retrieve_similar_tasks(  # type: ignore[attr-defined]
                tenant_id="test-tenant-r01", signature=None
            )
        # If PermissionError were raised instead, pytest.raises(AttributeError) would
        # fail with "DID NOT RAISE" — that failure is the structural-claim weakening.


# ---------------------------------------------------------------------------
# Allowed method delegation — reviewer's 2 methods must forward to Memory
# ---------------------------------------------------------------------------


@pytest.mark.critical
@pytest.mark.asyncio
class TestReviewerProxyAllowedMethodDelegation:
    """The 2 allowed methods must delegate to the underlying Memory."""

    @pytest.fixture
    def fake_mem(self):
        return make_fake_memory()

    @pytest.fixture
    def reviewer_with_fake(self, fake_mem) -> ReviewerMemoryProxy:
        return ReviewerMemoryProxy(
            memory=fake_mem,
            tenant_id="test-tenant-r01",
            agent_name="quinn",
            spawn_id=__import__("uuid").uuid4(),
        )

    async def test_store_decision_delegates_to_memory(self, reviewer_with_fake, fake_mem) -> None:
        await reviewer_with_fake.store_decision("t", decision="dec")
        assert fake_mem.calls[-1][0] == "store_decision"

    async def test_flag_and_quarantine_delegates_to_memory(
        self, reviewer_with_fake, fake_mem
    ) -> None:
        await reviewer_with_fake.flag_and_quarantine("t", "entry-1", reason="r")
        assert fake_mem.calls[-1][0] == "flag_and_quarantine"
