"""Information Asymmetry Router — arch §7.

The asymmetry router is the load-bearing primitive for MAC's R4/R5
structural advantage over single-agent baselines. It exposes two
cross-cutting invariants:

  1. **Req-F two-step reviewer protocol (arch §7.1):** the reviewer
     constructs its ``independent_steelman`` FIRST, BEFORE reading the
     producer's own ``[STEELMAN]`` section. Only after committing to
     an independent steelman does the reviewer read the producer's
     section and perform a ``gap_assessment``. Field ordering on
     :class:`ReviewerCritique` is load-bearing — Pydantic v2 preserves
     insertion order, and step 6's :data:`NO_WAIVER_ALLOWLIST` entry
     #14 (``MAC-T-ASYM-R-F-02``) greps ``list(model_fields)`` and
     asserts ``independent_steelman`` precedes ``gap_assessment``.

  2. **Proxy construction via ``_construct_memory_proxy`` only (arch
     §7.2):** MAC never directly imports
     ``ProducerMemoryProxy``/``ReviewerMemoryProxy`` from
     ``praxis.kernel.runtime.spawner``. Spawns route through
     :class:`MacRuntimeAdapter` (step 3) which dispatches via
     :class:`AgentRole`. The grep test in
     ``tests/mac/negative/test_pinning.py::test_no_direct_memory_proxy_imports_in_mac``
     (step 3 coverage-floor) enforces this at PR-gate time.

The :class:`AsymmetryRouter` is a thin composition layer above
:class:`MacRuntimeAdapter`. It does NOT re-implement proxy construction
or bus filtering — those are Runtime's responsibilities per arch §7.5
and §9.0 "the punchline" (``AttributeError`` at the Python interpreter
level when a reviewer calls ``retrieve_similar_tasks``).

Binding anchors:
  - mac/architecture.md §7.1 Req-F Reviewer Elicitation Subsection
  - mac/architecture.md §7.2 Binding to Runtime §4.1 Proxies
  - mac/architecture.md §7.3 Information Hiding
  - mac/architecture.md §7.4 Aggregating Multiple Reviewers
  - mac/architecture.md §7.5 The Symmetric Asymmetry Boundary
  - runtime/architecture.md §4.1.5 ``_construct_memory_proxy`` single-point
  - runtime/architecture.md §7.5 Layer 2 communication-bus filtering
  - runtime/architecture.md §9.0 "the punchline" (AttributeError)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from praxis.kernel.mac.budget import DEFAULT_MAC_BUDGET, ResourceBudget
from praxis.kernel.mac.integrations.runtime import (
    AgentRole,
    MacRuntimeAdapter,
)


# =============================================================================
# ReviewerCritique — Req-F load-bearing field ordering (arch §7.1)
# =============================================================================
#
# **CRITICAL: field ordering is load-bearing per arch §7.1 Req-F.**
#
# Pydantic v2 preserves insertion order in ``model_fields``. The allow-list
# entry #14 ``MAC-T-ASYM-R-F-02`` (no_waiver deterministic) asserts:
#
#     keys = list(ReviewerCritique.model_fields.keys())
#     assert keys[0] == "independent_steelman"
#     assert keys[1] == "gap_assessment"
#
# This enforces the two-step protocol at the type level:
#   STEP 1 — Reviewer writes independent_steelman (no access to producer's
#            [STEELMAN] section).
#   STEP 2 — Reviewer reads producer's [STEELMAN].
#   STEP 3 — Reviewer writes gap_assessment comparing the two.
#
# If someone swaps the field order, the allow-list meta-test at step 6
# fails at collection time and the PR gate blocks.
# =============================================================================


class ReviewerCritique(BaseModel):
    """Req-F two-step reviewer output (arch §7.1).

    Pydantic v2 frozen model with LOAD-BEARING field ordering per arch
    §7.1. The ``independent_steelman`` field MUST precede
    ``gap_assessment`` so the reviewer commits to its own steelman
    BEFORE reading the producer's ``[STEELMAN]`` section.

    Additional fields (``raised_concerns``, ``reviewer_id``) follow
    the two Req-F fields in document order but do not affect the Req-F
    invariant.
    """

    model_config = ConfigDict(frozen=True)

    # ================================================================
    # LOAD-BEARING: do NOT reorder. Allow-list entry #14 enforces.
    # ================================================================
    independent_steelman: str
    """STEP 1 — Reviewer's independently-constructed strongest counter
    to the main recommendation. Written BEFORE reading the producer's
    ``[STEELMAN]`` section. Minimum length implied by arch §7.1
    guidance ("≥150 words")."""

    gap_assessment: str
    """STEP 3 — Reviewer's comparison of the independent steelman to
    the producer's ``[STEELMAN]`` section. What did the reviewer's
    version include that the producer missed, and vice versa."""
    # ================================================================

    raised_concerns: tuple[str, ...] = Field(default_factory=tuple)
    """Additional concerns the reviewer raises beyond the Req-F
    two-step. Order-preserving tuple so telemetry can replay."""

    reviewer_id: str = ""
    """Identifier for this reviewer instance. Used by
    :meth:`AsymmetryRouter.aggregate_critiques` to key outputs by
    reviewer index in multi-reviewer Cycle 2 runs."""


# =============================================================================
# Req-F prompt template (arch §7.1 canonical fragment)
# =============================================================================


REQ_F_PROMPT_TEMPLATE: str = """\
You are a reviewer agent. Your job is to evaluate the strength of the
producer's steelman counterarguments.

STEP 1 — Independent Steelman Construction (REQUIRED FIRST):
Before reading the analysis, what is the strongest counterargument to
the main recommendation? The task is:

{task_prompt}

You have NOT yet seen the producer's analysis. Construct your
independent steelman now. Your steelman should be the version of the
opposing position that a knowledgeable holder of that view would
recognize as their best argument — not a strawman.

Write your independent steelman below (>=150 words):
[REVIEWER WRITES independent_steelman HERE]

STEP 2 — Read the producer's analysis output:
{producer_output}

STEP 3 — Compare:
- What did your independent steelman include that the analysis's
  [STEELMAN] section missed?
- What did the analysis's [STEELMAN] section include that you did not?
- Is the gap material to the recommendation?

Write your gap_assessment below.
"""


# =============================================================================
# AsymmetryRouter — thin composition layer over MacRuntimeAdapter
# =============================================================================


class AsymmetryRouter:
    """Composes :class:`MacRuntimeAdapter` into the Req-F asymmetry pipeline.

    **What this class does:**
      - Spawns producers via ``MacRuntimeAdapter.spawn_producer`` (AgentRole.PRODUCER).
      - Spawns reviewer pools via ``MacRuntimeAdapter.spawn_reviewer`` (AgentRole.REVIEWER).
      - Renders the Req-F two-step prompt from :data:`REQ_F_PROMPT_TEMPLATE`.
      - Aggregates multiple :class:`ReviewerCritique` outputs per arch §7.4
        (R4 raw = MAX across reviewers).

    **What this class does NOT do:**
      - Directly construct :class:`ProducerMemoryProxy` or
        :class:`ReviewerMemoryProxy`. Those come from Runtime's
        ``_construct_memory_proxy`` inside the Spawner, NEVER from MAC
        (arch §7.2 + runtime §4.1.5).
      - Apply Layer 2 bus filtering. That's Runtime's
        :class:`MemoryProxy`'s responsibility (runtime §7.5). MAC
        composes the proxies but does not filter events.
      - Re-implement the ``retrieve_similar_tasks`` AttributeError
        guarantee on reviewer proxies. That is Runtime's "punchline"
        at §9.0 — MAC inherits the Python-interpreter-level
        enforcement without any MAC-side check.
    """

    def __init__(self, runtime_adapter: MacRuntimeAdapter) -> None:
        self._runtime = runtime_adapter

    async def spawn_producer(
        self, *, agent_id: str, budget: ResourceBudget | None = None
    ) -> Any:
        """Spawn a producer agent via :class:`AgentRole.PRODUCER`."""
        return await self._runtime.spawn_producer(
            agent_id=agent_id,
            budget=budget or DEFAULT_MAC_BUDGET,
        )

    async def spawn_reviewer_pool(
        self,
        *,
        count: int,
        agent_id_prefix: str = "mac-reviewer",
        budget: ResourceBudget | None = None,
    ) -> list[Any]:
        """Spawn ``count`` reviewer agents via :class:`AgentRole.REVIEWER`.

        Count is capped at 3 per arch §4.3 (same cap the Plan
        Decomposer enforces on ``reviewer_count`` fields). Step 5 does
        not silently reduce — invalid counts raise.
        """
        if count < 1 or count > 3:
            raise ValueError(
                f"reviewer_count must be in [1, 3] per arch §4.3; got {count}"
            )
        budget = budget or DEFAULT_MAC_BUDGET
        handles: list[Any] = []
        for i in range(count):
            handle = await self._runtime.spawn_reviewer(
                agent_id=f"{agent_id_prefix}-{i}",
                budget=budget,
            )
            handles.append(handle)
        return handles

    @staticmethod
    def build_req_f_prompt(*, task_prompt: str, producer_output: str) -> str:
        """Render the canonical Req-F two-step prompt for a reviewer.

        The prompt format is arch §7.1 verbatim — any edit is a Stage 5
        architecture revision, not a fix-the-test hotpatch. The
        returned string instructs the reviewer to write
        ``independent_steelman`` first (STEP 1), then read the producer
        output (STEP 2), then write ``gap_assessment`` (STEP 3).
        """
        return REQ_F_PROMPT_TEMPLATE.format(
            task_prompt=task_prompt,
            producer_output=producer_output,
        )

    @staticmethod
    def aggregate_critiques(
        critiques: list[ReviewerCritique],
    ) -> dict[str, Any]:
        """Aggregate N reviewer critiques per arch §7.4.

        For R4 (Steelman Completeness) and R5 (Dissent Preservation),
        the Quality Gate Engine takes the **MAX** across reviewers —
        if any reviewer's independent steelman matches the producer's,
        R4 scores high; if all reviewers found gaps, R4 scores low.

        Step 5 returns the structural aggregation shape (list of
        (reviewer_id, critique) pairs + concatenated concerns). Step 6
        wires this into :func:`compute_final_scores` as the
        ``reviewer_critique`` kwarg.
        """
        if not critiques:
            return {
                "reviewer_count": 0,
                "critiques": [],
                "all_raised_concerns": (),
                "manufactured_dissent_detected": False,
            }

        all_concerns: list[str] = []
        for critique in critiques:
            all_concerns.extend(critique.raised_concerns)

        return {
            "reviewer_count": len(critiques),
            "critiques": [
                {
                    "reviewer_id": c.reviewer_id,
                    "independent_steelman": c.independent_steelman,
                    "gap_assessment": c.gap_assessment,
                }
                for c in critiques
            ],
            "all_raised_concerns": tuple(all_concerns),
            # Step 5 does not yet compute this — step 6 will fold in
            # the real R5 manufactured-dissent detection from the task
            # context. The key is always present so compute_final_scores
            # can read it safely.
            "manufactured_dissent_detected": False,
        }


__all__ = (
    "REQ_F_PROMPT_TEMPLATE",
    "AgentRole",
    "AsymmetryRouter",
    "ReviewerCritique",
)
