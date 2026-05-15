# Stage 9.4.6 — Executor Handover

**Persona:** Amelia (executor)
**Predecessor:** `5b7019f` (Stage 9.4.5 RATIFIED close-handoff; 2026-05-12)
**Chain at HEAD:** 24-SHA at HEAD; target 25+-SHA at 9.4.6 phase landings
**Authorized model:** advisor-set per sub-charter; expect Sonnet 4.6 medium thinking for substance-heavy phases, Opus 4.7 for novel-substance phases (see `feedback_advisor_executor_model_effort`)

---

## §1. Authorization scope (TBD at sub-charter time)

This handover does **not** authorize work. Wait for the advisor's Stage 9.4.6 Phase A.1 sub-charter (or specific phase directive) before launching any halt-cycle.

When directive lands, authorization scope will name **exactly one phase** (e.g., "Phase A.1 only — ADR-9.1.2-7 §3 corrigendum + DTO PINNING for CompactionPort") with explicit halt-class boundaries.

---

## §2. Pre-launch gating reminders

Two prerequisites MUST clear before any 9.4.6 phase A.1 corrigendum substance:
1. **G-1 BLOCKING GATE** — Forge license audit (confirm MIT)
2. **A.1-JOHN-1 PREREQUISITE** — Stage 9.1 DTO PINNING audit (memory, cost_meter, serialization, common)

If executor receives a 9.4.6 directive without either gate cleared, **HALT and surface to advisor** rather than starting preload — gate clearance is the authorization predicate.

---

## §3. 5-halt cycle structure (inherited from 9.4.3/9.4.4/9.4.5)

| Halt | Executor produces | Advisor disposes |
|---|---|---|
| **H#1 — Preload** | Session surface + N preload outputs + Q-slate echoed + cosmetic-immutable lineage echoed + halt-class echoed + verbatim verification of target file lines + subject-line proposal (~85-95 char band) + spec-as-source-of-truth scan | GO / amendments / HALT |
| **H#2 — Substance design** | Full Edit proposal(s) + commit subject + ~140-LOC body draft mirroring sibling skeleton + F-token strip self-audit + section index | GO / amendments |
| **H#3 — Write + verify** | Apply Edit(s) + git diff verification (exact scope) + F-token grep + git status --short | GO to H#4 |
| **H#4 — Commit draft** | Write commit body to `.git/<phase>_COMMIT_MSG.txt` + body section index + pre-authorized commit sequence (7 steps) | GO to execute |
| **H#5 — Close** | C-SHA + log-grep verification + chain count + 1-file diff verification + working-tree state + Phase → CLOSED + (optional) Stage → RATIFIED + hand-back to advisor | Hand-back |

Per `feedback_preload_first_gating`: **no drafting of the target deliverable during preload**. No shortcuts. Preload and draft are separate halt points.

---

## §4. Tooling profile for Forge (substrate-distinct from 9.4.5)

### Rust sidecar via Docker
- Forge is a Rust binary distributed via Docker (NOT a PyPI library like LiteLLM at 9.4.5)
- `adapters/forge/` will contain: `pyproject.toml` + `__init__.py` + `version_pin.py` + `adapter.py` + `changelog.md` + likely a `Dockerfile` or `docker-compose.yml` reference
- Adapter wraps Docker subprocess invocation (or REST API to a running sidecar — substrate detail TBD at B.1 substrate-truth probe)
- Lifecycle: `on_init` likely spins up sidecar OR verifies container availability; `on_shutdown` likely sends shutdown signal

### Substrate-API-surface verification (per `feedback_preload_api_surface_verification`)
Before claiming Forge is CompactionPort substrate, verify at B.1 preload:
- Forge's CLI/API surface ≥ CompactionPort Protocol surface
- Forge supports the compaction algorithm CompactionPort requires (likely lossless deduplication of conversation context)
- Forge's output is parsable/typed to match `CompactionResponse` (or equivalent) DTO
- Forge's error semantics map to CompactionPort error specializations

**Precedent: 9.4.5 H2-falsification.** RTK was assumed to be LLMProxyPort substrate at ADR-9.2-V5; B.1 preload empirical investigation showed RTK is a single-binary compression tool with no chat-completion semantics. H2 falsified; substrate compressed to LiteLLM-only. **If Forge fails analogous substrate-fit probe at B.1 preload, surface as F-9.4.6-FORGE-* class and halt for advisor disposition.**

---

## §5. Inherited Windows-tooling lineage (high-risk class-continuity area)

Verdaca Stage 9.4.5 surfaced 4 Windows-tooling findings (F-B1-ENCODING-1 + AM-B.2-1 + AM-C-1 + AM-C-2 sub-threshold). Forge's Rust+Docker substrate may surface analogous tensions:

### File encoding (F-B1-ENCODING-1 lineage)
- Default Windows encoding: cp1252 (Win-1252)
- Default Python/repo encoding: UTF-8
- **Mitigation:** ALWAYS write scratch scripts/temp files with `encoding="utf-8"` explicit
- **Tracked-file impact threshold:** ZERO. Encoding fix on scratch scripts only; never on committed source.

### Path separators (AM-B.2-1 lineage)
- PYTHONPATH multi-path separator: `:` on Unix, `;` on Windows
- **Mitigation:** PowerShell uses `;`; Bash POSIX uses `:`. Adapt by shell-mode, not by hard-coded literal.
- **For Forge specifically:** Docker volume mounts use `/` even on Windows; ensure container paths are POSIX even when host paths are Windows.

### Shell-tool mode (AM-C-2 sub-threshold lineage)
- PowerShell tool: `Remove-Item`, `Test-Path`, native PS cmdlets
- Bash tool: `rm -f`, `test -f`, POSIX commands
- **Mitigation:** Match tool to shell — if using Bash tool, use POSIX; if using PowerShell tool, use PS cmdlets. Cleanup operations don't need transactionality; one tool is enough.

### Line endings (transient cycle artifact)
- Windows working tree: CRLF
- Repo storage: LF (per `.gitattributes` default)
- `LF will be replaced by CRLF` git warning is benign autoconversion; **no remediation required**
- Track as cycle artifact in close memo IF surfaces 3+ times; otherwise silent.

### Docker-on-Windows specifically (NEW for 9.4.6)
- Docker Desktop on Windows requires Linux containers mode for typical Rust workloads
- WSL2 backend has filesystem-mount overhead — slow if Forge sidecar reads large volumes
- **Pre-B.1 preview probe:** verify Docker availability + Linux-containers mode + Forge image pulls successfully before B.1 phase starts
- **Surface as F-9.4.6-DOCKER-* class** if Docker unavailability blocks substrate-truth probe

---

## §6. F-token discipline (refined at 5b7019f AM-C-1)

### Forbidden in pipeline line text
- F-class **status declarations** as bare claims, e.g., `[x] X wiring — F-9.4.6-Y-01 CLOSED-VIA-RESCOPE`

### Acceptable in pipeline line text
- F-tokens in **citation-chain context**, e.g., `corrigendum closing F-9.4.6-Y-01 at <SHA>` (sibling-precedent: eccc307 line 276 + 5b7019f line 281)
- Per Q-9.4.5-20 sibling-precedence application

### Acceptable in commit body
- F-tokens unrestricted in commit body §F-docket + §3 F-class lifecycle + §provenance + anywhere else (b0c333c / de365ff / 2043563 / 5b7019f precedent)

### Self-audit at H#2 substance design
- Grep proposed line text for F-tokens; classify each hit as status-declaration (REMOVE) or citation-chain (ACCEPT + surface as AM-X-N candidate for advisor disposition)
- Zero matches expected after self-audit

---

## §7. Memory writes: ZERO at executor seat

Per `feedback_memory_authorization`:
- Executor performs **zero** memory writes during halt-cycle
- All memory operations (new files, rewrites, MEMORY.md index updates) happen at advisor seat post-close, under explicit team-lead go
- If memory UPDATE proposal arises during executor work, surface at H#5 hand-back for advisor seat

Precedent: 9.4.5 Phase C executed close-handoff at `5b7019f` with zero memory writes during executor halt-cycle; advisor applied memory update post-close after explicit user `go memory update`.

---

## §8. Halt-class boundaries template (refine at sub-charter)

Inherited from 9.4.5 Phase C directive §5; refine at 9.4.6 sub-charter authoring:

| Category | Disposition |
|---|---|
| Tracked files outside 9.4.6 phase scope | READ-ONLY |
| Port files other than `ports/compaction.py` (at A.2 only) | READ-ONLY |
| Adapters other than `adapters/forge/` (at B.1 only) | READ-ONLY |
| Contract tests other than `test_compaction_contract.py` (at B.2 only) | READ-ONLY |
| Substrate (`praxis.kernel.*`) | READ-ONLY |
| Repo-root pyproject.toml + tests/pyproject.toml + uv.lock | READ-ONLY (Cleo 9.6) |
| conftest.py / meta-test / marker-registration / enforcer | READ-ONLY |
| Spec docs outside corrigendum window | READ-ONLY |
| 22-entry no_waiver allow-list | UNTOUCHED at phase scope; scope set at A.1 |
| Historical commits | IMMUTABLE (no --amend / --no-verify / --no-gpg-sign) |
| 24-SHA chain at predecessor | APPEND-ONLY → 25+-SHA |
| 2 baseline orthogonal `??` | PRESERVED VERBATIM |
| Memory files | ADVISOR-ONLY at C close |
| NO Stage 9.4.7 substance creep | forward-pointer only |
| NO Stage 9.1 retro-action audit execution | forward-pointer only |

---

## §9. 10-item preload artifacts template (H#1)

Mirror 9.4.5 Phase C directive §3 (10-item table). For 9.4.6 generally:

| # | Action | Output expected |
|---|---|---|
| 1 | `git log --oneline -24` (or current chain count) | Chain ends at `5b7019f` (or current predecessor) |
| 2 | `git rev-parse HEAD` | Predecessor SHA matches authorization |
| 3 | `git status --short` | Exactly 2 baseline orthogonal `??` (plus any phase-authorized work-in-progress) |
| 4 | Read target file at relevant line offsets | Verbatim verification + offset confirmation |
| 5 | `git log -1 --format=%B <sibling-SHA>` | Sibling close-handoff body loaded for shape reference |
| 6 | Read predecessor stage memory (`project_verdaca_stage9_4_5.md`) | Current stage state loaded |
| 7 | Glob/grep check on phase-specific tokens | Confirm presence/absence of expected substance |
| 8 | F-class lifecycle verification | Current F-class state confirmed |
| 9 | Spec-as-source-of-truth scan on predecessor directive | Surface gaps (or confirm clean) |
| 10 | Substantive cite check on target lines | Confirm cited dispositions stay accurate |

Customize per phase substance at sub-charter time.

---

## §10. Standing items reference

- **22-entry no_waiver allow-list:** UNTOUCHED across 9.4.5; zero Compaction-Port entries; establish allow-list scope at 9.4.6 A.1 corrigendum
- **6 Letta probes from 9.4.3:** UNTOUCHED (Q-9.4.5-9 OOS); inherit unless phase substance touches Memory port surface
- **`d0a393b` orthogonal substrate v1.0 commit:** captured as F-A1-CHAIN-1 at 9.4.5 A.1; chain canonicity preserved; reference if any team-lead parallel commits land during 9.4.6 cycles

---

## §11. Reference paths

- Pipeline: `docs/pipeline-stage9.md` (lines 284–287 are 9.4.6 scope)
- Predecessor: `git log -1 --format=%B 5b7019f` (Stage 9.4.5 close-handoff body)
- Sibling close-handoff templates: `eccc307` (9.4.4) + `5b7019f` (9.4.5; 17-§ body skeleton with standalone §provenance)
- Stage 9.4.5 memory: `~/.claude/projects/.../memory/project_verdaca_stage9_4_5.md` (full 5-phase rollup + 7-cosmetic-finding ledger + finalized F-class lifecycles + 21-Q slate)
- Stage 9.4.4 memory: `~/.claude/projects/.../memory/project_verdaca_stage9_4_4.md` (Pi-Mono Decimal-formula-parity precedent)
- Verdaca CLAUDE.md: project root (parallelization principles + git workflow + halt-class boundaries discipline)

---

## §12. Dispatch confirmation pattern

When advisor dispatches 9.4.6 Phase A.1 (or later phase):

1. Executor receives directive
2. Executor self-launches Halt-point #1 preload immediately per established dispatch-instruction-conditional pattern (no need to wait for further team-lead go after directive receipt)
3. Surface preload report (a–h items per 9.4.5 §6 template) for advisor disposition
4. Wait for explicit GO before any H#2 substance drafting (preload-first gating discipline is non-negotiable)

End of executor handover. Standing by for advisor sub-charter dispatch.
