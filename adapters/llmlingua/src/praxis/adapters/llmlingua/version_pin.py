"""Adapter version pin record for the LLMLingua PyPI-pinned Compaction adapter.

Per ADR-9.1.2-4 §3 (`port-contracts.md` v0.2.6; the v0.2.4 substrate
re-anchor Forge -> LLMLingua): the primary CompactionPort substrate.
PyPI-pinned `llmlingua==0.2.2` (microsoft/LLMLingua, MIT) — no `vendor/`
directory (the Stage 9.2 repo-root `vendor/` decision is for
submodule/sidecar substrates; PyPI substrates resolve from the registry —
LiteLLM precedent).

`UPSTREAM_KIND="pypi"` per sibling precedent (LiteLLM / Mem0 / Letta all
PyPI-pinned). Cleo 9.6 wires the real sha256 from `uv.lock` at supply-chain
review.

Per the v0.2.6 ADR-9.1.2-4 §3 corrigendum (W1 OD-1), this file is the
out-of-band home for the adapter's substrate identity — the
determinism-hash idempotency contract is scoped to a fixed adapter +
substrate-pin.
"""

from __future__ import annotations

from typing import Final, Literal

UPSTREAM_NAME: Final[str] = "llmlingua"
UPSTREAM_VERSION: Final[str] = "0.2.2"
UPSTREAM_KIND: Final[Literal["pypi", "submodule", "sidecar_image", "in_tree"]] = "pypi"
# Cleo 9.6 wires the real sha256 from uv.lock for llmlingua==0.2.2 at
# supply-chain review. Placeholder per the LiteLLM/Mem0/Letta convention.
UPSTREAM_LOCK_HASH: Final[str] = "sha256:1a0caedd8d5a65512a85dadb6bfda6f5b3c4b45e5cb9e7b1c6009573f9058572"
ADAPTER_API_VERSION: Final[str] = "0.1.0"
