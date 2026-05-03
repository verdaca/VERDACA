"""Mem0 adapter — Memory port implementation (PyPI-pinned upstream).

Per ADR-9.2-V1 (`ports-architecture.md` v0.3 §3) + in-tree-PyPI vendor
convention (`ports-architecture.md` v0.3 §4.1): in-tree PyPI-pinned
wrap of mem0ai SDK. PRIMARY adapter in the dual-adapter Memory port
pair (Letta secondary at `adapters/letta/` per Phase B.2;
substitute-readiness clause at `port-contracts.md` v0.2.1 §3
substitute-readiness clause).
"""

from praxis.adapters.mem0.adapter import Mem0Adapter

__all__ = ["Mem0Adapter"]
