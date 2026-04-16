"""ReviewerMemoryProxy — 2-method surface for reviewer agents.

Architecture §9.1.1 / §4.1.3: the asymmetry between producer and
reviewer is enforced at the Python interpreter level, NOT via runtime
access-control checks.  The forbidden methods are ABSENT — they are not
defined on this class.  Calling them raises AttributeError naturally.
There is no __getattr__ guard, no PermissionError wrapper, no explicit
raise.  The absence IS the feature.

Allowed surface (2 methods):
  store_decision      — reviewer can record a review decision / dissent
  flag_and_quarantine — reviewer can quarantine problematic content

Every other MemoryProtocol method is absent.
"""

from __future__ import annotations

from uuid import UUID


class ReviewerMemoryProxy:
    """Memory proxy for reviewer agents — write-only, decision/quarantine only.

    Constructor parameters match ProducerMemoryProxy for Spawner symmetry.
    """

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
    # Allowed surface — 2 methods only
    # ------------------------------------------------------------------

    async def store_decision(self, tenant_id: str, decision: object) -> object:
        """Delegate to the underlying Memory.store_decision."""
        return await self._memory.store_decision(tenant_id, decision)  # type: ignore[attr-defined]

    async def flag_and_quarantine(
        self,
        tenant_id: str,
        entry_id: str,
        reason: object,
        free_text: str | None = None,
    ) -> object:
        """Delegate to the underlying Memory.flag_and_quarantine."""
        return await self._memory.flag_and_quarantine(  # type: ignore[attr-defined]
            tenant_id, entry_id, reason, free_text
        )

    # NOTE: No other methods.  Accessing retrieve_*, store_task_outcome,
    # store_fact, delete, export, or health on this object raises
    # AttributeError at the Python interpreter level.  This is intentional
    # and is the structural enforcement of §9.1.1.


__all__ = ["ReviewerMemoryProxy"]
