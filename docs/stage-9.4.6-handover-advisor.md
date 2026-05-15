# Stage 9.4.6 — Advisor Handover

**Predecessor:** `5b7019f` (Stage 9.4.5 RATIFIED close-handoff; 2026-05-12)
**Chain at HEAD:** 24-SHA (target 25+-SHA at 9.4.6 phase landings)
**Authorized advisor model:** Opus 4.7 (1M) max thinking, fixed
**Successor:** Stage 9.4.7 (Repository atomic restructure PR; NOT authorized in this scope)

---

## §1. Stage 9.4.6 scope

Per `docs/pipeline-stage9.md` lines 284–287:

```
- [ ] **9.4.6 — Forge adapter** (~1.5 pw, MEDIUM risk — Rust sidecar, license recheck)
  - [ ] `ports/compaction.py` Protocol
  - [ ] Docker sidecar
  - [ ] License audit: confirm MIT (not GPL, not SSPL)
```

**Substrate distinction from 9.4.5:** Forge is a **Rust sidecar via Docker**, NOT a PyPI library. This re-introduces the Docker-sidecar substrate pattern that 9.4.5 H2-falsified for LiteLLM. Forge is the prototypical Docker-sidecar adapter — the substrate question that retired RTK does NOT retire Forge.

---

## §2. Two BLOCKING gates must clear before 9.4.6 A.1 corrigendum window opens

### G-1: Forge license audit
- **Verify:** Forge license is MIT
- **Reject:** GPL (any variant — copyleft incompatible with Verdaca's product posture), SSPL, AGPL, custom-non-OSI
- **Disposition if non-MIT:** H-class falsification analogous to 9.4.5 H2-rescope — Forge falsified as CompactionPort substrate; substrate analysis re-opens (alternate Rust compaction libraries? Pure-Python implementation? Re-scope CompactionPort to deferred stage?)
- **Source for audit:** Forge upstream `LICENSE` file at the pinned version. Check both repo root LICENSE and any subdirectory LICENSEs for vendored dependencies that might re-license.
- **Standing item from 9.2 architecture:** Forge G-1 was identified as BLOCKING GATE at 9.2 RATIFIED close (per memory `project_verdaca_stage9_2`)

### A.1-JOHN-1 retro-action: Stage 9.1 DTO PINNING audit
- **Scope:** retroactive DTO PINNING audit across Stage 9.1 ports: `memory`, `cost_meter`, `serialization`, `common`
- **Locked at:** A.1 (`de365ff`) per Q-9.4.5-17
- **Question:** are all DTOs in those 4 ports explicitly PINNED in the corresponding ADR's §3 (with §3.6 schema-overlap invariant + §3.7 corrigendum-DTO additions documented)?
- **Disposition options:**
  - **Clean across all 4 ports** → 9.4.6 proceeds normally
  - **Gap discovered in port X** → corrigendum window opens at relevant Stage 9.1.X (e.g., 9.1.2-7 for Memory); 9.4.6 launch blocked until gap closes via DTO PINNING corrigendum

Both gates can run in parallel. Surface for team-lead before launching 9.4.6 sub-charter.

---

## §3. Discipline carry-forward (memory references — load at preload)

These are battle-tested across 9.4.3/9.4.4/9.4.5; all apply to 9.4.6:

| Memory | Purpose |
|---|---|
| `feedback_preload_first_gating` | Force structured preload report + explicit go before drafting |
| `feedback_memory_authorization` | Zero memory writes at executor seat; advisor proposes, awaits explicit go |
| `feedback_go_with_amendments_tracked` | Never silently apply amendments; append ledger verbatim |
| `feedback_provenance_pin` | §provenance table required in env-foundational close memos |
| `feedback_advisor_executor_model_effort` | Advisor=Opus 4.7 max fixed; executor effort set per-task in sub-charter |
| `feedback_session_surface_audit` | Declare session ID/model/JSONL/working-dir at preload |
| `feedback_preload_api_surface_verification` | Verify X's implementation API surface ≥ Y's contract before claiming X is Y's substrate (H2-falsification precedent for Forge substrate fit) |
| `feedback_preload_tracking_status_verification` | Verify cited "binding" doc tracking status at preload |
| `project_verdaca_stage9_4_5` | Sibling-stage ratification state — full 5-phase rollup pattern reference |
| `project_verdaca_stage9_4_4` | 9.4.4 close pattern reference (eccc307 sibling-template lineage) |
| `project_verdaca_stage9_2` | Ports architecture ratification (Forge G-1 gate origin) |

---

## §4. Inherited locked dispositions (carry forward to 9.4.6 Q-slate seed)

- **Q-9.4.5-17 A.1-JOHN-1**: Stage 9.1 DTO PINNING audit prerequisite (above)
- **Q-9.4.5-18 spec-doc version-stamping**: HYBRID stacked-corrigenda-AT-TOP + sectional-cite-INTERNALLY for ports-architecture.md (applies if 9.4.6 needs ports-architecture.md amendments)
- **Q-9.4.5-19 working-tree-drift discipline**: capture F-X-DRIFT-N at H#5 if surfaces; baseline 2 orthogonal `??` (`docs/epam-security-clearance-email-draft.md` + `docs/openclaw-setup-guide.md`)
- **Q-9.4.5-20 sibling-pattern import precedence**: applied at C H#3 for Watch A interpretation refinement; reusable for any line-text vs commit-body discipline tension
- **22-entry no_waiver allow-list**: UNTOUCHED across 9.4.5; zero Compaction-Port entries to seed — establish allow-list scope at 9.4.6 A.1 corrigendum

---

## §5. 7-cosmetic-finding ledger forward-binding

Class-continuity check at 9.4.6 §F-docket if surfaces:

| Class | Watch for at 9.4.6 |
|---|---|
| **Windows tooling cluster** | F-B1-ENCODING-1 (cp1252 encoding) + AM-B.2-1 (path-separator) + AM-C-1 (literal-grep F-token sibling-precedent) + AM-C-2 sub-threshold (PowerShell↔POSIX retry); Forge's Rust sidecar via Docker may surface Docker-on-Windows tooling tensions |
| **Chain canonicity** | F-A1-CHAIN-1 (orthogonal commit absorption); track for any team-lead parallel commits during 9.4.6 cycles |
| **Working-tree drift** | F-A1-DRIFT-1 / F-A1-DRIFT-2 (untracked count mid-cycle); 5 consecutive clean phases at 9.4.5 (A.2/A.3/B.1/B.2/C) — drift events likely to recur, capture per Q-9.4.5-19 |
| **Auth-noise (substrate-specific)** | F-B1-AUTH-NOISE-1 was LiteLLM provider-introspection; Forge sidecar may have analogous startup-latency or version-discovery probes |

---

## §6. Phase structure expectation (modulo Forge-specific H-class refinements)

Mirror 9.4.4/9.4.5 phase pattern (validated across 2 sibling stages):

1. **Phase A.1** — `docs:` corrigendum (--allow-empty if pure docs); ADR-9.1.2-X §3 + §3.6 + §3.7 DTO PINNING; binding amendments lettered (e.g., A.1-WINSTON-N, A.1-MURAT-N, A.1-JOHN-N)
2. **Phase A.2** — `feat:` Protocol port file authoring (`ports/compaction.py` per pipeline 285); DTOs + errors + @runtime_checkable + API_VERSION="1.0.0"
3. **Phase A.3** — Reserved for H-class falsification corrigendum **if** Forge substrate falsifies at B.1 preload (mirror 9.4.5 H2-falsification precedent — if Forge satisfies CompactionPort contract, A.3 may be skipped)
4. **Phase B.1** — `feat:` Forge adapter (`adapters/forge/`); Docker sidecar wiring (distinct from 9.4.5 PyPI library substrate); ~5 DS rulings expected for adapter-side decisions
5. **Phase B.2** — `test:` contract tests (`tests/.../test_compaction_contract.py`); single-adapter MAC-Ts (or dual-adapter if substitute substrate surfaces); Mocking strategy γ inheritance likely
6. **Phase C** — `docs:` close-handoff with pipeline checkbox flip (lines 284–287; 4 lines = parent + 3 children); eccc307/5b7019f sibling-template body shape

**Effort projection:** ~1.5 pw (pipeline header) — but expect drift if H-class falsification triggers or G-1 blocks. Track actual against this in close memo §12.

---

## §7. Watch items to set up at sub-charter time

The Phase C sub-charter for 9.4.5 had Watch items A–L. For 9.4.6, expect:
- **Watch A** F-token discipline (line-text citation-chain vs status-declaration; per Q-9.4.5-20 refined interpretation)
- **Watch B** RETIRED-marker explicitness if any sub-item is rescoped (Forge alternate-substrate H-class falsification precedent)
- **Watch C** N-line scope precision (exact pipeline lines edited)
- **Watch D** Q-9.4.6-* INLINE vs separate-file ADR cite accuracy
- **Watch E** H-class falsification framing if substrate fails (retired-falsified / close-via-rescope language)
- **Watch F** Stage 9.1 retro-action: surface, do NOT execute, in close-handoff (forward-pointer pattern)
- **Watch G** NO Stage 9.4.7 substance creep (atomic restructure PR is separate)
- **Watch H** NO memory writes at executor seat
- **Watch I** Drift surfacing (F-X-CHAIN-N / F-X-DRIFT-N per Q-9.4.5-19)
- **Watch J** Subject within sibling band (~85-95 chars); H-class qualifier for future-search if H-falsification triggers
- **Watch K** Effort rollup numbers match close memo verbatim
- **Watch L** RATIFIED declaration as final substantive line at close-handoff

Adapt at sub-charter authoring time; this is the carry-forward template.

---

## §8. Halt-class boundaries template (15 categories — refine at sub-charter)

Per 9.4.5 Phase C directive §5:
- All other tracked files OUTSIDE 9.4.6 scope: READ-ONLY
- All port files (other than `ports/compaction.py` at A.2): READ-ONLY
- All adapters (other than `adapters/forge/` at B.1): READ-ONLY
- All contract tests (other than `test_compaction_contract.py` at B.2): READ-ONLY
- Substrate (`praxis.kernel.*`): READ-ONLY
- Repo-root pyproject.toml + tests/pyproject.toml + uv.lock: READ-ONLY (Cleo 9.6 territory)
- conftest.py / meta-test / marker-registration / enforcer: READ-ONLY
- Spec docs outside corrigendum window: READ-ONLY
- 22-entry no_waiver allow-list: scope TBD at A.1 (Forge-Port entries may be added or stay deferred-to-9.9)
- Historical commits: IMMUTABLE
- 24-SHA chain at predecessor: APPEND-ONLY → 25+-SHA at HEAD
- 2 baseline orthogonal `??`: PRESERVED VERBATIM
- Memory files: ADVISOR-ONLY at C close
- NO Stage 9.4.7 substance creep
- NO Stage 9.1 retro-action audit EXECUTION (forward-pointer only)

---

## §9. Dispatch posture

When the user authorizes 9.4.6 launch:
1. Verify **both G-1 and A.1-JOHN-1 gates clear** before any A.1 corrigendum substance starts.
2. Author Phase A.1 sub-charter (mirror 9.4.5 sub-charter shape; populate Q-9.4.6-* slate by inspection of ADR-9.1.2-7 or equivalent + ports-architecture.md ADR-9.2-V6 if any).
3. Apply preload-first gating discipline at every halt point.
4. Maintain advisor-as-witness posture; executor authors at H#2 substance design within advisor patterns.

---

## §10. Open questions for team-lead at 9.4.6 launch

1. **G-1 audit timing**: parallel with A.1-JOHN-1, or serial (G-1 first → A.1-JOHN-1 second)?
2. **A.1-JOHN-1 audit format**: in-session work-stream, or separate dedicated audit cycle?
3. **Forge upstream version pin**: latest stable, or specific commit?
4. **Compaction port substitute-adapter**: is there a second compaction library (e.g., zstd-python) for substitute-conformance H1 hedge per 9.4.3 Mem0/Letta dual-adapter precedent? Or is single-adapter post-H1-evaluation acceptable (9.4.4 Pi-Mono / 9.4.5 LiteLLM single-adapter precedent)?
5. **Docker availability on Windows dev environment**: F-B1-ENCODING-1 + AM-B.2-1 + AM-C-1 + AM-C-2 Windows tooling cluster suggests Docker-on-Windows tooling tensions may surface at B.1; preview before launch?

These don't need answers at handover time — surface to user when launching 9.4.6 sub-charter.

---

## §11. Reference paths

- Pipeline: `docs/pipeline-stage9.md` (lines 284–287 are 9.4.6 scope)
- Predecessor commit: `5b7019f` (`git log -1 --format=%B 5b7019f`)
- Sibling close-handoff structural template: `eccc307` (9.4.4) + `5b7019f` (9.4.5)
- Stage 9.4.5 memory: `~/.claude/projects/.../memory/project_verdaca_stage9_4_5.md`
- Stage 9.4.4 memory: `~/.claude/projects/.../memory/project_verdaca_stage9_4_4.md`
- Stage 9.2 architecture memory: `~/.claude/projects/.../memory/project_verdaca_stage9_2.md`
- Verdaca CLAUDE.md: project root
- Knowledge wiki: `knowledge/wiki/verdaca/stage-9-state.md` (if up-to-date)
