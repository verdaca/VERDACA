# Praxis Stage 4 — Agent Runtime Architecture

**Author:** Winston (Architect)
**Date:** 2026-04-13
**Status:** DRAFT v0.1 — §1–§5 produced; checkpoint halt at §5 boundary per Andrey's draft cadence instruction. §6–§12 pending verification of ReviewerMemoryProtocol narrowing and Spawner agent-construction path.
**Preload:** Three documents absorbed via frame report:
1. `_bmad-output/planning-artifacts/Praxis/stage-4-winston-prompt.md` — baseline architect frame
2. `_bmad-output/implementation-artifacts/praxis/runtime/tool-library-requirements.md` — Carson's 4.0.1 persona-grounded tool catalog (binding on §6)
3. `_bmad-output/planning-artifacts/Praxis/stage-4-deferred-findings-brief.md` — F-1 + F-3 architectural inputs (binding on §4.2, §8, §9)
**Corrections absorbed (binding):** F-1 Path A/Path B split per Andrey's verification; durable retry state in Postgres (not sidecar map); shared-DB peer-tables framed as correctness requirement, not optimization; information asymmetry via type-level ProducerMemoryProxy/ReviewerMemoryProxy partitioning with strict-subset Protocol narrowing.

---

## §1. Reference Analysis

This section documents what I extract from each reference dump and why. Per the Stage 4 frame's context strategy, I read dumps sequentially and selectively — the goal is pattern extraction, not wholesale porting. Every pattern named below is cited inline in §2–§5 when it lands in the design.

### §1.1 BMAD Agent Manifest — `_bmad/_config/agent-manifest.csv`

**Strategy:** Source of truth. Parse → Pydantic model. Not optional, not a pattern reference.

**What I absorb:** 16 rows, each row is one BMAD agent with 12 columns: `name, displayName, title, icon, capabilities, role, identity, communicationStyle, principles, module, path, canonicalId`. The `capabilities` column is a comma-separated natural-language list (e.g., `"market research, competitive analysis, requirements elicitation, domain expertise"`) — this is the primary input to §3 Agent Registry's matching algorithm. The `module` column groups agents by origin (bmm / cis / tea), and `path` locates the agent skill inside the `_bmad/` tree — these inform §2 Agent Definition extensibility hooks.

**Agent count:** 16.
- **bmm (10):** Mary (Analyst), Paige (Tech Writer), John (PM), Sally (UX), Winston (Architect), Amelia (Dev), Quinn (QA), Barry (Quick Flow Dev), Bob (SM)
- **cis (6):** Carson (Brainstorming), Dr. Quinn (Creative Problem Solver), Maya (Design Thinking), Victor (Innovation), Caravaggio (Presentation), Sophia (Storyteller)
- **tea (1):** Murat (Test Architect)

**What §2 inherits from the manifest:** The `AgentDefinition` Pydantic model is a 1:1 reflection of the CSV columns with validation rules on each field. Adding a new agent = appending a row and restarting the loader (or invoking reload support). No code change required — §2 extensibility is manifest-driven by construction.

**What §3 inherits from the manifest:** Capability strings are the *retrieval surface*. Indexed as (a) exact-token search over the comma-split list, (b) embedding-based semantic search for paraphrased task descriptions, (c) LLM-based ranked matching as a fallback. See §3 for the matching algorithm.

### §1.2 Atomic Agents — `brainblend-ai-atomic-agents-*.txt`

**Strategy:** Pattern extraction — Pydantic schema composition + typed generic agent class. Not porting.

**What I absorb (from targeted grep; full dump not loaded):**

1. **`BaseIOSchema`** as the Pydantic base for all agent input/output schemas. Every agent's input and output are Pydantic-typed, validated at the boundary, and composable with other agents'/tools' schemas via identity (one agent's `output_schema` can be set equal to another tool's `input_schema` for direct chaining).

2. **`AtomicAgent[InputSchema, OutputSchema]`** generic class pattern — an agent is parameterized by its I/O schemas at the type level, meaning the type system enforces composability and mismatches fail at static-analysis time (pylance / mypy), not at runtime.

3. **`AgentConfig`** — a composable config object passed into agent construction carrying model selection, system prompt, temperature, and I/O schema references. Clean separation between "what the agent is" (type) and "how the agent is wired" (config).

**What §2 inherits:** The Pydantic-schema-per-agent discipline applied to `AgentDefinition` itself and to the *per-agent I/O contract* that §2 declares. Every BMAD agent gets an `input_schema` and `output_schema` declared at load time, derived from the agent's role + capabilities. Stage 4 does NOT redesign each BMAD agent's prompt structure (that's the agent's own skill definition in `_bmad/`), but it DOES enforce a typed I/O boundary at the runtime layer.

**What §3 inherits:** The typed composability pattern for agent-to-tool and agent-to-agent chains. When §3's matching algorithm returns a list of candidate agents, the caller can statically verify that the chosen agent's `input_schema` accepts the task payload — no runtime surprise.

**Explicit non-goals:** We do NOT port `AtomicAgent` as a class, do NOT adopt their DSPy integration story (separate concern), and do NOT use their single-agent optimization loop. Praxis agents are BMAD agents that happen to be Pydantic-typed at the runtime boundary, not AtomicAgents.

### §1.3 Gas Town — `gastownhall-gastown-*.txt`

**Strategy:** Pattern extraction — agent spawning, coordination, session discovery, Polecat lifecycle. Selective read only; the 12MB full dump is never loaded.

**What I absorb (from targeted grep on lifecycle / polecat / seance):**

1. **Polecat pattern** (worker agent lifecycle) — Polecats are worker agents spawned by a Mayor role. Each polecat has a spawn → run → cleanup lifecycle with explicit resource release. Gas Town uses `gt deacon cleanup-orphans` to kill orphaned polecat processes that lose their controlling TTY. **Extractable:** the guaranteed-cleanup contract. Praxis adopts the "every spawn returns a handle; every handle has a cleanup hook that runs even on abnormal termination" discipline.

2. **Witness pattern** (per-rig lifecycle manager) — Witness monitors polecats, detects stuck agents, triggers recovery, manages session cleanup. This is a supervisor role that sits above worker agents and observes their health. **Extractable:** Praxis's Spawner (§4) owns the supervisor role — it tracks spawned agents, enforces resource budgets, and triggers cleanup on stuck/runaway states. Gas Town's Witness is the name; Praxis's equivalent lives inside the Spawner's §4.1 design.

3. **Seance pattern** (session discovery via event log) — Seance discovers sessions by reading `.events.jsonl` logs, enabling agents to recover context and decisions from earlier work without re-reading entire codebases. Events emitted include session lifecycle, agent state changes, polecat spawn/remove, mail operations. **Extractable:** The event-log-as-coordination-substrate pattern. Praxis's §7 Inter-Agent Communication Bus adopts append-only event log semantics (backed by Beads from Stage 3) for cross-agent coordination, but scoped strictly within a single deployment per R11. No cross-session fishing — only intra-session event replay.

4. **Orphan cleanup discipline** — `gt deacon cleanup-orphans` runs periodically and kills processes that lost their parent. **Extractable:** Praxis's §4.4 Polecat Cleanup subsection describes an equivalent orphan-sweeping pattern invoked on Runtime startup and on each Orchestrator tick.

**Explicit non-goals:** We do NOT adopt the Rig/Mayor/Convoy topology (too opinionated for Praxis's BMAD-anchored org chart), do NOT use `.events.jsonl` as a literal file format (Praxis uses Beads-backed event storage), and do NOT port Gas Town's Go code. We extract the shape of the lifecycle + supervision + discovery patterns and adapt them to Python + Beads.

### §1.4 Atelier Pipeline — `robertsfeir-atelier-pipeline-*.txt`

**Strategy:** Pattern extraction — wave-based execution, parallel reviewer asymmetry. Selective read only.

**What I absorb (from targeted grep on wave / phase / Poirot / review):**

1. **Wave execution pattern** — Eva (conductor) orchestrates feature work in waves. When multiple ADR steps are independent (no shared files), Eva creates Colby Teammate instances that execute simultaneously. Sequential by default, parallel when safe. **Extractable:** The "phases execute one at a time per turn; parallelism is opt-in and explicitly justified by independence" discipline. Praxis's §4.1 Spawner adopts this: subagent mode is sequential by default; team mode with parallelism requires an explicit independence claim from the caller.

2. **Poirot Blind Review pattern** — Poirot is a "Blind Code Investigator" — a reviewer agent that evaluates producer work WITHOUT seeing the producer's reasoning trace. Atelier calls this out as a distinct architectural role. **Extractable, and load-bearing for §4 + §7 + §9:** The structural separation of producer-visible and reviewer-visible information surfaces. This is the *prior-art citation* that Winston §9's "information asymmetry must be structural, not trusted" mandate builds on. Praxis implements Poirot's blindness via type-level Protocol narrowing (§4.1 ProducerMemoryProxy / ReviewerMemoryProxy), which is as structural as Python permits short of capability-language enforcement.

3. **Role specialization pattern** — Robert (Chief Product Officer), Sable (Senior UI/UX), Poirot (Investigator), Ellis (various), Eva (conductor), Cal (?), Colby (builder). Each role has a narrow responsibility + a matching skill surface. **Extractable:** Directly validates Praxis's 16-BMAD-agent approach — specialization beats generalism for multi-agent deliberation. Pattern already instantiated in Praxis; Atelier is confirmation, not novelty.

4. **Phase selection by feature complexity** — not every feature runs every phase. Eva adjusts. **Extractable:** Praxis's MAC (Stage 5) owns the phase-selection logic; Stage 4 Runtime provides the phase-execution substrate (Spawner can run any phase; it doesn't decide which phase to run).

**Explicit non-goals:** We do NOT port Eva's scheduling loop (Stage 5 MAC concern), do NOT adopt Colby-specific build mechanics (Stage 4 is agent-generic), and do NOT use their ADR-per-step format. We extract the wave + blind-review patterns and leave the orchestration semantics for Stage 5.

### §1.5 MCP Protocol — Client Integration

**Strategy:** Client integration — use the official MCP Python SDK. Not porting.

**What I absorb (general knowledge; will verify via Context7 at §5 draft time if specifics needed):**

1. **MCP is a JSON-RPC-over-stdio/HTTP protocol** for tool discovery, invocation, and result return between an LLM host (Praxis Runtime) and external tool servers (Tavily, GitHub, Filesystem, etc.). Each tool server exposes a manifest of available tools, each with a JSON Schema for inputs and outputs.

2. **Tool discovery** — on connection, the client asks the server for its tool list. The server returns a list of tool descriptors. The Runtime caches these, filters against the per-agent allowlist from §9, and presents the allowed subset to the agent.

3. **Invocation model** — the client sends a `call_tool` JSON-RPC request with the tool name and validated input payload. The server executes in its own process and returns a result (or a typed error). Sandboxing is the server's responsibility (the client cannot enforce sandbox escape prevention from outside); Runtime enforces trust boundaries at the *selection* of which servers to connect to and under what credentials.

4. **Result normalization** — MCP results may be text, structured JSON, or binary. Praxis normalizes to either Pydantic models (when the tool has a typed output schema) or TONL-encoded text (for unstructured tool outputs, per Stage 2 compression integration).

**What §5 inherits:** The MCP Tool Adapter is a client wrapper around `mcp.client` (the official Python SDK) that (a) manages per-tool connection lifecycle, (b) enforces the §9 per-agent allowlist at tool selection time, (c) normalizes results, (d) emits CostEvents per invocation for Pi-Mono integration, (e) wraps errors into Praxis's error hierarchy.

**Explicit non-goals:** We do NOT implement MCP from scratch, do NOT modify the SDK, do NOT design our own tool protocol. MCP is a standard; Praxis uses it.

### §1.6 Cross-Reference Mapping (What Lands Where)

| Pattern | Source | Lands in |
|---|---|---|
| Pydantic BaseIOSchema for agent I/O | Atomic Agents | §2 Agent Definition Schema |
| Typed generic agent class | Atomic Agents | §2 extensibility |
| Polecat spawn → run → cleanup lifecycle | Gas Town | §4.1 Spawner, §4.4 Polecat Cleanup |
| Witness supervisor pattern | Gas Town | §4.1 Spawner (embedded supervisor role) |
| Seance event-log session discovery | Gas Town | §7 Inter-Agent Communication Bus (pending §6–§9 block) |
| Orphan cleanup sweeper | Gas Town | §4.4 Polecat Cleanup |
| Wave execution + independence-opt-in parallelism | Atelier | §4.1 Spawner team mode |
| Poirot Blind Review (producer/reviewer asymmetry) | Atelier | §4.1 ProducerMemoryProxy/ReviewerMemoryProxy, §9 Security Model |
| Role specialization (validation of BMAD approach) | Atelier | §1 only (no design change needed) |
| MCP client integration | MCP SDK | §5 MCP Tool Adapter Design |

### §1.7 Reference Reading Discipline

Per the Stage 4 frame context strategy, I read references sequentially and selectively:

- **Agent manifest:** Fully absorbed during Carson's 4.0.1 preload. 17 lines, trivial cost.
- **Atomic Agents:** Targeted grep for class/schema patterns. Not loaded in full. Patterns extracted via pattern-name lookup (~30 grep hits read in context).
- **Gas Town:** Targeted grep for lifecycle/polecat/seance. Not loaded in full. 12MB avoided.
- **Atelier:** Targeted grep for wave/phase/Poirot. Not loaded in full. 3.3MB avoided.
- **MCP spec:** General knowledge; Context7 lookup deferred to §5 draft time if specifics needed.

**This is the entirety of §1 Reference Analysis.** Subsequent sections cite these patterns inline with back-references to §1.X subsections.

---

## §2. Agent Definition Schema

Every one of the 16 BMAD agents becomes a Pydantic-typed, runtime-loadable first-class object in Praxis. This section specifies the schema, validation, and extensibility.

### §2.1 The `AgentDefinition` Pydantic Model

```python
from enum import StrEnum
from pathlib import Path
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentModule(StrEnum):
    """BMAD module origin — groups agents by lineage."""
    BMM = "bmm"  # Business/Market/Methodology agents
    CIS = "cis"  # Creative Innovation Studio agents
    TEA = "tea"  # Test Architecture agents


class AgentDefinition(BaseModel):
    """Frozen, validated, typed representation of a BMAD agent as loaded from the manifest CSV.

    One-to-one reflection of `_bmad/_config/agent-manifest.csv` columns with
    validation rules applied at load time. Application code never instantiates
    this directly — the Loader (§2.3) owns construction.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Identity
    name: str = Field(..., min_length=1, description="Stable identifier, e.g. 'bmad-agent-architect'")
    display_name: str = Field(..., min_length=1, description="Human-readable name, e.g. 'Winston'")
    title: str = Field(..., min_length=1, description="Role title, e.g. 'Architect'")
    icon: str = Field(..., description="Emoji or short glyph for UX surfaces")

    # Capability surface (the retrieval target for §3 Registry)
    capabilities: tuple[str, ...] = Field(
        ...,
        min_length=1,
        description="Normalized capability tokens parsed from the CSV comma-separated list",
    )

    # Persona (drives system prompt assembly; not used for matching)
    role: str = Field(..., description="One-line role description")
    identity: str = Field(..., description="Multi-sentence identity/background")
    communication_style: str = Field(..., description="Tone, voice, interaction norms")
    principles: str = Field(..., description="Operating principles the agent draws on")

    # Provenance
    module: AgentModule = Field(..., description="Originating BMAD module")
    path: Path = Field(..., description="Relative path to the agent skill directory under _bmad/")
    canonical_id: str = Field(default="", description="Optional canonical identifier for cross-reference")

    @field_validator("capabilities", mode="before")
    @classmethod
    def _normalize_capabilities(cls, v: Any) -> tuple[str, ...]:
        """Parse CSV cell into normalized token tuple.

        Accepts either a raw CSV string (manifest source) or an already-normalized
        tuple/list (test fixtures, runtime reconstruction).
        """
        if isinstance(v, str):
            tokens = tuple(t.strip().lower() for t in v.split(",") if t.strip())
            if not tokens:
                raise ValueError("capabilities must contain at least one token")
            return tokens
        if isinstance(v, (tuple, list)):
            return tuple(t.strip().lower() for t in v if t and t.strip())
        raise TypeError(f"capabilities must be str, tuple, or list; got {type(v).__name__}")

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        """Agent name must match the BMAD slug convention."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"name {v!r} contains invalid characters; expected alphanumeric + hyphen/underscore")
        return v

    @field_validator("path")
    @classmethod
    def _validate_path(cls, v: Path) -> Path:
        """Path is relative (resolved at load time against _bmad/ root)."""
        if v.is_absolute():
            raise ValueError(f"path {v} must be relative to _bmad/")
        return v
```

**Design notes:**

- **`frozen=True, extra="forbid"`** — Agent definitions are immutable after construction. Any attempt to mutate an `AgentDefinition` instance or pass unknown fields is a TypeError. This is defense-in-depth against accidental runtime mutation of the agent catalog.
- **`capabilities` as tuple, not list** — Tuples are hashable; agents can be compared and deduplicated. Tuples also reinforce immutability.
- **Lowercased capability tokens** — Normalization at load time means §3 Registry's matching algorithm compares lowercase-to-lowercase without per-query normalization overhead.
- **`role/identity/communication_style/principles` as free-form strings** — These feed system-prompt assembly, not matching. Free-form is correct; imposing structure would over-constrain BMAD's prompt engineering.
- **`module` as StrEnum** — Type-safe module selection; catches typos at CSV parse time.

### §2.2 Input/Output Schema Per Agent

Per Atomic Agents' typed I/O pattern (§1.2), every agent has a typed input and output schema at runtime. For BMAD agents, these are NOT redesigned by Praxis — they are derived from the agent's role + capabilities at load time as a light type layer that the Runtime enforces at the invocation boundary.

```python
from pydantic import BaseModel


class AgentInputSchema(BaseModel):
    """Base class for all agent input payloads.

    Subclasses are generated per agent at load time (or pre-declared in
    _bmad/{module}/schemas/{agent}-input.py if the agent ships a custom schema).
    Runtime enforces: every agent invocation must pass a Pydantic model
    instance that validates against the agent's declared input_schema.
    """
    model_config = {"frozen": True, "extra": "forbid"}


class AgentOutputSchema(BaseModel):
    """Base class for all agent output payloads.

    Mirror of AgentInputSchema. Every agent invocation produces a Pydantic
    model instance (or raises); no untyped string outputs at the Runtime
    boundary.
    """
    model_config = {"frozen": True, "extra": "forbid"}


class GenericTaskInput(AgentInputSchema):
    """Default input schema used by agents that ship no custom schema.

    Captures the universal fields every BMAD agent needs: task description,
    context budget, and an optional reference bundle. Specialized agents
    (Winston, Amelia, Murat) will override with stricter schemas.
    """
    task_description: str
    context_budget_tokens: int
    reference_bundle: dict[str, Any] | None = None


class GenericTaskOutput(AgentOutputSchema):
    """Default output schema. Specialized agents override."""
    summary: str
    artifacts: tuple[Path, ...] = ()
    decisions: tuple[str, ...] = ()
    follow_ups: tuple[str, ...] = ()
```

**Schema registration:** The Loader (§2.3) accepts an optional `schemas_module` parameter pointing to a Python package where custom schemas live. For BMAD agents that ship custom schemas, the Loader imports `{schemas_module}.{agent_name}` and binds the schemas to the `AgentDefinition` at load time. For agents without custom schemas, the Loader assigns `GenericTaskInput` / `GenericTaskOutput` as the default.

**Where schemas attach:** The `AgentDefinition` model itself stays stable (CSV-mirrored); a sibling `AgentRuntimeConfig` model holds the schema bindings + other runtime-specific config. This separation keeps the CSV-authoritative `AgentDefinition` immutable while allowing Runtime-layer customization:

```python
class AgentRuntimeConfig(BaseModel):
    """Runtime-layer configuration bound to an AgentDefinition at load time.

    Holds schema bindings, model selection, and MCP tool allowlist. Populated
    by the Loader; consumed by the Spawner.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    agent: AgentDefinition
    input_schema: type[AgentInputSchema]
    output_schema: type[AgentOutputSchema]
    tool_allowlist: frozenset[str]  # §6 tool names the agent may invoke
    model_preference: str = "claude-sonnet-4-6"  # default, overridable at spawn time
    thinking_level: str = "high"  # default, overridable at spawn time
```

### §2.3 Loader — CSV → `AgentDefinition` Collection

```python
import csv
from pathlib import Path
from typing import Iterator
from collections.abc import Mapping


class AgentLoaderError(Exception):
    """Raised when manifest parsing or validation fails."""


class AgentLoader:
    """Load the BMAD agent manifest from CSV and produce AgentDefinition objects.

    Responsibilities:
    - Parse _bmad/_config/agent-manifest.csv
    - Validate each row via Pydantic
    - Detect duplicate names
    - Attach runtime configs (schemas, tool allowlists, model prefs)
    - Provide reload support for development mode
    """

    def __init__(
        self,
        manifest_path: Path,
        schemas_module: str | None = None,
        default_tool_allowlist_fn: "Callable[[AgentDefinition], frozenset[str]]" = None,
    ) -> None:
        self._manifest_path = manifest_path
        self._schemas_module = schemas_module
        self._default_tool_allowlist_fn = default_tool_allowlist_fn or _default_tool_allowlist
        self._cache: dict[str, AgentRuntimeConfig] | None = None

    def load(self) -> Mapping[str, AgentRuntimeConfig]:
        """Parse the manifest and return an immutable mapping keyed by agent name."""
        if self._cache is not None:
            return self._cache
        self._cache = dict(self._parse())
        return self._cache

    def reload(self) -> Mapping[str, AgentRuntimeConfig]:
        """Force re-parse. Intended for development; production uses load()."""
        self._cache = None
        return self.load()

    def _parse(self) -> Iterator[tuple[str, AgentRuntimeConfig]]:
        seen: set[str] = set()
        with self._manifest_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row_idx, row in enumerate(reader, start=1):
                try:
                    definition = AgentDefinition(**_row_to_model_kwargs(row))
                except Exception as e:
                    raise AgentLoaderError(f"row {row_idx}: {e}") from e
                if definition.name in seen:
                    raise AgentLoaderError(f"duplicate agent name {definition.name!r}")
                seen.add(definition.name)
                runtime_config = self._bind_runtime_config(definition)
                yield definition.name, runtime_config

    def _bind_runtime_config(self, agent: AgentDefinition) -> AgentRuntimeConfig:
        """Attach schemas and tool allowlist to the bare AgentDefinition."""
        input_schema, output_schema = self._resolve_schemas(agent)
        tool_allowlist = self._default_tool_allowlist_fn(agent)
        return AgentRuntimeConfig(
            agent=agent,
            input_schema=input_schema,
            output_schema=output_schema,
            tool_allowlist=tool_allowlist,
        )

    def _resolve_schemas(
        self, agent: AgentDefinition
    ) -> tuple[type[AgentInputSchema], type[AgentOutputSchema]]:
        """Look up custom schemas or fall back to Generic{Input,Output}."""
        if self._schemas_module is None:
            return GenericTaskInput, GenericTaskOutput
        try:
            mod = __import__(f"{self._schemas_module}.{agent.name.replace('-', '_')}", fromlist=["*"])
            return (
                getattr(mod, "input_schema", GenericTaskInput),
                getattr(mod, "output_schema", GenericTaskOutput),
            )
        except ImportError:
            return GenericTaskInput, GenericTaskOutput


def _row_to_model_kwargs(row: Mapping[str, str]) -> dict[str, Any]:
    """Translate CSV column names (camelCase) to Pydantic field names (snake_case)."""
    return {
        "name": row["name"],
        "display_name": row["displayName"],
        "title": row["title"],
        "icon": row["icon"],
        "capabilities": row["capabilities"],
        "role": row["role"],
        "identity": row["identity"],
        "communication_style": row["communicationStyle"],
        "principles": row["principles"],
        "module": row["module"],
        "path": row["path"],
        "canonical_id": row.get("canonicalId", ""),
    }


def _default_tool_allowlist(agent: AgentDefinition) -> frozenset[str]:
    """Map an agent to its default tool allowlist via capability heuristics.

    Implemented in §9 Security Model once §6 Tool Library Catalog is committed.
    Stage 4 default: empty allowlist (agents get tools by explicit grant only).
    """
    return frozenset()
```

**Design notes:**

- **Strict CSV parsing via `csv.DictReader`** — Pattern-matches the manifest's column names; row-level errors surface with row index in the exception message.
- **Duplicate-name check at load time** — Stops ambiguous registry state before the agent catalog ever becomes visible to §3 Registry.
- **Runtime config as a separate frozen model** — Keeps `AgentDefinition` pure-CSV while allowing Runtime customization.
- **Reload support** — Development mode only; production loads once at startup. Reload is explicit, not automatic file-watching (avoids subtle bugs from partial reloads mid-invocation).
- **Default tool allowlist is empty** — Default-deny per Andrey's decision resolution on Carson §6.9.1. Tools are granted per agent by explicit capability-to-tool mapping in §9 Security Model. Stage 4 ships no agent with a non-empty default allowlist; every grant is auditable.

### §2.4 Extensibility — Adding a New BMAD Agent Post-Launch

Adding a new BMAD agent requires:

1. **Append a row** to `_bmad/_config/agent-manifest.csv` with all 12 columns populated.
2. **Ensure the skill directory** exists at the path referenced in the `path` column (under `_bmad/{module}/`).
3. **(Optional) Ship custom schemas** by adding `input_schema` and `output_schema` exports in `{schemas_module}/{agent_name_underscored}.py`.
4. **Restart the Runtime** (or call `AgentLoader.reload()` in dev mode).

**No code change to the Runtime layer is required.** The Loader discovers the new agent automatically. §3 Registry's capability index is rebuilt on load. §4 Spawner can spawn the new agent immediately.

**What is NOT supported post-launch:**
- Changing an existing agent's `name` (breaks external references; requires migration)
- Removing capabilities (use versioning via `canonical_id` and a new row)
- Modifying the CSV column set (requires Praxis version bump)

### §2.5 Validation Rules (Summary)

| Rule | Enforced at | Failure mode |
|---|---|---|
| All 12 columns present in CSV row | Loader `_parse` | `AgentLoaderError` with row index |
| `name` matches alphanumeric + hyphen/underscore | Pydantic `@field_validator` | `ValidationError` |
| `capabilities` non-empty after parse | Pydantic `@field_validator` | `ValidationError` |
| `path` is relative | Pydantic `@field_validator` | `ValidationError` |
| `module` is one of BMM/CIS/TEA | StrEnum | `ValidationError` |
| No duplicate `name` | Loader `_parse` | `AgentLoaderError` |
| `AgentDefinition` is frozen | Pydantic `ConfigDict(frozen=True)` | `ValidationError` on mutation attempt |
| Unknown fields rejected | Pydantic `extra="forbid"` | `ValidationError` |

---

## §3. Agent Registry Design

The Registry is the query surface over the loaded `AgentRuntimeConfig` catalog. Given a task description (or a capability query), it returns ranked agent candidates. This section specifies indexing, the query API, the matching algorithm, and confidence semantics.

### §3.1 Indexing Strategy

**Two complementary indices**, built at Loader completion time:

1. **Token index** — exact-match lookup over the normalized lowercase capability tokens. Map: `capability_token → set[agent_name]`. O(1) lookup; handles queries like "brainstorming" → Carson.

2. **Semantic index** — embedding-based vector search over agent capability strings + role + identity summary. One embedding per agent, computed via a pinned embedding model (deployment manifest-bound per R14). Map: `embedding_vector → agent_name`. O(log n) or O(n) depending on backing store; for 16 agents, linear scan is fine.

**Why both:** The token index catches precise capability matches; the semantic index catches paraphrased queries where the task description doesn't use the BMAD vocabulary verbatim ("I need someone to help me think through whether to pivot" → Victor via semantic, not via token).

**Where the indices live:** In-process on the Runtime, rebuilt from `AgentRuntimeConfig` on every Loader load/reload. No persistent store; indices are fast to rebuild and always consistent with the current manifest.

### §3.2 Query API

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentMatch:
    """A single agent candidate with its match score and explanation."""
    agent: AgentRuntimeConfig
    score: float  # [0.0, 1.0], higher is better
    confidence: float  # [0.0, 1.0]; separate from score per §3.4
    match_source: str  # "token", "semantic", "llm_rerank"
    matched_tokens: tuple[str, ...]  # for token matches; empty otherwise
    rationale: str  # human-readable explanation


@dataclass(frozen=True)
class AgentQuery:
    """A capability or task-description query against the registry."""
    task_description: str
    required_tokens: tuple[str, ...] = ()  # hard filter; agent must have ALL
    min_confidence: float = 0.5
    top_k: int = 5


class AgentRegistry:
    """The query surface over the loaded agent catalog.

    Constructed once per Runtime init (or per Loader reload). Thread-safe for
    read operations.
    """

    def __init__(self, catalog: Mapping[str, AgentRuntimeConfig], embedder: "Embedder") -> None:
        self._catalog = catalog
        self._embedder = embedder
        self._token_index: dict[str, set[str]] = {}
        self._semantic_index: dict[str, list[float]] = {}
        self._build_indices()

    def find_agents(self, query: AgentQuery) -> list[AgentMatch]:
        """Primary query API. Returns up to `query.top_k` matches, sorted desc by score.

        Algorithm: token-filter → semantic rerank → LLM tie-break (only if
        semantic top-k is below min_confidence, §3.4).
        """
        # Hard filter by required tokens
        candidates = self._filter_by_required_tokens(query.required_tokens)
        if not candidates:
            return []

        # Score via token + semantic fusion
        scored = self._score_candidates(query.task_description, candidates)

        # LLM tie-break if all top-k scores are below min_confidence
        if all(m.confidence < query.min_confidence for m in scored[: query.top_k]):
            scored = self._llm_rerank(query.task_description, scored[: query.top_k * 2])

        return scored[: query.top_k]

    def get(self, agent_name: str) -> AgentRuntimeConfig | None:
        """Direct lookup by stable agent name. O(1)."""
        return self._catalog.get(agent_name)

    def all_agents(self) -> tuple[AgentRuntimeConfig, ...]:
        """Enumerate the full catalog. Stable ordering for deterministic tests."""
        return tuple(sorted(self._catalog.values(), key=lambda c: c.agent.name))
```

### §3.3 Matching Algorithm — Detail

**Pipeline:**

1. **Required-token filter** — `AgentQuery.required_tokens` specifies capabilities that MUST be present on any returned agent. Agents missing any required token are eliminated before scoring. This allows callers to say "I want an agent who can do UX design AND user research" and get only candidates that match both (Sally, not Maya).

2. **Token-match scoring** — For each remaining candidate, count the number of `task_description` tokens (after lowercase normalization and stopword removal) that appear in the agent's `capabilities` set. Normalize to `[0, 1]` by dividing by the description token count. This is `token_score`.

3. **Semantic-match scoring** — Embed `task_description` once; compute cosine similarity against each remaining candidate's pre-computed capability embedding. This is `semantic_score`.

4. **Fused score** — `score = 0.4 × token_score + 0.6 × semantic_score`. The 40/60 weighting biases toward semantic matching to handle paraphrases, while keeping token matches as a meaningful signal for precise queries. Weighting is tunable via deployment config; 40/60 is the strawman for launch.

5. **Confidence computation** — separate from score. Confidence reflects *how sure we are that this is the right agent*, which is not the same as how high the score is. See §3.4.

6. **LLM tie-break (fallback path)** — If all top-k candidates have confidence below `min_confidence`, invoke an LLM with the task description and the top-k candidates' full `AgentRuntimeConfig` (name, title, role, identity, capabilities). Prompt: "Which of these agents is best suited to this task? Rank them and explain why." Parse the LLM response into reranked `AgentMatch` records with `match_source="llm_rerank"`. CostEvent emitted per §8.

**Why 40/60 instead of equal weighting:** Token matching is high-precision, low-recall; semantic matching is lower-precision, higher-recall. For a 16-agent catalog where the same capability is often expressed with different words in the manifest and the query, semantic is the more important signal. Token matching acts as a tie-breaker when semantic scores are close.

### §3.4 Confidence Semantics (Score ≠ Confidence)

A high score means "this agent matches the query well." A high confidence means "we're sure this match is correct and not a close competitor to another agent."

**Confidence formula:**

```
confidence = score × (1 - second_score / max(first_score, 0.0001))
```

Where `first_score` is the current candidate's fused score and `second_score` is the next-highest candidate's fused score. The intuition: if the top candidate scores 0.9 and the runner-up scores 0.85, we're *not* confident (they're tied-ish). If the top candidate scores 0.9 and the runner-up scores 0.3, we're confident.

**Thresholds:**
- `confidence >= 0.7`: return as-is, high confidence
- `0.5 <= confidence < 0.7`: return but flag as "ambiguous" in `rationale`
- `confidence < 0.5`: trigger LLM tie-break

**Fallback escalation:** If LLM tie-break also produces sub-threshold confidence, the Registry returns the top-k candidates with a `rationale` field populated as "ambiguous match — recommend human selection" and the caller (Spawner or MAC) decides whether to escalate to a human operator or accept the top candidate with explicit uncertainty.

### §3.5 Embedding Model Selection

The Registry depends on an `Embedder` abstraction:

```python
from typing import Protocol


class Embedder(Protocol):
    """Abstract embedding function. Concrete implementation injected at Runtime init."""

    def embed(self, text: str) -> list[float]:
        """Return a fixed-dimensional embedding vector for the input text."""
        ...

    @property
    def model_id(self) -> str:
        """Stable model identifier, e.g. 'voyage-3' or 'text-embedding-3-small'."""
        ...

    @property
    def dimension(self) -> int:
        """Vector dimensionality; used for sanity checks."""
        ...
```

**Embedding model consistency:** Stage 3 Memory's requirement R14 mandates `embedding_model_id` be recorded in the deployment manifest. The Registry's embedder MUST use the same model as Memory's — otherwise agent-capability embeddings would be incompatible with task-signature embeddings from Memory, and §3 wouldn't be able to share any embedding cache. The Runtime init cross-checks Memory's manifest embedding_model_id against the Registry's embedder.model_id and hard-fails on mismatch.

**Swappability:** Changing the embedder requires a Runtime restart plus rebuild of the capability embedding index. Stage 4 does not support hot embedder swaps (would invalidate live caches and violate R14 manifest integrity).

### §3.6 Why Not a Persistent Vector Store

For 16 agents, a persistent vector store is over-engineering. In-process indices rebuilt on load are:
- Faster to develop (no schema, no migration)
- Always consistent with the manifest
- Trivially inspectable in tests
- Zero infrastructure dependency

**When to revisit:** If the catalog grows past ~200 agents (unlikely for BMAD-anchored Praxis), the in-process index becomes a memory and latency problem. At that point the Registry can be backed by Mem0 (via Memory's facade) using the seed-corpus mechanism for capability storage. Stage 4 does not need this; Stage 6+ may.

### §3.7 Registry Errors

```python
class AgentRegistryError(Exception):
    """Base class for registry failures."""


class EmbedderMismatchError(AgentRegistryError):
    """Runtime's embedder model_id does not match Memory's manifest embedding_model_id."""


class LLMRerankError(AgentRegistryError):
    """LLM fallback returned unparsable output."""
```

**Error policy:** `EmbedderMismatchError` is a hard-fail at Runtime init (fail-fast on configuration bugs). `LLMRerankError` during query is a soft-fail: the Registry returns the pre-rerank results with `match_source="semantic"` and a `rationale` note.

---

## §4. Agent Spawner Design

The Spawner is the Orchestrator's operational core. It constructs agents, manages their lifecycle (including the ProducerMemoryProxy / ReviewerMemoryProxy type-level partitioning for information asymmetry enforcement), owns the durable jobs infrastructure that absorbs F-3, and enforces resource budgets. This section has four subsections:

- **§4.1** Agent construction — subagent and team modes, proxy partitioning
- **§4.2** Jobs Infrastructure (F-3 absorption, composition paragraph)
- **§4.3** Resource Budgets
- **§4.4** Polecat Cleanup

### §4.1 Agent Construction — Subagent and Team Modes

The Spawner exposes two spawn modes, mirroring Gas Town's Polecat lifecycle with Praxis-specific additions.

#### §4.1.1 Subagent Mode

**Semantics:** Spawn an agent within the current session. The child agent reports results back to the parent synchronously (via awaited coroutine). No inter-agent messaging; the child is effectively a scoped callable with its own tool allowlist, memory proxy, and resource budget.

**Use case:** The default spawn mode. Whenever a parent agent needs "some work done by a specialist without needing to coordinate with peers," subagent is the right choice. Cheaper (no separate session state, no cross-session messaging overhead) and simpler to reason about.

**Signature:**

```python
from typing import AsyncContextManager
from uuid import UUID


@dataclass(frozen=True)
class SpawnHandle:
    """Opaque reference to a spawned agent. Cleanup is guaranteed via the context manager."""
    spawn_id: UUID
    agent_name: str
    mode: "SpawnMode"  # SUBAGENT or TEAM
    parent_spawn_id: UUID | None


class SpawnMode(StrEnum):
    SUBAGENT = "subagent"
    TEAM = "team"


class AgentRole(StrEnum):
    """Agent role at spawn time — drives ProducerMemoryProxy / ReviewerMemoryProxy selection."""
    PRODUCER = "producer"  # Agent generates outputs; gets full MemoryProtocol via ProducerMemoryProxy
    REVIEWER = "reviewer"  # Agent evaluates producer outputs; gets narrowed ReviewerMemoryProtocol


class AgentSpawner:
    """The Orchestrator's agent construction and lifecycle surface.

    Constructed once per Runtime. Thread-safe. Owns the active spawn registry
    for §4.4 cleanup.
    """

    async def spawn_subagent(
        self,
        agent_name: str,
        *,
        role: AgentRole = AgentRole.PRODUCER,
        input_payload: AgentInputSchema,
        parent_spawn_id: UUID | None = None,
        context_budget_tokens: int | None = None,
    ) -> AsyncContextManager["SpawnedAgent"]:
        """Spawn an agent in subagent mode. Returns an async context manager
        that guarantees cleanup on exit (success or exception).

        Caller usage:

            async with spawner.spawn_subagent("bmad-agent-architect",
                                              role=AgentRole.PRODUCER,
                                              input_payload=task) as agent:
                result = await agent.run()
                # agent is cleaned up automatically on context exit

        Preconditions:
        - agent_name exists in the registry
        - input_payload validates against the agent's input_schema
        - parent_spawn_id, if provided, references an active spawn

        Postconditions:
        - A SpawnedAgent is returned, configured with the appropriate memory proxy
          (ProducerMemoryProxy or ReviewerMemoryProxy per `role`)
        - The spawn is registered in the active registry for §4.4 cleanup tracking
        - CostEvent(type="runtime.agent_spawn") emitted to Pi-Mono outbox
        - On context exit: resource release, cleanup CostEvent, registry deregistration
        """
        ...
```

#### §4.1.2 Team Mode

**Semantics:** Spawn an agent as an independent session. Team members can message each other directly via the §7 Inter-Agent Communication Bus. Uses the `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` substrate where applicable (reflected in Spawner config, not hardcoded).

**Use case:** When multiple independent work items need parallel execution AND agents may need to coordinate mid-task (e.g., Amelia spawns Quinn as a teammate while implementing so Quinn can start writing tests in parallel; Atelier wave-execution pattern from §1.4).

**Independence requirement (Atelier pattern, §1.4):** Team mode with parallelism requires an explicit independence claim from the caller. The caller passes an `independence_justification: str` argument; the Spawner records it in the spawn metadata for audit. If two team agents try to write to overlapping resources (filesystem paths, Memory keys), the Spawner flags a conflict at cleanup time — not at spawn time, because detecting the conflict at spawn time would require path prediction that isn't always possible. Post-hoc flagging means conflicts surface in Murat's Stage 4.4 test reports and the caller learns to tighten their independence claims.

```python
    async def spawn_team(
        self,
        agent_names: tuple[str, ...],
        *,
        roles: tuple[AgentRole, ...],
        input_payloads: tuple[AgentInputSchema, ...],
        independence_justification: str,
        parent_spawn_id: UUID | None = None,
    ) -> AsyncContextManager[tuple["SpawnedAgent", ...]]:
        """Spawn a team of agents in parallel sessions.

        Length of agent_names, roles, and input_payloads MUST match.
        independence_justification is non-empty and recorded in spawn metadata.

        Team members can message each other via the §7 Inter-Agent Communication
        Bus. Parent waits for all team members (or until the first raises) via
        asyncio.gather semantics.
        """
        ...
```

#### §4.1.3 The ProducerMemoryProxy / ReviewerMemoryProxy Partitioning

**This is the section Andrey's checkpoint 1 asks me to justify. It is the structural implementation of information asymmetry per Winston §9's "structural, not trusted" mandate and the Atelier Poirot Blind Review pattern (§1.4).**

**Problem statement:** Reviewer agents (Quinn QA, Murat Test Architect, Cleo Clean Code Reviewer, and any agent invoked in `AgentRole.REVIEWER` mode) must not be able to see the producer's prior reasoning trace. If a reviewer can call `Memory.retrieve_similar_tasks()` and get the producer's outputs returned to them, the multi-agent quality advantage collapses — reviews become echo-chamber validations of the producer's prior choices rather than independent blind investigations.

**Non-solution (rejected per frame verification):** A runtime allowlist that blocks reviewer agents from calling certain Memory methods. This is a *trusted* control — a single configuration bug in the allowlist = asymmetry breach. Winston §9 explicitly says "structural, not trusted." Fails the bar.

**Rejected alternative (B):** Add a `visibility_scope` parameter to Memory's facade retrieve methods. This would require unfreezing `memory/src/` (violates binding condition #4) and would leak agent-role concepts into Memory's layer (Memory doesn't know about agent roles; roles are a Runtime concept).

**Chosen design — type-level Protocol partitioning:**

Define two distinct Protocol types. The full `MemoryProtocol` already exists in `memory/_internal/protocol.py` with 10 methods (3 write, 3 read, 3 GDPR, 1 health). Runtime defines a narrower `ReviewerMemoryProtocol` in its own namespace that exposes a strict subset — specifically, the methods that a reviewer legitimately needs without leaking producer context:

```python
from typing import Protocol, runtime_checkable

from praxis.kernel.memory.models import (
    DecisionDraft,
    DecisionRecord,
    QuarantineReason,
    QuarantineResult,
)


@runtime_checkable
class ReviewerMemoryProtocol(Protocol):
    """Strict-subset view of MemoryProtocol for agents in AgentRole.REVIEWER mode.

    This Protocol EXCLUDES by design (not by gating):
    - retrieve_similar_tasks  — would leak producer's prior work
    - retrieve_decisions       — would leak producer's decision history
    - retrieve_facts           — would leak producer's Mem0 facts
    - store_task_outcome       — producer-side capture; not a reviewer activity
    - store_fact               — producer-side knowledge building; not a reviewer activity
    - delete / export          — GDPR operations, tenant-admin surface, not agent surface
    - health                   — ops-level, not agent surface

    Reviewers get:
    - store_decision           — capture the review decision as an Atelier decision record
    - flag_and_quarantine      — mark problematic producer outputs (the defining reviewer action)

    Enforcement semantics: any reviewer agent that attempts to call a method
    not on this Protocol will hit AttributeError at the Python interpreter
    level. There is no runtime check. There is no allowlist. The method is
    literally not present on the object. Misconfiguration is structurally
    impossible because there is nothing to misconfigure.
    """

    async def store_decision(
        self,
        tenant_id: str,
        decision: DecisionDraft,
    ) -> DecisionRecord:
        """Capture an Atelier-style decision record. Reviewers use this to log
        their review decisions ('producer output X is flagged because Y')."""
        ...

    async def flag_and_quarantine(
        self,
        tenant_id: str,
        entry_id: str,
        reason: QuarantineReason,
        free_text: str | None = None,
    ) -> QuarantineResult:
        """The defining reviewer action: mark a producer-produced record as
        quarantined. Embedding is stripped in-place per Memory Req #35 /
        FM3.10."""
        ...


@runtime_checkable
class ProducerMemoryProtocol(Protocol):
    """Full-surface Memory view for agents in AgentRole.PRODUCER mode.

    Structurally identical to the existing MemoryProtocol — exposed as a
    distinct name in the Runtime layer so that the Spawner's construction
    path is type-aware. Producer agents get this protocol; reviewer agents
    get the narrower one above.

    Note: This is not a re-declaration of MemoryProtocol. It is a Runtime-layer
    alias that imports MemoryProtocol and re-exports it under the Role-tagged
    name. The aliasing makes the Spawner's type signatures readable:

        def spawn_subagent(..., memory: ProducerMemoryProtocol | ReviewerMemoryProtocol)
    """
    # Full interface is inherited from MemoryProtocol via structural typing.
    # See praxis.kernel.memory._internal.protocol.MemoryProtocol for the 10-method surface.
    ...
```

**Why two named Protocols instead of `ReviewerMemoryProtocol` + bare `MemoryProtocol`:** Clarity. The Spawner's construction signature reads `memory: ProducerMemoryProtocol | ReviewerMemoryProtocol`, which immediately communicates to every reader that the Spawner is aware of the asymmetry. Using the bare `MemoryProtocol` would obscure the partition.

**Why `ProducerMemoryProtocol` is a pass-through:** Because the full `MemoryProtocol` already exists and is the authoritative contract. Re-declaring its method signatures here would (a) risk drift from the Memory package's canonical definition and (b) violate DRY. The aliasing is purely a type-readability convenience; structurally `ProducerMemoryProtocol` and `MemoryProtocol` are the same type.

#### §4.1.4 The Proxy Classes — Runtime Construction

Each spawned agent is constructed with a proxy object that wraps the real `Memory` facade. The proxy type is selected at construction time based on `AgentRole`:

```python
from praxis.kernel.memory import Memory  # the concrete facade from Stage 3


class ProducerMemoryProxy:
    """Full-surface proxy exposing ProducerMemoryProtocol.

    Forwards every call to the underlying Memory facade. Adds:
    - Automatic tenant_id injection from the Orchestrator manifest (R6 defense-in-depth)
    - Per-call audit tagging for §8 CostEvent attribution
    - Rate-limiting hooks for §4.3 Resource Budgets
    """

    def __init__(self, memory: Memory, *, tenant_id: str, agent_name: str, spawn_id: UUID) -> None:
        self._memory = memory
        self._tenant_id = tenant_id
        self._agent_name = agent_name
        self._spawn_id = spawn_id

    async def store_task_outcome(self, tenant_id: str, task, outcome):
        self._cross_check_tenant(tenant_id)
        return await self._memory.store_task_outcome(tenant_id, task, outcome)

    async def store_decision(self, tenant_id: str, decision):
        self._cross_check_tenant(tenant_id)
        return await self._memory.store_decision(tenant_id, decision)

    async def store_fact(self, tenant_id, agent_id, run_id, fact):
        self._cross_check_tenant(tenant_id)
        return await self._memory.store_fact(tenant_id, agent_id, run_id, fact)

    async def retrieve_similar_tasks(self, tenant_id, signature, top_k=5, min_similarity=0.75):
        self._cross_check_tenant(tenant_id)
        return await self._memory.retrieve_similar_tasks(tenant_id, signature, top_k, min_similarity)

    async def retrieve_decisions(self, tenant_id, query, top_k=10):
        self._cross_check_tenant(tenant_id)
        return await self._memory.retrieve_decisions(tenant_id, query, top_k)

    async def retrieve_facts(self, tenant_id, agent_id, run_id, query, top_k=10):
        self._cross_check_tenant(tenant_id)
        return await self._memory.retrieve_facts(tenant_id, agent_id, run_id, query, top_k)

    async def delete(self, tenant_id, criteria):
        self._cross_check_tenant(tenant_id)
        return await self._memory.delete(tenant_id, criteria)

    async def export(self, tenant_id, criteria):
        self._cross_check_tenant(tenant_id)
        return await self._memory.export(tenant_id, criteria)

    async def flag_and_quarantine(self, tenant_id, entry_id, reason, free_text=None):
        self._cross_check_tenant(tenant_id)
        return await self._memory.flag_and_quarantine(tenant_id, entry_id, reason, free_text)

    async def health(self):
        return await self._memory.health()

    def _cross_check_tenant(self, caller_tenant_id: str) -> None:
        """Defense-in-depth per brief §2.4 item (d).

        Raises if the caller-provided tenant_id does not match the proxy's
        configured tenant_id. Since the proxy is constructed with the
        Orchestrator manifest's tenant_id, any divergence is a structural
        bug or a malicious agent attempt to cross scopes.
        """
        if caller_tenant_id != self._tenant_id:
            raise PermissionError(
                f"ProducerMemoryProxy: caller tenant_id={caller_tenant_id!r} "
                f"does not match Spawner manifest tenant_id={self._tenant_id!r}"
            )


class ReviewerMemoryProxy:
    """Strict-subset proxy exposing ONLY ReviewerMemoryProtocol.

    Two methods. That is the entire interface. Any attempt to call
    retrieve_similar_tasks, retrieve_decisions, retrieve_facts,
    store_task_outcome, store_fact, delete, export, or health on this
    object raises AttributeError at the Python interpreter level.

    This is the structural enforcement of information asymmetry. There is
    no allowlist. There is no runtime role check. The methods are not
    present.
    """

    def __init__(self, memory: Memory, *, tenant_id: str, agent_name: str, spawn_id: UUID) -> None:
        self._memory = memory
        self._tenant_id = tenant_id
        self._agent_name = agent_name
        self._spawn_id = spawn_id

    async def store_decision(self, tenant_id: str, decision):
        self._cross_check_tenant(tenant_id)
        return await self._memory.store_decision(tenant_id, decision)

    async def flag_and_quarantine(self, tenant_id: str, entry_id: str, reason, free_text=None):
        self._cross_check_tenant(tenant_id)
        return await self._memory.flag_and_quarantine(tenant_id, entry_id, reason, free_text)

    def _cross_check_tenant(self, caller_tenant_id: str) -> None:
        if caller_tenant_id != self._tenant_id:
            raise PermissionError(
                f"ReviewerMemoryProxy: caller tenant_id={caller_tenant_id!r} "
                f"does not match Spawner manifest tenant_id={self._tenant_id!r}"
            )
```

**Critical property:** `ReviewerMemoryProxy` has NO `retrieve_*` methods, NO `store_task_outcome`, NO `store_fact`, NO `delete`, NO `export`, NO `health`. A reviewer agent holding an instance of this class LITERALLY CANNOT call `retrieve_similar_tasks` — `hasattr(proxy, "retrieve_similar_tasks")` is `False`, and `proxy.retrieve_similar_tasks(...)` raises `AttributeError: 'ReviewerMemoryProxy' object has no attribute 'retrieve_similar_tasks'`.

This is as structural as Python permits without capability-language enforcement. There is no runtime check to forget, no allowlist to misconfigure, no role string to typo. The enforcement is in the class definition itself.

#### §4.1.5 The Spawner's Agent-Construction Path (Checkpoint 1 Deliverable)

```python
class AgentSpawner:

    def __init__(
        self,
        registry: AgentRegistry,
        memory: Memory,
        manifest: DeploymentManifest,
        cost_tracker: "CostTracker",  # Pi-Mono
        jobs_store: "JobsStore",       # §4.2
    ) -> None:
        self._registry = registry
        self._memory = memory
        self._manifest = manifest
        self._cost_tracker = cost_tracker
        self._jobs_store = jobs_store
        self._active_spawns: dict[UUID, "SpawnedAgent"] = {}

    def _construct_memory_proxy(
        self,
        role: AgentRole,
        agent_name: str,
        spawn_id: UUID,
    ) -> ProducerMemoryProxy | ReviewerMemoryProxy:
        """The type-level partitioning happens here and nowhere else.

        This is the entire structural enforcement of information asymmetry.
        Every spawned agent's memory handle is constructed through this
        method; no other code path exists to create a memory proxy.
        """
        if role is AgentRole.PRODUCER:
            return ProducerMemoryProxy(
                memory=self._memory,
                tenant_id=self._manifest.tenant_id,
                agent_name=agent_name,
                spawn_id=spawn_id,
            )
        if role is AgentRole.REVIEWER:
            return ReviewerMemoryProxy(
                memory=self._memory,
                tenant_id=self._manifest.tenant_id,
                agent_name=agent_name,
                spawn_id=spawn_id,
            )
        raise ValueError(f"unknown AgentRole: {role}")
```

**Properties of this construction path:**

1. **Single point of proxy creation.** Every memory handle an agent ever holds flows through `_construct_memory_proxy`. There is no other path. Future audits (Murat's Stage 4.4, Cleo's code review) have a single grep target: `grep "_construct_memory_proxy" praxis/kernel/runtime/`.

2. **Role is explicit at spawn time.** The caller MUST pass `AgentRole.PRODUCER` or `AgentRole.REVIEWER` when invoking `spawn_subagent` or `spawn_team`. There is no default; omitting the argument is a TypeError. This forces callers to think about the asymmetry at every spawn site.

3. **Type-level verification in Murat's test suite.** Static analysis (mypy / pylance) checks whether callers that bind reviewer agents try to call producer-only methods on the proxy. Misuse surfaces at development time, not at runtime.

4. **No back-door.** `SpawnedAgent` does not expose `self._memory` or a way to escape the proxy. The agent's only memory access is via the proxy assigned at construction.

**§4.1 status:** Checkpoint 1 deliverable complete. §4.1.3 defines the Protocol narrowing; §4.1.4 defines the proxy classes; §4.1.5 defines the Spawner's construction path. Ready for Andrey verification before §6 drafting begins.

### §4.2 Jobs Infrastructure (F-3 Absorption)

**Purpose:** Provide the durable substrate for the Memory retention reaper, satisfying NFR-C-A1 (7-day crypto-shred SLA) and NFR-Q6 (5-min RTO). This is the F-3 absorption per the deferred-findings brief.

#### §4.2.1 Composition With §8.1 — This Is a Correctness Requirement, Not an Optimization

> **Composition statement (bold because it is load-bearing):**
>
> The F-1 outbox adapter (defined in full in §8.1) and the F-3 jobs infrastructure are NOT independent components. They share a single deployment Postgres instance that hosts both `jobs_queue` and `events_outbox` as peer tables. This composition is **load-bearing for NFR-C-A1** because it enables Path A (reaper-direct CostEvent emission, §8.1) to preserve Memory architecture §3.5's "same database transaction" invariant for `memory.retention_action` CostEvents. When the reaper worker completes a retention job, the transaction that updates `jobs_queue.state='completed'` ALSO inserts the corresponding `CostEvent` into `events_outbox`. One transaction = atomicity = audit trail mathematically sound by construction. Separating the jobs table and the outbox into different datastores would force a two-phase commit or a saga pattern for retention_action emission, both of which would weaken the NFR-C-A1 audit guarantee from schema-enforced to orchestration-enforced.
>
> **The shared-DB topology is therefore not an optimization — it is a correctness requirement.** Any future proposal to split the jobs store and the outbox into independent datastores must re-derive the NFR-C-A1 guarantee under the new topology. I do not expect such a derivation to succeed.

This composition is referenced from §4.2, §8.1 (where Path A is fully elaborated), and §9 Security Model (where the NFR-C-A1 structural claim is consolidated).

#### §4.2.2 The `jobs_queue` Schema

```sql
-- Praxis Runtime — jobs_queue
-- Lives in the deployment-scoped Postgres alongside Pi-Mono's events_outbox.

CREATE TYPE job_type_enum AS ENUM (
    'retention_shred',       -- Memory right-to-erasure crypto-shred
    'retention_cascade',     -- Memory full-tenant delete cascade
    'quarantine_promote',    -- Async quarantine-to-delete transition
    'backup_rewrite',        -- Post-delete backup key destruction
    -- ... extensible via Praxis releases
);

CREATE TYPE job_state_enum AS ENUM (
    'pending',        -- Created, awaiting worker claim
    'claimed',        -- Worker claimed; claim_token and claim_expires_at set
    'in_progress',    -- Worker actively running; started_at set
    'completed',      -- Success; completed_at set
    'failed',         -- Transient failure; next_retry_at set
    'abandoned',      -- Max retries exceeded, operator intervention required
    'poisoned'        -- Pathological failure; NEVER retried, alerts operator
);

CREATE TYPE failure_reason_enum AS ENUM (
    'transient_backend',
    'backend_timeout',
    'invariant_violation',
    'tenant_drift',            -- R4 manifest drift detected mid-execution
    'resource_exhaustion',
    'unknown'
);

CREATE TABLE jobs_queue (
    id                   UUID PRIMARY KEY,
    tenant_hash          TEXT NOT NULL,                        -- R6 base-model mandatory
    job_type             job_type_enum NOT NULL,
    payload_json         JSONB NOT NULL,                       -- typed per job_type, schema in runtime code
    state                job_state_enum NOT NULL DEFAULT 'pending',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    claimed_at           TIMESTAMPTZ,
    started_at           TIMESTAMPTZ,
    completed_at         TIMESTAMPTZ,
    retry_count          INT NOT NULL DEFAULT 0,
    max_retries          INT NOT NULL,                         -- set at creation per job_type policy
    next_retry_at        TIMESTAMPTZ,
    last_error           TEXT,
    failure_reason       failure_reason_enum,
    claim_token          UUID,                                 -- fencing against zombie workers
    claim_expires_at     TIMESTAMPTZ,                          -- for crash detection; typically claimed_at + 5 min
    parent_job_id        UUID REFERENCES jobs_queue(id),       -- for cascade tracking (e.g., retention_cascade spawns retention_shred children)
    dedup_key            TEXT,                                 -- optional; unique per (tenant_hash, dedup_key) when non-null
    retry_state          JSONB NOT NULL DEFAULT '{}'::jsonb,   -- per Andrey's correction: retry-tracking lives durably in this column, NOT in a sidecar map

    CONSTRAINT tenant_hash_not_empty CHECK (tenant_hash <> ''),
    CONSTRAINT retry_bounds CHECK (retry_count >= 0 AND retry_count <= max_retries + 1),
    CONSTRAINT claim_consistency CHECK (
        (state = 'claimed') = (claim_token IS NOT NULL AND claim_expires_at IS NOT NULL)
    )
);

-- Worker pick query
CREATE INDEX idx_jobs_pending_pickup ON jobs_queue (next_retry_at NULLS FIRST, created_at)
    WHERE state = 'pending';

-- Orphan reclaim query (NFR-Q6 crash recovery)
CREATE INDEX idx_jobs_orphan_reclaim ON jobs_queue (claim_expires_at)
    WHERE state = 'claimed';

-- Idempotency enforcement for dedup_key
CREATE UNIQUE INDEX idx_jobs_dedup ON jobs_queue (tenant_hash, dedup_key)
    WHERE dedup_key IS NOT NULL;

-- Cascade tracking
CREATE INDEX idx_jobs_parent ON jobs_queue (parent_job_id)
    WHERE parent_job_id IS NOT NULL;
```

**Per-column notes:**

- **`retry_state JSONB`** — Per Andrey's binding correction on item 3(c): retry tracking for Path A CostEvent emission lives here durably, NOT in a sidecar in-memory map. If the reaper worker crashes mid-retry, the retry counter is preserved in Postgres and the crash-recovered worker picks up from the same state.
- **`parent_job_id`** — A `retention_cascade` job (full-tenant delete) may spawn multiple `retention_shred` child jobs. Parent tracking enables aggregate progress reporting and coordinated completion.
- **`dedup_key`** — Optional idempotency. When a retention job is submitted with a dedup_key, a second submission with the same (tenant_hash, dedup_key) is a no-op returning the original job. Prevents duplicate reaper work during crash-recovery replays.
- **`claim_expires_at`** — Set to `claimed_at + 5 minutes` at claim time. On worker restart, any row with `state='claimed' AND claim_expires_at < NOW()` is reclaimed as orphaned per §4.2.4.

#### §4.2.3 The `outbox_drain_retries` Table (Path B Retry State)

Per Andrey's binding correction, Path B (tick-drain for `memory.record_created` and `memory.retrieval_cache_hit`) also needs durable retry state. This lives in a separate, simpler table:

```sql
CREATE TABLE outbox_drain_retries (
    audit_event_id       UUID PRIMARY KEY,              -- matches Memory AuditEvent.id; also the dedup_key for events_outbox
    tenant_hash          TEXT NOT NULL,
    event_type           TEXT NOT NULL,                 -- 'memory.record_created' | 'memory.retrieval_cache_hit'
    first_seen_at        TIMESTAMPTZ NOT NULL,
    retry_count          INT NOT NULL DEFAULT 0,
    max_retries          INT NOT NULL DEFAULT 5,
    last_error           TEXT,
    next_retry_at        TIMESTAMPTZ NOT NULL,
    state                TEXT NOT NULL DEFAULT 'pending'  -- 'pending' | 'quarantined'
);

CREATE INDEX idx_outbox_retries_pending ON outbox_drain_retries (next_retry_at)
    WHERE state = 'pending';
```

**Why a separate table:** The `jobs_queue` schema is tuned for the reaper's retention jobs. Mixing tick-drain CostEvent retries into the same table would mean tick-drain rows compete with retention-job rows for the worker pick index. Separation keeps Path B's retry pipeline independent from the reaper's job pipeline, at the cost of one extra tiny table. Worth it.

#### §4.2.4 Worker Lifecycle

**Topology:** Single worker per deployment. Concurrent job processing via an async task pool inside the single worker process. This is driven by R1's single-tenant-per-deployment pin — horizontal worker scale is unnecessary at Stage 4. Multi-worker is a Stage 6+ optimization if load measurement demands it.

```python
class JobsWorker:
    """The retention reaper + tick drain worker.

    Single instance per deployment. Runs as an asyncio task pool inside the
    main Runtime process (or as a separate process if configured; topology
    decision is deployment-time).

    Two responsibilities:
    1. Claim and process jobs from jobs_queue (retention actions)
    2. Drain Memory.audit_buffer via the tick loop, writing to events_outbox
       with Path B idempotency
    """

    def __init__(
        self,
        jobs_store: "JobsStore",
        memory: Memory,
        cost_tracker: "CostTracker",
        manifest: DeploymentManifest,
        *,
        tick_interval_ms: int = 500,
        claim_duration_seconds: int = 300,  # NFR-Q6 5-min RTO budget
        max_concurrent_jobs: int = 4,
    ) -> None:
        ...

    async def run(self) -> None:
        """Main worker loop. Runs until cancelled."""
        await self._reclaim_orphans_on_startup()
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._tick_drain_loop())  # Path B
            tg.create_task(self._jobs_worker_loop())  # Path A job processing

    async def _reclaim_orphans_on_startup(self) -> None:
        """NFR-Q6 RTO recovery: reclaim claimed-but-unfinished jobs from
        the prior (crashed) worker process."""
        async with self._jobs_store.transaction() as tx:
            await tx.execute(
                """
                UPDATE jobs_queue
                SET state='pending',
                    retry_count=retry_count + 1,
                    claim_token=NULL,
                    claim_expires_at=NULL,
                    last_error=COALESCE(last_error, '') || '; reclaimed on worker restart'
                WHERE state='claimed' AND claim_expires_at < NOW()
                """
            )
```

**Startup sequence:**

1. `_reclaim_orphans_on_startup()` runs first. One SQL UPDATE. Sub-second on the `idx_jobs_orphan_reclaim` partial index. Any jobs the prior worker crashed mid-claim are returned to the pending pool with retry_count incremented.
2. `_tick_drain_loop()` begins polling `Memory.audit_buffer` every `tick_interval_ms` (default 500 ms). For each batch, it opens a transaction, writes to `events_outbox` (with `audit_event_id` as the dedup key for idempotency), clears the drained entries from `Memory.audit_buffer`, and commits. See §8.1 Path B for full detail.
3. `_jobs_worker_loop()` queries `jobs_queue` for pending jobs, claims them with a fresh UUID claim_token and `claim_expires_at = NOW() + 5 minutes`, processes them (retention_shred, retention_cascade, etc.), and on completion updates the row to `state='completed'` IN THE SAME TRANSACTION as the Path A CostEvent insert to `events_outbox`.

**NFR-Q6 RTO guarantee:** Worker startup (seconds) + orphan reclaim query (<1 second) ≈ much less than 5 minutes. Comfortable margin. If the worker restarts under load, the orphan reclaim runs before any new work is claimed, so newly-claimed jobs cannot mask unfinished prior work.

#### §4.2.5 Failure Recovery Semantics

**Retry budget:** Each job has `max_retries` (set at creation per job_type policy — e.g., `retention_shred` gets 10, quick jobs get 3). On failure:
- `retry_count < max_retries` → `state='failed'`, `next_retry_at = NOW() + backoff(retry_count)`, `retry_count += 1`
- `retry_count >= max_retries` → `state='abandoned'` OR `state='poisoned'` depending on failure_reason:
  - `failure_reason IN ('transient_backend', 'backend_timeout')` → `abandoned` (might recover later with operator help)
  - `failure_reason IN ('invariant_violation', 'tenant_drift', 'unknown')` → `poisoned` (pathological; operator must intervene)

**Alerting severity by job_type:**
- `retention_shred` poison → **P1 alert** (NFR-C-A1 SLA in flight)
- `retention_cascade` poison → **P1 alert** (GDPR Article 17 obligation)
- `quarantine_promote` poison → **P2 alert** (operational backlog)
- `backup_rewrite` poison → **P1 alert** (backup integrity)

**No auto-abandon for poison.** Human review is mandatory. Break-glass tooling for manual reprocess exists but is audit-logged per Memory Req #47 (state-column transitions via DB triggers + break-glass ledger).

**Backoff function:**

```python
def backoff(retry_count: int) -> timedelta:
    """Exponential backoff with jitter. retry_count is 0-indexed."""
    base_seconds = 2 ** min(retry_count, 8)  # cap exponent to avoid absurd delays
    jitter = random.uniform(0.75, 1.25)
    return timedelta(seconds=base_seconds * jitter)
```

At `retry_count=8`, backoff is ~4-8 minutes. After `max_retries` (typically 10), total elapsed retry time is hours, not days. NFR-C-A1 7-day SLA has wide margin.

#### §4.2.6 Deployment Topology Decision — Tenant-Scoped Postgres

**Decision:** Tenant-scoped Postgres per deployment. One Postgres instance per Praxis deployment, hosting both `jobs_queue` (this section) and `events_outbox` (§8.1) + any other Runtime-owned durable state.

**Rationale (from the brief §3.2 item 5):**
- **R11 as structural impossibility, not policy.** Per-deployment DB makes cross-tenant retrieval a non-existent code path literally. Shared-with-RLS preserves R11 *by policy* (one RLS bug = cross-tenant leak).
- **R3 manifest signing + DB fingerprint.** Manifest already records DB fingerprint; per-deployment DB makes this trivially enforceable via connection-string validation at boot.
- **Blast radius.** Shared Postgres outage = all tenants down. Per-deployment = one tenant.
- **Praxis scale at Stage 4.** Managed single-tenant deployments, not thousand-tenant SaaS. Operational N-DB cost is acceptable.

**Concrete implications:**
- The Runtime's config accepts a single `database_url` pointing to the deployment-local Postgres.
- `DeploymentManifest.database_fingerprint` (per R3) is cross-checked against the running DB's `server_version` + `catalog_name` + `datname` at Runtime boot. Mismatch → hard-fail with `DeploymentManifestDriftError`.
- Memory's own backing stores (Beads, Mem0) may live in the same Postgres (via separate schemas) or in separate infrastructure (SQLite beads, separate Mem0 Postgres). This is a Memory config concern; Runtime just ensures the jobs + outbox DB is co-located.

### §4.3 Resource Budgets

Every spawned agent has a resource budget enforced by Pi-Mono (§8 CostTracker integration).

**Budget dimensions:**
- **Token budget** — max input + output tokens the agent may consume, enforced via Pi-Mono's `track_cost` with a hard-fail on overrun
- **Wall-time budget** — max seconds the agent may run before cancellation
- **Tool-call count** — max MCP tool invocations (see §5); prevents runaway tool-calling loops
- **Memory-write count** — max `store_*` calls to Memory; prevents runaway memory writes

```python
@dataclass(frozen=True)
class ResourceBudget:
    """Hard ceilings enforced by the Spawner."""
    max_tokens: int
    max_wall_seconds: float
    max_tool_calls: int
    max_memory_writes: int

    @classmethod
    def default_for_role(cls, role: AgentRole) -> "ResourceBudget":
        if role is AgentRole.PRODUCER:
            return cls(max_tokens=200_000, max_wall_seconds=600.0, max_tool_calls=100, max_memory_writes=50)
        if role is AgentRole.REVIEWER:
            return cls(max_tokens=100_000, max_wall_seconds=300.0, max_tool_calls=40, max_memory_writes=20)
        raise ValueError(f"unknown role: {role}")
```

**Enforcement:** Budget checks run on every token-consuming call (Pi-Mono integration), every tool invocation (§5 adapter), every Memory write (via the proxy). Budget overrun raises `BudgetExceededError`, which the Spawner catches, cancels the agent, emits a `CostEvent(type="runtime.budget_exceeded")`, and returns a structured failure to the parent.

**Non-bypassable:** The budget is enforced at the proxy layer (§4.1.4) and at the tool adapter layer (§5). Agents have no way to read or modify their own budget. Attempting to construct a new ResourceBudget inside an agent's tool call does nothing — the Spawner's budget is authoritative.

### §4.4 Polecat Cleanup

Every spawn lifecycle has guaranteed cleanup. This section describes how.

#### §4.4.1 Cleanup Guarantees

**Contract:** When `spawn_subagent` or `spawn_team` is used as an async context manager (the only intended usage), cleanup runs on context exit regardless of whether the exit is normal or exceptional.

```python
async with spawner.spawn_subagent("winston", role=AgentRole.PRODUCER, input_payload=task) as agent:
    result = await agent.run()
# <-- cleanup happens here, always
```

Cleanup includes:
1. **Resource release** — cancel pending tool calls, close MCP client connections used only by this spawn, release the memory proxy handle
2. **Active spawn registry deregistration** — remove the spawn from `AgentSpawner._active_spawns`
3. **Final CostEvent emission** — `CostEvent(type="runtime.agent_terminate")` with aggregate resource usage for the spawn
4. **Parent notification** — if parent is waiting on team-mode completion, wake the parent with the spawn's final state

#### §4.4.2 Orphan Sweeping (Gas Town Pattern, §1.3)

Despite the context-manager discipline, orphans can still occur:
- Process SIGKILL (no __aexit__ run)
- Asyncio cancellation edge cases
- Bugs in nested context management

The Spawner runs an orphan sweeper on:
- **Runtime startup** — scan for spawns persisted to `jobs_queue` (for team-mode parents that wrote checkpoint state) that are marked `in_progress` but whose claim has expired. Reclaim as orphaned.
- **Every Orchestrator tick** (piggybacking on the §4.2 tick drain) — scan `AgentSpawner._active_spawns` for spawns whose last-heartbeat time exceeds a threshold (default 2 minutes). Mark these as "suspected stuck" and initiate cleanup.

**Why not Gas Town's `gt deacon cleanup-orphans`:** That pattern scans host processes for orphaned TTYs. Praxis agents run as asyncio tasks inside a single Python process (or asyncio subprocesses for team mode), not as detached shell processes. The Python-native equivalent is asyncio task inspection + heartbeat tracking, which is what §4.4.2 does.

---

## §5. MCP Tool Adapter Design

The MCP Tool Adapter is the boundary between Praxis's agents and the external MCP ecosystem. It provides (a) per-tool client lifecycle management, (b) per-agent allowlist enforcement per §9, (c) result normalization, (d) CostEvent emission, and (e) error handling.

### §5.1 Client Integration — Official Python SDK

**Decision:** Use the official `mcp` Python SDK (`mcp.client`) via its stdio and HTTP client transports. Do NOT reimplement MCP.

**Rationale:**
- MCP is a standard; rolling our own fractures the ecosystem
- The SDK handles JSON-RPC framing, tool discovery, reconnection, and streaming results
- Boring technology for stability (§1 principle)

**Version pinning:** The SDK version is pinned in `pyproject.toml`. Breaking upstream changes trigger the tool-library versioning protocol (Carson §5.2) — stage the old version for one release while migrating.

### §5.2 Tool Registry Data Model

```python
from enum import StrEnum


class ToolBlastRadiusClass(StrEnum):
    """Carson §5.6 blast radius tiering — drives sandbox policy in §9."""
    A = "A"  # Inert — read-only, no egress beyond request
    B = "B"  # Scoped egress — read + network to known public APIs
    C = "C"  # Tenant data surface — read/write within tenant-scoped datastores
    D = "D"  # Destructive / escalation-capable — write to external state
    E = "E"  # Unbounded — sandbox-escape capable; NOT ADMITTED (auto-P2 at best)


@dataclass(frozen=True)
class ToolDescriptor:
    """Metadata for a single tool in the Praxis tool library.

    Sourced from Carson's P0/P1 list; new tools enter via the §5.4 intake protocol.
    """
    name: str
    mcp_server_id: str               # e.g. 'tavily-mcp', 'github-mcp'
    blast_class: ToolBlastRadiusClass
    read_mode_capable: bool
    write_mode_capable: bool
    default_mode: str                 # 'read-only' per §9 default-deny, overridable per-agent
    persona_anchors: tuple[str, ...]  # from Carson's per-tool cards
    hat_anchors: tuple[str, ...]      # from Carson's per-tool cards
    compliance_flags: tuple[str, ...] # R11, R30, R31, R36, R53 touches
    input_schema_hint: str | None = None  # typed schema reference if available
    output_schema_hint: str | None = None
```

**The Registry:**

```python
class ToolRegistry:
    """Catalogue of all known tools. Built at Runtime init from the tool library
    spec in §6 (which is anchored on Carson's tool-library-requirements.md)."""

    def __init__(self, descriptors: tuple[ToolDescriptor, ...]) -> None:
        self._by_name = {d.name: d for d in descriptors}

    def get(self, name: str) -> ToolDescriptor:
        try:
            return self._by_name[name]
        except KeyError as e:
            raise UnknownToolError(f"tool {name!r} not in registry") from e

    def all(self) -> tuple[ToolDescriptor, ...]:
        return tuple(self._by_name.values())

    def by_blast_class(self, klass: ToolBlastRadiusClass) -> tuple[ToolDescriptor, ...]:
        return tuple(d for d in self._by_name.values() if d.blast_class == klass)
```

### §5.3 The MCP Tool Adapter

```python
class MCPToolAdapter:
    """The runtime boundary for MCP tool invocation.

    Responsibilities:
    - Hold per-tool MCP client connections (lazy-open, pooled)
    - Enforce the caller agent's tool allowlist (§9)
    - Validate inputs against the tool's JSON Schema
    - Invoke the tool via mcp.client
    - Normalize results to Pydantic or TONL
    - Emit CostEvent per invocation
    - Wrap errors in Praxis's hierarchy
    """

    def __init__(
        self,
        registry: ToolRegistry,
        cost_tracker: "CostTracker",
        manifest: DeploymentManifest,
    ) -> None:
        self._registry = registry
        self._cost_tracker = cost_tracker
        self._manifest = manifest
        self._clients: dict[str, "mcp.client.Session"] = {}  # lazy

    async def invoke(
        self,
        *,
        caller_agent: AgentRuntimeConfig,
        tool_name: str,
        mode: str,  # 'read' or 'write'
        payload: BaseModel,
        spawn_id: UUID,
    ) -> BaseModel | str:
        """Invoke a tool on behalf of an agent.

        Pipeline:
        1. Allowlist check — caller_agent.tool_allowlist must contain tool_name
        2. Mode check — if mode='write', tool must be write_mode_capable AND
           agent's per-tool mode grant must include write
        3. Input validation — payload validates against tool's input schema
        4. Client acquisition — lazy-open MCP session for the tool's server
        5. Invocation — mcp.client.call_tool
        6. Result normalization
        7. CostEvent emission
        8. Return
        """
        descriptor = self._registry.get(tool_name)
        if tool_name not in caller_agent.tool_allowlist:
            raise ToolNotAllowedError(
                f"agent {caller_agent.agent.name!r} has no allowlist entry for {tool_name!r}"
            )
        if mode == "write" and not descriptor.write_mode_capable:
            raise ToolCapabilityError(f"tool {tool_name!r} does not support write mode")
        # ... (full pipeline in Amelia's implementation)
```

### §5.4 Result Normalization

**Decision:** Return Pydantic models when the tool has a typed output schema, else return TONL-encoded text when the tool has a declared text output shape, else return raw text (fallback).

**Why TONL for unstructured outputs:** Stage 2's compression integration. Tools that return long unstructured text (Tavily research results, Context7 doc lookups) are TONL-encodable — Stage 2 compression handles this transparently, reducing token footprint in the agent's LLM context.

**Pydantic validation is strict.** If the tool's output schema says a field is an int and the MCP server returns a string, the adapter raises `ToolResultValidationError` rather than coercing. The agent's LLM context should never see a silently-coerced wrong type.

### §5.5 Sandboxing Mechanism

**Philosophy:** The MCP Tool Adapter does NOT implement sandboxing. Sandboxing is the tool server's responsibility (Tavily sandboxes its browser, GitHub MCP sandboxes its shell ops, etc.). The Adapter enforces *trust boundaries at the selection layer*, not at the execution layer:

- **Allowlist per agent** — which tools can each agent invoke? Enforced at §5.3 step 1.
- **Mode per agent** — which tools can the agent invoke in write mode? Enforced at §5.3 step 2.
- **Tenant credential scoping** — per R31, each deployment uses its own credentials for each MCP server. The Adapter holds credentials in memory from the deployment manifest; agents never see them.
- **Budget enforcement** — each tool invocation is cost-tracked; budget exhaustion terminates the spawn.

**The high-risk exceptions — Class D tools:** Per Carson §5.6 and the decision resolution on §6.9.2, Class D tools (Kubernetes write, Terraform apply, Vault write, etc.) are **P2-capped and not admitted at Stage 4 launch**. The destructive-op approval workflow required to make Class D safe is deferred to Stage 5 MAC or Stage 7 POV Harness. Stage 4 ships Class D tools only in their read-only mode (if the tool supports it, e.g., Kubernetes MCP at P1).

**The subprocess / Python sandbox split (Carson §6.8):** Subprocess is Class D (tight per-binary allowlist, Amelia/Barry/Quinn only, specific binaries: pytest/ruff/mypy/python/pip). Python sandbox is Class C (broad allowlist, containerized execution, no-network default). Full treatment in §6.

### §5.6 Error Hierarchy

```python
class MCPAdapterError(Exception):
    """Base class for all MCP Tool Adapter errors."""


class UnknownToolError(MCPAdapterError):
    """Tool name not in the registry."""


class ToolNotAllowedError(MCPAdapterError):
    """Caller agent has no allowlist entry for this tool."""


class ToolCapabilityError(MCPAdapterError):
    """Caller requested a mode (read/write) the tool does not support or the agent is not granted."""


class ToolInputValidationError(MCPAdapterError):
    """Payload failed validation against the tool's input schema."""


class ToolInvocationError(MCPAdapterError):
    """MCP server returned an error or the invocation failed at the protocol level."""


class ToolResultValidationError(MCPAdapterError):
    """MCP server returned a result that failed validation against the declared output schema."""


class ToolBudgetExceededError(MCPAdapterError):
    """The caller's resource budget was exhausted before or during this invocation."""
```

**Policy:** Every error is caught by the Spawner and surfaces as a structured failure in the agent's result. No raw exceptions cross the agent boundary. The agent's LLM context sees `ToolInvocationError: GitHub MCP returned 404 for repo X` (or equivalent), not a Python traceback.

### §5.7 Retries and Rate Limits

**Retry policy:** Transient errors (network timeouts, 5xx responses, rate-limit 429s) are retried automatically with exponential backoff, up to 3 retries. Permanent errors (4xx, validation failures, allowlist denials) are NOT retried.

**Rate limits:** Each MCP server has a configurable rate-limit envelope per deployment. The Adapter enforces this at invocation time via a token-bucket limiter. Rate-limit exhaustion raises `ToolInvocationError` with retry-after metadata; the caller can choose to wait or fail.

**Back-pressure:** If a high-frequency caller (e.g., a runaway agent) saturates a tool's rate limit, the budget enforcement (§4.3) terminates the spawn before the rate limit becomes a deployment-wide problem.

---

## §5 End — Checkpoint 1 Boundary

**Status:** §1 Reference Analysis, §2 Agent Definition Schema, §3 Agent Registry Design, §4 Agent Spawner Design (including §4.1 Spawner + ProducerMemoryProxy/ReviewerMemoryProxy partitioning, §4.2 Jobs Infrastructure + §8.1 composition paragraph, §4.3 Resource Budgets, §4.4 Polecat Cleanup), §5 MCP Tool Adapter Design.

**Halt at §5 boundary per Andrey's draft cadence instruction.** §6 Tool Library Catalog, §7 Inter-Agent Communication Bus, §8 Integration Contracts (where §8.1 Path A/Path B gets the full treatment), §9 Security Model are NOT drafted. Andrey's checkpoint brief on the Spawner agent-construction path and the ReviewerMemoryProtocol narrowing is the gate for proceeding to §6.

**Forward references in §1–§5 that will be resolved in §6–§9:**
- §2.3 default tool allowlist → §6 + §9
- §4.2 composition paragraph → §8.1 (full Path A/Path B elaboration)
- §4.3 ResourceBudget → §9 budget enforcement consolidation
- §4.4 heartbeat sweeper → §10 Observability Hooks
- §5.3 allowlist + mode enforcement → §9 Security Model
- §5.5 Class D destructive-op workflow deferral → §12 Open Questions
- §5 error hierarchy → §11 Testability Notes for Murat

---

## §6. Tool Library Catalog

**Binding constraint:** This section is anchored on Carson's 4.0.1 output (`_bmad-output/implementation-artifacts/praxis/runtime/tool-library-requirements.md`). Tools in this catalog are not invented by me — they are ratified from Carson's P0 (8 tools, launch-binding) and P1 (15 tools, strong candidates) lists with the 8 collision dispositions I acknowledged in the frame verification. Carson's P2 (22 tools, deferred) are referenced in §12 Open Questions, not here.

**Meta-policy inheritance:** The Blue Hat meta-policy in Carson §5 (inclusion criteria, versioning, auth model, intake protocol) is inherited wholesale — I do not re-derive it. The blast-radius Class A–E tiering in Carson §5.6 is the sandbox-tier substrate for §9 Security Model.

### §6.1 P0 — Launch-Binding Tools (8)

Every P0 tool has a full per-tool card. Caller allowlists are the default-deny grants that the Loader assigns at load time (§2.3); deployments may further narrow via config but may not broaden without explicit approval.

#### §6.1.1 Filesystem — `fs-mcp`

| Field | Value |
|---|---|
| **MCP server** | Official Anthropic `mcp-server-filesystem` |
| **Blast class** | C — Tenant data surface |
| **Default mode** | Read-only |
| **Personas that surfaced it** | P1, P2, P3, P4, P5 (unanimous — Carson §4.1 P0-1) |
| **Hat anchors** | White (all 5 personas), Yellow (P1, P5), Black (all 5) |
| **Primary BMAD callers** | Amelia (read + write), Barry (read + write), Paige (read + write), Winston (read), Quinn (read + write), Sophia (read), Caravaggio (read + write), all others (read) |
| **Compliance flags** | R11 ✅ per-deployment path scope, R36 ✅ deployment-local residency, R53 ⚠️ file contents must not leak to central obs (enforced at §10 telemetry allowlist, not at tool boundary) |
| **Sandbox notes** | Workspace-bounded. The MCP server is configured with a tenant-scoped root directory at Runtime init. Reads and writes outside the root are refused at the server layer. Prohibited paths: `.env`, `.ssh/`, `credentials.*`, any path matching `**/secrets/**`. |

**Write allowlist** — at launch, only Amelia, Barry, Paige, Quinn, Caravaggio may write. All other BMAD agents are read-only by default. A deployment operator may grant additional write permissions via `agent_tool_grants` config, audit-logged per R47.

**CostEvent emission:** Low. File I/O itself emits negligible cost events; downstream LLM processing of file contents is the real cost and is attributed via normal agent token tracking.

#### §6.1.2 Tavily — `tavily-mcp`

| Field | Value |
|---|---|
| **MCP server** | Official Tavily `tavily-mcp` |
| **Blast class** | B — Scoped egress (read-only from third-party web APIs) |
| **Default mode** | Read-only (Tavily has no write surface) |
| **Personas that surfaced it** | P1, P2, P3, P5 (Carson §4.1 P0-2) |
| **Hat anchors** | White (P1, P2, P3, P5), Yellow (P1 elevated — "research is the deliverable") |
| **Primary BMAD callers** | Mary (market/competitive research), Victor (disruption signals), John (PM analysis), Dr. Quinn (root cause external research), Sophia (narrative research) |
| **Compliance flags** | R31 ✅ tenant API key, R57 ✅ CostEvent emission MANDATORY (high per-call cost), R53 ⚠️ queries telemetered as hash-only, never raw |
| **Sandbox notes** | External HTTPS egress to `api.tavily.com`. No other domains. |

**Budget enforcement (critical for Tavily):** Tavily is the single most cost-volatile tool in the library — deep-research bursts can cost $0.05–$0.50 per call. Every invocation emits a CostEvent to Pi-Mono before returning. The caller agent's resource budget (§4.3) caps total Tavily spend per spawn; overrun terminates the spawn.

**Write allowlist:** N/A — Tavily has no write surface.

#### §6.1.3 GitHub — `github-mcp`

| Field | Value |
|---|---|
| **MCP server** | Official GitHub `github-mcp-server` |
| **Blast class** | B (read) / C (write) — split by mode |
| **Default mode** | Read-only |
| **Personas that surfaced it** | P1, P2, P3, P4, P5 (unanimous — Carson §4.1 P0-3) |
| **Hat anchors** | White (P2, P3, P4, P5), Yellow (P4 elevated), Black (write surface, secret scanning) |
| **Primary BMAD callers** | Amelia (read + write), Barry (read + write), Quinn (read), Murat (read), Winston (read — reference repos), Bob (read + issue-comment write), Paige (read + docs-repo write) |
| **Compliance flags** | R11 ✅ per-deployment GitHub App, R31 ✅ tenant-scoped credentials, R53 ⚠️ repo file contents must not flow to central obs |
| **Sandbox notes** | External HTTPS egress to `api.github.com` only. GitHub App or PAT credentials loaded from deployment manifest at Runtime init; agents never see the credential. |

**Write allowlist:** Amelia and Barry get PR-create + commit + issue-comment. Bob and Paige get issue-comment only. Amelia and Barry additionally get branch-create; they do NOT get branch-delete, PR-merge, or repo-settings-modify (those are Class D destructive ops, deferred per §9.3).

**Secret scanning defense:** The adapter runs a redaction pass on file-contents results — any detected secrets (via the MCP server's built-in GitHub secret scanning metadata) are stripped before the result reaches the agent's LLM context. If the strip fails, the result is rejected with `ToolResultValidationError`.

#### §6.1.4 Context7 — `context7-mcp`

| Field | Value |
|---|---|
| **MCP server** | Official Upstash `context7-mcp` |
| **Blast class** | A — Inert (read-only, no persistent state, third-party library docs only) |
| **Default mode** | Read-only |
| **Personas that surfaced it** | P1 (tech engagements), P3 (enterprise eng docs), P4 (daily infra library docs) — Carson §4.1 P0-4 |
| **Hat anchors** | White (P1, P3, P4), Yellow (P4 — reduces API hallucination materially) |
| **Primary BMAD callers** | Winston (library docs during architecture drafting), Amelia (API syntax during impl), Quinn (framework docs for test scaffolding), Barry (Quick Flow spec-and-build), Paige (doc standards lookup) |
| **Compliance flags** | R31 ✅ per-tenant API key, R57 ✅ per-query CostEvent, R53 ✅ doc lookups are not tenant data |
| **Sandbox notes** | External HTTPS egress to `context7.com` (or pinned equivalent) only. |

**Budget note:** Low per-call cost. Batch lookups during a drafting session amortize well. No special cap needed.

#### §6.1.5 Playwright — `playwright-mcp`

| Field | Value |
|---|---|
| **MCP server** | Microsoft official `@playwright/mcp` |
| **Blast class** | B (read) / D (write — credential-bearing browser sessions) |
| **Default mode** | Read-only (screenshot, navigate, inspect DOM) |
| **Personas that surfaced it** | P1 (competitor capture), P2 (founder UX analysis), P4 (test authoring for Quinn) — Carson §4.1 P0-5 |
| **Hat anchors** | White (P1, P2, P4), Yellow (P4 — Quinn/Murat need it), Black (egress, credential surface) |
| **Primary BMAD callers** | Quinn (E2E test generation + execution), Sally (UX screenshot + accessibility audit), Mary (competitor page capture), Murat (E2E test architecture, visual regression), Barry (Quick Flow UI verification) |
| **Compliance flags** | R31 ✅ tenant browser creds, R36 ✅ no cross-region egress default, R53 ⚠️ screenshots must not flow to central obs (allowlist at §10) |
| **Sandbox notes** | Headless browser can egress to any domain the test navigates. Deployment operator may configure a domain allowlist (default: none — all navigation permitted; compliance-sensitive deployments should narrow). Credentials stored in tenant-scoped secret vault, injected at session start. |

**Class D distinction:** In read-only mode (screenshots, DOM inspection, non-authenticated navigation), Playwright is Class B. In write mode (form submission with stored credentials, authenticated actions), it becomes Class D because the agent can effect real-world state changes on external services. Write mode is P2-capped per §9.3 until the destructive-op approval workflow ships.

**Launch write allowlist:** None. Playwright is read-only at launch.

#### §6.1.6 PostgreSQL — `postgres-mcp`

| Field | Value |
|---|---|
| **MCP server** | Crystal DBA `postgres-mcp` (read-focused) + explicit query-builder wrapper for writes |
| **Blast class** | C — Tenant data surface |
| **Default mode** | Read-only |
| **Personas that surfaced it** | P2 (product analytics DB), P3 (enterprise data warehouse), P4 (database ops) — Carson §4.1 P0-6 |
| **Hat anchors** | White (P2, P3, P4), Yellow (P4, P3), Black (PII, write blast radius) |
| **Primary BMAD callers** | Amelia (schema queries, migration review), Quinn (test data setup), Mary (product analytics), Barry (rapid impl), Murat (query perf) |
| **Compliance flags** | R8 facade-discipline echo (typed query methods, no raw query builder exposed to agents), R11 ✅, R31 ✅, R53 ⚠️ query result content must not flow to central obs |
| **Sandbox notes** | Connection string scoped to deployment-local Postgres per Runtime config. Query execution via parameterized statements only — the tool interface accepts structured query objects, not raw SQL strings. SQL injection via agent-composed queries is structurally impossible because the agent does not have a raw-SQL surface. |

**Write allowlist:** Amelia and Barry get write access to non-system tables only. Write operations must go through the typed query-builder wrapper, which rejects DDL (`CREATE`, `ALTER`, `DROP`) and privilege-modifying statements (`GRANT`, `REVOKE`). Full DDL requires break-glass tooling and is Class D / P2-capped.

#### §6.1.7 Python Sandbox + Subprocess (split per Carson §6.8 collision)

**Two distinct tools, not one.** Carson's collision report correctly identified that bundling these into a single conceptual tool obscures blast-radius asymmetry. I ratify the split with strong agreement.

##### §6.1.7a Python Sandbox — `python-sandbox-mcp`

| Field | Value |
|---|---|
| **MCP server** | Containerized Python execution (e.g., E2B, Daytona, or equivalent MCP wrapper) |
| **Blast class** | C — Tenant data surface |
| **Default mode** | Read-only execution (no-network default; writes scoped to sandbox-local filesystem) |
| **Primary BMAD callers (broad allowlist)** | Amelia, Barry, Quinn, Murat, Mary (data munging), Paige (doc generation), Dr. Quinn (analysis scripts), Victor (quick numerical models) |
| **Compliance flags** | R11 ✅ no cross-tenant filesystem path, R31 ✅ no secret access, R57 ✅ CostEvent per execution |
| **Sandbox notes** | Containerized Python runtime. No host filesystem access. No network by default (opt-in per call, deployment-operator-grantable). CPU-time, memory, wall-time bounded by caller's ResourceBudget (§4.3). On timeout or resource exhaustion, container is SIGKILL'd and a CostEvent emitted. |

**Why Class C not Class D:** The sandbox is containerized. Escape requires a container-escape exploit, which is a known hard problem. Under realistic threat modeling, Python sandbox is tenant-data-surface (the agent can read and compute on workspace files) but not escalation-capable (the agent cannot touch the host or other tenants). Class C is the correct tier.

##### §6.1.7b Subprocess — `subprocess-mcp`

| Field | Value |
|---|---|
| **MCP server** | Bounded binary execution wrapper (per-binary allowlist; no generic shell) |
| **Blast class** | D — Destructive / escalation-capable |
| **Default mode** | Allowlist-gated (no default access) |
| **Primary BMAD callers (narrow allowlist — 3 agents)** | Amelia, Barry, Quinn — and ONLY these three |
| **Compliance flags** | R11 ✅ tenant-scoped workspace, R31 ✅ no secret access, R57 ✅ per-execution CostEvent |
| **Sandbox notes** | Per-binary allowlist. Permitted binaries at launch: `pytest`, `ruff`, `mypy`, `python`, `pip`, `npm test`, `node`. Nothing else. `curl`, `ssh`, `nc`, `sh`, `bash`, `/bin/sh` are explicitly blocked. Network isolation inherited from workspace sandbox. CPU/memory/wall-time caps from ResourceBudget. |

**Why Class D:** Even with a narrow binary allowlist, subprocess can run arbitrary Python via `python -c "..."` which bypasses the Python sandbox's containerization. This is a known tension: the binary allowlist gains us narrowness at the cost of opening a Python-is-Turing-complete attack surface. The mitigation is that `python` subprocess execution runs in the workspace-bounded filesystem with no network and CPU/memory caps — narrower than an unrestricted host Python but broader than the containerized Python sandbox. Rating Class D reflects the escalation risk honestly rather than optimistically.

**Why not Class E (unbounded):** Carson's §5.6 Class E is "sandbox-escape capable if mis-configured → not admitted." Subprocess with the launch allowlist is NOT Class E because (a) the binary list is finite and audited, (b) workspace bounds are enforced by the filesystem sandbox, (c) CPU/memory caps are ResourceBudget-enforced. Mis-configuration is possible but requires explicit deployment-operator action to broaden the binary list, which is audit-logged.

#### §6.1.8 OpenTelemetry Exporter — `otel-exporter-mcp`

| Field | Value |
|---|---|
| **MCP server** | OTel exporter pattern wrapped as MCP tool |
| **Blast class** | A — Inert (emits telemetry, does not read any data back) |
| **Default mode** | Write-only (emit) |
| **Personas that surfaced it** | P4 (operational backbone), P5 (audit trail emission) — Carson §4.1 P0-8 |
| **Hat anchors** | White (P4), Yellow (P5 — compliance depends on trace emission), Black (R53 exposure point) |
| **Primary BMAD callers** | ALL 16 agents via framework integration (not direct invocation); Murat for observability test strategy |
| **Compliance flags** | R51 ✅ schema allowlist mirrored, R53 ✅ **hard gate — this tool IS the R53 enforcement point**, R54 ✅ tenant-local sink support |
| **Sandbox notes** | THIS TOOL IS WHERE R53 ENFORCEMENT LIVES. Configuration MUST use a strict field allowlist at emit time, mirroring Memory Req #51's TelemetryEvent schema discipline. No raw query content, no retrieval results, no embeddings, no tenant-data field values. Only numeric/aggregate metrics + allowlisted structured fields. Backend configurable per deployment: default is tenant-local sink; central observability is opt-in after allowlist verification. |

**Why this tool is special:** Every other tool's R53 compliance is enforced *at the telemetry boundary using this tool*. If this tool is mis-configured, every other tool's compliance is compromised. §9 Security Model re-states this as a structural invariant.

**CostEvent emission:** This tool EMITS CostEvents for other tools and agents; it does not consume CostEvents itself. The self-cost is the collector infrastructure, not per-call.

### §6.2 P1 — Strong Candidates (15 tools, summary cards)

These tools land at P1 per Carson's catalog with the collision-report additions (Jira, Confluence, Kubernetes, Datadog/Grafana/Prometheus) included. Each card is a summary; full cards are produced at Stage 4.3 Amelia implementation time or at Stage 5+ if promotion to P0 is considered.

| # | Tool | MCP server | Blast class | Default mode | Personas | Top risk | Primary BMAD callers |
|---|---|---|---|---|---|---|---|
| P1-1 | Jira MCP | `jira-mcp` | B | Read-only | P3, P5 | SSO/SAML required for enterprise | Bob, Murat, Paige |
| P1-2 | Confluence MCP | `confluence-mcp` | B | Read-only | P3, P5 | R53 at tool boundary (large content) | Paige, Mary, Dr. Quinn |
| P1-3 | Slack MCP (read + write, NOT webhook-only) | `slack-mcp` | B | Read-only | P2, P3 | Per-channel allowlist critical | Bob, Mary, John |
| P1-4 | Kubernetes MCP | `k8s-mcp` | C (read) / D (write) | Read-only | P4 | Destructive ops → P2-capped per §9.3 | Amelia, Murat, Winston |
| P1-5 | Datadog / Grafana / Prometheus MCP (observability read-path) | `observability-mcp` | B | Read-only | P4, P5 | Dashboards may contain PII → R53 | Murat, Dr. Quinn |
| P1-6 | Docker MCP | `docker-mcp` | C | Read-only | P4 | Image pull from untrusted registries | Amelia, Quinn, Barry |
| P1-7 | Stripe MCP | `stripe-mcp` | B | Read-only | P2 | PCI-adjacent, customer PII | Mary, Victor |
| P1-8 | Notion MCP | `notion-mcp` | B | Read-only | P2 | Broad workspace access | Paige, Mary, Sally |
| P1-9 | GitLab MCP | `gitlab-mcp` | B (read) / C (write) | Read-only | P4 | (alternative to GitHub) | Amelia, Barry, Quinn |
| P1-10 | PagerDuty MCP | `pagerduty-mcp` | B | Read-only | P4 | Incident data sensitivity | Murat, Dr. Quinn |
| P1-11 | Security Scanner MCP (Semgrep / Trivy / Snyk) | `security-scanner-mcp` | C | Read-only | P4, P5 | False positive noise | Murat, Amelia |
| P1-12 | Vault MCP (read-only) | `vault-mcp` | C | Read-only | P4 | Mis-config = total compromise | Amelia, Barry (2 agents only) |
| P1-13 | SEC EDGAR MCP | `sec-edgar-mcp` | A | Read-only | P1 | None significant (public data) | Mary, Victor |
| P1-14 | Google Workspace MCP | `google-workspace-mcp` | B | Read-only | P2 | OAuth scope sprawl | Mary, John, Paige |
| P1-15 | OTel Collector MCP (write-side) | `otel-collector-mcp` | A | Write-only | P4 | Same R53 discipline as P0-8 | Murat (infra instrumentation) |

**Operational readiness:** P1 tools land at Stage 4.3 Amelia implementation time if capacity permits; any P1 tool not shipped at Stage 4.6 pre-sales checkpoint carries over to Stage 5 as a named deliverable with the Stage 4 rationale preserved.

**Promotion path:** P1 → P0 requires Carson's §5.4 intake protocol gate: two release cycles of operational maturity + ≥3 personas demanding it + zero security incidents. No P1 tool is promoted to P0 at Stage 4 without re-running the §5.4 gates.

### §6.3 P2 — Deferred (22 tools, reference only)

Per Carson's §3 P2 list: Salesforce, Microsoft 365 / Graph, SAP / Oracle ERP, Workday, Okta / Azure AD, ServiceNow, Tableau / PowerBI, HubSpot, QuickBooks, Shopify, Terraform, AWS / GCP / Azure CLI, Ansible, SIEM (Splunk / Sumo), Vanta / Drata / Secureframe, DLP Scanner, arXiv / Google Scholar, News RSS, dbt / LookML, LocalStack, OpenSCAP / CIS Benchmark, Discord Webhook.

**Placement:** Referenced in §12 Open Questions with their per-persona rationale inherited from Carson's §3. No drafting is required in this section; Stage 5+ reassess ceremonies promote individual P2 tools into P1 via the §5.4 intake protocol.

### §6.4 Intake Protocol for Post-Launch Additions

Inherited wholesale from Carson §5.4. Summary (not re-derived):

1. Request trigger → seven-gate inclusion check (§5.1) → Black Hat re-pass → persona + hat anchor → P2 incubation (one release cycle minimum) → P1 promotion criteria → P0 promotion criteria.
2. New tools enter the Praxis release process via `tools-lock.toml` version pin + regression test against affected-persona workflows.
3. No tool enters the library without the persona/hat anchor and Black Hat Memory-req compliance trace.

The Runtime's Tool Registry (§5.2) is updated via Praxis release cuts, not at runtime. Hot-adding tools post-deploy is not supported.

### §6.5 Blast-Radius Class Usage Across P0/P1

Per Carson §5.6, tools are tiered by blast radius. The distribution across P0 + P1:

| Class | Tools | Sandbox policy |
|---|---|---|
| **A — Inert** | Context7, SEC EDGAR, OTel exporter, OTel collector | Broadly allowlisted; minimal per-agent gating |
| **B — Scoped egress** | Tavily, GitHub (read), Jira, Confluence, Slack, Datadog/Grafana, Stripe, Notion, GitLab (read), PagerDuty, Google Workspace, Playwright (read) | Per-agent allowlist; rate-limited |
| **C — Tenant data surface** | Filesystem, PostgreSQL, Python Sandbox, Docker, Kubernetes (read), Security Scanner, Vault (read), GitHub (write), GitLab (write) | Per-agent allowlist + read/write separation mandatory |
| **D — Destructive / escalation-capable** | Subprocess, Kubernetes (write), Playwright (write), Terraform (P2), AWS CLI (P2), Vault (write, P2) | Per-agent allowlist + per-operation approval (human-in-loop workflow deferred; §9.3 Class D P2-cap) |
| **E — Unbounded** | NONE ADMITTED | Auto-P2 at best — Carson §5.6 hard stop |

§9 Security Model consolidates this into explicit per-class sandbox policy.

---

## §7. Inter-Agent Communication Bus

The Communication Bus is how agents coordinate in team mode (§4.1.2). Subagent mode does not use the bus — subagents return via awaited coroutine to their parent. Team mode uses the bus for direct messaging, broadcast, and structured coordination.

### §7.1 Architectural Anchor — Beads + Seance

Per §1.3 Gas Town pattern extraction, the bus is an **append-only event log** backed by Beads (the content-addressed event store from Stage 3). This satisfies three properties simultaneously:

1. **Append-only** — no event is ever modified or deleted; coordination history is immutable and auditable
2. **Content-addressed** — events are identified by hash; duplicate emissions are idempotent
3. **Tenant-scoped** — Beads is tenant-scoped per Memory §3 architecture; cross-tenant bus communication is structurally impossible (R11)

Seance-style session discovery is NOT adopted literally (Gas Town uses `.events.jsonl` files; Praxis uses Beads-backed event storage). The *shape* of event-log session discovery is adopted: agents can query the bus for events since a timestamp, filtered by team-id and event-type, to reconstruct session context.

### §7.2 Message Format

```python
from typing import Literal
from uuid import UUID


class BusEventType(StrEnum):
    AGENT_SPAWNED = "agent_spawned"           # Spawner → all
    AGENT_READY = "agent_ready"               # agent → parent (ready to receive work)
    AGENT_MESSAGE = "agent_message"           # agent → agent (direct)
    AGENT_BROADCAST = "agent_broadcast"       # agent → team (broadcast)
    AGENT_RESULT = "agent_result"             # agent → parent (final output)
    AGENT_FAILED = "agent_failed"             # agent → parent (terminal failure)
    AGENT_TERMINATED = "agent_terminated"     # Spawner → all (lifecycle)
    TEAM_BARRIER = "team_barrier"             # coordinator → team (synchronization point)
    TEAM_BARRIER_REACHED = "team_barrier_reached"  # agent → coordinator (I hit the barrier)


class BusEvent(BaseModel):
    """An append-only event on the Communication Bus.

    Stored in Beads with content-hash identity. Never modified, never deleted.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: UUID                  # Also the Beads content-hash key
    event_type: BusEventType
    tenant_hash: str                # R6 mandatory
    team_id: UUID | None            # None for subagent-mode events (rare; mostly team-mode)
    spawn_id: UUID                  # Originating spawn
    sender_agent: str               # Agent name (BMAD-stable)
    sender_role: AgentRole          # PRODUCER or REVIEWER — asymmetry discipline applies to bus reads
    recipient_agent: str | None     # None for broadcasts
    payload_json: dict[str, Any]    # Typed per event_type at Runtime layer
    emitted_at: datetime
    parent_event_id: UUID | None    # For reply chains and barrier acknowledgments
```

**`sender_role` is critical:** Bus events carry the sender's role tag. The bus's read API filters events by recipient role — reviewer agents subscribing to the bus see only events from other reviewers and from the coordinator, never events authored by producer agents. This reinforces §4.1's type-level asymmetry at the coordination layer. See §7.5 below.

### §7.3 Bus Write API

```python
class CommunicationBus:
    """The inter-agent communication substrate.

    Thread-safe. Backed by Beads (tenant-scoped content-addressed store).
    Wired into the Spawner so that spawn lifecycle events are auto-emitted.
    """

    def __init__(
        self,
        beads_store: "BeadsStore",  # via Memory facade; the bus does NOT hold a direct Memory handle
        manifest: DeploymentManifest,
    ) -> None:
        self._beads = beads_store
        self._manifest = manifest

    async def emit(self, event: BusEvent) -> None:
        """Append an event to the bus. Idempotent per event_id.

        Preconditions:
        - event.tenant_hash == manifest.tenant_hash (hard-fail on mismatch, R4 drift)
        - event.sender_agent is a known agent name
        - For non-broadcast events, recipient_agent is set and is also a known name
        """
        ...
```

**Idempotency:** `emit()` is idempotent on `event_id`. Re-emitting the same event is a no-op. This is how the bus survives transient failures without double-delivery.

**No deletion:** There is no `delete_event()` method. The bus is append-only. Corrections are emitted as new events that reference the original via `parent_event_id`.

### §7.4 Bus Read API

```python
@dataclass(frozen=True)
class BusQuery:
    """A filter over the event log."""
    team_id: UUID | None = None
    since: datetime | None = None
    event_types: tuple[BusEventType, ...] = ()
    sender_agents: tuple[str, ...] = ()
    recipient_agent: str | None = None
    limit: int = 100


class CommunicationBus:
    # ... (continued from §7.3)

    async def read(
        self,
        caller_agent: AgentRuntimeConfig,
        caller_role: AgentRole,
        query: BusQuery,
    ) -> tuple[BusEvent, ...]:
        """Read bus events matching the query.

        Role-based filter (THE asymmetry enforcement at the bus layer):
        - If caller_role == PRODUCER: sees all events addressed to it + all team broadcasts
        - If caller_role == REVIEWER: sees events addressed to it + team broadcasts
          WHERE the sender_role is NOT PRODUCER. Reviewer never sees producer-authored events.

        This mirrors §4.1's type-level asymmetry at the coordination layer.
        Bus-side filter is defense-in-depth; the primary enforcement remains
        the §4.1.4 memory proxy class structure.
        """
        events = await self._read_unfiltered(query)
        return tuple(e for e in events if self._visible_to(e, caller_agent.agent.name, caller_role))

    def _visible_to(self, event: BusEvent, caller_name: str, caller_role: AgentRole) -> bool:
        if event.tenant_hash != self._manifest.tenant_hash:
            return False  # R11 structural impossibility, but defense-in-depth anyway
        # Direct messages: only visible to the recipient
        if event.recipient_agent is not None and event.recipient_agent != caller_name:
            return False
        # Reviewer asymmetry: reviewers never see producer-authored events
        if caller_role is AgentRole.REVIEWER and event.sender_role is AgentRole.PRODUCER:
            return False
        return True
```

### §7.5 Information Asymmetry at the Bus Layer

**Redundancy with §4.1 is intentional.** §4.1 enforces asymmetry at the *memory* layer (ReviewerMemoryProxy has no retrieve_* methods). §7 enforces asymmetry at the *coordination* layer (ReviewerMemoryProxy owner cannot read producer-authored bus events). A reviewer agent that somehow obtained a reference to another agent's ProducerMemoryProxy (impossible by §4.1.5 construction, but let's pretend) would STILL be blocked from seeing producer work via the bus because the bus-read API filters by sender_role.

**This is defense-in-depth, not duplication.** §9 Security Model consolidates the claim: asymmetry enforcement has two independent structural layers. Breaching both requires either (a) direct Memory facade access bypassing the proxy (impossible — proxies are constructed by the Spawner and never handed out), or (b) a bug in `_visible_to` (auditable — single function, single grep target).

### §7.6 Team Barriers

Coordination pattern: a team coordinator emits `TEAM_BARRIER`; each team member must emit `TEAM_BARRIER_REACHED` in reply before the coordinator proceeds. Useful for wave execution where phase N+1 cannot begin until all team members complete phase N.

```python
async def await_team_barrier(
    self,
    coordinator: AgentRuntimeConfig,
    team_id: UUID,
    expected_responders: set[str],
    timeout_seconds: float = 60.0,
) -> bool:
    """Emit a TEAM_BARRIER and wait for TEAM_BARRIER_REACHED from all expected responders.

    Returns True on all-respond, False on timeout.
    """
    ...
```

**Timeout policy:** Barriers have a configurable timeout. On timeout, the coordinator receives a `BarrierTimeoutError` listing the unresponded members. The coordinator decides whether to retry, proceed without them, or escalate.

### §7.7 Bus Capacity and Retention

**Beads-backed retention:** Bus events inherit Memory's retention semantics. Per-team event history is retained indefinitely within tenant scope (Memory Req #15 — Beads versions retained indefinitely), bounded only by the tenant's NFR-Q2 entry ceiling (soft 100K / hard 250K).

**High-volume teams:** A runaway agent emitting thousands of bus events can hit the soft ceiling and trigger telemetry warnings, then the hard ceiling and MemoryQuotaExceeded. The Spawner's §4.3 ResourceBudget `max_memory_writes` limit is the first line of defense — an agent that emits too many bus events triggers budget exhaustion before hitting Memory's hard ceiling.

### §7.8 Forward Reference — §9 Security Model

§7's information asymmetry contribution is consolidated into §9's structural claim. See §9.1 for the unified statement.

---

## §8. Integration Contracts

This section specifies every cross-stage integration seam: Runtime ↔ Pi-Mono (F-1 outbox adapter), Runtime ↔ Memory (agent outcomes), Runtime ↔ Compression (agent conversations), Runtime ↔ MAC (Stage 5 handoff). §8.1 is the F-1 absorption and is elaborated in full with the Path A / Path B split Andrey corrected in frame verification.

### §8.1 Memory Audit Stream → Pi-Mono Outbox Adapter (F-1 Absorption)

**Forward-reference resolved:** This is the full elaboration of the F-1 absorption plan committed in my frame report and the composition paragraph stated in §4.2.1. This subsection is the highest-stakes structural contract in Stage 4.

#### §8.1.1 The Problem, Restated

Memory's architecture §3.5 and §9.3 promise that:
- Every retention-action (crypto-shred, delete cascade, quarantine-to-delete) emits a `CostEvent(type='retention_action')` in the same database transaction as the Memory operation, preserving Stage 1's durability guarantee exactly
- Every Mem0 fact extraction emits a `CostEvent(type='record_created', component='memory.mem0.*')`
- Every retrieval cache hit emits a `CostEvent(type='retrieval_cache_hit')` per Req #57

Memory's code currently has ZERO imports of `praxis.kernel.cost`. The `Memory.audit_buffer` property on `facade.py:142` is the integration seam. Stage 4 must build the adapter.

#### §8.1.2 Two Paths, Not One

Per Andrey's binding correction in frame verification, F-1 is split into TWO distinct emission paths with different durability guarantees:

**Path A — Reaper-Direct (same-transaction)** for `memory.retention_action`
**Path B — Tick-Drain (at-least-once with tick-window gap)** for `memory.record_created` and `memory.retrieval_cache_hit`

#### §8.1.3 Side-by-Side Path Comparison

| Property | **Path A — Reaper-Direct** | **Path B — Tick-Drain** |
|---|---|---|
| **Triggered by** | Reaper worker completing a `retention_shred`, `retention_cascade`, `quarantine_promote`, or `backup_rewrite` job | Orchestrator tick loop draining `Memory.audit_buffer` every `tick_interval_ms` (default 500ms) |
| **Transaction boundary** | **Same Postgres transaction** that updates `jobs_queue.state='completed'` ALSO inserts the CostEvent row into `events_outbox`. Atomic. Zero gap. | One Postgres transaction per tick-batch: insert N CostEvent rows into `events_outbox`, commit, then clear the drained entries from `Memory.audit_buffer` on commit success |
| **Durability guarantee** | **Mathematically sound by construction.** Preserves Memory §3.5 "same database transaction" invariant literally. Cannot lose events because the commit that marks the job complete IS the commit that writes the CostEvent. | At-least-once with idempotency keys in `events_outbox.dedup_key`. The commit happens-before the buffer clear, so a crash between commit and clear replays events (deduped by the sink). **Window-of-loss:** a crash BETWEEN `_audit_append()` and the next tick loses in-memory events that never reached the transaction. Bounded by `tick_interval_ms` (default ≤500ms). |
| **CostEvent categories flowing through** | `memory.retention_action` (retention_shred, retention_cascade, quarantine_promote, backup_rewrite, crypto-shred completion) | `memory.record_created` (Mem0 fact extraction, component tag `memory.mem0.*`); `memory.retrieval_cache_hit` (negative-cost savings, Req #57) |
| **NFR anchor** | **NFR-C-A1** (7-day crypto-shred audit SLA); **NFR-Q6** (5-min crash RTO) — both structurally guaranteed by the shared-DB transaction + the §4.2.4 orphan reclaim | **None hard.** Billing reconciliation; telemetry savings attribution. Neither feeds a compliance SLA. |
| **Failure mode (on Postgres error)** | Job remains `state='in_progress'` → retries via `jobs_queue.retry_state` → escalates to `poisoned` + P1 alert on retry exhaustion (§4.2.5) | Batch rolls back; buffer state unchanged; next tick retries. Per-event retry state in `outbox_drain_retries` table. On retry exhaustion, event moves to `quarantined` state with P3 alert. |
| **Window-of-loss** | **ZERO** | **≤ `tick_interval_ms` on process crash** (default 500ms). Bounded, documented, operationally tolerable for the affected categories. |
| **Retry state location** | `jobs_queue.retry_state` JSONB column | `outbox_drain_retries` table |
| **Worker** | `JobsWorker._jobs_worker_loop` (§4.2.4) | `JobsWorker._tick_drain_loop` (§4.2.4) |
| **Where events_outbox rows originate** | Reaper's completion transaction | Tick-drain batch transaction |
| **Emission volume (expected)** | Low — retention actions are rare (deletion workflows) | High — every Mem0 write and every retrieval are candidates |
| **Idempotency key** | Deterministic from (job_id, sub-step) | Deterministic from `AuditEvent.id` |

**Diagram:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DEPLOYMENT POSTGRES                              │
│                                                                         │
│    ┌─────────────────┐            ┌──────────────────┐                 │
│    │   jobs_queue    │            │  events_outbox   │                 │
│    │  (§4.2.2)       │            │  (Pi-Mono Stage1)│                 │
│    └────────┬────────┘            └──────▲─────▲─────┘                 │
│             │                            │     │                       │
│             │ Path A:                    │     │                       │
│             │ SAME TRANSACTION           │     │                       │
│             │ (reaper commits            │     │                       │
│             │  job + CostEvent           │     │                       │
│             │  atomically)               │     │                       │
│             ▼                            │     │                       │
│    ┌────────────────────────────┐        │     │                       │
│    │ JobsWorker                 │        │     │                       │
│    │ _jobs_worker_loop()        │────────┘     │                       │
│    │                            │ Path A       │                       │
│    │ _tick_drain_loop()         │──────────────┘                       │
│    └────────▲───────────────────┘ Path B (batched insert, dedup_key)   │
│             │                                                           │
│             │ in-memory drain (500ms tick)                              │
└─────────────┼───────────────────────────────────────────────────────────┘
              │
              │
    ┌─────────▼──────────────┐
    │ Memory.audit_buffer    │  (in-memory, cleared on Path B commit success)
    │ (AuditEvent objects)   │
    └────────────────────────┘
```

#### §8.1.4 Path A — Reaper-Direct, Elaborated

```python
async def _complete_retention_job(
    self,
    job: JobRecord,
    outcome: RetentionOutcome,
) -> None:
    """Mark a retention job completed and emit its CostEvent in the same transaction.

    This is the Path A emission path. Memory architecture §3.5's 'same database
    transaction' invariant is preserved literally — the commit that writes
    jobs_queue.state='completed' IS the commit that writes the CostEvent row
    into events_outbox. There is no window between job completion and cost
    attribution.
    """
    async with self._jobs_store.transaction() as tx:
        # Update the job row
        await tx.execute(
            """
            UPDATE jobs_queue
            SET state='completed',
                completed_at=NOW(),
                last_error=NULL
            WHERE id=$1 AND claim_token=$2
            """,
            job.id, job.claim_token,
        )

        # Insert the CostEvent into events_outbox IN THE SAME TRANSACTION
        cost_event = self._build_retention_cost_event(job, outcome)
        await tx.execute(
            """
            INSERT INTO events_outbox
                (event_id, event_type, tenant_hash, payload_json, dedup_key, emitted_at)
            VALUES ($1, $2, $3, $4, $5, NOW())
            ON CONFLICT (dedup_key) DO NOTHING
            """,
            cost_event.event_id,
            cost_event.event_type,
            cost_event.tenant_hash,
            cost_event.payload_json,
            f"retention:{job.id}",  # deterministic dedup key
        )

        # Commit is implicit on context exit — BOTH writes land atomically or neither does
```

**Properties:**

1. **Atomicity.** Postgres commits both writes or neither. No partial state is ever observable. No orchestration coordination is required.
2. **Idempotency on retry.** If the transaction fails and the job is retried, the `ON CONFLICT (dedup_key) DO NOTHING` clause prevents duplicate CostEvent insertion. The dedup key `retention:{job.id}` is deterministic per job, so retries are safe.
3. **Fail-hard on tenant drift.** The transaction reads `tenant_hash` from the job row, which was validated against the manifest at job creation time. If somehow the job row's `tenant_hash` does not match the Orchestrator's manifest at completion time (R4 drift scenario), the cost event generation step hard-fails and the Runtime terminates. This is defense-in-depth on top of R4's 60s manifest verification.
4. **NFR-C-A1 structural guarantee.** The 7-day crypto-shred audit SLA is now a property of the schema, not a property of orchestration. As long as the jobs_queue state machine progresses (§4.2.5), the CostEvent is emitted. The only way to breach the SLA is for the job to never complete — which is detectable via `retry_count >= max_retries → poisoned → P1 alert`.

#### §8.1.5 Path B — Tick-Drain, Elaborated

> **Footnote on method names:** The code below uses placeholder method names on a `DrainAdapter` abstraction — `snapshot_undrained()` and `mark_drained(count)`. These are NOT methods on Stage 3's shipped `AuditBuffer` class (which exposes only `append`, `events`, `clear`, `__len__`). The DrainAdapter is a Runtime-layer wrapper Amelia builds at Stage 4.3 to provide the drain coordination semantics this path requires. The exact coordination mechanism (position-based shim vs. surgical AuditBuffer extension vs. sidecar queue) is an implementation decision specified in §12 OQ-N with a defaulted choice and an escalation trigger. The architecture shape of Path B is unchanged regardless of which coordination mechanism ships.

```python
async def _tick_drain_loop(self) -> None:
    """Drain Memory.audit_buffer into events_outbox once per tick.

    Runs as an asyncio task inside the JobsWorker. Tick interval is
    deployment-tunable (default 500ms).

    Durability: at-least-once with idempotency keys. Window-of-loss is
    bounded by the tick interval — if the process crashes between
    _audit_append() and the next tick, those events are lost. This is
    acceptable for memory.record_created and memory.retrieval_cache_hit
    because neither feeds NFR-C-A1 or any hard SLA (billing reconciliation
    and observability savings attribution only).

    Critically: this loop does NOT drain memory.retention_action events.
    Those are handled by Path A (reaper-direct) and must not appear in
    the audit_buffer. The Memory layer's _audit_append implementation
    is responsible for the correct categorization; the adapter trusts
    that categorization and only processes the Path B event types here.
    """
    while not self._shutdown.is_set():
        await asyncio.sleep(self._tick_interval_seconds)
        try:
            await self._drain_once()
        except Exception as exc:
            logger.exception("tick drain failed: %s", exc)
            # Loop continues; next tick retries the whole batch

async def _drain_once(self) -> None:
    # Step 1: snapshot undrained events via the DrainAdapter abstraction.
    # The concrete coordination mechanism (position-based shim, surgical
    # AuditBuffer extension, or sidecar queue) is specified in §12 OQ-N
    # with Path (i) position-based shim as the architecture-committed default.
    events = self._drain_adapter.snapshot_undrained()

    path_b_events = [
        e for e in events
        if e.event_type in {AuditEventType.RECORD_CREATED, AuditEventType.RETRIEVAL_CACHE_HIT}
    ]
    if not path_b_events:
        return

    async with self._jobs_store.transaction() as tx:
        for event in path_b_events:
            # Cross-check tenant identity (R4 defense-in-depth)
            if event.tenant_hash != self._manifest.tenant_hash:
                raise TenantDriftError(
                    f"audit buffer event tenant_hash {event.tenant_hash!r} "
                    f"does not match manifest {self._manifest.tenant_hash!r}"
                )

            cost_event = self._translate_audit_to_cost(event)

            # Idempotent insert with dedup key = AuditEvent.id
            await tx.execute(
                """
                INSERT INTO events_outbox
                    (event_id, event_type, tenant_hash, payload_json, dedup_key, emitted_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (dedup_key) DO NOTHING
                """,
                cost_event.event_id,
                cost_event.event_type,
                cost_event.tenant_hash,
                cost_event.payload_json,
                str(event.id),  # AuditEvent.id IS the dedup key
            )

    # Commit succeeded — advance the drain high-water mark via the adapter.
    # With the §12 OQ-N Path (i) default, this is a position counter increment;
    # with Path (ii), this would be an atomic drain on the AuditBuffer itself.
    # Either way, the semantic contract at this line is: "these N events are
    # now durably in events_outbox and should not be re-emitted on the next tick."
    self._drain_adapter.mark_drained(len(path_b_events))

    # If the commit failed, mark_drained is NEVER called; next tick replays
    # the same events, deduped by events_outbox.dedup_key
```

**Properties:**

1. **At-least-once delivery.** The commit happens before the buffer clear. On crash between commit and clear, the next tick replays the events, deduped by `events_outbox.dedup_key` on `AuditEvent.id`. No double-counting.
2. **Bounded window-of-loss.** A process crash BETWEEN `_audit_append()` and the next tick loses the in-memory events that never made it into the transaction. The window is bounded by `tick_interval_ms` — default 500ms, deployment-tunable. For non-compliance categories (record_created, retrieval_cache_hit), this is operationally tolerable.
3. **Per-event retry state.** On transient backend failures, individual events can be tracked via `outbox_drain_retries` (§4.2.3) rather than rolling back the entire tick. Implementation detail — the strawman above uses batch rollback for simplicity; Amelia may optimize at Stage 4.3.
4. **No retention_action leakage.** The drain loop explicitly filters by event type. If a `retention_action` somehow appears in `audit_buffer` (shouldn't, because Memory's _audit_append emits retention_actions through a different code path — the reaper's direct path), the filter drops it and logs a warning. This is defense-in-depth; the expected invariant is that retention_action never enters the tick-drain pipeline.

#### §8.1.6 Documented Window-of-Loss (Test Spec for Murat)

**Murat §11 test requirement:** Add the following test specs:

```
Test spec M8.1.B.1 — Path B at-least-once under crash
  Given: Memory._audit_append has been called N times with record_created events
  And:   The tick-drain transaction has committed for M of those events (M < N)
  And:   The Orchestrator process crashes BEFORE the buffer clear completes
  When:  The Orchestrator restarts and the tick-drain loop runs again
  Then:  All N events are delivered to events_outbox (deduped by AuditEvent.id)
  And:   No event is counted twice (verified by query over events_outbox)

Test spec M8.1.B.2 — Path B window-of-loss on crash before tick
  Given: Memory._audit_append has been called N times
  And:   The tick-drain loop has NOT yet run
  And:   The Orchestrator process crashes
  When:  The Orchestrator restarts
  Then:  Those N events are LOST (documented acceptable behavior for
          record_created and retrieval_cache_hit)
  And:   The test verifies this loss is ≤ tick_interval_ms worth of events

Test spec M8.1.A.1 — Path A same-transaction guarantee
  Given: A retention job is claimed by the reaper
  And:   The reaper is simulated to crash mid-completion
  When:  The transaction either commits or rolls back
  Then:  jobs_queue.state and events_outbox row are consistent
         (either both updated or neither)

Test spec M8.1.A.2 — Path A NFR-C-A1 structural guarantee
  Given: A retention_shred job completes
  When:  The test queries events_outbox for the corresponding CostEvent
  Then:  The CostEvent exists and was written in the same transaction as the
         jobs_queue update (verified by a single-query join on transaction ID)
```

#### §8.1.7 Forward Reference — §9 Security Model

§8.1's F-1 absorption is consolidated into §9's defense-in-depth tenant validation section. Specifically: the tenant cross-check in both Path A and Path B paths is one of three layers of R4 manifest drift detection that §9 specifies.

### §8.2 Runtime → Pi-Mono Agent and Tool Cost Events

Beyond the Memory-originated events covered in §8.1, the Runtime itself emits CostEvents for its own operations:

| Category | Event type | Emitter | Trigger |
|---|---|---|---|
| Agent lifecycle | `runtime.agent_spawn` | AgentSpawner | `spawn_subagent` / `spawn_team` called |
| Agent lifecycle | `runtime.agent_terminate` | AgentSpawner | context-manager exit (success or failure) |
| Tool invocation | `runtime.tool_call.class_a` | MCPToolAdapter | Class A tool invoked |
| Tool invocation | `runtime.tool_call.class_b` | MCPToolAdapter | Class B tool invoked |
| Tool invocation | `runtime.tool_call.class_c` | MCPToolAdapter | Class C tool invoked |
| Tool invocation | `runtime.tool_call.class_d` | MCPToolAdapter | Class D tool invoked (rare, P2-capped) |
| Budget | `runtime.budget_exceeded` | AgentSpawner | ResourceBudget exhausted |
| Registry | `runtime.registry_llm_rerank` | AgentRegistry | LLM tie-break invoked in §3.3 |

**Emission path:** Runtime-originated CostEvents are written directly to `events_outbox` via Pi-Mono's `CostTracker.track_cost(...)` API. No tick-drain required because the Runtime has a synchronous path to Pi-Mono (unlike Memory, which was architected as a self-contained package).

**Namespace discipline:** Every Runtime category is prefixed with `runtime.`; every Memory-originated category (via §8.1) is prefixed with `memory.`. Pi-Mono's aggregation queries use namespace-prefix filtering (`WHERE type LIKE 'runtime.%'`) to produce per-layer cost attribution.

### §8.3 Runtime → Memory (Agent Outcomes)

When a producer agent completes a task, the Runtime writes the outcome to Memory via the ProducerMemoryProxy. This is the happy path:

```python
async with spawner.spawn_subagent("bmad-agent-architect", role=AgentRole.PRODUCER, input_payload=task) as agent:
    result = await agent.run()
    # result is an AgentOutputSchema instance
    await agent.memory.store_task_outcome(
        tenant_id=manifest.tenant_id,
        task=task.to_signature(),
        outcome=TaskOutcomeDraft.from_agent_result(result),
    )
```

**Reviewer agents don't store task outcomes.** ReviewerMemoryProxy has no `store_task_outcome` method — reviewers capture their output via `store_decision` (Atelier decision record) or `flag_and_quarantine` (if they find problems).

**Error path:** If `store_task_outcome` raises (Memory backend failure, quota exceeded, tenant drift), the Spawner catches the exception, emits a `runtime.agent_result_lost` CostEvent with severity metadata, and re-raises to the caller. The agent's work is still returned to the parent (the result is in the `result` variable); it's just not persisted for cross-session retrieval. This is a graceful degradation mode — correctness of the current session is preserved; the cost is loss of future retrieval value.

### §8.4 Runtime → Compression (Agent Conversations)

Agent conversations are long — a Winston drafting session can span 50–200 LLM turns. Stage 2 compression (TONL + Forge + Caveman) was built to compact exactly this kind of payload.

**Integration seam:** The MCPToolAdapter (§5) and the agent's LLM wrapper invoke Stage 2 compression on two paths:

1. **Pre-send compression:** When assembling an LLM request that exceeds a threshold (default 50% of the model's context window), the Runtime compresses prior-turn payloads via `praxis.kernel.compression.compress(...)`. The compressed form is sent; the decompressed form is reconstructed on the receiving side only if explicitly needed (e.g., for Mary's research output to feed into Caravaggio's slide deck).

2. **Memory-write compression:** When writing large payloads to Memory (agent outcomes with verbose artifacts), the Runtime can optionally pass the payload through Stage 2 compression first. This is the F-2 absorption that was PARKED to Stage 6 per the deferred-findings brief — I am NOT designing it in Stage 4. If Winston's 4.1 architecture naturally exposes a compression seam at the Memory boundary, that's a free optionality; if not, Stage 6 reassesses.

**Configuration:** Compression is opt-in per tool-call and per Memory-write, controllable via deployment config. Default: pre-send compression enabled on conversations above the threshold; Memory-write compression disabled (F-2 parked).

### §8.5 Runtime → MAC Handoff (Stage 5)

The Runtime is the substrate MAC (Stage 5 Meta-Agent Controller) consumes. This handoff contract specifies what MAC can expect from Runtime and what Runtime expects back.

**What Runtime provides to MAC:**
- Agent spawning (subagent + team modes) via `AgentSpawner`
- Agent registry queries via `AgentRegistry`
- Tool invocation via `MCPToolAdapter`
- Communication bus (§7) for team coordination
- Cost attribution via Pi-Mono (§8.1, §8.2)
- Memory integration via proxy construction (§4.1)
- Jobs infrastructure for durable work (§4.2)

**What MAC provides to Runtime:**
- Phase-selection logic (which agent invocations run in what order) — MAC is the conductor; Runtime is the stage
- Quality scoring for agent outputs (populating Memory's `quality_score` and `quality_confidence` fields used in admission gating, Memory Req #39)
- Deliberation loop semantics (producer/reviewer cycles, consensus protocols)
- Phase-to-agent mapping (MAC decides that "this problem needs Winston → Murat → Amelia," Runtime executes the sequence)

**What MAC does NOT override:**
- Information asymmetry enforcement — §4.1's type-level partitioning is structural; MAC does not relax it
- Tool allowlists — §9 allowlists are structural; MAC respects them
- Resource budgets — §4.3 budgets bind MAC-initiated spawns exactly as they bind direct spawns

**Stage 5 open questions deferred to this section** (listed in §12 Open Questions):
- Does MAC introduce a finer-grained `visibility_scope` primitive that allows "reviewer sees decisions of type X but not Y"? If so, the type-level partitioning in §4.1 must compose with it cleanly.
- Does MAC own the destructive-op approval workflow (§9.3 Class D P2-cap deferral), or does Stage 7 POV Harness?

### §8.6 Runtime → Stage 2 Compression (Formal Contract)

Formal seam for §8.4:

```python
from praxis.kernel.compression import Compressor, CompressionPolicy


class RuntimeCompressionAdapter:
    """The Runtime's single seam to Stage 2 compression.

    All compression calls route through this adapter so that CostEvents
    are consistently attributed and the on/off switch per deployment is
    centrally enforced.
    """

    def __init__(
        self,
        compressor: Compressor,
        cost_tracker: "CostTracker",
        manifest: DeploymentManifest,
        enable_presend_compression: bool = True,
        enable_memory_write_compression: bool = False,  # F-2 parked
    ) -> None:
        ...

    async def compress_llm_payload(self, payload: str, *, policy: CompressionPolicy) -> str:
        """Compress a payload destined for an LLM request. Emits CostEvent."""
        if not self._enable_presend_compression:
            return payload
        result = await self._compressor.compress(payload, policy=policy)
        await self._cost_tracker.track_cost(
            CostEvent(type="runtime.compression", ...)
        )
        return result.compressed

    # Memory-write compression is NOT exposed in Stage 4 — F-2 is parked
```

**F-2 parking:** `enable_memory_write_compression` defaults to `False` and has no enabling pathway in Stage 4 config. This is deliberate — F-2 is parked per Pipeline.md §4.7 and the deferred findings brief §4. Stage 6 optimization pass revisits.

---

## §9. Security Model

### §9.0 The Punchline — Information Asymmetry Enforcement

**Information asymmetry is enforced at the Python type system level via Protocol narrowing (§4.1.3) and Spawner-side proxy construction (§4.1.5). Misconfiguration is not a runtime allowlist error — it is an `AttributeError` at the Python interpreter level, because the forbidden method does not exist on `ReviewerMemoryProxy`.**

Elaboration follows. Every other security claim in this section is downstream of this one.

### §9.1 Information Asymmetry — Full Structural Claim

Winston §9 (stage-4-winston-prompt.md risk context) mandates: *"Information asymmetry violation: if reviewer agent accidentally sees producer's reasoning, the multi-agent quality advantage collapses. Enforcement must be structural, not trusted."*

**Praxis implements this via two independent structural layers.**

#### §9.1.1 Layer 1 — Type-Level Memory Protocol Partitioning (§4.1.3–§4.1.5)

`MemoryProtocol` has 10 methods (store_task_outcome, store_decision, store_fact, retrieve_similar_tasks, retrieve_decisions, retrieve_facts, delete, export, flag_and_quarantine, health). `ReviewerMemoryProtocol` is a strict subset with 2 methods: `store_decision` and `flag_and_quarantine`.

`ProducerMemoryProxy` is a concrete class implementing the full 10-method surface, forwarding to the Memory facade with tenant-identity defense-in-depth checks.

`ReviewerMemoryProxy` is a concrete class implementing the 2-method surface ONLY. The 8 excluded methods are **not present on the class**. They cannot be called. They cannot be discovered via `hasattr`. They do not exist.

The Spawner's `_construct_memory_proxy` method (§4.1.5) is the single point of proxy creation in the entire Runtime. Every spawned agent receives either `ProducerMemoryProxy` or `ReviewerMemoryProxy` based on the mandatory `AgentRole` argument at spawn time. There is no default, no inheritance path, no back-door. `SpawnedAgent` does not expose the underlying Memory facade to the spawned agent's code — the proxy is the only memory handle the agent ever holds.

**Enforcement property:** A reviewer agent that attempts to call `retrieve_similar_tasks` on its memory handle receives `AttributeError: 'ReviewerMemoryProxy' object has no attribute 'retrieve_similar_tasks'` at the Python interpreter level. No runtime check. No allowlist. No role string. No configuration. **The method is not present.** Breaching this enforcement requires modifying `ReviewerMemoryProxy` class source and redeploying — an auditable change visible in git history and blocked by Cleo clean-code review per Stage 2/3 precedent.

#### §9.1.2 Layer 2 — Bus-Layer Role Filtering (§7.5)

The Communication Bus's `read(...)` API filters events by role: reviewer agents cannot receive events whose `sender_role == PRODUCER`. This is the coordination-layer equivalent of Layer 1.

**Enforcement property:** The `_visible_to` filter in §7.4 is a single Python function. Its correctness is verifiable by grep + unit test. Breaching this enforcement requires modifying `_visible_to` and redeploying — same audit trail as Layer 1.

#### §9.1.3 Defense-in-Depth Composition

Layer 1 and Layer 2 are independent. Breaching information asymmetry requires breaching both. A reviewer that somehow obtained a `ProducerMemoryProxy` (impossible by §4.1.5 construction, but assume) would still be blocked from seeing producer-authored bus events by Layer 2. Conversely, a bug in `_visible_to` that leaked bus events would not leak Memory state because Layer 1 still enforces the type-level narrowing.

**This is structural, not trusted.** There is no configuration field that toggles asymmetry enforcement. There is no allowlist that can be mis-typed. There is no role-string that can be forgotten. The enforcement is in the class structure itself.

### §9.2 Tool Allowlist Enforcement (Per Agent)

Every agent has a `tool_allowlist: frozenset[str]` on its `AgentRuntimeConfig`. The MCPToolAdapter (§5.3) enforces allowlist at invocation time as step 1 of the invocation pipeline — before input validation, before client acquisition, before anything else.

**Default is empty.** Per Andrey's decision resolution on Carson §6.9.1, agents have NO default tool access. Every tool grant is explicit, auditable, and deployment-configurable. Stage 4 ships with a baseline capability-to-tool mapping (e.g., Amelia gets fs-write, GitHub-write, PostgreSQL-read, subprocess) but this mapping is config, not code — deployments can narrow further but cannot broaden without explicit operator action audit-logged per R47.

**Mode separation.** Tools that support both read and write modes are granted separately. `tool_allowlist` entries are tuples `(tool_name, mode)` where mode is `read` or `write`. An agent granted `("fs-mcp", "read")` cannot write via fs-mcp; attempting to do so raises `ToolCapabilityError` before the MCP call is issued.

**Grant precedence:**
1. Deployment-operator explicit deny (absolute, non-overridable)
2. Deployment-operator explicit grant
3. Baseline capability-to-tool mapping for the agent's role
4. Default: no access

### §9.3 Class D Tools — P2-Cap with Forward Reference to §12

**Carson §6.9.2 decision resolved:** The human-in-loop destructive-op approval workflow is deferred from Stage 4. Class D tools are P2-capped and not admitted in their write modes at launch.

**Concrete consequences:**
- **Kubernetes MCP (P1-4):** Read-only at launch. Pod inspection, log retrieval, deployment observation permitted. `kubectl apply`, `kubectl delete`, namespace operations NOT permitted. Write mode is P2-capped until the approval workflow ships.
- **Playwright MCP (P0-5):** Read-only at launch. Screenshots, DOM inspection, non-authenticated navigation permitted. Form submission with stored credentials NOT permitted. Write mode P2-capped.
- **Vault MCP (P1-12):** Read-only at launch. Secret lookups permitted (for operational debugging by Amelia and Barry specifically). Secret creation, rotation, ACL modification NOT permitted. Write mode P2-capped.
- **Terraform / AWS CLI / GCP CLI / Ansible (all P2 per Carson §3):** Not admitted at launch in any mode. Stage 5+ reassess.
- **Subprocess (P0-7b):** Admitted at launch with Class D blast radius rating, but narrow per-binary allowlist (pytest, ruff, mypy, python, pip, npm test, node) and tight agent allowlist (Amelia, Barry, Quinn only). This is the only Class D tool admitted at launch. Its admission is justified by the narrowness of the binary allowlist + the ResourceBudget enforcement of CPU/memory/wall-time caps (§4.3).

**§12 forward reference:** *"§12 Open Question 4 — Destructive-op approval workflow scope. Stage 5 MAC (if approval is part of the deliberation cycle) OR Stage 7 POV Harness (if approval is a UI/notification concern). Decision deferred to Stage 5.0.1 elicitation or Stage 7 kickoff. Until resolved, Class D tools remain read-only-capped at launch."*

### §9.4 Defense-in-Depth Tenant Validation (R3, R4, R6 Anchors)

Tenant identity is validated at **three independent layers**:

#### §9.4.1 Layer A — Manifest Boot Check (R3)

At Runtime startup, the `DeploymentManifest` is loaded from its signed file and its signature is verified against the deployment's signing authority public key. The manifest records:
- `tenant_id` (stable)
- `tenant_hash` (cryptographic, used as primary row-level tenant marker per R6)
- `database_fingerprint` (cross-checked against the actual Postgres instance's metadata)
- `embedding_model_id` (cross-checked against Memory's embedder + §3.5 Registry's embedder)
- `provider_key_identifier` (cross-checked against the loaded LLM provider credentials)
- `seed_version`, `praxis_version`, `signing_authority_signature`

Any cross-check failure at boot → **hard-fail with `DeploymentManifestDriftError`.** The Runtime refuses to start.

#### §9.4.2 Layer B — Manifest Heartbeat (R4)

Every 60 seconds at runtime, the manifest is re-verified. The signature check repeats. The database fingerprint is re-validated. If any drift is detected → **hard-fail with `DeploymentManifestDriftError`, cancel all active spawns, terminate the Runtime process.** This is the R4 invariant translated directly to code.

**Why hard-fail rather than degrade:** Manifest drift is the canonical attack surface for tenant impersonation. Degrading gracefully would preserve availability at the cost of R11 (cross-tenant retrieval is a non-existent code path). Praxis chooses correctness over availability here. Operators can restart the Runtime with a valid manifest after investigating the drift.

#### §9.4.3 Layer C — Per-Operation Cross-Check

Every cross-stage operation that carries a tenant identifier cross-checks it against the manifest at operation time:

- `ProducerMemoryProxy` / `ReviewerMemoryProxy` `_cross_check_tenant` (§4.1.4) — compares caller-provided `tenant_id` against the manifest's `tenant_id`; raises `PermissionError` on mismatch
- `§8.1.4 Path A` reaper completion — transaction reads `tenant_hash` from the job row, compares against the manifest at cost-event emission time; hard-fail on mismatch
- `§8.1.5 Path B` tick drain — `_drain_once` validates every `AuditEvent.tenant_hash` against the manifest before building the CostEvent; raises `TenantDriftError` on mismatch
- `§7.4` bus read — `_visible_to` filter checks `event.tenant_hash` against the manifest; filters out any event with a mismatched tenant (defense-in-depth against structurally impossible states)

**Three independent layers. Breaching tenant isolation requires breaching all three.** Each layer is individually auditable (grep target per layer) and each layer operates on a different information flow (boot-time config, runtime heartbeat, per-operation invocation).

### §9.5 Sandbox Boundaries (Per Blast-Radius Class)

Derived from Carson §5.6 and §6.5, Stage 4's sandbox policy is:

| Class | Sandbox policy |
|---|---|
| **A — Inert** | No sandbox beyond the MCP server's own isolation. Broadly allowlisted. |
| **B — Scoped egress** | HTTPS egress to a per-tool domain allowlist. Rate-limited per-tool via token bucket. Credentials loaded from tenant-scoped manifest at Runtime init; agents never see them. |
| **C — Tenant data surface** | Filesystem-sandboxed to workspace root. No access to `.env`, `.ssh/`, `credentials.*`, `**/secrets/**`. Read-write separation mandatory — write requires explicit per-agent mode grant. Credentials tenant-scoped. |
| **D — Destructive / escalation-capable** | Read mode: same as Class C. Write mode: P2-capped at launch (§9.3). Subprocess is the sole exception, admitted with narrow per-binary allowlist + ResourceBudget caps. |
| **E — Unbounded** | **Not admitted.** Tool submissions that would fall into Class E are rejected at the Carson §5.4 intake protocol gate, not at the sandbox layer. |

### §9.6 Secret Isolation

**No agent has access to secret files.** The filesystem sandbox blocks reads of `.env`, `.ssh/`, `credentials.*`, and `**/secrets/**`. This is enforced at the MCP filesystem server's own path validation, not at the Praxis layer — the MCP server is configured with a denylist at Runtime init and refuses reads matching those patterns.

**Credentials flow only through deployment config.** LLM provider keys, MCP server credentials (GitHub App, Tavily API key, Slack token, etc.), and Postgres connection strings are loaded from the signed manifest at Runtime init into in-memory config structures. Agents have no API to inspect credentials, no tool to read them, no Memory method to retrieve them. If an agent's code generation produces a string that matches the shape of a known credential (e.g., `sk-...`), the telemetry layer's R53 allowlist enforces redaction before any logging.

**Credential rotation:** Credentials rotate via deployment operator action — config file update + Runtime SIGHUP to reload. There is no hot-rotation of credentials mid-spawn (Stage 4 does not support this — agents that started with a credential continue with it until their spawn completes or is cancelled).

### §9.7 Privilege Escalation Prevention

**Agents cannot:**
1. Modify their own `AgentRuntimeConfig` (frozen Pydantic model)
2. Modify their `tool_allowlist` (frozen set)
3. Modify their `ResourceBudget` (frozen dataclass; Spawner is authoritative)
4. Modify their memory proxy (proxy is constructed by Spawner; no mutation API)
5. Spawn child agents with broader permissions than themselves (the Spawner refuses spawns where the child's implied allowlist exceeds the parent's)

**Enforcement:** All of the above are enforced by Pydantic `frozen=True` models + immutable primitive types (frozenset, tuple). Attempting to mutate raises `ValidationError` or `AttributeError`. There is no dynamic override path.

**The Spawner's "broader permissions" check:** When an agent requests `spawn_subagent` or `spawn_team`, the Spawner computes the requested child agent's implied allowlist from the config baseline and compares it against the parent's current allowlist. Any tool in the child's implied list that is NOT in the parent's allowlist is stripped. This prevents privilege escalation via "spawn a more-privileged child."

### §9.8 Circular Spawning Prevention

**Problem:** Agent A spawns Agent B which spawns Agent A which spawns Agent B — infinite recursion that consumes the deployment's cost budget.

**Defenses (three-layer):**
1. **Depth limit.** Every spawn carries a `spawn_depth` counter inherited from the parent + 1. The Spawner refuses spawns where `spawn_depth > max_depth` (default 8). Depth limit is configurable; deeper workflows are explicit opt-in.
2. **Cycle detection.** Each spawn records its `(agent_name, parent_spawn_id)` chain. The Spawner scans the chain on spawn request and refuses a spawn where the same agent appears more than N times in the ancestry (default 2 — agents can be recursively invoked up to 2 deep, but not 3).
3. **Budget enforcement.** Parent's ResourceBudget includes the aggregate cost of its descendants. A runaway recursive spawn exhausts the parent's budget long before it exhausts the deployment — and budget exhaustion cancels the entire spawn tree, not just the leaf.

### §9.9 Cross-Session State Leakage Prevention

**Problem:** An agent in Session X somehow reads state from Session Y (within the same tenant, different workflow).

**Defenses:**
1. **Session-scoped memory facets.** Mem0's three-axis scoping (`tenant_id`, `agent_id`, `run_id`) per Memory Req #12 means facts written in Session Y are retrievable only by queries matching the same `run_id`. Session X's run_id is different → zero hits.
2. **Atelier decisions and task outcomes** are tenant-scoped but NOT session-scoped — they are intentionally cross-session so that Memory's R22 source-distribution telemetry can attribute cross-session learning. This is the DESIGN, not a bug. Information leakage across sessions within a tenant is acceptable and expected because sessions within a single tenant are owned by the same customer.
3. **Cross-tenant leakage** is prevented by R11 + §9.4's three-layer tenant validation + §4.1.4 proxy-level `_cross_check_tenant`. Cross-tenant retrieval is structurally impossible.

### §9.10 Summary of Structural vs. Trusted Controls

| Control | Structural or Trusted | Where enforced |
|---|---|---|
| Information asymmetry (producer/reviewer) | **Structural** | §4.1.3–§4.1.5 type-level; §7.5 bus filter |
| Tenant isolation | **Structural** | §9.4 three-layer (boot, heartbeat, per-op) |
| Cross-tenant retrieval (R11) | **Structural** | Per-deployment Postgres + proxy cross-check |
| Secret file access | **Structural** | Filesystem sandbox denylist at MCP server layer |
| Privilege escalation | **Structural** | Frozen Pydantic models; parent-child allowlist intersection |
| Circular spawning | **Mixed** | Depth limit + cycle detection (structural) + budget enforcement (operational) |
| Tool allowlist | **Trusted** (config-driven) | §9.2 — per-agent allowlist is deployment config, can be mis-typed |
| Rate limits | **Trusted** (config-driven) | Per-tool token bucket; deployment config |
| Class D write-mode gating | **Trusted deferral** | §9.3 — P2-cap at launch; approval workflow deferred |

**Praxis's structural claim:** the *correctness-critical* controls (asymmetry, tenant isolation, R11, secret access, escalation) are all structural. The *operationally-tunable* controls (allowlists, rate limits) are trusted config and are the appropriate abstraction for deployment flexibility. The line between these two categories is the line between "invariants that, if violated, break the system" and "policies that, if mis-tuned, degrade the system."

---

## §9 End — Checkpoint 2 Boundary

**Status:** §6 Tool Library Catalog (P0 full cards + P1 summary cards + P2 reference + intake protocol + blast-radius mapping), §7 Inter-Agent Communication Bus (Beads-backed append-only event log, Layer 2 asymmetry via bus-read filter, team barriers), §8 Integration Contracts (§8.1 full Path A/Path B elaboration with side-by-side table and diagram, §8.2 Runtime CostEvent categories, §8.3 Memory writeback, §8.4 Compression seam, §8.5 MAC handoff, §8.6 F-2 parking), §9 Security Model (punchline first, §9.1 structural asymmetry claim, §9.2 allowlist, §9.3 Class D P2-cap with §12 forward-ref, §9.4 three-layer tenant validation, §9.5–§9.10 sandbox/secret/escalation/cycles/leakage and the structural-vs-trusted summary).

**Halt at §9 boundary per Andrey's draft cadence instruction.** §10 Observability Hooks, §11 Testability Notes for Murat, §12 Open Questions are NOT drafted.

---

## §10. Observability Hooks

The Observability layer is how operators, Murat's Stage 4.4 tests, and downstream Stage 5 MAC deliberation consume Runtime state. This section specifies the metrics, the alert wiring, and the dashboard-level aggregation. All metrics flow through the OpenTelemetry exporter tool (§6.1.8 P0-8) and therefore inherit R53's hard allowlist discipline: numeric/aggregate/allowlisted fields only; raw content is never emitted.

### §10.1 Metric Taxonomy Overview

Runtime metrics are organized into six families, each with its own namespace prefix so that downstream aggregation queries can filter cleanly:

| Family | Prefix | Purpose |
|---|---|---|
| **Agent Lifecycle** | `runtime.agent.*` | Spawn, terminate, budget exhaustion, registry queries |
| **Tool Invocation** | `runtime.tool.*` | Per-class tool call counts, latency, errors |
| **F-1 Adapter** | `runtime.outbox.*` | Path A reaper emission, Path B tick-drain lag, poison alerts |
| **Asymmetry Enforcement** | `runtime.asymmetry.*` | Bus filter hits, proxy enforcement, reviewer visibility |
| **Tenant Validation** | `runtime.manifest.*` | R3 boot check, R4 heartbeat success rate, per-op drift |
| **Jobs Infrastructure** | `runtime.jobs.*` | Queue depth, worker loop health, orphan reclaim, retry state |

All metrics carry a `tenant_hash` label (per R6) and a `praxis_version` label. No metric carries raw query content, embeddings, or retrieval results — those are R53 violations and are rejected at the exporter tool boundary.

### §10.2 Agent Lifecycle Metrics

#### §10.2.1 Spawn and Terminate

| Metric | Type | Labels | Description |
|---|---|---|---|
| `runtime.agent.spawn.count` | Counter | `tenant_hash`, `agent_name`, `role`, `mode` | Total agent spawns since process start |
| `runtime.agent.spawn.duration_ms` | Histogram | `tenant_hash`, `agent_name`, `mode` | Time from spawn request to agent-ready state |
| `runtime.agent.terminate.count` | Counter | `tenant_hash`, `agent_name`, `role`, `mode`, `terminate_reason` | Termination reason ∈ {normal, budget_exceeded, crash, cancelled, parent_failed} |
| `runtime.agent.active.gauge` | Gauge | `tenant_hash` | Currently-active spawn count — watch for runaway growth |
| `runtime.agent.depth.histogram` | Histogram | `tenant_hash` | Spawn tree depth distribution — flags deep recursive chains before §9.8 depth-limit kicks in |

**Spawn-time SLO:** `runtime.agent.spawn.duration_ms` p99 ≤ 500ms for subagent mode, ≤ 2s for team mode (per Winston §5 NFR 10). Violations trigger a P3 alert.

#### §10.2.2 Registry Queries

| Metric | Type | Labels | Description |
|---|---|---|---|
| `runtime.agent.registry.query.count` | Counter | `tenant_hash`, `match_source` | match_source ∈ {token, semantic, llm_rerank} |
| `runtime.agent.registry.query.confidence` | Histogram | `tenant_hash`, `match_source` | Confidence score distribution; low-confidence cluster indicates registry mis-tuning |
| `runtime.agent.registry.llm_rerank.count` | Counter | `tenant_hash` | LLM tie-break invocations (expensive; should be <5% of queries) |

**Budget enforcement:**

| Metric | Type | Labels | Description |
|---|---|---|---|
| `runtime.agent.budget.exceeded.count` | Counter | `tenant_hash`, `agent_name`, `dimension` | dimension ∈ {tokens, wall_time, tool_calls, memory_writes} |
| `runtime.agent.budget.consumed_pct` | Histogram | `tenant_hash`, `agent_name`, `dimension` | Budget fraction consumed at spawn termination |

### §10.3 Tool Invocation Metrics (Per Blast-Radius Class)

Per Andrey's specific ask, tool-call metrics carry a `blast_class` label referencing Carson §5.6 Class A–E tiering:

| Metric | Type | Labels | Description |
|---|---|---|---|
| `runtime.tool.call.count` | Counter | `tenant_hash`, `agent_name`, `tool_name`, `blast_class`, `mode`, `outcome` | blast_class ∈ {A, B, C, D}; mode ∈ {read, write}; outcome ∈ {ok, denied, error, budget_exceeded} |
| `runtime.tool.call.duration_ms` | Histogram | `tenant_hash`, `tool_name`, `blast_class` | End-to-end tool call latency |
| `runtime.tool.call.cost_usd` | Histogram | `tenant_hash`, `tool_name`, `blast_class` | Per-call cost via Pi-Mono CostEvent lookup |
| `runtime.tool.allowlist.denied.count` | Counter | `tenant_hash`, `agent_name`, `tool_name` | Tool invocation denied due to missing allowlist entry (§9.2) — **watch for spikes as a potential misconfiguration signal** |
| `runtime.tool.mode.denied.count` | Counter | `tenant_hash`, `agent_name`, `tool_name` | Write mode requested but not granted (§9.2) |
| `runtime.tool.class_d.call.count` | Counter | `tenant_hash`, `agent_name`, `tool_name` | **Dedicated Class D counter.** Class D tool calls are rare by design; any non-zero value warrants review. |

**Class-level rollups** (derived from the above):
- `runtime.tool.call.count{blast_class="A"}` — expected highest volume (Tavily, Context7, SEC EDGAR)
- `runtime.tool.call.count{blast_class="D"}` — expected near-zero at launch (only subprocess admitted; others P2-capped per §9.3)

**Cardinality budget:** Per R53, metric cardinality is bounded. `tool_name` is cardinality-bounded by the Registry (§5.2) — currently 8 P0 + 15 P1 = 23 distinct names. `agent_name` is cardinality-bounded by the manifest — 16 distinct names. `tenant_hash` is cardinality-bounded by the single-tenant-per-deployment topology — 1 distinct value per deployment. Total cardinality per metric ≤ 23 × 16 × 1 × (outcome_count=4) × (mode_count=2) ≈ 3K series. Well within observability backend limits.

### §10.4 F-1 Adapter Metrics (Path A and Path B)

Per Andrey's specific asks:

#### §10.4.1 Path A — Reaper-Direct Emission

| Metric | Type | Labels | Description |
|---|---|---|---|
| `runtime.outbox.reaper.emit.count` | Counter | `tenant_hash`, `job_type` | **Per Andrey's ask:** reaper CostEvent emission volume by tenant_hash + job_type |
| `runtime.outbox.reaper.txn.duration_ms` | Histogram | `tenant_hash`, `job_type` | Time for the combined `jobs_queue UPDATE + events_outbox INSERT` transaction |
| `runtime.outbox.reaper.txn.rollback.count` | Counter | `tenant_hash`, `job_type`, `rollback_reason` | Path A transaction rollback rate — should be near-zero |

**Path A SLO:** `runtime.outbox.reaper.txn.duration_ms` p99 ≤ 200ms. Violations trigger a P2 alert (reaper throughput degradation affects NFR-C-A1 crypto-shred SLA).

#### §10.4.2 Path B — Tick-Drain

| Metric | Type | Labels | Description |
|---|---|---|---|
| `runtime.outbox.tickdrain.lag_ms` | Histogram | `tenant_hash`, `event_type` | **Per Andrey's ask:** time from `_audit_append()` to `events_outbox` commit. p99 target ≤ 1500ms (3× tick interval) |
| `runtime.outbox.tickdrain.batch.size` | Histogram | `tenant_hash` | Events drained per tick; steady growth without drain is a leak indicator |
| `runtime.outbox.tickdrain.rollback.count` | Counter | `tenant_hash`, `rollback_reason` | Tick-drain transaction rollback rate |
| `runtime.outbox.tickdrain.window_gap.events_dropped` | Counter | `tenant_hash`, `event_type` | **The documented Path B window-of-loss.** Incremented only when crash recovery reveals events that were in `_audit` buffer but not yet in the transaction. Non-zero values are expected (documented acceptable behavior) but should be tracked per incident. |

**Path B SLO:** `runtime.outbox.tickdrain.lag_ms` p99 ≤ 1500ms under nominal load, ≤ 3000ms under stress. p99.9 ≤ 5000ms. Violations trigger a P3 alert (billing reconciliation lag, not a compliance SLA breach).

**Gap metric note:** `runtime.outbox.tickdrain.window_gap.events_dropped` is the *honest* metric — it acknowledges that the window-of-loss exists and measures its frequency. A compliance auditor reading this metric sees exactly what Andrey specified in the Path B semantics: "at-least-once-with-tick-boundary-gap-on-process-crash." The metric value is normally 0 (no crashes); under crash load-testing it is bounded by `tick_interval_ms` worth of events.

**Alert threshold (P2 — steady-state sustained non-zero):** Non-zero on crash-recovery is expected and documented (bounded by `tick_interval_ms`). **Sustained non-zero in steady-state — i.e., `runtime.outbox.tickdrain.window_gap.events_dropped` incrementing without a recent process-restart signal within the last 10 minutes — is a P2 alert.** Sustained increment outside its documented cause indicates either (a) the tick drain is failing silently (events are being marked dropped without a crash justifying them), or (b) crash-recovery attribution is missing an event (increments are not being correlated back to their triggering restart). The honest operational story is: *we accept a bounded window-of-loss on documented cause, and we alert loudly if that window shows up without its cause.* Operators investigate any increment in `events_dropped` that is not paired with a corresponding `runtime.jobs.worker.orphan_reclaim.count` increment within the same 10-minute window.

#### §10.4.3 Poison Event Alerts (Per §8.1.5 Severity Map)

| Alert | Trigger | Severity | Escalation |
|---|---|---|---|
| `runtime.outbox.poison.retention_action` | `jobs_queue.state='poisoned' AND job_type='retention_shred' OR job_type='retention_cascade' OR job_type='backup_rewrite'` | **P1** | NFR-C-A1 SLA in flight — page on-call immediately |
| `runtime.outbox.poison.quarantine_promote` | `jobs_queue.state='poisoned' AND job_type='quarantine_promote'` | **P2** | Operational backlog — notify within 4 hours |
| `runtime.outbox.poison.record_created` | `outbox_drain_retries.state='quarantined' AND event_type='memory.record_created'` | **P3** | Billing reconciliation needed — notify in daily digest |
| `runtime.outbox.poison.retrieval_cache_hit` | `outbox_drain_retries.state='quarantined' AND event_type='memory.retrieval_cache_hit'` | **P3** | Silent telemetry degradation acceptable — notify in weekly digest |

**Per Andrey's specific ask:** retention_action poison = P1, record_created poison = P3. Wired exactly per §8.1.5 severity map.

### §10.5 Asymmetry Enforcement Metrics (Per Andrey's Specific Ask)

**The measurement question:** how do we know if asymmetry enforcement is catching anything vs. catching nothing? The §9.1 structural claim is type-level (AttributeError at Python interpreter level), which by construction produces no runtime events when enforcement holds — violations cause hard-crashes, not soft-filters. But Layer 2 (bus-level role filter, §7.5) produces observable events: each filtered event is an asymmetry-enforcement hit.

| Metric | Type | Labels | Description |
|---|---|---|---|
| `runtime.asymmetry.bus_filter.hit.count` | Counter | `tenant_hash`, `reviewer_agent_name`, `filtered_event_type`, `producer_sender_name` | **Per Andrey's ask:** how many bus events were filtered out per reviewer agent. Non-zero values prove the filter is actively working. |
| `runtime.asymmetry.bus_filter.visibility_events.count` | Counter | `tenant_hash`, `caller_role`, `caller_agent` | Total bus events visible to each caller after filtering — baseline for comparison with hit count |
| `runtime.asymmetry.proxy.attribute_error.count` | Counter | `tenant_hash`, `proxy_class`, `attempted_method` | **Type-level Layer 1 enforcement.** Emitted when a try/except in agent code catches an `AttributeError` from calling a non-existent method on `ReviewerMemoryProxy`. Value should be **0 in production** — a non-zero value means an agent author is attempting forbidden calls and catching the error, which is a code review signal. |

**Interpretation guide for operators:**
- `runtime.asymmetry.bus_filter.hit.count = 0` AND `runtime.asymmetry.bus_filter.visibility_events.count > 0` → filter is installed but no asymmetry violations are being attempted (healthy)
- `runtime.asymmetry.bus_filter.hit.count > 0` → reviewers are successfully prevented from seeing producer-authored events (enforcement is working)
- `runtime.asymmetry.proxy.attribute_error.count > 0` → an agent author tried to call a producer-only method on a reviewer proxy; investigate agent code (this should not happen at runtime if §11 tests pass)
- **Anomaly pattern:** `bus_filter.hit.count` suddenly drops to 0 across tenants → possible filter regression; investigate `_visible_to` implementation

### §10.6 Tenant Validation Metrics (R3/R4 Anchors)

Per Andrey's ask for R4 manifest heartbeat success rate:

| Metric | Type | Labels | Description |
|---|---|---|---|
| `runtime.manifest.boot.check.ok` | Gauge | `tenant_hash`, `praxis_version` | 1.0 if last boot check succeeded, 0.0 otherwise. Set once at startup. |
| `runtime.manifest.heartbeat.success_rate` | Gauge | `tenant_hash` | **Per Andrey's ask:** rolling 5-minute success rate for the R4 60-second heartbeat. Must be 1.0 in steady state. **Any value < 1.0 is a P1 alert — the Runtime is about to hard-fail.** |
| `runtime.manifest.heartbeat.last_success_age_seconds` | Gauge | `tenant_hash` | Seconds since last successful heartbeat. Budget: 60s. If this exceeds 75s (one missed heartbeat + jitter), P2 alert. If it exceeds 120s (two missed), P1 alert — the Runtime should have already hard-failed. |
| `runtime.manifest.drift.detected.count` | Counter | `tenant_hash`, `drift_type` | drift_type ∈ {signature_mismatch, db_fingerprint_mismatch, embedding_model_mismatch, provider_key_mismatch}. Any non-zero value is a P1 alert and the process terminates. |
| `runtime.manifest.per_op.cross_check.failure.count` | Counter | `tenant_hash`, `operation`, `layer` | operation ∈ {proxy, path_a, path_b, bus}; layer = §9.4 Layer C. Non-zero values indicate per-operation tenant identity drift. |

**The heartbeat gauge semantics are critical:** Andrey specified that a drop below 100% is itself the alert — the metric is a leading indicator of the hard-fail, not a lagging indicator of the damage. Operators learn about manifest drift via this metric *before* the Runtime terminates, giving them a few seconds to capture state or initiate controlled shutdown.

### §10.7 Jobs Infrastructure Metrics

| Metric | Type | Labels | Description |
|---|---|---|---|
| `runtime.jobs.queue.depth` | Gauge | `tenant_hash`, `state`, `job_type` | Jobs per state per type — watch for growing `pending` queue (worker starvation) or growing `failed` queue (systematic error) |
| `runtime.jobs.worker.claim.duration_ms` | Histogram | `tenant_hash`, `job_type` | Time from claim to completion |
| `runtime.jobs.worker.orphan_reclaim.count` | Counter | `tenant_hash` | NFR-Q6 orphan reclaim events at worker startup — **tracks NFR-Q6 crash recovery invocations** |
| `runtime.jobs.worker.orphan_reclaim.duration_ms` | Histogram | `tenant_hash` | Time for the UPDATE query. Must be <1000ms for NFR-Q6 budget. |
| `runtime.jobs.worker.retry.count` | Counter | `tenant_hash`, `job_type`, `retry_count_bucket` | Retry distribution — heavy tails indicate systematic issues |

### §10.8 Alert Wiring — Severity Map

Consolidating all alerts emitted across Runtime components:

| Severity | Trigger | Source | Response Time |
|---|---|---|---|
| **P1** | `runtime.outbox.poison.retention_action` | §8.1.5 | Immediate page |
| **P1** | `runtime.manifest.heartbeat.success_rate < 1.0` | §9.4 Layer B | Immediate page — hard-fail imminent |
| **P1** | `runtime.manifest.drift.detected.count > 0` | §9.4 | Immediate page — process terminating |
| **P1** | `runtime.outbox.poison.backup_rewrite` | §4.2.5 | Immediate — backup integrity at risk |
| **P1** | `runtime.outbox.poison.retention_cascade` | §4.2.5 | Immediate — GDPR Article 17 at risk |
| **P2** | `runtime.outbox.reaper.txn.duration_ms p99 > 200ms` | §10.4.1 | Within 1 hour |
| **P2** | `runtime.outbox.poison.quarantine_promote` | §8.1.5 | Within 4 hours |
| **P2** | `runtime.manifest.heartbeat.last_success_age_seconds > 75s` | §9.4 Layer B | Within 1 hour |
| **P3** | `runtime.outbox.poison.record_created` | §8.1.5 | Daily digest |
| **P3** | `runtime.outbox.poison.retrieval_cache_hit` | §8.1.5 | Weekly digest |
| **P3** | `runtime.agent.spawn.duration_ms p99 > 500ms` (subagent) / `> 2s` (team) | §10.2.1 | Daily digest |
| **P3** | `runtime.outbox.tickdrain.lag_ms p99 > 1500ms` | §10.4.2 | Daily digest |
| **P3** | `runtime.asymmetry.proxy.attribute_error.count > 0` | §10.5 | Code review signal — notify in digest |

### §10.9 Dashboard-Level Aggregation

**Operator-facing dashboard layout (strawman for Stage 4.6 pre-sales demo):**

1. **Top row:** Runtime health — manifest heartbeat, active spawns gauge, jobs queue depth, poison count
2. **Middle row:** Cost attribution by namespace — `runtime.agent.*`, `runtime.tool.*`, `memory.*` — sliced by tenant
3. **Middle row (continued):** Tool class distribution — stacked bar of `runtime.tool.call.count` by `blast_class`
4. **Lower row:** F-1 adapter health — Path A txn duration p99, Path B tick-drain lag p99, drain batch size
5. **Lower row (continued):** Asymmetry enforcement — bus filter hit count per reviewer, proxy AttributeError count
6. **Footer:** Versioning — Praxis version, manifest seed_version, embedding_model_id, tool-lock version

**Customer-facing surfacing:** Per Memory Req #56, retrieval-quality dashboard is operator-facing by default; customer surfacing is a Stage 6/7 decision. Runtime-layer metrics follow the same rule — operator-only at Stage 4 launch.

---

## §11. Testability Notes for Murat

This section enumerates the test specs Stage 4.2 Murat Test Architect will receive. Specs are organized by security property, with acceptance criteria and coverage expectations. Every spec references the architecture subsection it validates.

### §11.1 Test Pyramid Shape

Stage 4 test budget is roughly:
- **Unit tests (60% of specs)** — component-level validation of Pydantic models, Protocol narrowing, proxy construction, schema parsing, registry indexing
- **Integration tests (30% of specs)** — cross-component flows: Spawner → Registry → Proxy → Memory; MCPToolAdapter → MCP server; tick drain → events_outbox; reaper → jobs_queue
- **End-to-end tests (10% of specs)** — full agent spawn with real Memory facade, bus coordination, tool invocation, CostEvent emission verified in Pi-Mono

**Coverage gate:** ≥85% line coverage + ≥85% branch coverage for `praxis.kernel.runtime.*`. Cleo clean-code review must pass with zero critical violations. Property-based tests for the invariants listed in §11.3–§11.7.

### §11.2 F-1 Path A / Path B Test Specs (Promoted from §8.1.6)

The four test specs from §8.1.6 are promoted to first-class §11 entries and expanded:

#### M11.2.A.1 — Path A Same-Transaction Guarantee (CRITICAL)

```
Given: A retention_shred job has been claimed by the reaper worker
And:   The reaper has executed the shred sub-steps successfully
When:  The reaper attempts to commit the completion transaction
And:   A database connectivity failure is injected AFTER the UPDATE but
       BEFORE the INSERT
Then:  The entire transaction rolls back
And:   jobs_queue.state remains 'in_progress' (not 'completed')
And:   events_outbox contains NO CostEvent for this job_id
And:   The next reaper iteration reclaims the orphan and re-runs the job
```

**Invariant:** `EXISTS events_outbox row with dedup_key='retention:{job.id}'` ⇔ `jobs_queue row with id=job.id has state='completed'`. Tested via Postgres constraint + application-level assertion on every run.

#### M11.2.A.2 — Path A NFR-C-A1 Structural Guarantee (CRITICAL)

```
Given: 10,000 retention_shred jobs have been processed over a 7-day window
When:  The test queries events_outbox for CostEvents emitted in the same
       transaction as each corresponding jobs_queue completion
Then:  Every completed job has exactly one matching CostEvent
And:   No CostEvent exists for an incomplete job
And:   The query uses a single-transaction JOIN on (transaction_id, job_id)
       to prove atomicity, not temporal correlation
```

**Coverage requirement:** Murat's test harness generates a property-based load (hypothesis strategy) of retention job sequences and asserts this invariant holds for every commit.

#### M11.2.B.1 — Path B At-Least-Once Under Crash

```
Given: The Orchestrator tick-drain loop has processed N record_created events
And:   The transaction for batch N has committed
And:   The `mark_drained(count)` call has NOT yet executed (process crash simulation)
When:  The Orchestrator restarts
Then:  The tick-drain loop re-queries the drain adapter
And:   The N events are re-proposed for drain
And:   The events_outbox idempotent INSERT silently drops the duplicates (via dedup_key on AuditEvent.id)
And:   No duplicate CostEvents exist in events_outbox
And:   The final CostEvent count matches the number of unique AuditEvent.id values originally emitted
```

**Invariant:** ∀ AuditEvent.id, the number of matching events_outbox rows is exactly 1 after recovery.

#### M11.2.B.2 — Path B Window-of-Loss on Crash Before Tick

```
Given: N record_created events have been appended to Memory.audit_buffer
And:   Zero tick-drain iterations have occurred since the last drain
And:   The Orchestrator process is SIGKILLed
When:  The Orchestrator restarts
Then:  Those N events are NOT in events_outbox
And:   The `runtime.outbox.tickdrain.window_gap.events_dropped` metric increments by N
And:   The loss is documented as acceptable Path B behavior (per §8.1.3 and §8.1.5)
And:   The test verifies the loss is bounded by tick_interval_ms worth of events
       (i.e., N ≤ expected emission rate × tick_interval_ms)
```

**Compliance note for Murat:** This test ASSERTS the loss. It does not flag the loss as a bug. The test's purpose is to prove the window is bounded — not to prove events are never lost. Billing reconciliation downstream of this test must tolerate the bound.

### §11.3 Asymmetry Enforcement Tests — Type-Level Layer (§9.1.1)

Per Andrey's specific ask: the enforcement is structural, so the test is structural. Not "does the allowlist fire?" but "does the method exist on the class?"

#### M11.3.A — ReviewerMemoryProxy Method Presence

```python
def test_reviewer_proxy_excludes_producer_methods():
    """Type-level enforcement: forbidden methods must NOT exist on the class."""
    proxy = ReviewerMemoryProxy(memory=..., tenant_id="...", agent_name="quinn", spawn_id=...)

    # Allowed methods must be present
    assert hasattr(proxy, "store_decision")
    assert hasattr(proxy, "flag_and_quarantine")

    # Forbidden methods must NOT be present
    assert not hasattr(proxy, "retrieve_similar_tasks")
    assert not hasattr(proxy, "retrieve_decisions")
    assert not hasattr(proxy, "retrieve_facts")
    assert not hasattr(proxy, "store_task_outcome")
    assert not hasattr(proxy, "store_fact")
    assert not hasattr(proxy, "delete")
    assert not hasattr(proxy, "export")
    assert not hasattr(proxy, "health")
```

#### M11.3.B — Forbidden Method Call Raises AttributeError (NOT PermissionError)

```python
async def test_forbidden_method_raises_attribute_error():
    """Structural enforcement: the method doesn't exist, so Python raises
    AttributeError, not a runtime allowlist PermissionError.

    This distinction is critical per §9.1.1 — PermissionError would mean a
    runtime allowlist check (trusted control); AttributeError means the method
    literally does not exist on the class (structural enforcement).
    """
    proxy = ReviewerMemoryProxy(memory=..., tenant_id="...", agent_name="quinn", spawn_id=...)

    with pytest.raises(AttributeError, match="object has no attribute 'retrieve_similar_tasks'"):
        await proxy.retrieve_similar_tasks(tenant_id="t1", signature=...)
```

**Test philosophy note:** If Amelia's implementation somehow catches the AttributeError and re-raises as PermissionError (to provide a "nicer" error message), this test FAILS. That's intentional — re-raising would hide the structural claim. The raw AttributeError is the feature, not a bug.

#### M11.3.C — Spawner Construction Path Enforces Role

```python
async def test_spawner_constructs_correct_proxy_type():
    spawner = AgentSpawner(...)

    async with spawner.spawn_subagent("bmad-agent-dev", role=AgentRole.PRODUCER, ...) as agent:
        assert isinstance(agent.memory, ProducerMemoryProxy)

    async with spawner.spawn_subagent("bmad-tea", role=AgentRole.REVIEWER, ...) as agent:
        assert isinstance(agent.memory, ReviewerMemoryProxy)

    # Role is mandatory
    with pytest.raises(TypeError):
        async with spawner.spawn_subagent("bmad-agent-dev", ...) as agent:  # missing role
            pass
```

### §11.4 Asymmetry Enforcement Tests — Bus Layer (§9.1.2)

Per Andrey's specific ask for bus role-filter tests:

#### M11.4.A — Bus Role Filter — Reviewer Sees No Producer Events

```python
async def test_reviewer_does_not_see_producer_bus_events():
    bus = CommunicationBus(...)

    # Producer emits an event
    await bus.emit(BusEvent(
        event_type=AGENT_MESSAGE,
        sender_role=AgentRole.PRODUCER,
        sender_agent="winston",
        recipient_agent="quinn",
        ...
    ))

    # Reviewer queries the bus
    reviewer_visible_events = await bus.read(
        caller_agent=quinn_config,
        caller_role=AgentRole.REVIEWER,
        query=BusQuery(team_id=team_id),
    )

    # Reviewer sees NOTHING because the sender was a producer
    assert reviewer_visible_events == ()
```

#### M11.4.B — Bus Role Filter — Reviewer Sees Other Reviewers' Events

```python
async def test_reviewer_sees_reviewer_authored_events():
    # Two reviewers coordinating
    await bus.emit(BusEvent(
        event_type=AGENT_MESSAGE,
        sender_role=AgentRole.REVIEWER,
        sender_agent="quinn",
        recipient_agent="murat",
        ...
    ))

    reviewer_visible_events = await bus.read(
        caller_agent=murat_config,
        caller_role=AgentRole.REVIEWER,
        query=BusQuery(team_id=team_id),
    )

    assert len(reviewer_visible_events) == 1
```

#### M11.4.C — Bus Filter Metric Emission

```python
async def test_bus_filter_emits_hit_metric():
    """Verifies §10.5 runtime.asymmetry.bus_filter.hit.count increments."""
    with metric_assertions() as metrics:
        await bus.emit(producer_event)
        _ = await bus.read(caller_role=AgentRole.REVIEWER, ...)

    assert metrics.counter_value("runtime.asymmetry.bus_filter.hit.count") == 1
```

### §11.5 Tenant Validation Tests — Three Independent Layers (§9.4)

Per Andrey's specific ask: each layer tested independently.

#### M11.5.A — Layer A Boot Check Drift

```python
def test_boot_check_fails_on_signature_mismatch():
    """Manifest boot check rejects tampered manifest."""
    manifest = DeploymentManifest.load("/path/to/manifest.json")
    # Tamper with a field
    manifest_tampered = manifest.model_copy(update={"tenant_id": "attacker_tenant"})

    with pytest.raises(DeploymentManifestDriftError, match="signature"):
        verify_manifest_at_boot(manifest_tampered, signing_key_public)


def test_boot_check_fails_on_db_fingerprint_mismatch():
    """Runtime boot fails when manifest's DB fingerprint doesn't match actual DB."""
    manifest = DeploymentManifest(..., database_fingerprint="expected_fp")
    actual_db_fp = "different_fp"

    with pytest.raises(DeploymentManifestDriftError, match="database_fingerprint"):
        cross_check_db_fingerprint(manifest, actual_db_fp)
```

#### M11.5.B — Layer B Heartbeat Drift

```python
async def test_heartbeat_hard_fails_on_mid_runtime_drift():
    """Runtime terminates on R4 drift detection."""
    runtime = await Runtime.create(manifest=...)

    # Start the 60s heartbeat
    heartbeat_task = asyncio.create_task(runtime._manifest_heartbeat_loop())

    # Inject drift: signature validity changes (e.g., signing key rotated)
    inject_signature_change(runtime._manifest)

    # Wait for next heartbeat
    await asyncio.sleep(65)

    # Heartbeat task should have raised and cancelled
    assert heartbeat_task.done()
    assert isinstance(heartbeat_task.exception(), DeploymentManifestDriftError)
    # All active spawns should be cancelled
    assert runtime._active_spawns == {}
```

#### M11.5.C — Layer C Per-Operation Drift

```python
async def test_proxy_cross_check_rejects_mismatched_tenant_id():
    proxy = ProducerMemoryProxy(memory=..., tenant_id="t1", ...)

    with pytest.raises(PermissionError, match="does not match Spawner manifest tenant_id"):
        await proxy.store_task_outcome(tenant_id="t2", task=..., outcome=...)  # wrong tenant


async def test_path_a_cross_check_rejects_drift_at_completion():
    """Simulated scenario: job row has tenant_hash='t1', manifest has tenant_hash='t2'.
    Path A completion transaction must hard-fail.
    """
    # ... (setup)
    with pytest.raises(TenantDriftError):
        await reaper._complete_retention_job(drift_injected_job, outcome)


async def test_path_b_cross_check_rejects_drift_in_tick_drain():
    # Inject an AuditEvent with tenant_hash mismatching the manifest
    drain_adapter.inject_event(AuditEvent(tenant_hash="wrong_tenant", ...))

    with pytest.raises(TenantDriftError):
        await worker._drain_once()
```

### §11.6 Allowlist Regression Tests (Observation 2 Compensating Control)

Per Andrey's specific ask — CI gate for allowlist drift:

#### M11.6.A — Allowlist Diff Without Justification Fails CI

```python
def test_allowlist_diff_requires_justification():
    """CI-level regression test. Compares the current commit's allowlist
    manifest against the baseline in main. Any diff must be accompanied by
    a JSON 'justification' field in the commit's tool_grants.json, else CI
    fails.

    This is the compensating control for tool allowlist being a trusted-not-
    structural control per §9.10.
    """
    baseline = load_allowlist_from_ref("origin/main")
    current = load_allowlist_from_ref("HEAD")

    diff = allowlist_diff(baseline, current)
    for change in diff:
        assert change.justification is not None and change.justification.strip(), (
            f"Allowlist change {change!r} requires a justification per §9.10 "
            f"compensating control policy."
        )
```

**Placement:** This test runs in the CI pipeline, not in the unit test suite. Its failure blocks merge, not runtime. Murat's Stage 4.4 CI configuration wires this into GitHub Actions / GitLab CI / Azure DevOps (whichever the deployment uses).

#### M11.6.B — Runtime Allowlist Audit Log

```python
async def test_allowlist_denial_is_audit_logged():
    """§9.2: every allowlist denial is audit-logged per R47 break-glass ledger."""
    with audit_log_assertions() as audit:
        adapter = MCPToolAdapter(...)
        try:
            await adapter.invoke(caller_agent=carson_config, tool_name="fs-mcp", mode="write", ...)
        except ToolNotAllowedError:
            pass

    assert audit.contains_entry(
        event_type="tool_allowlist_denial",
        agent="bmad-cis-agent-brainstorming-coach",
        tool="fs-mcp",
        mode="write",
    )
```

### §11.7 Jobs Table Crash Recovery Tests (NFR-Q6)

Per Andrey's specific ask:

#### M11.7.A — Worker Kill Mid-Claim → Orphan Reclaim Within 5 Min

```python
async def test_worker_crash_orphan_reclaim_within_5min():
    """NFR-Q6 5-min RTO guarantee."""
    # Start worker process 1
    worker_1 = JobsWorker(...)
    worker_1_task = asyncio.create_task(worker_1.run())

    # Insert N retention jobs
    for _ in range(100):
        await jobs_store.insert_pending_job(...)

    # Wait for worker_1 to claim some jobs
    await asyncio.sleep(1)
    claimed_before_crash = await jobs_store.query("SELECT id FROM jobs_queue WHERE state='claimed'")
    assert len(claimed_before_crash) > 0

    # Simulate SIGKILL: cancel the task brutally
    worker_1_task.cancel()
    try:
        await worker_1_task
    except asyncio.CancelledError:
        pass

    # Start worker process 2 (replacement)
    start_time = time.monotonic()
    worker_2 = JobsWorker(...)
    worker_2_task = asyncio.create_task(worker_2.run())

    # Wait for orphan reclaim
    while True:
        if not await jobs_store.query("SELECT id FROM jobs_queue WHERE state='claimed' AND claim_expires_at < NOW()"):
            break
        elapsed = time.monotonic() - start_time
        assert elapsed < 300, f"Orphan reclaim took {elapsed}s, exceeds NFR-Q6 300s budget"
        await asyncio.sleep(0.1)

    elapsed = time.monotonic() - start_time
    assert elapsed < 10, f"Orphan reclaim should be <10s nominal; took {elapsed}s"
```

### §11.8 Circular Spawning Prevention Tests (§9.8)

```python
async def test_circular_spawn_depth_limit():
    """Depth limit catches runaway recursion."""
    spawner = AgentSpawner(..., max_depth=8)

    async def nested_spawn(current_depth: int):
        if current_depth > 10:
            return
        async with spawner.spawn_subagent(
            "bmad-agent-dev",
            role=AgentRole.PRODUCER,
            input_payload=...,
            parent_spawn_id=...,
        ) as agent:
            await nested_spawn(current_depth + 1)

    with pytest.raises(MaxSpawnDepthExceededError):
        await nested_spawn(0)


async def test_circular_spawn_cycle_detection():
    """Cycle detection catches A → B → A → B patterns."""
    spawner = AgentSpawner(..., max_recursion_per_agent=2)

    # A spawns B which spawns A which spawns B (3 deep for A)
    with pytest.raises(CircularSpawnError):
        # ... orchestration ...
        pass
```

### §11.9 Privilege Escalation Tests (§9.7)

```python
def test_agent_cannot_mutate_tool_allowlist():
    """frozen=True enforcement."""
    config = AgentRuntimeConfig(..., tool_allowlist=frozenset({"fs-mcp:read"}))
    with pytest.raises((ValidationError, AttributeError)):
        config.tool_allowlist = frozenset({"fs-mcp:read", "fs-mcp:write"})


async def test_spawned_child_allowlist_is_parent_intersect():
    """Child cannot have tools the parent doesn't have."""
    parent_config = AgentRuntimeConfig(..., tool_allowlist=frozenset({"fs-mcp:read"}))
    child_baseline = frozenset({"fs-mcp:read", "github-mcp:read", "subprocess-mcp"})

    effective_child_allowlist = compute_child_allowlist(parent_config, child_baseline)
    assert effective_child_allowlist == frozenset({"fs-mcp:read"})
```

### §11.10 Tool Sandbox Escape Red Team Tests

Per Winston prompt §9 risk context: sandbox escape = security incident. Murat runs red-team-style tests against each sandbox tier:

```python
async def test_subprocess_cannot_access_secrets():
    """Subprocess sandbox blocks .env, .ssh/, credentials.*"""
    for forbidden_path in [".env", ".ssh/id_rsa", "credentials.json", "secrets/api_key"]:
        with pytest.raises(FileSystemAccessDeniedError):
            await adapter.invoke(
                caller_agent=amelia_config,
                tool_name="subprocess-mcp",
                mode="read",
                payload=SubprocessPayload(command=["cat", forbidden_path]),
            )


async def test_python_sandbox_no_network_default():
    """Python sandbox has no network by default."""
    import_test_code = "import urllib.request; urllib.request.urlopen('https://example.com').read()"
    with pytest.raises(SandboxNetworkDeniedError):
        await adapter.invoke(
            caller_agent=amelia_config,
            tool_name="python-sandbox-mcp",
            mode="read",
            payload=PythonSandboxPayload(code=import_test_code),
        )


async def test_fs_write_outside_workspace_root_denied():
    """Filesystem writes outside workspace root are blocked."""
    outside_path = "/etc/passwd"  # or equivalent on the host
    with pytest.raises(FileSystemAccessDeniedError):
        await adapter.invoke(
            caller_agent=amelia_config,
            tool_name="fs-mcp",
            mode="write",
            payload=FsWritePayload(path=outside_path, content="exploit"),
        )
```

### §11.11 Coverage Targets

| Module | Line coverage | Branch coverage | Notes |
|---|---|---|---|
| `praxis.kernel.runtime.loader` | ≥95% | ≥90% | Hot path; CSV parsing critical |
| `praxis.kernel.runtime.registry` | ≥90% | ≥85% | Semantic scoring determinism |
| `praxis.kernel.runtime.spawner` | ≥90% | ≥85% | **ProducerMemoryProxy / ReviewerMemoryProxy tests are gate-critical** |
| `praxis.kernel.runtime.proxies` | **≥98%** | **≥95%** | Every method on both proxies tested |
| `praxis.kernel.runtime.jobs` | ≥90% | ≥85% | Crash recovery path + poison handling |
| `praxis.kernel.runtime.outbox` | **≥95%** | **≥90%** | Path A/B atomicity invariants |
| `praxis.kernel.runtime.tools` | ≥85% | ≥80% | MCP adapter invocation pipeline |
| `praxis.kernel.runtime.bus` | ≥90% | ≥85% | `_visible_to` filter coverage |
| `praxis.kernel.runtime.security` | ≥90% | ≥85% | Tenant validation + sandbox tests |

**Property-based testing targets** (Hypothesis):
- Spawn depth + cycle detection (state machine strategies)
- Path A/B atomicity under randomized Postgres failure injection
- Tenant cross-check under randomized drift injection
- Bus `_visible_to` filter under randomized (sender_role, caller_role) combinations

### §11.12 Murat's Stage 4.2 Pre-Conditions

Before Murat's Stage 4.2 test strategy drafting begins, the following must be available:
- This architecture.md (§11 as the test-spec input)
- Stage 1 pi-mono test-strategy.md (for CostEvent emission test patterns)
- Stage 3 memory test-strategy.md (for proxy test patterns and R-01..R-06 precedent)
- Access to the Stage 4 reference dumps for gap analysis

**Expected Murat output:** A test-strategy.md mirroring Stage 3's ~1250-line format with explicit risk register, test IDs, and coverage matrix. Gate to Stage 4.3 Amelia is Murat's strategy approval per Stage 3 precedent.

---

## §12. Open Questions

Consolidated list of decisions deferred to Stage 5+ or pending explicit Andrey ratification. Each entry has: status, rationale, deferral target, and re-trigger conditions.

### OQ-1 — Read/Write Default Mode for P0 Tools

**Status:** **RATIFIED** (listed for traceability, not actually open)
**Resolution:** Read-only default + per-agent write allowlist. Per Andrey's decision resolution on Carson §6.9.1. See §2.3 default allowlist empty, §5.3 mode check, §5.5 sandbox philosophy, §9.2 allowlist enforcement.
**Deferral target:** None.
**Re-trigger:** None expected — this is a structural commitment.

### OQ-2 — F-2 Memory → Compression Passthrough

**Status:** **PARKED** to Stage 6 optimization pass
**Rationale:** Per `stage-4-deferred-findings-brief.md §4` and Pipeline.md §4.7, F-2 is a cost optimization, not a correctness concern. Memory writes are correct with raw JSON payloads; TONL encoding of bead payloads is a storage-footprint optimization that Stage 4 does not require.
**Deferral target:** Stage 6 optimization pass.
**Re-trigger:** Stage 5 cost data reveals a meaningful storage-cost lever from bead-payload TONL encoding. If compression ratios on bead payloads would save >10% of Stage 3 storage footprint, Stage 6 elicitation promotes this from parked to active.
**Architecture note:** Per the deferred-findings brief, if §8 naturally exposes a compression seam at the Memory boundary, that's free optionality. §8.4 / §8.6 do not expose such a seam — the Compression adapter is wired to LLM-request pre-send compression only. F-2 remains fully parked.

### OQ-3 — Reviewer Access to Reviewer-Authored Decision Corpus (Stage 5 MAC)

**Status:** **DEFERRED STRUCTURAL REFINEMENT** pending Stage 5 MAC visibility-scope primitive
**Rationale:** Per Andrey's Checkpoint 1 resolution #1, the current Stage 4 asymmetry model is binary: ReviewerMemoryProtocol exposes `store_decision` and `flag_and_quarantine` only, with no retrieve surface. A finer-grained model would allow reviewers to retrieve decisions authored by other reviewers (for collaborative review sessions) while still blocking retrieval of producer-authored records. This partitioning requires Memory-side scope filtering, which would violate binding condition #4.
**Deferral target:** Stage 5 MAC.
**Re-trigger:** Stage 5 MAC design introduces a `visibility_scope` primitive at the deliberation-cycle level. If MAC's primitive allows "reviewer sees decisions of a certain scope-tag but not others," Stage 5 handoff (§8.5) updates the proxy partitioning to consume that primitive.
**Why not now:** Stage 4's binary partitioning is the minimum viable asymmetry enforcement. Finer partitioning adds complexity without proven need — no Stage 4 use case requires reviewer-to-reviewer decision retrieval. Adding it preemptively violates "design for the problem you have, not the problem you might have."

### OQ-4 — Destructive-Op Approval Workflow Scope

**Status:** **DEFERRED** to Stage 5 MAC or Stage 7 POV Harness
**Rationale:** Per Andrey's decision resolution on Carson §6.9.2, a human-in-loop approval workflow for Class D destructive operations is architecturally substantial (pending-approval queue, notification channel, timeout policy, approval audit trail, UI surface) and spans Runtime + Notification + Durable State + UI layers. Stage 4 does not include UI or notification layers. Shipping a partial workflow in Stage 4 introduces integration debt to Stage 5 and Stage 7.
**Deferral target:** Stage 5 MAC (if approval is part of the deliberation cycle — MAC decides whether to escalate a destructive action to human review) OR Stage 7 POV Harness (if approval is a UI/notification concern — users approve actions via a web interface).
**Re-trigger:** Stage 5.0.1 elicitation explicitly scopes this. If Stage 5 MAC owns approval, Runtime's Class D write mode unblocks at Stage 5 completion. If Stage 7 POV Harness owns it, Class D write mode unblocks at Stage 7 completion.
**Consequences at Stage 4 launch:**
- Kubernetes MCP (P1): read-only at launch; destructive ops P2-capped
- Playwright MCP (P0): read-only at launch; credential-bearing form submission P2-capped
- Vault MCP (P1): read-only at launch; secret creation/rotation P2-capped
- Terraform / AWS CLI / GCP CLI / Ansible: not admitted at launch in any mode
- Subprocess (P0): admitted at launch as **sole Class D exception** with narrow per-binary allowlist + tight agent allowlist + ResourceBudget caps

### OQ-N — Stage 4.3 Implementation Decision: AuditBuffer Drain Coordination

**Status:** **OPEN** — Implementation decision deferred to Stage 4.3 Amelia, with architecture-committed default and explicit escalation trigger
**Framing:** The F-1 Path B tick-drain (§8.1.5) requires the Orchestrator to (a) snapshot undrained audit events, (b) translate them to CostEvents and insert into events_outbox atomically, (c) mark those specific events as drained so the next tick does not re-emit them. The Stage 3 AuditBuffer class at `memory/_internal/audit.py` exposes only `append(event)` / `events() → list[AuditEvent]` / `clear()` / `__len__`. There is no per-event drain semantic. `clear()` is all-or-nothing and cannot distinguish drained from newly-appended events.

**Three resolution paths:**

#### Path (i) — Position-Based Shim in Orchestrator (DEFAULT)

The Orchestrator maintains a local `_drained_count` high-water mark. Each tick:
1. Snapshot `buffer.events()` (a full list)
2. Skip the first `_drained_count` events (already drained)
3. Drain the remainder via the normal Path B transaction
4. On commit success, advance `_drained_count` by the batch length

The underlying `AuditBuffer` grows unboundedly until process restart.

**Memory footprint at NFR-Q2 rates:** `AuditEvent ≈ 500 bytes × 100K entries/tenant ≈ 50 MB per tenant across process lifetime`. Tolerable for single-tenant-per-deployment topology.

**Optional quiesce-window compaction:** Periodically check if `_drained_count == len(buffer) AND no spawns in-flight` → if both true, call `buffer.clear()` and reset `_drained_count = 0`. **However, this introduces a race condition:** a `_audit_append` call interleaving between the emptiness check and the `clear()` would silently drop the new event. Mitigation: **skip compaction entirely.** The 50 MB ceiling per tenant lifetime is acceptable; process restart resets the buffer. Simpler to not compact than to compact with races.

**Pros:** Zero memory/src/ edit. Preserves binding condition #4. Implementation is ~20 lines of Python.
**Cons:** Unbounded memory growth until process restart. Position-based accounting is subtle and easy to get wrong under concurrent append during drain.

#### Path (ii) — Minimal AuditBuffer Extension (REQUIRES BINDING CONDITION #4 RELAXATION)

Add a single new method to AuditBuffer:

```python
def drain_atomic(self) -> list[AuditEvent]:
    """Atomically snapshot and clear the buffer. Returns the snapshot.

    Acquires the internal lock, copies the events list, clears the underlying
    storage, returns the copy — all under one lock hold. Zero race conditions.
    """
    with self._lock:
        events = list(self._events)
        self._events.clear()
        return events
```

**Pros:** Surgical. One new method. Zero changes to `append`, `events`, `clear`, or to `_audit_append` call sites. Clean semantics. Zero memory leak.
**Cons:** Requires binding condition #4 relaxation. Establishes a precedent for Stage 4 → Stage 3 reaching-back, which is the exact thing binding condition #4 guards against.

#### Path (iii) — Runtime-Side Sidecar Queue (REJECTED)

Orchestrator maintains its own sidecar queue. `_audit_append` is wrapped by an Orchestrator-injected callback that mirrors each event into the sidecar. The sidecar is drained normally.

**Rejected because:** Breaks §4.2.1 composition. The sidecar is not a peer table in the shared deployment Postgres — it's an Orchestrator-owned in-memory structure. Path A's atomicity guarantee is unchanged (retention_action is reaper-direct), but the F-1 composition story becomes harder to reason about because two different drain substrates coexist. The §4.2.1 "shared-DB topology is a correctness requirement" claim weakens because Path B's state lives outside the shared topology.

**Path (iii) is rejected at architecture time, not deferred to Amelia's discretion.**

#### Architecture-committed default and escalation trigger

**Default for Amelia at Stage 4.3:** Path (i) — position-based shim with no compaction, accepting the 50 MB per-tenant-per-lifetime memory ceiling as tolerable.

**Escalation trigger:** If Amelia at implementation time discovers a blocker (e.g., `buffer.events()` has unexpected lock contention under Stage 4.4 Murat's load tests, or the position-based accounting interacts badly with async reentrance), Amelia halts Stage 4.3 implementation and elevates to a binding-condition relaxation conversation for Path (ii). Amelia does NOT silently take Path (ii) without explicit escalation — this preserves Andrey's stage-gate discipline.

**Who owns the decision:** Amelia at Stage 4.3 (implementation-layer detail); Andrey retains veto power via the escalation mechanism.

**Cross-references:** §8.1.5 Path B code uses placeholder method names `snapshot_undrained()` / `mark_drained(count)` on a `DrainAdapter` abstraction. The DrainAdapter is the Runtime-layer wrapper Amelia builds at Stage 4.3 per this OQ's default.

### OQ-5 — [Reserved slot; no novel questions surfaced during §10–§12 drafting]

### OQ-6 — Stage 5 MAC Handoff Contract Details

**Status:** **OPEN** — Stage 5 design will own these
**Rationale:** §8.5 specifies what Runtime provides to MAC and what MAC provides to Runtime at a structural level, but several details require Stage 5 elicitation:
1. MAC's phase-selection logic — does it consume `AgentRegistry.find_agents()` directly, or does it maintain its own agent-to-phase mapping?
2. MAC's quality scoring — how does MAC populate Memory's `quality_score` and `quality_confidence` fields (Memory Req #39)? Does Runtime provide an API, or does MAC write directly via its own ProducerMemoryProxy?
3. MAC-initiated spawns — do they go through the Spawner's `spawn_subagent` / `spawn_team` API with MAC as the parent, or does MAC have a privileged spawn path?
4. MAC error propagation — how are MAC deliberation errors surfaced to the Runtime's observability layer?

**Deferral target:** Stage 5 MAC design.
**Re-trigger:** Stage 5.0.1 elicitation begins. Each question becomes an elicitation input for Stage 5 Winston.

### OQ-7 — Embedding Model Consistency Between Registry and Memory

**Status:** **CONFIRMED LIVE CONSTRAINT** — not open, but worth explicitly listing
**Rationale:** Per §3.5, the Registry's embedder.model_id MUST match Memory's manifest `embedding_model_id` (R14). This cross-check happens at Runtime init and hard-fails on mismatch via `EmbedderMismatchError`.
**Re-trigger:** Deployment operator swaps embedding models without also updating Memory's manifest. Runtime refuses to start until the manifest is updated and re-signed. This is the correct behavior, not a bug.

### OQ-8 — Cardinality Explosion Under High-Tenant Counts

**Status:** **OPEN** — not relevant for Stage 4, flagged for Stage 6+
**Rationale:** §10.3 notes that current metric cardinality is bounded by the single-tenant-per-deployment topology. If Stage 6+ introduces multi-tenant-per-deployment (which would require relaxing R1), the cardinality assumptions in §10 break and the observability backend load grows linearly with tenant count.
**Deferral target:** Stage 6 scaling pass.
**Re-trigger:** Stage 6 elicitation on deployment topology evolution. If Praxis moves from managed single-tenant to multi-tenant SaaS, §10 is re-derived.

### OQ-9 — Tool Library Growth Beyond Stage 4 Catalog

**Status:** **CONFIRMED PROTOCOL** — not open, but worth listing for operators
**Rationale:** Post-launch tool additions follow Carson §5.4 intake protocol (§6.4). Tools cannot be hot-added at runtime; additions require a Praxis release cut + regression testing against affected personas.
**Re-trigger:** Customer-driven request for a new tool integration. The request flows through:
1. Seven-gate inclusion check (§5.1)
2. Black Hat re-pass against current Memory/Winston security
3. Persona + hat anchor assignment
4. P2 incubation (minimum one release cycle)
5. P1 promotion on adoption + zero incidents
6. P0 promotion on universal need + operational maturity

### §12.10 Open Question Summary Table

| ID | Title | Status | Owner | Deferral Target | Blocks Stage 4.6 completion? |
|---|---|---|---|---|---|
| OQ-1 | Read/write default mode | **RATIFIED** | — | — | No |
| OQ-2 | F-2 Memory→Compression | **PARKED** | — | Stage 6 | No |
| OQ-3 | Reviewer access to reviewer corpus | **DEFERRED** | Stage 5 MAC | Stage 5 | No |
| OQ-4 | Destructive-op approval workflow | **DEFERRED** | Stage 5 MAC / Stage 7 POV | Stage 5/7 | No — Class D read-only at launch |
| OQ-N | AuditBuffer drain coordination | **OPEN (defaulted)** | Amelia Stage 4.3 | Stage 4.3 implementation | **YES — default path (i) must ship** |
| OQ-5 | Novel-question reserve | **EMPTY** | — | — | No |
| OQ-6 | Stage 5 MAC handoff contract details | **OPEN** | Stage 5 Winston | Stage 5 | No |
| OQ-7 | Embedding model consistency | **LIVE** | — | — | No |
| OQ-8 | Cardinality explosion | **OPEN** | Stage 6 | Stage 6 | No |
| OQ-9 | Tool library growth | **PROTOCOL** | — | — | No |

**Critical path for Stage 4 completion (Pipeline.md §4.7):** OQ-N default path (i) must ship in Amelia's Stage 4.3 implementation. OQ-1, OQ-2, OQ-3, OQ-4, OQ-5, OQ-6, OQ-7, OQ-8, OQ-9 do not block Stage 4.6 completion.

**F-1 and F-3 closure status** (Pipeline.md §4.7 explicit requirement):
- **F-1:** Absorbed into §4.2 Jobs Infrastructure, §8.1 Memory → Pi-Mono Outbox Adapter (Path A / Path B), §9.4 Defense-in-Depth Tenant Validation Layer C. Stage 4.3 Amelia ships the implementation; Stage 4.4 Murat validates via M11.2.A.1, M11.2.A.2, M11.2.B.1, M11.2.B.2. Stage 4.5 Alignment Review flips Pipeline.md §3.5 `[~]` to `[x]` on successful test pass. Stage 4.6 completion gate confirms.
- **F-3:** Absorbed into §4.2 Jobs Infrastructure (schema + worker lifecycle + crash recovery). Stage 4.3 Amelia ships migration + worker; Stage 4.4 Murat validates via M11.7.A. Stage 4.5 closes.
- **F-2:** Parked to Stage 6 per OQ-2 above.

---

## DRAFT v0.3 — End of Sections §1–§12

**Status:** Full draft landed. §1 Reference Analysis, §2 Agent Definition Schema, §3 Agent Registry Design, §4 Agent Spawner Design, §5 MCP Tool Adapter Design, §6 Tool Library Catalog (anchored on Carson §4.0.1), §7 Inter-Agent Communication Bus, §8 Integration Contracts (with §8.1 full Path A/Path B elaboration), §9 Security Model (with §9.0 punchline + §9.1–§9.10), §10 Observability Hooks, §11 Testability Notes for Murat, §12 Open Questions.

**Awaiting Andrey's final architecture review before ratification.** Post-ratification, the flow advances to:
1. Stage 4.2 Murat — test strategy drafting against §11
2. Stage 4.3 Amelia — implementation with §4.2, §8.1 Path A/B, §9 structural claims, and OQ-N default path (i)
3. Stage 4.3.5 Cleo — clean-code review
4. Stage 4.4 Quinn — coverage + regression tests
5. Stage 4.5 Alignment Review — F-1 and F-3 closure gate
6. Stage 4.6 Pre-Sales Checkpoint
7. Stage 4.7 (per Pipeline.md §4.7) — F-1 and F-3 closure verification + Stage 5 gate

End of DRAFT v0.3.
