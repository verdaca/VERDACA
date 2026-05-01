"""In-memory fake implementing `Mem0ClientProtocol` for tests.

Andrey's 3B-ii(a) decision explicitly authorizes mocked tests when a
live Mem0 backend is infeasible (pgvector + API keys required). This
fake is the mock: a dict-backed store that honors the three-axis
scoping (user_id × agent_id × run_id) and supports add / search /
get / get_all / delete / delete_all.

This fake is NOT a behavioral replica of Mem0. It does NOT embed or
vector-search. Search is naive substring matching over the `memory`
field, scored inversely by position. That is deliberately simple: the
purpose is to exercise `Mem0Adapter`'s boundary logic (tenant
injection, error translation, async wrapping, parsing of return
shapes), NOT to validate Mem0's retrieval quality.

Quinn (Step 3.4) is expected to add live-Mem0 integration tests.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


def _new_id() -> str:
    return uuid.uuid4().hex


@dataclass
class _StoredRecord:
    id: str
    memory: str
    user_id: str
    agent_id: str | None
    run_id: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self, score: float | None = None) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "memory": self.memory,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "run_id": self.run_id,
            "metadata": dict(self.metadata),
        }
        if score is not None:
            out["score"] = score
        return out


class FakeMem0Client:
    """In-memory Mem0 client conforming to Mem0ClientProtocol structurally."""

    def __init__(self) -> None:
        self._store: dict[str, _StoredRecord] = {}
        # Counters so tests can assert adapter made the expected calls.
        self.add_calls = 0
        self.search_calls = 0
        self.delete_calls = 0
        self.delete_all_calls = 0
        self.get_calls = 0
        self.get_all_calls = 0

    # ------------------------------------------------------------------
    # Mem0ClientProtocol methods
    # ------------------------------------------------------------------

    def add(
        self,
        messages: str | list[dict[str, Any]],
        *,
        user_id: str,
        agent_id: str | None = None,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        infer: bool = True,
    ) -> dict[str, Any]:
        self.add_calls += 1
        text = messages if isinstance(messages, str) else str(messages)
        record_id = _new_id()
        record = _StoredRecord(
            id=record_id,
            memory=text,
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            metadata=dict(metadata or {}),
        )
        self._store[record_id] = record
        return {"results": [record.as_dict()]}

    def search(
        self,
        query: str,
        *,
        user_id: str,
        agent_id: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        self.search_calls += 1
        q_lower = query.lower().strip()
        matches: list[tuple[float, _StoredRecord]] = []
        for rec in self._store.values():
            if not self._scope_matches(rec, user_id, agent_id, run_id):
                continue
            text_lower = rec.memory.lower()
            if q_lower and q_lower in text_lower:
                # Inverse-position scoring: earlier match = higher score.
                pos = text_lower.index(q_lower)
                score = 1.0 - (pos / max(len(text_lower), 1))
                matches.append((score, rec))
            elif not q_lower:
                matches.append((0.0, rec))
        matches.sort(key=lambda pair: pair[0], reverse=True)
        return {"results": [rec.as_dict(score=score) for score, rec in matches[:limit]]}

    def get(self, memory_id: str) -> dict[str, Any]:
        self.get_calls += 1
        rec = self._store.get(memory_id)
        if rec is None:
            # Real Mem0 raises; tests that expect missing handle via
            # Mem0Adapter's error translation.
            raise KeyError(memory_id)
        return rec.as_dict()

    def get_all(
        self,
        *,
        user_id: str,
        agent_id: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        self.get_all_calls += 1
        matches = [
            rec
            for rec in self._store.values()
            if self._scope_matches(rec, user_id, agent_id, run_id)
        ]
        return {"results": [rec.as_dict() for rec in matches[:limit]]}

    def delete(self, memory_id: str) -> dict[str, Any]:
        self.delete_calls += 1
        self._store.pop(memory_id, None)
        return {"status": "deleted", "id": memory_id}

    def delete_all(
        self,
        *,
        user_id: str,
        agent_id: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        self.delete_all_calls += 1
        to_delete = [
            rec_id
            for rec_id, rec in self._store.items()
            if self._scope_matches(rec, user_id, agent_id, run_id)
        ]
        for rec_id in to_delete:
            self._store.pop(rec_id, None)
        return {"status": "deleted", "count": len(to_delete)}

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _scope_matches(
        rec: _StoredRecord,
        user_id: str,
        agent_id: str | None,
        run_id: str | None,
    ) -> bool:
        if rec.user_id != user_id:
            return False
        if agent_id is not None and rec.agent_id != agent_id:
            return False
        if run_id is not None and rec.run_id != run_id:
            return False
        return True

    # ------------------------------------------------------------------
    # Test-only inspection helpers
    # ------------------------------------------------------------------

    def total_records(self) -> int:
        return len(self._store)

    def records_for(self, user_id: str) -> list[_StoredRecord]:
        return [r for r in self._store.values() if r.user_id == user_id]
