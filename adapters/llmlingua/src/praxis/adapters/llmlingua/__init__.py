"""LLMLingua adapter — CompactionPort implementation (PyPI-pinned).

Per ADR-9.1.2-4 §3 (`port-contracts.md` v0.2.6): the primary CompactionPort
adapter — wraps the `llmlingua` PyPI SDK (microsoft/LLMLingua,
`llmlingua==0.2.2`, MIT). Supersedes the v0.1-era `adapters/forge/`
(F-9.4.6-FORGE-SEMANTIC-MISFIT). Sibling: `adapters/litellm/` (9f6a010).
"""

from praxis.adapters.llmlingua.adapter import LLMLinguaAdapter

__all__ = ["LLMLinguaAdapter"]
