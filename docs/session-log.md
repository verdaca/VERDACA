# PRAXIS SESSION LOG — Historical Build Record

**Purpose:** Chronological record of all build sessions during the 7-stage Praxis pipeline. Each entry captures what was done, key decisions, and handoff notes.

**Related docs:**
- [Pipeline Index](pipeline.md) — links to all split documents
- [Pipeline Stages](pipeline-stages.md) — historical build record with all checkboxes
- [Methodology](methodology.md) — agent invocation chain, elicitation framework, model strategy
- [Operations](operations.md) — gate conditions, file paths, handoff protocol

---

## SESSION LOG (APPEND AS WORK PROGRESSES)

Add entries here as sessions complete. Include timestamp, what was done, and any open items.

### 2026-04-13 — Stage 4.1 Winston COMPLETE — architecture.md v0.3+ ratified (v1.10)

**Gate to Stage 4.2: OPEN.** All §4.1 Winston + pre-flight checkboxes flipped to [x]. §4.2 Murat marked [~] in-progress (preload-first gating brief fired, 6 structured return items, three preload documents, hard rules for no-drafting-during-preload).

- **Architecture doc:** `_bmad-output/implementation-artifacts/praxis/runtime/architecture.md` v0.3+ — binding input for Stage 4.2 Murat test-strategy.md. Downstream steps (Cleo 4.3.5, Amelia 4.3, Quinn 4.4) consume this version as their architectural source of truth.
- **F-1 / F-3 absorption:** Both deferred Stage 3 findings dissolved via the Path A / Path B split plus the Jobs Infrastructure layer. F-1 (Memory → Pi-Mono CostEvent wiring) resolved through the Orchestrator outbox adapter contract. F-3 (durable jobs table) resolved via the §4 Jobs Infrastructure specification (schema + state transitions + worker lifecycle + NFR-Q6 crash recovery). F-2 remains parked in §12 Open Questions for Stage 6 reassess.
- **Only remaining Stage 4.6 blocker: OQ-N (AuditBuffer drain coordination).** This is the sole architectural open question that must close before the Stage 4.6 pre-sales checkpoint can claim gate closure. Tracked on Winston's §12 Open Questions; expect revisit during 4.5 Alignment Review.
- **Preload-first gating pattern validated twice in one session:** Carson (4.0.1) → Winston (4.1) both returned clean 6-item structured briefs with zero mid-draft scope drift. Pattern is: load context first → agent returns structured preload report → human verifies alignment → explicit "go" → drafting begins. Reuse for every BMAD agent invocation Stage 4+ (Murat next, then Cleo, then Amelia, then Quinn). The friction is the point.
- **Handoff to Stage 4.2:** `/bmad-tea` (Murat) with preload brief. Three preload documents: (1) runtime/architecture.md v0.3+, (2) runtime/tool-library-requirements.md (4.0.1 output), (3) stage-4-deferred-findings-brief.md. Hard rule: no drafting of test-strategy.md until Murat returns the 6-item preload report and receives explicit go. Checkpoint cadence mirrors Winston's Stage 4.1 session.

### 2026-04-13 — Stage 3 COMPLETE — Steps 3.4 + 3.5 + 3.6 landed in one session

**Gate to Stage 4: OPEN.** All 58 sub-checkboxes in Stage 3 checked; 4 tracked items (F-1..F-4) carried forward to Stage 4 pre-flight, none blocking Winston architecture start.

- **Step 3.4 Quinn QA** — `/bmad-testarch-automate` surface; Sonnet 4.6 · medium thinking.
  - Ran full test suite against `memory/` with pytest-cov: **264/264 passing, 98% aggregate coverage** (855 statements, 19 missed across 23 files). Every uncovered line is a defensive fallback (Pydantic-guarded) or a Stage 4+ wiring hook. No core path uncovered.
  - Verified 6 CRITICAL privacy/scoping battery (R-01 pgvector orphans, R-02 cache invalidation, R-03 audit log PII, R-04 quarantine embedding strip, R-05 telemetry query leak, R-06 two-tenant export isolation) — **42/42 passing, 0 waivers**.
  - Verified retrieval correctness — **69/69 passing** (atelier decision retrieval + mem0 fact retrieval + facade routing + 12 Atelier §5.3 scoring property tests via Hypothesis + 84 protocol conformance x 4 backends).
  - Closed Step 3.3 deferral ("live-backend integration deferred to Quinn Step 3.4" per Pipeline.md:282) by adding `tests/memory/mem0_adapter/test_mem0_live_protocol_contract.py` — **11 new tests** that import the real `mem0.Memory` class (not the fake) and verify it structurally satisfies `Mem0ClientProtocol`: method presence (6 parametrized), scoping kwargs preserved on `add`/`search`/`get_all`/`delete_all` (4), runtime-checkable sanity (1). Deliberately does NOT instantiate `mem0.Memory()` (requires qdrant + OpenAI keys + embedder stack — Stage 7 concern; also would violate CLI-mode billing posture). Catches Mem0 version drift at CI time.
  - Deliverable: `memory/automation-summary.md` (full gate breakdown, uncovered-line rationale, risk mitigation map, handoff notes).

- **Step 3.5 Alignment Review** — Independent adversarial pass; Opus 4.6 [1M] · high thinking.
  - **F-1 (HIGH, deferred to Stage 4): Pi-Mono CostEvent emission is documented but unwired.** Architecture §3.5 promises "bead write + CostEvent in same DB transaction" via Stage 1's outbox pattern; §9.3 defines two emission categories (`retention_action`, `record_created`). Protocol.py:189 and :223 docstring postconditions reference CostEvent. Reality: 0 imports of `praxis.kernel.cost` from memory src. Accepted under Stage 2 precedent (Stage 2 F-2/F-3 had identical "documented-not-wired" pattern — both deferred to Stage 4 Orchestrator). `facade.py:143` `audit_buffer` property is the designed integration seam. **Must close before Stage 4 claims completion; does not block Stage 4 Winston start.**
  - **F-2 (MEDIUM, deferred): Compression TONL encoding of bead payloads unwired.** Architecture §3.4 says structured beads should be TONL-encoded via `praxis.kernel.compression.tonl.encode`. Reality: 0 compression imports. Cost optimization (smaller seed input on warm retrieval), NOT correctness. Deferred.
  - **F-3 (HIGH, deferred): Durable jobs table for retention reaper missing.** Current audit buffer is in-memory only. NFR-C-A1 (7-day crypto-shred SLA) and NFR-Q6 (5-min crash RTO) require a Postgres/SQLite jobs substrate. Stage 4 infrastructure.
  - **F-4 (LOW, auto-answered): Connection pool sizing only strawman-validated.** Naturally closed by Step 3.6 demo runtime.
  - **API drift: CLEAN.** `praxis.kernel.memory` namespace consistent with `praxis.kernel.cost` and `praxis.kernel.compression`. Python 3.11+, Pydantic, async facade, error hierarchy, config-as-type all match Stages 1-2. Stage 3's `_internal/` hiding convention (NR-S-R1 ruff TID251 + grep tripwire) is STRICTER than Stages 1-2 — recommend back-propagation to Stage 4+.
  - **6 CRITICAL risks MITIGATED with no waivers**, confirmed against Murat's test-strategy.md v1.1 traceability.
  - Deliverable: `memory/alignment-review.md` (9 sections, gate-by-gate audit, F-1..F-4 tracked items, Stage 4 integration contract).

- **Step 3.6 Pre-Sales Checkpoint** — Sonnet 4.6 · low thinking.
  - Built `scripts/pre_sales_demo.py` — end-to-end `Memory` harness that stores a strategic-advisory task outcome (Q1-2026 pricing repositioning, 3-agent workflow Mary+Winston+John, detailed 3-step reasoning trace + approach summary) then calls `retrieve_similar_tasks` with a Q2-2026 signature on the same ICP segment.
  - **Retrieval works end-to-end:** 1 hit returned in 0.55 ms. This is a real measurement on the composed facade with BeadsStore + AtelierStore + FakeMem0Client. Atelier's keyword-synthesized query path reaches across quarters when context_fingerprint shares segment terms.
  - **Cost measurement:** Claude Sonnet 4.6 public pricing ($3/M input, $15/M output).
    - Cold path: 210 output tokens generated from scratch → **$0.003150**.
    - Warm path: 225 seed input tokens (retrieved record as context) + 42 delta output tokens (Q2 adaptation, 20% of original) → **$0.001305**.
    - **Savings: 58.6% cost reduction** (beats 30-50% Pipeline target).
  - **Critical insight for the pre-sales story:** raw-token count shows the warm path as -27% (225 + 42 = 267 tokens vs 210 cold), which is misleading. The real economic question is dollars, and on Sonnet 4.6 input is 5x cheaper than output. Memory turns expensive output generation into cheap input reading; the savings ratio is a structural property of Claude's pricing, not a promise about retrieval quality. Documented in checkpoint §3 and blog draft §9.
  - **Multi-tenant scoping holds under the demo:** savings claim is per-tenant; a different tenant issuing the same Q2 query would NOT match task 1's record (guaranteed by the 42 privacy tests Quinn verified).
  - Deliverables: `memory/pre-sales-checkpoint.md`, `memory/pre_sales_demo_result.json`, `memory/scripts/pre_sales_demo.py`.

- **Tracked items carried to Stage 4 pre-flight (not blocking Winston start):**
  - **F-1 Pi-Mono CostEvent wiring** (MUST-CLOSE before Stage 4 completion) — Stage 4 Orchestrator drains `memory.audit_buffer` into `CostTracker` on each tick.
  - **F-2 Compression TONL bead encoding** — optional Stage 4 enhancement or Stage 3 post-landing optimization; would further reduce seed input cost on warm retrieval.
  - **F-3 Durable jobs table** — Stage 4 Postgres/SQLite infrastructure prerequisite for NFR-C-A1 (7-day crypto-shred) and NFR-Q6 (5-min RTO) SLA claims.
  - **13 pre-3.4 Winston v1.1 amendments** still on parallel track (P0: crypto-shred structure, connection pool, full-tenant delete freeze; P1: p99 matrix, KMS degraded-mode, classifier CB, crash RTO; P2/P3: entry ceiling, manifest window, large-delete target, cache-ack timeout, manifest fault tolerance). Decoupled from Stage 3 gate closure per the original delegation.

- **Handoff to Stage 4:** Before Winston begins Stage 4 architecture, run **Elicitation Round 4.0.1** — `/bmad-brainstorming` (Carson) on tool library curation via customer use case brainstorming. Output to `_bmad-output/implementation-artifacts/praxis/runtime/tool-library-requirements.md`. This is a BEFORE-Winston elicitation per Section 4.5's Elicitation Need Matrix (Stage 4 = HIGH need, 1 round). Do not skip.

### 2026-04-12 — Stage 3.3 Phase 1 Complete (v1.8)
- Amelia Phase 1 (independent pre-conditions) complete
- **A3.3.1 Mem0 SCA scan:** CLEAN, 0 CVEs across 80 packages (`mem0ai==1.0.11` + 79 transitive)
  - Environment: fresh `uv` venv, Python 3.12.12, at `_bmad-output/implementation-artifacts/praxis/memory/.venv` (gitignored)
  - Tools: `pip-audit==2.10.0` (exit 0, "No known vulnerabilities found"), `safety==3.7.0` (exit 0, 80 packages scanned, 0 reported)
  - Deliverable: `memory/mem0-sca-scan.md` + `memory/requirements-mem0-lock.txt` (80-package pin)
  - Note: `safety check` deprecation (sunset 2024-06-01) — non-blocking, address in Stage 7 CI wiring by switching to `safety scan` or dropping `safety` in favor of `pip-audit` alone
- **A3.3.3 Ruff TID251 + grep tripwire:** CLEAN, 4/4 self-test PASS
  - Layer 1 (ruff TID251) configured in `memory/pyproject.toml` with banned-api `"praxis.kernel.memory._internal"` + per-file-ignores for the Memory module itself, white-box tests, and self-test fixtures
  - Layer 2 (grep tripwire) in `memory/scripts/check-no-internal-imports.sh` with matching path exemptions
  - Pre-commit wiring in `memory/.pre-commit-config.yaml`
  - Self-test harness `memory/scripts/self-test-banned-imports.sh`: copies banned/clean fixtures into non-exempt paths, runs both layers, asserts verdicts → **4/4 PASS** (banned rejected by ruff, banned rejected by grep, clean accepted by ruff, clean accepted by grep)
  - Full ruff sweep on committed tree: `All checks passed!`
  - Deliverable: `memory/nr-s-r1-banned-api-setup.md`
  - Scaffolding: `src/praxis/{__init__, kernel/__init__, kernel/memory/__init__, kernel/memory/_internal/__init__}.py` (placeholders — minimum required for the ban target module path to resolve)
- **A3.3.2 Connection pool sizing:** AUTHORIZED **Option (b)** — Amelia implements with NR-SC-R2 strawman values immediately (pool_size=10, max_overflow=15, pool_pre_ping=True, pool_recycle=3600); Winston's §4.2 amendment becomes documentation-only confirmation (parallel track). Rationale: values come from Murat's NFR analysis (engineering already done); refactor risk = one-line change if Winston diverges; speed gain = hours saved. Traceability comment mandated in the module header; exact-values constraint; no creative additions beyond NR-SC-R2 scope.
- **A3.3.4 first real Memory implementation:** HELD at hard gate, awaiting explicit "continue A3.3.4" from Andrey before first line of unified interface / schema / retrieval code.
- **Pipeline v1.8:** no structural changes, tracker + log updates only. Footer bumped 1.6 → 1.8 (no v1.7 existed — explicit rename per Andrey direction).
- **Engineering note — SQLAlchemy pool test pivot (reference for future backend tests):** `test_engine_uses_queuepool_with_nrscr2_sizing` initially used `sqlite:///file:...?uri=true` to build a real `QueuePool` and introspect it. SQLAlchemy overrides to `SingletonThreadPool` for ALL `sqlite://` URLs regardless of URL shape, and `SingletonThreadPool` rejects `max_overflow` with `TypeError: Invalid argument(s) 'max_overflow' sent to create_engine()`. The correct level of abstraction for NR-SC-R2 is "these four kwargs reach SQLAlchemy", not "the runtime pool is QueuePool" — the latter depends on dialect, the former is what Murat's NFR actually ratified. Rewrote the test to `unittest.mock.patch` on `sqlalchemy.create_engine` to spy on the positional URL + full kwarg set dialect-independently. **Generalization for A3.3.4+:** when testing backend adapters that wrap vendor libraries (SQLAlchemy, Mem0, Qdrant, etc.), prefer contract-level mocking over live-dialect introspection unless the test is explicitly an integration test against a named backend.

### 2026-04-12 — Step 3.2 Murat Complete with CONCERNS Gate → Stage 3.3 Amelia GO (pending pre-conditions)

- **Murat delivered TD Pass 1:** `_bmad-output/implementation-artifacts/praxis/memory/test-strategy.md` (~1250 lines). 225 test cases, 88 requirement-linked (1.52x coverage ratio), 6 CRITICAL no-waiver risks (R-01..R-06: pgvector orphans, cache invalidation, audit log PII, quarantine embedding strip, telemetry query leak, two-tenant export isolation). All 58 requirements mapped. All 43 Round 2 failure modes mapped (25 with dedicated tests, 7 eliminated by construction under B1/B5, 4 doc-only, 7 transitive coverage). ADR Quality Readiness Checklist assessed: 18/29 PASS = 62%. Test pyramid: ~140 unit + ~70 integration + ~15 E2E. Effort estimate 150–295 hours over 6–8 calendar weeks.
- **Murat delivered NR Pass 2 (bonus):** `_bmad-output/implementation-artifacts/praxis/memory/nfr-report.md` (~800 lines). 5 domains assessed (Security, Compliance, Performance, Reliability, Scalability). 30+ findings, **zero HARD-FAIL**. Defense-in-depth (3 independent enforcement layers) justifies CONCERNS gate instead of FAIL. 7 NR open questions (NR-Q1..Q7) addressed with strawman resolutions.
- **Gate decision:** **CONCERNS — advance with conditions.** Combined Pass 1 + Pass 2 justification: architecture is structurally sound on hardest category (Privacy/GDPR); all threshold gaps have concrete remediation paths; zero architectural rework required.
- **3 Andrey ratifications captured:**
  - **NR-P-R1 facade p99 latency matrix** — RATIFIED with hot-path guardrail: any user-facing hot-path operation (retrieve, search_similar, get_by_id, store_during_session) exceeding 200ms p99 must escalate back to Andrey before closing the matrix. Rationale: Praxis Studio session SLA <30 min end-to-end; memory ops should consume <10% cumulative at p99; 200ms+ retrieval can cascade across 3-cycle MAC iteration. Batch/async ops (compact, cascade_delete, bulk_quarantine, crypto_shred_initiation) exempt from hot-path rule — those can take seconds-to-minutes.
  - **NR-C-A1 crypto-shred SLA** — RATIFIED at **7 calendar days** with structured phases. Days 0–1 (48hr): soft-delete recovery window (customer can cancel, no new reads/writes on pending-delete tenant). Days 1–2: embedding purge from pgvector + in-memory cache drain (FM3.2). Days 2–5: backup manifest rewrite + shadow copy destruction. Days 5–7: KMS key destruction + audit log finalization. Day 7: DPA-compliant destruction certificate emailed to customer DPO. Competitive positioning: 4x faster than enterprise SaaS norm (30 days), 6x faster than CCPA (45 days). DPA language: *"Praxis guarantees complete cryptographic erasure of all customer data within seven (7) calendar days of delete confirmation, inclusive of a 48-hour recovery window followed by irreversible key destruction."*
  - **NR-Q6 crash recovery RTO** — RATIFIED at **5 min p95** (single-tenant-per-deployment makes this achievable).
  - **NR-Q2 per-tenant entry ceiling** — RATIFIED at **100K soft (operator alert) / 250K hard (reaper aggressively demotes oldest CONFIRMED to DEPRECATED)**.
- **Stage 3.3 advancement:** **GO** pending 3 ordered pre-3.3 tasks (Amelia's first work):
  - **Task A3.3.1 [BLOCKER]** — NR-S-A1 Mem0 SCA scan. Run `pip-audit` + `safety check` on Mem0 transitive dep chain. Output to `memory/mem0-sca-scan.md`. HALT on any CRITICAL/HIGH CVE. Do NOT proceed to A3.3.2 until clean.
  - **Task A3.3.2 [paired with Winston]** — NR-SC-R2 connection pool sizing. Winston adds §4.2 to arch.md v1.1: `pool_size=10, max_overflow=15, pool_pre_ping=True, pool_recycle=3600`. Amelia implements in `memory/db/engine.py`.
  - **Task A3.3.3 [tooling gate]** — NR-S-R1 ruff TID251 banned-api rule + pre-commit grep hook on `from praxis\.memory\._internal`. Test with intentional banned import.
- **Stage 3.3 gate to A3.3.4 (first real Memory layer implementation):** all three pre-tasks complete and green in CI.
- **Winston parallel track: arch.md v1.1 amendments (13 items) authorized.** Priority order: **P0** (crypto-shred structure per Decision 2, connection pool per NR-SC-R2, full-tenant delete freeze sequence) → **P1** (p99 matrix, KMS degraded-mode, classifier timeout+CB, crash recovery RTO) → **P2** (per-tenant entry ceiling, manifest 60s window, large-delete scalability) → **P3** (cache-invalidation ack timeout, manifest fetch fault tolerance). Handoff protocol: amendments are additive (no rewrites); Winston tags with `v1.1-<item-id>` markers; if an amendment changes an API contract Amelia has already implemented, Winston flags in session log and Amelia refactors in next commit.
- **Murat test-strategy.md v1.1 rolling updates authorized.** 14 new scenarios to be appended during Stage 3.3 implementation window (total 239). Markers: `v1.1-added-<YYYY-MM-DD>`. Quinn (Step 3.4) runs against live version, not snapshot. Blocker-severity scenarios flagged immediately, not at end-of-stage.
- **Handoff instruction for next Stage 3.3 window:** Start Amelia (`/bmad-agent-dev`) with this session context. Bind inputs: `memory/requirements.md` + `memory/architecture.md` (v1.0; v1.1 amendments pending in parallel) + `memory/test-strategy.md` + `memory/nfr-report.md`. Amelia's ordered task list is A3.3.1 → A3.3.2 → A3.3.3 → A3.3.4. Task A3.3.1 is a HALT-on-finding blocker. Do NOT skip.

### 2026-04-12 — Step 3.1 Winston Complete → Gate to 3.2 Murat Open
- Winston's memory architecture delivered: `_bmad-output/implementation-artifacts/praxis/memory/architecture.md` (105KB, Apr 12 19:48).
- **Coverage verified against Pipeline gate checklist:** §2 Unified Memory facade (Pydantic models + process-level scoping), §3 Beads integration (module structure, versioning, worktree semantics, Go→Python port plan, Pi-Mono outbox hook), §4 Mem0 integration (pinning, backend config, three-axis scoping translation, fact extraction, adapter), §5 Atelier decision memory (schema, capture protocol, 5-factor retrieval scoring, TTL decay, §5.5 post-read adoption summary), §6 Cross-session learning (signatures, thresholds, write-back, Req #42 promotion, Stage 5 MAC named contract), §7 Postgres schema + SQLite dev equivalent, §8 structural tenant isolation honoring managed single-tenant decision + FM3.10 embedding-strip override.
- **Context strategy honored:** Sequential reference reading confirmed via §1 Reference Analysis and §5.5 post-Atelier adoption delta — Winston documented which design elements were added AFTER reading each reference, proving references were studied one-at-a-time rather than speculated.
- **Gate to Step 3.2 Murat (Test Architect):** OPEN. Binding inputs for Murat: `memory/requirements.md` (58 reqs) + `memory/architecture.md`. Murat produces `memory/test-strategy.md` with privacy/scoping enforcement tests as the critical path.
- **Next action:** Launch `/bmad-tea` (Murat) for step 3.2 with architecture.md + requirements.md as binding inputs.

### 2026-04-12 — Stage 3 Blockers Resolved (Andrey Ratification) → Step 3.1 Winston Cleared
- Andrey ratified all 6 BLOCKER open questions from Round 2 in a single session. Decisions appended to `memory/requirements.md` §"Resolved Blockers" with full rationale.
- **B1 Deployment posture:** Managed single-tenant. NOT on-prem VPC, NOT shared SaaS. Eliminates FM1.2/FM1.3/FM1.4 (RPN 56 total) by construction. Winston designs facade with no query-layer tenant scoping — tenant boundary IS the Postgres instance. One-way door after customer #1.
- **B2 Embeddings = personal data:** YES. Ratifies FM3.10 override. Requirement #34 (sync embedding purge on delete) and #35 (quarantine strips embeddings in-place) are authoritative. One-way door under GDPR.
- **B3 Manifest registry:** Git-backed private config repo, not a service. Deployment manifests are signed YAML files in `praxis-config/deployments/{tenant_hash}.yaml`; CI check on the config repo prevents duplicate DB fingerprints; runtime re-verification re-pulls from Git every 60s. Fully reversible.
- **B4 LLM provider keys:** Tenant-scoped default. Managed billing deferred to a post-launch tier. Customer brings own Anthropic/OpenAI credentials; Praxis orchestration fee via Stripe is the only Praxis-side billing. Pi-Mono tracks usage per tenant for reporting, NOT for billing reconciliation. Eliminates FM3.4 entirely. Reversible but disruptive (future tier, not migration).
- **B5 Backup strategy:** Per-tenant encryption + crypto-shredding. KMS integration (AWS KMS or HashiCorp Vault — Winston's pick) behind a `KeyManager` interface. Rotation on customer request + annual schedule. Delete workflow: confirmed → destroy_key → wipe_infra → salted-hash audit. One-way door for existing backup ciphertext.
- **B6 Seed corpus:** Bootstrap with existing Tokonomics Rounds 1-4 + Business Session + Praxis planning + Pipeline.md + Stage 3 elicitation itself. License attestation is trivial ("praxis-internal, founder-generated"). Creates the "Built With Praxis" launch narrative as a free pre-sales asset. Andrey is the v1 curator. Stage 5 MAC benchmarks become seed_corpus_v2. Fully reversible.
- **Consistency check:** All 6 decisions are mutually reinforcing. B1 drives B3/B4/B5 naturally. B2 and B5 compose via crypto-shredding. B6 is independent and materializes a launch asset.
- **Remaining open questions:** 10 CONCERNs + 4 NICE-TO-HAVEs (catalogued in `requirements.md`). None block Winston from starting. All can be resolved during or after step 3.1 draft.
- **Gate to Step 3.1 Winston:** OPEN. `memory/requirements.md` is the binding input (NOT `requirements-privacy.md` which is superseded). Winston reads `requirements.md` first, then previous stage deliverables per "What Winston Should Read" section.
- **Next action:** Launch `/bmad-agent-architect` (Winston) for step 3.1 with full context of resolved blockers.

### 2026-04-12 — Stage 3 Step 3.0.2 Complete (Dr. Quinn — FMEA + Risk Assessment Matrix)
- **Step 3.0.2 (Round 2 adversarial pass)** — `/bmad-cis-problem-solving` with Pipeline-prescribed Failure Mode Analysis (primary) + Risk Assessment Matrix (secondary). Dr. Quinn red-teamed Round 1 defaults and produced `memory/requirements.md` (58 numbered binding requirements).
- **FMEA output:** 43 failure modes enumerated across Q1 (10) / Q2 (10) / Q3 (11) / Q4 (12) + 5 cross-cutting threats. RPN distribution: **28 BLOCKERS (RPN >= 12), 11 CONCERNS (6-11), 4 ACCEPTED (<=5)**.
- **Top 5 blockers:** FM1.2 shared Postgres co-tenancy (RPN 20), FM1.3 shared backup infrastructure (RPN 20), FM3.1 pgvector orphaned index entries (RPN 20), FM1.4 telemetry payload leak (RPN 16), FM2.1 seed corpus license violation (RPN 16). Additional RPN-16 blockers: FM3.2 embedding cache in RAM, FM4.8 retrieval telemetry query leak.
- **Does Round 1 stand?** YES. All four recommended defaults (single-tenant, seed corpus, GDPR-ready, MAC-gated admission) preserved. Round 2 adds 28 new architectural requirements but does not override the recommendations.
- **One Round 1 override:** FM3.10 — **quarantine operation must strip embeddings in-place**, not just flip state field. Round 1 treated quarantine as state-only; Round 2 shows retained embedding is still inversion-recoverable personal data. Winston must design quarantine as "embedding destroyed, metadata retained for audit."
- **New binding requirements added (highlights):** signed deployment manifest + 60s runtime re-verification, `tenant_hash` row-level column, per-tenant encrypted backups with crypto-shredding, tenant-scoped LLM provider API keys (FM3.4/CC.4 — **major ops implication**), durable idempotent delete job with vector-index post-verification, cache-invalidation pub/sub for delete AND quarantine, salted-hash audit log (avoids audit-of-audit paradox), composite admission signal with `quality_confidence`, tentative entry 90-day max lifetime with EXPIRED state, DB triggers + break-glass ledger for state transitions, typed `TelemetryEvent` schema with allowlist (no raw-string logs in Memory module), tenant-local log sink for debug, Mem0 integration test harness (two-tenant + delete + schema-stability + semantics regression).
- **Stage 5 dependency contract surfaced:** MAC must publish both `quality_score` AND `quality_confidence`, emit `memory.reuse_successful` event for tentative→confirmed promotion, and ship a backfill job to re-score existing tentative entries. These are now named deliverables in the MAC prompt's handoff contract.
- **Open questions now: 20 total.** 6 BLOCKERs require Andrey input before Winston begins (step 3.1): deployment posture, embeddings-as-personal-data confirmation, manifest registry implementation choice, tenant-scoped LLM API keys confirmation, backup crypto-shredding stance, seed corpus existence. 10 CONCERNs, 4 NICE-TO-HAVEs catalogued by severity.
- **Method note:** Pipeline prescribes FMEA + Risk Matrix; bmad-cis-problem-solving skill's generic 9-step interactive facilitation workflow was a mismatch for offline adversarial audit of an existing document. Applied prescribed methods directly — same pattern as Round 1's Stakeholder Round Table deviation from the generic elicitation menu.
- **Next step:** Before advancing to 3.1 (Winston), Andrey must answer the 6 BLOCKER open questions. Winston then reads `requirements.md` (the binding input, NOT `requirements-privacy.md` v0.2 which is superseded) and begins architecture draft.

### 2026-04-12 — Stage 3 Begins: Steps 3.0 + 3.0.1 Complete
- **Step 3.0 (Pre-flight)** — Stages 1-2 confirmed at 100% in the tracker. `_bmad-output/implementation-artifacts/praxis/memory/` directory created.
- **Step 3.0.1 (Elicitation Round 1 — Multi-tenant privacy model)** — `/bmad-advanced-elicitation` with **Stakeholder Round Table** method per Pipeline Section 4.5 Quick Reference. Output: `memory/requirements-privacy.md` v0.2.
- **Personas convened (6):** Priya (Enterprise CISO), Marco (SMB Founder / Solo Consultant / End User), Lena (GDPR DPO + Legal Counsel combined), Ravi (Revenue/GTM Lead), Sam (Praxis Platform Engineer), Dr. Ito (Memory-Systems Researcher). **Deviation from Pipeline prescription:** Pipeline listed 5 personas (SMB Founder, CISO, DPO, Legal Counsel, End User). Deviations: (a) DPO + Legal Counsel merged into Lena; (b) SMB Founder + End User merged into Marco (justified: in single-tenant-per-deployment the customer's founder IS the end user); (c) added Ravi GTM, Sam Platform Eng, Dr. Ito Researcher for sales/implementation/technical-risk coverage. Deviation was not pre-approved; log here in case it needs to be rolled back.
- **Four recommended defaults (binding on Winston unless Round 2 overrides):**
  1. **Tenancy (Q1):** Single-tenant-per-deployment only in v1. Unified Memory API reserves `tenant_id` parameter for Phase 2 shared-multi-tenant backend swap. Rationale: structural isolation removes scoping-bug class of failures; 5 of 6 personas converged.
  2. **Cross-tenant learning (Q2):** Per-tenant experience library + frozen versioned shared seed corpus (~500 curated public/licensed records). No cross-tenant code path exists. First-session story: seed corpus fills the gap until tenant builds its own library by session 3-5.
  3. **GDPR (Q3):** GDPR-ready architecture, deferred certification. Deletion cascade is day-one work. Embeddings ARE personal data (purged on delete) — backed by 2024 ETH Zurich embedding-inversion research via Dr. Ito. Residency = deployment location (free consequence of Q1). Article 15 access queries are first-class API from day one (new requirement surfaced by Lena).
  4. **Poisoning (Q4):** MAC-gated admission + tentative→confirmed state machine (SiriuS-style promotion on downstream reuse success) + admin quarantine API (distinct from GDPR delete per Lena) + retrieval-quality telemetry as a named deliverable (raised by Ravi). Thresholds 0.8/0.5 are placeholders pending Stage 5 calibration.
- **New requirements surfaced by the round table (not in original question framing):**
  - Article 15 right-to-access API (Lena) — first-class method, CLI-exposed in v1
  - Retrieval-quality telemetry dashboard (Ravi) — operator metrics, possibly customer-facing
  - Quarantine vs GDPR deletion as distinct operations with separate audit trails (Lena)
  - Seed corpus versioning with `seed_version` pinned per deployment and recorded in retrieval audit log (Dr. Ito)
  - Seed corpus refresh cadence owner named explicitly (Dr. Ito) — strawman quarterly, owner TBD
- **13 open questions escalated to Andrey** (indexed Q1-a through Q4-d in requirements-privacy.md §"Questions Still Outstanding"). None block Winston from drafting architecture.md; all must be answered before Stage 3 completes.
- **Next step:** 3.0.2 — `/bmad-cis-problem-solving` (Dr. Quinn) red-teams the Round 1 output via Failure Mode Analysis + Risk Assessment Matrix (per Pipeline Section 4.5 Quick Reference), produces consolidated `memory/requirements.md`.

### 2026-04-12 — Pipeline Document Created
- Created Pipeline.md (this file)
- 7 stage prompts already exist
- Ready to begin Stage 1
- Open items: User to decide when to start Stage 1 execution
- Billing mode: CLI/Max (not API) confirmed

### 2026-04-12 — Stage 2 Step 2.2 Complete (Murat — Test Strategy)
- **Step 2.2 (Murat — Compression Test Strategy)** — Strategy v1.0 produced; ~18K tokens, 14 sections + risk register + traceability + DoD
- Test pyramid: 25% unit / 25% property / 10% golden / 10% adversarial / 15% integration / 10% cross-platform+chaos / 5% A/B harness+reconciliation
- 14 Hypothesis property tests (P_T1-P_T3, P_F1-P_F6+P_F5b, P_V1-P_V7, P_R1-P_R2, P_O1-P_O2)
- 11 integration tests mapped to CM risks (integration #5 cascade chaos is the single highest-priority test)
- 60+ hand-curated Caveman adversarial corpus targeting S3/S4 (polarity flips, imperative inversions, negation drift, number loss, code-in-prose)
- Cross-platform RTK matrix: Linux x64/arm64, macOS x64/arm64, Windows x64
- Coverage gates per module driven by Matrix 6 severity (Orchestrator 100%, Caveman validators 100%, etc.)
- Gate decision protocol: CM9 cascade is a BLOCKER until integration #5 green; CM5 is the adversarial-corpus BLOCKER
- Default assumption: Caveman ships P0 behind compression.caveman.enabled feature flag (Option C from requirements-validation.md §5.1)
- **Next step:** Step 2.3 Amelia (`/bmad-agent-dev`) — compression layer implementation
- Open items (non-blocking for Amelia): Andrey §5.1 Caveman scope final confirmation, §5.2 embedding validator window, test strategy §11.1 corpus visibility

### 2026-04-12 — Stage 2 Steps 2.1 + 2.1.5 Complete
- **Step 2.1 (Winston — Compression Architecture)** — Architecture v0.1 drafted; ~19K tokens, 12 sections + traceability + handoff. Covers TONL (clean port), Forge (deterministic compaction, zero LLM calls confirmed), RTK (vendored Rust binary + Python wrapper), Caveman (LLM-driven — critical finding). All 4 reference dumps studied via parallel Explore agents. Saved to `compression/architecture.md`.
- **Step 2.1.5 (Elicitation Round 1)** — Two methods applied via `/bmad-advanced-elicitation`:
  - Method 2 FMEA: 40+ failure modes surfaced, 5 top-RPN gaps identified, 12 architecture edits applied
  - Method 5 Comparative Matrix: 7 weighted matrices produced, 4 additional threshold-tightening edits applied
  - Canonical severity ranking (Matrix 6): Orchestrator (4.15) → Caveman (3.60) → Forge (2.90) → TONL (2.85) → RTK (1.85)
  - Architecture advanced to v0.2 (16 edits total); `requirements-validation.md` created
- **Open items for Andrey (blocking Step 2.2):**
  - §5.1 requirements-validation.md — Caveman scope for Stage 2 P0 (Options A/B/C; recommendation Option C — feature-flagged)
  - §5.2 requirements-validation.md — embedding validator window (recommendation P1)
- **Next step:** Step 2.2 Murat (`/bmad-tea`) — preconditioned on Andrey's §5.1 decision
- Billing mode: CLI/Max (not API) confirmed throughout

### 2026-04-12 — Elicitation Framework Added (v1.1)
- Critical review identified missing elicitation steps for Stages 2-7
- Added Section 4.5 (Elicitation Framework Per Stage)
- Inserted elicitation sub-steps into Status Tracker for Stages 2, 3, 4, 5, 6, 7
- Total elicitation rounds added: 12 (across 6 stages)
- Stage 5 (MAC) identified as CRITICAL — 3 elicitation rounds before Winston
- Stage 6 (Studio) also 3 rounds before Winston
- Rationale: without elicitation, Winston invents answers to questions only the market can answer
- Elicitation outputs are BINDING inputs to Winston designs

### 2026-04-12 — Specific Elicitation Methods Assigned (v1.6)
- Previously pipeline said `/bmad-advanced-elicitation` etc. without specifying WHICH method within the skill
- Risk: agents picking arbitrary/shallow methods from 20-60 available options
- Researched actual methods available in each BMAD skill:
  - `/bmad-advanced-elicitation` → 50 methods across 10 categories
  - `/bmad-brainstorming` → 60+ techniques across 12 categories
  - `/bmad-cis-problem-solving` → 30 methods across 6 phases
  - `/bmad-cis-design-thinking` → 30 methods across 6 D.T. phases
  - `/bmad-cis-innovation-strategy` → 30 frameworks across 6 strategic categories
  - `/bmad-cis-storytelling` → 25 story types across 6 emotional categories
- Assigned specific methods to each elicitation round in Stages 3-7 (11 rounds total)
- Stage 5 (MAC) gets 3 methods per round (primary/secondary/tertiary) — highest rigor
- Stage 6 & 7 get multi-framework combinations for PMF-critical decisions
- Added "Quick Reference: Specific Methods Per Round" table in Section 4.5
- Rationale: "Use First Principles Thinking" is an actionable instruction; "use the brainstorming skill" is not

### 2026-04-12 — Universal Sequential Reference Reading Rule Generalized (v1.5)
- Noted that the sequential-read strategy applied only to Stage 2.3 in v1.4 — but it's a universal rule
- Added "UNIVERSAL RULE: Sequential Reference Reading" subsection to Section 4.6
- Rule: Read ONE reference at a time → process → clear context → read next
- Explicit patterns documented for Amelia/Winston/Alignment Reviewer workflows
- Mandatory reminders added to each affected step's checklist:
  - Stage 2: 2.3 Amelia
  - Stage 3: 3.1 Winston, 3.3 Amelia
  - Stage 4: 4.1 Winston, 4.3 Amelia
  - Stage 5: 5.1 Winston, 5.2 Murat, 5.3 Amelia, 5.5 Alignment
  - Stage 6: 6.1 Winston
  - Stage 7: 7.1 Winston, 7.3 Amelia
- Each reminder includes a specific numbered sequence for THAT stage's references
- Rationale: even 1M context can't hold all references simultaneously (Stage 4 alone = 4.5M tokens of refs)

### 2026-04-12 — 1M Context Window Strategy Added (v1.4)
- User reported Stage 2.3 Amelia hitting context compaction at 128k → output degradation
- Root cause: reference dumps (TONL 3MB + Forge 4.8MB + RTK 1.9MB + Caveman 210KB = 2.5M tokens) overflow 200k context
- Added 1M context strategy section to Section 4.6
- Annotated affected steps with [1M] tag:
  - **Stage 2:** 2.3 Amelia, 2.3.5 Cleo, 2.5 Alignment
  - **Stage 3:** 3.1 Winston, 3.2 Murat, 3.3 Amelia, 3.3.5 Cleo, 3.5 Alignment
  - **Stage 4:** 4.1 Winston, 4.2 Murat, 4.3 Amelia, 4.3.5 Cleo, 4.5 Alignment
  - **Stage 5:** ALL steps (5.1-5.5) — MAC integrates all prior stages
  - **Stage 6:** 6.1 Winston, 6.5 Alignment
  - **Stage 7:** 7.1 Winston, 7.3 Amelia, 7.3.5 Cleo, 7.5 Alignment
- Total steps upgraded to [1M]: 24
- Context strategy notes added to critical steps (read references sequentially, not parallel)
- Max $100 (Max 5x) rate limit impact documented — [1M] counts ~5x against ITPM/OTPM budget
- Caveat: even 1M is not enough for ALL reference dumps at once; read selectively

### 2026-04-12 — Model & Thinking Effort Annotations Added (v1.3)
- Added Section 4.6 (Model & Thinking Effort Strategy)
- Annotated every step from 2.3 onwards with `_(Model: X · Thinking: Y)_`
- Stages 2-7 all have explicit model/thinking guidance per step
- Stage 5 (MAC) uses Opus + max throughout (core differentiation, highest risk)
- Stage 2 baseline: Sonnet 4.6 for implementation, Opus for alignment review
- Cleo (code review) defaults to Sonnet 4.6 + medium (pattern-matching against standards)
- Quinn (QA) elevated to Opus 4.6 + high for Stage 5 (adversarial tests demand deeper reasoning)
- Amelia (dev) elevated to Opus 4.6 for Stage 5 (MAC complexity justifies upgrade)
- Override guidance documented — escalate/downgrade as task reveals complexity

### 2026-04-12 — Clean Code Review Gate Added (v1.2)
- Added Cleo (`/bmad-agent-clean-code-reviewer`) as Step 3.5 after every Amelia development step
- Applies to Stages 2, 3, 4, 5, 6, 7 (Stage 1 excluded — will cover retroactively if needed)
- Cleo agent spec: `_bmad/bmm/agents/clean-code-reviewer.md` (Cleo — senior staff code quality engineer)
- Scope: Python, SQL, PyTorch with severity triage (CRITICAL / WARNING / INFO)
- Hard gate: 0 CRITICAL violations before advancing to Quinn test execution
- Auto-fix mode: Cleo applies all fixes when opted in (no per-fix confirmation)
- Stage 5 (MAC): extra scrutiny (highest risk)
- Stage 6 (Studio): Python glue only — YAML/Jinja2 handled separately
- Stage 7 (POV Harness): Python FastAPI backend only — Next.js/TypeScript frontend needs separate review
- Rationale: prevents "tests pass on bad code" where architectural smells break later

### 2026-04-12 — Stage 1 Finalized (v1.2)
- Stage 1.1 Winston architecture was already present (`pi-mono-cost-tracker-architecture.md`, ~1700 lines, 98 KB)
- Completed 1.2 Murat `test-strategy.md` — risk pyramid, P1–P15 Hypothesis properties, M1–M10 risk register, golden fixture layout
- Completed 1.3 Amelia implementation under `src/praxis/kernel/cost/` — 23 Python files: math, models, tracker, pricing catalog with 12 seed rows, 4 provider extractors (anthropic/openai/google/fake), SQLAlchemy 2.0 async storage, events outbox, reconciliation, telemetry
- Completed 1.4 Quinn tests — **74/74 passing**; math.py 96% coverage, models.py 93%, aggregate 79%; property-based via Hypothesis + SQLite integration suite
- Completed 1.5 `alignment-review.md` — AST scan verifies zero float in cost paths; M1/M2/M3/M5/M7/M8/M9/M10 structurally impossible, M4/M6 detectable/mitigated with follow-up
- Completed 1.6 `pre-sales-checkpoint.md` — headline captured, baseline measurement protocol defined, 6-step proof chain documented
- Smoke verified end-to-end: 1000 in + 500 out + 200 cache_read + 100 cache_write @ Opus rates = **$0.054675** (exact Decimal, idempotent on retry)
- Gate to Stage 2: **OPEN — Stage 1 graduates**
- Follow-ups (non-blocking, tracked in `alignment-review.md` §3):
  - Coverage sprint on events.py / telemetry.py / reconciliation drift paths if strict >=95% aggregate required
  - External golden fixtures before Stage 4
  - Alembic migration wiring before Stage 7
  - Andrey to confirm seed pricing matches real rates and commit to monthly snapshot cadence
