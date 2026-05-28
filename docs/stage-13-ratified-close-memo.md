# Stage 13 RATIFIED Close Memo

**Path of record:** `docs/stage-13-ratified-close-memo.md` (**tracked** per `.gitignore:61` negation `!docs/stage-*-ratified-close-memo.md`, overriding the broader `.gitignore:55 docs/*.md` ignore rule — ratified close memos are first-class repo artifacts)
**Stage:** 13 — Production Hardening (Option A — no new feature surface)
**Branch:** `stage-13.0-production-hardening` (local-only Path A continuation; D13 keeps local through Stage 13)
**Base:** `5306c8d` (Stage 12 hygiene tail tip on `stage-12.0-channel-adapters`)
**Stage 12 binding RATIFIED anchor:** `43f57ba` (preserved)
**Close SHA:** `1ce9539` (V3.A — V1 C-1 acceptance criterion fully closed structurally)
**Ratification date:** 2026-05-28
**Authored by:** Stage 13 advisor (Opus 4.7 1M MAX) + Claude Code executor (Opus 4.7 1M MAX)
**Predecessor close memo:** `docs/stage-12-ratified-close-memo.md` (Stage 12 RATIFIED 2026-05-27 at `43f57ba` + 3 hygiene commits tail tip `5306c8d`)

Canonical close-state pin:
"Runtime no_waiver = 13 / Stage 13 AST gates = 6 NEW / Total enforced markers = 19"

---

## §1 Headline

Stage 13 = **production hardening cycle (Option A)** — no new feature surface, no new ports, no REFREEZE ceremonies. The cycle structurally closes the Stage 11→12 auth-quartet wiring at the canonical gateway composition root, hardens channel adapter inbound/outbound paths under real event-loop semantics, and pins six new AST gates plus four new runtime no_waiver MAC-Ts as Stage 13's permanent regression floor.

- **13 implementation commits** on `stage-13.0-production-hardening` from base `5306c8d` to close `1ce9539`
- **321 tests passed / 8 skipped / 1 warning** (Stage 12 baseline 281 → +40 via Stage 13 contract surface additions)
- **13-entry no_waiver allow-list** under strict-equality meta-test (9 Stage 12 carry + 4 Stage 13 NEW)
- **6 new Stage 13 AST gates A–F** (extract_claims · OidcPolicy · build_gateway 11-param · NonceStore SQLite invariants · session-id min width · close-memo tracking symmetry)
- **5/5 V1 Cleo findings CLOSED structurally** (C-1 + H-1 + H-2 + M-1 + L-1) — C-1 reached full acceptance only at V3.A after the conditional vkey-budget gap was caught and fixed
- **2/12 V3 Cleo findings CLOSED at V3.A** (HIGH F-13-V3-VKEY-BUDGET-OPTIONAL-01 + folded MEDIUM F-13-V3-SERVICE-POLICY-DEFAULT-FACTORY-01)
- **10/12 V3 findings carried to Stage 14** (2 MEDIUM + 4 LOW + 4 WARNING) — see §5 ledger
- **HARD-constraint grep zero hits** across Stage 13 source surfaces (Mary H#7 PASS preserved at V3.A close)
- **Stage 9–12 invariants ALL preserved**: M-T-GATEWAY-WIRING-NO-AUTH-LOGIC-01 (Stage 11), Stage 12 no_waiver count = 9, Stage 9 cardinality = 9
- **Frozen Port surfaces preserved**: `GatewayPort` + `ChannelAdapterPort` Protocols unchanged (no REFREEZE-03 triggered)
- **Canonical pin `13 / 6 / 19` unchanged** end-to-end across V2.A → V3.A
- **HYPOTHETICAL-VOC caveat inherited** from A7 override (Stage 10 `f181a7e` 2026-05-24) — every customer-fit claim must carry the override caveat per `project_verdaca_strategic_sequencing`
- **Path A local-only** — Stage 13 NOT merged to `main` per D13; merge ceremony deferred to post-implementation+test demo trigger

---

## §2 Scope Delivered

### E1 — Auth quartet wiring + channel async hardening

- **`kernel/gateway/composition.py`** — canonical composition root `build_gateway(...)` with 11 keyword-only required dependencies (V2.B `f91aad0`); no internal `GatewayPolicy(...)` synthesis; `WebhookSigningKeyResolver` threaded to channel adapters but not on the GatewayPort execute path.
- **`kernel/gateway/composition_types.py`** — `WebhookSigningKeyResolver` frozen dataclass (E1-H3 `2802754`); rejects empty configured secrets at `__post_init__`.
- **`kernel/auth/oidc.py`** — `OidcPolicy(verifier, audience)` class added at E1-H3.B (`8be62e0`); both arguments required and keyword-only; `authenticate(bearer_token)` calls `verifier.decode(token, audience=self._audience)`.
- **`kernel/auth/claims.py`** — `extract_claims(token, verifier)` relocated from prior Stage 12 surface to module-level signature with NO `None` default for `verifier` (E1-H3.B `8be62e0`).
- **`kernel/auth/nonce.py`** — `NonceStore` SQLite-backed persistence with `WAL` journal mode, `synchronous=NORMAL`, `BEGIN IMMEDIATE` atomic transaction around the DELETE-expired + INSERT-new replay gate, asyncio.Lock for within-process concurrency, `InMemoryNonceStore` test fake (E1-H4 `54f9235`). Closes Stage 12 carry-forward `F-12-CLEO-M3-NONCE-RESTART-DEFER-01` for persistence + restart-replay coverage.
- **`adapters/channels/teams/.../adapter.py`** + **`adapters/channels/slack/.../adapter.py`** — `post_result` migrated to `httpx.AsyncClient` (E1-H5 `a354283`); V2.C `2776be0` added in-loop task retention via `self._post_tasks: set[asyncio.Task[None]]` + `add_done_callback(self._post_result_done)` that discards from set + logs exceptions via `_LOGGER.exception`. Closes Stage 12 carry-forward `F-12-CLEO-W2-SYNC-HTTPX-01`.
- **`adapters/channels/teams/.../events.py`** + **`adapters/channels/slack/.../events.py`** — `parse_activity` / `parse_event` made verifier-required at V2.B (`f91aad0`); synthetic-claims `"unverified-teams-token"` / `"unverified-slack-token"` fallback REMOVED; webhook TODOs at `webhook.py:81`/`:83` closed (verifier threaded through `receive_webhook → dispatch → parse_*`).
- **`kernel/gateway/service.py`** — `VerdacaGatewayService.execute()` invokes auth quartet via `_run_auth_first` at line 69 BEFORE `evaluate_gateway_policy` (V2.A `e2ece6f`); V3.A `1ce9539` removed the `if self.policy.virtual_keys is not None:` conditional at line 201 (vkey budget now UNCONDITIONAL); V3.A also removed `field(default_factory=GatewayPolicy)` on the `policy` field (line 58 — policy is now a REQUIRED keyword-only param; `dataclasses.field` import removed).
- **`shell/api/gateway_startup.py`** — mirror 11-param `create_gateway` shell delegator (V2.B `f91aad0`).
- **E1 MAC-Ts** added across the cycle: M-T-GATEWAY-EXECUTE-AUTH-FIRST-01 (V2.A renamed at V2.D), M-T-AUTH-NONCE-PERSISTENCE-RESTART-01, M-T-CHANNEL-EVENT-VERIFIER-REQUIRED-01, M-T-CHANNEL-POST-RESULT-ERROR-OBSERVED-01, M-T-GATEWAY-COMPOSITION-POLICY-CONFIGURED-01, M-T-AUTH-NONCE-{STARTUP-SWEEP, ATOMIC-EXPIRY-BOUNDARY, REPLAY-BLOCK, SEPARATE-DB-FILE}-01, M-T-CHANNELS-TEAMS-POST-RESULT-ASYNC-01, M-T-CHANNELS-SLACK-POST-RESULT-ASYNC-01, M-T-CHANNELS-HTTPX-ASYNCCLIENT-01, M-T-AUTH-E1-CONSUMES-E2-IDP-FIXTURE-01, M-T-AUTH-VERIFIER-WIRED-AT-COMPOSITION-01, M-T-COMPOSITION-NO-NONE-DEFAULT-01, M-T-COMPOSITION-NO-INTERNAL-IMPORT-01.

### E2 — Hygiene + data-plane invariants

- **`kernel/gateway/service.py` session-id width hardening (W-1)** — `_session_id` now uses `hashlib.sha256(...).hexdigest()[:32]` (128-bit floor) instead of the prior 16-hex slice (E2-H3.B `4d45100`). Closes the prior 64-bit entropy floor as a Cleo regression risk.
- **`tests/.../test_ast_gates_stage13.py` Gate F** — close-memo tracking symmetry gate (E2-H3.C `f1aa572`); enforces `git ls-files docs/stage-*-ratified-close-memo.md` set-equality with on-disk POSIX set. Catches missing-from-tracking close memos at AST evaluation time.
- **`tests/.../test_gateway_session_id_width.py`** — 3 MAC-Ts for session-id width / entropy floor / determinism (E2-H3.B + E2-H5 `2e1d134` ruff cleanup).
- **`tests/.../test_stage13_no_waiver_count.py`** — V2.D `3fc11c7` broadened tree-walk discovery + 9-path `PRE_STAGE13_MARKER_PATHS` exclusion frozenset + defensive `_format_path` fallback for tmp_path + `M-T-STAGE13-NO-WAIVER-DISCOVERY-DRIFT-01` synthetic canary. Also closed an undocumented V2.A marker rename regression (`M-T-AUTH-VERIFIER-WIRED-AT-COMPOSITION-01` → `M-T-GATEWAY-EXECUTE-AUTH-FIRST-01`) by switching from 4-file hard-code to tree-walk.
- **E2 MAC-Ts** added: M-T-SESSION-ID-ENTROPY-FLOOR-01 (no_waiver), M-T-GATEWAY-SESSION-ID-WIDTH-01, M-T-GATEWAY-SESSION-ID-DETERMINISTIC-01, Gate F, M-T-STAGE13-NO-WAIVER-DISCOVERY-DRIFT-01.

### Stage 12 hygiene tail (retroactive close, base `5306c8d`)

The Stage 12 close memo committed at `9fe3057` and gitignore-citation parity at `5306c8d` retroactively closed:
- `F-12-CLOSE-MEMO-UNTRACKED-01` (Stage 12 close memo had not been `git add`-ed; tracked at `9fe3057`)
- `F-13-HANDOVER-CLOSE-MEMO-GITIGNORE-CLAIM-{01,02}` (close memo line-3 wording incorrectly cited the broader `docs/*.md` rule instead of the `.gitignore:61` negation; corrected at `9fe3057` and `5306c8d` with parity at line-194 §provenance row)

These hygiene commits are technically Stage 12's tail but their disposition is documented here because the F-13-HANDOVER-CLOSE-MEMO-GITIGNORE-CLAIM finding numbers belong to the Stage 13 handover-template drift ledger (§5).

### Stage 13 V2 + V3.A finding closures

V2.A–V2.D + V3.A is the Cleo H#8 amendment chain:
- **V2.A `e2ece6f`** — Cleo CRITICAL C-1: `VerdacaGatewayService.execute()` now invokes the auth quartet in strict order (bearer → OidcPolicy.authenticate → NonceStore.check_and_mark → conditional vkey-budget → evaluate_gateway_policy → memory/LLM/cost) BEFORE any side effect.
- **V2.B `f91aad0`** — Cleo HIGH H-1 (`build_gateway(*, ..., policy: GatewayPolicy)` 11th required keyword-only param + shell mirror + no internal `GatewayPolicy(...)` construction) + HIGH H-2 (channel parsers require verifier; synthetic-claims fallback removed; webhook TODOs closed).
- **V2.C `2776be0`** — Cleo MEDIUM M-1: async post_result tasks retained + done_callback observes failures via `_LOGGER.exception`.
- **V2.D `3fc11c7`** — Cleo LOW L-1: broadened no_waiver discovery + drift canary + V2.A rename regression fix + em-dash UTF-8 fidelity restored.
- **V3.A `1ce9539`** — Cleo V3 HIGH F-13-V3-VKEY-BUDGET-OPTIONAL-01: vkey-budget invocation in `_auth_first` made UNCONDITIONAL (V1 C-1's binding acceptance criterion *"virtual-key budget is checked"* now structurally on the path) + folded MEDIUM F-13-V3-SERVICE-POLICY-DEFAULT-FACTORY-01 (policy is now a required constructor param; `default_factory=GatewayPolicy` removed; `dataclasses.field` import dropped).

---

## §3 SHA Chain (13 commits from `5306c8d`)

| Phase | SHA | Description |
|---|---|---|
| E2-H3.B | `4d45100` | fix: Stage 13 E2-H3.B — gateway session-id 128-bit deterministic prefix (W-1 entropy floor) |
| E2-H3.C | `f1aa572` | test: Stage 13 E2-H3.C — Gate F close-memo tracking symmetry |
| E1-H3 | `2802754` | feat: Stage 13 E1-H3 — composition root + WebhookSigningKeyResolver |
| E1-H3.B | `8be62e0` | feat: Stage 13 E1-H3.B — OidcPolicy class + extract_claims relocation |
| E1-H4 | `54f9235` | feat: Stage 13 E1-H4 — NonceStore SQLite persistence + BEGIN IMMEDIATE |
| E1-H5 | `a354283` | feat: Stage 13 E1-H5 — Teams + Slack post_result async migration |
| E1-H6 | `a3c589a` | test: Stage 13 E1-H6 — auth + composition + channels MAC-Ts + AST gates A–E |
| E2-H5 | `2e1d134` | test: Stage 13 E2-H5 — ruff cleanup for session-id width test |
| V2.A | `e2ece6f` | fix: Stage 13 H#8.V2.A — Cleo CRITICAL fix (C-1 auth quartet invoked in VerdacaGatewayService.execute() with strict order) |
| V2.B | `f91aad0` | fix: Stage 13 H#8.V2.B — Cleo HIGH fixes (H-1 policy param + H-2 verifier-required channel events) |
| V2.C | `2776be0` | fix: Stage 13 H#8.V2.C — Cleo MEDIUM fix (M-1 async post_result failures observed) |
| V2.D | `3fc11c7` | fix: Stage 13 H#8.V2.D — Cleo LOW fix (L-1 broaden no_waiver discovery with pre-Stage-13 exclusion + defensive path formatter) |
| **V3.A** | **`1ce9539`** | **fix: Stage 13 H#8.V3.A — Cleo HIGH fix (V3-VKEY-BUDGET-OPTIONAL-01: enforce_budget unconditional + policy as required param)** |

V2.A–V2.C commit subjects render em-dash as `"?"` due to predecessor Codex/GPT-5 shell encoding artifact; V2.D `3fc11c7` restores em-dash UTF-8 fidelity, V3.A `1ce9539` preserves it. Per advisor §10 disposition: V2.A/B/C are NOT amended; encoding artifact documented in V2.D commit body and re-noted here.

---

## §4 13-entry no_waiver Allow-List (strict-equality meta-test enforced)

Stage 12 carry (9) + Stage 13 NEW (4) = 13 runtime no_waiver markers.

| # | ID | Stage origin |
|---|---|---|
| 1 | M-T-TEAMS-WEBHOOK-HMAC-TAMPERED-01 | Stage 12 carry (E1) |
| 2 | M-T-SLACK-WEBHOOK-SIGNING-TAMPERED-01 | Stage 12 carry (E1) |
| 3 | M-T-TEAMS-CHANNEL-ADAPTER-PORT-CONTRACT-01 | Stage 12 carry (E1) |
| 4 | M-T-SLACK-CHANNEL-ADAPTER-PORT-CONTRACT-01 | Stage 12 carry (E1) |
| 5 | M-T-AUTH-JWT-ALG-PIN-01 | Stage 12 carry (E2) |
| 6 | M-T-AUTH-NONCE-REPLAY-BLOCK-01 | Stage 12 carry (E2) |
| 7 | M-T-AUTH-CLAIMS-SCHEMA-01 | Stage 12 carry (E2) |
| 8 | M-T-VKEY-BUDGET-EXHAUSTED-01 | Stage 12 carry (E2) |
| 9 | M-T-AUTH-KERNEL-NO-ADAPTER-IMPORT-01 | Stage 12 carry (E2) |
| 10 | **M-T-GATEWAY-EXECUTE-AUTH-FIRST-01** | **Stage 13 NEW (V2.A; renamed at V2.D — replaces M-T-AUTH-VERIFIER-WIRED-AT-COMPOSITION-01)** |
| 11 | **M-T-AUTH-NONCE-PERSISTENCE-RESTART-01** | **Stage 13 NEW (E1-H4)** |
| 12 | **M-T-SESSION-ID-ENTROPY-FLOOR-01** | **Stage 13 NEW (E2-H3.B)** |
| 13 | **M-T-NO-BARE-EXCEPT-AUTH-CRYPTO-01** | **Stage 13 NEW (E1-H6; co-located with Gate E in test_ast_gates_stage13.py)** |

**Stage 13 AST gates A–F (6, enumerated by `STAGE_13_AST_GATE_IDS` in `test_stage13_no_waiver_count.py`):**

| Gate | ID | Invariant |
|---|---|---|
| A | gate_a_extract_claims_no_none_default | `extract_claims` + `parse_activity` + `parse_event` have no `None` default for `verifier`; annotation is not `Optional`. |
| B | gate_b_oidc_policy_verifier_required | `OidcPolicy.__init__(*, verifier, audience)` requires both args; verifier annotation not Optional. |
| C | gate_c_build_gateway_full_deps | `build_gateway` 11 keyword-only params with no defaults. |
| D | gate_d_nonce_store_sqlite_invariants | `NonceStore.__init__` declares `db_path: Path`; module contains `persistent: ClassVar[bool] = True`, `PRAGMA journal_mode=WAL`, `PRAGMA synchronous=NORMAL`, `BEGIN IMMEDIATE`. |
| E | gate_e_session_id_min_width | `kernel/gateway/service.py` contains no `hexdigest()[:16]`; all `hexdigest()[:<N>]` slices ≥ 32 hex chars (128-bit floor). |
| F | gate_f_close_memo_tracking_symmetry | `git ls-files docs/stage-*-ratified-close-memo.md` set-equality with on-disk POSIX-relative set. |

**Strict-equality enforcement:** `tests/src/praxis/contract_tests/test_stage13_no_waiver_count.py` (V2.D) uses `rglob("test_*.py")` tree-walk over `tests/src/praxis/contract_tests/` with `PRE_STAGE13_MARKER_PATHS` 9-path exclusion frozenset; AST file `test_ast_gates_stage13.py` retained in scope per Option α disposition (M-T-NO-BARE-EXCEPT-AUTH-CRYPTO-01 lives alongside Gate E); synthetic drift canary `M-T-STAGE13-NO-WAIVER-DISCOVERY-DRIFT-01` writes a synthetic marker into `tmp_path` and asserts `AssertionError("Unratified Stage 13 no_waiver tests")`.

**Stage 12 enforcer cardinality preserved:** `tests/.../test_stage12_no_waiver_count.py` continues to enforce exactly 9 markers via its own scope.

---

## §5 Findings Ledger (durable record)

### §5.1 V1 Cleo findings (5 ratified CLOSED)

| ID | Severity | Closure SHA(s) | Evidence (file:line / MAC-T) |
|---|---|---|---|
| F-13-CLEO-C1 | CRITICAL | `e2ece6f` (V2.A — auth quartet invoked) + `1ce9539` (V3.A — vkey-budget unconditional) | `service.py:69` `_run_auth_first` call; `service.py:201` unconditional `enforce_budget`; `M-T-GATEWAY-EXECUTE-AUTH-FIRST-01` asserts order `["auth", "nonce", "budget"]` AND `virtual_keys.checked == ["user-1"]` |
| F-13-CLEO-H1 | HIGH | `f91aad0` (V2.B) | `composition.py:25-56` 11-param signature; `shell/api/gateway_startup.py:20-47` shell mirror; AST Gate C + `M-T-GATEWAY-COMPOSITION-POLICY-CONFIGURED-01` |
| F-13-CLEO-H2 | HIGH | `f91aad0` (V2.B) | `events.py` (teams + slack) `parse_*` verifier required; synthetic-claims fallback removed; AST Gate A + `M-T-CHANNEL-EVENT-VERIFIER-REQUIRED-01` |
| F-13-CLEO-M1 | MEDIUM | `2776be0` (V2.C) | `adapter.py` (teams + slack) `_post_tasks` set + `add_done_callback(_post_result_done)`; `M-T-CHANNEL-POST-RESULT-ERROR-OBSERVED-01` exercises failure-then-callback under running loop |
| F-13-CLEO-L1 | LOW | `3fc11c7` (V2.D) | `test_stage13_no_waiver_count.py` tree-walk + 9-path exclusion + defensive `_format_path` + `M-T-STAGE13-NO-WAIVER-DISCOVERY-DRIFT-01` canary |

### §5.2 V3 Cleo findings (2 CLOSED at V3.A + 10 carried to Stage 14)

**CLOSED at `1ce9539` (V3.A):**

| ID | Severity | Closure |
|---|---|---|
| F-13-V3-VKEY-BUDGET-OPTIONAL-01 | HIGH | Conditional `if self.policy.virtual_keys is not None:` REMOVED at `service.py:201`; `enforce_budget` invoked unconditionally; `GatewayPolicy.enforce_budget` fail-closes on `virtual_keys=None` (operational misconfig surfaces as `auth:builtins.RuntimeError` at first request); MAC-T `M-T-GATEWAY-EXECUTE-AUTH-FIRST-01` now exercises vkey-budget via `_TracingVirtualKeys` and asserts order `["auth", "nonce", "budget"]` + `order.index("budget") < order.index("memory")` + `virtual_keys.checked == ["user-1"]` |
| F-13-V3-SERVICE-POLICY-DEFAULT-FACTORY-01 | MEDIUM | `policy: GatewayPolicy` at `service.py:58` (REQUIRED; no `field(default_factory=GatewayPolicy)`); `dataclasses.field` import removed; direct `VerdacaGatewayService(...)` construction now raises `TypeError: missing 1 required keyword-only argument: 'policy'` at construction time |

**Carried to Stage 14 (10):**

| ID | Severity | Brief evidence | Recommended fix (Stage 14) |
|---|---|---|---|
| F-13-V3-AUDIENCE-DOUBLE-DECODE-01 | MEDIUM | `claims.py:20` `_CHANNEL_ADAPTER_AUDIENCE = "verdaca-channel-adapter"` (hardcoded) vs `OidcPolicy(audience=...)` caller-configured (test fixtures use `"api://verdaca"`). Token must satisfy both for end-to-end auth; multi-aud requirement undocumented. | Unify audience config (pass audience to `extract_claims`) OR document multi-aud + add contract test fixture |
| F-13-V3-PARSE-ACTIVITY-CLAIMS-DICT-BYPASS-01 | MEDIUM | `parse_activity` / `parse_event` accept `claims: Mapping[str, Any]` parameter that bypasses verifier in dict-path; test usage at `test_auth_claims_channel_contract.py:76` passes `claims=dict, verifier=object()`. Production receive_webhook flow doesn't expose, but signature permits | Split into production-only `parse_*` and test-fixture-only `parse_*_with_pre_validated_claims` OR AST gate banning `claims=` kwarg in production callers |
| F-13-V3-AUTH-EVENT-LOOP-PER-REQUEST-01 | LOW | `service.py:182-195` `_run_auth_first` calls `asyncio.run(...)` per request → new event loop per call (~1ms overhead at high QPS) | Long-lived loop per gateway instance OR async port boundary (REFREEZE-impact; defer) |
| F-13-V3-EXECUTE-IN-ASYNC-RAISES-01 | LOW | `service.py:195` raises `RuntimeError` if execute() called from a running event loop; async webhook handlers need `asyncio.to_thread` wrap | Add port contract docstring at `ports/gateway.py:21` noting sync-from-async requirement |
| F-13-V3-HTTPX-CLIENT-NOT-POOLED-01 | LOW | Channel adapter `post_result` creates fresh `httpx.AsyncClient(timeout=10.0)` per call when no DI'd client; no connection pooling | Require `http_client` injection (remove no-DI branch) OR cache lazy-init AsyncClient on adapter |
| F-13-V3-JWKS-NOT-INTEGRATED-01 | LOW | `kernel/auth/oidc.py:48-125` `JwksCache` defined with TTL + rotation logic, but `OidcPolicy` / `JwtVerifier` (`jwt.py:22-42`) hold static JWKS dict; key rotation requires manual `JwtVerifier` reconstruction | Wire `OidcPolicy` to consume `JwksCache` for kid-based verifier resolution at decode time |
| F-13-V3-RATE-LIMIT-TOKEN-NAMING-DRIFT-01 | WARNING | `ChannelContext.rate_limit_token` field at `gateway_dto.py:80` semantically holds bearer token (set by `events.py` channel parsers; read by `service._bearer_token`). Name is misleading | REFREEZE-class corrigendum to rename `bearer_token` (significant ceremony) OR doc-comment documenting the dual purpose |
| F-13-V3-CHARTER-11-PARAM-RATIFICATION-01 | WARNING | V2.B commit labels 11-param `build_gateway` as "V3 charter corrigendum candidate"; Charter v0.2 formal ratification status not explicit | Charter v0.2 amendment line documenting 11-param `build_gateway` signature + reference AST Gate C as runtime invariant carrier |
| F-13-V3-DONE-CALLBACK-CANCELLED-NOT-LOGGED-01 | WARNING | `_post_result_done` `except Exception:` doesn't catch `asyncio.CancelledError` (3.11+ extends `BaseException`); cancelled post_result tasks silently disappear from logs | Add `except asyncio.CancelledError: _LOGGER.debug(...)` branch OR accept current behavior (cancellations are intentional) |
| F-13-V3-AUTH-EXCEPTION-WRAPPING-INFO-LOSS-01 | WARNING | `_auth_error` at `service.py:414-426` wraps any auth exception with `context_field=f"auth:{module.classname}"`; original message lost (chain preserved via `from exc`). Mildly aggravated at V3.A: empty-policy rejection now surfaces as `auth:builtins.RuntimeError` (vkey-misconfig subsumed under `auth:` prefix) | Add `cause_message: str | None = None` field to `GatewayCtxError` populated from `str(exc)` at wrap time |

### §5.3 Handover-template drift candidates (Stage 14 checklist amendment)

Captures the F-13-HANDOVER-* drift findings surfaced across the cycle's H#0 + H#1 preloads:

| ID | Disposition | Notes |
|---|---|---|
| F-13-HANDOVER-LOCAL-SHA-01 | DEFERRED (R13-A, Stage 14 checklist) | Local-SHA citation discipline in advisor handover §provenance |
| F-13-HANDOVER-COMMIT-AUTH-01 | DEFERRED (R13-A, Stage 14 checklist) | Commit-authority routing in concurrent-executor handovers |
| F-13-HANDOVER-CLOSE-MEMO-GITIGNORE-CLAIM-01 | CLOSED at `9fe3057` | Stage 12 hygiene retro-fix to close-memo line-3 wording (broader rule → `.gitignore:61` negation) |
| F-13-HANDOVER-CLOSE-MEMO-GITIGNORE-CLAIM-02 | CLOSED at `5306c8d` | Stage 12 hygiene retro-fix at line-194 §provenance Path-of-record row |
| F-13-HANDOVER-V2.D-AST-EXCLUSION-01 | CLOSED at `3fc11c7` via Option α | Advisor §3.1 binding-fix spec excluded the AST gate file entirely; would have lost M-T-NO-BARE-EXCEPT-AUTH-CRYPTO-01. Option α (drop `{AST_GATE_FILE}` from EXCLUSIONS) preserved the marker — catalog scope matches HEAD enumeration |
| F-13-E1-PRELOAD-OIDC-CLASS-DRIFT-01 | CLOSED at `8be62e0` | E1 executor preload caught the OidcPolicy class-vs-function drift before code edits |
| F-13-E1-PRELOAD-EXTRACT-CLAIMS-LOCATION-01 | CLOSED at `8be62e0` | E1 executor preload caught extract_claims module-location drift before code edits |
| F-13-E2-PRELOAD-HANDOVER-SCOPE-DRIFT-01 | DEFERRED (Stage 14 checklist) | E2 handover scope description drift detected at preload; advisor edit preserved binding text |
| F-13-E2-PRELOAD-MEMORY-DESCRIPTION-STALE-01 | CLOSED (advisor edit) | Stale memory descriptor on Stage 13 G1 corrected during preload |
| F-13-E2-PRELOAD-CLOSE-MEMO-STUB-MISSING-01 | CLOSED (folded into this memo) | Pre-cycle close-memo stub absent; this document supersedes |

### §5.4 Cosmetic-only observations (informational; no Stage 13 action)

- **V2.A/V2.B/V2.C commit-subject em-dash rendered as `"?"`** — Codex/GPT-5 shell encoding artifact in those sessions. V2.D `3fc11c7` restored em-dash UTF-8 fidelity via commit-message-file path; V3.A `1ce9539` preserves the pattern. Per advisor §10: V2.A/B/C are NOT amended; encoding artifact is durable in commit history.
- **Mary H#7 buyer-language observations (3 cosmetic; no rejection)** — Teams/Slack class docstrings absent (cosmetic), BEGIN IMMEDIATE lock-rationale comment missing (cosmetic), `validate_claims` docstring mentions H#1.5 internal vocabulary (cosmetic). All accepted as Stage-13-vocabulary-OK; Stage 14 may polish during broader README pass.

---

## §6 Discipline + Pattern Captures

- **`feedback_preload_first_gating`** — H#0 preload reports issued by every executor before any code/document edit; surfacing of §0.5 F-13-HANDOVER-V2.D-AST-EXCLUSION-01 at H#0 demonstrates the discipline's value (advisor caught a spec contradiction PRE-implementation).
- **`feedback_handover_template_discipline`** — advisor + Cleo Code executor + Codex/GPT-5 executors all surfaced handover-template drift candidates at preload (10 F-13-HANDOVER/PRELOAD findings captured in §5.3); Stage 14 will fold these into a handover-template checklist amendment.
- **`feedback_no_waiver_discipline`** — strict-equality enforcer at `test_stage13_no_waiver_count.py` is the sole authority for Stage 13 NEW; tree-walk discovery + 9-path exclusion + synthetic drift canary make future marker additions structurally surface.
- **`feedback_corrigendum_paired_sweep`** — no namespace/layout corrigenda triggered Stage 13; ports / DTO surfaces preserved without REFREEZE.
- **`feedback_go_with_amendments_tracked`** — every advisor disposition (V2.A–V2.D charter R15/R16 + V3.A) carried amendment ledger verbatim into commit messages and this memo §findings.
- **`feedback_concurrent_executor_orchestration`** — 2-window parallel pattern preserved through E1 + E2 phases; cross-window contamination ZERO commits; path-scoped `git commit <pathspec>` discipline maintained.
- **`feedback_hard_constraint_word_boundary`** — `\bstrategic analysis\b` + `\bseamless\b` + `\benterprise-grade\b` regex grep on Stage 13 source surfaces: **zero hits** (verified at H#7 Mary PASS; re-verified at V3.A close via the §provenance HARD-constraint row).
- **`feedback_memory_authorization`** — no memory writes performed during the cycle on agent initiative; `project_verdaca_stage13_ratified` memory entry pending team-lead "save" post this close-memo commit.
- **`feedback_provenance_pin`** — §provenance table below uses Stage 12 close-memo schema as binding precedent.
- **`feedback_escalation_criticality_threshold`** — non-critical V3 findings (10/12) resolved on advisor initiative + documented in §5.2 carry-forward; only the V3 HIGH (F-13-V3-VKEY-BUDGET-OPTIONAL-01) triggered V3 fix-cycle dispatch.
- **`feedback_advisor_executor_model_effort`** — advisor + Claude Code executor both Opus 4.7 (1M context, MAX effort); Codex/GPT-5 predecessor executor windows aged out mid-V2.D and were inherited by single Claude Code executor (per handover §reason).
- **`feedback_preload_api_surface_verification`** + **`feedback_preload_tracking_status_verification`** — H#0 preload tracking-status sweep at executor activation verified binding-doc tracking states matched handover claims; no drift surfaced at this cycle's preload.

---

## §7 Implications for Stage 14

Stage 14 will inherit:

1. **10 V3 carry-forward findings** (§5.2) — vkey-audience double-decode, parse_activity claims-dict backdoor, per-request asyncio.run overhead, async-execute contract documentation, httpx connection pooling, JwksCache integration, ChannelContext.rate_limit_token rename, Charter v0.2 11-param ratification, done_callback CancelledError handling, GatewayCtxError cause_message field.
2. **Handover-template checklist amendment** (§5.3 R13-A items) — local-SHA citation discipline + commit-authority routing + E2-PRELOAD-HANDOVER-SCOPE-DRIFT closure.
3. **HYPOTHETICAL-VOC re-do gate** — per `project_verdaca_strategic_sequencing` finish-then-demo lock 2026-05-27, real VOC fires post-implementation+test demo. Stage 14 should NOT propose VOC as a stage-close blocker until then.
4. **Path A merge ceremony** — Stages 11+12+13 cumulative diff on `stage-13.0-production-hardening` not pushed to `origin`; merge to `main` deferred to first VOC demo or further stage trigger per D13.
5. **Stage 13 AST gates A–F as Stage 14 invariant baseline** — additions to `kernel/auth/`, `kernel/gateway/`, `adapters/channels/`, or `shell/api/` must preserve all 6 gates.
6. **Canonical pin floor `13 / 6 / 19`** — Stage 14 additions may increase but must not decrease the runtime no_waiver / AST gate counts.
7. **Auth contract: virtual_keys is REQUIRED at production deployment** — Stage 14 production wiring docs should explicitly call out the V3.A contract (`GatewayPolicy.virtual_keys` MUST be configured; misconfig fails LOUDLY at first request via `auth:builtins.RuntimeError`).
8. **`policy_health_check()`** — Stage 12 added bearer-token warning; consider adding vkey-presence warning at Stage 14 for operational symmetry with the V3.A binding contract.

---

## §provenance

| Field | Value |
|---|---|
| **Authored by** | Stage 13 advisor (Opus 4.7 1M MAX) + Claude Code executor (Opus 4.7 1M MAX) |
| **Authored date** | 2026-05-28 |
| **Working directory** | `C:\Users\AndreyPopov\Documents\Anthropic` |
| **Branch** | `stage-13.0-production-hardening` |
| **Close SHA** | `1ce9539` (V3.A — V1 C-1 acceptance criterion fully closed structurally) |
| **Base SHA** | `5306c8d` (Stage 12 hygiene tail tip on `stage-12.0-channel-adapters`) |
| **Stage 12 binding RATIFIED anchor** | `43f57ba` (preserved) |
| **Stage 13 implementation commit count** | 13 (`5306c8d..1ce9539`) |
| **uv workspace** | 22 active members (unchanged from Stage 12; no new workspace members in Stage 13) |
| **Test count** | 321 passed / 8 skipped / 1 warning |
| **Runtime no_waiver markers** | 13 (9 Stage 12 carry + 4 Stage 13 NEW) — strict-equality meta-test green |
| **Stage 13 AST gates** | 6 NEW (A–F) — co-enforced by `test_ast_gates_stage13.py` + sibling enumeration in `test_stage13_no_waiver_count.py` |
| **Total enforced markers** | 19 (canonical pin) |
| **HARD-constraint grep** | `\bstrategic analysis\b`, `\bseamless\b`, `\benterprise-grade\b` — **zero hits across Stage 13 source surfaces** (Mary H#7 PASS preserved at V3.A close; verified at memo authoring) |
| **Stage 12 no_waiver enforcer cardinality** | 9 (preserved; separate enforcer scope at `test_stage12_no_waiver_count.py`) |
| **Stage 11 baseline preserved** | M-T-GATEWAY-WIRING-NO-AUTH-LOGIC-01 still PASS (`kernel/gateway/policy.py` imports no `{authlib, cryptography, hashlib, hmac}`) |
| **Frozen Port surfaces** | `GatewayPort` + `ChannelAdapterPort` Protocol shapes unchanged (Stage 11 REFREEZE-02 preserved; no REFREEZE-03) |
| **Path-of-record** | `docs/stage-13-ratified-close-memo.md` (tracked per `.gitignore:61` negation `!docs/stage-*-ratified-close-memo.md`, overriding the broader `.gitignore:55 docs/*.md` ignore rule — ratified close memos are first-class repo artifacts) |
| **Predecessor close memo** | `docs/stage-12-ratified-close-memo.md` (tracked; Stage 12 RATIFIED 2026-05-27 at `43f57ba` + 3 hygiene commits tail `5306c8d`) |
| **Charter v0.2 (LOCKED)** | `_bmad-output/implementation-artifacts/verdaca/stage13/ports-architecture-delta.md` (gitignored) |
| **MAC-T catalog v0.2 (LOCKED)** | `_bmad-output/implementation-artifacts/verdaca/stage13/test-strategy-delta.md` (gitignored) |
| **H#1 substrate report** | `_bmad-output/implementation-artifacts/verdaca/stage13/substrate-probes-h1.md` (gitignored) |
| **Mary H#7 buyer-language audit (PASS)** | `_bmad-output/implementation-artifacts/verdaca/stage13/buyer-language-audit-h7.md` (gitignored) |
| **Cleo H#8 V4 review (PASS-WITH-AMENDMENTS)** | `_bmad-output/implementation-artifacts/verdaca/stage13/cleo-review-h8.md` (gitignored; V4 overwrites V1+V3) |
| **Advisor handover** | `docs/stage-13-advisor-handover.md` (gitignored per `docs/*.md`) |
| **Claude Code executor handover** | `docs/stage-13-claude-executor-handover.md` (gitignored per `docs/*.md`) |
| **E1 + E2 executor handovers** | `docs/stage-13-e1-auth-channel-hardening-executor-handover.md` + `docs/stage-13-e2-hygiene-data-plane-executor-handover.md` (gitignored per `docs/*.md`) |
| **Memory entries created this cycle** | None on agent initiative per `feedback_memory_authorization` |
| **Memory entry pending team-lead "save"** | `project_verdaca_stage13_ratified` (this memo's summary) |
| **VOC posture** | Compounding HYPOTHETICAL inherited from A7 (Stage 10 override `f181a7e` 2026-05-24); Stage 13 G2 closed via finish-then-demo lock per `project_verdaca_strategic_sequencing` 2026-05-27; real VOC gated to post-implementation+test demo |
| **Merge status** | Local-only per D13; `stage-13.0-production-hardening` chain (atop Stage 11 + Stage 12 cumulative diff) not pushed to `origin`; merge ceremony deferred to post-Stage-13 external trigger (demo or further stage close) |
| **Cleo V1 → V3 → V4 verdict progression** | V1 (Codex/GPT-5): FAIL → V3 (Claude Code, post-V2.D): FAIL (1 NEW HIGH residual gap) → V4 (Claude Code, post-V3.A): **PASS-WITH-AMENDMENTS** (5/5 V1 FULLY VERIFIED, 2/12 V3 CLOSED, 10/12 V3 carried to Stage 14) |
| **V1 closure ratio** | 5/5 (100% structurally verified) |
| **V3 closure / carry ratio** | 2 closed (1 HIGH + 1 MEDIUM at V3.A) / 10 carried (2 MEDIUM + 4 LOW + 4 WARNING) |

---

*End of Stage 13 RATIFIED Close Memo*
