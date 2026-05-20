# praxis-adapter-mem0 changelog

Per `ports-architecture.md` v0.2 §5 (upgrade workflow shape; one entry per version bump).

## v0.1.0 (2026-05-03)

Initial in-tree PyPI-pinned Mem0 adapter implementing `MemoryPort` per ADR-9.2-V1
(`ports-architecture.md` v0.3 §3). PRIMARY adapter in the dual-adapter pair (Letta
secondary at `adapters/letta/` per Phase B.2).

Upstream: `mem0ai==1.0.11` (post-modernization stable per Mem0 SDK survey 2026-05-02 §2).
Range pin `>=1.0.11,<2.0`.

### Substance

- 5 `MemoryPort` methods (`store`, `query`, `promote`, `revoke_promotion`, `migrate`)
- AP-3 TierNormalizer (query, promote) per `port-contracts.md` v0.2.1 §7 line 306 (i)
- AP-4 ThresholdGuard (promote pre-upstream PS-1 enforcement)
- AP-5 TwoPhaseIdempotencyCommit (on_init reconcile + every idempotent method) per
  Q-B1-22 disposition (i'): in-process dict + on_init read-back from Mem0 sidecar
  metadata; PS-2 v0.2 §3.4 PS-2 durability conformant. AP-5 dedup includes
  payload-equivalence check per `IdempotencyViolation` contract (`common.py`
  IdempotencyViolation): cache key → (payload_hash, prior_call_at, cached_dto);
  payload mismatch raises `IdempotencyViolation`, not silent return-of-stale-DTO
- AP-6 SpanAttributeContract (promote 5-attribute canonical per PS-3 set-equality
  verbatim) + adapter-private `verdaca.memory.confidence_synthesis` on degraded-signal
  query paths only per Q-B3-4 disposition adapter-private
- AP-7 OpaqueIDWrapper (promote/revoke_promotion `promotion_id` generation)
- AP-9 ConfidenceScaleNormalizer (query F-011 belt-and-braces clamp) per §7 line 306 (ii)
- M.1 adapter-internal migrator registry per Q-MIGRATE-1 disposition (no Protocol-level
  migrator parameter; no fresh corrigendum)

### Caller-DI Mem0 instance configuration (caller responsibility)

The adapter accepts a caller-constructed `Memory` instance via `__init__(*, mem0_client=...)`.
Mem0 lifecycle (embedder, LLM, vector store, auth) is the caller's responsibility per
Q-B1-1 caller-DI disposition. Two caller-side configuration constraints worth flagging:

1. **Vector store dim alignment**: `vector_store.config.embedding_model_dims` MUST align
   with embedder model dims (e.g., `nomic-embed-text` = 768; OpenAI
   `text-embedding-3-small` = 1536). Mem0 v1.0.11 has no auto-alignment; mismatch fails
   at first search call with `ValueError: shapes ... not aligned`.
2. **`infer=False` mode**: adapter-internal sidecar writes use `infer=False` to skip
   Mem0's LLM-based fact-extraction layer (sidecar entries are admin-shaped `verdaca.*`
   metadata records, not user-extractable facts). Standard Mem0 v1.0.11 behavior; no
   special caller config needed.

### Stable user_id partitioning (per Q-B1-Sub-10 disposition)

- User-memory corpus uses `_VERDACA_USER_ID = "verdaca.system.user"` (stable across all
  caller correlation_ids; cross-session retrieval works correctly). Caller may override
  via adapter `__init__(*, user_id=...)` kwarg.
- Idempotency-sidecar entries use `_VERDACA_SIDECAR_USER_ID = "verdaca.system.idempotency"`
  (cleanly partitioned from user-memory corpus). Mem0 v1.0.11 rejects arbitrary
  `memory_type` strings (only `'procedural_memory'` accepted) per Q-B1-Sub-3 probe;
  user_id-based partitioning is the working alternative per Q-B1-Sub-10 fallback.
- Caller's per-call `correlation_id` threads through Mem0 metadata as
  `verdaca.correlation_id` key, NOT as `user_id`.

### `revoke_promotion` idempotency-key divergence (per Q-B1-Sub-1 disposition)

Protocol signature `revoke_promotion(self, promotion_id: str, reason: str) ->
RevokedPromotion` carries no explicit `idempotency_key` parameter. Adapter derives
natural key as `sha256(f"{promotion_id}:{reason}").hexdigest()` for AP-5 dedup.
Caller cannot supply an explicit `idempotency_key` for `revoke_promotion` at v0.1.0;
same `(promotion_id, reason)` call replay returns cached `RevokedPromotion` DTO; replay
with different `reason` for the same `promotion_id` raises `IdempotencyViolation` per
payload-equivalence check.

Stage 10 hardening could revisit if a corrigendum to ADR-1 §3 method signatures adds
an explicit `idempotency_key` parameter.

### Mem0 v1.0.11 architectural finding (probe-surfaced)

Mem0 `Memory.__init__` constructs BOTH the embedder and the LLM eagerly at construct
time (verified via probe trace at `mem0/memory/main.py:250` + `:258`). Both default to
OpenAI and unconditionally validate API key at constructor (`mem0/embeddings/openai.py:35`,
`mem0/llms/openai.py:52`). The `infer=False` flag suppresses LLM USAGE during
`Memory.add()`, NOT LLM CONSTRUCTION at init. This validates Q-B1-1 caller-DI
disposition retroactively: the adapter contains the API-key surface at caller-construction
time, NOT at adapter execution. B.1 commit substance is unaffected by Mem0's eager-init
behavior — caller pays the embedder/LLM-init cost at `Memory()` construction; adapter
just consumes the constructed `Memory` instance. The dual-adapter substitution story
(per `port-contracts.md` v0.2.1 §3 substitute-readiness clause) holds: Mem0 caller can
swap embedders / LLMs via Mem0 config; Letta caller has different config surface; both
adapter shells stay caller-config-agnostic.

### AP-5 sidecar role discipline (Mem0 v1.0.11 quirk)

Idempotency-sidecar INTENT/SUCCESS entries use `role='user'` rather than `role='system'`.
Mem0 v1.0.11 silently drops `role='system'` messages when `infer=False` (returns empty
results; entries never persist; verified via probe at v0.1.0 verification). Partition
discipline relies on `user_id=_VERDACA_SIDECAR_USER_ID` (per Q-B1-Sub-10 user_id-only
partitioning fallback) plus `verdaca.idempotency.kind` metadata-key presence; role
field is non-discriminating. Caller-DI Mem0 instances on future v1.x versions should
re-verify this behavior; if Mem0 ever begins accepting `role='system'` under
`infer=False`, the adapter implementation could be tightened to use role-based
defense-in-depth.

### Stage 10 deferred

- Durable cache backend (option ii Mem0-metadata-backed durable cache vs option iii
  sidecar SQLite/Redis); v0.1.0 ships option (i') in-process dict + AP-5 reconciliation
  per Q-B1-22 disposition.
- Async mode (Mem0 has `AsyncMemory`; B.1 targets sync per Q-B1-1 caller-DI disposition).
- Mem0 `Memory.update()` semantics hardening (Q-B1-Sub-8 / survey-Q1) — v0.1.0 uses
  read-merge-update pattern (`update(memory_id, data=existing_content,
  metadata=merged_metadata)`) per N3-a-rev disposition.
- Admin migrator-registration method (B.1 ships `__init__`-kwarg-only registry per
  Q-B1-Sub-7).
- `revoke_promotion` resolution-by-search uses adapter-side O(n) filter loop (Mem0
  filter syntax for nested metadata keys not verified at v0.1.0); Stage 10 could
  optimize via Mem0 filter once syntax is verified or Mem0 indexing improves.
