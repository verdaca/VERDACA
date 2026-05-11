"""LiteLLM adapter — LLM Proxy port implementation (PyPI-pinned).

Per ADR-9.2-V5 v0.6 (`ports-architecture.md` post-2026-05-11
stacked-corrigendum): sole LLMProxyPort substrate post-H2-falsification
(Q-9.4.5-21). No Docker sidecar; no dual-adapter pattern; no vendor/<sidecar>/.
"""

from praxis.adapters.litellm.adapter import LiteLLMAdapter

__all__ = ["LiteLLMAdapter"]
