# Stage 3 — Memory & Learning Layer: Consolidated Requirements (Round 2 Hardened)

**Status:** Draft v0.1 — Round 2 elicitation output (BEFORE Winston)
**Pipeline step:** 3.0.2 — `/bmad-cis-problem-solving` (Dr. Quinn)
**Methods applied:** Failure Mode Analysis (primary) + Risk Assessment Matrix (secondary), per Pipeline.md Section 4.5 Quick Reference
**Author role:** Dr. Quinn, Master Problem Solver
**Supersedes:** `requirements-privacy.md` v0.2 (Round 1). Round 1 defaults stand; Round 2 hardens with 43 failure modes and 28 new load-bearing architectural requirements.
**Binding on:** Winston's Stage 3 architecture draft (`memory/architecture.md`). This document is the authoritative input to step 3.1 per Pipeline Section 4.5 rule 2.

---

## Executive Summary

**Failure modes identified:** 43 across 4 Round 1 recommendations + 5 cross-cutting threat categories.

**Risk Priority Number (RPN) distribution:**

| Severity | RPN range | Count | Gate |
|----------|-----------|-------|------|
| **BLOCKER** | ≥ 12 | 28 | Must be mitigated in architecture.md before Amelia begins implementation |
| **CONCERN** | 6–11 | 11 | Must be acknowledged and either mitigated or explicitly deferred with rationale |
| **ACCEPTED** | ≤ 5 | 4 | Documented but no mitigation required |

**Top 5 risks by RPN (all BLOCKERS):**

| # | Failure mode | RPN | Category |
|---|-------------|-----|----------|
| FM1.2 | Shared Postgres across deployments for cost reduction | 20 | Q1 Tenancy |
| FM1.3 | Shared backup infrastructure with cross-tenant IAM misconfiguration | 20 | Q1 Tenancy |
| FM3.1 | Delete cascade misses vector index entries (pgvector orphans) | 20 | Q3 GDPR |
| FM1.4 | Shared telemetry pipeline leaks payload content | 16 | Q1 Tenancy |
| FM2.1 | Seed corpus contains non-redistributable licensed content | 16 | Q2 Seed Corpus |
| FM3.2 | Embedding cache in running process RAM survives delete | 16 | Q3 GDPR |
| FM4.8 | Retrieval-quality telemetry dashboard leaks query content | 16 | Q4 Poisoning |

(7-way tie at positions 4-7 — all require explicit mitigation in architecture.md.)

**Blockers resolved (2026-04-12):** Andrey ratified all 6 BLOCKER open questions. See §"Resolved Blockers" at end of document for the binding decisions. Requirements below are fully unblocked for Winston.

**Does Round 1's posture stand?** **YES — with hardening, not overrides.**

The Stakeholder Round Table converged correctly on all four recommended defaults. FMEA did not overturn any of them. However, FMEA revealed **28 new architectural requirements** that Round 1 did not call out — most are implementation discipline for features Round 1 described at a conceptual level (e.g., "delete cascade exists" → "delete cascade is a durable idempotent job with vector-index post-verification and embedding cache invalidation events"). Treat this document as **Round 1 + 28 amendments**, not as an alternative plan.

**One override of Round 1:** the quarantine operation (Q4) must **strip the embedding in place**, not just flip the state field. Round 1 treated quarantine as state-only; FM3.10 shows that a retained embedding is still personal data subject to inversion attack. Winston's design must treat quarantine as "embedding destroyed, metadata retained for audit."

---

## Scoring Methodology (How to Read the FMEA Tables)

- **Likelihood (L), 1–5:** 1=rare (single industry precedent), 2=uncommon (documented but not frequent), 3=plausible (known failure class in similar systems), 4=common (widely-documented industry failure mode), 5=near-certain (always happens without prevention)
- **Impact (I), 1–5:** 1=cosmetic/internal inconvenience, 2=recoverable in hours with no customer impact, 3=days to recover, customer-facing incident, 4=multi-customer incident OR regulatory exposure, 5=existential (data breach, major regulator fine, loss of customer base)
- **RPN = L × I**
- **Gates:** RPN ≥ 12 is a **BLOCKER** (architecture must mitigate before implementation begins). RPN 6–11 is a **CONCERN** (architecture must acknowledge and either mitigate or defer with rationale). RPN ≤ 5 is **ACCEPTED** (documented without mitigation requirement).

Scoring is adversarial — when in doubt, score toward higher likelihood rather than lower. Round 2 errs on the side of over-inclusion.

---

## Q1 — Tenancy: Single-Tenant-Per-Deployment

### Round 1 Recommendation (Restated)

Ship single-tenant-per-deployment as the only supported mode in v1. Design the unified Memory API to accept `tenant_id` as a required parameter from day one so Phase 2 shared-multi-tenant is a backend swap. Deployment manifest pins tenant_id at install time; startup hard-fails if drift is detected.

### Failure Mode Analysis

| # | Failure mode | Cause | Effect | L | I | RPN | Gate | Mitigation |
|---|-------------|-------|--------|---|---|-----|------|------------|
| **FM1.1** | Deployment manifest drift — a second tenant_id appears in the DB at runtime (ops script, migration, test seed) | Manual DB intervention, leaked test data, ops mistake | Two customers share a DB; one bug away from cross-tenant leak | 3 | 4 | **12** | BLOCKER | Startup check runs on **every** service boot, not just deploy. Startup hashes observed tenant_ids and compares to a signed manifest file. Periodic runtime re-verification every 60s; process exits if drift detected. |
| **FM1.2** | Shared Postgres across deployments for cost reduction — ops co-tenants two customers to save infra cost | Cost pressure at scale | Full cross-tenant leak surface exposed; "single-tenant" claim is false | 4 | 5 | **20** | BLOCKER | Deployment manifest records a cryptographic DB fingerprint `hash(host + port + db_name)`. Process refuses to start if another Praxis instance's manifest registers the same fingerprint (coordination via a manifest registry). Ops MUST provision distinct Postgres instances — no "just point at the shared DB" code path exists. |
| **FM1.3** | Shared backup infrastructure — single S3 bucket / backup server for multiple deployments with cross-tenant IAM misconfiguration | Infra consolidation for cost; IAM policy drift | One IAM misconfig = all backups readable by all tenants | 4 | 5 | **20** | BLOCKER | Backups are tenant-scoped. Each deployment writes to `s3://praxis-backups-{tenant_hash}/` with IAM scoped to the owning tenant only. Backup destination fingerprint verified at restore time. NO shared backup bucket — the configuration path to create one does not exist. See also FM3.3 (crypto-shredding). |
| **FM1.4** | Shared telemetry pipeline — metrics/logs routed to central observability platform with tenant data in payloads | Central ops wants unified dashboards | Query content, embeddings, retrieval results bleed into logs; operator debugging sees other tenants' data | 4 | 4 | **16** | BLOCKER | tenant_id is a dimension in central telemetry; payloads of metrics/logs MUST NOT contain query content, embeddings, retrieval results, or raw memory records. Structured logging schema has an explicit allowlist of sendable fields. Sensitive fields route to a **tenant-local log sink** that never leaves the deployment. CI lint rule: no raw-string log statements in Memory modules. |
| **FM1.5** | Test/staging contamination — dev/QA data seeded into prod via shared image or env misconfig | Image build baking test data; env var points to wrong DB | Prod has test tenant data OR test envs have prod data | 3 | 3 | 9 | CONCERN | Image build forbids embedding any data (tenant-agnostic base image). Prod deployments fail startup if `praxis_environment != 'production'` in config table. CI pipeline has a dedicated test for this failure mode. |
| **FM1.6** | tenant_id in caller-provided metadata — developer adds a metadata field passing tenant_id through, bypassing the facade | Developer convenience, time pressure | Facade enforcement undermined; callers now control effective tenant_id | 3 | 4 | **12** | BLOCKER | Static-analysis rule (CI-enforced): no Memory API method may accept a kwarg whose name contains "tenant". Violation fails CI. Plus: facade validates incoming metadata dicts against an allowlist before persisting. |
| **FM1.7** | Multi-process deployment sharing in-memory state — module-level cache keyed by query hash, not tenant | Poorly-scoped cache | Same query hash returns wrong tenant's cached result | 2 | 3 | 6 | CONCERN | All in-process caches MUST key on `(tenant_id, ...)` tuples. Discipline survives the Phase 2 transition to shared multi-tenant. Unit test enforces. |
| **FM1.8** | Database backup-restore to wrong tenant — during recovery, ops restores backup from deployment A into deployment B | Ops mistake, backup labeling error | Tenant A's data appears in tenant B's retrievals | 3 | 5 | **15** | BLOCKER | Every row in the DB carries a `tenant_hash` column (not just the configured tenant_id). On startup, process scans a sample and fails if `tenant_hash != configured_value`. Restore operations re-validate the entire DB before serving traffic. |
| **FM1.9** | Schema migration run against wrong DB — Alembic migration intended for staging runs against prod | Env misconfig | Data corruption or loss | 3 | 4 | **12** | BLOCKER | Migrations check `tenant_hash` + environment tag before applying; abort if mismatch. Dry-run required before apply in prod. CI has a migration-safety test harness. |
| **FM1.10** | Memory facade exports internal helper that bypasses scope — "for testing" export leaks into prod code | Missing `__all__` discipline | Scoping bypass via direct Mem0/Beads access | 3 | 4 | **12** | BLOCKER | Memory facade module uses `__all__` to restrict exports. Internal helpers live in `_internal/` submodule. CI lint rule: no direct imports from `_internal/` in application code. |

**Q1 total:** 10 failure modes, 7 BLOCKERS, 2 CONCERNS, 1 ACCEPTED (none — actually 2 concerns, which leaves FM1.5 and FM1.7 as CONCERN).

### New Load-Bearing Assumptions for Winston (Q1)

Beyond Round 1's load-bearing assumptions, architecture.md must bake in:

1. **Signed deployment manifest file** recording: tenant_id, tenant_hash, DB fingerprint, environment tag, Praxis version, seed_version, embedding_model_id, signing authority signature. Produced by deploy tooling, verified on every boot and every 60s at runtime.
2. **`tenant_hash` column on every row** in every Memory-owned table. Added by a mandatory base model class. Startup scans a sample and fails on mismatch.
3. **Manifest registry** (lightweight coordination service or shared config) that prevents two deployments from registering the same DB fingerprint.
4. **CI lint rules** enforceable in the repo: (a) no "tenant" kwargs on Memory API methods, (b) no raw-string log statements in Memory modules, (c) no imports from `_internal/` in application code.
5. **Allowlisted telemetry fields** — Memory module exposes a typed `TelemetryEvent` schema with a fixed set of fields; anything else is dropped at emit time, not filtered later.
6. **Tenant-local log sink** — in-deployment logging destination that never exports to central observability. Operators access via explicit authorization and a separate audit trail.
7. **Migration safety harness** — Alembic integration runs `tenant_hash` + environment pre-check as a hook before every apply.

---

## Q2 — Cross-Tenant Learning: Per-Tenant + Shared Seed Corpus

### Round 1 Recommendation (Restated)

Per-tenant experience library + frozen versioned shared seed corpus (~500 curated public/licensed records). No cross-tenant code path exists. Seed corpus is read-only at tenant layer, versioned with `seed_version` hash, refreshed on a named cadence.

### Failure Mode Analysis

| # | Failure mode | Cause | Effect | L | I | RPN | Gate | Mitigation |
|---|-------------|-------|--------|---|---|-----|------|------------|
| **FM2.1** | Seed corpus contains licensed-not-redistributable content — curator added copyrighted material believing it was public | Curation without legal review | Regulatory/legal exposure for Praxis and all customers | 4 | 4 | **16** | BLOCKER | Seed ingest tool requires a `license_attestation` record per entry: provenance URL, license type (public domain / CC0 / CC-BY / Praxis-owned), curator name, attestation date. Records without attestation refuse to ingest. Quarterly refresh has a legal-review gate. |
| **FM2.2** | Seed corpus poisoning at curation — adversarial record injected via insider threat, compromised curator tool, or upstream source compromise | Insider threat or supply-chain compromise | Every tenant retrieving against that record inherits the harm | 2 | 5 | 10 | CONCERN | Seed ingest is content-addressed (each record hashed). Two-person review required for new records. Seed_version bump manifest lists every record added since last version. Anomaly detection on curation cadence. |
| **FM2.3** | Customer data accidentally ingested into seed corpus — curator pastes customer content thinking it was sanitized | Human error, sloppy internal/external boundary | Customer content redistributed to all other customers → GDPR breach | 3 | 5 | **15** | BLOCKER | Seed ingest tool runs on an isolated workstation with no access to customer data stores. Each ingested record is scanned for PII patterns (names, emails, monetary amounts, phone numbers) before commit. Ingestion audit log is reviewable and retained. |
| **FM2.4** | Seed corpus vs tenant collision — tenant record happens to share a hash with a seed corpus record | Hash collision (unlikely with SHA-256) OR Mem0 namespace collision | Tenant can't retrieve own content OR seed reads corrupted | 1 | 3 | 3 | ACCEPTED | Tenant and seed records live in disjoint Mem0 collections with separate namespaces. Document the convention in architecture.md. |
| **FM2.5** | Seed corpus stale → customer retrieval regression — no refresh for 6+ months causes results to mismatch customer queries | Curation cadence slipping in a small team | Customer trust erodes ("your memory is getting worse") | 4 | 3 | **12** | BLOCKER | `seed_version` has an expiry date in the manifest. Retrievals emit a warning metric when serving a stale seed. Dashboards surface corpus age to operators. Refresh is a named role's responsibility with a scheduled recurring ticket. |
| **FM2.6** | Scope enum misuse — developer writes code that passes `scope=SEED_CORPUS` to a write operation | API misunderstanding | Tenant context writes to seed collection, contaminating all tenants | 3 | 5 | **15** | BLOCKER | Memory facade write methods DO NOT accept a `scope` parameter. Scope is inferred from the method name (e.g., `store_task_outcome()` is always TENANT scope). Seed writes are a separate offline tool, not a runtime code path. |
| **FM2.7** | Down-weighting formula bug → seed dominates after N=25 — off-by-one in crossover logic | Formula tuning error | Customer sees "compounding advantage" not compounding; pitch fails | 3 | 3 | 9 | CONCERN | Formula is a pure function with unit + property tests. Telemetry reports source distribution (seed vs tenant) per retrieval. Dashboard flags anomalies. |
| **FM2.8** | `seed_version` hash mismatch after upgrade — new binary has different baked seed; old audit references dangling hash | Poor upgrade discipline | Reproducibility of prior retrievals broken | 4 | 2 | 8 | CONCERN | Seed corpus versions are content-addressed and retained in Beads **indefinitely**. Upgrades pin seed_version forward-compatibly. Old versions remain queryable for audit. |
| **FM2.9** | Embedding provider change invalidates seed corpus — switching embedding models changes retrieval semantics | Cost optimization, vendor migration | Entire seed corpus retrieval quality degrades | 3 | 4 | **12** | BLOCKER | Embedding provider is part of seed_version identity: `seed_version = sha256(content) + embedding_model_id`. Switching providers requires re-embedding the seed and incrementing seed_version. Mixed-provider queries are forbidden. |
| **FM2.10** | Seed corpus download bandwidth — air-gapped deployment fails to fetch seed at startup | Deployment into restricted network | Startup fails | 2 | 2 | 4 | ACCEPTED | Seed corpus bundled in the Praxis distribution image; not fetched at runtime. Air-gapped works by construction. |

**Q2 total:** 10 failure modes, 5 BLOCKERS, 3 CONCERNS, 2 ACCEPTED.

### New Load-Bearing Assumptions for Winston (Q2)

1. **License attestation schema** per seed record: provenance URL, license type, curator name, attestation date, signature. Records without attestation are non-ingestable.
2. **PII scanner in seed ingest tool** — regex + NER pass over every record before commit. Failures block ingest.
3. **`seed_version` composite identity** = `sha256(content_manifest) + embedding_model_id + schema_version`. All three must match for a retrieval to use the pinned version.
4. **Seed corpus versions retained indefinitely in Beads** — never deleted, only superseded. Old audit trail queries still resolve.
5. **Scope is method-implicit, not parameter-explicit** — no write method takes a `scope` parameter; seed writes are a separate offline tool executable.
6. **Quarterly refresh calendar** with a named owner and legal-review gate. Owner role is filled at the operator level, not engineering.
7. **Source-distribution telemetry** — every retrieval emits `retrieved_from: {seed: N, tenant: M}` so dashboards can watch the crossover behavior over time.

---

## Q3 — GDPR: Ready Architecture, Deferred Certification

### Round 1 Recommendation (Restated)

GDPR-ready by construction: `delete(scope, criteria)` cascades across Beads / Mem0 / Atelier / experience library; embeddings are purged as personal data; residency = deployment location; Article 15 access query is a first-class API. DPA template and SOC2 certification deferred until first enterprise ask.

### Failure Mode Analysis

| # | Failure mode | Cause | Effect | L | I | RPN | Gate | Mitigation |
|---|-------------|-------|--------|---|---|-----|------|------------|
| **FM3.1** | Delete cascade misses pgvector index entries — Mem0 row deleted but pgvector index still contains vectors | pgvector separate physical storage; Mem0's delete doesn't always reclaim the index page | Similarity queries return results referencing "deleted" IDs; regulator-visible incompleteness | 4 | 5 | **20** | BLOCKER | Post-delete verification: after cascade, run a query by deleted IDs against the index and confirm zero hits. Integration tests inspect index state directly, not just API-level delete confirmation. Vacuum/reindex is a named step in the delete cascade. |
| **FM3.2** | Embedding cache in running process RAM — Mem0 client holds LRU cache of recently-fetched embeddings; delete removes from DB but not from live processes | Standard client-side caching | Delete returns success while embedding persists in RAM | 4 | 4 | **16** | BLOCKER | Delete operation emits a cache-invalidation event (pub/sub channel) to every running Praxis process. Processes subscribe and purge their caches before acknowledging. Ack aggregation gates the user-facing delete confirmation. |
| **FM3.3** | Backup contains deleted data — backups taken before the delete still hold personal data; standard 30+ day retention | Immutable backup retention | Regulatory ambiguity; incident during audit | 5 | 3 | **15** | BLOCKER | Backups are tenant-scoped (from FM1.3) AND encrypted with a per-tenant key managed by the deployment. Right-to-erasure cascades to **crypto-shredding**: the per-tenant key is destroyed on full-tenant deletion, rendering backups cryptographically inaccessible. For partial (record-level) deletion, backups age out normally under the disclosed retention window. DPA language says: "backups are cryptographically erased within N days." |
| **FM3.4** | LLM provider retention — task calls Anthropic/OpenAI; provider retains prompt for 30 days; Praxis delete doesn't cascade there | Out-of-scope retention | Delete is incomplete; DPA must disclose | 5 | 3 | **15** | BLOCKER | Praxis uses **zero-retention endpoints** by default (Anthropic Zero Data Retention, OpenAI ZDR endpoints). Non-ZDR endpoints are opt-in and gated by a prominent warning + operator acknowledgment. DPA language discloses provider retention clearly. API keys are tenant-scoped (see CC.4). |
| **FM3.5** | Article 15 access query returns other tenants' data — new code path didn't inherit facade's scoping discipline | Access API implemented separately from retrieval | Full tenant leak + regulatory finding | 3 | 5 | **15** | BLOCKER | Access API uses the **same facade** as retrieval. No bypass path, no separate query builder. Integration tests include a "two-tenant access isolation" test class marked CRITICAL. |
| **FM3.6** | Delete-before-create race — user deletes and immediately recreates with same content; in-flight retrieval references deleted ID mid-cascade | Concurrent operations | Retrieval sees a dangling ID or wrong record | 3 | 2 | 6 | CONCERN | Delete cascade runs in a serializable transaction; retrievals see either pre-delete or post-delete state, never a mix. |
| **FM3.7** | Async experience library rewrite leaves window — primary cascade ack'd, async rewrites take minutes, retrieval can surface to-be-deleted entry during window | Async cascade design | Regulatory window where "deleted" data is retrievable | 3 | 3 | 9 | CONCERN | Async rewrites mark affected records as `state=QUARANTINED` **synchronously** (retrieval ignores); full removal happens async. Telemetry reports quarantine-to-delete gap distribution. |
| **FM3.8** | Audit log contains personal data — delete log records criteria like `user_email = alice@example.com` | Audit designed to record matches | Audit-of-audit paradox: deleting the user doesn't delete evidence of the user's identifier | 5 | 3 | **15** | BLOCKER | Audit log records a **salted hash** of criteria, not raw values. Salt retained for statute-of-limitations window (strawman 2 years), then destroyed — log becomes cryptographically anonymous. DPA discloses audit log as a separate data subject record with its own retention policy. |
| **FM3.9** | Partial delete — cascade fails halfway (Beads done, Mem0 pending, Atelier not started); crash leaves inconsistent state | Mid-operation failure | Some stores have the data, some don't; next delete may not re-run missing parts | 3 | 4 | **12** | BLOCKER | Delete cascade is a **durable job** (written to a jobs table before starting). Each sub-step is idempotent and resumable. Crash recovery re-runs pending sub-steps. User delete NOT ack'd until all sub-steps complete. |
| **FM3.10** | Embedding inversion on retained-but-quarantined vectors — quarantined records keep embedding; embedding inversion recovers content | Quarantine preserves state for audit (Lena, Round 1) but embedding is still personal data | "Quarantined" records remain personal data | 3 | 4 | **12** | BLOCKER | **OVERRIDE of Round 1:** quarantine operation STRIPS the embedding in-place (zeros it out). Only ID + state + reason-hash + audit trail survive. Retrieval filters by state; inversion neutralized by embedding destruction. |
| **FM3.11** | Mem0 upstream bug — future Mem0 version has delete bug that leaves graph-store orphans | Upstream dependency risk | Unknown until discovered; reliance on upstream quality | 3 | 4 | **12** | BLOCKER | Pin Mem0 version. Add integration test for delete-then-query-by-id zero-result. Test runs on every CI and every Mem0 version bump. Mem0 upgrades require the test to pass before merging. |

**Q3 total:** 11 failure modes, 8 BLOCKERS, 2 CONCERNS, 1 override of Round 1 (FM3.10).

### New Load-Bearing Assumptions for Winston (Q3)

1. **Vacuum/reindex is part of the delete cascade**, not a separate ops job. Post-delete verification query runs and must return zero hits.
2. **Cache-invalidation pub/sub channel** — delete emits an event; all Praxis processes subscribe and purge caches; ack aggregation gates user-visible delete confirmation.
3. **Per-tenant encryption key for backups** + crypto-shredding on tenant-wide delete. Backup key management is an ops-level responsibility with documented procedures.
4. **Zero-retention endpoints as the default** for all LLM provider calls. Non-ZDR requires an opt-in flag with operator acknowledgment.
5. **Durable delete job** — jobs table + idempotent sub-steps + resume-on-crash. Matches the pattern used in Stage 1 Pi-Mono outbox (cross-reference for consistency).
6. **Salted-hash audit log** — criteria never stored as raw values. Salt destroyed at statute-of-limitations expiry for cryptographic anonymization.
7. **Quarantine strips embeddings in-place** — new constraint; overrides Round 1's "quarantine is state-only" framing. Quarantined records carry (id, state, reason_hash, audit_trail) but no embedding.
8. **Mem0 integration test harness** — delete/query round-trip, two-tenant isolation, schema stability check; runs on every CI and every upstream bump.

---

## Q4 — Poisoning: MAC-Gated Admission + Tentative/Confirmed State Machine

### Round 1 Recommendation (Restated)

MAC-gated admission into a tentative→confirmed state machine, with admin quarantine as escape hatch, SiriuS-style promotion on downstream reuse success, and retrieval-quality telemetry as a named deliverable. No auto-rollback on downstream failure.

### Failure Mode Analysis

| # | Failure mode | Cause | Effect | L | I | RPN | Gate | Mitigation |
|---|-------------|-------|--------|---|---|-----|------|------------|
| **FM4.1** | Adversarial prompt inflates quality_score — task prompt is crafted to game MAC's scoring rubric | Measurement gaming (Goodhart's law) | Junk enters as CONFIRMED, pollutes retrieval | 3 | 4 | **12** | BLOCKER | Admission gate uses composite signal: `quality_score` + semantic novelty + historical tenant admission rate. Outlier detection (too many high-score admissions from one tenant in a short window) triggers rate-limiting + manual review queue. |
| **FM4.2** | MAC score uncalibrated for new task type — distribution shift when new task class first appears | Distribution shift in inputs | Library quality degrades silently | 4 | 3 | **12** | BLOCKER | Admission requires both `quality_score` above threshold AND `quality_confidence` above a minimum. Low-confidence scores default to TENTATIVE even when quality value is high. MAC publishes confidence alongside score. |
| **FM4.3** | Tentative pool unbounded — tentative entries accumulate; retrieval performance degrades; storage bloats | Low reuse rate on tentative entries | p99 retrieval latency creeps up; storage cost grows | 4 | 3 | **12** | BLOCKER | Tentative entries have a max lifetime (strawman 90 days). After expiry, non-promoted tentative entries demote to `state=EXPIRED` (invisible to retrieval, retained for audit until retention policy expiry). Expiry job is a named recurring task. |
| **FM4.4** | Adversarial reuse to promote bad entries — user deliberately reuses a known-bad tentative to trigger promotion | Insider threat or user error | Bad entry promoted to CONFIRMED | 2 | 4 | 8 | CONCERN | Promotion requires the reusing task's own `quality_score ≥ 0.8` AND (where principal data exists) a different principal than the original author. Adds a liveness requirement, removes trivial self-promotion. |
| **FM4.5** | Quarantine reason field as leakage vector — admin enters "customer X complained about leaked acquisition plans" in the reason field; audit log now contains that sentence | Free-form sensitive text input | Audit log contains personal/confidential data (see FM3.8) | 3 | 3 | 9 | CONCERN | Quarantine reason is a **structured enum** (PII_LEAK, HALLUCINATION, OUTDATED, POISONED, OTHER) + optional hashed free-text field. Free-text is scrubbed of PII patterns before storage. |
| **FM4.6** | Quarantine as deletion shortcut — admin quarantines records for a DSAR expecting them to be gone; doesn't realize quarantine retains them | UX confusion between quarantine and delete | User expects delete, data persists, GDPR non-compliance for DSAR responses | 4 | 3 | **12** | BLOCKER | Quarantine and delete APIs are documented with prominent "quarantine is reversible, delete is permanent" warnings. Admin tooling presents both options with clear visual/verbal differentiation. **DSAR-handling runbook explicitly mandates delete, not quarantine.** |
| **FM4.7** | Reuse-success signal lag confuses retrieval — tentative entry retrieved today; confirmation signal takes 7 days; same query returns different results across time | Async promotion lifecycle | Non-deterministic results across days without user understanding | 4 | 2 | 8 | CONCERN | Retrieval API returns `state_snapshot_version` timestamp; users can re-run pinned to a version for determinism. Documentation explicitly describes the async lifecycle. |
| **FM4.8** | Retrieval-quality telemetry dashboard leaks content — dashboards include example queries/results for debugging | Debug-dashboard convenience | Operator sees customer query content | 4 | 4 | **16** | BLOCKER | Telemetry metrics are numeric/aggregate only. Example queries are NEVER in the central telemetry pipeline. Debugging requires a **separate tenant-local log sink** (from FM1.4) accessed with explicit authorization + audit trail. Dashboard enforces schema at emission, not display. |
| **FM4.9** | `state` column tampering — DBA updates `state=CONFIRMED` directly in the DB, bypassing MAC gate | DBA intervention for "quick fix" | Unauthorized promotions skew retrieval | 3 | 4 | **12** | BLOCKER | State transitions enforced by DB triggers that verify source (must be via Memory facade's state-change API, authenticated with a service credential). Direct UPDATE statements fail unless operator presents a break-glass credential audit-logged to a write-only ledger. |
| **FM4.10** | MAC absent → all-tentative mode never cleaned — Stage 5 ships late; Memory runs all-tentative; MAC arrival doesn't retroactively score | Staged rollout | Legacy tentative pool never gets promoted | 4 | 2 | 8 | CONCERN | MAC rollout includes a **backfill job** that scores all existing entries. Backfill is a named deliverable in Stage 5's handoff contract with Memory. Not an assumption. |
| **FM4.11** | Promotion race — two concurrent downstream tasks both retrieve and report success; both try to promote | Concurrency | Possible double-accounting of promotion counts | 3 | 1 | 3 | ACCEPTED | State transitions are idempotent (CONFIRMED is terminal; re-promotion is a no-op). Counter increments use atomic DB operations. |
| **FM4.12** | Retrieval-quality regression from quarantine cascade — quarantining a popular entry doesn't immediately invalidate downstream caches | Downstream caching lag | Dashboard shows degradation; users see stale retrievals | 3 | 2 | 6 | CONCERN | Quarantine emits a cache-invalidation event (same pattern as FM3.2 delete). Downstream caches subscribe. |

**Q4 total:** 12 failure modes, 6 BLOCKERS, 5 CONCERNS, 1 ACCEPTED.

### New Load-Bearing Assumptions for Winston (Q4)

1. **Composite admission signal** — not just `quality_score`, but also `quality_confidence` and semantic-novelty outlier detection. MAC must publish both score and confidence.
2. **Tentative entries have max lifetime** (strawman 90 days). Expiry demotes to `state=EXPIRED`, not deletion.
3. **Structured quarantine reason enum** + optional PII-scrubbed free-text field. Free-form strings are not stored raw.
4. **Quarantine ≠ delete** is documented at API boundary AND in the DSAR-handling runbook. Admin tooling surfaces both with clear differentiation.
5. **`state_snapshot_version` in retrieval responses** — enables deterministic replay for users who need it.
6. **DB triggers enforce state transitions** — direct UPDATE statements fail without a break-glass credential. Break-glass use is audit-logged to a write-only ledger.
7. **MAC → Memory backfill job** as a named deliverable in the Stage 5 handoff contract.
8. **Quarantine invalidation event** mirrors delete invalidation (FM3.2 pattern).

---

## Cross-Cutting Threats

Threats whose mitigation spans multiple Round 1 recommendations. Each cross-cutting threat has a single unified architectural requirement that Winston must call out by name.

### CC.1 — Observability Pipeline (spans Q1 + Q3)

Covered by FM1.4 (telemetry payload leak) + FM3.8 (audit log PII) + FM4.8 (dashboard query leakage). **Unified requirement:** every log / metric / trace / dashboard emitter in the Memory module uses a typed `TelemetryEvent` schema with an allowlist of fields. The Memory module has zero raw-string logging. A tenant-local log sink exists for debug detail; it never exports to central observability.

### CC.2 — Backup Infrastructure (spans Q1 + Q3)

Covered by FM1.3 (shared backups) + FM3.3 (backups contain deleted data). **Unified mitigation:** backups are tenant-scoped, per-tenant-encrypted, crypto-shred on full-tenant deletion. Backup destination fingerprinting prevents cross-tenant access. DPA language references the crypto-shredding timeline.

### CC.3 — Mem0 Upstream Dependency (spans Q1 + Q3 + Q4)

Covered by FM3.11 (delete bug) + implicit risk in Q1 scoping + Q4 schema stability. **Unified requirement:** a Mem0 integration test harness runs on every CI and every upstream bump. Tests cover: (a) two-tenant isolation, (b) delete-then-query-by-id returns zero, (c) schema stability (no backward-incompatible field changes without detection), (d) retrieval semantics regression guard (a canonical query set with pinned expected top-K).

### CC.4 — LLM Provider API Keys (spans Q1 + Q3)

Covered by FM3.4 (provider retention) with additional Q1 implication: if Praxis uses a shared Anthropic/OpenAI org account across deployments, provider-side metadata could cross-tenant-attribute. **Unified requirement:** **API keys are tenant-scoped — each deployment uses its own Anthropic/OpenAI credentials, not a shared Praxis org account.** This is a major ops implication: operators must provision keys per deployment. Deployment manifest includes the provider key identifier. Tenant-local cost attribution (Stage 1 Pi-Mono) uses the per-deployment keys for reconciliation.

### CC.5 — Deployment Manifest Integrity (spans Q1 + Q3 + Q4)

Covered by FM1.1, FM1.2, FM1.8, FM1.9 and implied residency claim in Q3. **Unified requirement:** the deployment manifest is **cryptographically signed** by Praxis's deploy tooling and verified at runtime. The manifest records: `tenant_id`, `tenant_hash`, DB fingerprint, environment tag, Praxis version, seed_version, embedding_model_id, provider key identifier, backup destination fingerprint, signing authority signature. Tampering or drift = hard-fail on next boot or next 60s verification tick.

---

## Consolidated Final Requirements List (Binding on Winston)

This section is the flattened, numbered, binding input to `/bmad-agent-architect` step 3.1. It replaces `requirements-privacy.md` as the authoritative elicitation output per Pipeline.md Section 4.5 rules. Winston MUST reference these requirements (by number) in `architecture.md`.

### Part A — Tenancy & Isolation

1. Unified Memory API accepts `tenant_id` as a required parameter on every store/retrieve/delete/export/quarantine call. Backends reject calls where `tenant_id` ≠ deployment-pinned tenant identity.
2. Beads worktrees, Mem0 collections, and Atelier decision records inherit `tenant_id` from the Memory facade's deployment config, never from the caller.
3. Deployment manifest is cryptographically signed by the Praxis deploy tool. Manifest records tenant_id, tenant_hash, DB fingerprint, environment tag, Praxis version, seed_version, embedding_model_id, provider key identifier, backup destination fingerprint, signing authority signature.
4. Manifest verification runs on every service boot AND every 60s at runtime. Process hard-fails on drift or signature mismatch.
5. Manifest registry (lightweight coordination service) prevents two deployments from registering the same DB fingerprint.
6. Every row in every Memory-owned table carries a `tenant_hash` column via a mandatory base model class. Startup scans a sample and fails on mismatch.
7. No Memory API method accepts a kwarg whose name contains "tenant". CI lint rule enforces.
8. No Memory API method exposes a raw query builder. All retrieval paths are named typed methods on the facade.
9. Memory facade uses `__all__` to restrict exports. Internal helpers live in `_internal/` submodule. CI lint rule forbids imports from `_internal/` in application code.
10. In-process caches key on `(tenant_id, ...)` tuples even in single-tenant-per-deployment mode.
11. Cross-tenant retrieval is a non-existent code path — not a feature flag, not a config toggle, not reachable from any caller.

### Part B — Scope, Seed Corpus, and First-Session Value

12. Memory facade has a `scope` enum `{TENANT, SEED_CORPUS}`. Writes always go to TENANT (method-implicit, never parameter-explicit). Reads query both by default.
13. Seed corpus is a separate Mem0 collection, read-only at tenant layer. Zero code paths allow tenant-context writes to SEED_CORPUS.
14. Seed corpus identity is `sha256(content_manifest) + embedding_model_id + schema_version`. Switching embedding providers requires re-embedding and a seed_version bump.
15. Seed corpus versions are retained indefinitely in Beads; upgrades pin forward-compatibly; old versions remain queryable for audit.
16. Seed corpus ingest is a separate offline tool, run on an isolated workstation. Runtime service has no seed-write code path.
17. Seed ingest tool requires per-record license attestation (provenance URL, license type, curator name, attestation date, signature). Unattested records refuse to ingest.
18. Seed ingest tool runs a PII scanner (regex + NER) on every record before commit. Failures block ingest.
19. Seed corpus refresh has a named owner role and a legal-review gate per refresh cycle (strawman quarterly).
20. `seed_version` expiry date is stored in the manifest; retrievals emit a warning metric when serving stale content.
21. Seed corpus is bundled in the Praxis distribution image, not fetched at runtime.
22. Every retrieval emits a source-distribution telemetry event `{seed: N, tenant: M}` so operators observe the tenant-vs-seed crossover.
23. Seed vs tenant crossover (down-weight seed after N tenant records) is a pure function with unit + property tests. Strawman N=25, tunable per deployment.

### Part C — Deletion, Access, and GDPR Compliance

24. Unified Memory API exposes `delete(scope, criteria)` that cascades across Beads → Mem0 → Atelier → experience library. Cascade order is deterministic.
25. Delete cascade is a durable job (written to a jobs table before starting). Each sub-step is idempotent. Crash recovery re-runs pending sub-steps. User delete is NOT acknowledged until all sub-steps complete.
26. Delete cascade includes vacuum/reindex as a named step and runs a post-delete verification query (by deleted IDs) confirming zero index hits.
27. Delete operation emits a cache-invalidation event to all running Praxis processes via pub/sub. Processes subscribe, purge caches, and acknowledge. Ack aggregation gates the user-visible delete confirmation.
28. Async experience library rewrites mark affected records as `state=QUARANTINED` **synchronously**; full removal happens async. Quarantine-to-delete gap is telemetered.
29. Backups are tenant-scoped, per-tenant-encrypted. Full-tenant deletion triggers crypto-shredding of the per-tenant backup key. DPA discloses the crypto-shredding window.
30. Praxis uses zero-retention LLM provider endpoints by default. Non-ZDR endpoints require explicit opt-in with operator acknowledgment.
31. API keys for LLM providers are **tenant-scoped** — each deployment uses its own credentials, not a shared Praxis org account. Manifest records the provider key identifier.
32. Unified Memory API exposes `export(scope, criteria)` implementing GDPR Article 15 right-to-access. Uses the same facade as retrieval. CLI-exposed in v1; programmatic surface optional for Stage 6 (see open question Q3-d).
33. Audit log records a **salted hash** of delete/access criteria, not raw values. Salt is retained for statute-of-limitations window (strawman 2 years, configurable), then destroyed.
34. Embeddings are personal data. Delete cascades purge embeddings synchronously within the delete call.
35. Quarantine operation STRIPS the embedding in-place (zeros it). Quarantined records retain only (id, state, reason_hash, audit_trail). (Override of Round 1's "state-only" framing.)
36. Default residency = deployment location. No cross-region replication, no automatic backups to other regions.
37. Right-to-access API and delete API use identical facade scoping discipline. Integration tests include a two-tenant access isolation test marked CRITICAL.

### Part D — Experience Library, Admission, and Governance

38. Every experience library entry has a `state` field: `{tentative, confirmed, quarantined, expired}`. State is a first-class column.
39. Admission gate uses composite signal: `quality_score` + `quality_confidence` + semantic novelty + tenant admission rate outlier detection. MAC publishes both score and confidence.
40. Admission thresholds: `quality_score ≥ 0.8 AND confidence ≥ C_min` → CONFIRMED; `0.5 ≤ quality_score < 0.8 OR confidence < C_min` → TENTATIVE; `quality_score < 0.5` → REJECTED. Thresholds are configuration, not hard-coded.
41. Tentative entries have max lifetime (strawman 90 days). Expiry demotes to `state=EXPIRED` (invisible to retrieval, retained for audit until retention policy expiry).
42. Promotion from TENTATIVE to CONFIRMED requires: entry is retrieved AND reused in a downstream task AND that task's own `quality_score ≥ 0.8` AND (where principal data exists) the reusing principal differs from the original author.
43. Retrieval weighting formula is explicit in architecture.md:
    `score = semantic_similarity × recency_decay(age) × state_weight(state) × quality_score^alpha`
    with `state_weight`: CONFIRMED=1.0, TENTATIVE=0.5, QUARANTINED=0.0, EXPIRED=0.0. `alpha ≈ 0.5`, tunable.
44. Retrieval API returns `state_snapshot_version` timestamp enabling deterministic replay.
45. `flag_and_quarantine(entry_id, reason_enum, free_text)` is a reversible state transition. `reason_enum` is structured: `{PII_LEAK, HALLUCINATION, OUTDATED, POISONED, OTHER}`. Free-text is PII-scrubbed before storage.
46. Quarantine ≠ delete. API docs, admin tooling UX, and DSAR runbook explicitly differentiate them.
47. DB triggers enforce state-column transitions. Direct UPDATE statements fail unless accompanied by a break-glass credential audit-logged to a write-only ledger.
48. MAC → Memory backfill job (re-scores existing tentative entries when MAC ships) is a named deliverable in the Stage 5 handoff contract. Not assumed.
49. In MAC-absent mode, Memory admits all entries as TENTATIVE with explicit logging of the degraded state.
50. Quarantine emits a cache-invalidation event (same pattern as delete).

### Part E — Observability, Telemetry, and Cross-Cutting

51. Memory module exposes a typed `TelemetryEvent` schema with an allowlist of sendable fields. Anything else is dropped at emit time.
52. Memory module contains zero raw-string log statements. CI lint rule enforces.
53. Central observability pipeline receives ONLY numeric/aggregate metrics and allowlisted structured fields. Query content, embeddings, retrieval results, and raw memory records are NEVER transmitted to central observability.
54. Tenant-local log sink exists for debug detail. Operators access it with explicit authorization; access is audit-logged.
55. Required telemetry metrics: admission rate, rejection rate, tentative-to-confirmed conversion rate, retrieval score distribution, p99 retrieval latency, source distribution (seed vs tenant), `seed_version` age, delete cascade duration, quarantine-to-delete gap, cache invalidation ack latency.
56. Retrieval-quality telemetry dashboard is operator-facing by default. Customer-facing surfacing is a Stage 6/7 decision (see open question Q4-d).
57. Memory integrates with Pi-Mono (Stage 1) as a cost attribution source. Retrievals emit `CostEvent` of type `retrieval_cache_hit` with savings attribution. Delete cascades emit `CostEvent` of type `retention_action`.
58. Mem0 integration test harness runs on every CI and every Mem0 upstream bump. Tests: two-tenant isolation, delete-then-query-by-id zero-result, schema stability (backward-compat detection), retrieval semantics regression guard.

---

## Delta from Round 1 (Explicit Diff)

**Unchanged (Round 1 defaults stand):**
- Q1 single-tenant-per-deployment
- Q2 per-tenant experience library + shared seed corpus
- Q3 GDPR-ready / deferred certification
- Q4 MAC-gated admission / tentative→confirmed / admin quarantine

**Added (new requirements not in Round 1):**
- Signed deployment manifest + registry + 60s runtime re-verification (FM1.1, 1.2)
- `tenant_hash` column on every row (FM1.8)
- CI lint rules for tenant kwarg, raw-string logs, internal imports (FM1.6, 1.4, 1.10)
- Tenant-scoped backups with per-tenant encryption + crypto-shredding (FM1.3, 3.3)
- Tenant-local log sink (FM1.4)
- License attestation + PII scanner in seed ingest (FM2.1, 2.3)
- `seed_version` composite identity (content + embedding_model_id + schema_version) (FM2.9)
- Seed_version expiry warning telemetry (FM2.5)
- Source-distribution retrieval telemetry (FM2.7)
- Durable delete job with resumable sub-steps (FM3.9)
- Post-delete vector-index verification + vacuum/reindex in cascade (FM3.1)
- Cache-invalidation pub/sub for delete AND quarantine (FM3.2, 4.12)
- Zero-retention LLM endpoints default + tenant-scoped API keys (FM3.4, CC.4)
- Salted-hash audit log (FM3.8)
- `export()` API for GDPR Article 15 (Round 1 surfaced this; Round 2 elevates to binding)
- Composite admission signal with `quality_confidence` (FM4.1, 4.2)
- Tentative max-lifetime + EXPIRED state (FM4.3)
- Structured quarantine reason enum + PII-scrubbed free-text (FM4.5)
- `state_snapshot_version` for deterministic retrieval replay (FM4.7)
- DB triggers + break-glass ledger for state transitions (FM4.9)
- MAC backfill job as a named Stage 5 deliverable (FM4.10)
- Typed `TelemetryEvent` schema with allowlist (CC.1, FM4.8)

**Overridden from Round 1:**
- **Quarantine now strips embeddings** (FM3.10). Round 1 treated quarantine as state-only; Round 2 requires in-place embedding destruction to neutralize inversion attack.

**Nothing removed.** Round 1's recommendations are all preserved.

---

## Updated Open Questions for Andrey (13 + 7 new)

Each question is tagged with severity and ordered by blocking priority.

### BLOCKER — Answer before Winston begins (step 3.1)

| # | Question | Why it blocks |
|---|----------|---------------|
| **B1** | Q1-a: Target early customer deployment posture — on-prem VPC, managed single-tenant (Praxis hosts one instance per customer), or shared SaaS? | Determines whether Phase 2 shared-multi-tenant is ever built and whether Praxis needs BYO-KMS support. |
| **B2** | Q3-c: Confirm embedding-as-personal-data stance. Round 2 treats embeddings as personal data and requires in-place destruction on both delete and quarantine. | Determines Mem0 delete cascade design and quarantine operation. Softening this invalidates FM3.10's mitigation. |
| **B3** | **NEW:** Manifest registry — is this a lightweight coordination service Praxis provides, or a shared config file on deployment infrastructure? | Changes architecture for FM1.2 (shared Postgres prevention). |
| **B4** | **NEW:** LLM provider API keys — confirm tenant-scoped per-deployment is acceptable (ops burden) vs a shared Praxis org account (convenience but creates FM3.4 risk). | Major ops implication; reversing later is expensive. |
| **B5** | **NEW:** Backup strategy — accept per-tenant encryption + crypto-shredding as the standard? Some operators will prefer standard object-storage retention. | Determines FM3.3 mitigation and DPA language. |
| **B6** | Q2-a: Does the seed corpus exist, or is it a Stage 6 Studio deliverable? | Winston needs to know whether to design the ingest pipeline only or to also specify content curation protocol. |

### CONCERN — Answer before Stage 3 completes

| # | Question | Why |
|---|----------|-----|
| **C1** | Q1-b: Is single-tenant-per-deployment compatible with the Stage 7 pricing model? | Flags pricing/architecture mismatch if any. |
| **C2** | Q2-b: Seed corpus licensing sign-off authority — who at Praxis can attest? | Required for the license_attestation schema (FM2.1). |
| **C3** | Q2-c: Any customer segment where cross-tenant learning is a required feature? | Confirms Option C is definitive. |
| **C4** | Q3-a: Accept the DPA template gap for Stage 7? Budget 1-2 weeks legal drafting when first prospect asks? | Sales posture for Stage 7. |
| **C5** | Q3-b: Audit log retention default — 2 years (strawman) or longer? | Deployment defaults. |
| **C6** | Q3-d: GDPR Article 15 access API — CLI-only in v1, or programmatic surface for Stage 6? | API surface scope. |
| **C7** | Q4-a: MAC threshold calibration — dedicated Stage 5 elicitation round, or Winston uses 0.8/0.5 as strawman? | Stage 5 prompt scoping. |
| **C8** | Q4-b: Quarantine admin surface — CLI/API in v1, or UI requirement? | Stage 6 Studio dependency. |
| **C9** | Q4-c: Reuse-success signal 7-day async lifecycle acceptable? | MAC → Memory contract timing. |
| **C10** | Q4-d: Library-health dashboard — operator-only or customer-facing? | Stage 6 + Stage 7 scoping. |
| **C11** | **NEW:** Tentative entry max-lifetime — 90 days (strawman) acceptable? Some workflows take longer to produce reuse signal. | Tunable but default matters. |
| **C12** | **NEW:** Break-glass credential for DB state-column writes — who holds it, what audit process around its use? | Ops procedure. |
| **C13** | **NEW:** `quality_confidence` signal from MAC — does Stage 5 design include this as a published output, or does Memory need to request it? | MAC → Memory contract. |

### NICE-TO-HAVE — Answer opportunistically

| # | Question | Why |
|---|----------|-----|
| **N1** | **NEW:** Central observability platform — which one are we targeting (Honeycomb, Datadog, custom)? | Only matters for the allowlist schema details. |
| **N2** | **NEW:** Article 15 access export format — JSON? Markdown? Both? | Stage 6 Studio decision more than Stage 3. |
| **N3** | **NEW:** Seed corpus quarterly refresh cadence — confirm or adjust? | Operator calendar. |
| **N4** | **NEW:** Manifest signing authority — who owns the signing key, how is it rotated? | Ops procedure. |

---

## Stage 5 Dependency Summary (What Memory Needs from MAC)

Consolidated from Part D requirements so Stage 5's prompt can explicitly commit:

1. **`quality_score`** per completed task (0.0–1.0).
2. **`quality_confidence`** per completed task (0.0–1.0). Not just the score.
3. **Reuse-success signal** — when a downstream task retrieves a tentative entry AND the downstream task's own `quality_score ≥ 0.8`, MAC publishes a `memory.reuse_successful(entry_id, downstream_quality_score, downstream_principal)` event.
4. **Backfill job** — when MAC first ships, run a one-time pass re-scoring existing tentative entries in the library.
5. **Distribution-shift detection** — when a new task class appears and MAC's confidence drops below C_min, Memory should observe this via the confidence signal and default new admissions to TENTATIVE.

---

## What Winston Should Read Before Drafting `architecture.md`

1. **This document (`requirements.md`)** — the 58 consolidated requirements + FMEA + Stage 5 dependency summary are authoritative.
2. **`requirements-privacy.md`** (Round 1) — for the multi-persona debate context behind the recommendations. Not binding anymore; binding has shifted to this document.
3. **Stage 1 (`pi-mono/architecture.md`)** — CostEvent contract, outbox pattern (mirror in delete cascade), telemetry conventions.
4. **Stage 2 (`compression/architecture.md`)** §3.3 RTK polyglot boundary — Forge compaction of Beads state uses same subprocess-wrapper contract.
5. **Stage 2 `alignment-review.md`** §6 — integration contracts, `tenant_id` propagation through compression layer is new work.
6. **Mem0 reference dump** — per Pipeline's "Universal Sequential Reference Reading" rule, read one reference at a time; do NOT load Beads + Mem0 + Atelier simultaneously.

---

## Method Notes

**Why FMEA + Risk Assessment Matrix (not the skill's 9-step workflow):** Pipeline.md Section 4.5 Quick Reference prescribes these two methods explicitly for Stage 3 Round 2. The bmad-cis-problem-solving skill's generic 9-step interactive facilitation workflow is designed for live problem diagnosis with user interaction; it's a mismatch for an adversarial audit of a concrete pre-existing document. Dr. Quinn applied the prescribed methods directly, producing this document as a single deliverable — the same pattern Round 1 used with Stakeholder Round Table.

**Adversarial discipline:** FMEA was run with a bias toward higher-likelihood scoring (when uncertain, scored up not down). Mitigations are concrete architectural requirements, copy-pasteable into architecture.md, not "be careful" exhortations. Round 1's defaults were tested by attack, not rubber-stamped.

**Override discipline:** only one Round 1 position was overridden (FM3.10, quarantine must strip embeddings). All other Round 1 recommendations stand as-is, with Round 2 adding implementation constraints Winston must honor.

---

---

## Resolved Blockers (2026-04-12 — Andrey Ratification)

All 6 BLOCKER open questions from Round 2 were ratified with the decisions below. Each decision is binding on Winston. Rationale is recorded here so future sessions understand *why*, not just *what*.

### B1 — Deployment Posture → **Managed Single-Tenant**

**Decision:** Managed single-tenant. Each customer gets an isolated deployment (Postgres + pgvector + worker containers + encryption keys) that Praxis hosts and operates. **NOT** on-prem VPC (operational suicide for solo founder). **NOT** shared SaaS (FMEA already ruled out via FM1.2–FM1.4 totaling RPN 56).

**Rationale:**
- Eliminates the top 3 blockers (FM1.2 shared Postgres, FM1.3 shared backups, FM1.4 shared telemetry) by construction — the shared-infra code paths simply don't exist.
- Managed (vs on-prem) keeps Praxis in control of updates, debugging, and ops without customer infrastructure entanglement.
- Sales motion becomes: "Praxis Studio runs in a sandbox dedicated to your org." Matches the Stage 6/7 positioning.
- Consistent with the Round 4 red team (Tokonomics): start at POV scale, not venture scale.

**Implications for Winston (binding):**
- **No `tenant_id` scoping at the query layer.** The tenant boundary is the Postgres instance itself. `tenant_id` remains a required parameter on the Memory facade (per Requirement #1) as a defense-in-depth + Phase 2 option, but the enforcement model is structural, not WHERE-clause-based.
- **Deployment provisioning is a first-class operation.** Terraform/Pulumi/Docker Compose per-customer topology is part of the Stage 7 POV Harness work, but the *per-deployment manifest* and the boot-time verification (Requirements #3–#5) are Stage 3 responsibilities.
- **Simplified code, stronger guarantee.** Winston can design the Memory facade assuming exactly one tenant per process lifetime. All caches, connection pools, and Beads worktrees are scoped at the process level.
- **One-way door after customer #1.** Once the first customer is live under this model, flipping to shared multi-tenant is a rebuild, not a refactor. Winston should NOT design "shared-ready" abstractions — they add cost now for a future that may never arrive.

**Reversibility:** One-way door after customer #1. Committed.

### B2 — Embeddings Are Personal Data → **YES, Confirmed**

**Decision:** Treat embeddings as personal data under GDPR, HIPAA, and SOC 2 analysis. This ratifies the FM3.10 override and the Round 2 delete-cascade posture.

**Rationale:**
- EDPB guidance and CNIL (France) explicitly treat ML embeddings derived from personal data as personal data.
- Model inversion attacks can reconstruct source text from embeddings — this is a real attack vector in 2025–2026 literature (Dr. Ito's ETH Zurich citation from Round 1 stands).
- Conservative stance is defensible under all three frameworks Praxis will eventually need.
- The cost (delete/quarantine must strip embeddings from pgvector + in-memory caches + backups) is architectural, not ongoing operational burden.

**Implications for Winston (binding):**
- **Requirement #34** (embeddings purged synchronously on delete) is authoritative.
- **Requirement #35** (quarantine strips embedding in-place) is authoritative. Quarantined records retain only `(id, state, reason_hash, audit_trail)`.
- **FM3.1** mitigation (pgvector post-delete verification) is non-negotiable.
- **FM3.2** mitigation (cache-invalidation pub/sub on delete) is non-negotiable.
- Backup strategy (B5 below) must honor this: backups containing embeddings are personal data and require crypto-shreddable encryption.

**Reversibility:** One-way door under GDPR.

### B3 — Manifest Registry → **Git-Backed Config File (NOT a service)**

**Decision:** Shared config file on Git infrastructure. Each deployment pulls its manifest from a private GitHub repository at boot via read-only deploy key. **NOT** a lightweight coordination service — solo founder has no time to operate a second service.

**Rationale:**
- Git gives version control, audit trail, rollback, and PR review for free.
- Agent manifest, tool catalog, quality gate configs, per-deployment manifest — all YAML in one repo.
- Migration path preserved: if Praxis hits >10 customers and needs dynamic updates, converting to a service is a transport change, not a data-model change.

**Structure (reference for Winston):**
```
praxis-config/          ← private GitHub repo (read-only deploy key per deployment)
├── deployments/
│   └── {tenant_hash}.yaml       # signed deployment manifest (per-tenant)
├── agents/
│   └── agent-manifest.yaml
├── tools/
│   └── tool-catalog.yaml
├── gates/
│   └── quality-gates.yaml
└── versions/
    └── 2026-04-12-v1.lock
```

**Implications for Winston (binding):**
- **Requirement #3** (signed deployment manifest) is now implemented as a YAML file committed to Git with a signature field generated by the Praxis deploy tool. Verification at boot is: (1) clone manifest from Git at deploy_key-authenticated URL, (2) verify signature, (3) compare `tenant_hash` / DB fingerprint / etc. to actual runtime state, (4) hard-fail on mismatch.
- **Requirement #5** (manifest registry prevents duplicate DB fingerprints) is now: "Git pre-commit/PR-review enforcement — no two deployment YAMLs in `praxis-config/deployments/` may share a DB fingerprint. Enforcement is a CI check on the config repo, not a runtime service."
- **Requirement #4** (60s runtime re-verification) remains: process periodically re-pulls its manifest from Git and hard-fails on drift. The Git URL + deploy key are pinned at process startup.

**Reversibility:** Fully reversible. If Praxis later needs dynamic manifest updates, swap Git fetch for service RPC without changing the manifest schema or verification logic.

### B4 — LLM Provider API Keys → **Tenant-Scoped Default; Managed Billing Deferred**

**Decision:** Tenant-scoped API keys by default. Each customer brings their own Anthropic/OpenAI credentials. **NOT** a shared Praxis org account. Managed billing ("Praxis holds the keys, marks up 25%") is a **future tier, not MVP**.

**Rationale:**
- FM3.4 risk (shared key leak affects all tenants) is eliminated entirely.
- Matches the "customer owns their LLM relationship" narrative — enterprise customers want audit trails + existing contracts + credits.
- Removes Stripe ↔ LLM cost reconciliation from the Stage 7 Shell scope (huge simplification for a solo operator). Stripe charges only the Praxis orchestration fee ($500–$2000/session), customer sees their own Anthropic/OpenAI invoice directly.
- SMBs who balk at BYO keys are explicitly NOT the ICP for first POVs.

**Implications for Winston (binding):**
- **Requirement #31** (API keys are tenant-scoped, manifest records provider key identifier) is authoritative.
- **Per-tenant encrypted secrets** for key storage. Key material NEVER lives in shared Praxis infrastructure, even temporarily.
- **Pi-Mono integration semantic clarified:** Pi-Mono tracks usage per tenant for **reporting and observability only, NOT for billing reconciliation**. The customer's own provider invoice is the billing source of truth. Praxis's own invoice (via Stripe) covers orchestration fee only.
- **Stage 7 handoff implication:** the Shell's Stripe integration is scoped to orchestration-fee billing. No LLM-cost passthrough logic in v1. Add a note to the Stage 7 prompt when it's being drafted.
- **Sales positioning:** "Bring your own Anthropic/OpenAI keys. Praxis orchestrates; you own the LLM relationship and billing." This is a feature, not a friction.

**Reversibility:** Reversible but disruptive. Adding "Managed Billing" tier later is a new product tier, not a migration — existing BYO-key customers stay on their plan.

### B5 — Backup Strategy → **Per-Tenant Encryption + Crypto-Shredding**

**Decision:** Per-tenant encryption key for all backups. Full-tenant deletion triggers crypto-shredding (destroy the per-tenant key → backups cryptographically unrecoverable forever).

**Rationale:**
- Natural fit with B1 (managed single-tenant) — each deployment already has its own key material.
- True GDPR deletion: destroying the key proves data unrecoverable, satisfies "within reasonable time" requirement without fighting backup retention windows.
- Cross-tenant backup deduplication would be a premature optimization with catastrophic failure modes; by ruling it out, we simplify the delete workflow.
- Standard enterprise SaaS practice (AWS KMS / GCP Cloud KMS / HashiCorp Vault).
- Solo-operator maintenance story: "Customer X churns → destroy their key → nothing to clean up."

**Implications for Winston (binding):**
- **Requirement #29** (tenant-scoped encrypted backups + crypto-shredding on full-tenant delete) is authoritative.
- **KMS integration** is a named architecture component. Default backend: AWS KMS or HashiCorp Vault (Winston to select based on operational complexity). Abstract behind a `KeyManager` interface so alternative backends are possible.
- **Key rotation policy:** rotate on customer request AND on schedule (strawman annually). Rotation is a named operation on the KeyManager interface.
- **Delete workflow:** `confirmed_by_customer → destroy_key → wipe_infrastructure → audit_log`. The audit log entry is salted-hashed per Requirement #33.
- **DPA language** (produced on-demand per Round 1 Q3): "backups are cryptographically erased within N days of account termination. The encryption key is destroyed at termination; remaining ciphertext is mathematically unrecoverable."

**Reversibility:** One-way door for backups of existing data (you can't ungrind the crypto-shred).

### B6 — Seed Corpus → **Use Existing BMAD + Tokonomics NOW; Stage 6 Augments**

**Decision:** Bootstrap the seed corpus with existing Praxis-internal assets (Tokonomics Rounds 1–4, Business Session, Praxis planning artifacts, Pipeline.md build sessions, the Stage 3 elicitation itself). Stage 5 MAC benchmark questions + gold answers become seed_corpus_v2. Stage 6 Studio augments with customer-validated corpora.

**Seed Corpus v1 Composition:**

| Asset | Location | Role |
|-------|----------|------|
| Tokonomics Round 1 | `_bmad-output/planning-artifacts/Tokonomics/1st_Round_table.md` | 7-agent + 10-research multi-agent deliberation |
| Tokonomics Round 2 | `_bmad-output/planning-artifacts/Tokonomics/2nd_Round_table.md` | Deep strategy sessions, 10 sessions, 25+ frameworks |
| Tokonomics Round 3 | `_bmad-output/planning-artifacts/Tokonomics/3rd_Round_table.md` | Competitive landscape validation |
| Tokonomics Round 4 | `_bmad-output/planning-artifacts/Tokonomics/4th_Round_table.md` | Red team analysis, 6 agents, critical findings |
| Business Session | `_bmad-output/planning-artifacts/Tokonomics/business_session.md` | GTM, resources, design, brand, pitch — 8 parallel analyses |
| Praxis planning | `_bmad-output/planning-artifacts/Praxis/*.md` | Strategic reframing, architecture, build plan |
| Pipeline.md | `_bmad-output/planning-artifacts/Praxis/Pipeline.md` | Meta-level "how to plan a complex build" exemplar |
| Stage 3 elicitation | `_bmad-output/implementation-artifacts/praxis/memory/requirements-privacy.md` + `requirements.md` | First in-anger Stakeholder Round Table + FMEA |

**Rationale:**
- The seed corpus problem is already solved; Andrey accumulated it over months.
- The content is Praxis-internal and founder-generated — zero license ambiguity, zero PII from customers, zero redistribution concern. License attestation (per Requirement #17) is trivial: "Praxis-owned, founder-generated, self-attested 2026-04-12."
- **"Built With Praxis" narrative:** seed corpus IS the literal build history of Praxis. This materializes a free pre-sales asset — the launch blog post writes itself: *"Praxis was built using Praxis. Every strategic decision in this product was made via the same multi-agent deliberation methodology you'll buy."*

**Implications for Winston (binding):**
- Seed corpus schema must support **heterogeneous source types** — round-table transcripts, framework lists, strategic decisions, architecture docs, FMEA tables. Not just "case studies."
- **Ingest pipeline** chunks long-form markdown into semantically coherent units before embedding. Winston specifies the chunking strategy; likely paragraph-or-section-level with metadata pointing back to the source file + offset.
- **Source attribution is first-class metadata** on each record: `source_file`, `source_section`, `ingest_date`, `license_attestation="praxis-internal/founder-generated"`, `generator="bmad-agent-{name}"` where applicable.
- **Seed corpus v1 initial size:** rough estimate is ~1–2M tokens of source material chunked into ~2000–5000 records depending on chunk size. Embedding cost is a one-time ingest operation.
- **Seed_corpus_v2 (Stage 5 deliverable):** MAC's 10 benchmark questions + gold-standard answers are added as a distinct namespace within the seed corpus, used specifically for calibration validation.
- **Curator role:** Andrey is the curator for v1. Stage 6 Studio defines the curator role going forward.

**Reversibility:** Fully reversible. The seed corpus is versioned (Requirement #15 — retained indefinitely in Beads). If v1 proves unsuitable, v2/v3 replace it without touching prior audit trails.

---

## Decision Dependency Graph

```
B1 (managed single-tenant) ┬─→ B3 (Git config is fine — no tenant scoping service needed)
                           ├─→ B4 (tenant-scoped LLM keys are natural)
                           └─→ B5 (per-tenant backup encryption is natural)

B2 (embeddings = PII)      ┬─→ FM3.10 override (quarantine strips embeddings) ratified
                           └─→ B5 (backup must honor delete via crypto-shredding)

B6 (seed corpus = BMAD)    ──→ Stage 5 MAC benchmarks become seed_corpus_v2
                           ──→ "Built With Praxis" launch narrative materialized
```

All 6 decisions are mutually consistent. No internal contradictions. Winston has a coherent constraint set to design against.

---

**End of Round 2 hardened requirements.** Next step: 3.1 — `/bmad-agent-architect` (Winston) drafts `memory/architecture.md` against this document. Per Pipeline.md Section 4.5 rule 3, Winston may raise objections to specific requirements but cannot silently override.
