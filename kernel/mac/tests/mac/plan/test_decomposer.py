"""Coverage-floor tests for the Plan Decomposer (arch §4).

Per Stage 5.3 preload Q3 disposition (2026-04-14): v0.3 test-strategy has no
explicit ``MAC-T-PLAN-*`` catalog family, so these tests satisfy the ≥90%
coverage floor on ``plan.py`` without MAC-T IDs, without ``no_waiver``
markers, and without additions to the 16-entry ``NO_WAIVER_ALLOWLIST``.
Quinn 5.4 QA will decide whether to formally catalog them.

Anchors:
  - mac/architecture.md §4.1 Plan Decomposer Purpose
  - mac/architecture.md §4.2 PhaseDAG Structure
  - mac/architecture.md §4.3 Default DAG (cycle1 → cycle2 → cycle3 → publish)
  - mac/architecture.md §4.4 Validation and Repair
  - mac/architecture.md §4.5 Why a DAG
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.plan import (
    PhaseDAG,
    PhaseNode,
    PlanDecomposer,
    PlanRepairFailedError,
)
from praxis.kernel.mac.task import DomainClass, OutputFormatContract, TaskSignature


def _build_signature(task_type: str = "strategic_advisory_uncategorized") -> TaskSignature:
    return TaskSignature(
        task_type=task_type,
        input_hash="a" * 64,
        agents_involved=(),
        context_fingerprint="b" * 64,
    )


def _default_contract() -> OutputFormatContract:
    return OutputFormatContract(domain_guards_active=())


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_default_dag_is_linear_cycle_1_2_3_publish() -> None:
    """Arch §4.3: the default DAG is linear:
    ``cycle1_produce → cycle2_review → cycle3_gate → publish``.

    Reviewer count defaults to 2 for ``DomainClass.CONTESTED`` per arch §4.3
    ("two independent reviewers — gives the gate engine richer critique
    signal for R4/R5") and 1 for all other domain classes.
    """
    decomposer = PlanDecomposer()
    dag = decomposer.decompose(
        signature=_build_signature(),
        domain_class=DomainClass.CONTESTED,
        output_contract=_default_contract(),
    )

    # Topological order matches the arch §4.3 chain.
    order = dag.topological_order()
    assert order == (
        "cycle1_produce",
        "cycle2_review",
        "cycle3_gate",
        "publish",
    )

    # Phase kinds match arch §4.2 definitions.
    by_id = {node.phase_id: node for node in dag.nodes}
    assert by_id["cycle1_produce"].phase_kind == "produce"
    assert by_id["cycle2_review"].phase_kind == "review_parallel"
    assert by_id["cycle3_gate"].phase_kind == "gate_evaluate"
    assert by_id["publish"].phase_kind == "publish"

    # CONTESTED → reviewer_count = 2 per arch §4.3.
    assert by_id["cycle2_review"].reviewer_count == 2

    # Non-CONTESTED → reviewer_count = 1.
    dag_consensus = decomposer.decompose(
        signature=_build_signature(),
        domain_class=DomainClass.CONSENSUS,
        output_contract=_default_contract(),
    )
    by_id_c = {n.phase_id: n for n in dag_consensus.nodes}
    assert by_id_c["cycle2_review"].reviewer_count == 1


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_dag_validate_acyclic_rejects_cycles() -> None:
    """Arch §4.4 rule 5: ``validate_acyclic`` rejects DAGs whose edge set
    forms a cycle. Constructing such a DAG and calling ``validate()`` must
    raise (exact exception type is ``ValueError`` or subclass; callers
    don't care which as long as it's not silently accepted)."""
    n_a = PhaseNode(
        phase_id="a",
        phase_kind="produce",
        depends_on=("c",),
        timeout_seconds=10.0,
    )
    n_b = PhaseNode(
        phase_id="b",
        phase_kind="review_parallel",
        depends_on=("a",),
        timeout_seconds=10.0,
        reviewer_count=1,
    )
    n_c = PhaseNode(
        phase_id="c",
        phase_kind="gate_evaluate",
        depends_on=("b",),
        timeout_seconds=10.0,
    )
    n_publish = PhaseNode(
        phase_id="publish",
        phase_kind="publish",
        depends_on=("c",),
        timeout_seconds=10.0,
    )
    dag = PhaseDAG(
        nodes=(n_a, n_b, n_c, n_publish),
        edges=(
            ("a", "b"),
            ("b", "c"),
            ("c", "a"),  # cycle edge
            ("c", "publish"),
        ),
    )
    with pytest.raises(ValueError, match="cycle"):
        dag.validate_acyclic()


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_dag_validate_terminal_publish_requires_exactly_one() -> None:
    """Arch §4.4 rule 4 + ``PhaseDAG.validate_terminal_publish`` docstring:
    exactly one publish node with no successors. Zero publish terminals OR
    two publish terminals must fail validation.
    """
    produce = PhaseNode(
        phase_id="cycle1_produce",
        phase_kind="produce",
        depends_on=(),
        timeout_seconds=10.0,
    )
    review = PhaseNode(
        phase_id="cycle2_review",
        phase_kind="review_parallel",
        depends_on=("cycle1_produce",),
        reviewer_count=1,
        timeout_seconds=10.0,
    )
    gate = PhaseNode(
        phase_id="cycle3_gate",
        phase_kind="gate_evaluate",
        depends_on=("cycle2_review",),
        timeout_seconds=10.0,
    )

    # Zero publish terminals → invalid.
    dag_zero = PhaseDAG(
        nodes=(produce, review, gate),
        edges=(
            ("cycle1_produce", "cycle2_review"),
            ("cycle2_review", "cycle3_gate"),
        ),
    )
    with pytest.raises(ValueError, match="publish"):
        dag_zero.validate_terminal_publish()

    # Two publish terminals → invalid.
    pub_a = PhaseNode(
        phase_id="publish_a",
        phase_kind="publish",
        depends_on=("cycle3_gate",),
        timeout_seconds=10.0,
    )
    pub_b = PhaseNode(
        phase_id="publish_b",
        phase_kind="publish",
        depends_on=("cycle3_gate",),
        timeout_seconds=10.0,
    )
    dag_two = PhaseDAG(
        nodes=(produce, review, gate, pub_a, pub_b),
        edges=(
            ("cycle1_produce", "cycle2_review"),
            ("cycle2_review", "cycle3_gate"),
            ("cycle3_gate", "publish_a"),
            ("cycle3_gate", "publish_b"),
        ),
    )
    with pytest.raises(ValueError, match="publish"):
        dag_two.validate_terminal_publish()


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_dag_repair_adds_missing_publish_once_then_raises() -> None:
    """Arch §4.4 single-pass repair: the Decomposer attempts exactly one
    repair (add missing publish, add default cycle3_gate if missing). After
    the single attempt, ``PlanRepairFailedError`` is raised — no loop.

    Paths exercised:
      (a) Missing publish only → repair succeeds, returns a valid DAG with
          an appended ``publish`` node.
      (b) Missing BOTH gate and publish (structurally broken beyond one
          repair pass) → first pass adds publish, second pass would be
          required for the gate, so ``PlanRepairFailedError`` is raised.
    """
    decomposer = PlanDecomposer()

    # (a) Malformed input: no publish node, but gate is present.
    malformed_missing_publish = PhaseDAG(
        nodes=(
            PhaseNode(
                phase_id="cycle1_produce",
                phase_kind="produce",
                depends_on=(),
                timeout_seconds=10.0,
            ),
            PhaseNode(
                phase_id="cycle2_review",
                phase_kind="review_parallel",
                depends_on=("cycle1_produce",),
                reviewer_count=1,
                timeout_seconds=10.0,
            ),
            PhaseNode(
                phase_id="cycle3_gate",
                phase_kind="gate_evaluate",
                depends_on=("cycle2_review",),
                timeout_seconds=10.0,
            ),
        ),
        edges=(
            ("cycle1_produce", "cycle2_review"),
            ("cycle2_review", "cycle3_gate"),
        ),
    )
    repaired = decomposer.repair(malformed_missing_publish)
    assert any(node.phase_kind == "publish" for node in repaired.nodes)
    repaired.validate_acyclic()
    repaired.validate_terminal_publish()

    # (b) Malformed input beyond single-pass repair: missing BOTH gate and
    # publish. The single repair pass adds one, then raises because the
    # next pass is not allowed.
    malformed_missing_both = PhaseDAG(
        nodes=(
            PhaseNode(
                phase_id="cycle1_produce",
                phase_kind="produce",
                depends_on=(),
                timeout_seconds=10.0,
            ),
            PhaseNode(
                phase_id="cycle2_review",
                phase_kind="review_parallel",
                depends_on=("cycle1_produce",),
                reviewer_count=1,
                timeout_seconds=10.0,
            ),
        ),
        edges=(("cycle1_produce", "cycle2_review"),),
    )
    with pytest.raises(PlanRepairFailedError):
        decomposer.repair(malformed_missing_both)


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_dag_repair_is_noop_when_dag_is_already_valid() -> None:
    """Arch §4.4: repair is idempotent for valid DAGs. Calling ``repair``
    on a fully-formed default DAG must return it unchanged (no new nodes,
    no new edges).
    """
    decomposer = PlanDecomposer()
    good = decomposer.decompose(
        signature=_build_signature(),
        domain_class=DomainClass.CONTESTED,
        output_contract=_default_contract(),
    )
    repaired = decomposer.repair(good)
    assert repaired is good or repaired == good
    assert len(repaired.nodes) == len(good.nodes) == 4
    assert len(repaired.edges) == len(good.edges) == 3


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_dag_repair_adds_missing_gate_when_publish_present() -> None:
    """Arch §4.4 repair order: when publish is present but gate_evaluate
    is absent, the single repair pass adds a synthesized ``cycle3_gate``
    anchored on the last review node. Validates that the gate-anchor
    fallback path (``_find_gate_anchor``) is exercised.
    """
    decomposer = PlanDecomposer()

    produce = PhaseNode(
        phase_id="cycle1_produce",
        phase_kind="produce",
        depends_on=(),
        timeout_seconds=10.0,
    )
    review = PhaseNode(
        phase_id="cycle2_review",
        phase_kind="review_parallel",
        depends_on=("cycle1_produce",),
        reviewer_count=1,
        timeout_seconds=10.0,
    )
    publish = PhaseNode(
        phase_id="publish",
        phase_kind="publish",
        # Note: depends_on intentionally skips gate; repair should insert one.
        depends_on=("cycle2_review",),
        timeout_seconds=10.0,
    )
    # Ordering: publish immediately follows review — gate is missing.
    malformed_missing_gate = PhaseDAG(
        nodes=(produce, review, publish),
        edges=(
            ("cycle1_produce", "cycle2_review"),
            ("cycle2_review", "publish"),
        ),
    )

    # This DAG has NO gate_evaluate node — validate() fails rule 3.
    with pytest.raises(ValueError, match="gate_evaluate"):
        malformed_missing_gate.validate()

    # Repair inserts the missing gate between review and publish, rewiring
    # the intermediate edge so rule 6 (path-to-publish) still holds. This
    # is one repair action — add one node, re-route one edge.
    repaired = decomposer.repair(malformed_missing_gate)
    assert any(n.phase_kind == "gate_evaluate" for n in repaired.nodes)
    gate_node = next(n for n in repaired.nodes if n.phase_kind == "gate_evaluate")
    assert "cycle2_review" in gate_node.depends_on

    # The repaired DAG must be fully valid — all 6 arch §4.4 rules.
    repaired.validate()

    # Topological order now runs produce → review → gate → publish.
    assert repaired.topological_order() == (
        "cycle1_produce",
        "cycle2_review",
        "cycle3_gate",
        "publish",
    )


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_dag_validate_rejects_rule_1_rule_2_rule_6_violations() -> None:
    """Arch §4.4 rules 1, 2, 6: exactly one produce node, at least one
    reviewer, every non-publish node has a path to publish. One compact
    test that hits each rule's failure path.
    """
    produce = PhaseNode(
        phase_id="cycle1_produce",
        phase_kind="produce",
        depends_on=(),
        timeout_seconds=10.0,
    )
    review = PhaseNode(
        phase_id="cycle2_review",
        phase_kind="review_parallel",
        depends_on=("cycle1_produce",),
        reviewer_count=1,
        timeout_seconds=10.0,
    )
    gate = PhaseNode(
        phase_id="cycle3_gate",
        phase_kind="gate_evaluate",
        depends_on=("cycle2_review",),
        timeout_seconds=10.0,
    )
    publish = PhaseNode(
        phase_id="publish",
        phase_kind="publish",
        depends_on=("cycle3_gate",),
        timeout_seconds=10.0,
    )

    # Rule 1: zero produce nodes.
    dag_no_produce = PhaseDAG(
        nodes=(review, gate, publish),
        edges=(
            ("cycle2_review", "cycle3_gate"),
            ("cycle3_gate", "publish"),
        ),
    )
    with pytest.raises(ValueError, match="produce node"):
        dag_no_produce.validate()

    # Rule 2: zero review nodes.
    dag_no_review = PhaseDAG(
        nodes=(produce, gate, publish),
        edges=(
            ("cycle1_produce", "cycle3_gate"),
            ("cycle3_gate", "publish"),
        ),
    )
    with pytest.raises(ValueError, match="review_parallel or review_serial"):
        dag_no_review.validate()

    # Rule 6: orphan node — an extra review with no path to publish.
    orphan_review = PhaseNode(
        phase_id="cycle2_review_orphan",
        phase_kind="review_parallel",
        depends_on=(),
        reviewer_count=1,
        timeout_seconds=10.0,
    )
    dag_orphan = PhaseDAG(
        nodes=(produce, review, orphan_review, gate, publish),
        edges=(
            ("cycle1_produce", "cycle2_review"),
            ("cycle2_review", "cycle3_gate"),
            ("cycle3_gate", "publish"),
            # orphan_review is in nodes but has no edges into the chain.
        ),
    )
    with pytest.raises(ValueError, match="path to publish"):
        dag_orphan.validate()
