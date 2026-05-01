"""Adapter version pin record for the in-tree TONL adapter.

Per ADR-9.2-V2 v0.2 corrigendum: in-tree wrap of `praxis.kernel.compression.tonl`
substrate. `UPSTREAM_LOCK_HASH` is the sha256 of the kernel substrate's
source root (`praxis.kernel.compression.tonl`-tree), NOT an upstream submodule
SHA — there is no upstream Python package to pin (upstream `tonl-dev/tonl`
is TypeScript-only per 9.4.2 preload Item 7 evidence).

Cross-ADR consistency (per V2 v0.2 binding note): `UPSTREAM_KIND="in_tree"`
mirrors V4 Pi-Mono and V3 Beads — three distinct substrate-composition
stories under the shared in_tree umbrella. V2 wraps kernel substrate that
composes for port primitives; V3 is greenfield (kernel substrate did not
compose); V4 wraps kernel substrate (Stage-1 derived from upstream TS).
"""

from __future__ import annotations

from typing import Final, Literal

UPSTREAM_NAME: Final[str] = "tonl_kernel_substrate"
UPSTREAM_VERSION: Final[str] = "0.1.0"
UPSTREAM_KIND: Final[Literal["pypi", "submodule", "sidecar_image", "in_tree"]] = "in_tree"
# Computed by Cleo 9.6 at supply-chain review: sha256 over the canonical
# concatenation of all .py files in
# kernel/compression/src/praxis/kernel/compression/tonl/.
# Placeholder until 9.6 wires the computation. Substrate path: the kernel
# TONL tree, NOT this adapter's own source root (the adapter is a thin
# wrapper; the substrate is the load-bearing implementation).
UPSTREAM_LOCK_HASH: Final[str] = "sha256:placeholder-cleo-9.6-computes-on-supply-chain-review"
ADAPTER_API_VERSION: Final[str] = "0.1.0"
