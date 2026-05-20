"""Fake Memory facade for MAC unit tests — arch §10.2 contract shape.

Mirrors ``praxis.kernel.memory.facade.Memory`` at the method level.
Step 6 uses this to test the named MAC contract (``mac.publish``,
``mac.reuse_successful``, ``mac.backfill``) without spinning up the
real Stage 3 Memory module.

The fake satisfies the structural contract MAC consumes per arch §10.2
without modifying Memory's signature. Step 7 (Stage 7 POV Harness)
substitutes the real ``Memory`` instance via constructor injection.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeMemoryFacade:
    """Method-level fake of ``praxis.kernel.memory.facade.Memory``.

    Captures every call to ``store_task_outcome`` and
    ``retrieve_similar_tasks`` so MAC asymmetry / publish tests can
    verify the call shape without a real Memory instance.
    """

    stored_outcomes: list[dict[str, Any]] = field(default_factory=list)
    retrieve_log: list[dict[str, Any]] = field(default_factory=list)
    canned_retrieve_results: list[Any] = field(default_factory=list)

    async def store_task_outcome(
        self,
        *,
        tenant_id: str,
        task: Any,
        outcome: Any,
    ) -> str:
        """Mirror of ``Memory.store_task_outcome``. Returns a fake
        ``entry_id`` (ULID-shaped) so the bootstrap loader can wire it
        into the sidecar.
        """
        entry_id = "01HX" + secrets.token_hex(11).upper()
        self.stored_outcomes.append(
            {
                "tenant_id": tenant_id,
                "task": task,
                "outcome": outcome,
                "entry_id": entry_id,
            }
        )
        return entry_id

    async def retrieve_similar_tasks(
        self,
        *,
        tenant_id: str,
        signature: Any,
        top_k: int = 5,
        min_similarity: float = 0.75,
    ) -> list[Any]:
        """Mirror of ``Memory.retrieve_similar_tasks``. Returns the
        ``canned_retrieve_results`` list — tests pre-populate this to
        script retrieval behavior.
        """
        self.retrieve_log.append(
            {
                "tenant_id": tenant_id,
                "signature": signature,
                "top_k": top_k,
                "min_similarity": min_similarity,
            }
        )
        return list(self.canned_retrieve_results)

    def reset(self) -> None:
        self.stored_outcomes.clear()
        self.retrieve_log.clear()
        self.canned_retrieve_results.clear()


__all__ = ("FakeMemoryFacade",)
