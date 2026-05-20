"""Learning loop — arch §8.3 cross-session promotion.

The :class:`LearningLoop` wraps :class:`MacMemoryAdapter.publish_outcome`
with the arch §8.3 admission gate:

  - ``DeliberationResult.final_phase == "complete"`` (failed
    deliberations are not published)
  - ``composite_score >= confidence_threshold`` (default 75.0 — below
    this, the result is interesting but not authoritative enough to
    seed future retrieval)

Confidence is computed from the variance of the 12 effective gate
scores per arch §8.3 formula. Low-variance high-mean → high
confidence; wide-spread → low confidence.

Binding anchors:
  - mac/architecture.md §8.3 Cross-Session Promotion Loop
  - memory/architecture.md §6.3 admission thresholds
  - memory/architecture.md §6.4 tentative→confirmed promotion
  - mac/test-strategy.md v0.3 §6.2 MAC-T-INT-MEMORY-PUBLISH-01..02
"""

from __future__ import annotations

from typing import Any

from praxis.kernel.mac.integrations.memory import MacMemoryAdapter
from praxis.kernel.mac.results import DeliberationResult


DEFAULT_CONFIDENCE_THRESHOLD: float = 75.0
"""Composite-score threshold below which results are NOT published.
Per arch §8.3 default; configurable per deployment."""


class LearningLoop:
    """Cross-session learning loop owner.

    Wraps :class:`MacMemoryAdapter` with the admission gate. Tests:

      - ``MAC-T-INT-MEMORY-PUBLISH-01``: high-confidence complete →
        ``store_task_outcome`` called.
      - ``MAC-T-INT-MEMORY-PUBLISH-02``: low-composite or failed →
        NOT published.
      - ``MAC-T-INT-MEMORY-REUSE-01``: ``mark_reused_successfully``
        wires through to the adapter.
    """

    def __init__(
        self,
        *,
        memory_adapter: MacMemoryAdapter,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> None:
        self._memory = memory_adapter
        self._threshold = confidence_threshold

    async def publish(
        self, *, tenant_id: str, deliberation: DeliberationResult
    ) -> str | None:
        """Publish a successful deliberation to Memory if it clears the gate.

        Returns the ``entry_id`` from
        :meth:`MacMemoryAdapter.publish_outcome` on success, or
        ``None`` when the result is not eligible (failed terminal,
        below-threshold composite).
        """
        if deliberation.final_phase != "complete":
            return None
        if (
            deliberation.composite_score is None
            or deliberation.composite_score < self._threshold
        ):
            return None

        confidence = self._compute_confidence(deliberation)

        outcome = {
            "composite_score": deliberation.composite_score,
            "confidence": confidence,
            "cost_usd": deliberation.cost_usd,
            "duration_seconds": deliberation.duration_seconds,
            "forge_degraded": deliberation.forge_degraded,
            "backtrack_count": deliberation.backtrack_count,
            "gate_scores": {
                gate_id: score.effective_score
                for gate_id, score in deliberation.gate_scores.items()
            },
        }

        return await self._memory.publish_outcome(
            tenant_id=tenant_id,
            task_signature=deliberation.task_signature,
            outcome=outcome,
        )

    async def mark_reused_successfully(
        self,
        *,
        tenant_id: str,
        signature: Any,
        top_k: int = 5,
    ) -> list[Any]:
        """Named MAC contract: ``mac.reuse_successful``.

        Currently a thin pass-through to
        :meth:`MacMemoryAdapter.reuse_successful`. Stage 7 POV Harness
        will add the sidecar annotation pass that flags retrieved
        bootstrap entries.
        """
        return await self._memory.reuse_successful(
            tenant_id=tenant_id,
            signature=signature,
            top_k=top_k,
        )

    @staticmethod
    def _compute_confidence(deliberation: DeliberationResult) -> float:
        """Variance-based confidence per arch §8.3.

        ``confidence = 1.0 - (variance_of_effective_scores / 4.0)``,
        clamped to [0.0, 1.0]. Wide-spread gate scores → low
        confidence; narrow-spread → high confidence. The 4.0 divisor
        normalizes the variance to a 1-5 score range (max plausible
        variance ≈ 4 for fully-spread scores).
        """
        scores = [s.effective_score for s in deliberation.gate_scores.values()]
        if not scores:
            return 0.0
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        confidence = 1.0 - (variance / 4.0)
        return max(0.0, min(1.0, confidence))


__all__ = ("DEFAULT_CONFIDENCE_THRESHOLD", "LearningLoop")
