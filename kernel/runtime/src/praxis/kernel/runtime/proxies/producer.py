"""ProducerMemoryProxy — full MemoryProtocol surface for producer agents.

Architecture §4.1.2 / §9.1.1: a producer agent can read from Memory
and write all three record types.  Every method on this proxy delegates
to the underlying Memory instance — there are no access-control gates
because producers are fully trusted by construction.

Contrast with ReviewerMemoryProxy: that class has only 2 methods.  This
class has all 10, matching the full MemoryProtocol surface.
"""

from __future__ import annotations

from uuid import UUID


class ProducerMemoryProxy:
    """Memory proxy for producer agents — full MemoryProtocol delegation."""

    __slots__ = ("_memory", "_tenant_id", "_agent_name", "_spawn_id")

    def __init__(
        self,
        *,
        memory: object,
        tenant_id: str,
        agent_name: str,
        spawn_id: UUID,
    ) -> None:
        self._memory = memory
        self._tenant_id = tenant_id
        self._agent_name = agent_name
        self._spawn_id = spawn_id

    # ------------------------------------------------------------------
    # Write surface
    # ------------------------------------------------------------------

    async def store_task_outcome(self, tenant_id: str, task: object, outcome: object) -> object:
        return await self._memory.store_task_outcome(tenant_id, task=task, outcome=outcome)  # type: ignore[attr-defined]

    async def store_decision(self, tenant_id: str, decision: object) -> object:
        return await self._memory.store_decision(tenant_id, decision)  # type: ignore[attr-defined]

    async def store_fact(self, tenant_id: str, agent_id: str, run_id: str, fact: object) -> object:
        return await self._memory.store_fact(tenant_id, agent_id, run_id, fact=fact)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Read surface
    # ------------------------------------------------------------------

    async def retrieve_similar_tasks(
        self,
        tenant_id: str,
        signature: object,
        top_k: int = 5,
        min_similarity: float = 0.75,
    ) -> object:
        return await self._memory.retrieve_similar_tasks(  # type: ignore[attr-defined]
            tenant_id, signature=signature, top_k=top_k, min_similarity=min_similarity
        )

    async def retrieve_decisions(self, tenant_id: str, query: str, top_k: int = 10) -> object:
        return await self._memory.retrieve_decisions(tenant_id, query=query, top_k=top_k)  # type: ignore[attr-defined]

    async def retrieve_facts(
        self,
        tenant_id: str,
        agent_id: str,
        run_id: str,
        query: str,
        top_k: int = 10,
    ) -> object:
        return await self._memory.retrieve_facts(  # type: ignore[attr-defined]
            tenant_id, agent_id, run_id, query=query, top_k=top_k
        )

    # ------------------------------------------------------------------
    # GDPR surface
    # ------------------------------------------------------------------

    async def delete(self, tenant_id: str, criteria: object) -> object:
        return await self._memory.delete(tenant_id, criteria)  # type: ignore[attr-defined]

    async def export(self, tenant_id: str, criteria: object) -> object:
        return await self._memory.export(tenant_id, criteria)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Quarantine / observability
    # ------------------------------------------------------------------

    async def flag_and_quarantine(
        self,
        tenant_id: str,
        entry_id: str,
        reason: object,
        free_text: str | None = None,
    ) -> object:
        return await self._memory.flag_and_quarantine(  # type: ignore[attr-defined]
            tenant_id, entry_id, reason, free_text
        )

    async def health(self) -> object:
        return await self._memory.health()  # type: ignore[attr-defined]


__all__ = ["ProducerMemoryProxy"]
