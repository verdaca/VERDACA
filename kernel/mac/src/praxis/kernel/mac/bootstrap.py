"""Bootstrap loader — arch §8.1 Option Y + S-Q1 idempotency.

The :class:`BootstrapLoader` writes the 10 gold-standard records into
``experience_entries`` (via the Memory facade) AND into the sidecar
table ``mac_bootstrap_metadata`` at the same logical write boundary.
Stage 3 Memory schema is FROZEN — the sidecar is the MAC-owned
artifact that satisfies SQ-6 without extending Memory.

**S-Q1 idempotency (ratified, v0.3 §8.4):** ``load_gold_standards()``
on second call:
  1. Returns 0 (no rows inserted)
  2. Logs ``mac.bootstrap.already_loaded`` telemetry via
     :class:`MacPathBEmitter`
  3. Does NOT raise

Idempotency check reads from the sidecar's ``is_loaded(tenant_hash)``
flag, NOT from ``experience_entries``. First-call semantics insert
into both.

Binding anchors:
  - mac/architecture.md §8.1 Option Y Ratification
  - mac/architecture.md §8.2 Bootstrap Records (10 gold standards)
  - mac/test-strategy.md v0.3 §8.4 MAC-T-BOOT-IDEMPOTENT-01..04 (S-Q1)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from praxis.kernel.mac.integrations.memory import MacMemoryAdapter
from praxis.kernel.mac.integrations.runtime import MacPathBEmitter
from praxis.kernel.mac.migrations.mac_bootstrap_metadata_0001 import (
    BootstrapMetadataStore,
)


@dataclass(frozen=True)
class GoldStandardRecord:
    """One gold-standard task outcome from benchmark §2 + §5 + §8.

    Step 6 ships a structurally-correct stub set; Stage 7 POV Harness
    populates the real content from
    ``scripts/build_bootstrap_corpus.py`` reading benchmark-questions.md
    §2 / §5 / §8.
    """

    benchmark_question_id: str  # "Q1".."Q10"
    task_signature_data: dict[str, Any]
    approach_summary: str
    quality_score: float = 4.2
    quality_confidence: float = 0.85
    calibration_anchor_score: float = 4.2


def default_gold_standard_corpus() -> list[GoldStandardRecord]:
    """Return the canonical 10-record gold standard corpus.

    Per benchmark-questions.md §8 OQ-6 Memory Bootstrap Plan: 10
    task signatures (Q1..Q10) seed the initial Memory corpus before
    the first real user task. Each record carries ``quality_score=4.2``
    and ``calibration_anchor_score=4.2`` (representative of a
    score-4 performance per §6 step 5 composite math).
    """
    signatures = (
        ("Q1", "pricing-model-change", "SaaS", "revenue-model-migration"),
        ("Q2", "capital-allocation", "runway", "raise-vs-extend"),
        ("Q3", "make-vs-buy", "capability-gap", "integration-risk"),
        ("Q4", "strategic-alliance", "exclusivity", "optionality-cost"),
        ("Q5", "defensibility", "commoditization-threat", "moat-building"),
        ("Q6", "competitive-pricing", "race-to-bottom", "differentiation"),
        ("Q7", "geographic-expansion", "readiness", "entity-specific-risk"),
        ("Q8", "platform-commoditization", "next-layer", "existential"),
        ("Q9", "gtm-model", "enterprise-vs-smb", "runway-constraint"),
        ("Q10", "diverging-metrics", "hypothesis-generation", "root-cause"),
    )
    return [
        GoldStandardRecord(
            benchmark_question_id=q_id,
            task_signature_data={
                "task_type": "strategic_advisory",
                "domain": domain,
                "decision_class": klass,
                "complication": complication,
            },
            approach_summary=(
                f"Gold-standard analytical approach for {q_id}: "
                f"{domain} / {klass} / {complication}."
            ),
        )
        for q_id, domain, klass, complication in signatures
    ]


class BootstrapLoader:
    """One-shot loader of the 10 gold-standard records into Memory + sidecar.

    Constructor takes the Memory adapter + sidecar store + the
    canonical gold-standard corpus. The :meth:`load_gold_standards`
    method is idempotent per S-Q1 ratified semantics.
    """

    BOOTSTRAP_ALREADY_LOADED_EVENT: str = "mac.bootstrap.already_loaded"
    """Telemetry event emitted on the second-call path per S-Q1
    bake-in. Test-strategy v0.3 §8.4 references this event name
    verbatim."""

    def __init__(
        self,
        *,
        memory_adapter: MacMemoryAdapter,
        metadata_store: BootstrapMetadataStore,
        gold_standards: list[GoldStandardRecord] | None = None,
    ) -> None:
        self._memory = memory_adapter
        self._sidecar = metadata_store
        self._corpus: list[GoldStandardRecord] = (
            gold_standards if gold_standards is not None else default_gold_standard_corpus()
        )

    @property
    def corpus(self) -> list[GoldStandardRecord]:
        return list(self._corpus)

    async def load_gold_standards(
        self,
        *,
        tenant_id: str,
        tenant_hash: str | None = None,
        path_b_emitter: MacPathBEmitter | None = None,
    ) -> int:
        """Load the gold-standard corpus into Memory + sidecar.

        Returns the number of records inserted. **Idempotent per S-Q1:**
        on second call, returns 0, emits
        ``mac.bootstrap.already_loaded`` (if emitter provided), does
        NOT raise.

        ``tenant_hash`` defaults to ``tenant_id`` if not provided —
        the real implementation derives a stable hash from the tenant
        ID via Memory's hashing convention; the step 6 fake just
        reuses the ID.
        """
        effective_tenant_hash = tenant_hash or tenant_id

        # S-Q1 idempotency check — reads from sidecar, NOT experience_entries.
        if self._sidecar.is_loaded(effective_tenant_hash):
            if path_b_emitter is not None:
                await path_b_emitter.emit(
                    cycle_id="bootstrap",
                    event_type=self.BOOTSTRAP_ALREADY_LOADED_EVENT,
                    payload={
                        "tenant_hash": effective_tenant_hash,
                        "corpus_size": len(self._corpus),
                    },
                )
            return 0

        # First call: write to Memory facade + sidecar at same logical boundary.
        inserted = 0
        for record in self._corpus:
            entry_id = await self._memory.publish_outcome(
                tenant_id=tenant_id,
                task_signature=record.task_signature_data,
                outcome={
                    "approach_summary": record.approach_summary,
                    "quality_score": record.quality_score,
                    "quality_confidence": record.quality_confidence,
                },
            )
            self._sidecar.insert(
                experience_entry_id=entry_id,
                tenant_hash=effective_tenant_hash,
                source="benchmark_gold_standard",
                benchmark_question_id=record.benchmark_question_id,
                calibration_anchor_score=record.calibration_anchor_score,
            )
            inserted += 1

        self._sidecar.mark_loaded(effective_tenant_hash)
        return inserted


__all__ = (
    "BootstrapLoader",
    "GoldStandardRecord",
    "default_gold_standard_corpus",
)
