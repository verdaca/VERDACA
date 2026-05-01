"""Minimal structural protocol for the Mem0 vendor client.

Captures only the shape of the `mem0.Memory` class that `Mem0Adapter`
depends on. Using a Protocol rather than importing `mem0.Memory`
directly means:

1. Tests can inject a fake that implements the same shape without
   spinning up a real pgvector + LLM stack.
2. If mem0ai renames methods or changes kwargs in a minor version,
   the boundary is a single file to update.
3. Ruff TID251 and static type checkers catch breakage at the boundary
   instead of deep in the facade.

The shape follows mem0ai's public API per architecture §1.2 — `add`,
`search`, `get`, `get_all`, `update`, `delete`, `delete_all`. Praxis
uses a subset.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Mem0ClientProtocol(Protocol):
    """Structural shape of the mem0ai `Memory` client.

    All methods are SYNC — matches mem0ai's public API as of 1.0.x.
    `Mem0Adapter` wraps each call in `asyncio.to_thread` so the protocol
    surface on the Praxis side remains fully async.

    The return types are loosely typed as `dict[str, Any]` and
    `list[dict[str, Any]]` to match mem0ai's own signatures — the
    adapter narrows these into Praxis Pydantic models at the boundary.
    """

    def add(
        self,
        messages: str | list[dict[str, Any]],
        *,
        user_id: str,
        agent_id: str | None = None,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        infer: bool = True,
    ) -> dict[str, Any]: ...

    def search(
        self,
        query: str,
        *,
        user_id: str,
        agent_id: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]: ...

    def get(self, memory_id: str) -> dict[str, Any]: ...

    def get_all(
        self,
        *,
        user_id: str,
        agent_id: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]: ...

    def delete(self, memory_id: str) -> dict[str, Any]: ...

    def delete_all(
        self,
        *,
        user_id: str,
        agent_id: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]: ...


__all__ = ["Mem0ClientProtocol"]
