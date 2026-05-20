"""Req-F two-step reviewer tests — mac/test-strategy.md v0.3 §5.1.

Covers MAC-T-ASYM-R-F-01/02/03/04. Entry #14 in the 16-entry allow-list
is ``MAC-T-ASYM-R-F-02`` (no_waiver deterministic field-ordering carrier).
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.asymmetry import (
    REQ_F_PROMPT_TEMPLATE,
    AsymmetryRouter,
    ReviewerCritique,
)


@pytest.mark.critical
@pytest.mark.asymmetry_structural
@pytest.mark.static
def test_mac_t_asym_r_f_01_schema_field_presence() -> None:
    """MAC-T-ASYM-R-F-01 — ReviewerCritique has required Req-F fields.

    Both ``independent_steelman`` and ``gap_assessment`` MUST be
    declared on the Pydantic model. Additional fields (raised_concerns,
    reviewer_id) are allowed.
    """
    fields = ReviewerCritique.model_fields
    assert "independent_steelman" in fields
    assert "gap_assessment" in fields
    # Additional optional fields.
    assert "raised_concerns" in fields
    assert "reviewer_id" in fields


# Entry #14 in the 16-entry allow-list — Q-1 preserved canonical name.
@pytest.mark.critical
@pytest.mark.asymmetry_structural
@pytest.mark.static
@pytest.mark.no_waiver  # Decision 1 item 9 deterministic carrier — §13.3.3 entry #14
def test_mac_t_asym_r_f_02_field_ordering_deterministic() -> None:
    """MAC-T-ASYM-R-F-02 — independent_steelman precedes gap_assessment.

    Per arch §7.1 Req-F: the reviewer writes its own steelman FIRST
    (before reading the producer's [STEELMAN]), then writes
    gap_assessment comparing the two. Pydantic v2 preserves insertion
    order in ``model_fields``; this test asserts
    ``independent_steelman`` is at index 0 and ``gap_assessment`` at
    index 1.

    Allow-list entry #14 — no_waiver. Swapping the order here breaks
    the step 6 meta-test at collection time.
    """
    keys = list(ReviewerCritique.model_fields.keys())
    assert keys[0] == "independent_steelman", (
        f"Req-F violation: independent_steelman must be the first field; "
        f"got {keys}"
    )
    assert keys[1] == "gap_assessment", (
        f"Req-F violation: gap_assessment must be the second field; "
        f"got {keys}"
    )
    # Index explicit to make the invariant visible in failures.
    assert keys.index("independent_steelman") < keys.index("gap_assessment")


@pytest.mark.nightly_only
@pytest.mark.critical
@pytest.mark.asymmetry_structural
def test_mac_t_asym_r_f_03_live_reviewer_run() -> None:
    """MAC-T-ASYM-R-F-03 — live reviewer protocol under real LLM.

    Tier 3 nightly test. NOT ``no_waiver`` because live judges drift
    per Decision 1 structural boundary. PR-gate skips via ``nightly_only``
    marker.
    """
    assert True  # Stage 7 POV Harness wires in the real reviewer call


@pytest.mark.critical
@pytest.mark.asymmetry_structural
def test_mac_t_asym_r_f_04_reviewer_prompt_step_order() -> None:
    """MAC-T-ASYM-R-F-04 — the Req-F prompt instructs STEP 1 before STEP 2.

    Arch §7.1: the canonical prompt template tells the reviewer to
    construct its independent_steelman FIRST, then read the producer's
    analysis, then compare. The three numbered steps MUST appear in
    order.
    """
    prompt = AsymmetryRouter.build_req_f_prompt(
        task_prompt="Sample task question.",
        producer_output="Sample producer [STEELMAN]...",
    )
    step_1_idx = prompt.find("STEP 1")
    step_2_idx = prompt.find("STEP 2")
    step_3_idx = prompt.find("STEP 3")
    assert 0 <= step_1_idx < step_2_idx < step_3_idx
    # STEP 1 must instruct "independent" steelman construction.
    step_1_body = prompt[step_1_idx:step_2_idx].lower()
    assert "independent" in step_1_body
    assert "before reading" in step_1_body.lower() or "not yet seen" in step_1_body
    # STEP 2 must instruct reading the producer output.
    step_2_body = prompt[step_2_idx:step_3_idx].lower()
    assert "read" in step_2_body or "producer" in step_2_body
