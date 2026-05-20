"""TONL adapter — Serialization port implementation (in-tree kernel-substrate wrap).

Per ADR-9.2-V2 v0.2 corrigendum (`ports-architecture.md` §3): in-tree wrap
of `praxis.kernel.compression.tonl` substrate. Single TONL implementation,
two consumers (kernel `compression/orchestrator.py` + this adapter). Direct
ADR-9.2-V4 Pi-Mono shape, NOT v0.5-Beads-greenfield shape.
"""

from praxis.adapters.tonl.adapter import TONLAdapter

__all__ = ["TONLAdapter"]
