"""Memory integration — arch §10.2 + memory §6.6 named MAC contract.

The MAC consumes the Memory facade exclusively (no ``_internal.*``
access). The "named MAC contract" per memory/architecture.md §6.6
lines 913–915 is a MAC-side wrapper over the existing Memory facade —
it does NOT extend Memory's public API. The three named MAC methods
(``mac.publish``, ``mac.reuse_successful``, ``mac.backfill``) are MAC
method names that call into Memory's existing facade methods:

  - ``mac.publish(...)``           → ``Memory.store_task_outcome(...)``  + sidecar write
  - ``mac.reuse_successful(...)``  → ``Memory.retrieve_similar_tasks(...)`` + sidecar lookup
  - ``mac.backfill(...)``          → batch loop calling the above

**Stage 3 Memory schema is FROZEN.** No new columns on
``experience_entries``. The sidecar table ``mac_bootstrap_metadata``
(arch §8.1 Option Y) holds MAC-specific metadata — it is owned by MAC
via ``praxis/kernel/mac/migrations/0001_mac_bootstrap_metadata.py``,
NOT by Memory.

Binding anchors:
  - mac/architecture.md §10.2 Memory Integration
  - mac/architecture.md §8.1 Option Y Bootstrap Protocol
  - memory/architecture.md §2.1 facade
  - memory/architecture.md §6.6 lines 913–915 named MAC contract
  - mac/test-strategy.md v0.3 §6.2 MAC-T-INT-MEMORY-PUBLISH-01..02 etc.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from praxis.kernel.mac.migrations.mac_bootstrap_metadata_0001 import (
    BootstrapMetadataStore,
)


@runtime_checkable
class MemoryFacadeProtocol(Protocol):
    """Shape of the Memory facade MAC consumes. Method-level Protocol;
    real :class:`praxis.kernel.memory.facade.Memory` satisfies this.
    """

    async def store_task_outcome(
        self, *, tenant_id: str, task: Any, outcome: Any
    ) -> str: ...

    async def retrieve_similar_tasks(
        self,
        *,
        tenant_id: str,
        signature: Any,
        top_k: int = 5,
        min_similarity: float = 0.75,
    ) -> list[Any]: ...


class MacMemoryAdapter:
    """MAC's named-contract wrapper over :class:`MemoryFacadeProtocol`.

    The three method names ``publish_outcome``, ``reuse_successful``,
    and ``backfill_outcome`` correspond to the named MAC contract per
    memory §6.6 lines 913–915. They are MAC-internal wrappers — Memory
    has no methods named ``mac.publish`` etc.; the "named MAC
    contract" is a naming convention for MAC's wrappers, NOT an
    extension of Memory's surface.
    """

    def __init__(
        self,
        *,
        memory: MemoryFacadeProtocol,
        sidecar: BootstrapMetadataStore,
    ) -> None:
        self._memory = memory
        self._sidecar = sidecar

    async def publish_outcome(
        self,
        *,
        tenant_id: str,
        task_signature: Any,
        outcome: Any,
    ) -> str:
        """Named MAC contract: ``mac.publish``.

        Calls ``Memory.store_task_outcome`` via the facade. The sidecar
        write is the bootstrap loader's responsibility (it knows
        whether the row is a gold-standard bootstrap entry); the
        publish path for organic deliberations does NOT touch the
        sidecar.
        """
        entry_id = await self._memory.store_task_outcome(
            tenant_id=tenant_id,
            task=task_signature,
            outcome=outcome,
        )
        return entry_id

    async def reuse_successful(
        self,
        *,
        tenant_id: str,
        signature: Any,
        top_k: int = 5,
        min_similarity: float = 0.75,
    ) -> list[Any]:
        """Named MAC contract: ``mac.reuse_successful``.

        Calls ``Memory.retrieve_similar_tasks`` via the facade. Step 6
        does not yet annotate retrieval results with the sidecar's
        ``is_bootstrap_entry`` flag — Stage 7 POV Harness adds the
        annotation pass when it wires the real Memory instance.
        """
        return await self._memory.retrieve_similar_tasks(
            tenant_id=tenant_id,
            signature=signature,
            top_k=top_k,
            min_similarity=min_similarity,
        )


__all__ = (
    "MacMemoryAdapter",
    "MemoryFacadeProtocol",
)
