# Verdaca — Next Improvements Backlog

Ideas captured during build sessions. Not roadmap commitments — a rolling list of things worth revisiting. Ordered roughly by when they become relevant, not by priority.

**Last updated:** 2026-05-08

---

## Stage 9 Tail / Stage 10 (Near-term)

### Memory hot/cold caching as first-class `MemoryPort` concern
Mem0 handles hot/cold internally, but it's not surfaced at the port level. A `MemoryPort.tier()` method (or adapter-level config) would let production deployments explicitly control what stays hot (Redis TTL) vs. cold storage. Currently a gap — Mem0's defaults work but aren't tunable without reaching into the adapter internals.
**Trigger:** When the first production tenant hits memory scale (200+ entries per session).

### Hermes-3 local-inference adapter for `LLMProxyPort`
At Stage 9.4.5, `ports/llm_proxy.py` gets built. Natural third adapter slot: RTK = cloud proxy, Claude API = frontier, Hermes-3 (local, llama-based) = cost-optimized for MAC iterations where full-frontier quality isn't required. Single-file adapter (~200 LOC). MIT-licensed model, runs on $5 VPS per Hermes docs.
**Trigger:** After 9.4.5 `LLMProxyPort` contract is ratified.

### Honcho dialectic user modeling → `UserModelPort`
Hermes Agent uses [Honcho](https://github.com/plastic-labs/honcho) to build persistent cross-session user profiles (behavioral patterns, preferences, inferred working style). Verdaca's memory system stores project state but has no equivalent for user behavioral modeling. New port: `UserModelPort` with a Honcho adapter. Small surface — store/retrieve/update user model.
**Trigger:** Stage 10 or when Verdaca ships to external users who return across sessions.

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
**Trigger:** After Stage 9 closes and there's enough session data to mine patterns.

---

## Knowledge Infrastructure

### Wiki auto-update hook
`/verdaca-wiki-update` currently requires manual invocation. Better: PreToolUse or PostToolUse Claude Code hook that detects a new handoff file landing in `knowledge/raw/session-handoffs/` and pings you to run the skill. Requires writing a hook entry in `.claude/settings.local.json`. Zero-LLM-cost detection (file watcher), wiki update still gated by explicit go.
**Trigger:** Any time — low effort addition to `settings.local.json`.

### FTS5 session search
Hermes uses SQLite FTS5 for fast keyword search across past conversation sessions. Current Verdaca approach: grep raw handoff files or read wiki pages. An FTS5 index over `knowledge/raw/session-handoffs/` would make "find the session where we decided X" instant and cheap. SQLite FTS5 is stdlib-adjacent (no external deps). Good fit for a future `knowledge` port adapter.
**Trigger:** When handoff count exceeds ~200 and grep becomes slow.

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
