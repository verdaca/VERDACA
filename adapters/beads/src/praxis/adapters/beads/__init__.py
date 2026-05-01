"""Beads adapter — Versioned State port implementation (greenfield in-tree).

Per ADR-9.2-V3 v0.5 corrigendum (`ports-architecture.md` §3). Codename
"Beads" inherited from Stage 9 frame; NOT a substrate-lift target.
"""

from praxis.adapters.beads.adapter import BeadsAdapter

__all__ = ["BeadsAdapter"]
