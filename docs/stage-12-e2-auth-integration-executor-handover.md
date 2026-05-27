# Handover B.E2 — Stage 12 Auth Integration (OAuth/OIDC + LiteLLM Virtual Keys)

**Path of record:** `docs/stage-12-e2-auth-integration-executor-handover.md` (gitignored-operational)
**Persona:** Executor — clean session
**Authored:** 2026-05-26 by Stage 11 RATIFIED close advisor (Opus 4.7 1M, MAX thinking)
**REFRESHED:** 2026-05-27 — applied BMAD roundtable opening positions (Winston `kernel/auth/` pivot, Murat MAC-T+no_waiver expansion, Mary HARD-constraint additions, Vera corpus state) + wiki sync + graphify Stage 11 source-scope refresh
**Parent handover:** `docs/stage-12-implementation-executor-handover.md`
**Sibling handover:** `docs/stage-12-e1-channel-adapters-executor-handover.md` (commit-authority window)
**Window:** E2 — **surfaces commits to E1 for landing** per `feedback_concurrent_executor_orchestration`
**Routing tag:** `[E2-H{N}]` for all findings, surfaces, halt markers
**Halt class:** GATE-AUTH

**Scope is TENTATIVE — Winston + roundtable ratifies at parent §3.1 charter halt; revise this handover before [E2-H#1] preload if scope shifts.**

**REFRESH NOTE — load-bearing deltas from 2026-05-27 BMAD roundtable:**
- **Winston #2026-05-27:** Auth module home = `kernel/auth/` (NEW cross-cutting module), **not gateway-local auth**. Auth is not gateway-specific — coupling OAuth/OIDC primitives to the MCP gateway lifecycle blocks Stage 13+ consumers (SessionIndex direct API, learning ports). `policy.py` becomes a thin orchestrator that **consumes** `kernel.auth` and `adapters.litellm.virtual_keys` rather than embedding the auth logic itself. This affects §3 Blast radius, §4 [E2-H#2] paths, §5 commit-surface paths, §6 integration handshake imports, §9 references — all updated below.
- **Murat #2026-05-27:** MAC-T scope expansion to **~20 entries for E2** (was 5-10): M-T-AUTH-OIDC-{1..12} (discovery + JWKS rotation + nbf/exp/aud validation + signature algorithm pinning + claim mapping + refresh + revocation + multi-IdP Entra/Okta/Auth0 fixture matrix) + M-T-VKEY-{1..8} (budget enforcement + overrun + key rotation + scope/tenant binding + cost_meter observability). **no_waiver: propose 4-5 of the 7-9 Stage 12 candidates land in E2** (OAuth signature/JWKS validation, virtual-key budget hard-overrun, IdP discovery TLS pinning, token replay/nbf clock-skew window).
- **Murat #2026-05-27:** `[E2-H#2-COMPLETE]` MUST be defined as a **contract artifact** (`auth_claims` schema frozen + 3-5 fixture claims published as JSON files E1 can consume), NOT a vibes-check. E1 codes against the fixture; integration test runs post-merge.
- **Murat #2026-05-27:** **DIAL-LIVE-SMOKE MUST land before E2 deploys** (Stage 11.5 debt item; HIGH risk — OIDC against a live IdP without an end-to-end smoke is flying blind). Verify availability of Entra dev tenant OR confirm DIAL is sole live IdP at [E2-H#1] preload.
- **Mary #2026-05-27:** HARD-constraint expansion — `\bseamless\b` + `\benterprise-grade\b` added to forbidden-token grep (word-boundary, case-sensitive) for any auth-related user-facing copy (error messages, IdP setup docs, README fragments). `\bstrategic analysis\b` from Stage 11 carries forward.

**Authorized models:**
- Advisor: Opus 4.7 (1M context), MAX thinking
- Executor: advisor-set per phase. Default — Codex/GPT-5 high reasoning for impl; Opus 4.7 (1M) for sub-charter / amendment phases. Surface actual model in [E2-H#1].

**Memory authorization:** Per `feedback_memory_authorization` — executor proposes; advisor authorizes; team-lead "save" writes.

---

## §1 Preload — session-surface audit ([E2-H#1])

Surface in first response, before any action:

1. **Session ID / model / JSONL path / working directory** (per `feedback_session_surface_audit`).
2. **Active branch** — `stage-12.0-channel-adapters` (shared with E1 window; verify with `git log --oneline -1`).
3. **Memory state** — confirm loaded: `project_verdaca_stage11_ratified`, `project_verdaca_stage10_ratified`, `project_verdaca_stage10_11_decision`, `feedback_concurrent_executor_orchestration`, `feedback_memory_authorization`, `feedback_advisor_executor_model_effort`, `feedback_provenance_pin`, `feedback_handover_template_discipline`.
4. **Handover-template drift check** — surface `F-12-E2-HANDOVER-{N}` at [E2-H#1] if any path / section-role / SHA does not resolve.
5. **Stage 12 charter loaded** — `_bmad-output/implementation-artifacts/verdaca/stage12/ports-architecture-delta.md` v0.1+ ratified.
6. **OAuth/OIDC library available** — verify authlib (or alternative chosen at H#1 substrate probe) imports cleanly; verify against a sample IdP discovery URL (e.g., `https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration` for Entra; equivalent for Okta/Auth0).
7. **LiteLLM virtual keys library available** — verify `litellm` Python SDK exposes the virtual keys API (e.g., `litellm.create_virtual_key`, `litellm.check_key_budget`); STAGE-11-DEBT-LITELLM-VKEY-01 documented the dependency.
8. **E1 status check** — confirm E1 window state:
   - If E1 has surfaced `[E1-H#3.3-COMPLETE]` (Slack adapter wiring needs auth) → E2 work has consumer ready
   - If E1 still in [E1-H#2.x] (Teams skeleton) → E2 proceeds independently through [E2-H#2] OAuth/OIDC + [E2-H#3] LiteLLM vkeys; E1 will consume at their adapter wiring halts
9. **Sibling-window coordination** — cross-window drift surfaced via `F-12-E1-E2-DRIFT-*`; E1 holds commit authority.

---

## §2 Entry preconditions (BLOCKING — verify before [E2-H#2])

Parent §3 H#A12 (if applicable) + H#1 + H#2 + H#3 MUST be CLOSED before E2 opens (same as E1).

| # | Precondition | Verification |
|---|---|---|
| 1 | A12 closed (if abbreviated VOC chosen) | `docs/stage-12-voc-gate.md` shows `provisional_voc=False` OR parent charter §VOC documents HYPOTHETICAL inheritance |
| 2 | H#1 §3.0 substrate probes GREEN | OAuth library + LiteLLM virtual keys API surface tests passing |
| 3 | H#2 §3.1 charter ratified | Stage 12 v0.1+ charter exists; auth integration design ratified (`kernel/auth/` + `adapters/litellm/virtual_keys.py` + `policy.py` refactor scope confirmed) |
| 4 | H#3 §3.2 MAC-T catalog ratified | Stage 12 v0.1+ test-strategy delta exists; auth-related MAC-Ts allocated to E2 (TBD by Murat; expected M-T-AUTH-OAUTH-JWT-VERIFY-01, M-T-AUTH-LITELLM-VKEY-BUDGET-01, etc.) |
| 5 | `stage-12.0-channel-adapters` branch exists | `git rev-parse stage-12.0-channel-adapters` |
| 6 | Working tree clean within E2 path scope | `git status` shows no uncommitted changes under `kernel/auth/`, `adapters/litellm/virtual_keys.py`, or E2 test files |
| 7 | Stage 11 policy.py + bearer MVP intact | `kernel/gateway/policy.py` carries STAGE-11-DEBT-AUTH-01 + STAGE-11-DEBT-LITELLM-VKEY-01 TODOs; bearer token MVP functional |
| 8 | E1 status known | Either (a) E1 not started → E2 proceeds independently; (b) E1 in flight → coordinate cross-window dependency on auth_claims wiring |

If any precondition fails → HALT, surface `F-12-E2-PRELOAD-{N}` to advisor.

---

## §3 E2 Scope

**Parent §§:** §3.3 (TENTATIVE) — auth integration replacing policy.py MVP
**Halt class:** GATE-AUTH
**Blast radius (REVISED per Winston #2026-05-27 — `kernel/auth/` pivot):**
- `kernel/auth/` (NEW module — cross-cutting auth substrate, not gateway-specific)
  - `kernel/auth/pyproject.toml`
  - `kernel/auth/src/praxis/kernel/auth/__init__.py`
  - `kernel/auth/src/praxis/kernel/auth/oidc.py` — OIDC discovery, JWKS cache + rotation
  - `kernel/auth/src/praxis/kernel/auth/jwt.py` — JWT validation (signature alg pinning, nbf/exp/aud)
  - `kernel/auth/src/praxis/kernel/auth/claims.py` — AuthClaims mapper (consumes ports/gateway_dto.AuthClaims DTO)
  - `kernel/auth/src/praxis/kernel/auth/idp.py` — IdP discovery registry (Entra/Okta/Auth0 templates)
- `adapters/litellm/src/praxis/adapters/litellm/virtual_keys.py` (NEW)
- `kernel/gateway/src/praxis/kernel/gateway/policy.py` (refactor — becomes thin orchestrator consuming `praxis.kernel.auth` + `praxis.adapters.litellm.virtual_keys`; no auth logic embedded)
- Auth-specific test seams: `tests/src/praxis/contract_tests/auth/` (new sub-tree) + `tests/.../test_gateway_policy_contract.py` (existing — extended for delegation tests)
- `pyproject.toml` (root workspace member registration for `kernel/auth`) + `uv.lock`

**MAC-Ts owned (REVISED per Murat #2026-05-27):** Expected **~20 entries**:
- **M-T-AUTH-OIDC-{1..12}** (~12): discovery, JWKS rotation, nbf/exp/aud validation, signature-algorithm pinning, claims mapping into AuthClaims, refresh, revocation, multi-IdP fixture matrix (Entra/Okta/Auth0), TLS pinning for IdP discovery URL, claim-required-but-missing rejection, issuer mismatch rejection, audience mismatch rejection
- **M-T-VKEY-{1..8}** (~8): per-key budget enforcement pre-call, overrun behavior (rejection without invoking LLMProxyPort), key rotation, scope/tenant binding, model allow-list rejection, observability into pi_mono cost_meter, key lookup for unknown user-workspace creates default key, key fetch idempotent

**no_waiver candidates owned (REVISED per Murat #2026-05-27):** 4-5 of the 7-9 Stage 12 candidates land in E2 (strong priors):
- `M-T-AUTH-OIDC-JWKS-VERIFY-01` — JWT signature/JWKS validation (auth bypass = RCE-equivalent)
- `M-T-VKEY-BUDGET-HARD-OVERRUN-01` — virtual-key budget enforcement (financial blast radius)
- `M-T-AUTH-OIDC-TLS-PIN-01` — IdP discovery TLS pinning (medium prior; depends on charter ratification)
- `M-T-AUTH-OIDC-CLOCK-SKEW-01` — token replay / nbf clock-skew window (medium prior)
- Final list ratified in Stage 12 allow-list delta — strict equality meta-test; never on initiative per `feedback_no_waiver_discipline`.

**Out of E2 scope (E1 owns):** `adapters/channels/teams/`, `adapters/channels/slack/`, ChannelContext population in adapters (E2 provides `validate_jwt` + `map_claims_to_auth_claims`; E1 calls them). **NEVER touch these paths.**

**Out of E1 + E2 scope but informational:** Stage 11 MCP adapter at `adapters/mcp_server/` — DO NOT TOUCH (Stage 11 RATIFIED). Stage 11 policy.py bearer MVP stays functional alongside new OAuth integration until refactor at [E2-H#4].

---

## §4 E2 Halt sequence (TENTATIVE)

- **[E2-H#1]** — preload + entry preconditions (§§1+2)

- **[E2-H#2]** — OAuth/OIDC integration (REVISED per Winston #2026-05-27 — `kernel/auth/` module, not gateway-local auth):
  - `kernel/auth/` NEW workspace member (registered in root `pyproject.toml` `[tool.uv.workspace] members` — 19→20 active)
  - Module structure:
    ```
    kernel/auth/
      pyproject.toml
      src/praxis/kernel/auth/
        __init__.py         # public API: validate_jwt, map_claims_to_auth_claims, discover_idp
        oidc.py             # OIDC discovery + JWKS cache + rotation
        jwt.py              # JWT validation (signature alg pinning, nbf/exp/aud)
        claims.py           # AuthClaims mapper (consumes ports/gateway_dto.AuthClaims DTO)
        idp.py              # IdP registry (Entra/Okta/Auth0 templates)
    ```
    ```python
    # Public API (kernel/auth/src/praxis/kernel/auth/__init__.py):

    def validate_jwt(token: str, *, issuer: str | None = None) -> Mapping[str, str]:
        """Validate JWT against IdP JWKS; return claims dict for AuthClaims."""

    def map_claims_to_auth_claims(claims: Mapping[str, str]) -> AuthClaims:
        """Standardized mapping: oid → caller_id, name → display_name, etc.
        Consumes ports.gateway_dto.AuthClaims DTO (Stage 11 FROZEN)."""

    def discover_idp(issuer_url: str) -> IdPMetadata:
        """OIDC discovery via /.well-known/openid-configuration; TLS-pinned."""
    ```
  - **Canonical import path:** `praxis.kernel.auth` ONLY (mirrors Winston #2 Stage 11 discipline for gateway). No re-exports through `praxis.kernel.gateway`.
  - Tests at `tests/src/praxis/contract_tests/auth/test_kernel_auth_contract.py`:
    - **`M-T-AUTH-OIDC-JWKS-VERIFY-01`** (no_waiver — strong prior): valid signed JWT validates; invalid signature rejected; expired token rejected; wrong issuer rejected; wrong audience rejected
    - `M-T-AUTH-OIDC-DISCOVERY-01`: JWKS endpoint reachable + cached per RFC 7517; rotation triggered on `kid` miss
    - `M-T-AUTH-OIDC-TLS-PIN-01` (no_waiver candidate): IdP discovery URL hits TLS-pinned cert
    - `M-T-AUTH-CLAIMS-MAPPING-01`: claims dict maps to AuthClaims correctly across Entra/Okta/Auth0 fixtures
    - `M-T-AUTH-OIDC-CLOCK-SKEW-01` (no_waiver candidate): nbf clock-skew window respected (±60s default)
    - Multi-IdP fixture matrix: Entra `oid` + name; Okta `sub` + email; Auth0 `sub` + nickname
  - **[E2-H#2-COMPLETE] DEFINED AS CONTRACT ARTIFACT per Murat #2026-05-27** — NOT a vibes-check. To close H#2:
    1. `praxis.kernel.auth.validate_jwt` + `map_claims_to_auth_claims` + `discover_idp` signatures FROZEN (commit + freeze SHA stamp, mirroring Stage 11 REFREEZE pattern)
    2. **3-5 fixture claims files published** at `tests/fixtures/auth_claims/` (JSON; representative shapes for Entra, Okta, Auth0; E1 codes against these fixtures, integration test runs post-merge)
    3. AuthClaims schema documented in `_bmad-output/implementation-artifacts/verdaca/stage12/auth-claims-contract.md` (freeze SHA stamp commit)
    4. Surface `[E2-H#2-COMPLETE]` post to E1 with explicit fixture paths + freeze SHA — E1 wires `auth_claims` against these fixtures immediately.

- **[E2-H#3]** — LiteLLM virtual keys integration:
  - **PRECONDITION:** DIAL-LIVE-SMOKE landed (Stage 11.5 debt item; per Murat #2026-05-27 — HIGH risk to deploy E2 without it). If DIAL-LIVE-SMOKE not yet closed, HALT and surface `F-12-E2-DIAL-SMOKE-MISSING-01` to advisor.
  - `adapters/litellm/src/praxis/adapters/litellm/virtual_keys.py` NEW
  - Module structure:
    ```python
    # LiteLLM virtual keys API integration
    # Per-key budget + model allow-list + TPM/RPM caps
    # Replaces policy.py budget-cap MVP

    def get_virtual_key_for_user(user_id: str, *, workspace_id: str) -> str:
        """Lookup or create LiteLLM virtual key for user-workspace pair."""

    def check_budget(virtual_key: str) -> BudgetCheckResult:
        """Pre-call budget check against LiteLLM-managed cap."""

    def rotate_key(virtual_key: str) -> str:
        """Key rotation primitive (M-T-VKEY-ROTATE-01)."""
    ```
  - Tests at `tests/src/praxis/contract_tests/ports/test_litellm_virtual_keys_contract.py`:
    - **`M-T-VKEY-BUDGET-HARD-OVERRUN-01`** (no_waiver — strong prior): pre-call budget check rejects over-cap WITHOUT invoking LLMProxyPort (financial blast radius)
    - `M-T-VKEY-LOOKUP-01`: virtual key lookup returns existing key for known user; creates default for unknown user-workspace
    - `M-T-VKEY-MODEL-ALLOWLIST-01`: model not in allow-list rejected
    - `M-T-VKEY-ROTATE-01`: key rotation primitive
    - `M-T-VKEY-SCOPE-BIND-01`: virtual key scope/tenant binding
    - `M-T-VKEY-COST-METER-OBS-01`: virtual key usage observed in `pi_mono cost_meter` (cross-Port wiring)
    - `M-T-VKEY-IDEMPOTENT-FETCH-01`: repeated `get_virtual_key_for_user` returns same key
    - `M-T-VKEY-TPM-RPM-CAP-01`: TPM/RPM caps enforced

- **[E2-H#4]** — policy.py refactor (REVISED per Winston #2026-05-27 — thin orchestrator consuming `praxis.kernel.auth`, NOT embedding auth logic):
  - `kernel/gateway/src/praxis/kernel/gateway/policy.py` becomes thin orchestrator
  - Bearer-token MVP STAYS for fallback (HTTP transport without OAuth still works); STAGE-11-DEBT-AUTH-01 TODO REMOVED from policy.py header (resolved via `kernel.auth`)
  - `verify_bearer_token` delegates to: `praxis.kernel.auth.validate_jwt()` if Authorization header is OAuth Bearer + IdP-configured; else fall back to legacy bearer token
  - `check_budget` delegates to: `praxis.adapters.litellm.virtual_keys.check_budget()` if virtual key configured for user; else fall back to legacy cost-meter cap; STAGE-11-DEBT-LITELLM-VKEY-01 TODO REMOVED
  - `policy_health_check()` updated to check `praxis.kernel.auth.discover_idp()` health + LiteLLM virtual keys API health
  - **Architectural invariant (Winston #2026-05-27):** policy.py imports only from `praxis.kernel.auth` and `praxis.adapters.litellm.virtual_keys` for auth/budget — NO direct OIDC/JWT logic embedded. This keeps `kernel.auth` available to Stage 13+ consumers (SessionIndex direct API, learning ports) without re-coupling to gateway lifecycle.
  - Tests at `tests/src/praxis/contract_tests/ports/test_gateway_policy_contract.py` (existing — extended):
    - Existing tests still GREEN (backward compat)
    - New: `M-T-GATEWAY-WIRING-POLICY-AUTH-DELEGATION-01`: policy.py delegates to `praxis.kernel.auth` when OAuth configured
    - New: `M-T-GATEWAY-WIRING-POLICY-VKEY-DELEGATION-01`: policy.py delegates to `virtual_keys` when LiteLLM virtual key configured
    - New: `M-T-GATEWAY-WIRING-NO-AUTH-LOGIC-01`: AST-level check that `policy.py` contains no `jwt.decode` / `jwks` / `authlib` imports (only delegation to `praxis.kernel.auth`)

- **[E2-H#5]** — Surface F-12-E2-COMMIT-SURFACE-1 to E1 for landing. Paths (REVISED per kernel/auth/ pivot):
  - **`kernel/auth/`** (NEW workspace member): pyproject.toml + src/praxis/kernel/auth/{__init__.py, oidc.py, jwt.py, claims.py, idp.py}
  - `adapters/litellm/src/praxis/adapters/litellm/virtual_keys.py` (NEW)
  - `kernel/gateway/src/praxis/kernel/gateway/policy.py` (refactor — thin orchestrator)
  - `tests/src/praxis/contract_tests/auth/test_kernel_auth_contract.py` (NEW sub-tree)
  - `tests/src/praxis/contract_tests/ports/test_litellm_virtual_keys_contract.py` (NEW)
  - `tests/src/praxis/contract_tests/ports/test_gateway_policy_contract.py` (extended)
  - `tests/fixtures/auth_claims/{entra,okta,auth0}_*.json` (3-5 fixture files per Murat #2026-05-27)
  - `_bmad-output/implementation-artifacts/verdaca/stage12/auth-claims-contract.md` (NEW — H#2 freeze artifact)
  - Workspace `pyproject.toml` + `uv.lock` E2 portions (`kernel/auth` workspace member registration + auth deps + LiteLLM virtual keys dep)

Advisor confirms at every halt. Memory writes only on explicit team-lead "save".

---

## §5 Path-scoped commit discipline (E2 surfaces; E1 lands)

Per `feedback_concurrent_executor_orchestration` shared-index H#4 hardening:

E2 has NO commit authority. E2 stages content locally, verifies path scope, then surfaces a `F-12-E2-COMMIT-SURFACE-{N}` post to E1:

```
F-12-E2-COMMIT-SURFACE-{N}
Paths staged (REVISED per Winston #2026-05-27 kernel/auth/ pivot):
  kernel/auth/                          # NEW workspace member
  adapters/litellm/src/praxis/adapters/litellm/virtual_keys.py
  kernel/gateway/src/praxis/kernel/gateway/policy.py    # refactor only
  tests/src/praxis/contract_tests/auth/test_kernel_auth_contract.py
  tests/src/praxis/contract_tests/ports/test_litellm_virtual_keys_contract.py
  tests/src/praxis/contract_tests/ports/test_gateway_policy_contract.py
  tests/fixtures/auth_claims/{entra,okta,auth0}_*.json  # H#2 contract fixtures
  pyproject.toml                         # kernel/auth workspace member registration (19→20 active)
  uv.lock                                # auth deps + LiteLLM virtual keys dep
Commit message proposal:
  feat: Stage 12 E2 — kernel/auth/ + LiteLLM virtual keys + policy.py orchestrator refactor (surfaced by E2)
Pre-commit verification:
  - mypy strict on kernel/auth/src + kernel/gateway/src + adapters/litellm/src: clean
  - ruff on touched files: clean
  - pytest auth + vkey + policy tests: GREEN (~20 MAC-Ts per Murat #2026-05-27)
  - HARD grep on new files: zero hits for \bstrategic analysis\b, \bseamless\b, \benterprise-grade\b (Mary #2026-05-27 — applies to user-facing IdP setup docs + error messages)
  - AST check: policy.py contains no jwt.decode / jwks / authlib imports (M-T-GATEWAY-WIRING-NO-AUTH-LOGIC-01)
  - DIAL-LIVE-SMOKE landed (Stage 11.5 debt — Murat #2026-05-27 HIGH-risk precondition for [E2-H#3])
  - test status: {GREEN | RED-by-design at this halt}
Ready for E1 to land.
```

E1 verifies (path scope correct; no adapters/channels/ paths bleeding in) then executes the path-scoped commit.

**Never** stage `kernel/auth/` and `adapters/channels/` in the same commit. F-9.4.6-B.1-W3-COMMIT-CONTAM-01 anti-pattern.

---

## §6 Integration handshake with E1

E1 consumes E2's `kernel/auth/` public API in TeamsChannelAdapter + SlackChannelAdapter (REVISED per Winston #2026-05-27):

```python
# In E1's TeamsChannelAdapter.execute or SlackChannelAdapter.execute:
from praxis.kernel.auth import validate_jwt, map_claims_to_auth_claims
claims = validate_jwt(jwt_token, issuer=os.environ["VERDACA_OIDC_ISSUER"])
auth_claims = map_claims_to_auth_claims(claims)
ctx = ChannelContext(
    caller_id=claims["oid"],
    caller_kind=CallerKind.HUMAN,
    auth_claims=auth_claims,
    channel=ChannelKind.TEAMS,  # or SLACK
    ...
)
```

**Canonical import path (Winston #2026-05-27, mirrors Winston #2 Stage 11 discipline):** `praxis.kernel.auth` ONLY. No re-exports through `praxis.kernel.gateway`. Stage 13+ consumers (SessionIndex direct API, learning ports) import the same path — no re-coupling to gateway lifecycle.

**E2 stability dependency (REVISED per Murat #2026-05-27):** Signatures of `praxis.kernel.auth.validate_jwt` + `map_claims_to_auth_claims` + `discover_idp` MUST stabilize at [E2-H#2-COMPLETE] AS A CONTRACT ARTIFACT — freeze SHA stamp commit + 3-5 fixture claims published at `tests/fixtures/auth_claims/` + schema doc at `_bmad-output/implementation-artifacts/verdaca/stage12/auth-claims-contract.md`. If signatures change post-completion, E2 surfaces `F-12-E2-SIG-DRIFT-{N}` and E1 pauses; advisor coordinates a REFREEZE ceremony (mirrors Stage 11 REFREEZE-01/02 pattern).

**Cross-window drift escalation:** Any interface mismatch between E1's consumption pattern and E2's published shape → surface `F-12-E1-E2-DRIFT-{N}` and escalate to advisor.

**Parallel-with-E1 sequencing (REVISED):** E2's [E2-H#2] OAuth integration runs independently of E1's Teams/Slack adapter skeletons. E1 BLOCKS at adapter `auth_claims` wiring on E2's [E2-H#2-COMPLETE] (defined as contract artifact — fixtures published — per Murat #2026-05-27). E2's [E2-H#3] LiteLLM virtual keys + [E2-H#4] policy.py refactor can proceed while E1 wires their adapters against the published fixtures.

---

## §7 E2 Close criteria

Before surfacing E2 complete to advisor (REVISED per BMAD roundtable 2026-05-27):

1. All E2 MAC-Ts GREEN (count per Murat #2026-05-27: **~20 entries** — M-T-AUTH-OIDC-{1..12} + M-T-VKEY-{1..8})
2. `test_kernel_auth_contract.py` + `test_litellm_virtual_keys_contract.py`: all GREEN
3. `test_gateway_policy_contract.py` extended + existing tests still GREEN (backward compat); `M-T-GATEWAY-WIRING-NO-AUTH-LOGIC-01` AST check confirms policy.py contains no embedded auth logic
4. STAGE-11-DEBT-AUTH-01 TODO REMOVED from policy.py (resolved via `kernel.auth`); STAGE-11-DEBT-LITELLM-VKEY-01 TODO REMOVED (resolved via `virtual_keys.py`)
5. `kernel/auth/` registered in root `pyproject.toml` `[tool.uv.workspace] members` (19→20 active workspace members; per verified `pyproject.toml` 2026-05-26)
6. **[E2-H#2-COMPLETE] contract artifact published** (Murat #2026-05-27): freeze SHA stamp commit + `tests/fixtures/auth_claims/{entra,okta,auth0}_*.json` 3-5 fixture files + `_bmad-output/implementation-artifacts/verdaca/stage12/auth-claims-contract.md` schema doc
7. OAuth/OIDC `validate_jwt` rejects: invalid signature, expired tokens, wrong issuer, wrong audience, missing required claims, signature algorithm not in allow-list (RS256/ES256 default; HS256 rejected unless explicitly configured)
8. JWKS rotation triggered on `kid` cache miss (M-T-AUTH-OIDC-DISCOVERY-01 covers)
9. IdP discovery URL TLS-pinned (M-T-AUTH-OIDC-TLS-PIN-01 no_waiver candidate)
10. Token nbf clock-skew window respected (±60s default; M-T-AUTH-OIDC-CLOCK-SKEW-01)
11. LiteLLM virtual key budget enforcement pre-call; over-cap rejection does NOT invoke LLMProxyPort (M-T-VKEY-BUDGET-HARD-OVERRUN-01 — no_waiver strong prior; M-T-GW-POLICY-BUDGET-CAP-01 Stage 11 pattern carries forward)
12. **DIAL-LIVE-SMOKE landed** before E2 deploys (Murat #2026-05-27 — HIGH-risk precondition for [E2-H#3]; Stage 11.5 debt item must close first)
13. All E2 surfaces landed by E1 (no uncommitted E2 work)
14. `F-12-E2-HANDOVER-*` findings ledger: routed or closed; `F-12-E2-DIAL-SMOKE-MISSING-01` MUST be CLOSED (not deferred)
15. Cross-window drift `F-12-E1-E2-DRIFT-*`: zero open
16. mypy strict on `kernel/auth/src` + `kernel/gateway/src` + `adapters/litellm/src` clean
17. ruff clean on `kernel/auth/` + `kernel/gateway/` + `adapters/litellm/`
18. **HARD-constraint grep (Mary #2026-05-27):** zero hits on `\bstrategic analysis\b`, `\bseamless\b`, `\benterprise-grade\b` across any auth user-facing copy (error messages, IdP setup docs, README fragments, type hints, comments). Variable names with underscores SAFE.
19. No secret leakage: IdP client_secret + LiteLLM master key NEVER in test fixtures, logs, or committed files (read from env at runtime); `tests/fixtures/auth_claims/` JSON contains synthetic claims only, never real tokens

Advisor confirms; integration H#7 (Phase D demo packaging — master handover scope) opens after BOTH E1 + E2 complete.

---

## §8 Findings ledger

E2 findings carry `F-12-E2-*` prefix. Subtypes:
- `F-12-E2-PRELOAD-{N}` — preload / entry precondition issues
- `F-12-E2-HANDOVER-{N}` — handover-template drift
- `F-12-E2-SIG-DRIFT-{N}` — `praxis.kernel.auth.*` / `virtual_keys.py` signature drift post-completion
- `F-12-E2-OIDC-DISCOVERY-DRIFT-{N}` — IdP discovery URL or claims mapping drift
- `F-12-E2-DIAL-SMOKE-MISSING-01` — Stage 11.5 DIAL-LIVE-SMOKE not landed before [E2-H#3] (Murat #2026-05-27 HALT)
- `F-12-E2-FIXTURE-DRIFT-{N}` — `tests/fixtures/auth_claims/` drift from published H#2 contract
- `F-12-E1-E2-DRIFT-{N}` — cross-window drift with E1 (escalate to advisor)
- `F-12-E2-COMMIT-SURFACE-{N}` — surface posts to E1 (coordination, not findings)
- `F-12-E2-{H#N}-{TOPIC}-{N}` — phase-specific findings

All findings open at surface time → routed at close. Status: CLOSED-IN-CYCLE / ROUTED-FORWARD / ROUTED-TO-CLEO (H#8 review surface).

---

## §9 References

- **Parent handover:** `docs/stage-12-implementation-executor-handover.md`
- **Sibling handover:** `docs/stage-12-e1-channel-adapters-executor-handover.md` (commit-authority)
- **Stage 12 advisor handover:** `docs/stage-12-advisor-handover.md`
- **Stage 11 RATIFIED close memo:** `docs/stage-11-ratified-close-memo.md` (commit `e0aade3`)
- **Stage 11 policy.py (pre-refactor baseline):** `kernel/gateway/src/praxis/kernel/gateway/policy.py` with STAGE-11-DEBT-AUTH-01 + STAGE-11-DEBT-LITELLM-VKEY-01 TODOs
- **Stage 11 LiteLLM adapter (extension point for virtual_keys.py):** `adapters/litellm/src/praxis/adapters/litellm/adapter.py` (DIAL fix at `e9c0643`)
- **Frozen Stage 11 ports (AuthClaims DTO consumed by `praxis.kernel.auth.claims`):** `ports/src/praxis/ports/gateway_dto.py`
- **Verdaca wiki (refreshed 2026-05-26):** `knowledge/wiki/verdaca/{stage-9-state,current-architecture,remaining-work}.md` — Stage 11 RATIFIED + Stage 12 OPEN state; uv workspace 19 active members documented (kernel/auth/ adds 20th at Stage 12)
- **Verdaca knowledge graph (refreshed 2026-05-26):** `graphify-out/GRAPH_REPORT.md` — Stage 11 source-scope (592 .py files / 6,319 nodes / 541 communities); top god nodes for E2-adjacent code: `ContractViolation` (72 edges — surfaces across `praxis.kernel.gateway` + future `praxis.kernel.auth`), `AtelierStore` (49 edges)
- **OAuth/OIDC reference:** authlib docs (verify via context7 MCP at H#1 substrate probe)
- **LiteLLM virtual keys reference:** docs.litellm.ai (verify via context7 MCP at H#1)
- **Microsoft Entra OIDC reference:** Microsoft identity platform documentation (manual lookup or context7)
- **Concurrent executor discipline:** `feedback_concurrent_executor_orchestration` memory
- **Project root:** `CLAUDE.md`
- **Memory dir:** `~/.claude/projects/C--Users-AndreyPopov-Documents-Anthropic/memory/`

End of Handover B.E2.
