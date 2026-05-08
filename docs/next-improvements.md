# Verdaca — Next Improvements Backlog

Ideas captured during build sessions. Not roadmap commitments — a rolling list of things worth revisiting. Ordered roughly by when they become relevant, not by priority.

**Last updated:** 2026-05-08 (roundtable: Winston + Amelia + Victor + Dr. Quinn on Hermes self-learning)

---

## Stage 9 Tail / Stage 10 (Near-term)

### Memory hot/cold caching as first-class `MemoryPort` concern
Mem0 handles hot/cold internally, but it's not surfaced at the port level. A `MemoryPort.tier()` method (or adapter-level config) would let production deployments explicitly control what stays hot (Redis TTL) vs. cold storage. Currently a gap — Mem0's defaults work but aren't tunable without reaching into the adapter internals.
**Trigger:** When the first production tenant hits memory scale (200+ entries per session).

### Hermes-3 local-inference adapter for `LLMProxyPort`
At Stage 9.4.5, `ports/llm_proxy.py` gets built. Natural third adapter slot: RTK = cloud proxy, Claude API = frontier, Hermes-3 (local, llama-based) = cost-optimized for MAC iterations where full-frontier quality isn't required. Single-file adapter (~200 LOC). MIT-licensed model, runs on $5 VPS per Hermes docs.
**Trigger:** After 9.4.5 `LLMProxyPort` contract is ratified.

### Honcho dialectic user modeling → `UserModelPort`
Hermes Agent uses [Honcho](https://github.com/plastic-labs/honcho) to build persistent cross-session user profiles (behavioral patterns, preferences, inferred working style). Verdaca's memory system stores project state but has no equivalent for user behavioral modeling. New port: `UserModelPort` with a Honcho adapter.

**Port interface (from Hermes MemoryProvider ABC pattern):**
```python
class UserModelPort(Protocol):
    def sync_turn(self, turn_messages: list[Message]) -> None: ...
    def prefetch(self, query: str) -> UserProfile: ...
    def shutdown(self) -> None: ...
```
`USER.md` behavioral profile is the DTO — distinct from episodic `MEMORY.md` (what happened) vs behavioral (how the user thinks, preferences, domain expertise, communication style).

**Dr. Quinn's constraint (roundtable 2026-05-08):** Andrey's working patterns are already captured in MEMORY.md. Honcho adds value when Verdaca has *external users* whose preferences the system doesn't know. Building it now optimizes for a user population that doesn't exist yet.
**Trigger:** Stage 10 or when Verdaca ships to first external users who return across sessions.

---

## Skills & Distribution

### BMAD Skill Marketplace compliance
BMAD roadmap includes Universal Skills Architecture ("one skill, any platform") and a Skill Marketplace for community discovery. Once that ships, Verdaca's project-specific skills (`verdaca-wiki-update`, etc.) should be packaged to conform. Currently `.claude/skills/` format (Claude Code-only). Adaptive variants needed for Cursor, Codex, Kimi, OpenCode.
**Trigger:** When BMAD Skill Marketplace goes live (not on roadmap ETA yet).

### agentskills.io standard compliance
Hermes Agent skills conform to the agentskills.io open standard, making them portable across frameworks. BMAD is heading the same direction with its marketplace. Verdaca's skills should align with whichever standard wins. Track both; don't invest in conformance until one has clear adoption.
**Trigger:** When one standard has 1k+ skills in its hub.

### Self-improving skills loop
Hermes creates and improves skills from experience automatically. Verdaca's BMAD skills are static (hand-authored, manually updated). MAC sessions generate quality signal (gate scores, beat counts, A4 metrics) that could feed skill improvement. Mechanism: after each MAC close, extract what changed in halt-point dispositions → propose patch to relevant skill file → require explicit go before writing.

**Key insight from Hermes source (roundtable 2026-05-08):** The learning effect is emergent — five interlocking components, not one module. Verdaca should not copy the architecture but extract the one component that solves its actual bottleneck: **cross-session recall (FTS5) first, telemetry second, curator last**.

Verdaca's advantage Hermes doesn't have: **MAC gate scores are structured ground truth outcome signals**. Hermes curator learns from usage frequency (proxy). Verdaca has direct quality signal and is currently throwing it away.

**Critical constraint:** `feedback_memory_authorization` means any curator Verdaca builds can *propose* patches but never *apply* them on initiative. `apply_patch(authorized_by: str)` raises `AuthorizationError` if `authorized_by` is empty — this is non-negotiable and must be baked into the port contract (`M-T-SKILL-PATCH-02`).

**Full implementation sequence** — see Self-Learning Implementation Roadmap section below.
**Trigger:** Data collection starts now (zero cost). Curator adapter at Stage 10 after LLMProxyPort (9.4.5) exists.

---

## Knowledge Infrastructure

### Wiki auto-update hook
`/verdaca-wiki-update` currently requires manual invocation. Better: PreToolUse or PostToolUse Claude Code hook that detects a new handoff file landing in `knowledge/raw/session-handoffs/` and pings you to run the skill. Requires writing a hook entry in `.claude/settings.local.json`. Zero-LLM-cost detection (file watcher), wiki update still gated by explicit go.
**Trigger:** Any time — low effort addition to `settings.local.json`.

### FTS5 session search
Hermes uses SQLite FTS5 for fast keyword search across past conversation sessions. Current Verdaca approach: grep raw handoff files or read wiki pages. An FTS5 index over `knowledge/raw/session-handoffs/` would make "find the session where we decided X" instant and cheap. SQLite FTS5 is stdlib-adjacent (no external deps).

**Concrete implementation (Dr. Quinn + Amelia, roundtable 2026-05-08):**
- Script: `scripts/index-sessions.py` — scans `knowledge/raw/session-handoffs/*.md`, builds `knowledge/sessions.db` with FTS5 virtual table
- ~50 lines of Python, zero external dependencies, runs in seconds
- Two query modes: keyword (FTS5 direct) + semantic (FTS5 candidates → LLM summarization)
- Wire into `/verdaca-wiki-update` as `--index` flag for freshness check + search
- Future port: `ports/src/praxis/ports/session_index.py` — `index_session(id, content)`, `search(query, mode) → List[SessionExcerpt]`

This is the **highest-leverage single component** — it's the memory that makes all other self-learning compoundable. Without it, a future curator is blind to prior art.
**Trigger:** Stage 9.4.8 (already scheduled). Don't wait for handoff count — do it while the corpus is still small.

---

## Self-Learning Implementation Roadmap

Derived from Hermes Agent source analysis (NousResearch, 512KB, MIT). Roundtable: Winston + Amelia + Victor + Dr. Quinn, 2026-05-08. Sequenced against existing Stage 9 roadmap.

### Architecture principle (Winston)
Hermes's load-bearing decision: **skills injected as user messages, not system prompt** — preserves prompt cache, enables lazy loading, allows mid-session mutation at zero cost. Verdaca cannot replicate this at the Claude Code layer (outside ports-and-adapters boundary). Adaptation: use `VersionedStatePort` (Beads adapter, already built) to version skill content instead of patching in-place — rollback becomes free.

### Victor's strategic framing
Self-learning is the mechanism that transitions Verdaca from "product you bought" to "system that knows your business." MAC methodology can be replicated by any engineer. A system that has learned your organization's patterns over 500 sessions cannot be. **Stub `SkillEvolutionPort` now as a zero-cost architectural commitment** — empty protocol, no implementation, just the contract. When Stage 10 opens, the seam exists.

---

### Phase 0 — Do Now (zero LLM cost, zero stage gate required)

**1. Provenance frontmatter tagging**
Add `provenance: user` to frontmatter of all 60+ SKILL.md files in `.claude/skills/`. This is the safety valve that prevents a future curator from touching hand-authored skills (it only patches `provenance: agent` skills). Zero risk, zero tests.

**2. Usage sidecar tracking** (`scripts/track-skill-usage.py`)
Read Claude Code JSONL transcript at `.claude/projects/C--Users-AndreyPopov-Documents-Anthropic/*.jsonl`, extract Skill tool invocations, write per-skill `.claude/skills/{name}/.usage.json`:
```json
{
  "use_count": 3,
  "last_used_at": "2026-05-08T18:54:00Z",
  "sessions": ["2ee13f9e-..."],
  "provenance": "user",
  "state": "active"
}
```
Pure Python, no new deps. Run manually or wire as PostToolUse hook in `settings.local.json`.

**3. MAC session telemetry capture**
At each MAC close, executor writes `knowledge/raw/skill-telemetry/{session-id}.json`:
```json
{
  "skill_id": "verdaca-wiki-update",
  "session_id": "...",
  "gate_scores": {"Q1": 8, "Q2": 9},
  "beat_count": 10,
  "halt_point_dispositions": {"HP1": "GO", "HP2": "REDIRECT"}
}
```
This is data capture only — curator reads it later. Currently this signal is written to handoff prose and discarded.

---

### Phase 1 — Stage 9.4.8 (FTS5 session index)

**`scripts/index-sessions.py`** → `knowledge/sessions.db`
SQLite FTS5 virtual table over all handoffs. ~50 lines Python, zero external deps.
Wire into `/verdaca-wiki-update` as `--index` flag.
Port definition deferred to post-9.6: `ports/src/praxis/ports/session_index.py`.

---

### Phase 2 — Post-9.6 (new ports, no adapters yet)

Three new port stubs. No implementations — just Protocol definitions + contract test skeletons.

**`ports/src/praxis/ports/session_index.py`** — `SessionIndexPort`:
```python
class SessionIndexPort(Protocol):
    def index_session(self, session_id: str, content: str) -> None: ...
    def search(self, query: str, mode: Literal["keyword","semantic"],
               limit: int = 10) -> list[SessionExcerpt]: ...
```

**`ports/src/praxis/ports/skill_observer.py`** — `SkillObserverPort`:
```python
class SkillObserverPort(Protocol):
    def record_invocation(self, skill_id: str, session_id: str,
                          outcome_signals: SkillOutcome) -> None: ...
    def suggest_patch(self, skill_id: str) -> Optional[SkillPatch]: ...
    def get_usage(self, skill_id: str) -> SkillUsage: ...
```
`outcome_signals` carries MAC gate scores — Verdaca's direct quality signal vs Hermes's usage-frequency proxy.

**`ports/src/praxis/ports/skill.py`** — `SkillPort` (full surface for curator adapter):
```python
class SkillPort(Protocol):
    def record_usage(self, skill_id: str, session_id: str,
                     outcome: SkillOutcome) -> None: ...
    def query_by_relevance(self, context: str,
                           limit: int = 5) -> list[SkillMatch]: ...
    def propose_improvement(self, skill_id: str,
                            evidence: list[SessionExcerpt]) -> SkillPatch: ...
    def apply_patch(self, skill_id: str, patch: SkillPatch,
                    authorized_by: str) -> None: ...
```

**5 contract test IDs** (pending test-strategy v0.3 ratification at 9.9):
- `M-T-SKILL-USAGE-01` — `record_usage` writes `.usage.json` with all required fields
- `M-T-SKILL-USAGE-02` — `query_by_relevance` ranked by `use_count × recency`
- `M-T-SKILL-PATCH-01` — `propose_improvement` returns `SkillPatch` with diff + rationale
- `M-T-SKILL-PATCH-02` — `apply_patch` raises `AuthorizationError` if `authorized_by` is empty (**non-negotiable — `feedback_memory_authorization`**)
- `M-T-SKILL-PROV-01` — `propose_improvement` raises `SkillExemptError` for `provenance: user` skills

---

### Phase 3 — Stage 10 (CuratorAdapter + UserModelPort)

**Prerequisite: Stage 9.4.5 `LLMProxyPort` must exist.** The curator is an LLM-powered review loop — hardcoding a model call inside the adapter violates the architecture.

**`adapters/skill_curator/`** — implements `SkillPort`:
- State machine per skill: `active` → `stale` (after `stale_after_days` idle) → `archived` (never delete)
- Reads `.usage.json` sidecar + `knowledge/raw/skill-telemetry/` MAC gate scores
- LLM review pass via `LLMProxyPort` — reads skill content + outcome signals → proposes patch
- `apply_patch` enforces `authorized_by != ""` — curator proposes, Andrey approves
- Only touches `provenance: agent` skills — `provenance: user` raises `SkillExemptError`
- Pinned skills immune to all auto-transitions

**`ports/src/praxis/ports/user_model.py`** + `adapters/honcho/` — `UserModelPort` with Honcho adapter:
- `sync_turn(turn_messages)`, `prefetch(query) → UserProfile`
- `USER.md` DTO: behavioral profile (how user thinks) distinct from `MEMORY.md` (what happened)
- Activate when first external users onboard

**Trajectory RL (Atropos):** Activate after 500+ rated MAC sessions. Verdaca's MAC closes are labeled trajectories. `save_trajectories: bool` flag in MAC config, opt-in.

---

### Architectural gap: skill injection caching
Hermes injects skills as user messages (not system prompt) to preserve prompt cache hits. Verdaca's Claude Code layer controls skill injection — this is outside the ports-and-adapters boundary. **Workaround:** version skill content via `VersionedStatePort` (Beads adapter already built) instead of patching in-place. Versioned rollback is free; cache behavior is Claude Code's concern.

---

## Model & Cost

### Trajectory generation + RL fine-tuning
Hermes includes batch trajectory generation and Atropos RL environment support for fine-tuning tool-calling models on their own usage data. Verdaca's MAC sessions are high-quality labeled trajectories (quality gate scores, beat counts, correction loops). After enough sessions accumulate, running Atropos on this data could produce a fine-tuned MAC-specialized model. Long-term R&D item.
**Trigger:** Stage 10+ after 500+ rated MAC sessions.

### Ebbinghaus decay eviction at the port level
Mem0 blog technique 3: importance × age × access-frequency decay with configurable eviction threshold (default 0.15). Currently `revoke_promotion` + `migrate` do this manually. A scheduled background job calling these methods with decay-computed scores would automate eviction. Could be a Celery/APScheduler task in the production adapter layer.
**Trigger:** Production deployment with multi-tenant memory stores.

---

## Product / Distribution

### BMad in a Box — self-hosted enterprise option
BMAD roadmap includes a self-hosted deployment ("BMad in a Box"). For Verdaca enterprise clients who can't use SaaS (data sovereignty, compliance), this is the path. Requires containerized deployment (Docker Compose at minimum) of the full stack including Stage 7 POV harness.
**Trigger:** First enterprise prospect with data residency requirement.

### PDF + pptx export
ADR-08 (Stage 6, deferred). Still in Stage 7 debt ledger. Caravaggio + Mary are wired for pptx generation via BMAD skills. Unblocking requires the Stage 7 export pipeline, not new architecture.
**Trigger:** Pre-sales demo request or Stage 7 debt clearance sprint.
