"""Test helpers for the Praxis Runtime package.

Lives in the source tree (not tests/) so test modules across the
package can import them with a stable path.  Not shipped in production.
"""

from __future__ import annotations

from praxis.kernel.memory.deployment.manifest import DeploymentManifest


class FakeMemory:
    """Minimal fake Memory for proxy and spawner tests.

    Records every call as a ``(method_name, args, kwargs)`` tuple in
    ``self.calls``.  Returns ``None`` for every method — tests only
    verify that the right call was forwarded.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []  # type: ignore[type-arg]

    async def store_task_outcome(self, tenant_id: str, task: object, outcome: object) -> None:
        self.calls.append(("store_task_outcome", (tenant_id, task, outcome), {}))

    async def store_decision(self, tenant_id: str, decision: object) -> None:
        self.calls.append(("store_decision", (tenant_id, decision), {}))

    async def store_fact(self, tenant_id: str, agent_id: str, run_id: str, fact: object) -> None:
        self.calls.append(("store_fact", (tenant_id, agent_id, run_id, fact), {}))

    async def retrieve_similar_tasks(
        self,
        tenant_id: str,
        signature: object,
        top_k: int = 5,
        min_similarity: float = 0.75,
    ) -> None:
        self.calls.append(("retrieve_similar_tasks", (tenant_id, signature), {}))

    async def retrieve_decisions(self, tenant_id: str, query: str, top_k: int = 10) -> None:
        self.calls.append(("retrieve_decisions", (tenant_id, query), {}))

    async def retrieve_facts(
        self,
        tenant_id: str,
        agent_id: str,
        run_id: str,
        query: str,
        top_k: int = 10,
    ) -> None:
        self.calls.append(("retrieve_facts", (tenant_id, agent_id, run_id, query), {}))

    async def delete(self, tenant_id: str, criteria: object) -> None:
        self.calls.append(("delete", (tenant_id, criteria), {}))

    async def export(self, tenant_id: str, criteria: object) -> None:
        self.calls.append(("export", (tenant_id, criteria), {}))

    async def flag_and_quarantine(
        self,
        tenant_id: str,
        entry_id: str,
        reason: object,
        free_text: str | None = None,
    ) -> None:
        self.calls.append(("flag_and_quarantine", (tenant_id, entry_id, reason, free_text), {}))

    async def health(self) -> None:
        self.calls.append(("health", (), {}))


def make_fake_memory() -> FakeMemory:
    """Return a fresh ``FakeMemory`` with an empty call log."""
    return FakeMemory()


def make_test_manifest(
    tenant_id: str = "test-tenant",
    tenant_hash: str = "abc123def456abc123def456abc123def456abc123def456abc123def456ab12",
) -> DeploymentManifest:
    """Return a ``DeploymentManifest`` populated with safe test values."""
    return DeploymentManifest(tenant_id=tenant_id, tenant_hash=tenant_hash)
