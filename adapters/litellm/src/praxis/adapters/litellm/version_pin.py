"""Adapter version pin record for the LiteLLM PyPI-pinned LLM Proxy adapter.

Per ADR-9.2-V5 v0.6 (`ports-architecture.md` post-2026-05-11 stacked-
corrigendum): sole LLMProxyPort substrate post-H2-falsification per
Q-9.4.5-21. Replaces v0.2 ratified dual-adapter RTK+LiteLLM design with
LiteLLM-only PyPI library (no Docker sidecar; no vendor/<sidecar>/).

UPSTREAM_KIND="pypi" per sibling-precedent (Mem0/Letta both PyPI-pinned;
Beads/TONL/Pi-Mono all in_tree). Q-9.4.5-20 sibling-pattern-import
precedence honored.
"""

from __future__ import annotations

from typing import Final, Literal

UPSTREAM_NAME: Final[str] = "litellm"
UPSTREAM_VERSION: Final[str] = "1.83.14"
UPSTREAM_KIND: Final[Literal["pypi", "submodule", "sidecar_image", "in_tree"]] = "pypi"
# Cleo 9.6 wires real sha256 from uv.lock for litellm==1.83.14 at supply-chain
# review. Placeholder per Mem0/Letta convention.
UPSTREAM_LOCK_HASH: Final[str] = "sha256:24aef9b47cdc424c833e32f3727f411741c690832cd1fe4405e0077144fe09c9"
ADAPTER_API_VERSION: Final[str] = "0.1.1"
