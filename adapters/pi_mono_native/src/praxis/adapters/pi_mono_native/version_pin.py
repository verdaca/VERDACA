"""Adapter version pin record for the in-tree-native Pi-Mono adapter.

Per ADR-9.2-V4 (`ports-architecture.md` v0.3 §3): in-tree Python
reimplementation of Pi-Mono pricing math. UPSTREAM_VERSION records the
Pi-Mono TS dump-file fragment hash (`8a5edab282632443`, per the
`badlogic-pi-mono-*.txt` reference dump in `_bmad-output/`) as the
derivation-origin identifier for parity audit per S1 disposition.
NOT necessarily an upstream git SHA — the dump-file is informational
reference, not a binding pin (per ADR-9.2-V4 monthly drift workflow).
UPSTREAM_LOCK_HASH is sha256 of this adapter's own source tree per
Beads in-tree-native sibling precedent (computed by Cleo 9.6 at
supply-chain review).
"""

from __future__ import annotations

from typing import Final, Literal

UPSTREAM_NAME: Final[str] = "pi_mono"
UPSTREAM_VERSION: Final[str] = "8a5edab282632443"
UPSTREAM_KIND: Final[Literal["pypi", "submodule", "sidecar_image", "in_tree"]] = "in_tree"
UPSTREAM_LOCK_HASH: Final[str] = "sha256:placeholder-cleo-9.6-computes-on-supply-chain-review"
ADAPTER_API_VERSION: Final[str] = "0.1.0"
