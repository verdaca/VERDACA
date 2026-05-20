"""Adapter version pin record for the in-tree Beads adapter.

Per ADR-9.2-V3 v0.5 corrigendum: greenfield Verdaca-authored Python.
`UPSTREAM_LOCK_HASH` is the sha256 of this adapter's own source tree
(`praxis.adapters.beads-tree`), NOT the kernel `_internal.beads` tree —
the v0.5 corrigendum stripped v0.4's "lifted from kernel" framing
(see `ports-architecture.md` §3 v0.5 Decision bullet on UPSTREAM_LOCK_HASH).
"""

from __future__ import annotations

from typing import Final, Literal

UPSTREAM_NAME: Final[str] = "beads_in_tree"
UPSTREAM_VERSION: Final[str] = "0.1.0"
UPSTREAM_KIND: Final[Literal["pypi", "submodule", "sidecar_image", "in_tree"]] = "in_tree"
# Computed by Cleo 9.6 at supply-chain review: sha256 over the canonical
# concatenation of all .py files in adapters/beads/src/praxis/adapters/beads/.
# Placeholder until 9.6 wires the computation.
UPSTREAM_LOCK_HASH: Final[str] = "sha256:placeholder-cleo-9.6-computes-on-supply-chain-review"
ADAPTER_API_VERSION: Final[str] = "0.1.0"
