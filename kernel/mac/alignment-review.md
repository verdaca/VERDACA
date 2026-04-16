# Praxis Stage 5.5 — MAC Alignment Review

**Author:** Alignment Review agent (Opus 4.6 [1M], max thinking)
**Date:** 2026-04-15
**Binding inputs:** `mac/architecture.md` v0.1, `mac/code-review.md` (Cleo 5.3.5), `mac/quinn-qa-report.md` (Quinn 5.4), `pi-mono/pi-mono-cost-tracker-architecture.md`, `compression/architecture.md`, `memory/architecture.md`, `runtime/architecture.md`, `project_praxis_stage5_3.md`, `project_praxis_stage5_4.md`, `feedback_no_waiver_discipline.md`, `feedback_praxis_stage_gates.md`
**Frozen artifacts touched:** NONE

---

## §1. Executive Summary

**Gate recommendation: GO WITH ONE ANDREY-ONLY DECISION PENDING.**

| Finding class | Count | Severity |
|---|---|---|
| Cross-stage arch-text contradictions | 3 | Non-blocking — MAC impl explicitly acknowledges via local Protocols + "Step 6/Stage 7 rebind" docstrings |
| Cross-stage arch-impl semantic contradictions | 1 | **Latent** — behaviorally irrelevant to 5.6 Pre-Sales Checkpoint; gate-blocks Stage 7 POV Harness wire-up |
| 5 forwarded audit items dispositioned | 4 | Team-lead pre-decisions adopted verbatim (Items 2, 3, 4, 5) |
| Andrey-only audit items | 1 | **OTEL #2/#3 — recommendation produced, Andrey decides** |

**What this means for 5.6 advancement:**

- 5.6 Pre-Sales Checkpoint is a **single-deliberation benchmark** (Praxis MAC vs single-agent on 10 strategic questions). It does NOT exercise the cross-session promotion path or the production Pi-Mono / Compression / Runtime wire-up. Therefore the 4 contradictions identified below do NOT gate-block 5.6.
- The only live blocker is Andrey's OTEL disposition (Item 1). Once Andrey marks disposition (a) / (b) / (c), Pipeline §5.5 can be marked [x] and 5.6 can begin.
- Stage 5.4 test baseline `211 passed, 30 skipped` preserved throughout 5.5 (verified at review start).

**Cross-stage invariant pass:** All 23 ratified decisions honored. Stage 3 Memory schema untouched. Option Y sidecar validated end-to-end. 16-entry `NO_WAIVER_ALLOWLIST` unchanged. No frozen artifact modified during review.

---

## §2. USR Reading Log

Sequential USR read per handoff §3 (8-step strategy):

| Step | Artifact | Line range | Focus | Status |
|---|---|---|---|---|
| 1 | `pi-mono/pi-mono-cost-tracker-architecture.md` | 299-365, 696-866 | `CostTracker.track_cost` + `LLMRequest`/`LLMResponse` contracts | ✓ |
| 2 | `compression/architecture.md` | 129, 482-610, 912-1036 | Facade (`CompressionLayer`) + Forge `CompactionResult.reasoning_preserved` F8 flag | ✓ |
| 3 | `memory/architecture.md` | 174-280, 875-920, 924-993 | `Memory` Protocol facade + named §6.6 MAC contract + frozen `experience_entries` schema | ✓ |
| 4 | `runtime/architecture.md` | 672-1020, 1850-1889, 2234-2332 | `AgentRole`, `_construct_memory_proxy`, bus filter, Runtime→MAC handoff, §9.0 "the punchline" | ✓ |
| 5 | `mac/architecture.md` v0.1 | 619-760, 919-1028, 1034-1172, 1480-1732 | MAC §5.6, §6.3, §7, §8.1 Option Y, §10.1–§10.4 Integration Contracts | ✓ |
| 6 | Cross-stage comparison | working memory | 4 integration-point cross-checks | ✓ |
| 7 | `mac/code-review.md` + `mac/quinn-qa-report.md` + memory entries `project_praxis_stage5_3.md` + `project_praxis_stage5_4.md` | full | Closed-item boundary + 5.5 audit list state | ✓ |
| 8 | `mac/src/praxis/kernel/mac/integrations/*.py` (pi_mono.py, compression.py, memory.py, runtime.py) | full | Impl verification of arch-text claims | ✓ |

**Scratchpad used:** none. Working-memory capacity held all 5 invariant sets during cross-comparison; 1M context window adequate.

**OTEL evidence file read:** `runtime/tests/runtime/tools/test_otel_exporter_mcp_contract.py` lines 1–104 (READ-ONLY, no modifications).

---

## §3. Pi-Mono Alignment (Stage 1 ↔ MAC)

### Invariants extracted (Pi-Mono §4.1–§4.2, §3.3.2–§3.3.3)

- Single public entry point: `CostTracker(storage_url, pricing_snapshot_dir, clock, engine_options, telemetry)` with async `initialize()`/`close()` lifecycle.
- Hot path: `async tracker.track_cost(request: LLMRequest, response: LLMResponse) -> CostRecord` — idempotent by `request_id`, exactly-once `CostRecord` + `CostEvent` emission in same transaction, <1ms amortized.
- `LLMRequest.request_id` invariant (pi-mono §3.3.2:317): `^[0-9A-HJKMNP-TV-Z]{26}$` ULID regex.
- `LLMResponse` invariant (pi-mono §3.3.3): integer token counts only, no Decimal, no cost — "anything from this point in toward the tracker deals in money; anything from here out toward the LLM deals in tokens."

### MAC's integration claim (arch §10.1:1484–1522)

> "The MAC writes a `CostEvent` per cycle via `CostTracker.track_cost(LLMRequest, LLMResponse)` per the Pi-Mono Stage 1 contract… request_id is `f'mac:{cycle_id}:{cycle_phase}:{call_seq}'`."

### Match

- ✓ **Method-level match:** MAC calls `track_cost(request, response)` — signature matches Pi-Mono §4.2.
- ✓ **Atomicity claim:** MAC arch §10.1:1510 correctly anchors the transactional guarantee to Pi-Mono §4.2:739.
- ✗ **`request_id` format (Contradiction C-2):** MAC sets `request_id = "mac:{cycle_id}:{cycle_phase}:{call_seq}"` which does NOT match Pi-Mono's ULID regex. See §9 C-2 below.
- ✗ **`LLMRequest` / `LLMResponse` shape (Contradiction C-3):** MAC's local dataclasses at `mac/src/praxis/kernel/mac/integrations/pi_mono.py:25-47` define a 3-field `LLMRequest` (`request_id`, `model`, `prompt_tokens`) and a 3-field `LLMResponse` (`request_id`, `completion_tokens`, `usd_cost`). Pi-Mono's canonical `LLMRequest` has 11 fields (§3.3.2) including `model_id` (not `model`), and Pi-Mono's `LLMResponse` explicitly prohibits cost fields ("No Decimal fields. No cost. Only integer token counts" §3.3.3:324) — MAC's impl has `usd_cost: float` on the response, directly contradicting this invariant. See §9 C-3 below.

### Behavioral note

MAC's pi_mono.py docstring at `integrations/pi_mono.py:10-11` explicitly acknowledges: *"Production wiring at step 6 or Stage 7 substitutes the real `praxis.kernel.cost.tracker.CostTracker` at construction time."* Both C-2 and C-3 are deferred-integration gaps, NOT behavioral bugs in MAC today (MAC uses its `FakeCostTracker` in tests; the real Pi-Mono wire-up has not happened yet). Gate impact: non-blocking for 5.6 Pre-Sales Checkpoint (which does not measure cost). Stage 7 POV Harness must reconcile before deployment.

---

## §4. Compression Alignment (Stage 2 ↔ MAC)

### Invariants extracted (Compression §3.2, §4.2)

- Public facade: `CompressionLayer(tracker, config)` with `encode_request`/`decode_response`/`rtk.run_command`/`session_stats`. Exported from `praxis.kernel.compression.__init__.py:9-16` along with `CompressionConfig` and `SessionStats`. **Nothing named `Compressor` is exported.**
- Forge sub-module: `Compactor(config=CompactionConfig).compact(conversation) -> CompactionResult` with `reasoning_preserved: bool` field (§3.2.2:485-506).
- F8 semantics (§3.2.5): `reasoning_preserved=False` signals (a) schema drift (sets `reasoning_drift_detected=True` + emits `forge.reasoning.unknown_schema` alert) or (b) extraction failure.

### MAC's integration claim (arch §10.4:1698–1732)

> "The MAC consumes the Compression layer only via the Forge F8 reasoning preservation contract… `from praxis.kernel.compression import Compressor, CompressionPolicy` … calls `Compressor.compact()` and returns `CompressionResult` carrying `reasoning_preserved` and `reasoning_drift_detected`."

### Match

- ✓ **Semantic intent match:** MAC correctly intends to consume the F8 `reasoning_preserved` flag and route it into §5.6 Forge Fallback Handling + §6.3 SQ-7 step-3 R7 penalty.
- ✓ **SQ-7 ordering enforced (ratified decision #4):** MAC arch §5.6:627–638 + §6.3:752–760 specify raw-scores → Req-C caps (using raw R7) → Forge penalty on R7_effective LAST. Worked example at §5.6:633–637 validates the ordering.
- ✓ **F-2 parking:** MAC arch §10.4:1732 correctly parks TONL per Pipeline.md §4.7, with grep-test enforcement from mac/test-strategy.md §11.3.
- ✗ **Class/method/type name drift (Contradiction C-1):** MAC arch imports `Compressor`, `CompressionPolicy`, `CompressionResult` that do NOT exist in `praxis.kernel.compression.__init__.py`. MAC impl at `integrations/compression.py:40-49` works around by declaring a local `CompressorProtocol` requiring method `compact_with_reasoning_preservation(payload: bytes) -> MacCompressionResult` — a method that does NOT exist on Compression's `Compactor` or `CompressionLayer`. See §9 C-1 below.

### Behavioral note

MAC impl's `CompressorProtocol` docstring at `integrations/compression.py:42-45` says: *"Shape of `praxis.kernel.compression.forge.compactor.ForgeCompactor` (or any alternative compressor) that MAC consumes."* The "or any alternative" phrasing acknowledges that no compression-side class currently satisfies this Protocol. MAC uses a fake in tests; Stage 7 wire-up requires either (i) adding `compact_with_reasoning_preservation` to Compression's Forge module as a wrapper that converts its `Compactor.compact(conversation)` signature to MAC's `compact_with_reasoning_preservation(bytes)` signature, or (ii) MAC-side adapter that calls `Compactor.compact()` and translates the `CompactionResult` to `MacCompressionResult`.

---

## §5. Memory Alignment (Stage 3 ↔ MAC)

### Invariants extracted (Memory §2.1, §6.6, §7.1)

- Single `Memory` Protocol facade at `praxis/kernel/memory/facade.py:174-271`. `tenant_id` required first arg. Methods: 3 writes (`store_task_outcome`, `store_decision`, `store_fact`), 3 reads (`retrieve_similar_tasks`, `retrieve_decisions`, `retrieve_facts`), 3 GDPR (`delete`, `export`, `flag_and_quarantine`), 1 `health`.
- `retrieve_similar_tasks(tenant_id, signature, top_k=5, min_similarity=0.75) -> RetrievalResult` with default thresholds per §6.2:875.
- Named MAC contract §6.6:910–918:
  - MAC→Memory: `mac.publish(task_signature, outcome, quality_score, quality_confidence) -> writes admission record` — maps to `store_task_outcome`.
  - MAC→Memory: `mac.reuse_successful(entry_id, downstream_quality_score, downstream_principal) -> Memory processes promotion` (§6.4 TENTATIVE→CONFIRMED).
  - MAC→Memory: `mac.backfill() -> one-time job at first MAC ship; re-scores TENTATIVE entries` (Req #48).
  - Memory→MAC: `memory.retrieve_similar_tasks(...) -> MAC seeds Cycle 1`.
- **Frozen schema invariant (ratified decision 14):** `experience_entries` has 11 columns per §7.1:976-993; no ALTER TABLE, no new migrations under `praxis/kernel/memory/migrations/`.
- **Option Y binding (ratified decision 13):** MAC owns `mac_bootstrap_metadata` in `praxis/kernel/mac/migrations/0001_mac_bootstrap_metadata.py`; FK to `experience_entries(entry_id)`; no modification to Memory schema.

### MAC's integration claim (arch §8.1 + §10.2)

> "The MAC uses the Memory facade exclusively — no `_internal.*` access… bootstrap writes go to `experience_entries` via facade AND to sidecar at same logical write boundary… `MacMemoryAdapter` wraps named MAC contract."

### Match

- ✓ **Facade-only access:** MAC impl `integrations/memory.py:32-33` imports ONLY `BootstrapMetadataStore` (from the MAC-owned migration) and `MemoryFacadeProtocol`. No `_internal.*` reach-through.
- ✓ **Option Y sidecar (ratified decision 13):** Arch §8.1:1056-1072 defines `mac_bootstrap_metadata` with PK = `experience_entry_id CHAR(26) REFERENCES experience_entries(entry_id)`. Migration owned by MAC per §8.1:1057. Verified: CRIT-1 closure at 5.3.5 (Cleo) already confirmed `BootstrapMetadataStore` Protocol extraction across 3 consumer files.
- ✓ **Stage 3 Memory schema FROZEN (ratified decision 14):** Arch §8.1:1048 explicitly ratifies "Option X (direct JSONB column on `experience_entries`) was considered and rejected" — see §13.2 Rejected Alternatives. No new columns, no migrations under `memory/migrations/`.
- ✓ **`retrieve_similar_tasks` default args:** MAC impl at `integrations/memory.py:47-54` matches Memory §6.2:875 defaults (`top_k=5, min_similarity=0.75`).
- ✓ **Reviewer asymmetry preserved:** MAC arch §10.2:1586 correctly states *"MacMemoryAdapter is held by MAC's producer-side code only. Reviewer-side MAC code does NOT take a MacMemoryAdapter — it takes a `ReviewerMemoryProxy` directly from the Spawner."* This honors Runtime §4.1.3 Layer 1.
- ✗ **`reuse_successful` semantic mismatch (Contradiction C-4, LATENT, GATE-BLOCKS STAGE 7):** MAC impl at `integrations/memory.py:99-119` defines `reuse_successful(tenant_id, signature, top_k, min_similarity) -> list[Any]` that calls `Memory.retrieve_similar_tasks(...)`. Memory arch §6.6:914 says `mac.reuse_successful(entry_id, downstream_quality_score, downstream_principal) -> Memory processes promotion` — a TENTATIVE→CONFIRMED promotion trigger, NOT a retrieval call. MAC arch §10.2:1574–1584 has `mark_reuse_successful(tenant_id, entry_id, downstream_quality_score, downstream_principal)` matching the ratified semantics but its body is stubbed `...`. See §9 C-4 below.

### Behavioral note

The Memory §6.4 promotion protocol has no MAC-side caller in the current impl. This is OK for 5.6 Pre-Sales Checkpoint (single-shot benchmark, no cross-session promotion). It is NOT OK for Stage 6 Studio or Stage 7 POV Harness, where repeated deliberations must drive TENTATIVE→CONFIRMED promotion or the learning loop collapses to a cold start each session.

---

## §6. Runtime Alignment (Stage 4 ↔ MAC)

### Invariants extracted (Runtime §4.1.3–§4.1.5, §7.5, §8.5, §9.0–§9.1)

- `AgentRole` enum: `PRODUCER | REVIEWER`, mandatory at spawn (no default, TypeError if omitted per §4.1.5:1014).
- **`_construct_memory_proxy(role, agent_name, spawn_id)` at Runtime §4.1.5:981-1007 — THE single point of proxy creation.** Single grep target `grep "_construct_memory_proxy" praxis/kernel/runtime/` per §4.1.5:1012. No other path exists.
- `ReviewerMemoryProxy` has 2 methods only (`store_decision`, `flag_and_quarantine`); 8 forbidden methods literally not present on the class → `AttributeError` at Python interpreter level (§4.1.4:957 + §9.0:2309 "the punchline").
- `ProducerMemoryProxy` forwards full 10-method surface with per-call tenant cross-check (§4.1.4:907-919).
- Bus filter Layer 2 (§7.5:1873-1889): `_visible_to(event, caller_name, caller_role)` — reviewer never sees events with `sender_role == PRODUCER`. Defense-in-depth with §4.1.3 type-level Layer 1.
- Runtime→MAC handoff §8.5:2234-2261: MAC consumes spawner + registry + MCP adapter + bus + cost attribution + memory proxy construction + jobs. **MAC MUST NOT override** asymmetry enforcement, tool allowlists, or resource budgets.
- MCP pin owned by Runtime pyproject.toml (`mcp>=1.9.0` per team-lead binding correction, §10.3:1593); shape guard `verify_mcp_sdk_shape()` runs at Runtime boot.
- SQ-8 dedup namespace (ratified decision 18): `"mac:"` prefix for all MAC-emitted Path B events.

### MAC's integration claim (arch §7.2, §10.3)

> "The MAC does NOT re-implement asymmetry; it consumes it… Phase Runner calls `spawner.spawn(agent_id, role=AgentRole.PRODUCER/REVIEWER, tenant_id, budget)`… MacRuntimeAdapter inherits MCP pin + shape guard from Runtime… `MacPathBEmitter.DEDUP_PREFIX = 'mac:'`."

### Match

- ✓ **Role dispatch via `AgentRole` enum (ratified decision 15):** MAC impl `integrations/runtime.py:49-64` mirrors Runtime's `AgentRole` locally. Docstring explicitly flags: *"Shape-compatible with `praxis.kernel.runtime.models.AgentRole`. The MAC-local mirror exists so step 3 does not depend on the full Runtime package at import time; step 6 rebinds to the canonical Runtime enum."*
- ✓ **No direct proxy imports:** MAC impl `integrations/runtime.py:11-16` states: *"MAC NEVER directly imports `ProducerMemoryProxy` or `ReviewerMemoryProxy` from `praxis.kernel.runtime.spawner`. The only legal dispatch is through `AgentRole` at `AgentSpawnerProtocol.spawn`. A grep test (`MAC-T-NEG-MCP-PIN-01` plus a static asymmetry grep in step 5) enforces this structurally at collection time."*
- ✓ **Single-point proxy construction invariant (ratified decision 15):** MAC's routing through `AgentRole` at `spawn(...)` means all proxy construction flows through Runtime's `_construct_memory_proxy`. MAC does NOT bypass.
- ✓ **MCP pin inherited (ratified decision — Runtime owns pin):** MAC impl `integrations/runtime.py:190-194` — `verify_mcp_sdk_shape()` is a zero-arg callable passed in at construction. MAC does NOT re-pin. Docstring at line 102-107 explicitly says *"The real Runtime version lives at `praxis.kernel.runtime.mcp_adapter.version_guard.verify_mcp_sdk_shape` and raises `MCPSDKShapeMismatchError`."*
- ✓ **SQ-8 dedup namespace `"mac:"` (ratified decision 18):** MAC impl `integrations/runtime.py:222-257` — `MacPathBEmitter.DEDUP_PREFIX = "mac:"` class constant, grep-locked by step-5 meta test. Format: `f"{DEDUP_PREFIX}{cycle_id}:{event_type}:{seq:05d}"`.
- ✗ **Spawner method name drift (Contradiction C-5):** MAC impl's `AgentSpawnerProtocol.spawn(*, agent_id, role, tenant_id, budget)` does NOT match Runtime's actual exposed entry point (`spawn_subagent(name, role, input_payload)` per Runtime §4.1.1 + `spawn_team` per §4.1.2). See §9 C-5 below.

### Behavioral note

C-5 is structurally equivalent to C-1/C-3: a deferred-integration gap where MAC defines a local Protocol capturing the shape it WANTS and relies on a wire-time adapter at Stage 7. MAC's impl docstring at `integrations/runtime.py:72-76` says: *"Shape of `praxis.kernel.runtime.spawner.spawner.AgentSpawner` that MAC consumes. Only the `spawn` entry point is pinned — MAC must not reach any other surface."* — the Protocol is explicit that it's a stand-in. Non-blocking for 5.6.

### Additional positive alignment observation

Runtime §8.5:2253 says *"What MAC does NOT override: Information asymmetry enforcement… Tool allowlists… Resource budgets."* MAC arch + impl honors all three: asymmetry routed through `AgentRole`, no tool allowlist override anywhere in MAC src, and `ResourceBudget` is imported from `praxis.kernel.mac.budget` (which itself inherits from Runtime §4.3 per MAC arch §5.7:648).

---

## §7. Five Forwarded Audit Item Dispositions

### Item 1 — OTEL provisional entries #2/#3 (Andrey-only)

**Status: RECOMMENDATION PRODUCED (§8 below). Andrey decides. Do not advance to §10 gate statement until Andrey dispositions.**

### Item 2 — Surviving §12.5 SQ-7 citations in `mac/test-strategy.md` v0.3

**Context:** 2 citations at `test-strategy.md` v0.3 lines 541 + 3488. Phase 2 pattern cleanup missed them. Amelia's 5.3 preload Q1 disposition: "accept-as-is with inline comments in implementation." Team-lead pre-decision: (a) ACCEPT.

**Disposition: (a) ACCEPT.**

Rationale: (i) The implementation at `mac/src/` already uses the corrected anchor via docstring comments (verifiable — e.g., `integrations/compression.py:13` cites `mac/architecture.md §5.6 Forge Fallback Handling (behavioral)` + `mac/architecture.md §6.3 SQ-7 ordering`). (ii) The 2 stale citations have zero behavioral impact — they live only in the frozen doc. (iii) A v0.4 patch would cost a Murat round-trip for cosmetic cleanup when the next v0.4 revision is already a candidate for the §17 test-count variance (Quinn 5.4 §8 forward-to-5.5). (iv) Future readers grepping `§12.5 SQ-7` will find the stragglers and this 5.5 report documenting why they stayed.

**Permanent record:** The 2 stale citations at `mac/test-strategy.md` v0.3:541 and v0.3:3488 are ACCEPTED AS-IS for the lifetime of v0.3. Any future v0.4 revision for unrelated reasons may clean them up as a no-cost correction.

### Item 3 — Step 4 rogue `@pytest.mark.no_waiver` incident

**Context:** Amelia added `@pytest.mark.no_waiver` to `test_mac_t_obs_label_reg_02_hard_fail_on_unknown_key` on her own initiative citing arch §12.2 "non-waivable" wording — SECOND recurrence of the Stage 4.3 OTEL pattern. Fix applied 2026-04-14. Lesson logged in `feedback_no_waiver_discipline.md`. Team-lead pre-decision: (a) CLOSE-AS-LESSON.

**Disposition: (a) CLOSE-AS-LESSON.**

Rationale: (i) The fix is applied and the `211 passed, 30 skipped` baseline preserves the remediated state. (ii) Memory-persisted rule `feedback_no_waiver_discipline.md` is durable across sessions and was consulted at the start of this review — "never add `@pytest.mark.no_waiver` on agent initiative; the ratified N-entry allow-list is the sole authority regardless of arch 'non-waivable' wording". (iii) Formalizing as process (b) or strengthening meta-test (c) adds CI surface for a pattern caught twice by manual review; disproportionate to the frequency. (iv) The meta-test at `tests/static/runtime/test_no_waiver_inventory.py` lines 197-205 already hard-fails if the allow-list count deviates from 16; this catches the structural breach even without a git-blame extension.

### Item 4 — Step 4 `parallel_pool.py` scope excursion

**Context:** Amelia added a local `ClockProtocol` to `cycle/parallel_pool.py` as a necessary structural consequence of the authorized `compute_final_scores()` signature evolution in `iteration_controller.py`. Retroactively accepted 2026-04-14 as one-time exception. Team-lead pre-decision: (a) CLOSE.

**Disposition: (a) CLOSE.**

Rationale: (i) Already on record in Stage 5.3 ratification line and `project_praxis_stage5_3.md`. (ii) Behaviorally inert — `FrozenClock` satisfies the Protocol structurally; no runtime behavior change. (iii) Refining the rule (b) would overgeneralize — "necessary structural consequences of an authorized change are in-scope" is the kind of language that accrues edge-case exploitation over time. (iv) Remediation (c) is net-negative — would touch frozen tests. (v) No precedent is set: future Amelia steps must still stop-and-report before cross-file edits beyond the authorized scope.

### Item 5 — Step 5 `testing/fakes/__init__.py` additive-only scope refinement

**Context:** Amelia modified `testing/fakes/__init__.py` to add `FakeProducerProxy`/`FakeReviewerProxy` re-exports under a step-5 "do not touch step-N source files" constraint. Accepted with refinement: additive-only export aggregator changes in `__init__.py` files are permitted. Cleo's 5.3.5 review applied the same rule at step 6 for bootstrap fakes. Team-lead pre-decision: (a) RATIFY.

**Disposition: (a) RATIFY.**

Rationale: (i) The refinement is already in use and was applied consistently at step 6 (Cleo 5.3.5) with clean results — Cleo's CRIT-1 resolution (2026-04-15) used the same additive-only rule for `BootstrapMetadataStore` Protocol extraction. (ii) The rule is narrow and operational: "`__init__.py` aggregator additions that introduce no new logic and modify no existing exports are permitted in future stages without re-opening the step-N source files." (iii) Tightening (b) re-opens unnecessary round-trips; rewriting (c) is premature abstraction.

**Permanent convention (logged here for 5.6 / 6 / 7):** Step-N "do not touch step-N source files" means "do not modify logic, signatures, or existing exports." Additive-only aggregator changes in `__init__.py` files are permitted.

---

## §8. OTEL Audit — Recommendation for Andrey (Andrey-Only Decision)

**Protocol adherence:** Handoff §9 Andrey-only protocol followed. No test modified. No allow-list modified. Below: evidence + recommendation + explicit "Andrey decides" statement.

### Evidence block

**Files:**
- Test file: `_bmad-output/implementation-artifacts/praxis/runtime/tests/runtime/tools/test_otel_exporter_mcp_contract.py`
- Allow-list file: `_bmad-output/implementation-artifacts/praxis/mac/tests/static/runtime/test_no_waiver_inventory.py`

**The two tests at lines 41–58 and 62–77:**

| | Line 41 test | Line 62 test |
|---|---|---|
| Name | `test_otel_exporter_forbidden_field_query_content_raises` | `test_otel_exporter_forbidden_field_embedding_raises` |
| Marks | `@pytest.mark.r53_structural`, `@pytest.mark.no_waiver` | same |
| Body | Constructs `build_telemetry_event(metric_name, metric_type, value, labels, praxis_version, tenant_hash, query_content="this should be rejected")` and asserts `pytest.raises(ValidationError)` | Same shape, substitutes `embedding=[0.1, 0.2, 0.3]` for `query_content` |
| External state | None (pure Pydantic construction) | None |
| Wall-clock / randomness / network | None | None |
| Deterministic? | **YES** — pure validator assertion; will raise `ValidationError` on exactly these inputs, always | **YES** |

**Arch anchors cited by the test file at line 4:** *"Architecture §6.1.8, §9.10, §10.5. S4.R-05 no-waiver."*

- Runtime arch §6.1.8: `otel-exporter-mcp` listed as a P0 launch-binding tool at **Class A blast radius** — the highest structural classification.
- Runtime arch §9.10: "Summary of Structural vs. Trusted Controls" — R53 (the TelemetryEvent forbidden-field enforcement) is classified as a **structural** control.
- Runtime arch §10.5: "Asymmetry Enforcement Metrics" — OTEL exporter is release-blocking per Andrey's specific ask.
- The arch text at line 2-4 of the test file itself declares it "**THE R53 enforcement point**."

**Memory-side binding:** The test at lines 27-37 (`test_otel_exporter_imports_telemetry_event_from_memory`) enforces **is-identity** that `otel_exporter_mcp.TelemetryEvent IS memory.telemetry.TelemetryEvent` — i.e., the OTEL exporter does not redefine its own TelemetryEvent but imports Memory's canonical allow-listed schema. This ties the R53 enforcement directly to Memory §9.1's "Typed `TelemetryEvent` Schema (Typed Allowlist)".

**Allow-list current state:**
```
# tests/static/runtime/test_no_waiver_inventory.py lines 77-80
# --- Entries 2, 3 — Runtime provisional, PENDING AUDIT at 5.5 Alignment Review ---
"tests/runtime/tools/test_otel_exporter_mcp_contract.py::<function at line 41>",  # PENDING AUDIT at 5.5
"tests/runtime/tools/test_otel_exporter_mcp_contract.py::<function at line 62>",  # PENDING AUDIT at 5.5
```

**Commit history context:** Per `project_praxis_stage5_3.md` / `feedback_no_waiver_discipline.md`, Amelia added these markers at Stage 4.3 citing the R53 structural binding. The escalation to "pending audit" was NOT because the tests are non-deterministic — it was because they were added without Pipeline ratification or 4.5 alignment-review documentation. The audit at 5.5 is the ratification ceremony that 4.3 skipped.

### Determinism check against Stage 5.2 Decision 1 criterion

Stage 5.2 Decision 1 (ratified 2026-04-14) established the `no_waiver` discipline: **"deterministic invariants only"**. Both tests:
- Take no external input beyond the test-file literals
- Use no wall-clock, randomness, or network I/O
- Assert on `pytest.raises(ValidationError)` from a pure Pydantic `BaseModel` field validator
- Will raise or not raise *identically on every run*, *on every platform*, *forever*

**They meet the criterion unambiguously.**

### Recommendation

**Andrey, I recommend disposition (a) RATIFY** because both tests are pure Pydantic-validator assertions with zero external state, they enforce the R53 structural privacy invariant (forbidden TelemetryEvent fields `query_content` and `embedding` rejected at construction), Runtime arch §6.1.8 + §9.10 + §10.5 already classify the underlying enforcement as non-waivable Class-A, and the is-identity binding to Memory's canonical `TelemetryEvent` allow-list schema closes the loop with Stage 3 Memory §9.1.

**Concrete action if (a) RATIFY:** Strip the `# PENDING AUDIT at 5.5` trailing comments at lines 79–80 of `test_no_waiver_inventory.py`. Leave the allow-list entries in place. The 16-entry count is preserved. The `<function at line NN>` nodeid format is preserved. No test code changes.

**If (b) STRIP:** Remove `@pytest.mark.no_waiver` decorators from lines 41 and 62 of the test file; remove the 2 entries from `NO_WAIVER_ALLOWLIST` (count drops 16→14); update the meta-test's `assert len(NO_WAIVER_ALLOWLIST) == 16` to `== 14` at line 197; document the cleanup as a 5.5 corrigendum in Pipeline.md. F-13.C1 runtime + MAC entries unchanged. **Note:** This interpretation treats R53 enforcement as important but not `no_waiver`-grade — the tests remain `r53_structural` and still fail CI on violation; only the "cannot be skipped via `--no-waiver` CLI flag" escalation is withdrawn.

**If (c) DEFER:** Keep the provisional tag; move the audit to Stage 7 deployment checkpoint. This is the cheapest option but pushes the same question to Stage 7 where the context will be colder.

**This is your decision — I will not modify the tests or allow-list without your explicit go.**

**Stage 5.5 gate status is blocked on this disposition.** Once you confirm (a), (b), or (c), §10 below records the final gate statement.

---

## §9. Contradictions Found

Five contradictions identified. Listed in order of severity.

### C-1 — Compression arch-text class name drift (arch-text only)

**Files:**
- `mac/architecture.md:1705` — `from praxis.kernel.compression import Compressor, CompressionPolicy`
- `compression/src/praxis/kernel/compression/__init__.py:9-16` — exports `CompressionLayer`, `CompressionConfig`, `SessionStats` (nothing named `Compressor` or `CompressionPolicy`)
- `compression/architecture.md:485` — Forge sub-module uses `Compactor.compact(conversation) -> CompactionResult`, not `Compressor.compact(payload, policy) -> CompressionResult`
- `mac/src/praxis/kernel/mac/integrations/compression.py:40-49` — works around via local `CompressorProtocol` Protocol requiring method `compact_with_reasoning_preservation(payload: bytes) -> MacCompressionResult` — a method NOT present on either `CompressionLayer` or `Compactor`

**Classification:** Arch-text drift acknowledged by MAC impl docstring as deferred-integration gap.

**Reconciliation options:**
1. **(preferred)** Add a new wrapper method `compact_with_reasoning_preservation(payload: bytes) -> CompressionResultCompatible` to `praxis.kernel.compression.forge` at Stage 7 POV Harness wire-up. Requires Murat review but no MAC-side change.
2. Alternative: add a MAC-side adapter that calls Compression's `CompressionLayer.encode_request` + inspects the `Compactor`'s F8 flag and maps to `MacCompressionResult`. Requires MAC-side Stage 7 wire-up.
3. (Not recommended) Author a v0.2 of mac/architecture.md correcting §10.4 class names. Reopens arch; unnecessary for 5.6.

**Owner at wire-up:** Amelia + Winston at Stage 7 POV Harness planning.

**Gate impact:** Non-blocking for 5.6 Pre-Sales Checkpoint. MAC's `FakeCompressor` in tests exercises the full `reasoning_preserved=False` → SQ-7 step-3 path; production wiring happens at Stage 7.

### C-2 — Pi-Mono `request_id` ULID invariant vs. MAC `"mac:"` prefix (arch-text + impl)

**Files:**
- `pi-mono/pi-mono-cost-tracker-architecture.md:317` — *"request_id matches ULID regex (`^[0-9A-HJKMNP-TV-Z]{26}$`)"*
- `mac/architecture.md:1522` — *"request_id field on LLMRequest is set to… `f'mac:{cycle_id}:{cycle_phase}:{call_seq}'`"*
- `mac/src/praxis/kernel/mac/integrations/pi_mono.py:128-145` — `_format_request_id` produces `"mac:..."` strings

**Classification:** Arch-text + impl drift. MAC's local `LLMRequest` dataclass has no ULID validator, so the MAC-side tests pass. Once MAC is wired to the real Pi-Mono `LLMRequest`, any non-ULID `request_id` will be rejected at Pydantic construction time.

**Reconciliation options:**
1. **(preferred)** MAC switches to ULID `request_id` and moves `{cycle_id, cycle_phase, call_seq}` into `LLMRequest.tags` (Pi-Mono §3.3.2 allows up to 32 tag keys, values freeform). This keeps the downstream cost-report join pattern (`tags.cycle_id == cycle_id`) functional and honors the ULID invariant. Requires MAC arch §10.1 v0.2 text correction + impl update.
2. Pi-Mono relaxes the ULID regex to accept a `"mac:"`-prefix escape. Not recommended — ULID is the universal request identity primitive and relaxing it leaks domain-specific patterns into a shared contract.

**Owner at wire-up:** Amelia + Winston at Stage 7 POV Harness planning.

**Gate impact:** Non-blocking for 5.6 (Pre-Sales Checkpoint does not measure cost).

### C-3 — Pi-Mono `LLMRequest` / `LLMResponse` shape drift (arch-text + impl)

**Files:**
- `pi-mono/pi-mono-cost-tracker-architecture.md:299-341` — canonical `LLMRequest` 11 fields (including `model_id`), `LLMResponse` token-counts-only (no Decimal, no cost)
- `mac/src/praxis/kernel/mac/integrations/pi_mono.py:25-47` — MAC-local `LLMRequest` has 3 fields (`request_id`, `model`, `prompt_tokens`), MAC-local `LLMResponse` has `request_id`, `completion_tokens`, `usd_cost: float` — the `usd_cost` field directly violates Pi-Mono §3.3.3:324 *"No Decimal fields. No cost. Only integer token counts."*

**Classification:** Arch-text + impl drift. MAC impl docstring at `integrations/pi_mono.py:10-11` explicitly acknowledges: *"Step 6 rebinds to the Pi-Mono canonical type."*

**Reconciliation options:**
1. **(preferred)** At Stage 7 wire-up, replace MAC's local `LLMRequest` / `LLMResponse` dataclasses with imports from `praxis.kernel.cost.models` (the real Pi-Mono types). Rename `model` → `model_id` in MAC callers. Remove `usd_cost` from `LLMResponse` — cost is computed by `CostTracker.track_cost` internally from the token counts + pricing catalog (Pi-Mono §6).
2. Pi-Mono relaxes its response contract to accept `usd_cost`. Not recommended — violates Pi-Mono's core "tokens in, cost out" invariant that keeps cost math in one place.

**Owner at wire-up:** Amelia + Winston at Stage 7 POV Harness planning.

**Gate impact:** Non-blocking for 5.6.

### C-4 — Memory `mac.reuse_successful` semantic mismatch (arch-text vs. impl, LATENT STAGE-7 GATE-BLOCKER)

**Files:**
- `memory/architecture.md:914` — *"`mac.reuse_successful(entry_id, downstream_quality_score, downstream_principal) → Memory processes promotion`"* (TENTATIVE→CONFIRMED trigger per §6.4)
- `mac/architecture.md:1574-1584` — `MacMemoryAdapter.mark_reuse_successful(tenant_id, entry_id, downstream_quality_score, downstream_principal) -> None` with docstring *"Triggers memory §6.4 tentative→confirmed promotion"* and stubbed body `...`
- `mac/src/praxis/kernel/mac/integrations/memory.py:99-119` — `MacMemoryAdapter.reuse_successful(tenant_id, signature, top_k, min_similarity) -> list[Any]` calls `Memory.retrieve_similar_tasks(...)` — this is a RETRIEVAL call, NOT a promotion trigger

**Classification:** **Arch-impl semantic contradiction.** MAC arch §10.2 specifies one signature matching Memory §6.6; MAC impl delivers a different method with retrieval semantics under the same name. The TENTATIVE→CONFIRMED promotion path has no caller in MAC impl. MAC impl docstring at `integrations/memory.py:10-11` incorrectly summarizes the named contract as *"`mac.reuse_successful(...)` → `Memory.retrieve_similar_tasks(...)` + sidecar lookup"* — which contradicts Memory §6.6:914's actual text.

**Severity classification:** LATENT. Non-blocking for 5.6 Pre-Sales Checkpoint (single-deliberation benchmark, no cross-session promotion). **Gate-blocking for Stage 7 POV Harness** — production deployment needs the learning loop to advance entries from TENTATIVE to CONFIRMED, which currently has no code path.

**Reconciliation options:**
1. **(preferred — Stage 7 scope)** Rename MAC impl's `reuse_successful` to `retrieve_for_cycle1` (matching MAC arch §10.2:1543) and add a new `mark_reuse_successful(tenant_id, entry_id, downstream_quality_score, downstream_principal) -> None` method that routes to Memory's promotion handler. Update MAC impl `integrations/memory.py:10-11` docstring to match Memory §6.6 semantics.
2. MAC impl adds a NEW `mark_reuse_successful` method alongside the existing `reuse_successful` (keeping backward compatibility for MAC's current tests) and the rename is deferred to Stage 8. Less clean but zero risk to 5.3/5.4 test state.
3. (Not recommended) Memory §6.6 is rewritten to match MAC's impl semantics. Memory arch is FROZEN; reopening for text-level semantic reversal is a load-bearing arch change that would require re-ratification.

**Owner:** Amelia + Winston at Stage 7 POV Harness planning.

**Gate impact:**
- For 5.6: **non-blocking.** 5.6 does not exercise promotion.
- For Stage 7: **blocking.** Must be resolved before production deployment.

### C-5 — Runtime spawner method-name drift (arch-text vs. impl)

**Files:**
- `runtime/architecture.md:645, 720` — exposed entry points are `spawn_subagent(name, role, input_payload)` and `spawn_team(roles, …)`
- `mac/architecture.md:984-988, 1625-1643` — calls `spawner.spawn(agent_id, role, tenant_id, budget)`
- `mac/src/praxis/kernel/mac/integrations/runtime.py:72-86` — `AgentSpawnerProtocol.spawn(*, agent_id, role, tenant_id, budget)` — a MAC-local Protocol that Runtime's concrete `AgentSpawner` does NOT directly satisfy

**Classification:** Arch-text + impl drift acknowledged by MAC impl docstring. MAC's `AgentSpawnerProtocol.spawn` signature is narrower than Runtime's concrete `spawn_subagent` + `spawn_team` surface and uses different keyword-arg names.

**Reconciliation options:**
1. **(preferred)** Add a convenience method `AgentSpawner.spawn(*, agent_id, role, tenant_id, budget)` in Runtime at Stage 7 wire-up that internally dispatches to `spawn_subagent` with the appropriate name → `agent_id` remap and a `None` `input_payload` (or threads it from the MAC cycle controller). Requires minor Runtime arch v0.2 note.
2. MAC impl's `MacRuntimeAdapter.spawn_producer` / `spawn_reviewer` are rewired to call `spawn_subagent(name=agent_id, role=role, input_payload=...)` at Stage 7; arch §10.3 text patched.
3. (Not recommended) Runtime arch is rewritten to expose `spawn(...)` as the canonical entry point. Runtime is ratified; re-ratification for cosmetic rename is disproportionate.

**Owner:** Amelia + Winston at Stage 7 POV Harness planning.

**Gate impact:** Non-blocking for 5.6.

---

### Summary of contradictions

| ID | Artifact layer | Blocking 5.6? | Blocking Stage 7? | MAC impl acknowledges? |
|---|---|---|---|---|
| C-1 Compression class name drift | arch-text + impl | No | Yes (wire-time adapter required) | Yes (`integrations/compression.py:42-45` "or any alternative compressor") |
| C-2 Pi-Mono ULID vs "mac:" prefix | arch-text + impl | No | Yes (Pydantic validator will reject) | Yes (`integrations/pi_mono.py:10-11` "Step 6 rebinds") |
| C-3 Pi-Mono `LLMRequest`/`LLMResponse` shape | arch-text + impl | No | Yes (Pydantic validator will reject) | Yes (`integrations/pi_mono.py:10-11` "Step 6 rebinds") |
| C-4 Memory `reuse_successful` semantic mismatch | arch-impl | No | **Yes — promotion path has no caller** | No (impl docstring contradicts Memory §6.6) |
| C-5 Runtime spawner method-name drift | arch-text + impl | No | Yes (concrete spawner does not satisfy Protocol) | Yes (`integrations/runtime.py:72-76` "only the `spawn` entry point is pinned") |

**All 5 are Stage 7 POV Harness debt.** Analogous to Cleo 5.3.5's 5 deferred WARNINGs (W-2/W-3/W-4/W-5/W-7) — known integration gaps with documented remediation paths, flagged but not gate-blocking the intermediate measurement checkpoint.

**Added to the Stage 7 debt ledger** alongside Cleo's 5 WARNINGs. The Stage 7 POV Harness planning step must disposition all 10 items before production deployment.

---

## §10. Gate Statement

### Items satisfied unconditionally

- USR sequential reading of all 5 stage architectures completed (Pi-Mono → Compression → Memory → Runtime → MAC, with 8th step verification against MAC src integrations).
- All 23 ratified decisions honored across the 5 architectures.
- 16-entry `NO_WAIVER_ALLOWLIST` verified unchanged.
- Stage 3 Memory schema verified frozen (no migrations under `praxis/kernel/memory/migrations/`, Option Y sidecar confirmed at `praxis/kernel/mac/migrations/0001_mac_bootstrap_metadata.py`).
- Test suite baseline preserved: `211 passed, 30 skipped in 2.13s` at review start; no artifacts touched during review.
- No frozen artifacts modified (arch.md, test-strategy.md, quality-rubric.md, benchmark-questions.md, src/, tests/, Pipeline.md §5.5 checkbox, memory files).
- 4 of 5 forwarded audit items dispositioned:
  - Item 2 (§12.5 SQ-7 citations): (a) ACCEPT — matches team-lead pre-decision.
  - Item 3 (rogue no_waiver marker incident): (a) CLOSE-AS-LESSON — matches team-lead pre-decision.
  - Item 4 (parallel_pool.py scope excursion): (a) CLOSE — matches team-lead pre-decision.
  - Item 5 (testing/fakes/__init__.py additive-only refinement): (a) RATIFY — matches team-lead pre-decision; convention logged as permanent §7 Item 5.

### Items pending Andrey's decision (BLOCKER to gate close)

- **Item 1 (OTEL provisional entries #2/#3):** Recommendation produced in §8. Andrey dispositions (a) RATIFY, (b) STRIP, or (c) DEFER. Stage 5.5 is **NOT ADVANCED** until this disposition is explicit.

### Items flagged to Stage 7 debt ledger

- Contradictions C-1 through C-5 (§9). Non-blocking for 5.6 Pre-Sales Checkpoint. Added to Stage 7 POV Harness planning scope alongside Cleo's 5 deferred WARNINGs.

### Final statement

**5.5 Alignment Review is READY-TO-PASS, blocked only on Andrey's OTEL disposition.**

Once Andrey confirms (a) / (b) / (c) on Item 1:
1. The 5.5 report is complete as written (no further text changes expected).
2. Pipeline.md §5.5 checkbox `[ ]` → `[x]` — **awaiting team-lead explicit "continue" per `feedback_praxis_stage_gates.md` (never advance stages without explicit go).**
3. Stage 5.6 Pre-Sales Checkpoint opens. Expected scope: 10 benchmark strategic questions, single-agent baseline vs MAC baseline, blind evaluation targeting +15-25% quality headline.

**Deliverable for Stage 7 debt ledger (copy-paste-ready):**

```
Stage 7 POV Harness planning inputs (from 5.3.5 Cleo + 5.5 Alignment Review):
- [5.3.5] W-2 MacTelemetryEmitter._events unbounded list
- [5.3.5] W-3 broad except ValueError in MetaAgentController._build_deliberation_result
- [5.3.5] W-4 synthesized raw_score=max(1,score) in step-6 smoke
- [5.3.5] W-5 hardcoded manufactured_dissent_detected=False
- [5.3.5] W-7 HybridScoringHarness callable fields typed as Any
- [5.5]   C-1 Compression class name drift (Compressor / CompressionPolicy / CompressionResult)
- [5.5]   C-2 Pi-Mono ULID vs "mac:" prefix drift
- [5.5]   C-3 Pi-Mono LLMRequest/LLMResponse shape drift (incl. usd_cost on response)
- [5.5]   C-4 Memory reuse_successful semantic mismatch — promotion path has no caller (BLOCKING for Stage 7)
- [5.5]   C-5 Runtime spawner method-name drift (spawn vs spawn_subagent)
```

**End of Stage 5.5 Alignment Review.**
