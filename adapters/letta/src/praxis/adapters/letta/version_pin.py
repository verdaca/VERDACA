"""Adapter version pin record for the in-tree PyPI-pinned Letta adapter.

Per ADR-9.2-V1 (`ports-architecture.md` v0.3 §3) + in-tree-PyPI vendor
convention (`ports-architecture.md` v0.3 §4.1): SECONDARY adapter in the
dual-adapter Memory port pair (Mem0 primary at `adapters/mem0/`, shipped
34a4eca). SECOND `UPSTREAM_KIND="pypi"` adapter in the repo (B.1 first;
Beads/TONL stay `in_tree`). Cross-ADR consistency: `pypi` is the
established Literal value at `adapters/{tonl,beads}/version_pin.py:22`;
B.1 instantiated it; B.2 reuses verbatim.

Substitute-readiness clause at `port-contracts.md` v0.2.1 §3
substitute-readiness clause: Protocol MUST be implementable on top of
either Mem0 OR Letta without modification. This adapter's existence is
the load-bearing test of that property.

Server pre-1.0 caveat (Q-B2-Sub-9 disposition): SDK `letta-client`
v1.10.3 is post-1.0; server-side `letta` is pre-1.0 (v0.16.7 /
2026-03-31 per Letta SDK survey 2026-05-03 §2). SDK API stability is
downstream of server schema; v0.x server may break compat at v0.17.0+
and force SDK v2.0 bump. Adapter consumers should be aware that the
range pin `>=1.10,<2.0` brackets SDK semantic stability, NOT server
schema stability.
"""

from __future__ import annotations

from typing import Final, Literal

UPSTREAM_NAME: Final[str] = "letta-client"
UPSTREAM_VERSION: Final[str] = "1.10.3"
UPSTREAM_KIND: Final[Literal["pypi", "submodule", "sidecar_image", "in_tree"]] = "pypi"
# Cleo 9.6 wires real sha256 from uv.lock for letta-client==1.10.3 at
# supply-chain review. Placeholder per Beads/TONL/Mem0 convention.
UPSTREAM_LOCK_HASH: Final[str] = "sha256:placeholder-cleo-9.6-computes-on-supply-chain-review"
ADAPTER_API_VERSION: Final[str] = "0.1.0"
