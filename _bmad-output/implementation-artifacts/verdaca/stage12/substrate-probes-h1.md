# Stage 12 H#1 Substrate Probes

**Date:** 2026-05-27
**Branch:** `stage-12.0-channel-adapters`
**Pre-report HEAD:** `4bc4cba`
**Mode:** Report-only substrate verification. No package installs, no source edits, no `tests/fixtures/auth_claims/` creation.

## §1 Teams

### Candidate

Recommended candidate: `botbuilder-core` + `botframework-connector`.

Rejected as primary substrate:
- `msrest` alone: transport/runtime dependency, not a Teams/Bot Framework adapter surface.
- `aiohttp` + manual: viable only for raw HTTP, but would hand-roll token validation and Bot Framework activity handling.

### PyPI Metadata

| Package | Latest | Last release upload | Python compatibility | Latest release artifact size |
|---|---:|---|---|---:|
| `botbuilder-core` | `4.17.1` | 2026-01-05T19:49:41Z | not declared | 116,145 bytes |
| `botframework-connector` | `4.17.1` | 2026-01-05T19:49:48Z | not declared | 100,883 bytes |
| `msrest` | `0.7.1` | 2022-06-13T22:41:25Z | `>=3.6` | 260,716 bytes |
| `aiohttp` | `3.13.5` | 2026-03-31T22:01:03Z | `>=3.9` | 171,103,208 bytes across release files |

Observed wheel metadata:
- `botbuilder-core` requires `botbuilder-schema==4.17.1`, `botframework-connector==4.17.1`, `botframework-streaming==4.17.1`, `jsonpickle<4,>=1.2`.
- `botframework-connector` requires `msrest==0.7.*`, `PyJWT>=2.4.0`, `botbuilder-schema==4.17.1`, `msal>=1.31.1`.

### API Surface

Frozen Verdaca surface in `ports/src/praxis/ports/gateway.py` exposes:

```python
class ChannelAdapterPort(Protocol):
    def execute(
        self,
        intent: StartAnalysisRequest,
        ctx: ChannelContext,
        gateway: GatewayPort,
    ) -> AnalysisResult: ...
```

The handover mentions `receive_event()`, but no such method exists in the frozen Stage 11 `ChannelAdapterPort`.

Teams intake and auth surfaces found in wheel inspection:
- `botbuilder.core.bot_framework_adapter.BotFrameworkAdapter.process_activity(req, auth_header, logic)` parses the incoming activity, authenticates it, and runs the bot middleware pipeline.
- `botframework.connector.auth.jwt_token_validation.JwtTokenValidation.authenticate_request(activity, auth_header, credentials, channel_service_or_provider, auth_configuration)`.
- `botframework.connector.auth.jwt_token_validation.JwtTokenValidation.validate_auth_header(auth_header, credentials, channel_service_or_provider, channel_id, service_url, auth_configuration)`.
- `botframework.connector.auth.jwt_token_extractor.JwtTokenExtractor.get_open_id_metadata(metadata_url)`.
- `botframework.connector.auth.jwt_token_extractor.JwtTokenExtractor(..., allowed_algorithms)` sets `validation_parameters.algorithms`.

Verdict: Teams substrate is sufficient for event intake and JWT validation of incoming Bot Framework tokens, then adapter code translates the activity into Verdaca `StartAnalysisRequest` + `ChannelContext` and calls `ChannelAdapterPort.execute(...)`.

## §2 Slack

### PyPI Metadata

| Package | Latest | Last release upload | Python compatibility | Latest release artifact size |
|---|---:|---|---|---:|
| `slack-sdk` | `3.42.0` | 2026-05-18T17:50:44Z | `>=3.7` | 567,605 bytes |

Wheel metadata shows optional extras for `aiohttp`, `websockets`, `websocket-client`, `SQLAlchemy`, and `boto3`; core SDK install has no required runtime dependencies in the inspected metadata.

### Signature Surface

Found:
- `slack_sdk.signature.SignatureVerifier(signing_secret, clock=Clock())`.
- `SignatureVerifier.is_valid_request(body, headers)`.
- `SignatureVerifier.is_valid(body, timestamp, signature)`.
- `SignatureVerifier.generate_signature(timestamp=..., body=...)`.

The implementation normalizes headers, reads `x-slack-request-timestamp` and `x-slack-signature`, constructs the Slack `v0:{timestamp}:{body}` base string, and rejects requests when `abs(now - timestamp) > 60 * 5`.

### Events API vs Socket Mode

Events API:
- `slack-sdk` provides the signature verifier and Web API clients.
- HTTP request routing / URL verification / event dispatch are not a full framework in `slack-sdk`; the adapter should implement the small HTTP wrapper or add Slack Bolt later if H#2 ratifies it.

Socket Mode:
- `slack_sdk.socket_mode.SocketModeClient` variants exist under builtin, websocket-client, websockets, and aiohttp paths.

Recommendation: use Events API for Stage 12 channel adapter work. It matches the webhook/VCR-cassette test strategy, keeps ingress deterministic, and avoids WebSocket lifecycle ownership in the first Teams/Slack adapter stage.

## §3 Authlib

### PyPI Metadata

| Package | Latest | Last release upload | Python compatibility | Latest release artifact size |
|---|---:|---|---|---:|
| `Authlib` | `1.7.2` | 2026-05-06T08:10:23Z | `>=3.10` | 436,059 bytes |

Wheel metadata dependencies:
- `cryptography`
- `joserfc>=1.6.0`

### OIDC / JWT / JWKS Surface

Found:
- `authlib.jose.JsonWebKey`.
- `authlib.jose.JsonWebToken`.
- `authlib.jose.rfc7519.jwt.JsonWebToken(algorithms, private_headers=None)`.
- `authlib.jose.rfc7519.jwt.JsonWebToken.decode(s, key, claims_cls=None, claims_options=None, claims_params=None)`.
- `authlib.integrations.base_client.sync_app.OAuth2Mixin.load_server_metadata()` fetches and caches OIDC metadata from `server_metadata_url`.
- `authlib.integrations.base_client.async_app.AsyncOAuth2Mixin.load_server_metadata()` async equivalent.
- `authlib.integrations.base_client.sync_openid.OpenIDMixin.fetch_jwk_set(force=False)`.
- `authlib.integrations.base_client.async_openid.AsyncOpenIDMixin.fetch_jwk_set(force=False)`.
- `parse_id_token(...)` catches `InvalidKeyIdError` and retries `fetch_jwk_set(force=True)`, which is a JWKS refresh-on-`kid`-miss surface.
- `authlib.oauth2.rfc8414.models.validate_jwks_uri()` enforces HTTPS for `jwks_uri`.

Verdict: JWKS fetch and refresh-on-`kid`-miss exist; no `F-12-AUTHLIB-JWKS-ROTATION-01`.

### Algorithm Pinning

Authlib/`joserfc` exposes an `algorithms=` argument on JWT decode paths, so Verdaca can pin `RS256` / `ES256` and reject `none` / `HS256`.

Important wrapper requirement: Authlib's OpenID mixin reads `id_token_signing_alg_values_supported` from discovery and passes it to decode. Verdaca must filter discovery algorithms through a local allow-list before decode rather than trusting the IdP discovery list directly.

Finding: `F-12-AUTHLIB-ALG-PINNING-01` tracks that wrapper requirement for H#2.

## §4 LiteLLM-vkeys

### Versions

Installed workspace version:
- `litellm==1.83.14`

Current PyPI version:
- `litellm==1.86.1`
- Last release upload: 2026-05-26T03:51:58Z
- Python compatibility: `<3.14,>=3.10`
- Latest release artifact size: 32,392,120 bytes across release files

### Installed SDK Probe

In installed `litellm==1.83.14`:
- `litellm.create_virtual_key`: missing.
- `litellm.check_key_budget`: missing.

Candidate module paths searched:
- `litellm.proxy.management_endpoints.*`
- `litellm.experimental_mcp_client.*`
- `litellm.proxy.proxy_server.*`

Installed proxy internals found:
- `litellm.proxy.management_endpoints.key_management_endpoints.generate_key_fn(...)`
- `update_key_fn(...)`, `info_key_fn(...)`, `list_keys(...)`, `block_key(...)`, `unblock_key(...)`, `reset_key_spend_fn(...)`, `key_health(...)`
- `GenerateKeyRequest` fields include `models`, `max_budget`, `tpm_limit`, `rpm_limit`, `budget_duration`, `model_max_budget`, `model_rpm_limit`, `model_tpm_limit`, `budget_limits`, `key_alias`, `team_id`, `user_id`, `budget_id`.
- `LiteLLM_VerificationToken` carries `spend`, `max_budget`, `models`, `tpm_limit`, `rpm_limit`, `budget_duration`, `model_max_budget`, and related enforcement state.
- `LiteLLM_BudgetTable` carries `max_budget`, `tpm_limit`, `rpm_limit`, `model_max_budget`, `budget_duration`, `allowed_models`.

### Latest Wheel Probe

In no-install inspection of `litellm==1.86.1`:
- Top-level `create_virtual_key`: not found.
- Top-level `check_key_budget`: not found.
- `litellm.proxy.client.keys.KeysManagementClient.generate(models, aliases, spend, duration, key_alias, team_id, user_id, budget_id, config, return_request)` exists and POSTs to `/key/generate`.
- `KeysManagementClient.info(...)`, `list(...)`, `update(...)`, and `delete(...)` exist.
- Proxy server internals still expose `generate_key_fn(...)`, `key_health(...)`, `info_key_fn(...)`, and budget/rate/model fields.

Verdict: LiteLLM virtual-key support is present as proxy routes and proxy-management internals, not as the named SDK functions requested by the handover.

Finding: `F-12-LITELLM-VKEY-API-VERSION-01`.

Proposed disposition:
- Do not design E2 against nonexistent `litellm.create_virtual_key` / `litellm.check_key_budget`.
- If H#2 chooses an official client wrapper, bump candidate pin to `litellm==1.86.1` and wrap `litellm.proxy.client.keys.KeysManagementClient`.
- If H#2 avoids a version bump, wrap proxy HTTP endpoints (`/key/generate`, `/key/info`, `/key/health`, `/key/update`) against installed `1.83.14` server internals and validate with integration tests.

## §5 vcrpy

### PyPI Metadata

| Package | Latest | Last release upload | Python compatibility | Latest release artifact size |
|---|---:|---|---|---:|
| `vcrpy` | `8.1.1` | 2026-01-04T19:22:03Z | `>=3.10` | 128,215 bytes |

Wheel metadata dependencies:
- `PyYAML`
- `wrapt`

### Surface

Found:
- `vcr.config.VCR(...)`.
- Constructor/default fields include `record_mode=RecordMode.ONCE`.
- Default `match_on=("method", "scheme", "host", "port", "path", "query")`.
- `vcr.cassette.Cassette(..., record_mode=..., match_on=...)`.
- `vcr.record_mode.RecordMode`.

Cassette convention for Stage 12:
- `tests/fixtures/vcr_cassettes/teams/`
- `tests/fixtures/vcr_cassettes/slack/`

Confirmed: `pact-python` is not introduced. It was queried only for metadata comparison; no install or source reference was added.

## §6 DIAL-live-smoke

### Environment

Checked without printing secrets:
- Process `DIAL_API_KEY`: absent.
- User `DIAL_API_KEY`: absent.
- Machine `DIAL_API_KEY`: absent.
- Process/User/Machine `EPAM_DIAL_KEY`: absent.

### Discovery Probes

Known DIAL base from source:
- `kernel/gateway/src/praxis/kernel/gateway/dial.py`: `https://ai-proxy.lab.epam.com`

Discovery-only GET attempts:
- `https://ai-proxy.lab.epam.com/.well-known/openid-configuration` -> HTTP 401, body prefix: `At least API-KEY or Authorization header must be provided`.
- `https://ai-proxy.lab.epam.com/openid/.well-known/openid-configuration` -> HTTP 401, same body prefix.
- `https://ai-proxy.lab.epam.com/auth/.well-known/openid-configuration` -> HTTP 401, same body prefix.

No token exchange was attempted.
No key value was logged.

Verdict: DIAL endpoint is reachable, but DIAL-LIVE-SMOKE is not closeable from this shell because no `DIAL_API_KEY` is visible and discovery requires an API key or Authorization header.

Finding: `F-12-DIAL-LIVE-SMOKE-FAIL-01`.

## §7 uv-workspace-delta

Root `pyproject.toml` currently has 19 active uv workspace members:

```text
ports
adapters/beads
adapters/tonl
adapters/in_tree_compaction_stub
adapters/pi_mono_native
adapters/litellm
adapters/mcp_server
adapters/mem0
adapters/letta
adapters/llmlingua
tests
kernel/compression
kernel/mac
kernel/gateway
kernel/memory
kernel/pi-mono/src
kernel/runtime
kernel/session_index
kernel/studio
```

Stage 12 proposed new package members:
- `adapters/channels/teams`
- `adapters/channels/slack`
- `kernel/auth`

Reconciliation:
- Handover text says `19->20` because it counts only Winston's `kernel/auth/` pivot.
- If Teams and Slack are implemented as separate uv workspace packages, canonical count becomes `19 + 3 = 22`.
- If `adapters/channels/` is one shared workspace member containing both channel adapters, canonical count becomes `21`.

Finding: `F-12-WORKSPACE-COUNT-DELTA-01`.

Proposed canonical count for the current handover layout: 22 active members.

## §8 Findings Ledger

| Finding | Severity | Status | Evidence | Proposed route |
|---|---|---|---|---|
| `F-12-CHANNELADAPTER-RECEIVE-EVENT-DRIFT-01` | Medium | OPEN | Handover asks to verify `receive_event()`, but frozen `ChannelAdapterPort` only exposes `execute(intent, ctx, gateway)`. | H#2 charter should either correct wording to event-intake wrapper or open REFREEZE-03 if a new port method is truly required. |
| `F-12-AUTHLIB-ALG-PINNING-01` | Medium | OPEN | Authlib has algorithm parameters, but built-in OpenID mixin consumes discovery alg list directly. | Verdaca `kernel/auth/` wrapper must filter to local allow-list before decode and reject `none` / `HS256`. |
| `F-12-LITELLM-VKEY-API-VERSION-01` | High | OPEN | Installed `litellm==1.83.14` and latest `1.86.1` lack top-level `create_virtual_key` / `check_key_budget`; virtual-key support is proxy-route based. | H#2 chooses either `litellm==1.86.1` client wrapper or installed-version HTTP route wrapper. |
| `F-12-DIAL-LIVE-SMOKE-FAIL-01` | High | OPEN | `DIAL_API_KEY` absent in Process/User/Machine env; discovery URLs return HTTP 401. | Re-run H#1.F with `DIAL_API_KEY` exported into this shell; do not mark Stage 11.5 DIAL-LIVE-SMOKE closed yet. |
| `F-12-WORKSPACE-COUNT-DELTA-01` | Medium | OPEN | Current workspace count is 19; handover says `19->20`; proposed Stage 12 paths add three members under current package layout. | H#2 charter must pin workspace package topology and canonical active-member count. |
| `F-12-HANDOVER-ADVISOR-DRIFT-01` | Low | OPEN | D11 edited the three executor handovers only; `docs/stage-12-advisor-handover.md` still contains obsolete gateway-local auth references. | Advisor should either authorize a follow-up advisor-handover sweep or accept it as non-executor operational drift. |

## §provenance

| Field | Value |
|---|---|
| Surface | Codex CLI/API runtime |
| Model | GPT-5 / Codex |
| Working directory | `C:\Users\AndreyPopov\Documents\Anthropic` |
| Session JSONL path | `C:\Users\AndreyPopov\.codex\sessions\2026\05\26\rollout-2026-05-26T18-33-56-019e64eb-cfb5-7ae2-a906-5c431a8986a5.jsonl` |
| Python | `Python 3.12.12` |
| uv | `uv 0.10.6` |
| Pre-report branch | `stage-12.0-channel-adapters` |
| Pre-report HEAD | `4bc4cba` |
| PyPI metadata source | `https://pypi.org/pypi/{package}/json` |
| Wheel inspection cache | `%TEMP%\verdaca_stage12_probe_wheels` |
| No-install packages inspected | `botbuilder-core`, `botframework-connector`, `slack-sdk`, `Authlib`, `vcrpy`, `litellm==1.86.1` |

