"""In-tree compaction stub adapter — CompactionPort implementation.

Per ADR-9.1.2-4 §3 Substitute-readiness (`port-contracts.md` v0.2.6): the
G-1 fallback CompactionPort adapter, greenfield Verdaca-authored Python.
A permanent CI fallback — lets the B.2 contract suite run green with no
LLMLingua wheel installed (Phase B.1 handover §5).
"""

from praxis.adapters.in_tree_compaction_stub.adapter import (
    InTreeCompactionStubAdapter,
)

__all__ = ["InTreeCompactionStubAdapter"]
