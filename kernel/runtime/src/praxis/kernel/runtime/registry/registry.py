"""Praxis Runtime registry — AgentRegistry query surface.

Architecture references:
  architecture.md §3 (Agent Registry Design)
  architecture.md §3.2 (Query API)
  architecture.md §3.3 (Matching Algorithm)
  architecture.md §3.4 (Confidence Semantics)
  architecture.md §3.7 (Registry Errors)
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from praxis.kernel.runtime.loader.manifest import AgentRuntimeConfig
from praxis.kernel.runtime.registry.embedder import Embedder
from praxis.kernel.runtime.registry.matching import (
    confidence_score,
    fused_score,
    semantic_score,
    token_score,
)

# ---------------------------------------------------------------------------
# Errors  (architecture §3.7)
# ---------------------------------------------------------------------------


class AgentRegistryError(Exception):
    """Base class for registry failures."""


class EmbedderMismatchError(AgentRegistryError):
    """Runtime's embedder model_id does not match expected embedding_model_id."""


class LLMRerankError(AgentRegistryError):
    """LLM fallback returned unparsable output."""


# ---------------------------------------------------------------------------
# Query types  (architecture §3.2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentMatch:
    """A single agent candidate with its match score and explanation."""

    agent: AgentRuntimeConfig
    score: float  # [0.0, 1.0], fused score
    confidence: float  # [0.0, 1.0], separate from score
    match_source: str  # "token", "semantic", "llm_rerank"
    matched_tokens: tuple[str, ...] = field(default_factory=tuple)
    rationale: str = ""


@dataclass(frozen=True)
class AgentQuery:
    """A capability or task-description query against the registry."""

    task_description: str
    required_tokens: tuple[str, ...] = field(default_factory=tuple)
    min_confidence: float = 0.5
    top_k: int = 5


# ---------------------------------------------------------------------------
# AgentRegistry  (architecture §3.2)
# ---------------------------------------------------------------------------


class AgentRegistry:
    """The query surface over the loaded agent catalog.

    Constructed once per Runtime init (or per Loader reload). Thread-safe for
    read operations.
    """

    def __init__(
        self,
        catalog: Mapping[str, AgentRuntimeConfig],
        embedder: Embedder,
        expected_embedding_model_id: str | None = None,
    ) -> None:
        # Hard-fail on embedder mismatch at init time (architecture §3.5, R14)
        if expected_embedding_model_id is not None:
            if embedder.model_id != expected_embedding_model_id:
                raise EmbedderMismatchError(
                    f"Embedder model_id {embedder.model_id!r} does not match "
                    f"expected {expected_embedding_model_id!r}. "
                    "Ensure the Registry and Memory use the same embedding model."
                )
        self._catalog = dict(catalog)
        self._embedder = embedder
        # Pre-compute capability text per agent (concatenated capabilities + role)
        self._agent_capability_texts: dict[str, str] = {
            name: " ".join(cfg.agent.capabilities) + " " + cfg.agent.role
            for name, cfg in self._catalog.items()
        }

    def find_agents(self, query: AgentQuery) -> list[AgentMatch]:
        """Primary query API. Returns up to top_k matches, sorted desc by score.

        Pipeline: required-token filter → token+semantic fusion → confidence →
        LLM tie-break (only if all top-k below min_confidence).
        """
        # Step 1: hard filter by required tokens
        if query.required_tokens:
            candidates = {
                name: cfg
                for name, cfg in self._catalog.items()
                if all(
                    any(rt in cap for cap in cfg.agent.capabilities) for rt in query.required_tokens
                )
            }
        else:
            candidates = self._catalog

        if not candidates:
            return []

        # Step 2+3: compute fused scores
        scored: list[AgentMatch] = []
        query_text = query.task_description.lower()
        for name, cfg in candidates.items():
            caps = cfg.agent.capabilities
            cap_text = self._agent_capability_texts[name]

            ts = token_score(query_text, caps)
            ss = semantic_score(query_text, cap_text, self._embedder)
            fs = fused_score(token_score=ts, semantic_score=ss)

            scored.append(
                AgentMatch(
                    agent=cfg,
                    score=fs,
                    confidence=0.0,  # filled below
                    match_source="semantic" if ts == 0.0 else "token",
                    matched_tokens=tuple(),
                    rationale="",
                )
            )

        # Sort descending by score
        scored.sort(key=lambda m: m.score, reverse=True)

        # Step 4: compute confidence per match
        matches_with_conf: list[AgentMatch] = []
        for i, match in enumerate(scored):
            second = scored[i + 1].score if i + 1 < len(scored) else 0.0
            conf = confidence_score(first_score=match.score, second_score=second)
            rationale = (
                "ambiguous match — consider human selection"
                if 0.5 <= conf < 0.7
                else ("low confidence — LLM rerank attempted" if conf < 0.5 else "")
            )
            matches_with_conf.append(
                AgentMatch(
                    agent=match.agent,
                    score=match.score,
                    confidence=conf,
                    match_source=match.match_source,
                    matched_tokens=match.matched_tokens,
                    rationale=rationale,
                )
            )

        top_k = matches_with_conf[: query.top_k]

        # Step 5: LLM tie-break (soft-fail on LLMRerankError — return pre-rerank)
        if top_k and all(m.confidence < query.min_confidence for m in top_k):
            try:
                top_k = self._llm_rerank(query.task_description, top_k)
            except LLMRerankError:
                # Soft-fail: return semantic results unchanged
                pass

        return top_k

    def get(self, agent_name: str) -> AgentRuntimeConfig | None:
        """Direct lookup by stable agent name. O(1)."""
        return self._catalog.get(agent_name)

    def all_agents(self) -> tuple[AgentRuntimeConfig, ...]:
        """Enumerate the full catalog in alphabetical order."""
        return tuple(sorted(self._catalog.values(), key=lambda c: c.agent.name))

    def _llm_rerank(
        self,
        task_description: str,
        candidates: list[AgentMatch],
    ) -> list[AgentMatch]:
        """LLM-based tie-break fallback (architecture §3.3 step 6).

        At Stage 4.3, this is a stub that raises LLMRerankError — triggering
        the soft-fail path. A real LLM call will be wired in Stage 5+.
        """
        raise LLMRerankError("LLM rerank not yet wired at Stage 4.3 — returning semantic results")


__all__ = [
    "AgentRegistry",
    "AgentMatch",
    "AgentQuery",
    "AgentRegistryError",
    "EmbedderMismatchError",
    "LLMRerankError",
]
