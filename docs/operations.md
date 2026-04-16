# PRAXIS OPERATIONS — Gates, Paths, Handoff & Review Protocols

**Purpose:** Operational runbook for the Praxis build pipeline. Contains gate conditions, file path registry, context window handoff protocol, alignment review protocol, and quick references.

**Related docs:**
- [Pipeline Index](pipeline.md) — links to all split documents
- [Pipeline Stages](pipeline-stages.md) — historical build record with all checkboxes
- [Methodology](methodology.md) — agent invocation chain, elicitation framework, model strategy
- [Session Log](session-log.md) — chronological session history

---

## SECTION 5: GATE CONDITIONS (INTERNAL CHECKS)

### Before starting ANY stage, verify:

1. **Previous stage status:**
   - [ ] Previous stage's Winston (architect) output exists at the expected `kernel/<component>/architecture.md`
   - [ ] Previous stage's Murat (test strategy) output exists at `kernel/<component>/test-strategy.md`
   - [ ] Previous stage's Amelia (implementation) output exists in `kernel/<component>/src/`
   - [ ] All Pipeline.md checkboxes for previous stage are `[x]`

2. **Billing mode:**
   - [ ] User confirmed `ANTHROPIC_API_KEY` is unset (CLI/Max billing)
   - [ ] User has Max subscription active

3. **Environment:**
   - [ ] Current working directory is the project root
   - [ ] `.claude/settings.local.json` has `acceptEdits` mode
   - [ ] Agent Teams env var set (if needed for stage)

4. **Reference materials:**
   - [ ] Relevant .txt dump files exist (workspace-only, see File Path Registry below)
   - [ ] Relevant prior stage architecture docs exist

### If ANY gate fails:
- STOP immediately
- Report which gate failed
- Do NOT attempt workarounds
- Wait for user to resolve

---

## SECTION 6: FILE PATH REGISTRY (EVERYTHING IN ONE PLACE)

### Project Root
```
(repo root)
```

### Critical Files at Root
| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project instructions + directory trees (auto-loaded by Claude Code) |
| `claude-setup-reference.md` | Subscription/billing/coordination reference |
| `.claude/settings.local.json` | Permission mode, agent teams, allow/deny lists |

### BMAD Framework (workspace-only — not in repo)
| Path | Purpose |
|------|---------|
| `_bmad/_config/agent-manifest.csv` | 16 BMAD agent definitions (source of truth) |
| `_bmad/core/config.yaml` | user_name, language, output_folder |
| `_bmad/bmm/` | Business/Market/Methodology agents (Mary, Winston, Amelia, etc.) |
| `_bmad/cis/` | Creative Innovation Studio (Carson, Dr. Quinn, Maya, Victor, Sophia, Caravaggio) |
| `_bmad/tea/` | Test Architecture (Murat) |

### Planning Artifacts (workspace-only — not in repo)
| Path | Purpose |
|------|---------|
| `_bmad-output/planning-artifacts/Praxis/` | Praxis project planning docs (legacy location) |
| `_bmad-output/planning-artifacts/src/` | Reference repo .txt dumps + framework analysis |
| `_bmad-output/planning-artifacts/Tokonomics/` | Previous analysis (5 round tables) |

### Praxis Planning Docs
| File | Location | Purpose |
|------|----------|---------|
| `docs/pipeline.md` | **In repo** | Index linking to all split pipeline documents |
| `docs/pipeline-stages.md` | **In repo** | 7-stage build history with all checkboxes |
| `docs/methodology.md` | **In repo** | Agent chain, elicitation, model strategy |
| `docs/operations.md` | **In repo** | THIS FILE — gates, paths, handoff, review |
| `docs/session-log.md` | **In repo** | Historical session log |
| `docs/build-plan.md` | **In repo** | Full 7-stage build plan |
| `docs/box-architecture.md` | **In repo** | 5-layer technical architecture |
| `docs/hybrid-architecture.md` | **In repo** | 8-layer best-of-breed analysis |

### Stage Prompt Files (workspace-only — not in repo)
| File | Purpose |
|------|---------|
| `_bmad-output/planning-artifacts/Praxis/stage-1-winston-prompt.md` | Stage 1 launch prompt |
| `_bmad-output/planning-artifacts/Praxis/stage-2-winston-prompt.md` | Stage 2 launch prompt |
| `_bmad-output/planning-artifacts/Praxis/stage-3-winston-prompt.md` | Stage 3 launch prompt |
| `_bmad-output/planning-artifacts/Praxis/stage-4-winston-prompt.md` | Stage 4 launch prompt |
| `_bmad-output/planning-artifacts/Praxis/stage-4-deferred-findings-brief.md` | Stage 4.1 pre-flight — F-1 + F-3 architectural inputs |
| `_bmad-output/planning-artifacts/Praxis/stage-5-winston-prompt.md` | Stage 5 launch prompt |
| `_bmad-output/planning-artifacts/Praxis/stage-6-winston-prompt.md` | Stage 6 launch prompt |
| `_bmad-output/planning-artifacts/Praxis/stage-7-winston-prompt.md` | Stage 7 launch prompt |

### Reference Repos (workspace-only — not in repo)
Located at `_bmad-output/planning-artifacts/src/`:

| File | Project | Used In Stage |
|------|---------|---------------|
| `badlogic-pi-mono-8a5edab282632443.txt` | Pi-Mono (cost tracker) | Stage 1 |
| `tonl-dev-tonl-8a5edab282632443.txt` | TONL (serialization) | Stage 2 |
| `antinomyhq-forgecode-8a5edab282632443.txt` | Forge (compaction) | Stage 2, 5 |
| `rtk-ai-rtk-8a5edab282632443.txt` | RTK (CLI compression) | Stage 2 |
| `juliusbrussee-caveman-8a5edab282632443.txt` | Caveman (output compression) | Stage 2 |
| `gastownhall-beads-8a5edab282632443.txt` | Beads (versioned state) | Stage 3 |
| `mem0ai-mem0-8a5edab282632443.txt` | Mem0 (hybrid memory) | Stage 3 |
| `robertsfeir-atelier-pipeline-8a5edab282632443.txt` | Atelier (quality gates) | Stages 3, 4, 5 |
| `brainblend-ai-atomic-agents-8a5edab282632443.txt` | Atomic Agents (schemas) | Stage 4 |
| `gastownhall-gastown-8a5edab282632443.txt` | Gas Town (multi-agent) | Stage 4 |
| `badlogic-cchistory-8a5edab282632443.txt` | CCHistory (instruction extraction) | Reference only |

### Reference Analysis Docs (workspace-only — not in repo)
Located at `_bmad-output/planning-artifacts/src/`:

| File | Purpose |
|------|---------|
| `agentic-ai-framework.md` | 8 functional areas framework (Claude Code baseline) |
| `bmad-business-process-mapping.md` | 13 business processes mapped to BMAD agents |
| `project-analysis-classification.md` | Project classification taxonomy |

### Previous Analysis (workspace-only — not in repo)
Located at `_bmad-output/planning-artifacts/Tokonomics/`:

| File | Purpose |
|------|---------|
| `1st_Round_table.md` | Initial strategy (7 agents + 10 research) |
| `2nd_Round_table.md` | Deep strategy sessions (8 agents, 25+ frameworks) |
| `3rd_Round_table.md` | Competitive landscape validation |
| `4th_Round_table.md` | Red team analysis (CRITICAL context) |
| `business_session.md` | GTM, resources, design, brand, pitch |

### Implementation Outputs (in repo)
All implementation work lives under these paths:
```
kernel/
├── pi-mono/            # Stage 1
│   ├── architecture.md       (Winston output)
│   ├── test-strategy.md      (Murat output)
│   └── src/                  (Amelia output)
├── compression/        # Stage 2
│   ├── architecture.md
│   ├── test-strategy.md
│   └── src/
├── memory/             # Stage 3
│   ├── architecture.md
│   ├── test-strategy.md
│   └── src/
├── runtime/            # Stage 4
│   ├── architecture.md
│   ├── test-strategy.md
│   └── src/
├── mac/                # Stage 5
│   ├── architecture.md
│   ├── test-strategy.md
│   └── src/
└── studio/             # Stage 6
    ├── architecture.md
    ├── test-strategy.md
    └── src/

shell/                  # Stage 7
├── architecture.md
├── test-strategy.md
└── api/
```

### Test Outputs
```
(test artifacts colocated with each kernel/<component>/tests/ directory)
```

---

## SECTION 7: CONTEXT WINDOW HANDOFF PROTOCOL

When your Claude session approaches 180k tokens (out of 200k), prepare for handoff to a fresh session.

### Handoff Procedure (at 180k context)

1. **Save current state to Pipeline.md:**
   - Update Status Tracker with latest checkboxes
   - Add a note in the "Session Log" section with timestamp and summary
   - Write Pipeline.md back to disk

2. **Create a handoff summary file:**
   - Path: `_bmad-output/planning-artifacts/Praxis/session-handoff-<timestamp>.md`
   - Content:
     - What was worked on in this session
     - What's the NEXT immediate action
     - Any blockers or open questions
     - Any temporary state that isn't in a permanent file yet

3. **Tell the user:**
   > "Context approaching limit. I've updated Pipeline.md and created session-handoff-<timestamp>.md. To continue in a fresh session:
   > 1. Start new Claude Code session (`claude`)
   > 2. Attach `Pipeline.md` + `session-handoff-<timestamp>.md` + the current stage prompt file
   > 3. I'll resume from where we left off."

### Fresh Session Resume Procedure

When starting a new session with attached Pipeline.md:

1. Read Pipeline.md (Section 1: Bootstrap)
2. Read the attached session-handoff file (if any)
3. Read the attached stage prompt file
4. Verify gate conditions for the current stage
5. Report to user: "Resuming at Stage N, Step X.Y. Previous step was [summary]. Next action: [next step]."
6. Wait for user confirmation before proceeding

---

## SECTION 8: ALIGNMENT REVIEW PROTOCOL

After each stage completes (before starting the next), run this alignment check:

### Alignment Check Prompt Template

Use this in a FRESH Claude subagent (not the main session) to get an independent review:

```
Perform an alignment review for Praxis Stage N.

Read these architecture docs in order:
- kernel/pi-mono/architecture.md (S1)
- kernel/compression/architecture.md (S2, if exists)
- kernel/memory/architecture.md (S3, if exists)
- kernel/runtime/architecture.md (S4, if exists)
- kernel/mac/architecture.md (S5, if exists)
- kernel/studio/architecture.md (S6, if exists)
- shell/architecture.md (S7, if exists)

Identify inconsistencies across these documents:
1. Data model mismatches (e.g., Stage N uses CostRecord with field X, but Stage N-1 defines it without X)
2. API contract mismatches (e.g., Stage N calls `get_cost()` but Stage N-1 defines `fetch_cost()`)
3. Language/tooling drift (e.g., Stage 2 uses Pydantic v1, Stage 3 uses v2)
4. Dependency version mismatches
5. Error handling pattern inconsistencies
6. Naming convention inconsistencies

Output format:
- Alignment Report with specific file:line_number references
- Severity per issue: CRITICAL / HIGH / MEDIUM / LOW
- Proposed reconciliation for each issue

Do NOT write implementation. Review only.
```

### When Alignment Fails

If alignment review finds CRITICAL or HIGH issues:
1. STOP — do not advance to next stage
2. Return to Winston for the stage that caused the drift
3. Update that stage's architecture to reconcile
4. Re-run affected downstream checks
5. Re-run alignment review until clean

---

## SECTION 10: EMERGENCY REFERENCE — "WHERE IS X?" SHORTCUTS

| I need to know... | Find it at... |
|-------------------|---------------|
| Current stage status | [pipeline-stages.md](pipeline-stages.md) Section 3 |
| Current stage prompt | `_bmad-output/planning-artifacts/Praxis/stage-N-winston-prompt.md` (workspace-only) |
| Previous stage architecture | `kernel/<component>/architecture.md` |
| BMAD agent list | `_bmad/_config/agent-manifest.csv` (workspace-only) |
| Build plan context | [build-plan.md](build-plan.md) |
| Technical architecture | [box-architecture.md](box-architecture.md) |
| Reference repo for Stage N | See "Reference Repos" table above |
| Claude setup / billing | `claude-setup-reference.md` (root) |
| Permission config | `.claude/settings.local.json` |
| Previous tokonomics analysis | `_bmad-output/planning-artifacts/Tokonomics/` (workspace-only) |
| Project-wide conventions | `CLAUDE.md` (root, auto-loaded) |

---

## SECTION 11: COMMAND QUICK REFERENCE

### Start a stage
```bash
# In Claude Code, attach files:
#   - docs/pipeline-stages.md (stage history)
#   - Current stage prompt file (e.g., stage-N-winston-prompt.md)
#   - Any session-handoff file if resuming

# Then invoke the architect
/bmad-agent-architect
# Paste the stage prompt content
```

### Check current status (mid-build)
```bash
# Quick status check
cat "docs/pipeline-stages.md" | grep -E "\[[x~! ]\]"

# Check which stages have architecture docs
ls -la "kernel/"
```
