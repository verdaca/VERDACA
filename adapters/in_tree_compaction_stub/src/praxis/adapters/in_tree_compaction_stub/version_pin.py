"""Adapter version pin record for the in-tree compaction stub adapter.

Per ADR-9.1.2-4 §3 Substitute-readiness (`port-contracts.md` v0.2.6): the
G-1 fallback CompactionPort adapter. Greenfield Verdaca-authored Python —
no external upstream (no PyPI package, no submodule, no sidecar). Sibling
precedent: the Beads in-tree-greenfield adapter (`adapters/beads/`).

`UPSTREAM_KIND="in_tree"`; `UPSTREAM_NAME` is the stub's own identifier and
`UPSTREAM_VERSION` is the adapter's own version — there is no external
upstream to pin (B.1-W2 OD-4 disposition; Beads `beads_in_tree` precedent).
`UPSTREAM_LOCK_HASH` is the sha256 of this adapter's own source tree,
computed by Cleo 9.6 at supply-chain review (placeholder until then).

This file is also the out-of-band home for the stub's substrate identity
per the v0.2.6 ADR-9.1.2-4 §3 corrigendum (W1 OD-1): the determinism-hash
idempotency contract is scoped to a fixed adapter + substrate-pin, and the
substrate identity lives here — not in the hash.
"""

from __future__ import annotations

from typing import Final, Literal

UPSTREAM_NAME: Final[str] = "in_tree_compaction_stub"
UPSTREAM_VERSION: Final[str] = "0.1.0"
UPSTREAM_KIND: Final[Literal["pypi", "submodule", "sidecar_image", "in_tree"]] = "in_tree"
# Computed by Cleo 9.6 at supply-chain review: sha256 over the canonical
# concatenation of all .py files in
# adapters/in_tree_compaction_stub/src/praxis/adapters/in_tree_compaction_stub/.
# Placeholder until 9.6 wires the computation.
UPSTREAM_LOCK_HASH: Final[str] = "sha256:placeholder-cleo-9.6-computes-on-supply-chain-review"
ADAPTER_API_VERSION: Final[str] = "0.1.0"
