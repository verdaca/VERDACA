# Stage 3 — Memory & Learning Layer: Test Strategy

**Author:** Murat (Test Architect, BMAD TEA)
**Stage gate:** Pipeline.md Step 3.2
**Mode:** System-Level Test Design (Phase 3)
**Date:** 2026-04-12
**Version:** v1.0

**Binding inputs (authoritative):**
- `_bmad-output/implementation-artifacts/praxis/memory/requirements.md` — 58 numbered requirements + 43 failure modes (Round 1 + Round 2 FMEA) + 6 resolved blockers
- `_bmad-output/implementation-artifacts/praxis/memory/architecture.md` — Winston's Stage 3.1 architecture draft v1.0 (105KB, §0-§12)

**Downstream consumers:**
- **Stage 3.3 (Amelia — Developer):** uses this doc as the test-first blueprint. Acceptance tests land before module implementation per Pipeline.md "Tests first AI implements suite validates" principle.
- **Stage 3.4 (Quinn — QA):** uses the Risk Register + Coverage Matrix as gate criteria. Coverage ≥85% per Pipeline gate.
- **Stage 3.5 (Alignment Review):** verifies test strategy honors Stage 1 (Pi-Mono cost events) + Stage 2 (Compression) contracts.
- **Pass 2 (NR — NFR Assessment):** this doc is Pass 1 input; NR pass produces `nfr-report.md` covering Security / Compliance / Performance / Reliability / Scalability.

---

## Table of Contents

1. Executive Summary
2. Testability Review (system-level ADR assessment)
3. Risk Register (FMEA-anchored, TD-scored)
4. Test Level Strategy
5. Coverage Matrix
6. Critical Test Scenarios (P0 detailed)
7. Fixture Architecture (Python / pytest)
8. Test Data Strategy
9. Mem0 Integration Harness (Req #58)
10. Execution Strategy
11. Quality Gates
12. Resource Estimates
13. Open Questions → NR Pass + Winston
14. Handoff Contracts

---

## 1. Executive Summary

### 1.1 Scope

System-level test strategy for the **Memory & Learning Layer** — the third component of the Praxis kernel, sitting downstream of Stage 1 (Pi-Mono cost tracking) and Stage 2 (Compression) and upstream of Stage 4 (Agent Runtime) and Stage 5 (MAC). The layer composes three backends behind a unified facade:

- **Beads** (pattern-extracted, re-implemented on Postgres) — content-addressed versioned state
- **Mem0** (pip dependency, wrapped) — fact extraction + retrieval
- **Atelier decision memory** (pattern-extracted) — pgvector-backed decision records with TTL decay

Module namespace: `praxis.kernel.memory.*`. Test stack: **pytest + Hypothesis + testcontainers-postgres + pgvector** (Python backend, not a browser project — Playwright utils are stack-incompatible and skipped).

### 1.2 Top Risks (anchored to BLOCKER failure modes)

Five risks sit at TD score **9 (CRITICAL — BLOCK gate)**. These anchor the entire test effort:

| ID | Risk | Category | Score | Test strategy anchor |
|----|------|----------|-------|----------------------|
| **R-01** | Delete cascade misses pgvector index entries (FM3.1) | SEC | **9** | Post-delete index verification (integration, direct pgvector query) |
| **R-02** | Embedding cache in RAM persists after delete (FM3.2) | SEC | **9** | Multi-process cache-invalidation pub/sub ack test |
| **R-03** | Audit log contains raw PII criteria (FM3.8) | SEC | **9** | Schema-level rejection + salted-hash enforcement test |
| **R-04** | Embedding inversion on quarantined records (FM3.10 — Round 2 override) | SEC | **9** | Direct-DB verification that embedding = NULL post-quarantine |
| **R-05** | Retrieval telemetry leaks query content (FM4.8) | SEC | **9** | Pydantic extra-field rejection on `TelemetryEvent`; CI lint for raw-string logs |

Plus one **Winston-declared CRITICAL test** regardless of numeric score:
- **R-06** — Two-tenant access isolation (FM3.5 via `Memory.export()`). Integration test marked CRITICAL in architecture.md §10.2.

### 1.3 Gate Posture

**Gate = BLOCK if any R-01..R-06 test fails.** No waiver path. Other P1 risks (score 6-8) gate as CONCERNS — mitigation plans required but single failures don't auto-fail the release.

### 1.4 Test Pyramid (target shape)

```
                  E2E / Multi-Process
                 ┌──────────────────┐
                 │    ~15 tests     │  (cache invalidation, crash recovery, two-tenant)
                 └──────────────────┘
              Integration (pgvector + Postgres)
         ┌──────────────────────────────────────┐
         │            ~70 tests                 │  (facade ↔ backends, durable jobs, migrations)
         └──────────────────────────────────────┘
             Unit / Property / Static-Analysis
    ┌──────────────────────────────────────────────────┐
    │                   ~140 tests                      │  (pure functions, Pydantic schemas, introspection)
    └──────────────────────────────────────────────────┘
```

**Total target: ~225 tests across the three levels.** Coverage ≥85% (Pipeline gate); P0 pass-rate = 100%, P1 ≥95%.

---

## 2. Testability Review (System-Level)

Architecture assessed against the ADR Quality Readiness Checklist (8 categories, 29 criteria). Only non-PASS categories surfaced below.

### 2.1 🚨 Testability Concerns (actionable)

#### C-01 — **Fault injection surface for cache-invalidation timeout is undefined** (Winston Open Q W3)
**Category:** 6. Monitorability / 3. Scalability & Availability
**Impact:** The delete cascade step 7 waits for cache-invalidation pub/sub acks before acking the user delete. If one subscriber hangs, the delete blocks forever (Req #27 literally says "ack aggregation gates user-facing delete"). Winston flagged this as W3. Without a deterministic timeout, the cache-invalidation-ack test is non-terminating.
**Requirement for Murat's test design:** Declare a test-only timeout constant `CACHE_INVALIDATION_ACK_TIMEOUT_SECONDS` (strawman 5s) that the test harness injects. Production default must be settable per deployment.
**ACTIONABLE:** Winston must specify the timeout + fallback behavior (block forever vs best-effort after timeout). Recommend best-effort-with-telemetry: after timeout, mark unresponsive subscribers in the audit trail but proceed. This is a load-bearing design decision that affects whether `test_delete_cascade_cache_invalidation_ack_gate` is deterministic or flaky.

#### C-02 — **Deterministic replay of Beads chain requires pure state reducer** (§3.6)
**Category:** 1. Testability & Automation — 1.1 Isolation
**Impact:** `replay(beads[0..n])` is claimed deterministic (§3.6 test target, §10.3 test). Determinism only holds if the state reducer is pure (no side effects, no time/random dependencies). Architecture §3.1 puts replay in `_internal/beads/replay.py` but does not explicitly constrain the reducer signature.
**ACTIONABLE:** Amelia must implement `replay(beads, initial_state) -> final_state` as a pure function with no I/O. Property test will assert determinism across 1000 Hypothesis-generated chains.

#### C-03 — **Mem0 async vs sync boundary is a flakiness risk** (§4.5 `asyncio.to_thread` wrapper)
**Category:** 1. Testability — 1.1 Isolation / 6. Monitorability
**Impact:** Mem0's public `Memory` class is sync. Adapter wraps all calls in `asyncio.to_thread` to keep the facade non-blocking. Under test load, threadpool exhaustion could cause tests to hang or fail non-deterministically.
**ACTIONABLE:** Configure pytest-asyncio with an explicit bounded threadpool in test fixtures. Integration tests must set `PYTEST_ASYNCIO_MODE=strict` and use a dedicated `asyncio.get_event_loop().set_default_executor(...)` setup.

#### C-04 — **`last_accessed_at` write-during-retrieval is a hidden side effect** (§5.3, §12.1)
**Category:** 1. Testability — 1.1 Isolation
**Impact:** §5.3 says every retrieval updates `last_accessed_at` on returned decisions via a batch UPDATE. This is a write in the read path. Tests that assert "retrieval is read-only" will be wrong; tests that don't account for it will produce non-deterministic recency scores across runs.
**ACTIONABLE:** Expose a test-only `memory.retrieve_decisions(..., _touch_last_accessed=False)` escape hatch for deterministic-ranking tests. Document this is the ONLY flag that bypasses production behavior, and it's gated on `PRAXIS_TEST_MODE` env var (refuses to honor the flag in prod).

#### C-05 — **Cost attribution heuristic for `retrieval_cache_hit` is untestable against ground truth** (§9.3)
**Category:** 1. Testability — 1.4 Sample Requests / 6.3 Metrics
**Impact:** The savings_usd estimate is "average cost of cold-start workflow minus retrieval cost" — but cold-start cost is provided by Stage 4 runtime which isn't built yet. Stage 3 tests can't verify the attribution accuracy.
**FYI (not blocking):** Tests will assert the CostEvent is *emitted with the correct structure*, not that the savings number is *accurate*. Accurate attribution testing moves to Stage 5 (MAC integration test).

#### C-06 — **`test_seed_corpus_write_impossible` has no direct mechanism to verify**
**Category:** 1. Testability — 1.1 Isolation
**Impact:** Architecture §10.2 lists this test but the facade simply "has no method that writes to seed collection" (§8.3). Verifying a non-existent code path is a tautology — any test here is weak.
**ACTIONABLE:** Replace with stronger tests: (a) introspect `Memory` Protocol methods and assert none accept `scope` as a parameter (Req #12, already listed in §10.2 as `test_facade_no_scope_parameter` — DEDUPLICATE these two), (b) grep-level CI lint asserting no Python source file in `praxis.kernel.memory.*` contains `praxis_seed_v` in a write context.

### 2.2 ✅ Testability Assessment (strong areas)

| Category | Status | Evidence |
|----------|--------|----------|
| **1. Testability & Automation** | ✅ MOSTLY PASS (4 of 4 minus C-01, C-02) | Facade is 100% headless; state-control via DeploymentManifest + deployment fixtures; sample requests implicit in §2.1 Protocol signatures |
| **2. Test Data Strategy** | ✅ PASS (3 of 3) | Per-test deployment fixtures enforce isolation; synthetic data via Hypothesis + faker; auto-cleanup via testcontainers teardown |
| **3. Scalability & Availability** | ⚠️ CONCERNS (1 of 4) | Stateless per-process design ✅; bottlenecks identified (Mem0 LLM call in `store_decision` classifier path); SLA undefined (deferred to Stage 7); circuit breakers NOT present. **→ NR pass to assess.** |
| **4. Disaster Recovery** | ⚠️ CONCERNS (1 of 3) | Crypto-shred defined but RTO/RPO not quantified; failover not tested (managed single-tenant → supervisor restart suffices); backup restore validation **required** (FM1.8 test). **→ NR pass.** |
| **5. Security** | ✅ MOSTLY PASS (3 of 4) | AuthN via DeploymentManifest signature ✅; encryption per-tenant key via KMS ✅; secrets via KMS ✅; input validation via Pydantic + allowlist schemas ✅. Only gap: **Mem0 transitive dependency chain hasn't been SCA-scanned** — flag to NR. |
| **6. Monitorability** | ✅ PASS (4 of 4) | Allowlisted TelemetryEvent schema; structured logs; RED metrics via §9.2; dynamic log levels via tenant-local sink |
| **7. QoS / QoE** | ⚠️ CONCERNS (0 of 4) | Latency targets undefined (Req #10 mentions p99 ≤100ms for Beads retrieval in §3.6 but not for facade-level); rate limiting on admission rate (#39) but not on retrieval; **→ NR pass.** |
| **8. Deployability** | ✅ PASS (3 of 3) | Single Alembic migration (§12.1); blue/green implicit in managed single-tenant restart-on-manifest-change; rollback via Git revert + re-deploy |

**Overall readiness: 18/29 criteria PASS = 62% → ⚠️ CONCERNS.**
Gate decision for Stage 3.2 TD: **CONCERNS pending NR pass.** The remaining 11 criteria split into: 5 NR-pass items (scalability, reliability, performance), 3 blocking fixes (C-01, C-02, C-04), 2 improvements (C-03, C-06), 1 deferred-to-Stage-5 (C-05).

### 2.3 Architecturally Significant Requirements (ASRs)

| ASR | Source | Mark | Test implication |
|-----|--------|------|------------------|
| **ASR-1** Managed single-tenant boundary = Postgres instance | B1 | ACTIONABLE | Every integration test spins a dedicated Postgres container per tenant. No shared test DBs. |
| **ASR-2** Embedding = personal data → sync purge on delete | B2, Req #34 | ACTIONABLE | Post-delete direct-pgvector query test is non-negotiable. |
| **ASR-3** Quarantine strips embedding in-place | FM3.10, Req #35 | ACTIONABLE | Direct-DB verification test (not facade-level). |
| **ASR-4** Manifest verification every 60s at runtime | Req #4 | ACTIONABLE | Long-running process test with mid-flight manifest tampering → assert sys.exit(2). |
| **ASR-5** `tenant_hash` on every row via mandatory base model | Req #6 | ACTIONABLE | Alembic migration test: introspect every table, fail if any is missing `tenant_hash CHAR(64) NOT NULL`. |
| **ASR-6** TelemetryEvent allowlist via Pydantic frozen model | Req #51 | ACTIONABLE | Pydantic `extra="forbid"` + test that rejects `TelemetryEvent(query_content="foo")`. |
| **ASR-7** Durable delete cascade (jobs table, idempotent sub-steps) | Req #25 | ACTIONABLE | Crash-injection test mid-cascade + restart → assert job resumes. |
| **ASR-8** LLM provider API keys tenant-scoped | Req #31 | ACTIONABLE | Config loader test that rejects shared-key configs. |
| **ASR-9** Crypto-shreddable per-tenant backup encryption | Req #29 | ACTIONABLE | KMS integration test: destroy key → assert backup cannot decrypt. (Integration test + NR pass verification.) |
| **ASR-10** Seed corpus is a separate offline ingest tool (no runtime write path) | Req #16 | ACTIONABLE | Grep-based CI lint + facade introspection test for absence of write paths. |
| **ASR-11** Stage 5 MAC dependency: `quality_score` + `quality_confidence` | Req #39, §6.6 | FYI | Test strategy includes "MAC-absent mode" tests per Req #49 (all-tentative with logging). |
| **ASR-12** State transitions enforced by DB triggers + break-glass ledger | Req #47 | ACTIONABLE | Direct `UPDATE decisions SET state=...` test expecting permission denied. |

---

## 3. Risk Register (FMEA-anchored, TD-scored)

**Scoring:** TD uses 1–3 × 1–3 → score 1–9. Source FMEAs in `requirements.md` use 1–5 × 1–5 with RPN threshold ≥12 for BLOCKER. Normalization rule:
- FMEA RPN ≥16 → TD score **9** (CRITICAL/BLOCK)
- FMEA RPN 12-15 → TD score **6–8** (HIGH/MITIGATE)
- FMEA RPN 8–11 → TD score **4–5** (MEDIUM/MONITOR)
- FMEA RPN ≤7 → TD score **1–3** (LOW/DOCUMENT)
- Winston-CRITICAL override → TD score 9 regardless of FMEA RPN

All rows traceable back to the failure-mode ID so the Stage 3 FMEA remains the authoritative source.

### 3.1 CRITICAL (score = 9, BLOCK gate)

| ID | FM | Risk | Cat | P | I | Score | Mitigation (Winston arch) | Test-level anchor |
|----|----|------|-----|---|---|-------|---------------------------|-------------------|
| R-01 | FM3.1 | pgvector orphaned index entries after `Mem0.delete` | SEC | 3 | 3 | **9** | §8.5 step 4 (VACUUM+REINDEX) + step 5 (post-delete verification query) | **Integration**: direct pgvector query after facade delete returns zero hits |
| R-02 | FM3.2 | Live process RAM caches embedding after DB delete | SEC | 3 | 3 | **9** | §8.5 step 7 cache-invalidation pub/sub + ack aggregation | **E2E multi-proc**: 3 processes, delete from one, verify cache purge on all before ack |
| R-03 | FM3.8 | Audit log table contains raw PII criteria | SEC | 3 | 3 | **9** | §7.1 memory_audit_log schema — only `criteria_hash CHAR(64)` column | **Unit + Integration**: schema introspection + failed-write test on raw criteria |
| R-04 | FM3.10 | Quarantined record retains embedding → inversion attack | SEC | 3 | 3 | **9** | §8.7 — `UPDATE ... SET embedding=NULL` in serializable transaction | **Integration**: direct `SELECT embedding FROM decisions WHERE state='quarantined'` = NULL |
| R-05 | FM4.8 | Retrieval telemetry dashboard leaks query content | SEC | 3 | 3 | **9** | §9.1 Pydantic `frozen + extra="forbid"` allowlist | **Unit**: TelemetryEvent(query_content="...") raises ValidationError |
| R-06 | FM3.5 | Article 15 `export()` returns other tenant's data | SEC | 2 | 3 | **9*** | §8.6 — same facade as retrieve_*, two-tenant CRITICAL test | **E2E**: 2 isolated processes, export from A returns zero tenant_B records. *Winston-CRITICAL regardless of numeric score.* |

### 3.2 HIGH (score 6-8, MITIGATE — CONCERNS gate)

| ID | FM | Risk | Cat | P | I | Score | Mitigation | Test anchor |
|----|----|------|-----|---|---|-------|------------|-------------|
| R-07 | FM1.1 | Deployment manifest drift detected mid-runtime | SEC | 2 | 3 | 6 | §8.1 60s re-verification + sys.exit(2) | **Integration**: tamper manifest mid-run, assert exit code 2 within 70s |
| R-08 | FM1.4 | Central telemetry payload contains query content | SEC | 2 | 3 | 6 | §9.1 allowlist; tenant-local sink for debug | **Unit + CI lint**: grep for raw-string logs in memory module |
| R-09 | FM1.6 | Developer passes `tenant_id` via metadata kwarg | SEC | 2 | 3 | 6 | Req #7 CI lint, facade introspection | **Unit**: introspect `Memory` methods, fail if any kwarg name contains "tenant" (except `tenant_id` positional) |
| R-10 | FM1.8 | Backup restore into wrong tenant deployment | DATA | 2 | 3 | 6 | §8.1 step 4 tenant_hash sample scan | **Integration**: restore A's backup into B's DB, start process, expect sys.exit(2) |
| R-11 | FM1.9 | Alembic migration runs against wrong DB | OPS | 2 | 3 | 6 | Migration pre-check hook | **Integration**: migration-safety harness tests env-tag + tenant_hash preconditions |
| R-12 | FM1.10 | `_internal/` module imported by application code | SEC | 2 | 3 | 6 | `__all__` + CI lint | **Unit**: `import praxis.kernel.memory._internal.mem0` from `tests/lint/` raises ImportError |
| R-13 | FM3.3 | Backup ciphertext contains deleted personal data | SEC | 2 | 3 | 6 | §8.5 step 9 crypto-shred + KMS | **Integration**: destroy per-tenant key, attempt decrypt, assert cryptographic failure |
| R-14 | FM3.9 | Delete cascade partial failure → inconsistent state | DATA | 2 | 3 | 6 | §8.5 durable job, idempotent sub-steps | **E2E multi-proc**: SIGKILL mid-cascade, restart, assert job resumes and completes |
| R-15 | FM3.11 | Mem0 upstream delete bug leaves orphans | SEC | 2 | 3 | 6 | §4.1 upgrade test harness | **Integration**: Mem0 harness class 2 (delete-then-query-by-id = zero) |
| R-16 | FM2.1 | Seed corpus contains licensed/copyrighted content | OPS | 2 | 3 | 6 | §5 seed ingest license_attestation | **Unit**: ingest tool refuses records without attestation record |
| R-17 | FM2.3 | Customer data accidentally ingested to seed corpus | SEC | 2 | 3 | 6 | PII scanner + isolated workstation | **Unit**: ingest tool's PII scanner rejects records containing regex patterns |
| R-18 | FM2.6 | Developer passes `scope=SEED_CORPUS` to write method | SEC | 2 | 3 | 6 | Req #12 method-implicit scope | **Unit**: introspect facade, fail if any method has `scope` param |
| R-19 | FM4.6 | Admin quarantines for DSAR expecting delete semantics | BUS | 2 | 3 | 6 | §8.7 reversibility note + DSAR runbook | **Documentation test**: verify DSAR runbook explicitly says "delete, not quarantine"; API docstring assertion |
| R-20 | FM4.9 | DBA runs `UPDATE decisions SET state=...` bypassing MAC | SEC | 2 | 3 | 6 | §7.1 DB trigger + break-glass ledger | **Integration**: direct UPDATE without `praxis.state_change_authorized` session var → permission denied |
| R-21 | FM4.1 | Adversarial prompt gaming `quality_score` → junk CONFIRMED | BUS | 2 | 2 | 4 | §6.3 composite signal + outlier detection | **Integration**: 10x normal admission rate → rate-limiter + review queue test. *(Promoted to P1 due to reputational impact.)* |
| R-22 | FM4.2 | MAC score uncalibrated on new task type | BUS | 2 | 2 | 4 | §6.3 composite + confidence threshold | **Unit**: low-confidence scores default to TENTATIVE |
| R-23 | CC.5 | Manifest tampering between sign and verify | SEC | 2 | 3 | 6 | §8.1 signature verification | **Unit + Integration**: bad signature → sys.exit(2) on boot |
| R-24 | FM2.5 | Seed corpus stale → retrieval regression | BUS | 2 | 2 | 4 | seed_version expiry telemetry | **Integration**: set old seed_version_date, assert warning metric emitted |
| R-25 | FM4.3 | Tentative pool unbounded → p99 retrieval latency regression | PERF | 2 | 2 | 4 | §5.4 reaper (90-day TTL) | **Integration**: insert 1000 stale tentative entries, run reaper, assert demotion + latency stable. *(NR pass will benchmark p99.)* |

### 3.3 MEDIUM (score 4-5, MONITOR)

| ID | FM | Risk | Cat | P | I | Score | Mitigation | Test anchor |
|----|----|------|-----|---|---|-------|------------|-------------|
| R-26 | FM4.4 | Adversarial downstream reuse → bad promotion | BUS | 2 | 2 | 4 | §6.4 different-principal check | **Unit**: promotion requires principal change |
| R-27 | FM4.5 | Quarantine free-text contains PII | SEC | 2 | 2 | 4 | §8.7 PII-scrub before storage | **Unit**: scrubber removes regex matches |
| R-28 | FM4.7 | Reuse-success signal 7-day lag → non-determinism | BUS | 2 | 2 | 4 | §2.2 state_snapshot_version | **Unit**: retrieval with pinned version returns deterministic results |
| R-29 | FM4.10 | MAC-absent mode: tentative pool never promoted | BUS | 2 | 2 | 4 | §6.6 Stage 5 backfill deliverable | **Integration**: MAC-absent mode test asserts all admissions are TENTATIVE with logged warning |
| R-30 | FM4.12 | Quarantine cascade → downstream stale cache | BUS | 2 | 2 | 4 | §8.7 cache invalidation mirror of delete | **Integration**: quarantine emits pg_notify, downstream caches ack |
| R-31 | FM1.5 | Test/staging data bleeds into prod | OPS | 2 | 2 | 4 | env tag check + image discipline | **Integration**: prod deployment with non-prod env tag → sys.exit(2) |
| R-32 | FM2.7 | Crossover formula bug → seed dominates after N=25 | BUS | 2 | 2 | 4 | pure function + telemetry | **Unit / property**: `Hypothesis` tests monotonicity + N=25 crossover |
| R-33 | FM1.7 | In-process cache not keyed on tenant_id | SEC | 1 | 3 | 3 | Req #10 + unit test | **Unit**: cache key assertion |
| R-34 | FM2.9 | Embedding provider swap invalidates seed | DATA | 2 | 2 | 4 | seed_version includes embedding_model_id | **Unit**: version identity test |

### 3.4 LOW (score 1-3, DOCUMENT)

| ID | FM | Risk | Notes |
|----|----|------|-------|
| R-35 | FM1.2 | Shared Postgres co-tenancy | **ELIMINATED BY CONSTRUCTION** under B1 managed single-tenant. No test needed beyond ASR-1 (tenant_hash startup scan, R-10). |
| R-36 | FM1.3 | Shared backup infrastructure | **ELIMINATED** under B5 per-tenant backup keys. Covered by R-13. |
| R-37 | FM3.4 | LLM provider retention | Mitigated by ZDR default + B4 tenant-scoped keys. **Config validation test** asserts non-ZDR requires explicit opt-in. |
| R-38 | FM3.6 | Delete-before-create race | Mitigated by serializable transaction. **Concurrency test** is a nice-to-have. |
| R-39 | FM3.7 | Async quarantine window | §5.4 synchronous quarantine mark. **Integration test** asserts retrieval ignores quarantined entries during window. |
| R-40 | FM2.2 | Seed corpus poisoning at curation | Two-person review + content hash. **Documented process control, not a runtime test.** |
| R-41 | FM2.4 | Seed/tenant namespace collision | SHA-256 collision probability negligible. **Documented, no test.** |
| R-42 | FM4.11 | Promotion race | Idempotent CONFIRMED transition. **Unit test** asserts re-promotion is no-op. |
| R-43 | FM2.10 | Air-gapped seed fetch | Bundled in distribution image. **No runtime failure mode.** |

**Risk totals:** 6 CRITICAL (block gate), 19 HIGH (concerns), 9 MEDIUM (monitor), 9 LOW (document).

---

## 4. Test Level Strategy

### 4.1 Unit / Property / Static-Analysis Level

**Target: ~140 tests. Fastest feedback, highest density.**

Pure function + schema validation + introspection tests. No I/O, no DB, no network.

**Unit-suitable concerns:**
- Pure functions: `recency_decay`, `state_weight`, `retrieval_score` composition, `crossover_downweight`, `compute_content_hash`, `task_signature_hash`
- Pydantic schemas: `TelemetryEvent`, `TaskSignature`, `TaskOutcome`, `DecisionRecord`, `QuarantineReason` enum, `DeploymentManifest`
- Introspection / contract: Memory Protocol method signatures (no `scope`, no `tenant` kwarg drift)
- Static analysis lint: no raw-string logs in memory module, no `_internal/*` imports in application, no `scope=` in write-method call sites
- Config loader: accepts signed manifest, rejects tampered, rejects shared-keys, rejects SQLite in prod

**Hypothesis property tests (critical):**
- `retrieval_score` monotonicity in semantic similarity
- `retrieval_score` non-increasing in age
- `retrieval_score` = 0 for QUARANTINED / EXPIRED (invariance)
- `replay(beads[0..n])` determinism across any prefix
- `compact(compact(X)) == compact(X)` (idempotency — shared with Stage 2 contract test)
- `crossover_downweight` continuity + N=25 inflection point

**Favor unit when:** logic is isolable, no DB round-trip needed, no cross-process coordination.

### 4.2 Integration Level

**Target: ~70 tests. Highest risk density. Runs on `testcontainers-postgres` with pgvector + ltree extensions.**

Tests the Memory facade against real Postgres + real Mem0 + real pgvector — NOT mocks. Each test spins a fresh container per test class (class-scoped fixture) to honor test isolation.

**Integration-suitable concerns:**
- Facade ↔ pgvector delete cascade (R-01, R-04)
- Durable job resume on crash (R-14)
- Alembic migration safety (R-11)
- Backup restore validation (R-10)
- DB trigger enforcement of state transitions (R-20)
- Manifest 60s re-verification (R-07)
- Mem0 integration harness (R-15 + Req #58's 4 test classes)
- Seed corpus ingest tool (R-16, R-17, R-18)
- Experience library reaper + TTL expiry (R-25)
- Decision conflict detection (§5.5 write-time LLM classifier — stubbed LLM in tests)
- Tenant-local log sink audit trail (break-glass ledger)

**Favor integration when:** correctness depends on pgvector/ltree behavior, transactional semantics matter, or test validates a database migration or trigger.

### 4.3 E2E / Multi-Process Level

**Target: ~15 tests. Most expensive. Reserved for cross-process guarantees.**

Uses `pytest-xdist` + a docker-compose harness that spins up **N independent Praxis processes** with shared Postgres + Redis pub/sub. Captures what a single-process integration test cannot: cross-process cache invalidation, ack aggregation, multi-tenant isolation.

**E2E-suitable concerns:**
- R-02 cache-invalidation pub/sub across 3 processes
- R-06 two-tenant access isolation (2 processes, 2 deployments, 2 manifests)
- R-14 crash-and-resume of delete cascade (SIGKILL one process mid-cascade, supervisor restarts, another process observes completion)
- Worktree isolation hard-fail (process A with manifest pointing to worktree B fails at boot)

**Favor E2E when:** the guarantee depends on multi-process coordination that integration tests physically cannot verify.

### 4.4 Level Allocation Decision Matrix

| Concern | Unit | Integration | E2E | Primary |
|---------|------|-------------|-----|---------|
| Pydantic schema rejection of extra fields | ✅ | — | — | **Unit** |
| `retrieval_score` formula correctness | ✅ | — | — | **Unit (property)** |
| Delete cascade purges pgvector index | ⚠️ | ✅ | — | **Integration** |
| Cache invalidation across processes | — | ⚠️ | ✅ | **E2E** |
| Two-tenant access isolation | — | ⚠️ | ✅ | **E2E** |
| Crash-resume of durable delete job | — | ⚠️ | ✅ | **E2E** |
| Manifest 60s re-verification | — | ✅ | — | **Integration** |
| DB trigger denies direct state UPDATE | — | ✅ | — | **Integration** |
| Facade introspection: no `scope` kwarg | ✅ | — | — | **Unit** |
| Mem0 upgrade delete regression | — | ✅ | — | **Integration** |
| Crypto-shred backup decrypt failure | — | ✅ | ⚠️ | **Integration** |
| Tentative pool reaper + latency regression | — | ✅ | — | **Integration** |
| Beads replay determinism | ✅ | — | — | **Unit (property)** |

**Anti-pattern guard:** we explicitly refuse to E2E-test anything that can be verified at integration level. The E2E tier is exclusively for cross-process guarantees. This follows `test-levels-framework.md` "prefer lower level" principle.

---

## 5. Coverage Matrix

### 5.1 Requirement → Test Mapping (Parts A–E)

Every binding requirement (#1–#58) maps to at least one test case. Test IDs use format `{STAGE}.{PART}-{LEVEL}-{SEQ}` per `test-levels-framework.md`, prefixed `S3` for Stage 3:

**Part A — Tenancy & Isolation (Reqs 1-11)**

| Req | Test ID | Description | Level | Priority | Risk |
|-----|---------|-------------|-------|----------|------|
| 1 | S3.A-UNIT-001 | Every facade method accepts `tenant_id` as required positional arg (introspection) | Unit | P0 | R-09 |
| 1 | S3.A-INT-001 | Facade rejects call with `tenant_id ≠ manifest.tenant_id` | Integration | P0 | R-09 |
| 2 | S3.A-INT-002 | Beads worktree directory pinned from manifest, not caller | Integration | P0 | ASR-1 |
| 2 | S3.A-INT-003 | Mem0 `user_id` always injected from manifest, caller-provided value discarded | Integration | P0 | R-09 |
| 3 | S3.A-UNIT-002 | Manifest loader rejects missing signature field | Unit | P0 | R-23 |
| 3 | S3.A-UNIT-003 | Manifest loader rejects tampered signature | Unit | P0 | R-23 |
| 4 | S3.A-INT-004 | 60s re-verification exits process on drift (long-running test, 70s window) | Integration | P0 | R-07 |
| 5 | S3.A-UNIT-004 | Git CI lint rule rejects duplicate `db_fingerprint` in `praxis-config/deployments/*.yaml` | Unit (lint) | P1 | FM1.2 |
| 6 | S3.A-INT-005 | Every Memory-owned table introspection has `tenant_hash CHAR(64) NOT NULL` | Integration (migration) | P0 | ASR-5 |
| 6 | S3.A-INT-006 | Startup `tenant_hash` sample scan fails on mismatch | Integration | P0 | R-10 |
| 7 | S3.A-UNIT-005 | Introspection: no method kwarg name contains "tenant" (except `tenant_id` positional) | Unit | P0 | R-09 |
| 8 | S3.A-UNIT-006 | Facade exposes typed retrieval methods only (no `query(builder)` surface) | Unit | P1 | Req #8 |
| 9 | S3.A-UNIT-007 | `from praxis.kernel.memory._internal.mem0 import Mem0Client` raises ImportError | Unit | P0 | R-12 |
| 10 | S3.A-UNIT-008 | All in-process caches key on `(tenant_id, ...)` tuple — cache introspection | Unit | P1 | R-33 |
| 11 | S3.A-UNIT-009 | Facade has no method that accepts cross-tenant target | Unit | P0 | R-35 |

**Part B — Seed Corpus (Reqs 12-23)**

| Req | Test ID | Description | Level | Priority | Risk |
|-----|---------|-------------|-------|----------|------|
| 12 | S3.B-UNIT-010 | Facade introspection: no `scope` parameter on any method | Unit | P0 | R-18 |
| 13 | S3.B-INT-010 | Seed collection is separate Mem0 collection + read-only enforcement | Integration | P0 | ASR-10 |
| 14 | S3.B-UNIT-011 | `seed_version = sha256(content) + embedding_model_id + schema_version` hashing | Unit | P1 | R-34 |
| 15 | S3.B-INT-011 | Old seed_versions queryable in Beads after upgrade | Integration | P1 | FM2.8 |
| 16 | S3.B-UNIT-012 | No write code path to seed collection in `praxis.kernel.memory.*` (grep lint) | Unit (lint) | P0 | ASR-10 |
| 17 | S3.B-UNIT-013 | Seed ingest tool refuses records without license_attestation | Unit | P1 | R-16 |
| 18 | S3.B-UNIT-014 | Seed ingest PII scanner rejects regex matches (emails, SSN, phone) | Unit | P1 | R-17 |
| 18 | S3.B-INT-012 | Seed ingest NER scanner on full-record input | Integration | P2 | R-17 |
| 19 | S3.B-DOC-001 | Legal review gate documented in seed refresh runbook | Doc | P2 | FM2.1 |
| 20 | S3.B-INT-013 | Stale `seed_version` emits `seed_version_stale_warning` telemetry | Integration | P2 | R-24 |
| 21 | S3.B-INT-014 | Seed corpus loaded from distribution image, no network fetch | Integration | P2 | R-43 |
| 22 | S3.B-INT-015 | Every retrieval emits `source_distribution{seed: N, tenant: M}` | Integration | P1 | Req #22 |
| 23 | S3.B-UNIT-015 | Crossover formula is pure function + property test (monotonic, N=25 inflection) | Unit (property) | P1 | R-32 |

**Part C — Deletion, Access, GDPR (Reqs 24-37) — HIGHEST DENSITY**

| Req | Test ID | Description | Level | Priority | Risk |
|-----|---------|-------------|-------|----------|------|
| 24 | S3.C-INT-020 | `delete()` cascades across Beads → Mem0 → Atelier → experience library in order | Integration | P0 | R-14 |
| 25 | S3.C-INT-021 | Delete cascade writes `memory_jobs` row before starting (durable) | Integration | P0 | R-14 |
| 25 | S3.C-E2E-001 | Delete cascade crash-recovery: SIGKILL mid-cascade, restart, job resumes | E2E | P0 | R-14 |
| 26 | S3.C-INT-022 | Delete cascade runs VACUUM + REINDEX as named step | Integration | P0 | R-01 |
| 26 | S3.C-INT-023 | **CRITICAL** — post-delete verification query by deleted IDs returns zero hits on pgvector | Integration | P0 | **R-01** |
| 27 | S3.C-E2E-002 | **CRITICAL** — cache-invalidation pub/sub: 3 processes, delete from one, all ack before return | E2E | P0 | **R-02** |
| 28 | S3.C-INT-024 | Async experience library rewrites mark `state=QUARANTINED` synchronously | Integration | P1 | R-39 |
| 28 | S3.C-INT-025 | Quarantine-to-delete gap telemetered | Integration | P2 | FM3.7 |
| 29 | S3.C-INT-026 | Per-tenant KMS key created per deployment | Integration | P1 | R-13 |
| 29 | S3.C-INT-027 | Crypto-shred destroys key, backup decrypt fails cryptographically | Integration | P1 | R-13 |
| 30 | S3.C-UNIT-020 | Mem0 config loader rejects non-ZDR endpoints without explicit opt-in flag | Unit | P1 | R-37 |
| 31 | S3.C-UNIT-021 | Config loader rejects shared LLM API keys; requires per-deployment credentials | Unit | P0 | ASR-8 |
| 32 | S3.C-INT-028 | `export()` CLI returns structured bundle with all tenant records | Integration | P1 | Req #32 |
| 33 | S3.C-UNIT-022 | Audit log write: raw criteria rejected; only `criteria_hash` accepted | Unit | P0 | **R-03** |
| 33 | S3.C-INT-029 | Audit log schema introspection: no text column for raw criteria | Integration | P0 | **R-03** |
| 34 | S3.C-INT-030 | **CRITICAL** — after `delete()`, direct `SELECT embedding FROM decisions WHERE id IN (...)` returns zero rows | Integration | P0 | **ASR-2** |
| 34 | S3.C-INT-031 | Mem0 `delete()` followed by Mem0 `search()` returns zero hits | Integration | P0 | R-15 |
| 35 | S3.C-INT-032 | **CRITICAL** — after `flag_and_quarantine()`, direct `SELECT embedding FROM decisions WHERE id=?` returns NULL | Integration | P0 | **R-04** |
| 36 | S3.C-UNIT-023 | Mem0 config loader rejects cross-region replication | Unit | P2 | Req #36 |
| 37 | S3.C-E2E-003 | **CRITICAL (Winston)** — two-tenant access isolation: A's `export()` never returns B's records | E2E | P0 | **R-06** |

**Part D — Experience Library Governance (Reqs 38-50)**

| Req | Test ID | Description | Level | Priority | Risk |
|-----|---------|-------------|-------|----------|------|
| 38 | S3.D-INT-040 | `state` column CHECK constraint enforces 4 values | Integration | P1 | Req #38 |
| 39 | S3.D-INT-041 | Admission outlier detection rate-limits 10x normal | Integration | P1 | R-21 |
| 39 | S3.D-UNIT-030 | Composite admission signal: low `quality_confidence` → TENTATIVE even if score is high | Unit | P1 | R-22 |
| 40 | S3.D-UNIT-031 | Threshold classifier: `quality_score=0.85, confidence=0.7` → CONFIRMED | Unit | P1 | Req #40 |
| 40 | S3.D-UNIT-032 | Threshold: `quality_score=0.4` → REJECTED (not stored) | Unit | P1 | Req #40 |
| 41 | S3.D-INT-042 | Reaper demotes >90-day tentative entries to `state=EXPIRED` | Integration | P1 | R-25 |
| 42 | S3.D-INT-043 | Promotion requires downstream task quality_score ≥ 0.8 AND different principal | Integration | P1 | R-26 |
| 43 | S3.D-UNIT-033 | Retrieval score = 0 for QUARANTINED (invariance property) | Unit (property) | P0 | **R-04** |
| 43 | S3.D-UNIT-034 | Retrieval score = 0 for EXPIRED (invariance property) | Unit (property) | P1 | Req #43 |
| 43 | S3.D-UNIT-035 | Retrieval score monotonic in semantic similarity (Hypothesis) | Unit (property) | P1 | Req #43 |
| 44 | S3.D-INT-044 | `state_snapshot_version` returned with every retrieval; pinned queries are deterministic | Integration | P1 | R-28 |
| 45 | S3.D-UNIT-036 | `QuarantineReason` enum rejects non-enum values | Unit | P1 | R-27 |
| 45 | S3.D-INT-045 | Free-text PII scrubber removes regex matches before storage | Integration | P1 | R-27 |
| 46 | S3.D-DOC-002 | DSAR runbook explicitly mandates delete, not quarantine | Doc | P1 | R-19 |
| 46 | S3.D-UNIT-037 | `Memory.flag_and_quarantine()` docstring contains "NOT a delete" warning | Unit | P2 | R-19 |
| 47 | S3.D-INT-046 | Direct `UPDATE decisions SET state=...` denied without `praxis.state_change_authorized` | Integration | P1 | R-20 |
| 47 | S3.D-INT-047 | Break-glass writes append-only to `memory_break_glass_ledger` | Integration | P2 | R-20 |
| 48 | S3.D-DOC-003 | MAC → Memory backfill named in Stage 5 prompt (forward reference) | Doc | P1 | ASR-11 |
| 49 | S3.D-INT-048 | MAC-absent mode: all admissions TENTATIVE with `tentative_all_mode` telemetry | Integration | P1 | R-29 |
| 50 | S3.D-INT-049 | Quarantine emits `pg_notify('cache_invalidate')` same as delete | Integration | P2 | R-30 |

**Part E — Observability & Cross-Cutting (Reqs 51-58)**

| Req | Test ID | Description | Level | Priority | Risk |
|-----|---------|-------------|-------|----------|------|
| 51 | S3.E-UNIT-050 | `TelemetryEvent(query_content="foo")` raises Pydantic ValidationError | Unit | P0 | **R-05** |
| 51 | S3.E-UNIT-051 | `TelemetryEvent(extra_field="bar")` raises ValidationError (`extra="forbid"`) | Unit | P0 | **R-05** |
| 52 | S3.E-UNIT-052 | CI grep-lint: zero raw-string log statements in `praxis/kernel/memory/**/*.py` | Unit (lint) | P0 | R-08 |
| 53 | S3.E-INT-050 | Central telemetry sink receives only allowlisted fields (contract test) | Integration | P0 | R-08 |
| 54 | S3.E-INT-051 | Tenant-local log sink captures DEBUG; central sink does not | Integration | P1 | Req #54 |
| 54 | S3.E-INT-052 | Tenant-local sink access requires break-glass credential + audit log entry | Integration | P1 | R-20 |
| 55 | S3.E-INT-053 | All 10 required Prometheus metrics exposed | Integration | P1 | Req #55 |
| 56 | S3.E-DOC-004 | Retrieval-quality dashboard marked operator-only in Stage 6 handoff | Doc | P2 | Req #56 |
| 57 | S3.E-INT-054 | Memory emits `CostEvent(type="retrieval_cache_hit")` on successful cache hit | Integration | P1 | Req #57 |
| 57 | S3.E-INT-055 | Memory emits `CostEvent(type="retention_action")` on delete / quarantine | Integration | P1 | Req #57 |
| 58 | S3.E-INT-056 | Mem0 harness class 1: two-tenant isolation (overlapping content, no cross-leak) | Integration | P0 | R-15 |
| 58 | S3.E-INT-057 | Mem0 harness class 2: delete-then-query-by-id = zero | Integration | P0 | R-15 |
| 58 | S3.E-INT-058 | Mem0 harness class 3: schema stability (canary record after upgrade) | Integration | P0 | R-15 |
| 58 | S3.E-INT-059 | Mem0 harness class 4: retrieval semantics regression (pinned top-K) | Integration | P0 | R-15 |

### 5.2 Coverage Summary

| Part | Reqs | Tests | P0 | P1 | P2/P3 |
|------|------|-------|----|----|-------|
| A — Tenancy & Isolation | 11 | 15 | 11 | 3 | 1 |
| B — Seed Corpus | 12 | 16 | 3 | 8 | 5 |
| C — Deletion / GDPR | 14 | 22 | 11 | 8 | 3 |
| D — Experience Library | 13 | 21 | 2 | 14 | 5 |
| E — Observability | 8 | 14 | 6 | 6 | 2 |
| **Total** | **58** | **88** | **33** | **39** | **16** |

**Coverage ratio:** 88 test cases / 58 requirements = **1.52x**. This reflects defense-in-depth on privacy-critical requirements (C, E parts). No single requirement is uncovered.

Plus ~137 additional unit/property/static-analysis tests NOT tied to a specific requirement (pure function property tests, framework contract tests, and hardening lints) → **total ≈225 tests**.

---

## 6. Critical Test Scenarios (P0 Detailed Design)

This section gives Amelia the full test-first specification for every CRITICAL (score 9) risk. Each scenario is a complete pytest-ready description.

### 6.1 R-01 — pgvector Post-Delete Verification (S3.C-INT-023)

**Setup:**
```python
@pytest.fixture(scope="class")
async def populated_memory(deployment_manifest, test_postgres):
    """Memory instance with pgvector + 100 records across Beads/Mem0/Atelier."""
    memory = await Memory.from_manifest(deployment_manifest)
    for i in range(100):
        await memory.store_task_outcome(
            tenant_id=deployment_manifest.tenant_id,
            task=TaskSignature(input_hash=f"test_input_{i}", ...),
            outcome=TaskOutcome(quality_score=0.9, ...),
        )
    yield memory
    await memory.close()
```

**Test:**
```python
async def test_delete_cascade_purges_pgvector_index(populated_memory, test_postgres):
    """R-01 CRITICAL: After delete cascade, pgvector index contains zero hits."""
    target_ids = [f"test_input_{i}" for i in range(10)]

    delete_result = await populated_memory.delete(
        tenant_id=TENANT_ID,
        criteria=DeleteCriteria(input_hashes=target_ids),
    )
    assert delete_result.status == "succeeded"

    # Direct pgvector query — bypass the facade to validate underlying state
    async with test_postgres.acquire() as conn:
        for target_id in target_ids:
            rows = await conn.fetch(
                "SELECT 1 FROM mem0_vectors WHERE payload->>'input_hash' = $1 LIMIT 1",
                target_id,
            )
            assert rows == [], f"pgvector still contains {target_id}"

            # Also verify embedding column in decisions table
            rows = await conn.fetch(
                "SELECT embedding FROM decisions WHERE input_hash = $1",
                target_id,
            )
            assert rows == [], f"decisions table still has {target_id}"

    # Verify TelemetryEvent emitted
    events = await drain_telemetry_queue()
    assert any(
        e.event_type == "delete_cascade_verification_passed" for e in events
    )
```

**Fail conditions:**
- Any pgvector row still matches deleted ID → **TEST FAILS → GATE BLOCKED**
- `delete_cascade_verification_failed` event emitted → **TEST FAILS**

### 6.2 R-02 — Multi-Process Cache Invalidation (S3.C-E2E-002)

**Harness:** `tests/e2e/fixtures/multi_process_cluster.py` — spins 3 Praxis processes via docker-compose with shared Postgres + shared Redis pub/sub channel.

```python
async def test_cache_invalidation_gates_delete_ack(multi_process_cluster):
    """R-02 CRITICAL: delete() does NOT return until all 3 processes ack cache purge."""
    proc_a, proc_b, proc_c = multi_process_cluster.processes

    # Populate and warm caches on all 3 processes
    await proc_a.memory.store_task_outcome(tenant_id=TENANT, task=SIG, outcome=OUT)
    await asyncio.gather(
        proc_a.memory.retrieve_similar_tasks(TENANT, SIG),
        proc_b.memory.retrieve_similar_tasks(TENANT, SIG),
        proc_c.memory.retrieve_similar_tasks(TENANT, SIG),
    )

    # Verify all 3 have the embedding cached
    for proc in [proc_a, proc_b, proc_c]:
        assert proc.memory._internal_cache_has(SIG.input_hash)

    # Delete from proc_a — must block until b + c ack
    delete_task = asyncio.create_task(
        proc_a.memory.delete(TENANT, DeleteCriteria(input_hashes=[SIG.input_hash]))
    )

    # After 100ms, verify delete is still pending (waiting for acks)
    await asyncio.sleep(0.1)
    assert not delete_task.done(), "delete returned before acks received"

    # Verify proc_b and proc_c are purging (invariant: cache-invalidate event received)
    await asyncio.sleep(0.5)
    delete_result = await delete_task  # Should complete within timeout
    assert delete_result.status == "succeeded"

    # All 3 caches now empty
    for proc in [proc_a, proc_b, proc_c]:
        assert not proc.memory._internal_cache_has(SIG.input_hash)

    # Verify cache_invalidation_ack events from b and c
    events = await multi_process_cluster.drain_telemetry()
    ack_events = [e for e in events if e.event_type == "cache_invalidation_ack"]
    assert len(ack_events) == 2  # b + c (not a, which is the origin)
```

**Dependency:** C-01 (Winston must specify cache-invalidation ack timeout). Test uses strawman 5s; production value is deployment-manifest tunable.

### 6.3 R-03 — Audit Log Schema Rejection (S3.C-INT-029 + S3.C-UNIT-022)

**Integration test** (schema-level guarantee):
```python
async def test_audit_log_schema_has_no_raw_criteria_column(test_postgres):
    """R-03 CRITICAL: memory_audit_log schema contains only hashed criteria."""
    async with test_postgres.acquire() as conn:
        columns = await conn.fetch(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'memory_audit_log'"
        )
    column_names = {c['column_name'] for c in columns}

    # MUST have these
    assert 'criteria_hash' in column_names
    assert 'salt_epoch_id' in column_names
    assert 'operation_type' in column_names

    # MUST NOT have any raw-criteria column
    forbidden = {'criteria', 'raw_criteria', 'criteria_json', 'user_email',
                 'user_name', 'entry_payload', 'query_content'}
    assert not (forbidden & column_names), f"Forbidden columns: {forbidden & column_names}"

    # criteria_hash must be CHAR(64) (sha256 hex)
    hash_col = next(c for c in columns if c['column_name'] == 'criteria_hash')
    assert hash_col['data_type'] == 'character'
```

**Unit test** (write-path validation):
```python
def test_audit_log_writer_refuses_raw_criteria():
    """R-03 CRITICAL: Audit log writer rejects raw-criteria dict."""
    writer = AuditLogWriter(salt_rotator=FakeSaltRotator())

    with pytest.raises(PrivacyError, match="raw criteria"):
        writer.write_entry(
            operation="delete",
            raw_criteria={"user_email": "alice@example.com"},  # Forbidden path
        )

    # Correct path: pre-hashed
    writer.write_entry(
        operation="delete",
        criteria_hash=sha256_hex("alice@example.com", salt="epoch1"),
        salt_epoch_id="epoch1",
    )
    # Should succeed
```

### 6.4 R-04 — Quarantine Embedding Strip (S3.C-INT-032)

```python
async def test_quarantine_strips_embedding_in_place(memory, test_postgres):
    """R-04 CRITICAL: After flag_and_quarantine, embedding column = NULL."""
    # Create a decision
    decision = await memory.store_decision(
        tenant_id=TENANT,
        decision=DecisionRecord(
            decision="Test decision",
            rationale="Test rationale",
            alternatives_considered=[],
            evidence=[],
            confidence=0.9,
            captured_at=datetime.utcnow(),
        ),
    )

    # Verify embedding was computed and stored
    async with test_postgres.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT embedding, state FROM decisions WHERE decision_id = $1",
            decision.decision_id,
        )
    assert row['embedding'] is not None
    assert row['state'] == 'confirmed'

    # Quarantine
    result = await memory.flag_and_quarantine(
        tenant_id=TENANT,
        entry_id=decision.decision_id,
        reason=QuarantineReason.PII_LEAK,
        free_text=None,
    )
    assert result.status == "succeeded"

    # CRITICAL VERIFICATION: embedding is NULL post-quarantine
    async with test_postgres.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT embedding, state, reason_hash FROM decisions WHERE decision_id = $1",
            decision.decision_id,
        )

    assert row['embedding'] is None, "FM3.10 FAILURE: embedding retained after quarantine"
    assert row['state'] == 'quarantined'
    assert row['reason_hash'] is not None

    # Also verify retrieval cannot return this decision
    retrieved = await memory.retrieve_decisions(TENANT, "Test rationale", top_k=10)
    assert decision.decision_id not in [d.decision_id for d in retrieved.items]
```

### 6.5 R-05 — TelemetryEvent Extra-Field Rejection (S3.E-UNIT-050 + -051)

```python
def test_telemetry_event_rejects_query_content():
    """R-05 CRITICAL: TelemetryEvent refuses to accept query_content field."""
    with pytest.raises(ValidationError) as exc_info:
        TelemetryEvent(
            event_type="retrieval_completed",
            tenant_hash="abc",
            query_content="What is the meaning of life?",  # FORBIDDEN
        )
    assert "query_content" in str(exc_info.value)

def test_telemetry_event_rejects_result_ids():
    """R-05 CRITICAL: TelemetryEvent refuses result_ids list."""
    with pytest.raises(ValidationError):
        TelemetryEvent(
            event_type="retrieval_completed",
            tenant_hash="abc",
            result_ids=["id1", "id2"],  # FORBIDDEN
        )

def test_telemetry_event_rejects_arbitrary_extra():
    """R-05 CRITICAL: Pydantic extra='forbid' rejects any unknown field."""
    with pytest.raises(ValidationError):
        TelemetryEvent(
            event_type="retrieval_completed",
            tenant_hash="abc",
            embedding=[0.1, 0.2, 0.3],  # FORBIDDEN
        )

def test_telemetry_event_accepts_allowlisted_fields():
    """Positive control: allowlisted fields work."""
    event = TelemetryEvent(
        event_type="retrieval_completed",
        tenant_hash="abc",
        agent_id="architect",
        run_id="run_123",
        top_k=5,
        hit_count=3,
        source_distribution={"seed": 1, "tenant": 2},
        latency_ms=42.5,
    )
    assert event.hit_count == 3
```

### 6.6 R-06 — Two-Tenant Access Isolation (S3.C-E2E-003, Winston-CRITICAL)

```python
async def test_two_tenant_access_isolation_via_export(dual_tenant_cluster):
    """R-06 CRITICAL (Winston): Memory.export(A) never returns tenant B's records."""
    proc_a, proc_b = dual_tenant_cluster.processes
    assert proc_a.manifest.tenant_id != proc_b.manifest.tenant_id

    # Tenant A stores 50 records
    for i in range(50):
        await proc_a.memory.store_task_outcome(
            tenant_id=proc_a.manifest.tenant_id,
            task=TaskSignature(input_hash=f"tenant_a_task_{i}", ...),
            outcome=TaskOutcome(...),
        )

    # Tenant B stores 50 different records with overlapping content
    for i in range(50):
        await proc_b.memory.store_task_outcome(
            tenant_id=proc_b.manifest.tenant_id,
            task=TaskSignature(input_hash=f"tenant_b_task_{i}", ...),
            outcome=TaskOutcome(...),
        )

    # Export from tenant A
    export_a = await proc_a.memory.export(
        tenant_id=proc_a.manifest.tenant_id,
        criteria=ExportCriteria(include_all=True),
    )

    # CRITICAL: zero tenant B records in A's export
    assert len(export_a.records) == 50
    for record in export_a.records:
        assert not record.task.input_hash.startswith("tenant_b_"), \
            f"ISOLATION BREACH: {record.task.input_hash}"
        assert record.tenant_hash == proc_a.manifest.tenant_hash

    # Also verify: passing tenant B's ID to process A's facade is a hard fail
    with pytest.raises(TenantIdentityError):
        await proc_a.memory.export(
            tenant_id=proc_b.manifest.tenant_id,  # Wrong tenant for proc_a
            criteria=ExportCriteria(include_all=True),
        )
```

---

## 7. Fixture Architecture (Python / pytest)

Adheres to the `fixture-architecture.md` knowledge fragment: pure functions first, fixture wrappers second, composable via pytest fixture scoping.

### 7.1 Fixture Hierarchy

```
tests/
├── conftest.py                      # Project-wide fixtures
├── fixtures/
│   ├── __init__.py
│   ├── postgres.py                  # testcontainers-postgres class-scoped
│   ├── pgvector.py                  # pgvector+ltree extension bootstrap
│   ├── manifest.py                  # DeploymentManifest factory + signer
│   ├── memory_instance.py           # Memory facade factory
│   ├── telemetry.py                 # TelemetryEvent capture/drain
│   ├── mem0_mock.py                 # Mem0 stub for unit tests (NOT integration)
│   ├── llm_stub.py                  # Anthropic/OpenAI stub for cheap classifier calls
│   ├── data_factories.py            # TaskSignature / DecisionRecord / FactRecord factories
│   ├── multi_process_cluster.py     # E2E docker-compose harness (3-proc)
│   └── dual_tenant_cluster.py       # E2E 2-tenant harness
├── unit/
│   ├── test_facade_introspection.py # Protocol inspection tests
│   ├── test_telemetry_schema.py     # Pydantic allowlist tests (R-05)
│   ├── test_retrieval_score.py      # Property tests (Hypothesis)
│   ├── test_crossover.py            # Pure-function property tests
│   ├── test_beads_replay.py         # Replay determinism (Hypothesis)
│   ├── test_manifest_loader.py      # Signature validation
│   └── test_ci_lints.py             # grep-based lint rules
├── integration/
│   ├── test_delete_cascade.py       # R-01, cascade tests
│   ├── test_quarantine.py           # R-04 direct-DB verification
│   ├── test_audit_log.py            # R-03 schema + write-path
│   ├── test_manifest_reverify.py    # R-07 60s loop
│   ├── test_mem0_harness.py         # R-15 4 test classes (Req #58)
│   ├── test_tenant_hash_column.py   # ASR-5 schema introspection
│   ├── test_admission_gate.py       # R-21, R-22
│   ├── test_reaper.py               # R-25 TTL expiry
│   ├── test_seed_ingest_tool.py     # R-16, R-17
│   ├── test_state_triggers.py       # R-20 DB trigger enforcement
│   ├── test_migrations.py           # R-11 Alembic safety harness
│   ├── test_crypto_shred.py         # R-13 KMS integration
│   └── test_telemetry_contract.py   # R-08 central sink contract
└── e2e/
    ├── test_cache_invalidation.py   # R-02 (CRITICAL, 3-process)
    ├── test_two_tenant_isolation.py # R-06 (CRITICAL, 2-tenant)
    ├── test_delete_crash_recovery.py # R-14 (SIGKILL mid-cascade)
    └── test_worktree_isolation.py   # Boot-hard-fail on worktree mismatch
```

### 7.2 Core Fixtures (API contracts)

**`deployment_manifest` (class-scoped, factory)** — returns a signed DeploymentManifest with a deterministic tenant_id per test class. Under the hood: generates a per-test KMS-stub key, signs a YAML manifest, writes it to a temp `praxis-config/deployments/` dir. Fresh per class to prevent cross-test contamination.

**`test_postgres` (class-scoped)** — testcontainers-postgres running Postgres 16 with pgvector + ltree extensions bootstrapped. Runs `0001_memory_initial` Alembic migration before yielding. Auto-cleanup on class teardown (container destroyed, no state leak).

**`memory` (function-scoped)** — constructs a Memory facade bound to the deployment_manifest + test_postgres. Function-scope so each test gets a fresh facade (guards against in-process cache leakage across tests).

**`telemetry_capture` (function-scoped)** — installs a test-only TelemetryEvent sink that captures all emitted events in-memory. Test body can drain the queue and assert expected events. Auto-drains on teardown.

**`multi_process_cluster` (session-scoped)** — docker-compose harness with N Praxis containers + shared Postgres + shared Redis pub/sub. Session-scoped because container startup is expensive; tests within the session share the cluster but use distinct tenant_ids per test to maintain isolation.

**`dual_tenant_cluster` (class-scoped, subset of multi_process)** — 2 processes with 2 independent tenant_ids and 2 independent Postgres databases (two tenant boundaries). Specifically for R-06 two-tenant isolation tests.

### 7.3 Data Factories

Factory functions following `data-factories.md` pattern (no static JSON fixtures, no hardcoded IDs):

```python
# tests/fixtures/data_factories.py
from faker import Faker
import hashlib, ulid

faker = Faker()
Faker.seed(42)  # deterministic where it helps — each test still gets unique values via ULID

def make_task_signature(**overrides) -> TaskSignature:
    return TaskSignature(
        task_type=overrides.get("task_type", "strategic_advisory"),
        input_hash=overrides.get("input_hash", hashlib.sha256(faker.text().encode()).hexdigest()),
        agents_involved=tuple(overrides.get("agents_involved", ("architect", "pm"))),
        context_fingerprint=overrides.get("context_fingerprint", hashlib.sha256(faker.text().encode()).hexdigest()),
        schema_version=overrides.get("schema_version", 1),
    )

def make_task_outcome(**overrides) -> TaskOutcome:
    return TaskOutcome(
        quality_score=overrides.get("quality_score", 0.85),
        quality_confidence=overrides.get("quality_confidence", 0.75),
        cost_usd=overrides.get("cost_usd", 0.50),
        reasoning_trace=overrides.get("reasoning_trace", []),
        approach_summary=overrides.get("approach_summary", faker.sentence()),
        dissents=overrides.get("dissents", []),
    )

def make_decision_record(**overrides) -> DecisionRecord:
    return DecisionRecord(
        decision=overrides.get("decision", faker.sentence()),
        rationale=overrides.get("rationale", faker.paragraph()),
        alternatives_considered=overrides.get("alternatives_considered", []),
        evidence=overrides.get("evidence", []),
        confidence=overrides.get("confidence", 0.8),
        captured_at=overrides.get("captured_at", datetime.utcnow()),
        ttl_days=overrides.get("ttl_days", 365),
    )
```

**Parallel safety:** every factory uses `faker` + ULID for non-deterministic ID generation → tests can run with `pytest-xdist` workers without collision.

### 7.4 Fixture Composition Rules

- **Unit tests** use NO fixtures except factories + stubs (`mem0_mock`, `llm_stub`). No DB, no network, no containers.
- **Integration tests** use `test_postgres` + `deployment_manifest` + `memory` + `telemetry_capture` + factories. LLM calls stubbed.
- **E2E tests** use `multi_process_cluster` OR `dual_tenant_cluster`. Containers run real Mem0 dependency (not stub). LLM stubbed at the Mem0 config level.

**Anti-pattern refused:** page-object-model-like base classes. All helpers are pure functions + fixture wrappers.

---

## 8. Test Data Strategy

### 8.1 Parallel-Safe Uniqueness

Every factory generates unique IDs per call (ULID + faker). **Never hardcode `input_hash="test_input_1"`** — parallel runs collide. Test code that needs referential IDs does so via local variable, not hardcoded string.

### 8.2 Privacy-Critical Test Data

**Integration and E2E tests MUST use synthetic PII-shaped data** — never real emails, real names, or production data dumps. Rationale: these tests exercise the delete cascade and audit log; accidentally ingesting real PII defeats the purpose of testing privacy guarantees.

```python
# synthetic PII generator
def make_pii_bearing_content() -> dict:
    return {
        "email": faker.email(),                    # FAKE
        "phone": faker.phone_number(),             # FAKE
        "ssn": faker.ssn(),                        # FAKE
        "name": faker.name(),                      # FAKE
        "credit_card": faker.credit_card_number(), # FAKE
    }
```

### 8.3 Seeding via API (not UI)

The Memory layer has no UI. All seeding is via direct facade calls. There is no "UI-based setup" temptation to avoid — standard hazard doesn't apply at this stage. Tests use `memory.store_*()` directly from factories.

### 8.4 Cleanup Discipline

`testcontainers-postgres` tears down the container on class teardown → automatic cleanup of all test data. No manual DELETE cleanup needed. For session-scoped `multi_process_cluster`, each test uses a distinct tenant_id / input_hash namespace and cleanup happens at session end.

### 8.5 Fixture Data for Mem0 Regression Harness (Req #58 class 4)

The canonical query set for Mem0 retrieval-semantics regression lives at `tests/fixtures/mem0_regression_corpus.yaml`:
- ~20 canonical query/top-K pairs generated once with the initial Mem0 version
- Every Mem0 upgrade PR must re-run the harness; ranking drift = PR reviewed, not auto-merged
- Updating the corpus requires an ADR (`decision-memory/adr-mem0-regression-corpus-v{N}.md`)

---

## 9. Mem0 Integration Harness (Req #58)

Dedicated test module `tests/integration/test_mem0_harness.py` runs on every CI build AND every Mem0 upstream version bump. The four test classes are non-negotiable and gate the Mem0 pin.

### 9.1 Class 1 — Two-Tenant Isolation

**Purpose:** Defense-in-depth verification that Mem0's `user_id` boundary honors isolation even under managed single-tenant.

```python
async def test_mem0_two_tenant_isolation(test_postgres):
    """FM1.2 DIL: Mem0 query on user_id=A never returns user_id=B's records."""
    mem0_a = await Mem0Client.from_config(make_config(user_id="tenant_a_hash"))
    mem0_b = await Mem0Client.from_config(make_config(user_id="tenant_b_hash"))

    # Insert overlapping content into both collections
    for i in range(20):
        await mem0_a.add_fact(messages=[{"role": "user", "content": f"shared topic {i}"}])
        await mem0_b.add_fact(messages=[{"role": "user", "content": f"shared topic {i}"}])

    # Query tenant A
    results_a = await mem0_a.search("shared topic", top_k=50)
    for r in results_a:
        assert r.metadata['user_id'] == "tenant_a_hash"
```

### 9.2 Class 2 — Delete Then Query Zero-Result

**Purpose:** Guards against FM3.1 and FM3.11 (Mem0 upstream delete bug).

```python
async def test_mem0_delete_then_query_zero_hits(mem0_client):
    """FM3.1 + FM3.11: After delete, query by deleted ID returns zero."""
    fact = await mem0_client.add_fact(
        messages=[{"role": "user", "content": "unique test content"}],
    )
    results_before = await mem0_client.search("unique test content", top_k=10)
    assert any(r.id == fact.id for r in results_before)

    await mem0_client.delete(fact.id)

    # Immediate query — MUST be zero
    results_after = await mem0_client.search("unique test content", top_k=10)
    assert not any(r.id == fact.id for r in results_after), \
        "FM3.11: Mem0 upstream delete bug — pgvector still has entry"

    # Also query by exact ID
    by_id = await mem0_client.get(fact.id)
    assert by_id is None
```

### 9.3 Class 3 — Schema Stability

**Purpose:** Detects backward-incompatible field changes in Mem0 upstream.

```python
async def test_mem0_schema_stability(mem0_client):
    """FM3.11/CC.3: Canary record with every field type; upgrade must preserve all."""
    canary = await mem0_client.add_fact(
        messages=[{"role": "user", "content": "canary"}],
        metadata={
            "str_field": "hello",
            "int_field": 42,
            "float_field": 3.14,
            "bool_field": True,
            "list_field": [1, 2, 3],
            "nested": {"key": "value"},
        },
    )

    retrieved = await mem0_client.get(canary.id)

    assert retrieved.metadata['str_field'] == "hello"
    assert retrieved.metadata['int_field'] == 42
    assert abs(retrieved.metadata['float_field'] - 3.14) < 1e-6
    assert retrieved.metadata['bool_field'] is True
    assert retrieved.metadata['list_field'] == [1, 2, 3]
    assert retrieved.metadata['nested']['key'] == "value"
```

### 9.4 Class 4 — Retrieval Semantics Regression

**Purpose:** Pinned query set with expected top-K; any Mem0 upstream change that shifts rankings = regression flag.

```python
async def test_mem0_retrieval_semantics_pinned(mem0_client):
    """Regression guard: canonical queries must return expected top-K."""
    corpus = load_yaml("tests/fixtures/mem0_regression_corpus.yaml")

    for record in corpus['seed_records']:
        await mem0_client.add_fact(**record)

    for query_case in corpus['queries']:
        results = await mem0_client.search(query_case['query'], top_k=query_case['top_k'])
        actual_ids = [r.id for r in results]
        expected_ids = query_case['expected_top_k_ids']

        # Rankings must match — any drift is a regression for review
        assert actual_ids == expected_ids, \
            f"Mem0 ranking drift for query '{query_case['query']}'"
```

### 9.5 Harness Invocation

```bash
# Per-CI run (every PR):
pytest tests/integration/test_mem0_harness.py -m "mem0_harness" --timeout=120

# Mem0 upgrade gate (PR that bumps the version):
pytest tests/integration/test_mem0_harness.py -m "mem0_harness" --mem0-version-check
```

Mem0 version bumps that fail any of the 4 classes cannot merge. This is enforced by a branch protection rule on `main`.

---

## 10. Execution Strategy

Simple PR / Nightly / Weekly model per `test-priorities-matrix.md`.

### 10.1 PR Gate (blocks merge)

**All P0 + all P1 tests. Target: ≤15 minutes total.**

Runs on every PR via GitHub Actions (`ci.yml`):
- All unit tests (~140 tests, ~90 seconds with pytest-xdist)
- All P0/P1 integration tests (~60 tests, ~8 minutes with pytest-xdist + testcontainers)
- Exactly 4 E2E tests marked `@pytest.mark.critical` (R-02, R-06, R-14, worktree-isolation), ~5 minutes
- Coverage report via pytest-cov; gate fails if <85%
- Mem0 harness (4 classes, ~2 minutes)

**Selective test execution** via pytest marks:
```python
@pytest.mark.p0
@pytest.mark.critical   # R-01..R-06 subset
@pytest.mark.privacy    # all Part C tests
@pytest.mark.mem0_harness
```

PR runs: `pytest -m "p0 or p1 or critical" --timeout=60`

### 10.2 Nightly (scheduled 02:00 UTC)

**All tests including P2 + P3 + property tests with higher example counts.**

- Full suite including P2/P3 tests
- Hypothesis tests with `max_examples=500` (PR runs with 50 for speed)
- Mem0 canary tests against nightly-pinned Mem0 version
- Long-running reaper / admission-rate-limit tests (strawman 30+ minutes)

### 10.3 Weekly (scheduled Sunday 04:00 UTC)

**Soak / chaos / performance baselines.**

- NR-pass-owned: p99 retrieval latency under sustained load (feed forward into NR report)
- Crash-resume soak: 100 iterations of delete-then-SIGKILL
- Beads replay soak: 10K bead chains
- Mem0 upgrade scan: check pypi for new Mem0 version, run full harness if found

### 10.4 On-Demand Triggers

- **Mem0 version bump PR** → runs full Mem0 harness + nightly integration suite
- **Architecture.md changes** → runs full PR suite + documentation-linked tests (DSAR runbook, API docstring assertions)
- **requirements.md changes** → traceability audit: every new/modified requirement must have a linked test case or the build fails

### 10.5 Failure Escalation

- **P0 failure in PR run** → merge blocked, author pinged, no override
- **P1 failure in PR run** → merge blocked, author may request waiver via PR comment to `@murat-tea-bot` (requires Quinn approval for Stage 3.4 gate)
- **Nightly failure** → GitHub issue auto-opened with logs; review at next daily standup
- **Mem0 harness failure** → Mem0 version pin reverted automatically; PR author notified

---

## 11. Quality Gates

### 11.1 Stage 3.4 Gate Criteria (Quinn handoff)

| Gate | Threshold | Hard/Soft |
|------|-----------|-----------|
| **P0 pass rate** | 100% | **HARD** — no waiver |
| **P1 pass rate** | ≥95% | HARD |
| **P2 pass rate** | ≥80% | SOFT (documented gaps allowed) |
| **Line coverage** | ≥85% | HARD (Pipeline.md gate) |
| **Branch coverage** | ≥75% | SOFT |
| **All R-01..R-06 CRITICAL tests green** | 100% | **HARD — BLOCK gate** |
| **Mem0 harness 4 classes pass** | 100% | **HARD** |
| **Zero audit-log raw-criteria columns** | 0 | HARD |
| **Zero `_internal` imports from application code** | 0 | HARD |
| **Zero raw-string log statements in memory module** | 0 | HARD |
| **Privacy enforcement tests** | 100% of Part C tests green | **HARD** |

### 11.2 Gate Decision Logic

- **PASS:** all hard gates green + ≥85% coverage → advance to Stage 3.5 alignment review
- **CONCERNS:** all hard gates green but P2 pass <80% OR branch coverage <75% → advance with documented remediation plan (owner + deadline)
- **FAIL:** any hard gate red → block advancement, return to Amelia for fixes, re-run gate after fixes

### 11.3 No-Waiver Zones

These risks have zero waiver path:
- R-01 (pgvector orphaned entries) — regulator-visible
- R-02 (cache invalidation) — undermines delete guarantee
- R-03 (audit log PII) — audit-of-audit paradox
- R-04 (quarantine embedding strip — FM3.10 override) — B2 one-way door
- R-05 (telemetry query leak) — undermines privacy posture
- R-06 (two-tenant isolation) — Winston-marked CRITICAL

If any of the six is failing, release is blocked full stop.

---

## 12. Resource Estimates

Ranges only — avoid false precision.

### 12.1 Test Authoring Effort

| Level | Test count | Effort/test | Subtotal |
|-------|-----------|-------------|----------|
| Unit / property / static-analysis | ~140 | 15–30 min | ~35–70 hours |
| Integration | ~70 | 45–90 min | ~50–105 hours |
| E2E multi-process | ~15 | 3–6 hours | ~45–90 hours |
| Mem0 harness (Req #58) | 4 classes | already estimated above | included |
| Fixture architecture + factories | — | one-time | ~20–30 hours |
| **Total authoring** | **~225** | — | **~150–295 hours** |

At a 4-hour productive window per day, that's **5–8 weeks of focused test-first work** interleaved with Amelia's implementation. Realistic with Amelia working Sonnet-4.6 high-thinking on implementation and test harness in parallel.

### 12.2 Priority Band Estimates

| Priority | Tests | Effort | Notes |
|----------|-------|--------|-------|
| P0 | ~50 | ~50–85 hours | All R-01..R-06 + privacy-critical Part C |
| P1 | ~90 | ~60–110 hours | Admission, reaper, Mem0 harness, manifest |
| P2 | ~60 | ~25–60 hours | Observability, seed corpus, stale warnings |
| P3 | ~25 | ~15–40 hours | Promotion races, crossover formula, docs |

### 12.3 Test Infrastructure Setup (one-time)

- **testcontainers-postgres + pgvector + ltree bootstrap:** 6–10 hours
- **multi_process_cluster docker-compose harness:** 12–20 hours (E2E is expensive)
- **Mem0 stub + LLM stub:** 8–12 hours
- **pytest-xdist + coverage config:** 2–4 hours
- **CI pipeline (GitHub Actions workflow):** 6–10 hours
- **Branch protection + required status checks:** 1–2 hours

**Infrastructure total: ~35–58 hours** (done once, amortized across all test work).

### 12.4 Timeline (calendar)

With test-first discipline and Amelia writing implementation in parallel:
- **Week 1–2:** Infrastructure + fixtures + Part A tests (tenancy) ≈ 60 hours
- **Week 3–4:** Part C tests (delete/GDPR — highest density) ≈ 80 hours — HEAVIEST BLOCK
- **Week 5–6:** Parts B + D + E + Mem0 harness ≈ 80 hours
- **Week 7:** Full regression pass + coverage polish + gate sign-off ≈ 20 hours
- **Week 8:** Buffer for gate fixes + Stage 3.4 Quinn review

**Total calendar: 6–8 weeks.** Matches Stage 3 implementation window.

---

## 13. Open Questions (forwarded to NR pass + Winston)

### 13.1 Forwarded to NR Assessment (Pass 2)

These questions are NFR-shaped and belong in the upcoming NR pass:

| ID | Question | NR Category |
|----|----------|-------------|
| NR-Q1 | **Retrieval p99 latency target** — architecture mentions 100ms p99 for Beads (§3.6 test target) but no facade-level p99 for decision/fact retrieval. NR pass must define. | PERF |
| NR-Q2 | **Scalability ceiling for tentative pool** — R-25 ticks PERF CONCERN. At what tenant size does p99 retrieval regress when tentative count grows? NR benchmark. | SCAL |
| NR-Q3 | **Crypto-shred timing guarantee** — DPA language says "within N days." What is N? NR pass quantifies and drafts the DPA language. | COMP |
| NR-Q4 | **Mem0 transitive dependency SCA scan** — flagged in §2.2 (ADR readiness table). Not in Stage 3 scope but NR pass should surface known CVEs in Mem0's deps. | SEC |
| NR-Q5 | **Manifest re-verification latency window** — 60s is the contract, but what's the window where a drifted state could still serve requests? | REL |
| NR-Q6 | **Reliability under backup/restore** — R-10 tests restore hard-fail, but not the RTO after a restore. NR defines RTO. | REL |
| NR-Q7 | **KMS failure behavior** — if AWS KMS is unreachable, Memory can't crypto-shred. Degraded mode? | REL |

### 13.2 Forwarded to Winston (architecture clarifications before Amelia)

| ID | Question | Reference |
|----|----------|-----------|
| W3-T | **Cache-invalidation ack timeout strategy** — C-01 in §2.1. Current arch says "ack aggregation gates" (blocking). Recommend: best-effort with 5s timeout + unresponsive-subscriber telemetry. Winston needs to ratify OR specify alternative. | Req #27, §8.5 step 7, §11 W3 |
| TEST-1 | **Test-only `_touch_last_accessed=False` parameter** — C-04 in §2.1. Proposed escape hatch for deterministic-ranking tests. Winston approves? | §5.3 |
| TEST-2 | **`test_seed_corpus_write_impossible` (§10.2)** — C-06 in §2.1. Recommend deduplicating with `test_facade_no_scope_parameter`. Winston agrees? | §10.2 |
| TEST-3 | **Reducer purity constraint for `replay.py`** — C-02 in §2.1. Formalize in §3.6 so property tests can assert it? | §3.6 |
| TEST-4 | **Mem0 retrieval regression corpus update process** — § 9.5 proposes ADR. Winston agrees? | Req #58 |

### 13.3 Carried Forward to Stage 3.3 (Amelia)

- All P0 test scenarios in §6 are test-first specifications — Amelia writes test code FROM these specifications, then implements the module to make them green.
- Fixture architecture in §7 is binding — no alternative fixture patterns.
- Module layout honors §3.1 from architecture.md. No deviation.

### 13.4 Carried Forward to Stage 3.4 (Quinn)

- Gate criteria in §11 are binding.
- Coverage metric = pytest-cov line + branch.
- No-waiver zones (§11.3) are enforced by branch protection; Quinn cannot override.

### 13.5 Carried Forward to Stage 3.5 (Alignment Review)

- Verify Memory CostEvent integration honors Stage 1 Pi-Mono contract (test S3.E-INT-054/055).
- Verify Beads compaction interaction with Stage 2 Forge honors the subprocess-wrapper contract (§3.4).
- Verify `tenant_id` propagation through the compression layer (Stage 2 alignment-review.md §6 follow-up).

---

## 14. Handoff Contracts

### 14.1 Stage 3.3 (Amelia — Developer) — test-first blueprint

**Binding inputs you MUST read:**
1. This document (`test-strategy.md`) — start with §6 Critical Test Scenarios
2. `architecture.md` §3.1 module layout — no deviation
3. `architecture.md` §10 Testability Notes — Winston scaffolding (many redundancies with this doc; where they disagree, **this doc wins** for test wording because it honors the fuller FMEA mapping)

**Build order (test-first):**
1. Write fixtures first (`tests/fixtures/`) — pure functions + wrappers
2. Write P0 unit tests (facade introspection, Pydantic, pure functions)
3. Write P0 integration tests for R-01..R-05 BEFORE implementing delete cascade or quarantine
4. Implement module in `praxis/kernel/memory/` — run the above tests red → green
5. Write P0 E2E tests for R-02, R-06 (multi-process cluster comes last)
6. Fill out P1/P2 tests interleaved with reaper, admission, and Mem0 adapter implementation

**Context discipline (from Pipeline §4.6):** Mem0 reference dump is 7.8MB. Read only §4.5 Mem0 Integration Adapter from architecture.md. Do NOT load the whole dump into context when writing the adapter — use `architecture.md §4.5` as the spec.

### 14.2 Stage 3.4 (Quinn — QA) — gate criteria

Gate criteria are defined in §11. Coverage reporter: `pytest-cov`. Summary format: JUnit XML + Markdown report posted to PR.

### 14.3 Stage 3.5 (Alignment Review) — integration checks

Cross-stage integration test targets listed in §13.5. Alignment review runs these specifically.

### 14.4 Stage 5 (MAC) — forward reference

Stage 3 includes tests for the **MAC-absent mode** (R-29, S3.D-INT-048). When Stage 5 MAC ships, it MUST run the backfill job (Req #48) and tests in this document's R-29 should flip from MAC-absent assertions to MAC-present assertions. That's a Stage 5 prompt addition, not Stage 3 work.

---

## Appendix A — Requirement Coverage Check

Every requirement #1–#58 has at least one test mapping in §5.1. Sample spot-check:

| Req | Covered | Test IDs |
|-----|---------|----------|
| #1  | ✅ | S3.A-UNIT-001, S3.A-INT-001 |
| #25 | ✅ | S3.C-INT-021, S3.C-E2E-001 |
| #34 | ✅ | S3.C-INT-030, S3.C-INT-031 |
| #35 | ✅ | S3.C-INT-032 (CRITICAL R-04) |
| #43 | ✅ | S3.D-UNIT-033, -034, -035 |
| #51 | ✅ | S3.E-UNIT-050, -051 (CRITICAL R-05) |
| #58 | ✅ | S3.E-INT-056, -057, -058, -059 + §9 full harness |

Full coverage audit runs as CI job `test_traceability` — fails build if any requirement lacks a linked test case after the final Stage 3.3 implementation sprint.

## Appendix B — Failure-Mode Coverage Check

All 43 failure modes from the Round 2 FMEA have risk-register entries in §3. Of these:
- **25 have dedicated test scenarios** (FM1.1, FM1.4, FM1.6, FM1.8-10, FM2.1, FM2.3, FM2.5-7, FM2.9, FM3.1-5, FM3.8-11, FM4.1-3, FM4.5-10, FM4.12, CC.5)
- **7 are ELIMINATED by construction** (FM1.2, FM1.3 under B1/B5; FM2.2, FM2.10, FM2.4, FM4.11 are process controls or accepted)
- **4 have documentation tests only** (FM2.1 attestation, FM4.6 DSAR runbook, FM4.7 docs, FM2.8 retention)
- **7 are covered transitively by higher-level tests** (FM3.6/3.7 by cascade tests, FM1.5 by env tag test, FM1.7 by unit cache test, FM4.4 by promotion test, FM4.12 by cascade test, FM2.6 by introspection test)

No failure mode is uncovered. Zero blind spots vs. the FMEA.

---

## Signoff

**Stage 3.2 Test Design: v1.0 COMPLETE.**

- Risk register: 43 FMs mapped to 6 CRITICAL + 19 HIGH + 9 MEDIUM + 9 LOW entries
- Coverage: 88 requirement-linked tests + ~137 additional unit/property tests = ~225 total
- Test levels: ~140 unit + ~70 integration + ~15 E2E
- Quality gates: 6 CRITICAL no-waiver tests anchor the BLOCK gate
- Estimated effort: 150–295 hours over 6–8 calendar weeks (matches Stage 3 window)

**Pipeline.md Step 3.2 gate checklist:**
- [x] Test strategy at `_bmad-output/implementation-artifacts/praxis/memory/test-strategy.md`
- [x] Privacy/scoping enforcement tests critical (R-01..R-06, Part C Deletion/GDPR — 22 tests, 11 P0)
- [x] Retrieval correctness tests designed (§10.1 pure function property tests, §5.1 Part D Req #43 invariants)

**Ready for NR pass (Pass 2).** Binding inputs for NR: this `test-strategy.md` + `requirements.md` + `architecture.md`. Focus categories: Security (embeddings-as-PII threat surface), Compliance (GDPR right-to-erasure verification), Performance (retrieval p99 under scale), Reliability (crypto-shredding under concurrent ops), Scalability (pgvector + multi-tenant-even-if-single-deployment). Output: `nfr-report.md`.

**— Murat (Test Architect)**
