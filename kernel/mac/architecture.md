# Praxis Stage 5.1 — Meta-Agent Controller (MAC) Architecture

**Stage:** Praxis 5.1 — MAC core architecture draft
**Author:** Winston (BMAD Architect)
**Date:** 2026-04-14
**Status:** RATIFIED v0.1 — 2026-04-14 — binding for Stage 5.2 (Murat test strategy) and Stage 5.3 (Amelia implementation). OQ-MAC-1 resolved via Option Y sidecar (see §8.1). Stage 3 Memory schema remains frozen.
**Binding inputs:**
1. `mac/quality-rubric.md` (Quinn, hardened — 12 confirmed gates R1–R12, 4 TRIZ resolutions, Req-A through Req-F)
2. `mac/benchmark-questions.md` (Stage 5.0.3 — 10 benchmark questions, 3 baselines, ADR-1 hybrid scoring, ADR-3 Spearman validation)
3. `mac/quality-dimensions-draft.md` (Carson, Round 1 — 1-5 scoring protocols for R2, R3, R10, R11)

**Prior-stage anchors (cited, not re-explained):**
- Stage 1 — `pi-mono/pi-mono-cost-tracker-architecture.md` (CostEvent, events_outbox, `CostTracker.track_cost`)
- Stage 2 — `compression/architecture.md` (Forge F8 reasoning preservation, `reasoning_preserved` semantics; F-2 TONL parked)
- Stage 3 — `memory/architecture.md` (`Memory(Protocol)` facade, §6.3 admission, §6.4 promotion, §6.6 named MAC contract, §7 schema, §9 TelemetryEvent envelope)
- Stage 4 — `runtime/architecture.md` (§4.1 ProducerMemoryProxy/ReviewerMemoryProxy, §4.3 ResourceBudget, §5 MCP adapter, §8.1 Path A/B outbox, §8.5 Runtime→MAC handoff, §12 OQ-N Path (i))

---

## §1. Research Foundation Review

### §1.1 Reference Patterns Consumed

The MAC inherits structural ideas from seven reference projects, but anchors its **gate content** on quality-rubric.md §6 (R1–R12). The references inform mechanism, not measurement.

| Reference | Pattern Extracted | Where Applied | Where Explicitly NOT Applied |
|---|---|---|---|
| **Self-Refine** (Madaan et al.) | 3-cycle iteration: generate → critique → revise; bounded iterations with stopping criteria | §5 Iteration Controller — three-phase Cycle 1/2/3 state machine | We do NOT use Self-Refine's single-agent self-critique; reviewer agent in Cycle 3 is structurally distinct from producer |
| **MetaAgent / FORGE** | Reasoning preservation across compaction boundaries via last-block injection | §10.4 Compression integration — consumes Forge F8 (`reasoning_preserved` flag) | We do NOT redo reasoning extraction in MAC; Forge owns it |
| **SiriuS** (multi-agent debate) | Adversarial deliberation with structured proposer/critic roles | §7 Information Asymmetry Router (binds to Runtime §4.1 proxies) | We do NOT use SiriuS's free-form turn-taking; deliberation is FSM-governed in §5 |
| **Tree-of-Thoughts** (ToT) | Explicit branching + backtracking when a path fails a quality gate | §5.5 Backtracking on gate failure — Cycle 2 may regenerate Cycle 1's plan if a critical gate fails | We do NOT maintain a full search tree; backtracking depth is capped at 1 by ResourceBudget |
| **Multi-agent debate** (Du et al.) | Independent agents producing parallel perspectives, then a synthesis pass | §5.4 Cycle 2 parallel reviewers (when domain class permits) | We do NOT use unanimous-voting consensus; quality-gate scores arbitrate |
| **Atelier** (Robertsfeir) | Wave-based pipeline (Poirot/Robert/Sable) with constrained-context reviewers (Poirot Blind Review pattern) | §6 Quality Gate Engine wave structure; mechanical enforcement of section-aware routing | Atelier's per-domain gate set is replaced by R1–R12 from quality-rubric.md §6 (see §1.3 Conflict #3 resolution) |
| **Forge / sage / muse / forge** (antinomyhq) | Per-mode reasoning fences | NOT applied — see §1.3 Conflict #4 refutation below |

### §1.2 Why Multi-Agent at All — The Differentiation Anchor

Quality-rubric.md §6 lists R4 (Steelman Completeness) and R5 (Dissent Preservation) as **Critical** priority and assigns them 2× weight in benchmark scoring (benchmark-questions.md §6 step 5). These are the gates that single-agent systems systematically fail, because:

1. A single agent generates the argument and the counterargument from **the same prior** — the counterargument is structurally weaker than the argument by construction. (This is Carson's D4 single-agent gap analysis, quality-dimensions-draft.md §D4.)
2. A single agent has **no genuine internal disagreement** — any "minority view" it produces is manufactured, not preserved. (Carson's D5 single-agent gap analysis, quality-dimensions-draft.md §D5.)

The MAC's structural fix is **information asymmetry** at the reviewer phase: the Cycle 3 reviewer agent reads only the producer's output (not its reasoning trace), AND is prompted via Req-F to **independently construct** the strongest counterargument before reading the producer's `[STEELMAN]` section. This dual mechanism (information hiding + independent generation) is what makes the R4 differentiation defensible. Information hiding alone is insufficient — quality-rubric.md A3 explicitly states: *"Information asymmetry removes anchoring bias; it does not create perspectival diversity from same-model agents."* Hence Req-F's mandatory independent-counterargument elicitation in §7.1 below.

### §1.3 Embedded Conflict Resolutions

**Conflict #3 — 12 gates: Atelier vs. R1-R12.** Atelier reference dumps describe a 12-gate wave pipeline tuned for general code/document review. The MAC retains Atelier's **mechanical pattern** (wave-based phases, constrained-context reviewers, pattern of mechanical enforcement) but **overrides Atelier's gate content** with R1-R12 from quality-rubric.md §6. Where this document references "12 gates," it always means R1–R12 from quality-rubric.md, never Atelier's set. Murat (5.2) and Amelia (5.3) must verify this by citation: every gate appearance in this doc cites a row from quality-rubric.md §6.

**Conflict #4 — sage / muse / forge are NOT reasoning modes.** A previous draft prompt erroneously treated Forge's `sage`, `muse`, and `forge` as orthogonal reasoning modes that the MAC could route between. This is wrong: per `compression/architecture.md` line 116, those names are UI presentation modes (TUI / CLI / ZSH) and have no semantic effect on reasoning preservation. The MAC does not consume them. The only Forge contract that the MAC consumes is the `reasoning_preserved: bool` fallback flag (`compression/architecture.md` §3.2, F8 row at line 129). Explicit refutation: any future doc that asserts "MAC switches to muse mode for reviewers" is incorrect and should be rejected at PR review.

### §1.4 What MAC Does Not Try to Do

To prevent scope creep, the MAC explicitly does NOT own:

- **Tool execution** — that is Runtime §5 MCP adapter
- **Memory persistence** — that is Memory facade §2.1
- **Cost accounting** — that is Pi-Mono `CostTracker.track_cost`
- **Compression** — that is Compression Forge F8
- **Tenant isolation** — that is Memory deployment manifest + Runtime proxy construction
- **Secret management** — that is the Runtime sandbox layer
- **Workflow templates / Studio surfaces** — those are Stage 6

The MAC is an **orchestration plane** that calls into these substrates via the integration contracts in §10. It owns the **deliberation loop**, the **quality gate scoring**, the **information asymmetry router**, and the **cross-session learning loop**, and nothing else.

---

## §2. Overall MAC Architecture

### §2.1 Component Diagram

The MAC has 8 internal components, organized into 3 horizontal planes:

```
                        ┌─────────────────────────────────────────────┐
                        │              MAC Public Surface             │
                        │   (deliberate(task) → DeliberationResult)   │
                        └─────────────────────────────────────────────┘
                                         │
   ┌─────────────────────────────────────┼──────────────────────────────────┐
   │                                     │                                  │
   │  ┌───────────────────┐    ┌─────────▼─────────┐    ┌────────────────┐  │
   │  │  Task Interpreter │───▶│  Plan Decomposer  │───▶│  3-Cycle Iter. │  │  Plane A:
   │  │       (§3)        │    │       (§4)        │    │  Controller §5 │  │  Plan
   │  └───────────────────┘    └───────────────────┘    └────────┬───────┘  │
   │                                                             │          │
   └─────────────────────────────────────────────────────────────┼──────────┘
                                                                 │
   ┌─────────────────────────────────────────────────────────────┼──────────┐
   │                                                             │          │
   │  ┌───────────────────┐    ┌───────────────────┐    ┌────────▼───────┐  │
   │  │ Information       │◀───│ Quality Gate      │◀───│  Phase Runner  │  │  Plane B:
   │  │ Asymmetry Router  │    │ Engine (§6)       │    │   (§5.3)       │  │  Execute
   │  │       (§7)        │    │  R1..R12          │    │                │  │
   │  └───────────────────┘    └───────────────────┘    └────────────────┘  │
   │                                                                        │
   └──────────────────────────────────────────────────────────────────┬─────┘
                                                                      │
   ┌──────────────────────────────────────────────────────────────────┼─────┐
   │                                                                  │     │
   │  ┌───────────────────┐    ┌───────────────────┐    ┌─────────────▼──┐  │
   │  │ Cross-Session     │    │ Observability     │    │ Integration    │  │  Plane C:
   │  │ Learning Loop §8  │    │ Hooks (§11)       │    │ Adapters §10   │  │  Persist
   │  └───────────────────┘    └───────────────────┘    └────────────────┘  │
   │                                                                        │
   └────────────────────────────────────────────────────────────────────────┘
```

**Plane A — Plan:** Deterministic, single-pass. Task Interpreter reads the user input, classifies the domain (§3.4 `DomainClass` enum per SQ-5), extracts the question signature, and emits an Output-Format Contract (Req-A section labels). Plan Decomposer expands into a phase DAG that the Iteration Controller will execute.

**Plane B — Execute:** Multi-cycle. The Iteration Controller's FSM (§5.2) walks the DAG, spawning agents through the Information Asymmetry Router (§7), running gate evaluation through the Quality Gate Engine (§6), and deciding whether to continue, backtrack, or finalize.

**Plane C — Persist:** Side-effects. Learning Loop writes outcomes to Memory via `mac.publish` (memory/architecture.md line 913); observability hooks emit telemetry via the registered MAC label namespace (§11 / SQ-2); integration adapters route Pi-Mono CostEvents and Runtime spawning calls.

### §2.2 Public Surface

The MAC exposes a single primary entry point:

```python
# praxis/kernel/mac/controller.py

from praxis.kernel.mac.task import TaskInput, DeliberationResult, ResourceBudget
from praxis.kernel.runtime.spawner import AgentSpawner
from praxis.kernel.memory.facade import Memory
from praxis.kernel.pi_mono.tracker import CostTracker

class MetaAgentController:
    """Praxis Stage 5 MAC. Single entry: deliberate()."""

    def __init__(
        self,
        spawner: AgentSpawner,            # Runtime §4.1 — provides ProducerMemoryProxy/ReviewerMemoryProxy construction
        memory: Memory,                   # Memory §2.1 — facade, never bypassed
        cost_tracker: CostTracker,        # Pi-Mono §4.2
        clock: Clock,                     # injectable for tests (Murat's hard requirement)
        gate_registry: "GateRegistry",    # §6.1 — 12 gate evaluator implementations
        bootstrap_loader: "BootstrapLoader",  # §8.1 — loads benchmark gold standards
    ) -> None: ...

    async def deliberate(
        self,
        task: TaskInput,
        budget: ResourceBudget | None = None,   # Defaults to ResourceBudget.default_for_role(MAC) per §5.7
    ) -> DeliberationResult: ...
```

`DeliberationResult` is the canonical output Pydantic model and is defined in §2.5.

### §2.3 The 3-Cycle Data Flow

The MAC executes exactly three cycles for every successful deliberation:

```
                     User TaskInput
                          │
                          ▼
                ┌──────────────────────┐
                │  §3 Task Interpreter │  ──── classifies domain_class (§3.4)
                │                      │       emits OutputFormatContract
                └──────────────────────┘       (Req-A section labels)
                          │
                          ▼
                ┌──────────────────────┐
                │ §4 Plan Decomposer   │  ──── DAG of phases (validation, repair)
                └──────────────────────┘
                          │
                          ▼
                ╔══════════════════════════════════════╗
                ║  CYCLE 1 — Producer Generation       ║
                ║  ─────────────────────────────────── ║
                ║  • §8.1 retrieve_similar_tasks       ║  ─── seed from memory + bootstrap
                ║  • §7 spawn ProducerAgent            ║      (gold standards land here)
                ║  • Producer emits structured output  ║
                ║    using Req-A labels [FINDINGS]…    ║
                ╚══════════════════════════════════════╝
                          │
                          ▼
                ╔══════════════════════════════════════╗
                ║  CYCLE 2 — Reviewer Critique         ║
                ║  ─────────────────────────────────── ║
                ║  • §7 spawn ReviewerAgent(s)         ║  ─── ReviewerMemoryProxy
                ║  • Req-F: independent steelman first ║      enforces info asymmetry
                ║  • Compare to producer's [STEELMAN]  ║      (§9.0 Runtime arch)
                ║  • Emit critique → §6 gate scoring   ║
                ╚══════════════════════════════════════╝
                          │
                          ▼
                ╔══════════════════════════════════════╗
                ║  CYCLE 3 — Verification & Repair     ║
                ║  ─────────────────────────────────── ║
                ║  • §6 Quality Gate Engine: R1..R12   ║  ─── section-aware routing
                ║  • Req-B: gate→section routing       ║      (Req-B); Req-C co-eval
                ║  • Req-C: (R8,R7) and (R5,R4) caps   ║      (Req-C); domain guards
                ║  • Req-E: domain guard suspension    ║      (Req-E); Req-D anchors
                ║  • Req-D: judge calibration anchors  ║      embedded in prompt
                ║  • If FAIL → backtrack (§5.5) ≤1×    ║
                ║  • If PASS → publish (§8 learning)   ║
                ╚══════════════════════════════════════╝
                          │
                          ▼
                ┌──────────────────────┐
                │ §8 Learning Loop     │  ──── mac.publish to Memory
                │ writes via Memory    │       (memory §6.6 line 913)
                └──────────────────────┘
                          │
                          ▼
                  DeliberationResult
```

**Why exactly three cycles, not N:** The 3-cycle pattern was chosen because it maps cleanly to producer/reviewer/verifier — the minimum viable separation that lets information asymmetry function. A 2-cycle (producer/reviewer-and-verifier-fused) collapses the gate-scoring pass into the reviewer agent, which we cannot do because gate evaluation must be a constrained-context judgment (Req-D anchors, Req-B routing) and the reviewer agent has full content access. A 4+ cycle scheme adds latency and burns tokens without a corresponding quality lift in our reference Self-Refine literature. Three is the floor that satisfies all binding constraints.

### §2.4 State Management

The MAC's per-deliberation state is a `DeliberationState` Pydantic model held in memory by the Controller for the duration of `deliberate()`. State is **not** persisted between deliberations — cross-session continuity flows through Memory facade calls in §8.

```python
# praxis/kernel/mac/state.py

from pydantic import BaseModel, ConfigDict
from typing import Literal
from datetime import datetime

class DeliberationState(BaseModel):
    model_config = ConfigDict(frozen=False)  # mutable: state machine progresses

    cycle_id: str                          # ULID, monotonic per deliberation
    task: TaskInput
    domain_class: "DomainClass"            # §3.4 — frozen schema
    output_contract: "OutputFormatContract"
    plan_dag: "PhaseDAG"

    cycle_1_output: ProducerOutput | None = None
    cycle_2_critique: ReviewerCritique | None = None
    cycle_3_gate_scores: dict[str, GateScore] | None = None  # keys: R1..R12

    backtrack_count: int = 0               # capped at 1 per §5.5
    started_at: datetime
    ended_at: datetime | None = None

    current_phase: Literal[
        "interpret", "decompose",
        "cycle_1_produce", "cycle_2_review", "cycle_3_verify",
        "publish", "complete", "failed"
    ] = "interpret"
```

State transitions are visible to telemetry (§11) — every transition emits a `mac.cycle.transition` event. Murat (5.2) MUST verify these are non-waivable property tests.

### §2.5 DeliberationResult Output Contract

```python
# praxis/kernel/mac/results.py

class GateScore(BaseModel):
    model_config = ConfigDict(frozen=True)
    gate_id: str                          # "R1".."R12"
    raw_score: int                        # 1..5 from Tier 1+2+3 evaluation
    effective_score: int                  # post-Req-C cap, post-Req-E suspend
    weight: int                           # 1 or 2 (§9 OQ-5 top-5 weighting)
    suspended: bool                       # True if §6.5 domain guard suspended
    rationale: str                        # judge prompt rationale (Tier 3)
    evaluated_section: Literal[
        "FINDINGS", "RECOMMENDATIONS", "STEELMAN",
        "DISSENT", "SCENARIOS", "L1", "L2", "FULL"
    ]                                     # Req-B routing trace

class DeliberationResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    cycle_id: str
    task_signature: TaskSignature         # memory/architecture.md §2.2
    output: ProducerOutput                # final Cycle-3-passed output, Req-A labeled
    gate_scores: dict[str, GateScore]     # 12 entries, R1..R12
    composite_score: float                # 0..100 per benchmark §6 step 5
    backtrack_count: int
    bootstrap_seeds_used: list[str]       # entry_ids retrieved from gold-standard corpus
    cost_usd: float                       # sum of CostEvent.amount across cycle
    duration_seconds: float
    forge_degraded: bool                  # §5.6 Forge fallback triggered (SQ-7)
```

### §2.6 Failure Recovery

Three named failure modes:

| Failure | Detection | Recovery |
|---|---|---|
| **Gate failure** (any Critical gate score < 3 after Cycle 3) | §6 Engine returns failed `gate_scores` | §5.5 backtrack to Cycle 1 ONCE; on second failure return `DeliberationResult` with `composite_score < threshold` and let caller decide |
| **Budget exhaustion** (`BudgetExceededError` from any cycle) | Runtime §4.3 raises | Spawner cancels the cycle; MAC catches, returns partial `DeliberationResult` with `current_phase="failed"`, `cost_usd` populated, `output=None` |
| **Forge degradation** (`reasoning_preserved=False` from Compression) | §10.4 adapter returns flag | §6.6 applies R7 1-point penalty AFTER Req-C caps (SQ-7 ordering); deliberation continues |

Crash recovery: MAC's in-memory state is NOT durable mid-deliberation. If the host process dies during a `deliberate()` call, the partial deliberation is lost (no checkpoint). This is a **deliberate non-goal** for Stage 5 — durable mid-deliberation checkpointing would require committing partial states to Memory, which complicates the §8 learning loop's promotion semantics. Stage 7 POV Harness may revisit if customers demand multi-hour deliberations.

---

## §3. Task Interpreter Design

### §3.1 Purpose

The Task Interpreter is the entry point of `deliberate()`. It transforms an unstructured `TaskInput` into a structured set of artifacts the rest of the MAC consumes:

1. A normalized `TaskSignature` (matches Memory's `TaskSignature` shape — memory/architecture.md §2.2)
2. A `DomainClass` classification (frozen 5-value enum — see §3.4 below; SQ-5 binding)
3. An `OutputFormatContract` declaring which Req-A section labels are required
4. An R13 deferral note (R13 is parked per SQ-3 — see §3.5 below; MAC.OQ-7)

### §3.2 TaskInput and TaskSignature

```python
# praxis/kernel/mac/task.py

from pydantic import BaseModel, ConfigDict, Field
from praxis.kernel.memory.models import TaskSignature  # memory §2.2

class TaskInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    raw_prompt: str
    customer_context: dict[str, str] = Field(default_factory=dict)
    workflow_template_id: str | None = None  # set by Stage 6 Studio when invoked there
    explicit_question: str | None = None     # if caller already extracted; else MAC infers
```

The Task Interpreter calls a small Haiku-class extractor agent (via Runtime §4.1 ProducerMemoryProxy with retrieval disabled) to:
1. Identify the explicit decision question (if not provided)
2. Hash the canonicalized input → `TaskSignature.input_hash`
3. Compute `context_fingerprint` over the `customer_context` dict
4. Set `task_type` based on workflow_template_id (or `"strategic_advisory_uncategorized"` if no template)

The resulting TaskSignature is what `retrieve_similar_tasks(tenant_id, signature, top_k=5, min_similarity=0.75)` (memory §2.1 line 216) consumes in Cycle 1 seeding.

### §3.3 OutputFormatContract — Req-A Mandatory Labels

Per Req-A (quality-rubric.md §7), all MAC outputs **must** use labeled sections. The Task Interpreter emits an `OutputFormatContract` that the Cycle 1 producer prompt embeds verbatim:

```python
# praxis/kernel/mac/task.py (continued)

class OutputFormatContract(BaseModel):
    model_config = ConfigDict(frozen=True)

    required_labels: tuple[str, ...] = (
        "[FINDINGS]",
        "[RECOMMENDATIONS]",
        "[STEELMAN]",
        "[DISSENT]",
        "[SCENARIOS]",
    )
    content_levels: tuple[str, ...] = (
        "L1: Executive Summary + Key Recommendations",
        "L2: Main Analysis Body",
        "L3: Supporting Detail / Appendices",
    )
    domain_guards_active: tuple[str, ...]  # populated per §3.4 + §6.5 mapping

    def to_producer_prompt_fragment(self) -> str: ...
    """Returns the verbatim instruction block injected into producer prompts.
    Includes all 5 required labels, the 3 content levels, and any domain-guard
    suspensions that affect required labels (e.g., R5 suspended on consensus
    domains makes [DISSENT] optional but recommended)."""
```

The fragment text is fixed at Stage 5 ship time and unit-tested for byte-for-byte stability — Murat's test plan (5.2) must include a snapshot test on `to_producer_prompt_fragment()` so any future edit is intentional and reviewed.

### §3.4 DomainClass Enum — SQ-5 Frozen Schema

Per **SQ-5** (frame binding), the domain classification primitive is a frozen Pydantic enum with **exactly 5 values**:

```python
# praxis/kernel/mac/task.py (continued)

from enum import Enum

class DomainClass(str, Enum):
    """Domain classification for Req-E gate guards.

    FROZEN SCHEMA: Workflow templates may OVERRIDE which guards activate per
    DomainClass value (via §6.5 mapping config), but CANNOT introduce new
    enum values. Adding a sixth class requires a new Stage 5 architecture
    revision, not a workflow YAML change.
    """
    CONTESTED = "contested"           # genuine disagreement; all gates fully active
    CONSENSUS = "consensus"           # established settled-fact domain; R5 guard fires
    DETERMINISTIC = "deterministic"   # has a knowable correct answer; R11 guard fires
    BINARY = "binary"                 # pass/fail or yes/no decision; R11 guard fires
    DIAGNOSTIC = "diagnostic"         # hypothesis-generation problem; R12 emphasized
```

The Task Interpreter classifies via a deterministic prompted call to a lightweight model:
- Input: `task.raw_prompt` + `task.customer_context` + benchmark task signatures (for nearest-neighbor anchor)
- Output: one of the 5 enum values + a confidence score

If confidence < 0.7, default to `CONTESTED` (the most permissive class — no gates suspended). This is the safe default that maximizes gate firing.

**Structural constraint (Murat 5.2 test):** A grep test in the test suite — `grep -r "class DomainClass" praxis/kernel/mac/` — must return **exactly one match** (the canonical definition). Any duplicate definition is a test failure. This prevents drift via copy-paste in workflow modules.

### §3.5 R13 Deferral — SQ-3 / MAC.OQ-7

Per **SQ-3** (frame binding) and quality-rubric.md §6 R13 row (CONDITIONAL), R13 Evidence Sourcing is **deferred to Stage 6**. The Task Interpreter's job here is to NOT emit R13 in the gate set for any Stage 5 deliberation.

**Two-sentence rationale:** Stage 5 MAC agents operate from training knowledge (no retrieval-augmented generation with source access in Stage 5 scope), so penalizing the absence of source citations creates systematic false positives on every output. R13 is admitted at Stage 6 if and only if Studio workflow templates elicit retrieval-grounded analysis with source attribution as a primary output contract — see §13 Open Questions for the Stage 6 re-admission trigger.

Practically: the Task Interpreter constructs a `gate_set: tuple[str, ...]` containing the 12 gates `("R1", ..., "R12")` and never `"R13"`. Murat 5.2 must include a property test asserting that `gate_set` is exactly this 12-tuple in Stage 5 builds.

### §3.6 Failure Modes for the Interpreter

| Mode | Detection | Handling |
|---|---|---|
| Empty / non-question prompt | extractor returns `explicit_question=None` and no fallback inference | Reject with `InvalidTaskError`; do not enter Cycle 1 |
| Adversarial prompt-injection in `customer_context` (e.g., "ignore quality gates") | structural check on `customer_context` (no keys matching `mac\.|gate_|disable_`) | Reject with `InvalidTaskError`; emit `mac.task.injection_blocked` telemetry |
| Domain classifier returns invalid value | Pydantic enum validation fires | Default to `CONTESTED` and emit `mac.task.classifier_fallback` telemetry |

---

## §4. Plan Decomposer Design

### §4.1 Purpose

Plan Decomposer is a deterministic transformation: given the `OutputFormatContract` from §3, the `DomainClass`, and the `TaskSignature`, produce a `PhaseDAG` that the §5 Iteration Controller will execute.

### §4.2 PhaseDAG Structure

```python
# praxis/kernel/mac/plan.py

from pydantic import BaseModel, ConfigDict
from typing import Literal

class PhaseNode(BaseModel):
    model_config = ConfigDict(frozen=True)
    phase_id: str                   # "cycle1_produce", "cycle2_review", "cycle3_gate", etc.
    phase_kind: Literal[
        "produce",                  # Cycle 1 — single producer agent spawn
        "review_parallel",          # Cycle 2 — N reviewer spawns in parallel
        "review_serial",            # Cycle 2 — N reviewers sequentially (rare, Forge-fallback path)
        "gate_evaluate",            # Cycle 3 — Quality Gate Engine pass
        "publish",                  # §8 Learning Loop write
    ]
    depends_on: tuple[str, ...]     # phase_ids that must complete first
    agent_role: str | None = None   # for produce/review_* phases — Runtime §4.1 AgentRole
    reviewer_count: int = 1         # for review_parallel; 1 by default
    timeout_seconds: float          # per-phase wall-time cap, summed against ResourceBudget

class PhaseDAG(BaseModel):
    model_config = ConfigDict(frozen=True)
    nodes: tuple[PhaseNode, ...]
    edges: tuple[tuple[str, str], ...]   # (predecessor_phase_id, successor_phase_id)

    def topological_order(self) -> tuple[str, ...]: ...
    def validate_acyclic(self) -> None: ...
    def validate_terminal_publish(self) -> None: ...
    """Asserts the DAG has exactly one terminal 'publish' node with no successors."""
```

### §4.3 The Default DAG (Cycle 1 → Cycle 2 → Cycle 3 → Publish)

The vast majority of deliberations use a single canonical DAG:

```
       cycle1_produce
              │
              ▼
     cycle2_review (parallel reviewers, count from §4.4)
              │
              ▼
       cycle3_gate
              │
              ▼
          publish
```

`reviewer_count` for `cycle2_review` defaults to:
- **2** for `DomainClass.CONTESTED` (two independent reviewers — gives the gate engine richer critique signal for R4/R5)
- **1** for all other domain classes (no benefit from a second reviewer when only one of the dimensions is contested)

For workflow templates (Stage 6) that need richer deliberation, the count can be lifted to a maximum of **3** (configured per template, validated by `PhaseDAG.validate()`); higher counts are rejected because of ResourceBudget concerns and cumulative cost.

### §4.4 Validation and Repair

`PhaseDAG.validate()` enforces:

1. Exactly one node with `phase_kind="produce"` (the Cycle 1 anchor)
2. At least one node with `phase_kind="review_parallel"` or `"review_serial"`
3. Exactly one node with `phase_kind="gate_evaluate"`
4. Exactly one terminal `phase_kind="publish"`
5. No cycles (topological sort succeeds)
6. Every non-publish node has a path to publish

If validation fails, the Decomposer attempts a single repair pass — adding the missing publish node if absent, or adding a default `cycle3_gate` if the gate phase is missing. After one repair attempt, the Decomposer raises `PlanRepairFailedError` and the deliberation aborts. Repair is intentionally limited to one pass — repeated repair indicates a malformed template that should be caught by Stage 6 template validation, not papered over here.

### §4.5 Why a DAG and Not a Single Linear Sequence

Although the default DAG is linear, the DAG abstraction lets us add **parallel reviewers** (the most common non-linear case) without re-architecting. Parallel reviewers are required for `DomainClass.CONTESTED`, which is the most common class in our benchmark questions (Q1–Q9 are all contested; only Q10 leans diagnostic). Encoding the structure as a DAG also lets Stage 6 Studio compose richer phase graphs without touching MAC core code.

---

## §5. 3-Cycle Iteration Controller

### §5.1 Purpose

The Iteration Controller is the **executor** of the PhaseDAG. It owns:

- The `DeliberationState` mutation across phases
- ResourceBudget enforcement (delegating to Runtime §4.3)
- Backtracking when Cycle 3 gate evaluation fails (§5.5)
- The single backtrack cap (1 retry max — see SQ-7 + §5.5)

### §5.2 State Machine

```
   ┌──────────────┐
   │   interpret  │ ── invokes §3 Task Interpreter
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   decompose  │ ── invokes §4 Plan Decomposer
   └──────┬───────┘
          │
          ▼
   ┌──────────────────┐
   │ cycle_1_produce  │ ── ProducerMemoryProxy retrieve + spawn (§7)
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │ cycle_2_review   │ ── ReviewerMemoryProxy spawn (§7)
   │   (parallel)     │       Req-F independent steelman protocol
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │ cycle_3_verify   │ ── §6 Quality Gate Engine pass
   └──────┬───────────┘
          │
       ┌──┴──┐
       │     │
   PASS│     │FAIL (any Critical gate < 3, backtrack_count == 0)
       │     │
       │     ▼
       │  ┌───────────────┐
       │  │ backtrack_set │ ── increment backtrack_count to 1
       │  └───────┬───────┘
       │          │
       │          └──────────► back to cycle_1_produce
       │
       ▼
   ┌──────────────┐
   │   publish    │ ── §8 Learning Loop write via Memory.mac.publish
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   complete   │
   └──────────────┘
```

There are also two terminal failure transitions not shown for brevity:
- `cycle_*_*` → `failed` (on `BudgetExceededError` from Runtime)
- `cycle_3_verify` → `failed` (on second consecutive Critical gate failure when `backtrack_count == 1`)

### §5.3 Phase Runner

The Phase Runner is the actual executor of a single `PhaseNode`. Its surface is intentionally tiny:

```python
# praxis/kernel/mac/runner.py

class PhaseRunner:
    """Stateless executor for a single PhaseNode against a DeliberationState."""

    def __init__(
        self,
        spawner: AgentSpawner,            # Runtime §4.1
        gate_engine: "QualityGateEngine", # §6
        learning_loop: "LearningLoop",    # §8
        cost_tracker: CostTracker,        # Pi-Mono §4.2
        clock: Clock,
    ) -> None: ...

    async def run_phase(
        self,
        phase: PhaseNode,
        state: DeliberationState,
        budget: ResourceBudget,
    ) -> DeliberationState: ...
    """Mutates state.current_phase, runs the phase, returns updated state.
    Phase-specific dispatch table inside (produce / review_* / gate_evaluate / publish).
    Raises BudgetExceededError if budget blown."""
```

The Iteration Controller calls `run_phase` in topological order, threading the (mutating) state through.

### §5.4 Cycle 2 Parallelism

When `phase_kind="review_parallel"` and `reviewer_count > 1`, the Phase Runner uses `asyncio.gather` to spawn N reviewer agents concurrently. Each reviewer:
- Receives a fresh `ReviewerMemoryProxy` (from Spawner via `_construct_memory_proxy`, runtime §4.1.5)
- Receives **only** the producer's output text — not the producer's reasoning trace, not the producer's bus events (Layer 1 type-level enforcement + Layer 2 bus filtering, runtime §9.1)
- Receives the Req-F instruction (independent steelman before reading `[STEELMAN]`)

The reviewers do not see each other's output. Their critiques are aggregated by the Quality Gate Engine in Cycle 3 — the Engine considers **both** critiques when scoring R4 and R5, taking the **higher** of the two scores when they disagree (R4/R5 are presence-and-quality gates; if either reviewer found a strong steelman the analysis demonstrates it).

**Why max 3 reviewers:** Each reviewer adds an LLM call (≈10–30s wall time) and ResourceBudget tokens. The marginal R4/R5 lift from a 4th reviewer is below the noise floor in our reference Self-Refine and SiriuS literature. We accept the tradeoff: Stage 5 caps at 3, Stage 6+ may revisit.

### §5.5 Backtracking on Critical Gate Failure

If Cycle 3 returns any Critical-priority gate (R1, R2, R4, R5, R7 per quality-rubric.md §6) with `effective_score < 3`, AND `state.backtrack_count == 0`, the Iteration Controller:

1. Increments `state.backtrack_count` to 1
2. Resets `state.cycle_1_output`, `state.cycle_2_critique`, `state.cycle_3_gate_scores` to `None`
3. Constructs a **repair-prompt fragment** that names the failed gate(s) and the rationale text from each failed `GateScore.rationale`
4. Re-enters Cycle 1 with the original task PLUS the repair-prompt fragment appended to the producer prompt

This is a **single-shot** retry. If Cycle 3 fails a second time on any Critical gate, the deliberation terminates with `current_phase="failed"`. We deliberately do not loop indefinitely:

- **ResourceBudget protection** — every retry burns roughly 2× the original deliberation cost; uncapped retries make worst-case cost unbounded and break Pi-Mono's predictability guarantees.
- **Learning loop integrity** — too many retries pollute the Memory write path and complicate the §8 promotion logic.
- **Customer signal** — a deliberation that fails twice signals that the task is harder than the MAC can handle without human escalation; pretending otherwise wastes tokens and produces lower-quality output.

The `failed` `DeliberationResult` still carries gate scores so the caller can see what failed; it just has `output=None` and `composite_score=None`.

### §5.6 Forge Fallback Handling — SQ-7

Per **SQ-7**, when the Compression layer signals `reasoning_preserved=False` (compression/architecture.md §3.2 fallback), the Iteration Controller:

1. Records `state.forge_degraded = True`
2. Cycle 3 attempts to **re-extract** reasoning from the pre-compaction buffer (the Spawner's bus history within the cycle window). If reusable reasoning is found, no penalty applies.
3. If pre-compaction extraction also fails, Cycle 3 tags the output `reasoning-trace-degraded` and applies a **1-point R7 penalty** as defined in §6.6.

**Critical SQ-7 ordering constraint:** the R7 penalty MUST NOT cascade into the Req-C R8 cap. Order of operations in the Quality Gate Engine (§6.3 detail):

1. Compute **raw** scores R1..R12 from gate evaluators (Tier 1+2+3)
2. Apply Req-C co-evaluation caps using **raw R7** (pre-penalty)
3. Apply the Forge-degradation R7 penalty **last** — only to R7's effective score, not propagating

Worked example (SQ-7 binding test, mirrored in §6.3):
- `R7_raw=4, R8_raw=4, forge_degraded=True`
- After Req-C: `R8_capped = min(4, 4+1) = 4` (no cap, since R7_raw=4)
- After Forge penalty: `R7_effective = 4 - 1 = 3`
- Final: `R7_effective = 3`, `R8_effective = 4` (NOT capped at 3)

Murat's 5.2 test plan must include this exact case as a property test, marked `no_waiver`.

### §5.7 ResourceBudget Defaults

The MAC inherits ResourceBudget from Runtime §4.3. The default for the MAC role (used when caller passes `budget=None` to `deliberate()`) is:

```python
# praxis/kernel/mac/budget.py

from praxis.kernel.runtime.spawner import ResourceBudget, AgentRole

DEFAULT_MAC_BUDGET = ResourceBudget(
    max_tokens=400_000,           # 2× producer + 2× reviewer + gate eval overhead
    max_wall_seconds=900.0,       # 15 min worst-case for 3-cycle + 1 backtrack
    max_tool_calls=200,           # generous for retrieval + memory writes
    max_memory_writes=100,        # tentative + confirmed paths × 3 cycles + backtrack
)
```

Per Runtime §4.3, budget overruns raise `BudgetExceededError`. The MAC's Iteration Controller catches at the cycle boundary and emits the appropriate failure transition. There is no "soft warn" mode — the budget is binding, exactly as Runtime §4.3 mandates.

---

## §6. Quality Gate Engine

### §6.1 The 12-Gate Catalog (R1–R12, anchored on quality-rubric.md §6)

The MAC's gate engine implements **exactly 12 gates**, taken **verbatim** from quality-rubric.md §6 Section 6 (Confirmed Gates table, lines 209–222 in that file).

| Gate ID | Name | Definition Anchor | Tier(s) | Priority | Section Applied | Source Row |
|---|---|---|---|---|---|---|
| **R1** | Epistemic Calibration | Claims labeled by evidential basis; confidence proportional; risks entity-specific | T1 (presence + body keyword density) + T3 (LLM-judge: calibration + risk specificity) | **Critical** | Full document | quality-rubric.md §6 R1 |
| **R2** | Question Fidelity | Stated question OR named reformulation answered; 5/5 = meta-evaluation | T1 (OR-logic) + T2 (retrieval consistency) | **Critical** | `[RECOMMENDATIONS]` | quality-rubric.md §6 R2 |
| **R3** | Falsifiability | Monitorable, observable invalidation conditions per conclusion | T1 (presence) + T2 (specificity comparison) | High | Full document | quality-rubric.md §6 R3 |
| **R4** | Steelman Completeness | Strongest counterarguments at full fidelity; **two-step judge protocol** (Req-F) | T3 two-step (independent generation → comparison) | **Critical** | `[STEELMAN]` | quality-rubric.md §6 R4 |
| **R5** | Dissent Preservation | Minority views with content depth; manufactured dissent detected (Req-C cap) | T1 (presence + depth floor) + T3 (faithful representation) | **Critical** | `[DISSENT]` | quality-rubric.md §6 R5 |
| **R6** | Decision Relevance Density | L1 layer dense; key findings prioritized | T1 (priority markers in L1) + T3 (L1 density only) | Medium | **L1 only** | quality-rubric.md §6 R6 |
| **R7** | Reasoning Traceability | Logic chain followable; inference markers; logical validity | T1 (marker density) + T2 (retrieval) + T3 (logical validity) | **Critical** | L2 main body | quality-rubric.md §6 R7 |
| **R8** | Actionability Calibration | Specific actionable recommendations; "further analysis" without conditional fails; R7 co-eval | T1 (presence) + T3 (specificity, with R7 co-eval cap per Req-C) | High | `[RECOMMENDATIONS]` | quality-rubric.md §6 R8 |
| **R9** | Evidence Impartiality (reformulated D10) | Conclusion strength proportional to findings evidence; STEELMAN/DISSENT exempt | T3 (judge on `[FINDINGS]` only; question = "proportional?", not "neutral?") | Medium | `[FINDINGS]` only | quality-rubric.md §6 R9 |
| **R10** | Epistemic Scope Honesty (D11+D12 merged) | Specific exclusion AND specific blind spot — both required, no boilerplate | T1 (BOTH components) + T3 (blind spot quality) | High | Full document | quality-rubric.md §6 R10 |
| **R11** | Scenario Coverage | Differentiated implications, trigger conditions; deterministic-domain guard (Req-E) | T1 (differentiated implications + guard) + T2 (scenario quality) | High | L2 main body | quality-rubric.md §6 R11 |
| **R12** | Internal Consistency | Premises in findings not denied in conclusions | T1 (direct contradiction detection) + T3 (implicit contradiction) | High | Full document | quality-rubric.md §6 R12 |

**R13 — DEFERRED.** Per **SQ-3** + quality-rubric.md §6 R13 row, R13 Evidence Sourcing is **not present in the Stage 5 gate set**. See §6.6 below for the deferral rationale and the Stage 6 re-admission trigger.

Each row in this catalog has a one-to-one corresponding `GateEvaluator` implementation in `praxis.kernel.mac.gates.r1` through `praxis.kernel.mac.gates.r12`. Murat's 5.2 test plan must verify a structural property: the directory `praxis/kernel/mac/gates/` contains **exactly 12** gate evaluator modules, named `r1.py` through `r12.py`. A 13th file is a test failure unless §13 R13 re-admission has happened.

### §6.2 Section-Aware Gate Router (Req-B)

Per **Req-B** (quality-rubric.md §7), the Cycle 3 gate evaluation pass MUST NOT apply all gates to the full document. The Quality Gate Router parses the producer's output for Req-A section labels and routes each gate to the appropriate substring(s).

```python
# praxis/kernel/mac/router.py

from typing import Mapping
from pydantic import BaseModel

class SectionRoute(BaseModel):
    gate_id: str
    section_keys: tuple[str, ...]   # which Req-A labels feed this gate

# Frozen routing table per quality-rubric.md §7 Req-A label table
GATE_SECTION_ROUTES: Mapping[str, SectionRoute] = {
    "R1":  SectionRoute(gate_id="R1",  section_keys=("FULL",)),
    "R2":  SectionRoute(gate_id="R2",  section_keys=("RECOMMENDATIONS",)),
    "R3":  SectionRoute(gate_id="R3",  section_keys=("FULL",)),
    "R4":  SectionRoute(gate_id="R4",  section_keys=("STEELMAN",)),
    "R5":  SectionRoute(gate_id="R5",  section_keys=("DISSENT",)),
    "R6":  SectionRoute(gate_id="R6",  section_keys=("L1",)),
    "R7":  SectionRoute(gate_id="R7",  section_keys=("L2",)),
    "R8":  SectionRoute(gate_id="R8",  section_keys=("RECOMMENDATIONS",)),
    "R9":  SectionRoute(gate_id="R9",  section_keys=("FINDINGS",)),
    "R10": SectionRoute(gate_id="R10", section_keys=("FULL",)),
    "R11": SectionRoute(gate_id="R11", section_keys=("L2",)),
    "R12": SectionRoute(gate_id="R12", section_keys=("FULL",)),
}
```

The routing table is **frozen** — Murat 5.2 includes a snapshot test that asserts byte-equality with this table. Any change to a routing assignment must be a deliberate code change reviewed by Quinn (or whoever owns the rubric in the future).

**Critical Req-B properties:**
- R6 receives `("L1",)` only — never the full document. Padding bodies cannot mask a poor exec summary, and dense exec summaries cannot be punished for verbose appendices (TRIZ-2 resolution).
- R9 receives `("FINDINGS",)` only — `[STEELMAN]` and `[DISSENT]` are **explicitly exempt** (TRIZ-3 resolution; quality-rubric.md §4 TRIZ-3 Winston action item).
- R2, R8 receive `("RECOMMENDATIONS",)` — they evaluate the decision sections, not the findings narrative.

If a producer fails to use the required labels, the router applies the post-processing fallback per benchmark-questions.md §6 Step 2: it identifies the closest structural analog (e.g., the last paragraph as `[RECOMMENDATIONS]`) and proceeds, but the absence of explicit labels is itself a signal that R1 (Epistemic Calibration) should drop a point — calibrated outputs use structured format.

### §6.3 Co-Evaluation Pairs (Req-C) + SQ-4 Resolution

Per **Req-C** (quality-rubric.md §7), two gate pairs must be evaluated jointly:

#### Pair 1: (R8, R7) — Actionability vs. Traceability

Per **SQ-4** (frame binding), the resolution is **Option (b)**: `R8_effective = min(R8_raw, R7_raw + 1)`.

**Worked example (mandatory SQ-4 test case, no_waiver):**
- `R7_raw = 2, R8_raw = 4` → `R8_effective = min(4, 2+1) = min(4, 3) = 3`; R7 is unchanged at 2.
- The composite-score effect: R8 loses 1 point because the recommendation is specific but the supporting reasoning chain is too thin for a reviewer to verify.

**Contrast with the rejected options (SQ-4 rationale):**
- **Option (a) hard cap at 3 on both:** rejected because it punishes R7 for R8's failure, distorting the gate signal — R7 is structurally distinct from R8 and should reflect what the reasoning trace actually looked like.
- **Option (c) co-failure flag instead of score modification:** rejected because composite scoring (benchmark §6 step 5) requires numeric scores; a flag would force ad-hoc post-processing in the scoring pipeline and make MAC-vs-baseline comparisons harder to interpret.
- **Option (b) — selected:** asymmetric cap on R8 only, with R7 unchanged. The signal is "actionable but not traceable" — exactly what we want to penalize without losing the R7 information.

#### Pair 2: (R5, R4) — Manufactured Dissent Detection

Per quality-rubric.md §7 Req-C: if `R5_raw >= 4` AND the dissenting positions in `[DISSENT]` do not correspond to positions referenced in the task context (per benchmark §6 Step 4 R5 Pass 2 with task context), R5 is **capped at 2**.

This requires the gate engine to perform R5 evaluation in **two passes** (matching benchmark-questions.md ADR-1 hybrid scoring):
1. **Pass 1 (blind):** R1–R4, R6–R12 evaluated without task context, scored on the output text alone.
2. **Pass 2 (with task context):** R5 ONLY, with the task context provided, applying the manufactured-dissent check.

#### Order of operations (SQ-7 ordering, binding)

The Quality Gate Engine MUST execute in **this exact order**:

1. Compute **raw** R1..R12 scores from gate evaluators (Tier 1 + Tier 2 + Tier 3 as applicable).
2. Apply Req-C co-evaluation caps using **raw** scores (R8 cap from raw R7; R5 cap from manufactured-dissent check).
3. Apply Forge-degradation penalties **last** — R7 penalty applies to `R7_effective` only and DOES NOT propagate back into the R8 cap.

Violating this order causes the SQ-7 worked example to fail: if the Forge penalty is applied first (lowering R7 to 3) and then the Req-C cap is computed (giving `R8 = min(4, 3+1) = 4`), the result LOOKS the same in this case but the principle is violated and other inputs will diverge. Murat 5.2 includes both "happy path" and "Forge-degraded" variants of the SQ-4 worked example, marked `no_waiver`.

### §6.4 Calibration Corpus (Req-D)

Per **Req-D** (quality-rubric.md §7), every Tier 3 LLM-judge gate prompt MUST embed **two calibration anchors**: one example scoring 2/5 and one example scoring 4/5, with explanations.

The anchors come from **benchmark-questions.md §5** (Gate Calibration Anchors R1–R12). The MAC ships with these anchors hard-coded into the gate evaluator modules — the Stage 5 build pipeline reads `benchmark-questions.md` §5, parses each pair, and writes them into `praxis/kernel/mac/gates/calibration_anchors.py` at build time. The build script is part of the Stage 5 release process.

Anchor data structure:

```python
# praxis/kernel/mac/gates/calibration_anchors.py
# AUTO-GENERATED from benchmark-questions.md §5 — DO NOT EDIT BY HAND

from typing import Mapping

class CalibrationAnchor(BaseModel):
    gate_id: str
    score_2_example: str
    score_2_explanation: str
    score_4_example: str
    score_4_explanation: str

CALIBRATION_ANCHORS: Mapping[str, CalibrationAnchor] = {
    "R1": CalibrationAnchor(
        gate_id="R1",
        score_2_example=(
            "European expansion is the right move for your company given your "
            "strong product-market fit and the growing EU AI services market "
            "projected to reach €40B by 2030."
        ),
        score_2_explanation="inference stated as fact; market projection unanchored; assertion masquerading as conclusion",
        score_4_example=(
            "Based on the two EU inbound leads (weak demand signal — inference, "
            "not validation) and the EU AI services market projections (third-party "
            "projection with ±30% uncertainty range), our assessment — which we "
            "treat as a reasoned recommendation, not a forecast — is that expansion "
            "readiness is not yet confirmed."
        ),
        score_4_explanation="claims labeled by basis; uncertainty quantified; conclusion proportional",
    ),
    # ... R2 through R12 follow the same shape, drawn from benchmark-questions.md §5
}
```

**Stability requirement:** the calibration anchors are part of the Stage 5 release; they MUST NOT change between MAC versions without a deliberate revision and re-baselining of the benchmark scores (otherwise the pre-sales comparison becomes meaningless). The build script verifies a SHA256 hash of `benchmark-questions.md` §5 against a recorded value; any mismatch is a build failure.

The judge prompt template that consumes these anchors looks like (canonical fragment, ships with the release):

```
You are evaluating R{n} ({gate_name}) on a 1-5 scale per the rubric.

Calibration anchors for this gate:
- Score 2/5 example: "{score_2_example}"
  Why score 2: {score_2_explanation}
- Score 4/5 example: "{score_4_example}"
  Why score 4: {score_4_explanation}

The output to evaluate (section: {section_key}):
"""
{section_text}
"""

Return JSON: {"score": <int 1-5>, "rationale": "<one sentence>"}
```

### §6.5 Domain Guard Conditions (Req-E) + SQ-5 Constraint

Per **Req-E** (quality-rubric.md §7), the Quality Gate Engine MUST apply task-type guards before evaluating R5 and R11:

- **R5 guard:** if `domain_class == DomainClass.CONSENSUS`, R5 is **suspended** (`GateScore.suspended=True`); the analysis passes if it explicitly notes the consensus, and the absence of a `[DISSENT]` section is not penalized.
- **R11 guard:** if `domain_class == DomainClass.DETERMINISTIC` OR `DomainClass.BINARY`, R11 is **suspended**; a note is added to the `GateScore.rationale` saying scenarios don't apply to this domain.

**SQ-5 constraint:** the guard mapping is keyed on the frozen `DomainClass` enum (§3.4) and **cannot accept arbitrary domain strings**. Workflow templates (Stage 6) may override which guards activate per `DomainClass` value — for example, a workflow template can decide that R5 should suspend for both `CONSENSUS` and `DIAGNOSTIC` (because diagnostic problems often have a single hypothesis under consideration). But the template **cannot** introduce a sixth `DomainClass` value or define a new enum; that requires a Stage 5 architecture revision.

```python
# praxis/kernel/mac/gates/guards.py

from praxis.kernel.mac.task import DomainClass

# Default guard mapping — workflow templates may override
DEFAULT_GUARD_MAP: dict[DomainClass, frozenset[str]] = {
    DomainClass.CONTESTED:     frozenset(),                  # no suspensions
    DomainClass.CONSENSUS:     frozenset({"R5"}),            # R5 suspended
    DomainClass.DETERMINISTIC: frozenset({"R11"}),           # R11 suspended
    DomainClass.BINARY:        frozenset({"R11"}),           # R11 suspended
    DomainClass.DIAGNOSTIC:    frozenset(),                  # no suspensions (default)
}

def gates_suspended_for(
    domain_class: DomainClass,
    workflow_override: dict[DomainClass, frozenset[str]] | None = None,
) -> frozenset[str]:
    if workflow_override and domain_class in workflow_override:
        return workflow_override[domain_class]
    return DEFAULT_GUARD_MAP[domain_class]
```

Suspended gates emit `GateScore(gate_id=..., suspended=True, raw_score=0, effective_score=0, ...)` and are excluded from composite scoring (their weight × score contribution is zero, but the denominator also excludes them, so the percentage is unaffected — see §9 composite formula caveat).

### §6.6 Tier Budget Allocation + R13 Deferral Rationale

Each gate evaluator runs through up to three tiers (see §6.1 catalog). Tier costs are roughly:

- **Tier 1** (rule-based + presence checks): negligible — pure Python, no LLM call, sub-millisecond
- **Tier 2** (retrieval comparison): one Memory `retrieve_*` call per gate; depends on Memory cache hit rate
- **Tier 3** (LLM-judge): one judge LLM call per (gate, output) pair; the dominant cost

For a 3-baseline benchmark run (vanilla / enhanced / MAC) with 12 gates × 10 questions × 3 baselines, Tier 3 alone is **360 LLM judge calls**. We have budgeted this against `DEFAULT_MAC_BUDGET.max_tokens` per deliberation; benchmark runs explicitly allocate a 10× budget per run (per benchmark-questions.md §6 Step 1).

**Tier ordering:** evaluators short-circuit. If Tier 1 fails (e.g., R10 has no scope declaration at all → score 1), Tier 2 and Tier 3 are skipped — no need to consult Memory or invoke the judge. This is a meaningful cost optimization and is enforced in the gate evaluator base class.

**R13 deferral — MAC.OQ-7 — SQ-3 binding:**

Per **SQ-3**, R13 Evidence Sourcing is **deferred to Stage 6**. Two-sentence rationale:

> Stage 5 MAC agents operate from training knowledge (no retrieval-augmented generation with source access in Stage 5 scope), so penalizing the absence of source citations creates systematic false positives on every output. R13 is admitted at Stage 6 if and only if Studio workflow templates elicit retrieval-grounded analysis with source attribution as a primary output contract.

The Stage 6 re-admission trigger is recorded in §13 below. R13 has no implementation in Stage 5 — `praxis/kernel/mac/gates/r13.py` does not exist, and Murat's structural test (`exactly 12 gate evaluator modules`) enforces this absence.

### §6.7 Quality Gate Engine Public Surface

```python
# praxis/kernel/mac/engine.py

class QualityGateEngine:
    """Cycle 3 verifier. Stateless across calls."""

    def __init__(
        self,
        gate_registry: "GateRegistry",     # 12 gate evaluator instances
        memory: Memory,                    # for Tier 2 retrieval
        cost_tracker: CostTracker,         # judge-call cost attribution
        clock: Clock,
    ) -> None: ...

    async def evaluate(
        self,
        producer_output: ProducerOutput,
        reviewer_critique: ReviewerCritique,
        task: TaskInput,
        domain_class: DomainClass,
        workflow_guard_override: dict[DomainClass, frozenset[str]] | None = None,
        forge_degraded: bool = False,
    ) -> dict[str, GateScore]: ...
    """Returns {gate_id: GateScore} for all 12 gates.

    Order of operations (SQ-7 binding):
    1. Compute raw scores R1..R12 (Tier 1+2+3 per evaluator)
    2. Apply Req-C caps using RAW R7 (R8 cap; R5 manufactured-dissent cap)
    3. Apply Forge-degradation penalty to R7 LAST (if forge_degraded=True)
    4. Apply Req-E suspensions per gates_suspended_for(domain_class)
    """
```

The dict-of-GateScore return value flows back into the Iteration Controller, which uses `effective_score` to decide PASS/FAIL for backtracking and then writes the full dict into `state.cycle_3_gate_scores`.

---

## §7. Information Asymmetry Router

### §7.1 Req-F Reviewer Elicitation Subsection

Per **Req-F** (quality-rubric.md §7), **information hiding alone is insufficient** for R4 improvement. The Information Asymmetry Router MUST ensure reviewer agents are explicitly prompted to:

1. **Independently construct** what they consider the strongest counterargument to the producer's main conclusion — BEFORE reading the producer's `[STEELMAN]` section
2. **Then read** the producer's `[STEELMAN]` section
3. **Then assess the gap** — what did the independent steelman include that the producer missed?

This is the binding architectural commitment that justifies the MAC's R4 differentiation claim. Without Req-F, R4 collapses to a presence-and-quality check that an enhanced single-agent prompt could satisfy (benchmark-questions.md §4 Persona 3 acknowledged this gap).

#### Req-F Reviewer Prompt Template (canonical)

```
You are a reviewer agent. You will receive a strategic analysis output and your
job is to evaluate the quality of its steelman counterarguments.

STEP 1 — Independent Steelman Construction (REQUIRED FIRST):
Before reading the analysis, what is the strongest counterargument to the main
recommendation in this task? The task is:

{task.raw_prompt}
{task.customer_context}

You have NOT yet seen the analysis. Construct your independent steelman now.
Your steelman should be the version of the opposing position that a knowledgeable
holder of that view would recognize as their best argument — not a strawman.

Write your independent steelman below (≥150 words):
[REVIEWER WRITES INDEPENDENT STEELMAN]

STEP 2 — Read the analysis output:
{producer_output.full_text}

STEP 3 — Compare:
- What did your independent steelman include that the analysis's [STEELMAN]
  section missed?
- What did the analysis's [STEELMAN] section include that you did not?
- Is the gap material to the recommendation?

Write your assessment below.
```

The reviewer's STEP 1 output is captured separately in the `ReviewerCritique` model and is fed to the Quality Gate Engine for R4 scoring — the Engine compares the reviewer's independent steelman to the producer's `[STEELMAN]` section to compute the R4 raw score per the quality-rubric.md §8 R4 score-4/5 definition ("gap between independently-generated steelman and included steelman is small/negligible").

```python
# praxis/kernel/mac/asymmetry.py

class ReviewerCritique(BaseModel):
    model_config = ConfigDict(frozen=True)
    reviewer_id: str
    independent_steelman: str        # REQUIRED — Req-F STEP 1 output
    comparison_notes: str            # Req-F STEP 3 output
    raised_concerns: tuple[str, ...] # other concerns from reading the output
```

### §7.2 Binding to Runtime §4.1 Proxies

The actual mechanical enforcement of information asymmetry is owned by Runtime §4.1 (`ProducerMemoryProxy` / `ReviewerMemoryProxy` type-level partitioning, asymmetry §9.0 "AttributeError at the Python interpreter level" guarantee). The MAC does **not** re-implement asymmetry; it consumes it.

Concretely, when the §5 Phase Runner spawns Cycle 1 producers and Cycle 2 reviewers, it uses the Runtime AgentSpawner with the appropriate `AgentRole` enum value:

```python
# praxis/kernel/mac/runner.py — inside _run_produce_phase
producer_handle = await self.spawner.spawn(
    agent_id="mac-producer",
    role=AgentRole.PRODUCER,           # Runtime §4.1.5 — receives ProducerMemoryProxy
    tenant_id=self.deployment.tenant_id,
    budget=phase_budget,
)

# inside _run_review_phase
reviewer_handle = await self.spawner.spawn(
    agent_id=f"mac-reviewer-{i}",
    role=AgentRole.REVIEWER,           # Runtime §4.1.5 — receives ReviewerMemoryProxy
    tenant_id=self.deployment.tenant_id,
    budget=phase_budget,
)
```

The Spawner's `_construct_memory_proxy` is the single point of proxy creation across all of Praxis (runtime/architecture.md §4.1.5, line 1012 "single grep target"). The MAC does NOT bypass this — it uses the Spawner exactly as a normal caller does. Murat 5.2 verifies that no MAC code path imports `ProducerMemoryProxy` or `ReviewerMemoryProxy` directly (grep test); only `AgentSpawner.spawn()` may construct them.

### §7.3 Information Hiding — What the Reviewer Sees and Does Not See

Per Runtime §9.1 (Layer 1 + Layer 2 enforcement):

| What the reviewer can see | What the reviewer cannot see |
|---|---|
| The producer's final output text (the `[FINDINGS]` / `[RECOMMENDATIONS]` / `[STEELMAN]` / `[DISSENT]` / `[SCENARIOS]` sections) | The producer's reasoning trace (the chain-of-thought, intermediate tool results, deliberation log) |
| The original task input (TaskInput, customer_context) | The producer's bus events (Layer 2 communication-bus filtering — runtime §7.5) |
| Memory results from `store_decision` and `flag_and_quarantine` (the only ReviewerMemoryProxy methods) | Memory results from `retrieve_*` (NOT on `ReviewerMemoryProxy` — `AttributeError`, runtime §4.1.3 line 957) |

**The structural guarantee** (runtime §9.0 "the punchline"): a reviewer agent that calls `retrieve_similar_tasks` raises `AttributeError: 'ReviewerMemoryProxy' object has no attribute 'retrieve_similar_tasks'` at the Python interpreter level. There is no fallback, no allowlist exception, no "trusted reviewer" mode. The MAC inherits this guarantee and does not weaken it.

### §7.4 Aggregating Multiple Reviewers

When `cycle_2_review` spawns N parallel reviewers (per §5.4), the Phase Runner gathers N `ReviewerCritique` objects. The Quality Gate Engine consumes them as follows:

- **R4 (Steelman):** For each reviewer's `independent_steelman`, compute the gap to producer's `[STEELMAN]`. R4 raw score is the **MAX** across reviewers — if any reviewer's independent steelman matches the producer's, R4 is 4 or 5; if all reviewers found gaps, R4 is 2 or 3.
- **R5 (Dissent):** Each reviewer's `comparison_notes` and `raised_concerns` are checked for whether the producer's `[DISSENT]` section matches positions the reviewers would recognize. Manufactured-dissent detection (§6.3 Pair 2) considers all reviewers jointly.
- **All other gates:** N reviewers do not affect the score; they're scored against the producer's output directly.

The aggregation logic is in `praxis/kernel/mac/engine.py` and is unit-tested with N=1, N=2, N=3 cases.

### §7.5 The Symmetric Asymmetry Boundary

A key subtlety: the **producer** has full Memory access (to seed its analysis from `retrieve_similar_tasks`), but the **reviewer** does NOT. This asymmetry is intentional — the reviewer's value comes from being **uncontaminated** by retrieved precedents. If the reviewer also retrieved similar tasks, it would re-anchor on the same prior knowledge that the producer used, defeating the asymmetry mechanism.

The producer's retrieved memory is NOT shared with the reviewer (Layer 2 bus filtering enforces this — runtime §7.5). The reviewer sees only the producer's final output, not the producer's retrieval history.

---

## §8. Cross-Session Learning Loop

### §8.1 MAC.OQ-6 Bootstrap Protocol — SQ-6 RESOLVED (2026-04-14)

#### SQ-6 Pre-Write Verification Result (preserved for record)

Per the SQ-6 binding requirement, this section reports whether the Memory schema (memory/architecture.md §7 Storage Schema) has a `metadata` JSONB column on the `experience_entries` table.

**Verification performed:** Grep of `memory/architecture.md` §7.1 Postgres Tables (lines 922–1054), specifically the `CREATE TABLE experience_entries` definition (lines 976–993).

**Result: NO `metadata` JSONB column exists on `experience_entries`.**

The columns present are: `entry_id`, `tenant_hash`, `task_signature_hash`, `task_signature` (JSONB — but this is reserved for the task signature itself, not arbitrary metadata), `approach_summary`, `quality_score`, `quality_confidence`, `cost_usd`, `reasoning_trace_ref`, `state`, `captured_at`, `embedding`, `embedding_version`. There is no general-purpose JSONB metadata column.

#### Ratification Decision (2026-04-14)

**Option Y — sidecar table `mac_bootstrap_metadata` — is the RATIFIED implementation path.** Stage 3 Memory schema remains frozen; `mac_bootstrap_metadata` is a new MAC-owned table, NOT a modification to `experience_entries`. The alternative (Option X — adding a `metadata` JSONB column to `experience_entries`) was considered and rejected; see §13.2 Rejected Alternatives for the five-point rationale.

Stage 5.3 Amelia implements the migration `0001_mac_bootstrap_metadata` as a MAC-owned schema artifact, consistent with Pi-Mono / Memory / Runtime each owning their own schemas.

#### Option Y Design (RATIFIED PATH)

The bootstrap loader writes each gold-standard record via the Memory facade (into `experience_entries`) AND its corresponding metadata into the sidecar table at the same logical write boundary:

```sql
-- New migration: praxis/kernel/mac/migrations/0001_mac_bootstrap_metadata.py
-- Owned by MAC, NOT by Memory — keeps Memory schema unchanged.

CREATE TABLE mac_bootstrap_metadata (
    experience_entry_id  CHAR(26) PRIMARY KEY REFERENCES experience_entries(entry_id),
    tenant_hash          CHAR(64) NOT NULL,
    source               TEXT     NOT NULL,                  -- 'benchmark_gold_standard'
    bootstrap            BOOLEAN  NOT NULL DEFAULT TRUE,
    benchmark_question_id TEXT    NOT NULL,                  -- 'Q1'..'Q10'
    calibration_anchor_score REAL NOT NULL,                  -- 4.2
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_hash, benchmark_question_id)
);

CREATE INDEX ix_mac_bootstrap_tenant ON mac_bootstrap_metadata (tenant_hash);
```

```python
# praxis/kernel/mac/bootstrap.py — Ratified path (Option Y sidecar)

class BootstrapLoader:
    def __init__(
        self,
        memory: Memory,
        sidecar: "MacBootstrapMetadataStore",   # writes mac_bootstrap_metadata
        gold_standards_path: str,
    ) -> None: ...

    async def load_gold_standards(self, tenant_id: str) -> int:
        """Writes 10 records into experience_entries via Memory facade,
        AND writes the corresponding metadata into the sidecar table."""
        inserted = 0
        for record in self._parse_gold_standards():
            outcome_record = await self.memory.store_task_outcome(
                tenant_id=tenant_id,
                task=record.task_signature,
                outcome=TaskOutcome(
                    quality_score=4.2,
                    quality_confidence=0.85,
                    cost_usd=0.0,
                    reasoning_trace=record.gate_indicators,
                    approach_summary=record.checklist_summary,
                    dissents=record.dissent_examples,
                ),
            )
            await self.sidecar.upsert(
                experience_entry_id=outcome_record.entry_id,
                tenant_hash=record.tenant_hash,
                source="benchmark_gold_standard",
                bootstrap=True,
                benchmark_question_id=record.q_id,
                calibration_anchor_score=4.2,
            )
            inserted += 1
        return inserted

    async def is_bootstrap_entry(self, entry_id: str) -> bool:
        """Helper for retrieval scoring — looks up the sidecar."""
        return await self.sidecar.exists(experience_entry_id=entry_id)
```

**Retrieval-time join:** When the §5 Cycle 1 phase calls `memory.retrieve_similar_tasks`, the result includes raw `experience_entries`. To filter or annotate bootstrap entries, the MAC's learning loop wraps the retrieval call with a sidecar lookup:

```python
# praxis/kernel/mac/learning.py

async def retrieve_with_bootstrap_annotation(
    memory: Memory,
    sidecar: "MacBootstrapMetadataStore",
    tenant_id: str,
    signature: TaskSignature,
) -> "AnnotatedRetrievalResult":
    raw = await memory.retrieve_similar_tasks(
        tenant_id=tenant_id,
        signature=signature,
        top_k=5,
        min_similarity=0.75,
    )
    bootstrap_ids = await sidecar.bootstrap_entries_in(
        [hit.entry_id for hit in raw.hits]
    )
    return AnnotatedRetrievalResult(
        hits=raw.hits,
        bootstrap_entry_ids=bootstrap_ids,
    )
```

**Properties of the ratified Option Y path:**
- Extra SQL query per retrieval is a small constant cost, and can be batched via the `bootstrap_entries_in([...])` helper shown above.
- Memory schema remains untouched — preserves Stage 3 ratification (2026-04-13) without reopening.
- MAC owns its own schema artifact (`0001_mac_bootstrap_metadata`), consistent with Pi-Mono / Memory / Runtime each owning their own schemas.
- Sidecar is reversible — dropping `mac_bootstrap_metadata` is a MAC-local change with no blast radius into the hot `experience_entries` table.
- Inline-read advantage of a `metadata` column would have been a premature optimization: bootstrap reads fire on MAC cold-start, not on the Cycle 1 hot path.

**Ratification:** Stage 5.1 is ratified with Option Y as the binding bootstrap implementation path (2026-04-14). Option X (direct JSONB column on `experience_entries`) is explicitly rejected — see §13.2 Rejected Alternatives for the rationale. Stage 3 Memory schema remains frozen; Amelia (Stage 5.3) implements the `mac_bootstrap_metadata` migration as a MAC-owned artifact.

### §8.2 Bootstrap Records — Source and Format

The 10 gold-standard records are derived from **benchmark-questions.md §8** (lines 532–547), which provides the task signature table:

| Q | Task Signature | Domain | DomainClass mapping |
|---|---|---|---|
| Q1 | `pricing-model-change + SaaS + revenue-model-migration` | Revenue strategy | `CONTESTED` |
| Q2 | `capital-allocation + runway + raise-vs-extend` | Financing | `CONTESTED` |
| Q3 | `make-vs-buy + capability-gap + integration-risk` | Strategic decision | `CONTESTED` |
| Q4 | `strategic-alliance + exclusivity + optionality-cost` | Partnership | `CONTESTED` |
| Q5 | `defensibility + commoditization-threat + moat-building` | Competitive strategy | `CONTESTED` |
| Q6 | `competitive-pricing + race-to-bottom + differentiation` | Competitive response | `CONTESTED` |
| Q7 | `geographic-expansion + readiness + entity-specific-risk` | Growth strategy | `CONTESTED` |
| Q8 | `platform-commoditization + next-layer + existential` | Strategic repositioning | `CONTESTED` |
| Q9 | `gtm-model + enterprise-vs-smb + runway-constraint` | Go-to-market | `CONTESTED` |
| Q10 | `diverging-metrics + hypothesis-generation + root-cause` | Operational diagnosis | `DIAGNOSTIC` |

Each record's `approach_summary` is taken from the question's "Gold Standard Required Elements" checklist in benchmark-questions.md §2, and `reasoning_trace` is constructed from the "Gate-specific indicators" subsection.

The build script `praxis/kernel/mac/scripts/build_bootstrap_corpus.py` reads `benchmark-questions.md` §2 + §5 + §8 and produces a `gold_standards.json` fixture that the BootstrapLoader consumes at first-deployment time.

### §8.3 Cross-Session Promotion Loop (Memory §6.3 + §6.4 binding)

Per memory/architecture.md §6.3 (admission thresholds) and §6.4 (tentative→confirmed promotion), the MAC consumes the Memory facade's promotion logic via the `mac.publish` / `mac.reuse_successful` / `mac.backfill` named contract (memory/architecture.md §6.6, lines 913–915).

```python
# praxis/kernel/mac/learning.py

class LearningLoop:
    """Owns the §8 cross-session learning loop. Wraps Memory's named MAC contract."""

    def __init__(self, memory: Memory) -> None: ...

    async def publish(
        self,
        result: DeliberationResult,
        tenant_id: str,
    ) -> None:
        """Calls Memory.mac.publish() per memory/architecture.md §6.6 line 913.

        memory.mac.publish(task_signature, outcome, quality_score, quality_confidence)

        Memory's admission gate evaluates:
        - quality_score >= 0.8 AND quality_confidence >= 0.6 → CONFIRMED
        - 0.5 <= quality_score < 0.8 → TENTATIVE
        - quality_score < 0.5 → REJECTED (not written)

        Per memory §6.3 admission thresholds.
        """
        outcome = TaskOutcome(
            quality_score=result.composite_score / 100.0,   # benchmark §6 step 5: 0..1 normalized
            quality_confidence=self._compute_confidence(result),
            cost_usd=result.cost_usd,
            reasoning_trace=self._format_reasoning_trace(result),
            approach_summary=self._summarize_approach(result),
            dissents=self._extract_dissents(result),
        )
        # Memory's facade routes this through admission gating
        await self.memory.store_task_outcome(
            tenant_id=tenant_id,
            task=result.task_signature,
            outcome=outcome,
        )

    async def mark_reused_successfully(
        self,
        tenant_id: str,
        entry_id: str,
        downstream_quality: float,
    ) -> None:
        """Calls Memory.mac.reuse_successful() per memory §6.6 line 914.

        Used when a Cycle 1 retrieval seed contributed to a high-scoring
        downstream deliberation — promotes the seed entry from TENTATIVE
        toward CONFIRMED per memory §6.4.
        """
        ...
```

**Confidence computation:** the MAC's `_compute_confidence` derives `quality_confidence` from gate score variance — if all 12 gates score 4-5 with low variance, confidence is high (~0.9); if there's wide spread (some 5s, some 2s), confidence is lower (~0.6). The exact formula:

```
quality_confidence = 1.0 - (stddev(gate_effective_scores) / 4.0)   # capped at [0.4, 0.95]
```

This maps directly to memory §6.3's two-axis admission: high score + high confidence → CONFIRMED; high score + low confidence → TENTATIVE; low score → REJECTED.

### §8.4 Backfill — One-Time MAC First-Ship Job

Per memory/architecture.md §6.6 line 915: `mac.backfill()` is a **one-time job** at first MAC ship that re-scores existing TENTATIVE entries (Memory Req #48). This is a named deliverable of the Stage 5 handoff contract.

```python
# praxis/kernel/mac/backfill.py

class BackfillJob:
    """One-time backfill of existing TENTATIVE experience entries.

    Run ONCE at MAC first deployment. Subsequent runs are no-ops (idempotent
    via a marker row in mac_bootstrap_metadata or equivalent).
    """

    async def run(self, tenant_id: str) -> BackfillReport:
        # 1. Query Memory for all TENTATIVE entries
        # 2. For each, run a lightweight quality re-scoring pass
        # 3. Update entries via Memory.mac.reuse_successful() if downstream_quality high
        # 4. Emit telemetry: mac.backfill.completed
        ...
```

The backfill job is invoked manually as part of the Stage 5 deployment runbook (Stage 7 POV Harness owns the runbook). It is NOT invoked automatically on every MAC start — that would re-run the backfill on every restart and break idempotency.

---

## §9. Evaluation Harness

### §9.1 Purpose

The Evaluation Harness is the **measurement substrate** that produces the +15-25% claim. It runs the MAC against the 3 baseline conditions on the 10 benchmark questions (benchmark-questions.md §2) and produces a comparative score table.

This section is the section where Murat (5.2) and Amelia (5.3) MUST trust verbatim citations to benchmark-questions.md. Do NOT invent new questions, do NOT reweight gates, do NOT change the scoring protocol.

### §9.2 The 10 Benchmark Questions (verbatim from benchmark-questions.md §2)

The Stage 5 Evaluation Harness consumes **exactly these 10 questions**, with **no substitutions**:

| Q | Title | Source |
|---|---|---|
| Q1 | Pricing Strategy Transition | benchmark-questions.md §2 Q1 |
| Q2 | Capital Strategy Under Uncertainty | benchmark-questions.md §2 Q2 |
| Q3 | Acquire vs. Build Decision | benchmark-questions.md §2 Q3 |
| Q4 | Strategic Partnership With Exclusivity | benchmark-questions.md §2 Q4 |
| Q5 | Moat Building Before Commoditization | benchmark-questions.md §2 Q5 |
| Q6 | Competitive Response to Aggressive Pricing | benchmark-questions.md §2 Q6 |
| Q7 | Market Expansion Timing | benchmark-questions.md §2 Q7 |
| Q8 | Platform Threat Response | benchmark-questions.md §2 Q8 |
| Q9 | GTM Model Selection | benchmark-questions.md §2 Q9 |
| Q10 | Diagnostic (Diverging Metrics) | benchmark-questions.md §2 Q10 |

The Evaluation Harness loads these from `benchmark-questions.md` §2 at run time (parses the markdown into a structured fixture). Murat's 5.2 test plan must include a snapshot test on the parsed fixture — a SHA256 of the parsed structure that fails if anyone edits §2 without intending to.

### §9.3 The 3 Baseline Conditions (verbatim from benchmark-questions.md §6 Step 1)

```python
# praxis/kernel/mac/eval/baselines.py

BASELINE_VANILLA_PROMPT = (
    "You are a strategic advisor. A client asks: {question}. "
    "Provide your analysis."
)

BASELINE_ENHANCED_PROMPT = (
    "You are a strategic advisor. A client asks: {question}. "
    "In your analysis: "
    "(a) explicitly steelman the strongest opposing recommendation; "
    "(b) present any significant minority views from different stakeholder perspectives; "
    "(c) show your reasoning chain explicitly."
)

# MAC baseline = standard MAC task intake via Task Interpreter; no special instructions
```

The three baselines are run **independently** with no cross-contamination. Each baseline's output is post-processed per benchmark-questions.md §6 Step 2 (label fallback if the output doesn't use Req-A labels — the absence of labels feeds back into R1 scoring).

### §9.4 Top-5 Weighting (OQ-5 — verbatim from benchmark-questions.md §7)

Per **benchmark-questions.md §7** (OQ-5 resolved), the top 5 gates are weighted 2× and the remaining 7 are weighted 1× for the **first** Stage 5.6 run. The total weight is 17 units.

| Gate | Weight | Why 2× |
|---|---|---|
| R1 Epistemic Calibration | **2×** | Universal; MAC structural advantage |
| R2 Question Fidelity | **2×** | Universal; MAC structural advantage |
| R4 Steelman Completeness | **2×** | Primary MAC differentiation gate |
| R5 Dissent Preservation | **2×** | Anti-conformity gate; MAC structural advantage |
| R7 Reasoning Traceability | **2×** | Required for Cycle 3 verification |
| R3, R6, R8, R9, R10, R11, R12 | 1× each | Standard weight |

**Composite formula** (verbatim from benchmark-questions.md §6 Step 5):

```
composite_score = Σ(gate_score × gate_weight) / (17 × 5) × 100
```

**Suspended-gate caveat:** When Req-E (§6.5) suspends a gate, the suspended gate contributes `0` to both numerator (no score × weight) AND denominator (its weight is excluded from the 17 total). The corrected denominator becomes `(17 - suspended_weight) × 5`. This keeps the percentage on the same 0-100 scale regardless of how many guards fire.

```python
def composite_score(gate_scores: dict[str, GateScore], weights: dict[str, int]) -> float:
    numerator = sum(
        s.effective_score * weights[s.gate_id]
        for s in gate_scores.values()
        if not s.suspended
    )
    active_weight = sum(
        weights[s.gate_id]
        for s in gate_scores.values()
        if not s.suspended
    )
    if active_weight == 0:
        return 0.0
    return (numerator / (active_weight * 5)) * 100.0
```

**Update protocol** (per benchmark-questions.md §7): after Stage 5.6's first run, observe which gates show the largest variance between MAC and both baselines. If R4 and R5 show the largest differential (expected), the top-5 weighting is validated. If unexpected gates differ most, weights are revised before subsequent evaluations. The weights are NOT updated mid-run — re-weighting requires a deliberate Stage 5.6.1 micro-revision.

### §9.5 ADR-1 Hybrid Scoring (verbatim from benchmark-questions.md §3 ADR-1)

The Evaluation Harness implements ADR-1 Option C (Hybrid blind/open) verbatim:

**Pass 1 — Blind Scoring (R1–R4, R6–R12):**
1. Assign random IDs to the three outputs (`Output-Kappa`, `Output-Lambda`, `Output-Mu`)
2. For each gate R1–R4 and R6–R12, run the LLM-judge with:
   - Gate definition from quality-rubric.md §6
   - Calibration anchors from benchmark-questions.md §5
   - Output section(s) per Req-B routing (§6.2 above)
3. Record scores on 1–5 for each (gate, output) pair
4. R4 runs the **two-step protocol** per Req-F (§7.1 above)

**Pass 2 — R5 Scoring with Task Context:**
1. Provide judge with: (a) task context (customer situation + question), (b) all three outputs with random IDs
2. Evaluate R5 for each output
3. Apply Req-C R5/R4 co-evaluation (manufactured-dissent cap)

```python
# praxis/kernel/mac/eval/scoring.py

class HybridScoringHarness:
    async def score_output(
        self,
        output: ProducerOutput,
        random_id: str,
        question: BenchmarkQuestion,
    ) -> dict[str, GateScore]:
        # Pass 1: blind R1-R4, R6-R12
        blind_scores = await self.gate_engine.evaluate(
            producer_output=output,
            reviewer_critique=None,                 # blind
            task=None,                              # blind
            domain_class=DomainClass.CONTESTED,     # default during blind pass
            forge_degraded=False,
        )
        blind_subset = {k: v for k, v in blind_scores.items() if k != "R5"}

        # Pass 2: R5 with task context
        r5_with_context = await self.gate_engine.evaluate_single(
            "R5",
            producer_output=output,
            reviewer_critique=None,
            task=question.to_task_input(),          # task context provided
            domain_class=question.domain_class,     # actual domain class
        )

        return {**blind_subset, "R5": r5_with_context}
```

### §9.6 ADR-3 A4 Validation (verbatim from benchmark-questions.md §3 ADR-3)

The Evaluation Harness implements ADR-3 Option B (Single evaluator, simplified checklist on 3 questions):

1. Randomly select 3 questions from the 10
2. Andrey evaluates all three outputs (vanilla, enhanced, MAC) per question using the 5-question simplified checklist (benchmark-questions.md §3 ADR-3 lines 329–334)
3. Compute **Spearman correlation** between automated composite scores and Andrey's simplified-checklist totals across the 9 (output × question) evaluations
4. Report correlation in the 5.6 pre-sales report

```python
# praxis/kernel/mac/eval/validation.py

async def run_a4_validation(
    selected_questions: list[BenchmarkQuestion],   # 3 randomly selected
    outputs: dict[str, ProducerOutput],            # vanilla/enhanced/MAC per question
    automated_scores: dict[str, float],            # composite scores per output
    human_scores: dict[str, int],                  # Andrey's 5-question total per output (max 25)
) -> A4ValidationReport:
    from scipy.stats import spearmanr
    rho, p_value = spearmanr(
        [automated_scores[k] for k in sorted(automated_scores)],
        [human_scores[k] for k in sorted(human_scores)],
    )
    return A4ValidationReport(
        spearman_rho=rho,
        spearman_p=p_value,
        provisional_validation=(rho >= 0.6),       # ADR-3 line 336 threshold
        sample_size=len(automated_scores),
    )
```

**Spearman ρ ≥ 0.6 threshold** is the ADR-3 line 336 binding criterion: a correlation of 0.6 or higher provides "provisional validation that rubric scores track human-judged quality." Below 0.6 is NOT a Stage 5.6 fail — it triggers a documented caveat in the pre-sales report and a Stage 6 rubric revisit.

### §9.7 N=10 Framing — Directional Demonstration, NOT Hypothesis Test

Per **benchmark-questions.md §4 Persona 1** (The Statistician's response), N=10 is **insufficient** for statistical hypothesis testing. The Stage 5.6 pre-sales report MUST characterize the result as:

> "In our benchmark evaluation of 10 diverse strategic questions, MAC scored an average of X% higher than single-agent baseline on the 12-gate quality rubric."

No p-values. No confidence intervals. No "statistically significant." This is **sales evidence**, not academic publication.

**Invalidation conditions (per R3 Falsifiability — benchmark-questions.md §4 Persona 1 last paragraph):**
- If MAC scores higher than the baseline on **fewer than 7 of 10 questions**, the differentiation claim requires revision
- If the **average improvement is below 10%**, the differentiation claim requires revision

Either invalidation forces a Stage 5.6 → Stage 5.7 retro and a stakeholder review of whether the +15-25% range is defensible.

### §9.8 Persona 2 Disclosure Mandate

Per **benchmark-questions.md §4 Persona 2** (The Practitioner's response), full disclosure is mandatory:

- All 10 individual question scores are published, not just the aggregate
- Any question where MAC underperforms the baseline is published — no cherry-picking
- The full 18-candidate matrix from §1 (selection rationale) is published in the pre-sales appendix

### §9.9 Persona 3 Acknowledgment

Per **benchmark-questions.md §4 Persona 3** (The Adversary's response), the rubric explicitly acknowledges that R4 and R5 are the gates **most susceptible to gaming** by enhanced single-agent prompting. The MAC's structural advantage on R4/R5 comes from information asymmetry generating genuinely independent analysis (Req-F), not just from presence/quality scoring.

The pre-sales report must include this acknowledgment verbatim — pretending otherwise is an over-claim that the Adversary would catch.

### §9.10 Reporting Format (from benchmark-questions.md §6 Step 7)

```
| Question | Vanilla Score | Enhanced Score | MAC Score | MAC vs Vanilla % | MAC vs Enhanced % |
|---|---|---|---|---|---|
| Q1 | … | … | … | … | … |
| … | … | … | … | … | … |
| Q10 | … | … | … | … | … |
| Average | … | … | … | … | … |
```

---

## §10. Integration Contracts

This section specifies every cross-stage seam. Each subsection includes a concrete Pydantic stub or function signature. No hand-waving — Murat will verify citations in 5.2.

### §10.1 Pi-Mono Integration

The MAC writes a `CostEvent` per cycle via `CostTracker.track_cost(LLMRequest, LLMResponse)` per the Pi-Mono Stage 1 contract (`pi-mono/pi-mono-cost-tracker-architecture.md` §3.3.9 + §4.2). Budget enforcement is **Runtime's**, NOT Pi-Mono's (per the Stage 1 architecture line 22 binding correction in the preload).

```python
# praxis/kernel/mac/integrations/pi_mono.py

from praxis.kernel.pi_mono.tracker import CostTracker
from praxis.kernel.pi_mono.models import LLMRequest, LLMResponse, CostEvent

class MacCostHook:
    """Wraps every MAC LLM call to emit a CostEvent."""

    def __init__(self, cost_tracker: CostTracker) -> None: ...

    async def emit_cycle_cost(
        self,
        cycle_id: str,
        cycle_phase: str,                  # "produce" | "review" | "gate_eval" | "publish"
        request: LLMRequest,
        response: LLMResponse,
    ) -> None:
        """Calls CostTracker.track_cost(request, response).

        track_cost emits a CostRecord to cost_records (append-only) AND
        a CostEvent to events_outbox in the same transaction (pi-mono §4.2,
        line 739: "Either both succeed or both roll back").

        This is the HOT PATH — sub-1ms amortized per pi-mono §4.2 line 751.
        Do NOT add MAC-side bookkeeping that breaks the budget.
        """
        await self._cost_tracker.track_cost(request=request, response=response)
        # Note: we do NOT add MAC dedup_keys here — see §10.3 for the Path B
        # path that handles MAC's cycle-boundary events with dedup_keys.
```

**MAC's CostEvent payload:** the `event_type` is one of `"record_created"` (every LLM call), `"record_amended"` (rare — only on reconciliation drift), or `"reconciliation_drift"` (NOT MAC-emitted; reconciliation is a Pi-Mono internal process). MAC only emits `record_created`.

**Cost attribution:** the `request_id` field on `LLMRequest` is set to a stable identifier per MAC cycle: `f"mac:{cycle_id}:{cycle_phase}:{call_seq}"`. This lets downstream cost reports filter by MAC cycle.

### §10.2 Memory Integration

The MAC uses the Memory facade (`memory/architecture.md §2.1` lines 182–270) **exclusively** — no `_internal.*` access. The contract is the named MAC three-method API per memory §6.6 lines 913–915:

```python
# praxis/kernel/mac/integrations/memory.py

from praxis.kernel.memory.facade import Memory
from praxis.kernel.memory.models import (
    TaskSignature, TaskOutcome, TaskOutcomeRecord,
    DecisionRecord, RetrievalResult,
)

class MacMemoryAdapter:
    """MAC's interface to Memory. Wraps the named MAC contract."""

    def __init__(self, memory: Memory) -> None: ...

    # Cycle 1 retrieval seed
    async def retrieve_for_cycle1(
        self,
        tenant_id: str,
        signature: TaskSignature,
    ) -> RetrievalResult:
        """Calls Memory.retrieve_similar_tasks(top_k=5, min_similarity=0.75)."""
        return await self._memory.retrieve_similar_tasks(
            tenant_id=tenant_id,
            signature=signature,
            top_k=5,
            min_similarity=0.75,
        )

    # Publish (named MAC contract — memory §6.6 line 913)
    async def publish_outcome(
        self,
        tenant_id: str,
        task_signature: TaskSignature,
        outcome: TaskOutcome,
    ) -> TaskOutcomeRecord:
        """Memory's admission gate routes via §6.3 thresholds:
        - quality_score >= 0.8 AND quality_confidence >= 0.6 → CONFIRMED
        - 0.5 <= quality_score < 0.8 → TENTATIVE
        - quality_score < 0.5 → REJECTED (raises NotAdmittedError)
        """
        return await self._memory.store_task_outcome(
            tenant_id=tenant_id,
            task=task_signature,
            outcome=outcome,
        )

    # Reuse-successful (named MAC contract — memory §6.6 line 914)
    async def mark_reuse_successful(
        self,
        tenant_id: str,
        entry_id: str,
        downstream_quality_score: float,
        downstream_principal: str,
    ) -> None:
        """Triggers memory §6.4 tentative→confirmed promotion."""
        ...   # routed via memory.mac.reuse_successful (named handle)
```

**Information asymmetry contract:** the MacMemoryAdapter is held by MAC's **producer-side** code only. Reviewer-side MAC code (the Phase Runner's `_run_review_phase`) does NOT take a MacMemoryAdapter — it takes a `ReviewerMemoryProxy` directly from the Spawner. This guarantees that MAC never gives a reviewer a back-door retrieval path.

### §10.3 Runtime Integration

The MAC consumes Runtime via:

1. **AgentSpawner** (§4.1) for spawning producers and reviewers
2. **MCPToolAdapter** (§5) for tool calls — the MAC pins to `mcp>=1.9.0` per Runtime's pyproject.toml (NOT 1.27.0 — verified via team-lead binding correction)
3. **ResourceBudget** (§4.3) — bound to every spawn
4. **Path A/B outbox absorption** (§8.1) — MAC's CostEvents and audit events flow through these

#### MCP Pin (SQ-1 binding)

Per **SQ-1**, the MAC **inherits** the Runtime MCP contract verbatim. It does NOT re-pin and does NOT add its own shape guard. Runtime §5 owns the pin (`mcp>=1.9.0` in `praxis/kernel/runtime/pyproject.toml`) and the shape guard (`verify_mcp_sdk_shape()`). The MAC imports from `praxis.kernel.runtime.mcp` and trusts the pin.

```python
# praxis/kernel/mac/integrations/runtime.py

from praxis.kernel.runtime.spawner import AgentSpawner, AgentRole, ResourceBudget
from praxis.kernel.runtime.mcp import MCPToolAdapter, verify_mcp_sdk_shape

class MacRuntimeAdapter:
    """MAC's interface to Runtime. Inherits MCP pin + shape guard from Runtime."""

    def __init__(
        self,
        spawner: AgentSpawner,
        mcp_adapter: MCPToolAdapter,       # Runtime owns the pin
    ) -> None:
        self._spawner = spawner
        self._mcp = mcp_adapter
        # Shape guard runs at Runtime boot, NOT at MAC init — we trust Runtime.

    async def spawn_producer(
        self,
        agent_id: str,
        tenant_id: str,
        budget: ResourceBudget,
    ) -> "SpawnedAgent":
        return await self._spawner.spawn(
            agent_id=agent_id,
            role=AgentRole.PRODUCER,
            tenant_id=tenant_id,
            budget=budget,
        )

    async def spawn_reviewer(
        self,
        agent_id: str,
        tenant_id: str,
        budget: ResourceBudget,
    ) -> "SpawnedAgent":
        return await self._spawner.spawn(
            agent_id=agent_id,
            role=AgentRole.REVIEWER,
            tenant_id=tenant_id,
            budget=budget,
        )
```

#### Path A vs Path B Routing — SQ-8 Binding

Per **SQ-8** (frame binding), MAC routes telemetry as follows:

- **Hot-path LLM costs (Path A):** routed through `CostTracker.track_cost` directly (§10.1). High volume; no MAC-side outbox; Pi-Mono's events_outbox handles delivery. This is the path that runs sub-1ms per pi-mono §4.2.
- **Cycle-boundary events (Path B):** routed through `Memory.audit_buffer` for cycle gate pass/fail, iteration_depth, backtrack, bootstrap hits. Lower volume; tick-drained at cycle boundaries; uses dedup keys for at-least-once semantics.

**SQ-8 dedup-key namespace constraint (binding):** every MAC-emitted Path B event MUST use a dedup key with the prefix `mac:`:

```
dedup_key = "mac:" + cycle_id + ":" + event_type + ":" + monotonic_seq
```

Examples:
- `mac:01HX...:gate_pass:0042`
- `mac:01HX...:gate_fail:0043`
- `mac:01HX...:backtrack:0044`
- `mac:01HX...:bootstrap_hit:0045`

Murat 5.2 includes a **structural test** that asserts no MAC event emits a `dedup_key` without the `mac:` prefix. The test grep target is `praxis/kernel/mac/`; any literal dedup_key construction without the `mac:` prefix fails the test.

```python
# praxis/kernel/mac/integrations/runtime.py (continued)

import itertools
from praxis.kernel.runtime.outbox import OutboxClient

class MacPathBEmitter:
    """Cycle-boundary event emitter for MAC. SQ-8 dedup namespace enforced."""

    DEDUP_PREFIX = "mac:"

    def __init__(self, outbox: OutboxClient) -> None:
        self._outbox = outbox
        self._seq_by_cycle: dict[str, itertools.count] = {}

    async def emit(
        self,
        cycle_id: str,
        event_type: str,                   # "gate_pass" | "gate_fail" | "backtrack" | "bootstrap_hit" | etc.
        payload: dict[str, str | int | float],
    ) -> None:
        seq = next(self._seq_by_cycle.setdefault(cycle_id, itertools.count(0)))
        dedup_key = f"{self.DEDUP_PREFIX}{cycle_id}:{event_type}:{seq:05d}"
        await self._outbox.enqueue(
            dedup_key=dedup_key,
            payload=payload,
        )
```

The `mac:` prefix is enforced as a literal class constant; no caller can construct a non-`mac:`-prefixed dedup_key from MAC code without modifying this constant, which is grep-locked by Murat's test.

### §10.4 Compression Integration

The MAC consumes the Compression layer **only** via the Forge F8 reasoning preservation contract (`compression/architecture.md` line 129, §3.2). It does NOT consume F-2 TONL bead encoding (deferred to Stage 6 per the preload binding).

```python
# praxis/kernel/mac/integrations/compression.py

from praxis.kernel.compression import Compressor, CompressionPolicy
from praxis.kernel.compression.results import CompressionResult

class MacCompressionAdapter:
    """MAC's interface to Compression. Consumes Forge F8 only."""

    def __init__(self, compressor: Compressor) -> None: ...

    async def compress_with_reasoning_preservation(
        self,
        payload: str,
        policy: CompressionPolicy,
    ) -> CompressionResult:
        """Calls Compressor.compact() and returns the result.

        The CompressionResult carries:
        - compressed_payload: the compacted text
        - reasoning_preserved: bool — F8 fallback flag (compression §3.2 line 576)
        - reasoning_drift_detected: bool — set on schema drift (compression §3.2)

        The MAC consumes both flags. If reasoning_preserved=False, the
        Iteration Controller §5.6 enters the Forge fallback path:
        attempt re-extraction, then if that fails, apply the SQ-7 R7 penalty.
        """
        return await self._compressor.compact(payload, policy=policy)
```

**F-2 TONL deferred:** any future MAC code that imports TONL or calls `compressor.compact_with_tonl()` is a build-time error (Murat 5.2 includes a grep test). F-2 is parked per Pipeline.md §4.7 and the Stage 4 §8.6 `enable_memory_write_compression: bool = False` parking.

---

## §11. Observability Hooks

### §11.1 Telemetry Label Cardinality Registry — SQ-2 Binding

Per **SQ-2**, the MAC owns a cardinality registry at:

```
praxis/kernel/mac/observability/telemetry_labels.py
```

This registry defines every label key that MAC events may carry, plus the bounded value set or value bound for each label. The Memory `TelemetryEvent` envelope (memory/architecture.md §9 — `praxis.kernel.memory.telemetry.TelemetryEvent`) has a generic `metric_name / metric_type / value / labels / timestamp / praxis_version / tenant_hash` shape, so all semantic information must be label-encoded.

```python
# praxis/kernel/mac/observability/telemetry_labels.py

from typing import FrozenSet, Mapping

# Every label key MAC may emit. Adding a key requires editing this file
# (which is grep-locked into Murat's tests).
ALLOWED_MAC_LABEL_KEYS: FrozenSet[str] = frozenset({
    "cycle_id",                # ULID — high cardinality but bounded by retention
    "cycle_phase",             # bounded enum (4 values)
    "gate_id",                 # bounded enum (12 values)
    "domain_class",            # bounded enum (5 values)
    "outcome",                 # bounded enum: "pass" | "fail" | "suspended"
    "backtrack_count",         # bounded int 0..1
    "bootstrap_hit",           # bounded bool
    "forge_degraded",          # bounded bool
    "tenant_hash",             # high cardinality; bounded by deployment count
    "praxis_version",          # bounded by release count
    "reviewer_count",          # bounded int 1..3
})

# Per-key bounded value sets where applicable. Unbounded keys (cycle_id, tenant_hash)
# are bounded by deployment-level retention.
ALLOWED_LABEL_VALUES: Mapping[str, FrozenSet[str]] = {
    "cycle_phase": frozenset({"interpret", "decompose", "produce", "review", "gate_eval", "publish"}),
    "gate_id": frozenset({f"R{i}" for i in range(1, 13)}),     # R1..R12 only
    "domain_class": frozenset({"contested", "consensus", "deterministic", "binary", "diagnostic"}),
    "outcome": frozenset({"pass", "fail", "suspended"}),
    "backtrack_count": frozenset({"0", "1"}),                  # int rendered as str
    "bootstrap_hit": frozenset({"true", "false"}),
    "forge_degraded": frozenset({"true", "false"}),
    "reviewer_count": frozenset({"1", "2", "3"}),
}

# Reverse: keys with unbounded value sets (high-cardinality, but allowed).
UNBOUNDED_KEYS: FrozenSet[str] = frozenset({"cycle_id", "tenant_hash", "praxis_version"})
```

#### SQ-2 Hard Reject Test (non-waivable)

Per **SQ-2** (binding), §12 MUST include a non-waivable test that MAC's emit path **rejects** any label key/value not in the registry. **Hard-fail, not warn.** The MAC's telemetry adapter MUST raise `LabelRegistryError` (subclass of `ValueError`) on any unknown label.

```python
# praxis/kernel/mac/observability/emitter.py

from praxis.kernel.memory.telemetry import TelemetryEvent
from .telemetry_labels import (
    ALLOWED_MAC_LABEL_KEYS,
    ALLOWED_LABEL_VALUES,
    UNBOUNDED_KEYS,
)

class LabelRegistryError(ValueError):
    """Raised on any label key/value not in the SQ-2 registry."""

class MacTelemetryEmitter:
    async def emit(
        self,
        metric_name: str,
        metric_type: str,
        value: float,
        labels: dict[str, str],
        tenant_hash: str,
    ) -> None:
        # SQ-2 hard-fail check
        for key, val in labels.items():
            if key not in ALLOWED_MAC_LABEL_KEYS:
                raise LabelRegistryError(f"unknown label key: {key!r}")
            if key in ALLOWED_LABEL_VALUES and val not in ALLOWED_LABEL_VALUES[key]:
                raise LabelRegistryError(
                    f"unknown label value for {key!r}: {val!r}"
                )
            # Keys in UNBOUNDED_KEYS pass without value validation.

        event = TelemetryEvent(
            metric_name=metric_name,
            metric_type=metric_type,
            value=value,
            labels=labels,
            tenant_hash=tenant_hash,
        )
        await self._sink.send(event)
```

**Murat 5.2 tests for SQ-2 (no_waiver):**
1. `test_emit_rejects_unknown_label_key()` — sends `{"nonexistent_key": "x"}` → expects `LabelRegistryError`
2. `test_emit_rejects_unknown_label_value_for_bounded_key()` — sends `{"gate_id": "R99"}` → expects `LabelRegistryError`
3. `test_emit_accepts_unbounded_key_value()` — sends `{"cycle_id": "01HX..."}` → succeeds
4. `test_no_warn_path_exists()` — grep test that no `logging.warning` is called in the emitter; only `raise`

### §11.2 Metric Catalog

| Metric Name | Type | Labels | What it captures |
|---|---|---|---|
| `mac.cycle.started` | counter | `cycle_id`, `cycle_phase`, `domain_class`, `tenant_hash` | One per phase entry |
| `mac.cycle.completed` | counter | `cycle_id`, `cycle_phase`, `outcome`, `tenant_hash` | One per phase exit |
| `mac.gate.evaluated` | counter | `gate_id`, `outcome`, `tenant_hash` | One per gate evaluation |
| `mac.gate.score` | gauge | `gate_id`, `tenant_hash` | Last evaluated effective_score |
| `mac.deliberation.composite_score` | gauge | `tenant_hash` | Last composite score |
| `mac.deliberation.cost_usd` | gauge | `tenant_hash` | Last deliberation cost |
| `mac.deliberation.duration_seconds` | histogram | `tenant_hash` | Wall time per deliberate() |
| `mac.bootstrap.hit` | counter | `bootstrap_hit`, `tenant_hash` | Cycle 1 retrieval bootstrap usage |
| `mac.forge.degraded` | counter | `forge_degraded`, `tenant_hash` | SQ-7 fallback triggers |
| `mac.backtrack.fired` | counter | `tenant_hash` | §5.5 backtrack invocations |
| `mac.label_registry.violations` | counter | `tenant_hash` | SQ-2 registry rejections (should be 0 in production) |

`mac.label_registry.violations` should be **zero** in production — a non-zero value indicates a code bug introducing an unregistered label, which Murat's grep test should have caught.

### §11.3 Linkage to Memory's TelemetryEvent

All MAC telemetry flows through `praxis.kernel.memory.telemetry.TelemetryEvent` (memory §9). This means:
- MAC events use the same generic envelope as Memory and Runtime events
- MAC label conventions must coexist with Memory and Runtime's labels (no key collision — MAC owns the `cycle_*`, `gate_*`, `domain_class`, `bootstrap_*`, `backtrack_*` namespaces; Memory owns `experience_*`, `decision_*`; Runtime owns `agent_*`, `proxy_*`)
- The cardinality bounds in §11.1 are enforced at the MAC emission layer, BEFORE the event is constructed

---

## §12. Testability Notes for Murat

This section is the binding handoff to Stage 5.2 (Murat — bmad-tea Test Architect). Murat's job is to take this section and produce the test strategy.

### §12.1 Coverage Requirement — SQ-9

Per **SQ-9** (frame binding), the MAC test suite MUST achieve **≥90% line + branch coverage** as a binding NFR. This inherits the Runtime test-strategy convention (runtime/pyproject.toml line 35).

The 90% target is measured against `praxis/kernel/mac/` excluding generated files (`calibration_anchors.py`, `gold_standards.json`).

### §12.2 `no_waiver` Markers

Adversarial gate tests (benchmark-questions.md §4 Persona 3 gaming scenarios) are marked `no_waiver` — they cannot be skipped, xfailed, or quarantined. The `no_waiver` marker is enforced via a pytest collection hook that fails the run if any test in the marker set is in `SKIPPED` / `XFAIL` / `XPASS` state.

The `no_waiver` test set MUST include:

1. **SQ-2 label registry hard-fail** (4 tests in §11.1)
2. **SQ-4 R8/R7 cap worked example** (R7=2, R8=4 → R8_eff=3)
3. **SQ-5 DomainClass single-definition grep** (`grep -r "class DomainClass"` returns exactly 1 match)
4. **SQ-7 Forge degradation ordering** (R7=4, R8=4, forge_degraded=True → R7_eff=3, R8_eff=4)
5. **SQ-8 dedup_key prefix grep** (no MAC dedup_key without `mac:` prefix)
6. **Req-A label snapshot** (OutputFormatContract.to_producer_prompt_fragment() byte-for-byte stable)
7. **Req-B routing snapshot** (GATE_SECTION_ROUTES table byte-for-byte stable)
8. **Req-D calibration anchor SHA256** (anchors match benchmark-questions.md §5)
9. **Req-F independent-steelman protocol** (reviewer prompt template hits STEP 1 before STEP 2 before STEP 3)
10. **Information asymmetry — ReviewerMemoryProxy AttributeError** (calling `retrieve_similar_tasks` on a reviewer raises AttributeError)
11. **Persona 3 gaming detection** (manufactured-dissent capping R5 at 2)
12. **R13 absence** (`praxis/kernel/mac/gates/r13.py` does NOT exist; gate set is exactly R1..R12)

### §12.3 Property Tests

Property-based tests via Hypothesis (Murat's standard) for:

- **Composite score arithmetic:** for any valid `dict[str, GateScore]`, `composite_score(scores) ∈ [0, 100]`
- **Composite score with suspensions:** if K gates are suspended, the denominator excludes their weight; for K=0 → denominator=85; for K=1 (R5 suspended) → denominator=83 (85 − 2×1); etc.
- **Phase DAG topological order:** any valid PhaseDAG has a linear extension; `topological_order()` is deterministic given the same node set
- **Gate score monotonicity in raw → effective:** `effective_score <= raw_score` always (no upward adjustment)

### §12.4 Calibration Tests

Per Req-D, Murat must verify that judge prompts include the calibration anchors. A snapshot test:

```python
def test_judge_prompt_includes_calibration_anchors():
    prompt = build_judge_prompt(gate_id="R4", section_text="...")
    anchor = CALIBRATION_ANCHORS["R4"]
    assert anchor.score_2_example in prompt
    assert anchor.score_4_example in prompt
    assert anchor.score_2_explanation in prompt
    assert anchor.score_4_explanation in prompt
```

Repeat for all 12 gates.

### §12.5 Asymmetry Tests

Per §7.2 binding to Runtime §4.1, Murat must verify:

1. **No direct ProducerMemoryProxy/ReviewerMemoryProxy import in MAC code:**
   ```bash
   grep -r "from praxis.kernel.runtime.spawner import.*MemoryProxy" praxis/kernel/mac/
   # Expected: 0 results
   ```
2. **Spawn role enforcement:** every `_run_review_phase` call uses `AgentRole.REVIEWER`; every `_run_produce_phase` uses `AgentRole.PRODUCER`
3. **Reviewer cannot retrieve:** integration test that spawns a reviewer, asserts `reviewer.memory.retrieve_similar_tasks(...)` raises `AttributeError`

### §12.6 Adversarial Tests (Persona 3 Gaming)

For each benchmark question, construct an "enhanced single-agent gaming attempt" — an output that has:
- A `[STEELMAN]` section with weak counterarguments
- A `[DISSENT]` section with manufactured dissent (positions not in the task context)
- A `[FINDINGS]` section that confidence-washes inferences as facts

Verify the gate engine catches this:
- R4 score ≤ 3 (weak steelman)
- R5 capped at 2 (manufactured dissent — Req-C)
- R1 score ≤ 3 (confidence washing)

These tests are `no_waiver` because they directly defend against the Persona 3 acknowledged limitation.

### §12.7 Mock vs Live Test Mix

- **Mocks:** Memory facade, AgentSpawner, CostTracker, MCPToolAdapter — Murat's standard pattern
- **Live (integration test, runs in CI nightly):** Full `deliberate()` against a stub LLM that returns canned outputs; verifies the full state machine + telemetry emission + Memory write

### §12.8 Coverage by Module

| Module | Target |
|---|---|
| `praxis.kernel.mac.controller` | ≥95% |
| `praxis.kernel.mac.task` (Task Interpreter) | ≥95% |
| `praxis.kernel.mac.plan` (Plan Decomposer) | ≥90% |
| `praxis.kernel.mac.runner` (Phase Runner) | ≥95% |
| `praxis.kernel.mac.engine` (Quality Gate Engine) | ≥95% |
| `praxis.kernel.mac.gates.r{1..12}` | ≥90% per gate |
| `praxis.kernel.mac.asymmetry` | ≥95% |
| `praxis.kernel.mac.learning` | ≥90% |
| `praxis.kernel.mac.bootstrap` | ≥90% |
| `praxis.kernel.mac.eval.*` | ≥85% (eval harness is run-mostly, less branching) |
| `praxis.kernel.mac.observability.*` | ≥95% (SQ-2 enforcement is gate-critical) |
| `praxis.kernel.mac.integrations.*` | ≥90% |

---

## §13. Open Questions

### §13.1 Stage 5 Gate Checklist

| Pipeline.md §5.1 sub-check | Fulfilling section(s) | Key citation |
|---|---|---|
| READS quality-rubric.md AND benchmark-questions.md BEFORE designing | §1, §6, §9 | quality-rubric.md §6 + §7; benchmark-questions.md §2 + §5 + §6 + §7 + §8 |
| Architecture doc at .../mac/architecture.md | (this document) | C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\mac\architecture.md |
| 3-cycle iteration pattern fully specified | §5 | §5.2 state machine; §5.3 Phase Runner; §5.4 Cycle 2 parallelism; §5.5 backtracking |
| 12 quality gates catalog ANCHORED on elicitation rubric | §6 (especially §6.1 catalog table) | quality-rubric.md §6 R1–R12 |
| Information asymmetry router design | §7 | Runtime §4.1 proxies + §7.1 Req-F; Runtime §9.0 punchline |
| Evaluation harness uses elicitation benchmark questions | §9 | benchmark-questions.md §2 (all 10 Qs) + §6 scoring protocol |
| SQ-1 MCP pin inheritance | §10.3 | Runtime §5; `mcp>=1.9.0` pin |
| SQ-2 Telemetry label registry hard-fail | §11.1, §12.2 | praxis.kernel.mac.observability.telemetry_labels |
| SQ-3 R13 deferral with re-admission trigger | §3.5, §6.6, §13.2 | quality-rubric.md §6 R13 row |
| SQ-4 R8/R7 cap (Option b) | §6.3 Pair 1 + §12.2 #2 | quality-rubric.md §7 Req-C |
| SQ-5 DomainClass enum frozen schema | §3.4, §6.5, §12.2 #3 | praxis.kernel.mac.task.DomainClass |
| SQ-6 Bootstrap loader (Option Y sidecar ratified) | §8.1 | memory/architecture.md §7.1 (no metadata column); ratified 2026-04-14 |
| **OQ-MAC-1 RESOLVED 2026-04-14** | §8.1 Ratification Decision + §13.2 Rejected Alternatives | Option Y sidecar accepted; Option X rejected (Stage 3 stays frozen) |
| SQ-7 Forge fallback ordering (penalty after Req-C cap) | §5.6, §6.3 §6.7 + §12.2 #4 | compression/architecture.md §3.2; SQ-7 binding |
| SQ-8 Path B dedup namespace `mac:` prefix | §10.3, §11, §12.2 #5 | runtime/architecture.md §8.1 |
| SQ-9 ≥90% coverage + no_waiver markers | §12.1, §12.2 | runtime/pyproject.toml line 35 |

### §13.2 Rejected Alternatives

**Rejected — Option X (direct `metadata` JSONB column on `experience_entries`)** — considered and rejected 2026-04-14 as the resolution path for OQ-MAC-1. Option X would have required Memory schema amendment (adding `metadata JSONB` to `experience_entries`) plus a facade extension (`Memory.store_task_outcome(..., metadata=...)` kwarg). The ratified path is Option Y (see §8.1). Rationale for rejection:

1. **Stage-gate discipline** — Stage 3 Memory was ratified 2026-04-13 and is binding. Reopening it to satisfy a Stage 5 bootstrap convenience violates the pipeline invariant that ratified stages do not re-open for downstream preferences.
2. **Blast radius** — The sidecar table `mac_bootstrap_metadata` is MAC-local. A `metadata` JSONB column on `experience_entries` touches every reader of a hot memory table (Cycle 1 retrieval, tentative→confirmed promotion logic, observability exporters).
3. **Reversibility** — Sidecar is reversible (drop a table); JSONB on a live table accumulates schema dependencies (indexes, retrieval filters, GDPR purge touchpoints) and is hard to evolve or remove cleanly.
4. **Premature optimization** — Option X's inline-read advantage matters only on the bootstrap read path, which fires on MAC cold-start, not on the Cycle 1 hot path. The per-retrieval sidecar lookup is a constant small cost that can be batched.
5. **Aesthetic preference vs. design requirement** — "All metadata in one place" is a preference, not a functional requirement. The functional requirement is that bootstrap entries be distinguishable at retrieval time, which Option Y satisfies via the sidecar join.

Amelia (Stage 5.3) implements the ratified Option Y path. Option X is not to be revisited unless a future stage surfaces a functional requirement the sidecar cannot meet.

### §13.3 Residual Open Questions (Non-Blocking)

None of the following block Stage 5.1 ratification. They are forward-looking items tracked for the stages that own them.

**OQ-MAC-2 — R13 Stage 6 re-admission trigger (per SQ-3)**
Re-admit R13 Evidence Sourcing at Stage 6 if and only if Studio workflow templates elicit retrieval-grounded analysis with source attribution as a primary output contract. The trigger condition must be checked at Stage 6 architecture time; if true, R13 is re-introduced as gate #13 with the conditional-gate definition from quality-rubric.md §6 R13 row.

**OQ-MAC-3 — Workflow template guard override schema (per SQ-5)**
The §6.5 `gates_suspended_for(workflow_override=...)` parameter accepts a per-template override of the `DomainClass → frozenset[gate_id]` mapping. Stage 6 Studio defines the YAML/JSON schema for templates to express this override. Stage 5 ships with the default mapping only; template overrides are a Stage 6 concern.

**OQ-MAC-4 — Reviewer count tuning per question type**
§4.3 caps `reviewer_count` at 3 and defaults to 2 for `CONTESTED` and 1 for others. The actual optimal count per question type is empirical — Stage 5.6 benchmark runs may reveal that some questions benefit from 3 reviewers (driving R4/R5 higher) while others plateau at 2. Stage 5.6 retro can revise the defaults.

**OQ-MAC-5 — Backfill scheduling**
§8.4 `BackfillJob` is a one-time job at first MAC ship. The exact deployment hook (manual run via runbook? automated on first deploy with a marker?) is owned by Stage 7 POV Harness deployment runbook design. MAC ships the job; Stage 7 schedules it.

**OQ-MAC-6 — Composite score threshold for "PASS"**
§5.5 backtracking fires on any Critical gate < 3, but the overall `composite_score` doesn't have a binary pass/fail cutoff in this document. The pre-sales report will use the raw 0-100 score, but workflow templates (Stage 6) may want a configurable PASS threshold (e.g., "composite ≥ 70 = ship"). Stage 6 owns this.

---

*Document produced by: Winston (BMAD Architect — bmad-agent-architect)*
*Status: RATIFIED v0.1 — 2026-04-14*
*Next: Stage 5.2 — Murat (Test Architect) takes §12 and produces the test strategy*
*Then: Stage 5.3 — Amelia (Developer) implements per the integration contracts in §10, including the `0001_mac_bootstrap_metadata` migration per §8.1 Option Y (ratified)*
