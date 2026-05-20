"""MAC Plan Decomposer — arch §4.

Deterministic transformation ``(OutputFormatContract, DomainClass,
TaskSignature) → PhaseDAG`` that the §5 Iteration Controller walks.
The default DAG is linear::

    cycle1_produce → cycle2_review → cycle3_gate → publish

with reviewer count derived from :class:`DomainClass` (arch §4.3):

  - ``CONTESTED`` → 2 parallel reviewers (richer critique signal for R4/R5)
  - every other class → 1 reviewer

Workflow templates (Stage 6) may lift this to a cap of 3; the Decomposer
enforces that cap at construction time.

Binding anchors:
  - mac/architecture.md §4.1 Purpose
  - mac/architecture.md §4.2 PhaseDAG Structure
  - mac/architecture.md §4.3 The Default DAG
  - mac/architecture.md §4.4 Validation and Repair
  - mac/architecture.md §4.5 Why a DAG and Not a Single Linear Sequence
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from praxis.kernel.mac.task import DomainClass, OutputFormatContract, TaskSignature


PhaseKind = Literal[
    "produce",
    "review_parallel",
    "review_serial",
    "gate_evaluate",
    "publish",
]
"""The five ratified phase kinds per arch §4.2. A ``PhaseNode`` outside this
set is a type error — Pydantic rejects it at model validation time."""


_MAX_REVIEWER_COUNT: int = 3
"""Arch §4.3 "max 3 reviewers" cap. Lifting this requires a Stage 5
architecture revision; workflow templates cannot override it."""


# =============================================================================
# Exceptions
# =============================================================================


class PlanRepairFailedError(ValueError):
    """Raised when :meth:`PlanDecomposer.repair` cannot restore a malformed
    :class:`PhaseDAG` in a single repair pass (arch §4.4).

    Repair is intentionally capped at one pass — repeated repair indicates a
    malformed template that belongs to Stage 6 Studio template validation,
    not to runtime self-correction here.
    """


# =============================================================================
# PhaseNode — frozen Pydantic model for a single DAG vertex
# =============================================================================


class PhaseNode(BaseModel):
    """A single phase in the 3-cycle plan (arch §4.2).

    Frozen: the Plan Decomposer constructs nodes once and the Iteration
    Controller reads them read-only thereafter. Mutation during cycle
    execution happens on :class:`DeliberationState`, not on the DAG.
    """

    model_config = ConfigDict(frozen=True)

    phase_id: str
    """Unique within a DAG. Canonical IDs for the default DAG are
    ``cycle1_produce``, ``cycle2_review``, ``cycle3_gate``, ``publish``."""

    phase_kind: PhaseKind
    """One of the five ratified arch §4.2 kinds."""

    depends_on: tuple[str, ...] = ()
    """``phase_id`` values that must complete before this node runs. Empty
    tuple means this node is a DAG root."""

    agent_role: str | None = None
    """For produce / review_* phases — the Runtime :class:`AgentRole` name
    passed to ``AgentSpawner.spawn``. None for gate_evaluate / publish."""

    reviewer_count: int = Field(default=1, ge=1, le=_MAX_REVIEWER_COUNT)
    """Only meaningful for ``review_parallel`` / ``review_serial``; defaults
    to 1 and is capped at 3 per arch §4.3."""

    timeout_seconds: float = Field(gt=0.0)
    """Per-phase wall-time cap, summed against the deliberation-level
    :class:`ResourceBudget` at step 3."""


# =============================================================================
# PhaseDAG — frozen container with validation
# =============================================================================


class PhaseDAG(BaseModel):
    """Immutable DAG of :class:`PhaseNode` instances (arch §4.2).

    Validation is opt-in via :meth:`validate_acyclic` and
    :meth:`validate_terminal_publish`; the aggregate :meth:`validate` method
    enforces all six arch §4.4 rules. The Plan Decomposer calls
    :meth:`validate` after construction and runs a single repair pass on
    failure.
    """

    model_config = ConfigDict(frozen=True)

    nodes: tuple[PhaseNode, ...]
    edges: tuple[tuple[str, str], ...]
    """``(predecessor_phase_id, successor_phase_id)`` edges. Must be a
    subset of ``depends_on``-implied edges but can be a superset for
    explicit ordering (the Plan Decomposer keeps them in sync by
    construction)."""

    # ------------------------------------------------------------------
    # Graph queries
    # ------------------------------------------------------------------

    def _adjacency(self) -> dict[str, list[str]]:
        adj: dict[str, list[str]] = {node.phase_id: [] for node in self.nodes}
        for pred, succ in self.edges:
            if pred in adj:
                adj[pred].append(succ)
        return adj

    def _indegree(self) -> dict[str, int]:
        indeg: dict[str, int] = {node.phase_id: 0 for node in self.nodes}
        for _, succ in self.edges:
            if succ in indeg:
                indeg[succ] += 1
        return indeg

    def topological_order(self) -> tuple[str, ...]:
        """Return a deterministic Kahn-style topological ordering.

        Ties broken by ``phase_id`` lexicographic order so repeated calls
        against the same DAG yield identical tuples — required for
        snapshot stability in the step 3 tests.
        """
        adj = self._adjacency()
        indeg = self._indegree()

        # Use a sorted list as the "ready" frontier for lexicographic tie-break.
        ready = sorted([pid for pid, d in indeg.items() if d == 0])
        out: list[str] = []
        frontier = deque(ready)

        while frontier:
            pid = frontier.popleft()
            out.append(pid)
            # Track new-ready nodes to insert in sorted position.
            new_ready: list[str] = []
            for succ in adj.get(pid, ()):
                indeg[succ] -= 1
                if indeg[succ] == 0:
                    new_ready.append(succ)
            for r in sorted(new_ready):
                frontier.append(r)
                # Maintain sort order for the next pop by resorting.
            if new_ready:
                frontier = deque(sorted(frontier))

        if len(out) != len(self.nodes):
            raise ValueError(
                "PhaseDAG contains a cycle; topological_order could not visit every node"
            )
        return tuple(out)

    # ------------------------------------------------------------------
    # Rule-specific validators (arch §4.4)
    # ------------------------------------------------------------------

    def validate_acyclic(self) -> None:
        """Arch §4.4 rule 5: no cycles.

        Implementation: run the Kahn-style topological sort and assert it
        visited every node. ``ValueError`` on cycle.
        """
        try:
            order = self.topological_order()
        except ValueError as exc:
            raise ValueError(f"PhaseDAG validation failed: cycle detected ({exc})") from exc
        if len(order) != len(self.nodes):
            raise ValueError("PhaseDAG validation failed: cycle detected (partial order)")

    def validate_terminal_publish(self) -> None:
        """Arch §4.4 rule 4: exactly one publish node with no successors.

        A DAG with zero publish terminals OR with a publish node that has
        an outgoing edge fails. A DAG with two or more publish nodes also
        fails (the Iteration Controller cannot choose which one to land on).
        """
        publish_ids = [n.phase_id for n in self.nodes if n.phase_kind == "publish"]
        if len(publish_ids) == 0:
            raise ValueError(
                "PhaseDAG validation failed: exactly one publish node required, found 0"
            )
        if len(publish_ids) > 1:
            raise ValueError(
                "PhaseDAG validation failed: exactly one publish node required, "
                f"found {len(publish_ids)}: {publish_ids}"
            )
        (publish_id,) = publish_ids
        successors = [succ for pred, succ in self.edges if pred == publish_id]
        if successors:
            raise ValueError(
                "PhaseDAG validation failed: publish node must have no successors; "
                f"found outgoing edges to {successors}"
            )

    def validate(self) -> None:
        """Run all six arch §4.4 validation rules.

        Raises ``ValueError`` on the first rule that fails.
        """
        # Rule 1: exactly one produce node
        produce_ids = [n.phase_id for n in self.nodes if n.phase_kind == "produce"]
        if len(produce_ids) != 1:
            raise ValueError(
                "PhaseDAG validation failed: exactly one produce node required, "
                f"found {len(produce_ids)}"
            )

        # Rule 2: at least one review_parallel or review_serial
        review_ids = [
            n.phase_id
            for n in self.nodes
            if n.phase_kind in ("review_parallel", "review_serial")
        ]
        if not review_ids:
            raise ValueError(
                "PhaseDAG validation failed: at least one review_parallel or "
                "review_serial node required, found 0"
            )

        # Rule 3: exactly one gate_evaluate
        gate_ids = [n.phase_id for n in self.nodes if n.phase_kind == "gate_evaluate"]
        if len(gate_ids) != 1:
            raise ValueError(
                "PhaseDAG validation failed: exactly one gate_evaluate node required, "
                f"found {len(gate_ids)}"
            )

        # Rule 4: exactly one terminal publish
        self.validate_terminal_publish()

        # Rule 5: no cycles
        self.validate_acyclic()

        # Rule 6: every non-publish node has a path to publish
        (publish_id,) = [n.phase_id for n in self.nodes if n.phase_kind == "publish"]
        adj = self._adjacency()
        reverse_reachable = _reverse_reach(adj, publish_id)
        orphans = [
            n.phase_id
            for n in self.nodes
            if n.phase_id != publish_id and n.phase_id not in reverse_reachable
        ]
        if orphans:
            raise ValueError(
                "PhaseDAG validation failed: every non-publish node must have a "
                f"path to publish; orphans: {orphans}"
            )


def _reverse_reach(adj: dict[str, list[str]], target: str) -> set[str]:
    """Return the set of node IDs that can reach ``target`` via ``adj``."""
    # Build reverse adjacency.
    rev: dict[str, list[str]] = defaultdict(list)
    for pred, succs in adj.items():
        for succ in succs:
            rev[succ].append(pred)

    seen: set[str] = set()
    stack = [target]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(rev.get(node, ()))
    return seen


# =============================================================================
# PlanDecomposer — builds + repairs the DAG
# =============================================================================


class PlanDecomposer:
    """Deterministic decomposition of a :class:`TaskInterpretation` into the
    arch §4.3 default DAG.

    Stateless. Step 6 (Stage 6 Studio templates) may subclass to emit richer
    graphs; at Stage 5 the default linear chain is the only path.
    """

    _DEFAULT_TIMEOUT_SECONDS: float = 300.0
    """Per-phase wall-clock cap. Feeds into :class:`ResourceBudget` at step 3
    and is deliberately generous — the deliberation-level cap in arch §5.7
    is the binding limit."""

    def decompose(
        self,
        *,
        signature: TaskSignature,
        domain_class: DomainClass,
        output_contract: OutputFormatContract,
    ) -> PhaseDAG:
        """Build the default linear DAG for the given interpretation.

        The ``signature`` and ``output_contract`` parameters are not
        consumed by the default decomposition — they are reserved for
        Stage 6 Studio template overrides that would inspect the task
        signature or the Req-A label set when choosing reviewer count or
        phase layout. Currently only ``domain_class`` influences the DAG
        (via reviewer count).
        """
        del signature, output_contract  # reserved for Stage 6 template overrides

        reviewer_count = self._default_reviewer_count(domain_class)

        produce = PhaseNode(
            phase_id="cycle1_produce",
            phase_kind="produce",
            depends_on=(),
            agent_role="mac-producer",
            timeout_seconds=self._DEFAULT_TIMEOUT_SECONDS,
        )
        review = PhaseNode(
            phase_id="cycle2_review",
            phase_kind="review_parallel",
            depends_on=("cycle1_produce",),
            agent_role="mac-reviewer",
            reviewer_count=reviewer_count,
            timeout_seconds=self._DEFAULT_TIMEOUT_SECONDS,
        )
        gate = PhaseNode(
            phase_id="cycle3_gate",
            phase_kind="gate_evaluate",
            depends_on=("cycle2_review",),
            timeout_seconds=self._DEFAULT_TIMEOUT_SECONDS,
        )
        publish = PhaseNode(
            phase_id="publish",
            phase_kind="publish",
            depends_on=("cycle3_gate",),
            timeout_seconds=self._DEFAULT_TIMEOUT_SECONDS,
        )

        dag = PhaseDAG(
            nodes=(produce, review, gate, publish),
            edges=(
                ("cycle1_produce", "cycle2_review"),
                ("cycle2_review", "cycle3_gate"),
                ("cycle3_gate", "publish"),
            ),
        )
        dag.validate()
        return dag

    def repair(self, dag: PhaseDAG) -> PhaseDAG:
        """Attempt a single repair pass against a malformed DAG (arch §4.4).

        The pass adds the first missing required element it finds — the
        publish terminal first, the gate_evaluate node second. After the
        one addition, the DAG is re-validated. If validation still fails,
        :class:`PlanRepairFailedError` is raised; there is no second pass.
        """
        # Try validating first — if the DAG is already valid, no repair needed.
        try:
            dag.validate()
            return dag
        except ValueError:
            pass

        # Single repair action: add exactly one missing element.
        repaired = self._add_single_missing_element(dag)

        # Re-validate the single-repair result.
        try:
            repaired.validate()
        except ValueError as exc:
            raise PlanRepairFailedError(
                f"Single-pass repair failed; DAG still invalid after one repair attempt: {exc}"
            ) from exc
        return repaired

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _default_reviewer_count(domain_class: DomainClass) -> int:
        if domain_class == DomainClass.CONTESTED:
            return 2
        return 1

    def _add_single_missing_element(self, dag: PhaseDAG) -> PhaseDAG:
        """Arch §4.4 repair: add one missing publish OR one missing gate.

        Check order: publish first (it's the terminal state and the
        Iteration Controller refuses to run without it), gate second.
        """
        has_publish = any(n.phase_kind == "publish" for n in dag.nodes)
        has_gate = any(n.phase_kind == "gate_evaluate" for n in dag.nodes)

        if not has_publish:
            # Find the last non-publish node to chain from; if a gate exists
            # use that, otherwise chain from the last review node.
            anchor_id = self._find_publish_anchor(dag)
            publish_node = PhaseNode(
                phase_id="publish",
                phase_kind="publish",
                depends_on=(anchor_id,) if anchor_id else (),
                timeout_seconds=self._DEFAULT_TIMEOUT_SECONDS,
            )
            new_nodes = dag.nodes + (publish_node,)
            new_edges = (
                dag.edges + ((anchor_id, "publish"),) if anchor_id else dag.edges
            )
            return PhaseDAG(nodes=new_nodes, edges=new_edges)

        if not has_gate:
            # Insert the new gate between the last review and publish so the
            # path invariant (rule 6) holds. This is still one repair action
            # — adding one node and re-routing one edge in a single atomic
            # transformation. Without the rewire, rule 6 would fire because
            # publish would orphan the new gate.
            anchor_id = self._find_gate_anchor(dag)
            publish_ids = [n.phase_id for n in dag.nodes if n.phase_kind == "publish"]
            publish_id = publish_ids[0] if publish_ids else None

            gate_node = PhaseNode(
                phase_id="cycle3_gate",
                phase_kind="gate_evaluate",
                depends_on=(anchor_id,) if anchor_id else (),
                timeout_seconds=self._DEFAULT_TIMEOUT_SECONDS,
            )

            # Rewire: drop any anchor→publish edge, add anchor→gate + gate→publish.
            new_nodes_list = list(dag.nodes)
            new_edges_list = [
                edge
                for edge in dag.edges
                if not (edge == (anchor_id, publish_id) and publish_id is not None)
            ]

            # Also rewire the publish node's depends_on to point at the new
            # gate rather than the old anchor.
            if publish_id is not None and anchor_id is not None:
                for idx, node in enumerate(new_nodes_list):
                    if node.phase_id == publish_id and anchor_id in node.depends_on:
                        new_depends = tuple(
                            "cycle3_gate" if d == anchor_id else d
                            for d in node.depends_on
                        )
                        new_nodes_list[idx] = node.model_copy(
                            update={"depends_on": new_depends}
                        )

            new_nodes_list.append(gate_node)
            if anchor_id is not None:
                new_edges_list.append((anchor_id, "cycle3_gate"))
            if publish_id is not None:
                new_edges_list.append(("cycle3_gate", publish_id))

            return PhaseDAG(nodes=tuple(new_nodes_list), edges=tuple(new_edges_list))

        # Nothing the repair pass knows how to add — return the DAG as-is
        # so the subsequent validate() re-raises the original error.
        return dag

    @staticmethod
    def _find_publish_anchor(dag: PhaseDAG) -> str | None:
        """Pick the node that the synthesized publish should depend on."""
        for node in dag.nodes:
            if node.phase_kind == "gate_evaluate":
                return node.phase_id
        for node in dag.nodes:
            if node.phase_kind in ("review_parallel", "review_serial"):
                return node.phase_id
        return None

    @staticmethod
    def _find_gate_anchor(dag: PhaseDAG) -> str | None:
        """Pick the node that the synthesized gate should depend on."""
        for node in dag.nodes:
            if node.phase_kind in ("review_parallel", "review_serial"):
                return node.phase_id
        for node in dag.nodes:
            if node.phase_kind == "produce":
                return node.phase_id
        return None


__all__: tuple[str, ...] = (
    "PhaseDAG",
    "PhaseKind",
    "PhaseNode",
    "PlanDecomposer",
    "PlanRepairFailedError",
)
