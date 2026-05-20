"""Letta adapter — Memory port implementation (PyPI-pinned upstream).

Per ADR-9.2-V1 (`ports-architecture.md` v0.3 §3) + in-tree-PyPI vendor
convention (v0.3 §4.1): in-tree PyPI-pinned wrap of letta-client SDK.
SECONDARY adapter in the dual-adapter pair (Mem0 primary at
`adapters/mem0/`, shipped 34a4eca). Existence proves Memory port
Protocol is substrate-neutral per substitute-readiness clause at
`port-contracts.md` v0.2.1 §3 — adapter is structurally interchangeable
with Mem0 adapter at the Protocol surface (`isinstance` both = True;
`inspect.signature` parity verified at #3).
"""

from praxis.adapters.letta.adapter import LettaAdapter

__all__ = ["LettaAdapter"]
