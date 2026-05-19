"""Adapter version pin record for the in-tree PyPI-pinned Mem0 adapter.

Per ADR-9.2-V1 (`ports-architecture.md` v0.3 §3) + in-tree-PyPI vendor
convention (`ports-architecture.md` v0.3 §4.1): primary adapter in the
dual-adapter Memory port pair (Letta secondary at `adapters/letta/`,
Phase B.2). FIRST `UPSTREAM_KIND="pypi"` adapter in the repo —
Beads (V3 v0.5) and TONL (V2 v0.2) both `in_tree`; Pi-Mono (V4)
`in_tree`. Cross-ADR consistency: `pypi` is the established Literal
value at `adapters/{tonl,beads}/version_pin.py:22`; B.1 is the first
adapter to instantiate it.

Substitute-readiness clause at `port-contracts.md` v0.2.1 §3
substitute-readiness clause: Protocol MUST be implementable on top of
either Mem0 OR Letta without modification.
"""

from __future__ import annotations

from typing import Final, Literal

UPSTREAM_NAME: Final[str] = "mem0ai"
UPSTREAM_VERSION: Final[str] = "1.0.11"
UPSTREAM_KIND: Final[Literal["pypi", "submodule", "sidecar_image", "in_tree"]] = "pypi"
# Cleo 9.6 wires real sha256 from uv.lock for mem0ai==1.0.11 at supply-chain
# review. Placeholder per Beads/TONL convention.
UPSTREAM_LOCK_HASH: Final[str] = "sha256:ddb803bedc22bd514606d262407782e88df929f6991b59f6972fb8a25cc06001"
ADAPTER_API_VERSION: Final[str] = "0.1.0"
