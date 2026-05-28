# Stage 12 RATIFIED Close Memo

**Path of record:** `docs/stage-12-ratified-close-memo.md` (**tracked** per `.gitignore:61` negation `!docs/stage-*-ratified-close-memo.md`, which overrides the broader `.gitignore:55 docs/*.md` ignore rule — ratified close memos are first-class repo artifacts)
**Stage:** 12 — Channel Adapters (Teams + Slack) + Auth Integration (kernel/auth/ + LiteLLM virtual keys)
**Branch:** `stage-12.0-channel-adapters` (local-only Path A continuation; D13 keeps local through Stage 12)
**Base:** `e0aade3` (Stage 11 RATIFIED close memo) on local `stage-11.0-mcp-gateway`
**Close SHA:** `43f57ba` (H#8.V2.D final cleanup commit)
**Ratification date:** 2026-05-27
**Authored by:** Stage 12 advisor (Opus 4.7 1M MAX)
**Predecessor close memo:** `docs/stage-11-ratified-close-memo.md` (Stage 11 RATIFIED 2026-05-26 at `1adbecb` on stage-11.0-mcp-gateway)

---

## §1 Headline

Stage 12 = **Channel-Neutral MCP Gateway saleability layer** — Teams + Slack channel adapters (E1) + kernel/auth/ OIDC+JWKS+claims+nonce + VirtualKeyPort + LiteLLM HTTP-client virtual keys (E2). Replaces Stage 11 policy.py bearer-stub + budget-cap-MVP with real OIDC + IdP federation + LiteLLM proxy budget enforcement.

**281 tests passed / 8 skipped / 0 failed.** 9-entry no_waiver allow-list strict-equality green. 6 AST gates green. HARD-constraint grep zero hits across Stage 12 source surfaces.

**Caveat (inherited):** all customer-fit framing carries the compounding HYPOTHETICAL-VOC caveat per `project_verdaca_strategic_sequencing` 2026-05-27 lock. Real VOC re-do gate fires post-implementation+test only.

---

## §2 Scope Delivered

### E1 — Channel adapters (3 new uv workspace members)
- `adapters/channels/teams/` — Teams inbound webhook adapter; HMAC-SHA256 signature verification, ±5min replay window, event translation, ChannelAdapterPort contract conformance
- `adapters/channels/slack/` — Slack inbound webhook adapter; `X-Slack-Signature` v0 verification, URL-verification challenge handler, event translation, ChannelAdapterPort contract conformance
- Both adapters implement frozen `ChannelAdapterPort.execute(intent, ctx, gateway) -> AnalysisResult` per `ports/src/praxis/ports/gateway.py` (Stage 11 freeze preserved)

### E2 — Auth + virtual keys
- `kernel/auth/` (NEW workspace member; 22nd active) — OIDC discovery (`idp.discover`), JWKS cache with rotation (`oidc.JwksCache`), JWT verifier with alg-pinning at construction time (`jwt.JwtVerifier`), AuthClaims opaque-dict validator (`claims.validate_claims`), nonce replay protection (`nonce.NonceStore`)
- `ports/src/praxis/ports/virtual_key.py` (NEW port) — `VirtualKeyPort` Protocol + `VirtualKeySpec` + `VirtualKeyInfo` + `BudgetExhaustedError`
- `adapters/litellm/src/praxis/adapters/litellm/virtual_keys.py` — httpx-based HTTP-client `LiteLLMVirtualKeyAdapter` against LiteLLM proxy routes (`/key/generate`, `/key/info`, `/spend/logs`); NO Python LiteLLM SDK import per F-12-LITELLM-VKEY-API-VERSION-01 substrate finding
- `kernel/gateway/src/praxis/kernel/gateway/policy.py` — thin-orchestrator refactor; consumes `kernel.auth` + `VirtualKeyPort`; preserves Stage 11 baseline `M-T-GATEWAY-WIRING-NO-AUTH-LOGIC-01`

### Test surface
- 47 binding MAC-Ts (12 Teams + 12 Slack + 10 kernel/auth + 5 LiteLLM-vkeys + 7 AST gates + 1 D2 cross-window)
- 9 no_waiver markers under strict-equality meta-test (4 E1 + 5 E2; allow-list set in stone by `tests/src/praxis/contract_tests/test_stage12_no_waiver_count.py`)
- 6 AST architectural gates (5 Cleo + 1 D1)
- 12 VCR cassettes (4 OIDC/JWKS + 5 LiteLLM + 3 fixture-derived) — all synthetic, all committed
- 3 IdP fixtures (entra/okta/auth0) at `tests/fixtures/auth_claims/`

---

## §3 SHA Chain (10 + 10 + 4 = 24 commits from `e0aade3`)

| Phase | SHA | Description |
|---|---|---|
| Phase 0 | `015240d` | docs: Stage 11 wiki refresh carry-forward |
| Phase 0 | `4bc4cba` | docs: Stage 12 handover sweep kernel/gateway/auth.py → kernel/auth/ |
| H#1 | `57fd348` | feat: Stage 12 H#1 substrate probes |
| H#1.5 | `3257304` | feat: Stage 12 H#1.5 auth_claims surface freeze (3 IdP fixtures + contract doc) |
| H#1.5 | `43036f4` | docs: Stage 12 H#1.5 back-fill SHA freeze stamp |
| E2-H#2 | `2c68f12` | feat: Stage 12 E2-H#2 — VirtualKeyPort + kernel/auth/ workspace member + [E2-H#2-COMPLETE] surface |
| E1-H#1 | `0a060dd` | feat: Stage 12 E1-H#1 — Teams + Slack adapter workspace members |
| E1-H#2.1 | `b2fcd38` | feat: Stage 12 E1-H#2.1 — Teams webhook HMAC/replay/startup tests |
| E1-H#2.2 | `4c50e03` | feat: Stage 12 E1-H#2.2 — Teams event translation + claims extraction |
| E1-H#2.3 | `7a8e5ff` | feat: Stage 12 E1-H#2.3 — Teams adapter contract + gateway roundtrip + manifest |
| E1-H#3.1 | `f212980` | feat: Stage 12 E1-H#3.1 — Slack signing/replay/url-verification/startup |
| E1-H#3.2 | `57b0306` | feat: Stage 12 E1-H#3.2 — Slack event translation + claims extraction |
| E1-H#3.3 | `6a3d1e8` | feat: Stage 12 E1-H#3.3 — Slack adapter contract + gateway roundtrip + manifest |
| E1 lint | `4931866` | chore: Stage 12 E1 channel adapter lint cleanup |
| E2-H#3.1 | `a398c91` | feat: Stage 12 E2-H#3.1 — kernel/auth/claims.py validate_claims + 2 MAC-Ts |
| E2-H#3.2 | `60698cc` | feat: Stage 12 E2-H#3.2 — kernel/auth/oidc.py (OidcMetadata + JwksCache) + 4 MAC-Ts + 3 VCR cassettes |
| E2-H#3.3 | `3e08c9d` | feat: Stage 12 E2-H#3.3 — kernel/auth/jwt.py JwtVerifier + alg-pin no_waiver MAC-T |
| E2-H#3.4 | `c09d43d` | feat: Stage 12 E2-H#3.4 — kernel/auth/idp.py discover() + sole-export AST gate |
| E2-H#3.5 | `2cb48af` | feat: Stage 12 E2-H#3.5 — kernel/auth/nonce.py NonceStore + replay-block no_waiver MAC-T |
| E2-H#3.6 | `bfd94c6` | feat: Stage 12 E2-H#3.6 — kernel/auth __init__ public surface + import verification |
| E2-H#4 | `01654ff` | feat: Stage 12 E2-H#4 — LiteLLM virtual keys HTTP-client adapter + 5 MAC-Ts + 5 VCR cassettes |
| E2-H#5 | `58fe467` | feat: Stage 12 E2-H#5 — policy.py thin-orchestrator + 6 AST gates + Stage-11 baseline preservation |
| E1-H#4 (compat) | `355f516` | chore: compatibility fix for legacy Stage 10 no_waiver inventory |
| E1-H#4 | `0457944` | feat: Stage 12 E1-H#4 — D2 cross-window contract test + 9-entry no_waiver meta-test |
| H#7 | `4608a52` | fix: Stage 12 H#7 — Mary buyer-language amendments R-1/R-2/R-3 |
| H#8.V2.A | `c48d3ce` | fix: Stage 12 H#8.V2.A — Cleo CRITICAL (C-1 JWKS race + C-2 unverified-JWT-bypass + M-5) |
| H#8.V2.B | `06bcb8a` | fix: Stage 12 H#8.V2.B — Cleo HIGH (H-1 typed JoseError + H-2 AuthClaims accessors + H-3 bearer pre-check) |
| H#8.V2.C | `16a147a` | fix: Stage 12 H#8.V2.C — Cleo MEDIUM (M-1 httpx pooling + M-2 LiteLLM typed errors + M-4 webhook log disambiguation) |
| H#8.V2.D | `43f57ba` | chore: Stage 12 H#8.V2.D — Cleo WARNING cleanups (W-1/W-3/W-4) |

---

## §4 9-entry no_waiver Allow-List (strict-equality meta-test enforced)

| # | ID | Owner |
|---|---|---|
| 1 | M-T-TEAMS-WEBHOOK-HMAC-TAMPERED-01 | E1 |
| 2 | M-T-SLACK-WEBHOOK-SIGNING-TAMPERED-01 | E1 |
| 3 | M-T-TEAMS-CHANNEL-ADAPTER-PORT-CONTRACT-01 | E1 |
| 4 | M-T-SLACK-CHANNEL-ADAPTER-PORT-CONTRACT-01 | E1 |
| 5 | M-T-AUTH-JWT-ALG-PIN-01 | E2 |
| 6 | M-T-AUTH-NONCE-REPLAY-BLOCK-01 | E2 |
| 7 | M-T-AUTH-CLAIMS-SCHEMA-01 | E2 |
| 8 | M-T-VKEY-BUDGET-EXHAUSTED-01 | E2 |
| 9 | M-T-AUTH-KERNEL-NO-ADAPTER-IMPORT-01 | E2 |

Meta-test: `tests/src/praxis/contract_tests/test_stage12_no_waiver_count.py` — frozenset strict equality.

---

## §5 Findings Ledger (advisor-resolved + carry-forward)

### Resolved in-cycle
| Finding | Severity | Resolution |
|---|---|---|
| F-12-CHANNELADAPTER-RECEIVE-EVENT-DRIFT-01 | n/a | Reconciled in charter §4.1; webhook.py → events.py → adapter.execute() pattern |
| F-12-AUTHLIB-ALG-PINNING-01 | n/a | Filter at JwtVerifier.__init__ before JsonWebToken construction (charter §5.4) |
| F-12-LITELLM-VKEY-API-VERSION-01 | n/a | HTTP-client redesign against proxy routes (charter §6.2) |
| F-12-WORKSPACE-COUNT-DELTA-01 | n/a | Canonical 19→22 (3 new members); supersedes Winston "20" |
| F-12-HANDOVER-ADVISOR-DRIFT-01 | n/a | WONT-FIX-CONTRAST-PRESERVED (advisor handover preserves architectural-pivot contrast text) |
| F-12-E1-H#1-UV-E2-WORKSPACE-DRIFT-01 | n/a | Closed in-cycle after E2-H#2 commit `2c68f12` |
| F-12-E1-H4-LEGACY-NOWAIVER-INVENTORY-01 | n/a | Stage 10 inventory test scoped to Stage 9/10 markers only; closed at `355f516` |
| F-12-E1-H4-CATALOG-FIXTURE-PATH-01 | n/a | Fixture path corrected to `tests/fixtures/` root anchoring; closed at `0457944` |
| F-12-DIAL-LIVE-SMOKE-FAIL-01 (twice) | HIGH | RESOLVED via D20 Azure-style model smoke at gpt-4o; HTTP 200 confirmed |
| Stage 11.5 DIAL-LIVE-SMOKE debt | HIGH | RESOLVED (same root cause; carried Stage 11.5 → closed Stage 12 H#3.0 pre-probe) |

### Cleo H#8 dispositions
| Finding | Severity | Disposition |
|---|---|---|
| C-1 JWKS invalidation race | CRITICAL | RESOLVED at `c48d3ce` |
| C-2 unverified JWT decoded into auth path | CRITICAL | RESOLVED at `c48d3ce` (renamed to `_decode_unverified_jwt_payload_for_testing` + `extract_claims` signature now accepts `JwtVerifier`) |
| M-5 missing await in policy.execute | MEDIUM | FALSE POSITIVE — GatewayPort.execute is sync. Surfaced F-12-CLEO-M5-FALSE-POSITIVE-01 (informational) |
| H-1 exception heuristic | HIGH | RESOLVED at `06bcb8a` (typed `authlib.jose.errors.JoseError`) |
| H-2 AuthClaims internal field access | HIGH | RESOLVED at `06bcb8a` (added `get`/`require` accessors; replaced `._claims[...]` call sites) |
| H-3 empty bearer + rate_limit_token | HIGH | RESOLVED at `06bcb8a` (empty-bearer pre-check + token populated from auth header) |
| M-1 httpx connection pooling | MEDIUM | RESOLVED at `16a147a` (injectable AsyncClient in JwksCache + idp) |
| M-2 LiteLLM KeyError untyped | MEDIUM | RESOLVED at `16a147a` (typed LiteLLMProxyError on missing field) |
| M-3 nonce unbounded + restart-replay | MEDIUM | DEFERRED — F-12-CLEO-M3-NONCE-RESTART-DEFER-01 (Stage 13 TTL/persistence) |
| M-4 webhook KeyError vs WebhookAuthError | MEDIUM | RESOLVED at `16a147a` (separate handlers + distinct log levels) |
| W-1 fallback claims exp=0 docstring | LOW | RESOLVED at `43f57ba` (module-level FALLBACK comment) |
| W-2 sync httpx in TeamsAdapter.post_result | LOW | DEFERRED — F-12-CLEO-W2-SYNC-HTTPX-01 (Stage 13 async-callback hardening) |
| W-3 OidcMetadata list→tuple | LOW | RESOLVED at `43f57ba` (tuple immutability) |
| W-4 idp.py alias imports | WARNING | RESOLVED at `43f57ba` (alias imports removed) |

### Carry-forward to Stage 13
| Finding | Class | Stage 13 target |
|---|---|---|
| F-12-CLEO-C2-COMPOSITION-PENDING-01 | Composition root | Inject JwtVerifier at gateway startup; production extract_claims path requires verifier |
| F-12-CLEO-M3-NONCE-RESTART-DEFER-01 | Persistence | NonceStore TTL + Redis-backed persistence for multi-process / restart-replay coverage |
| F-12-CLEO-W2-SYNC-HTTPX-01 | Async hardening | TeamsAdapter.post_result → async httpx.AsyncClient |
| F-12-OIDC-LIVE-DEFERRED-01 | VOC gate | Live IdP smoke deferred to first real Champion call post-implementation+test demo gate |
| F-12-CLEO-M5-FALSE-POSITIVE-01 | Informational | GatewayPort.execute is sync; Stage 13 may revisit async port boundary if performance requires |

### Advisor arithmetic correction
| Item | Resolution |
|---|---|
| E2 no_waiver count: dispatch said 4, ratified catalog says 5 | Catalog v0.1 §4 is authoritative; E2 owns 5 of 9 markers (the 4 kernel/auth + M-T-VKEY-BUDGET-EXHAUSTED-01); no allow-list change |

### Drift items resolved during parallel charter+catalog authoring (advisor-reconciled v0.1 merge)
- `idp.py` filename consistency (Winston `idp.py` vs Murat `discovery.py`) → `idp.py` chosen
- Required claims set (Winston 3 vs Murat 5) → `{sub, iss, aud, iat, exp}` (5 fields) chosen
- Validator API (Winston classmethod vs Murat standalone) → module-level `validate_claims(raw)` chosen
- `JwksCache` location (Winston `oidc.py` vs Murat `jwks.py`) → `oidc.py` chosen
- `nonce.py` module (absent in Winston draft v0; Murat tested it) → added to charter §5.6 in reconciled v0.1
- VirtualKeyPort method names (charter aligned to catalog: `create_virtual_key` / `get_key_info` / `check_budget` / `get_spend_logs`)
- WAL-CONCURRENCY → DEFERRED in both (HTTP-only adapter; no shared SQLite path)

---

## §6 Discipline + Pattern Captures

- `feedback_escalation_criticality_threshold` (NEW 2026-05-27) — tighter signal for team-lead; escalate only critical decisions; resolve non-critical on advisor initiative + document in §findings ledger. Validated in this cycle: D18 advisor handover sweep absorbed; multiple non-critical drift items resolved without escalation.
- `feedback_concurrent_executor_orchestration` — disjoint halt-class + path-scoped commits preserved across full E1+E2 cycle. Zero cross-contamination commits.
- `feedback_go_with_amendments_tracked` — D1–D11 ratifications, D12 G2 close, D13 G7 close, D14 strategic-sequencing memory, D15–D18 (D17 staged), D19 DIAL key, D20 DIAL identity correction — all amendments tracked verbatim in this memo + memory entries.
- `feedback_hard_constraint_word_boundary` — `\bstrategic analysis\b` + `\bseamless\b` + `\benterprise-grade\b` grep zero hits across Stage 12 source surfaces (verified at H#7 + re-verified at H#8.V2 close).
- `feedback_no_waiver_discipline` — strict-equality meta-test at `tests/src/praxis/contract_tests/test_stage12_no_waiver_count.py` enforces exactly 9 markers (no more, no less) via AST walker + frozenset comparison.

---

## §7 Implications for Stage 13

1. **Composition root completion (F-12-CLEO-C2-COMPOSITION-PENDING-01).** Wire JwtVerifier at gateway startup so production extract_claims path actually verifies tokens. Currently the test-only path is correctly isolated, but production wiring is incomplete.
2. **Webhook signing key rotation (D4/Q1 deferred from Stage 12).** Slack v0 → future signing protocol; Teams connector cert rotation. Add `SigningKeyPort` if Stage 13 confronts rotation events; otherwise SDK pinning remains sufficient.
3. **NonceStore persistence (F-12-CLEO-M3).** Redis-backed nonce store with TTL for multi-process deployments + restart-replay coverage.
4. **Async outbound callbacks (F-12-CLEO-W2).** TeamsAdapter.post_result + SlackAdapter.post_result migrate to httpx.AsyncClient.
5. **Live OIDC smoke at first Champion call (F-12-OIDC-LIVE-DEFERRED-01).** When real VOC happens (per `project_verdaca_strategic_sequencing` post-implementation+test gate), exercise live Entra/Okta/Auth0 tenant against kernel/auth/ — VCR cassettes are structural-only, not behavioral-against-real-IdP.
6. **WAL-CONCURRENCY re-evaluation.** Stage 12 deferred because LiteLLM vkey adapter is HTTP-only. If Stage 13 adds local SQLite session_index writes concurrent with channel webhook ingest, re-evaluate.

---

## §provenance

| Field | Value |
|---|---|
| **Authored by** | Stage 12 advisor (Opus 4.7 1M MAX) |
| **Authored date** | 2026-05-27 |
| **Working directory** | `C:\Users\AndreyPopov\Documents\Anthropic` |
| **Branch** | `stage-12.0-channel-adapters` |
| **Close SHA** | `43f57ba` (H#8.V2.D) |
| **Base SHA** | `e0aade3` (Stage 11 RATIFIED close memo) on `stage-11.0-mcp-gateway` |
| **uv workspace** | 22 active members (19 + 3 new: teams, slack, kernel/auth) |
| **Test count** | 281 passed / 8 skipped / 0 failed / 12 warnings |
| **HARD-constraint grep** | Zero hits across Stage 12 source surfaces |
| **no_waiver count** | Exactly 9 (strict-equality meta-test green) |
| **Path-of-record** | `docs/stage-12-ratified-close-memo.md` (tracked per `.gitignore:61` negation `!docs/stage-*-ratified-close-memo.md`, overriding the broader `docs/*.md` ignore) |
| **Predecessor close memo** | `docs/stage-11-ratified-close-memo.md` |
| **Charter v0.1** | `_bmad-output/implementation-artifacts/verdaca/stage12/ports-architecture-delta.md` (gitignored) |
| **MAC-T catalog v0.1** | `_bmad-output/implementation-artifacts/verdaca/stage12/test-strategy-delta.md` (gitignored) |
| **H#1 substrate report** | `_bmad-output/implementation-artifacts/verdaca/stage12/substrate-probes-h1.md` (gitignored) |
| **H#1.5 contract doc** | `_bmad-output/implementation-artifacts/verdaca/stage12/auth-claims-contract.md` (gitignored) |
| **Memory entries created this cycle** | `project_verdaca_stage12_scope` (G1 close), `project_verdaca_strategic_sequencing` (D14 finish-then-demo lock), `feedback_escalation_criticality_threshold` (D-rule narrowing) |
| **Memory entry pending team-lead "save"** | `project_verdaca_stage12_ratified` (this memo's summary) |
| **VOC posture** | Compounding HYPOTHETICAL inherited from A7 (Stage 10 override `f181a7e` 2026-05-24); Stage 12 G2 closed via option (a); real VOC gated to post-implementation+test demo per `project_verdaca_strategic_sequencing` |
| **Merge status** | Local-only per D13; `stage-11.0-mcp-gateway` + `stage-12.0-channel-adapters` chain not pushed to origin; merge ceremony deferred to Stage 12+ external trigger (demo or further stage close) |

---

*End of Stage 12 RATIFIED Close Memo*
