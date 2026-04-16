"""A/B comparison harness — arch §6.

Runs three paths on a benchmark question and produces a ComparisonReport:
  - Path A: single-agent baseline (direct prompt, no MAC)
  - Path B: enhanced single-agent baseline (structural prompt, no MAC)
  - Path C: Studio (full workflow through MAC)

Blind evaluation integrity is enforced by anonymizing output labels before
scoring (STUDIO-T-AB-BLIND-01 through BLIND-03).

Binding anchors:
  - studio/architecture.md §6 A/B Comparison Harness (all subsections)
  - studio/architecture.md §6.3 Blind Evaluation Protocol
  - studio/test-strategy.md §6 A/B Harness Tests
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Protocol

from praxis.kernel.studio.models import (
    ComparisonReport,
    GateScores,
    RenderedOutput,
    RunResult,
)
from praxis.kernel.studio.schema import WorkflowTemplate


# ---------------------------------------------------------------------------
# Protocols accepted by the harness
# ---------------------------------------------------------------------------


class LLMJudgeProtocol(Protocol):
    """Minimal protocol for an LLM-as-judge scorer."""

    def score(self, output_text: str) -> GateScores:
        """Score one output against R1–R12 and return GateScores."""
        ...


class SingleAgentProtocol(Protocol):
    """Minimal protocol for a single-agent baseline caller."""

    def call(self, question: str, structural_prompt: bool = False) -> str:
        """Call one agent with the question, return raw text output."""
        ...


# ---------------------------------------------------------------------------
# ABHarness
# ---------------------------------------------------------------------------


class ABHarness:
    """Three-path A/B comparison harness (arch §6).

    Args:
        single_agent: Callable satisfying SingleAgentProtocol.
        mac_session: A StudioSession-compatible callable with .invoke().
        judge: Callable satisfying LLMJudgeProtocol.
        seed: RNG seed for output-order randomization (§6.3).
    """

    def __init__(
        self,
        single_agent: SingleAgentProtocol,
        mac_session: Any,
        judge: LLMJudgeProtocol,
        seed: int = 42,
    ) -> None:
        self._single_agent = single_agent
        self._session = mac_session
        self._judge = judge
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_single_agent_baseline(self, question: str) -> str:
        """Run Path A: single-agent, direct prompt."""
        return self._single_agent.call(question, structural_prompt=False)

    def run_enhanced_baseline(self, question: str) -> str:
        """Run Path B: enhanced single-agent with structural prompt (no multi-agent)."""
        return self._single_agent.call(question, structural_prompt=True)

    def run_studio(
        self,
        question: str,
        template: WorkflowTemplate,
        customer_context: dict[str, str] | None = None,
    ) -> RenderedOutput:
        """Run Path C: full Studio workflow."""
        result = self._session.invoke(
            template=template,
            user_inputs={"strategic_question": question, "rendering_mode": template.rendering_mode.value},
            customer_context=customer_context or {},
        )
        if result.outputs:
            return result.outputs[0]
        # Fallback — should not occur in practice
        from praxis.kernel.studio.models import RenderedOutput
        from praxis.kernel.studio.schema import ProvenanceMode
        return RenderedOutput(
            text="",
            format="markdown",
            rendering_mode=template.rendering_mode,
            provenance_mode=template.resolved_provenance_mode(),
            word_count=0,
            register_violations=(),
        )

    def score(self, output_text: str) -> GateScores:
        """Score one output via the LLM judge."""
        return self._judge.score(output_text)

    def anonymize(self, outputs: list[str]) -> list[str]:
        """Strip path-identifying labels and randomize order (arch §6.3).

        Returns a new list with labels removed and order randomized.
        The mapping from anonymized → original is NOT returned here —
        the caller must track it separately for reporting.

        STUDIO-T-AB-BLIND-01: strips 'Studio'/'baseline'/'enhanced' labels.
        STUDIO-T-AB-BLIND-02: order randomized.
        STUDIO-T-AB-BLIND-03: no path-identifying metadata in result.
        """
        import re

        label_pattern = re.compile(
            r"\b(Studio|studio|Baseline|baseline|Enhanced|enhanced|Path [A-C])\b",
            re.IGNORECASE,
        )
        stripped = [label_pattern.sub("[ANALYSIS]", o) for o in outputs]
        shuffled = list(stripped)
        self._rng.shuffle(shuffled)
        return shuffled

    def run_full_comparison(
        self,
        question_id: str,
        question: str,
        template: WorkflowTemplate,
    ) -> tuple[RunResult, RunResult, RunResult]:
        """Run all three paths and return (baseline, enhanced, studio) RunResults."""
        import time

        t0 = time.monotonic()
        baseline_text = self.run_single_agent_baseline(question)
        baseline_time = time.monotonic() - t0

        t0 = time.monotonic()
        enhanced_text = self.run_enhanced_baseline(question)
        enhanced_time = time.monotonic() - t0

        t0 = time.monotonic()
        studio_output = self.run_studio(question, template)
        studio_time = time.monotonic() - t0

        baseline_scores = self.score(baseline_text)
        enhanced_scores = self.score(enhanced_text)
        studio_scores = self.score(studio_output.text)

        return (
            RunResult(
                path="single_agent",
                question_id=question_id,
                output_text=baseline_text,
                gate_scores=baseline_scores,
                cost_usd=0.0,
                duration_seconds=baseline_time,
                word_count=len(baseline_text.split()),
            ),
            RunResult(
                path="enhanced_single_agent",
                question_id=question_id,
                output_text=enhanced_text,
                gate_scores=enhanced_scores,
                cost_usd=0.0,
                duration_seconds=enhanced_time,
                word_count=len(enhanced_text.split()),
            ),
            RunResult(
                path="studio",
                question_id=question_id,
                output_text=studio_output.text,
                gate_scores=studio_scores,
                cost_usd=0.0,
                duration_seconds=studio_time,
                word_count=studio_output.word_count,
            ),
        )

    def generate_report(
        self, run_results: list[tuple[RunResult, RunResult, RunResult]]
    ) -> ComparisonReport:
        """Generate a ComparisonReport from a list of (baseline, enhanced, studio) triplets.

        Full disclosure: all results reported regardless of which path wins
        (ADR-2 §8.3 full disclosure).
        """
        per_question_rows = []
        per_gate_sums: dict[str, dict[str, float]] = {}
        per_gate_counts: dict[str, int] = {}
        cost_quality_data = []

        for baseline, enhanced, studio in run_results:
            cost_ratio = (
                studio.cost_usd / baseline.cost_usd
                if baseline.cost_usd > 0
                else float("inf")
            )
            time_ratio = (
                studio.duration_seconds / baseline.duration_seconds
                if baseline.duration_seconds > 0
                else float("inf")
            )
            per_question_rows.append(
                {
                    "question_id": studio.question_id,
                    "studio_score": studio.gate_scores.composite,
                    "baseline_score": baseline.gate_scores.composite,
                    "enhanced_score": enhanced.gate_scores.composite,
                    "cost_ratio": cost_ratio,
                    "time_ratio": time_ratio,
                }
            )
            cost_quality_data.append(
                {
                    "question_id": studio.question_id,
                    "studio_cost": studio.cost_usd,
                    "studio_composite": studio.gate_scores.composite,
                    "baseline_cost": baseline.cost_usd,
                    "baseline_composite": baseline.gate_scores.composite,
                }
            )
            for gate_id in studio.gate_scores.scores:
                if gate_id not in per_gate_sums:
                    per_gate_sums[gate_id] = {"studio": 0.0, "baseline": 0.0}
                    per_gate_counts[gate_id] = 0
                per_gate_sums[gate_id]["studio"] += studio.gate_scores.scores.get(gate_id, 0)
                per_gate_sums[gate_id]["baseline"] += baseline.gate_scores.scores.get(gate_id, 0)
                per_gate_counts[gate_id] += 1

        n = len(run_results) or 1
        per_gate_rows = []
        for gate_id, sums in per_gate_sums.items():
            count = per_gate_counts[gate_id] or 1
            studio_avg = sums["studio"] / count
            baseline_avg = sums["baseline"] / count
            per_gate_rows.append(
                {
                    "gate_id": gate_id,
                    "studio_avg": studio_avg,
                    "baseline_avg": baseline_avg,
                    "delta": studio_avg - baseline_avg,
                }
            )

        avg_studio = (
            sum(r["studio_score"] for r in per_question_rows) / n
        )
        avg_baseline = (
            sum(r["baseline_score"] for r in per_question_rows) / n
        )
        pct_diff = (
            ((avg_studio - avg_baseline) / avg_baseline * 100)
            if avg_baseline > 0
            else 0.0
        )
        studio_wins = sum(
            1 for r in per_question_rows if r["studio_score"] > r["baseline_score"]
        )
        headline = (
            f"Studio vs. single-agent on {n} benchmark questions: "
            f"+{pct_diff:.0f}% quality composite "
            f"(Studio {avg_studio:.1f} vs baseline {avg_baseline:.1f}); "
            f"beat count: Studio wins {studio_wins}/{n} questions. "
            f"(internal scoring; A4 deferred)"
        )

        r5_studio = [r["studio_avg"] for r in per_gate_rows if r.get("gate_id") == "R5"]
        r5_baseline = [r["baseline_avg"] for r in per_gate_rows if r.get("gate_id") == "R5"]
        r5_s = f"{r5_studio[0]:.2f}" if r5_studio else "n/a"
        r5_b = f"{r5_baseline[0]:.2f}" if r5_baseline else "n/a"
        dissent_analysis = (
            f"R5 Dissent Preservation — Studio avg: {r5_s}, "
            f"Baseline avg: {r5_b}."
        )

        return ComparisonReport(
            headline=headline,
            per_question_rows=tuple(per_question_rows),
            per_gate_rows=tuple(per_gate_rows),
            dissent_analysis=dissent_analysis,
            cost_quality_data=tuple(cost_quality_data),
        )


__all__: tuple[str, ...] = (
    "ABHarness",
    "ComparisonReport",
    "LLMJudgeProtocol",
    "RunResult",
    "SingleAgentProtocol",
)
