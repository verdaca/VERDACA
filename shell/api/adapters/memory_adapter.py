"""ShellMemoryAdapter — arch §10.3.

C-4 resolution: wire the promotion trigger at session-completion
time. After MAC returns DeliberationResult and user has their
result, shell calls memory.promote_entries() to confirm that
the retrieved experiences were useful.

Binding anchors:
  - shell/architecture.md §10.3 Shell → Memory (C-4 Promotion Hook)
  - memory/architecture.md §6.6 TENTATIVE → CONFIRMED promotion
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class MemoryFacadeProtocol(Protocol):
    """The Memory facade surface that ShellMemoryAdapter calls."""

    async def promote_task_entries(
        self,
        *,
        workspace_id: str,
        task_signature: str,
        confirmation_source: str,
    ) -> None: ...


class ShellMemoryAdapter:
    """C-4 resolution: wire the promotion trigger at session-completion time.

    After MAC returns DeliberationResult and user has their result,
    shell calls memory.promote_entries() to confirm that the retrieved
    experiences were useful.

    TENTATIVE entries from this session → CONFIRMED.
    """

    def __init__(self, memory: MemoryFacadeProtocol) -> None:
        self._memory = memory

    async def promote_entries(
        self,
        *,
        workspace_id: str,
        session_id: str,
        task_signature: str,
    ) -> None:
        """Promote TENTATIVE memory entries to CONFIRMED after session success."""
        await self._memory.promote_task_entries(
            workspace_id=workspace_id,
            task_signature=task_signature,
            confirmation_source=f"session:{session_id}",
        )
