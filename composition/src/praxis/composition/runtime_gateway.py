"""Transport-neutral runtime composition root for the Verdaca gateway.

Stage 14 Phase-0.5 ("wire now → attest live"). This module is the FIRST
runnable caller of the FROZEN kernel composition root
``praxis.kernel.gateway.composition.build_gateway`` — prior to Phase-0.5 it
had zero non-test callers (finding O-3), so the deployable MCP entrypoint ran
``gateway=None`` and every gateway-backed tool RuntimeError'd at
``_gateway_required(None)`` before reaching the auth-first ``execute()`` spine.

``build_runtime_gateway()`` reads configuration from the environment, builds
the 11 dependencies ``build_gateway`` requires, and returns a live
``GatewayPort``. It is intentionally transport-neutral (no MCP/FastMCP imports)
so the SAME composition is reusable by the MCP server and the Teams/Slack
channel transports. (D-1 locked: a transport-neutral home, not ``shell/api/``
— that package carries a separate Clerk-auth lineage.) Stage 14 Day-2: HOISTED
out of the ``mcp_server`` adapter into this dedicated neutral
``praxis.composition`` workspace member (D-1 / finding D-O6-6) now that channels
wire — so ``channels.webhook_app`` no longer transitively imports
``mcp_server``/FastMCP (the wrong-direction arrow is gone;
F-14-O6-COMPOSITION-HOIST-PENDING-01 resolved).

FROZEN — this module only CONSTRUCTS and INJECTS existing kernel classes. It
does not modify ``build_gateway``'s signature, the auth quartet, the
``service.py`` execute path, the no_waiver markers, or the 14/9/23 pin.

Secrets come from the environment ONLY; nothing is hardcoded.

────────────────────────────────────────────────────────────────────────────
DEMO-GAP LEDGER (Phase-0.5 Tier-1; each stub is NAMED, not silently faked)
────────────────────────────────────────────────────────────────────────────
The auth spine is exercised for-real; non-spine substrates are stubbed so the
B-6 auditor-floor attestation is honest about what runs live vs. what does not:

  REAL (genuine, dependency-free or real-crypto):
    - session_index   : SqliteSessionIndex (real SQLite + FTS5; per-call
                        connection — thread-safe under the worker-thread bridge)
    - compaction      : InTreeCompactionStubAdapter (real deterministic
                        CompactionPort — "stub" by name, NOT LLMLingua)
    - jwt_verifier /
      oidc_policy     : real JwtVerifier + JwksCache + OidcPolicy. Against a
                        local OIDC stub (real RS256 + real JWKS/kid-rotation)
                        in the integration test; against the configured
                        OIDC_ISSUER_URL in a real deployment. HONESTY LINE:
                        exercised against a LOCAL OIDC stub — commercial-IdP
                        (Entra/Okta/Auth0) integration is config-only, untested
                        in this demo.
    - webhook_resolver: real WebhookSigningKeyResolver; empty secrets map for
                        the MCP-only transport (no inbound channel webhooks on
                        this path — honest: {} means "no channels here", not a
                        bypass).

  DEMO-GAP (Tier-1 stub — NAMED; not exercised live this cycle):
    - llm_proxy       : _DemoStubLLMProxy — a Fake terminal that returns a
                        canned LLMResponse. The auth→nonce→budget spine and the
                        memory/compaction/cost path run for real; only the
                        model OUTPUT is stubbed (Tier-1 per D-4). Real DIAL
                        output is the Phase-1 Champion-demo concern (Tier-2),
                        NOT this cycle.
    - policy.virtual_keys : _DemoStubVirtualKeys — records check_budget()
                        without rejecting. Per-tenant BUDGET enforcement is not
                        exercised live; CC6.1-e/CC7.1-b vkey-REQUIRED wiring is
                        proven via policy_health_check(policy=...) at the
                        entrypoint (STEP 3), not via a live LiteLLM proxy.
    - memory          : _DemoStubMemory — in-process store/query echo. Real
                        Mem0 + vector backend is a later-cycle concern.
    - nonce_store     : InMemoryNonceStore — FORCED demo-gap (finding O-9):
                        the real SQLite NonceStore opens a thread-affine
                        sqlite3 connection (check_same_thread defaults True),
                        but the Option A bridge offloads execute() to an
                        anyio worker thread ≠ the composition thread that built
                        the connection → sqlite3.ProgrammingError at
                        nonce.py BEGIN IMMEDIATE on every real request. Making
                        NonceStore thread-safe touches FROZEN kernel/auth/
                        nonce.py + the no_waiver CC6.8-c control (REFREEZE) —
                        out of Phase-0.5 scope. InMemoryNonceStore is
                        thread-safe (asyncio.Lock + set), so live replay
                        rejection (CC6.8-a/b/d) runs end-to-end across worker
                        threads; persistence-across-restart (CC6.8-c) stays
                        pinned by its passing no_waiver test
                        (M-T-AUTH-NONCE-PERSISTENCE-RESTART-01), not the live
                        path. REAL-DEPLOY FOLLOW-UP: a thread-safe persistent
                        nonce store (connection-per-thread or
                        check_same_thread=False) is required before a
                        production deploy with the worker-thread bridge.
    - cost_meter      : _DemoStubCostMeter — canned CostLedgerEntry. FORCED
                        demo-gap (finding O-8): the FROZEN gateway hardcodes
                        DIAL identifiers ("azure", "gpt-4o") at
                        service.py:142-143 / dial.py:10-11, but the real
                        PiMonoNativeAdapter.PRICING_TABLE has only
                        ("openai", "gpt-4o") — no "azure" entry — so the real
                        cost meter raises PricingTableMismatch at record(),
                        downstream of the auth→nonce→budget spine. Adding
                        ("azure","gpt-4o") would change PRICING_TABLE_VERSION
                        (a hashed, contract-asserted constant) — out of
                        Phase-0.5 scope. The spine runs for real regardless;
                        only the cost number is stubbed (Tier-1, parallel to
                        the LLM stub per D-4). Surfaced as O-8 for advisor.

  NOT per-tenant outbound credential (carry-forward F-14-TRACK-B finding,
  CC6.7-c): even with a real LiteLLM adapter the outbound model credential is a
  static per-provider key, not the per-tenant vkey. Out of Phase-0.5 scope.
"""

from __future__ import annotations

import os
from collections.abc import Iterator, Sequence
from datetime import datetime, timezone
from decimal import Decimal
from typing import ClassVar

from praxis.adapters.in_tree_compaction_stub import InTreeCompactionStubAdapter
from praxis.kernel.auth import InMemoryNonceStore, JwtVerifier, OidcPolicy
from praxis.kernel.auth.idp import discover
from praxis.kernel.auth.oidc import JwksCache, OidcMetadata
from praxis.kernel.gateway.composition import build_gateway
from praxis.kernel.gateway.composition_types import WebhookSigningKeyResolver
from praxis.kernel.gateway.policy import GatewayPolicy
from praxis.kernel.session_index.sqlite_store import SqliteSessionIndex
from praxis.ports.cost_meter import (
    BudgetScope,
    BudgetStatus,
    CostBreakdown,
    CostEvent,
    CostLedgerEntry,
    CostMeterPort,
    CostQuery,
    CostReport,
)
from praxis.ports.gateway import GatewayPort
from praxis.ports.llm_proxy import (
    LLMProxyPort,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    ProviderInfo,
)
from praxis.ports.memory import (
    MemoryEntry,
    MemoryHit,
    MemoryPort,
    MemoryQuery,
    StoredMemory,
)
from praxis.ports.virtual_key import VirtualKeyPort

_AUDIENCE_ENV = "OIDC_AUDIENCE"
_ISSUER_ENV = "OIDC_ISSUER_URL"
_ALLOWED_USERS_ENV = "VERDACA_ALLOWED_USER_IDS"

# Stage 14 implementation-finalization: production-profile gating for the
# de-stubbed real adapters. At VERDACA_DEPLOY_PROFILE=production the runtime
# composes the REAL adapter and fails CLOSED if its creds are absent; at any
# other profile (dev/test) it keeps the Tier-1 stub so the hermetic,
# credential-less integration path stays green. Real adapters are imported
# LAZILY on the production branch ONLY (they are not declared mcp_server deps;
# the dev/test path never imports them).
_DEPLOY_PROFILE_ENV = "VERDACA_DEPLOY_PROFILE"
_LITELLM_BASE_URL_ENV = "LITELLM_PROXY_URL"
_LITELLM_MASTER_KEY_ENV = "LITELLM_MASTER_KEY"
_DIAL_API_KEY_ENV = "DIAL_API_KEY"
# Letta (secondary memory adapter) — the letta_client SDK reads these natively.
_LETTA_API_KEY_ENV = "LETTA_API_KEY"
_LETTA_BASE_URL_ENV = "LETTA_BASE_URL"


class ConfigurationError(RuntimeError):
    """Raised when required runtime composition config is absent from the env."""


# ───────────────────────────────────────────────────────────────────────────
# Tier-1 demo stubs (NAMED demo-gaps — see module docstring ledger)
# ───────────────────────────────────────────────────────────────────────────


class _DemoStubLLMProxy:
    """DEMO-GAP (Tier-1): canned LLMResponse terminal.

    The auth-first spine + memory/compaction/cost path run for real; only the
    model output is stubbed. NOT a production LLM path. Real DIAL output is the
    Phase-1 Champion-demo (Tier-2) concern.
    """

    API_VERSION: ClassVar[str] = "1.0.0"

    def call(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            schema_version=request.schema_version,
            correlation_id=request.correlation_id,
            idempotency_key=request.idempotency_key,
            content="[Phase-0.5 Tier-1 demo stub — real model output deferred to Phase 1]",
            finish_reason="stop",
            input_tokens=0,
            output_tokens=0,
            raw_response_id="phase05-demo-stub",
        )

    def stream(self, request: LLMRequest) -> Iterator[LLMStreamChunk]:
        return iter(())

    def supported_providers(self) -> Sequence[ProviderInfo]:
        return ()


class _DemoStubVirtualKeys:
    """DEMO-GAP (Tier-1): records check_budget without rejecting.

    Per-tenant budget enforcement is not exercised live this cycle; the
    vkey-REQUIRED wiring (CC6.1-e/CC7.1-b) is proven at the entrypoint via
    policy_health_check(policy=...), not via a live LiteLLM proxy.
    """

    def __init__(self) -> None:
        self.checked: list[str] = []

    async def check_budget(self, key_alias: str) -> None:
        self.checked.append(key_alias)


class _DemoStubMemory:
    """DEMO-GAP (Tier-1): in-process store/query echo.

    Real Mem0 + vector backend is a later-cycle concern.
    """

    API_VERSION: ClassVar[str] = "1.0.0"

    def __init__(self) -> None:
        self._stored: list[MemoryEntry] = []

    def store(self, entry: MemoryEntry) -> StoredMemory:
        self._stored.append(entry)
        return StoredMemory(
            schema_version=1,
            correlation_id=entry.correlation_id,
            idempotency_key=entry.idempotency_key,
            stored_id=f"demo-mem-{len(self._stored)}",
        )

    def query(self, q: MemoryQuery) -> Sequence[MemoryHit]:
        return ()


class _DemoStubCostMeter:
    """DEMO-GAP (Tier-1, FORCED — finding O-8): canned CostLedgerEntry.

    The FROZEN gateway records cost against ("azure", "gpt-4o")
    (service.py:142-143 / dial.py:10-11), which is absent from the real
    PiMonoNativeAdapter.PRICING_TABLE — so the real cost meter raises
    PricingTableMismatch at record(), downstream of the auth→nonce→budget
    spine. Adding the azure row would change the hashed, contract-asserted
    PRICING_TABLE_VERSION constant (out of Phase-0.5 scope). This stub lets
    execute() complete end-to-end so the spine is live-attestable; only the
    cost number is canned. budget_check returns "ok" (no limit) so the spine's
    pre-call budget gate behaves as in the contract fakes.
    """

    API_VERSION: ClassVar[str] = "1.0.0"

    def record(self, event: CostEvent) -> CostLedgerEntry:
        return CostLedgerEntry(
            schema_version=1,
            correlation_id=event.correlation_id,
            idempotency_key=event.idempotency_key,
            ledger_id="phase05-demo-ledger",
            cost_usd=Decimal("0"),
            cost_breakdown=CostBreakdown(
                schema_version=1,
                correlation_id=event.correlation_id,
                idempotency_key=event.idempotency_key,
                input_cost_usd=Decimal("0"),
                output_cost_usd=Decimal("0"),
                pricing_table_version="phase05-demo-stub",
            ),
            written_at=datetime.now(timezone.utc),
        )

    def query(self, q: CostQuery) -> CostReport:
        return CostReport(
            schema_version=1,
            correlation_id=q.correlation_id,
            idempotency_key=q.idempotency_key,
            entries=[],
            total_usd=Decimal("0"),
            query=q,
            pricing_table_versions=[],
        )

    def budget_check(self, scope: BudgetScope) -> BudgetStatus:
        return BudgetStatus(
            schema_version=1,
            correlation_id=scope.correlation_id,
            idempotency_key=scope.idempotency_key,
            scope=scope,
            consumed_usd=Decimal("0"),
            limit_usd=None,
            remaining_usd=None,
            status="ok",
        )


# ───────────────────────────────────────────────────────────────────────────
# Composition
# ───────────────────────────────────────────────────────────────────────────


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigurationError(
            f"{name} is required to compose the runtime gateway "
            f"(Stage 14 Phase-0.5 build_runtime_gateway)."
        )
    return value


def _allowed_user_ids() -> frozenset[str]:
    raw = os.environ.get(_ALLOWED_USERS_ENV, "")
    return frozenset(uid.strip() for uid in raw.split(",") if uid.strip())


def _is_production_profile() -> bool:
    return os.environ.get(_DEPLOY_PROFILE_ENV, "").lower() == "production"


def _build_virtual_keys() -> VirtualKeyPort:
    """Production → real LiteLLM virtual-key adapter (fail-closed if creds
    absent); dev/test → Tier-1 stub (keeps the credential-less hermetic path).

    De-stubs CC6.1-e / CC7.1-b from record-only theater to live budget
    ENFORCEMENT: the real adapter's ``check_budget`` rejects an over-budget key
    (``BudgetExhaustedError``), whereas ``_DemoStubVirtualKeys`` only records.
    FROZEN nonce/auth/pin untouched.
    """
    if not _is_production_profile():
        return _DemoStubVirtualKeys()
    base_url = os.environ.get(_LITELLM_BASE_URL_ENV)
    master_key = os.environ.get(_LITELLM_MASTER_KEY_ENV)
    if not base_url or not master_key:
        raise ConfigurationError(
            f"{_LITELLM_BASE_URL_ENV} + {_LITELLM_MASTER_KEY_ENV} are REQUIRED at "
            f"{_DEPLOY_PROFILE_ENV}=production (live virtual-key budget enforcement)."
        )
    from praxis.adapters.litellm.virtual_keys import LiteLLMVirtualKeyAdapter

    return LiteLLMVirtualKeyAdapter(base_url=base_url, master_key=master_key)


def _build_llm_proxy() -> LLMProxyPort:
    """Production → real DIAL-backed LiteLLM LLM proxy (fail-closed if the DIAL
    key is absent); dev/test → Tier-1 canned-output stub.

    Uses the canonical ``create_dial_llm_proxy`` factory (provider=azure,
    api_base=EPAM DIAL, version pinned) — the same wiring the DIAL contract
    test exercises. NOTE: the LLM proxy egresses DIRECT to DIAL, distinct from
    the virtual-key adapter's ``LITELLM_PROXY_URL`` (the dispatch's "same
    proxy/env" framing is corrected here per the codebase's existing topology).
    """
    if not _is_production_profile():
        return _DemoStubLLMProxy()
    api_key = os.environ.get(_DIAL_API_KEY_ENV)
    if not api_key:
        raise ConfigurationError(
            f"{_DIAL_API_KEY_ENV} is REQUIRED at {_DEPLOY_PROFILE_ENV}=production "
            "(real DIAL model output via create_dial_llm_proxy)."
        )
    from praxis.kernel.gateway.dial import create_dial_llm_proxy

    return create_dial_llm_proxy(api_key=api_key)


class _DialKeyNormalizingCostMeter:
    """Task 3 (O-8 EQUAL branch) composition-layer decorator over the REAL
    PiMonoNativeAdapter: rewrites DIAL cost events keyed ("azure","gpt-4o")
    onto the existing ("openai","gpt-4o") PRICING_TABLE row before pricing.

    The two are the SAME model at the SAME list price ($2.50 in / $10 out per
    1M tokens), so pricing the DIAL event via the openai row is ACCURATE — not
    a fudge. This avoids editing PRICING_TABLE or bumping the frozen, hashed
    PRICING_TABLE_VERSION (O-8: azure row absent; version bump deferred to
    Stage-14.x). Source of truth for the ("azure","gpt-4o") pair is
    dial.DIAL_LITELLM_PROVIDER / DIAL_LITELLM_MODEL.
    """

    API_VERSION: ClassVar[str] = "1.0.0"
    _FROM_PROVIDER: ClassVar[str] = "azure"
    _MODEL: ClassVar[str] = "gpt-4o"
    _TO_PROVIDER: ClassVar[str] = "openai"

    def __init__(self, inner: CostMeterPort) -> None:
        self._inner = inner

    def record(self, event: CostEvent) -> CostLedgerEntry:
        if (event.provider, event.model) == (self._FROM_PROVIDER, self._MODEL):
            event = event.model_copy(update={"provider": self._TO_PROVIDER})
        return self._inner.record(event)

    def query(self, q: CostQuery) -> CostReport:
        return self._inner.query(q)

    def budget_check(self, scope: BudgetScope) -> BudgetStatus:
        return self._inner.budget_check(scope)


def _build_cost_meter() -> CostMeterPort:
    """Production → real PiMonoNativeAdapter behind the DIAL key-normalizing
    decorator (O-8 EQUAL: azure/gpt-4o priced via the openai/gpt-4o row, no
    PRICING_TABLE edit / version bump); dev/test → Tier-1 stub. No external
    creds (pricing is in-process) → no fail-closed branch.
    """
    if not _is_production_profile():
        return _DemoStubCostMeter()
    from praxis.adapters.pi_mono_native import PiMonoNativeAdapter

    return _DialKeyNormalizingCostMeter(PiMonoNativeAdapter())


def _build_memory() -> MemoryPort:
    """Production → real memory adapter; dev/test → Tier-1 stub.

    Substrate selection (Task 4): Mem0 is the ratified PRIMARY, but its
    caller-constructed backing defaults to an OpenAI embedder + LLM, which is
    UNAVAILABLE here (no OPENAI_API_KEY; project policy is DIAL-only, no OpenAI
    products) and a DIAL-backed Mem0 embedder config is not yet built. So the
    SECONDARY adapter Letta (native passage-search) is wired — the
    ``letta_client`` SDK reads ``LETTA_API_KEY`` / ``LETTA_BASE_URL`` natively
    (no invented convention).

    Config precision (F-14-H8-1): the guard raises only if NEITHER
    ``LETTA_API_KEY`` nor ``LETTA_BASE_URL`` is set. A base-URL-only config is a
    VALID local-Letta mode (e.g. ``http://localhost:8283``) — construction
    succeeds and any auth failure surfaces at first call, NOT at startup. Both
    key + base URL are needed only for hosted Letta; local mode = base URL
    alone. So this is a presence-of-config gate, not a full hosted-credential
    fail-closed. Construction does not contact the server (``on_init``/
    ``health`` is not called by ``build_gateway``).
    """
    if not _is_production_profile():
        return _DemoStubMemory()
    if not (os.environ.get(_LETTA_API_KEY_ENV) or os.environ.get(_LETTA_BASE_URL_ENV)):
        raise ConfigurationError(
            f"{_LETTA_API_KEY_ENV} or {_LETTA_BASE_URL_ENV} is REQUIRED at "
            f"{_DEPLOY_PROFILE_ENV}=production (Letta memory substrate; the Mem0 "
            "primary needs an OpenAI/DIAL-backed embedder config not yet built)."
        )
    from letta_client import Letta

    from praxis.adapters.letta import LettaAdapter

    # Construction stays server-free (per this module's contract). The Letta
    # system agent is resolved/created by LettaAdapter.on_init(), which the
    # runtime ENTRYPOINT must invoke after composition — NOT here. See
    # F-14-LETTA-ONINIT-UNWIRED-01: no entrypoint currently calls on_init(),
    # so the live memory path routes to agent_id=None until that is wired.
    return LettaAdapter(letta_client=Letta())


async def _build_oidc_policy() -> tuple[JwtVerifier, OidcPolicy]:
    """Construct the real auth quartet's verifier + OIDC policy from env config.

    Discovers OIDC metadata from OIDC_ISSUER_URL (a local stub in the
    integration test; a real IdP in deployment), builds a real JwtVerifier and
    a real TTL JwksCache, and a real OidcPolicy with the configured audience.
    No auth LOGIC is added here — only construction of the frozen kernel
    classes.
    """
    issuer = _require_env(_ISSUER_ENV)
    audience = _require_env(_AUDIENCE_ENV)
    metadata: OidcMetadata = await discover(issuer)
    verifier = JwtVerifier(metadata)
    jwks_cache = JwksCache()
    oidc_policy = OidcPolicy(verifier=verifier, audience=audience, jwks_cache=jwks_cache)
    return verifier, oidc_policy


def build_runtime_gateway(
    *,
    jwt_verifier: JwtVerifier,
    oidc_policy: OidcPolicy,
) -> tuple[GatewayPort, GatewayPolicy]:
    """Compose a live GatewayPort + its GatewayPolicy from runtime config.

    Returns BOTH the gateway and the policy so the entrypoint can pass the
    SAME policy instance to ``policy_health_check(policy=...)`` (STEP 3).

    The auth quartet (``jwt_verifier`` + ``oidc_policy``) is passed in already
    constructed because its construction is async (OIDC discovery). Call
    ``compose_auth_quartet()`` to build it, or pass a test double.

    Delegates to the FROZEN ``build_gateway`` — this function only assembles
    arguments; it does not alter the kernel composition root.
    """
    virtual_keys = _build_virtual_keys()  # prod→real LiteLLM vkey; dev/test→stub
    policy = GatewayPolicy(
        allowed_user_ids=_allowed_user_ids(),
        oidc_policy=oidc_policy,
        virtual_keys=virtual_keys,
    )

    gateway = build_gateway(
        session_index=SqliteSessionIndex(),
        compaction=InTreeCompactionStubAdapter(),
        memory=_build_memory(),  # prod→real Letta (Mem0 backing absent); dev/test→stub
        llm_proxy=_build_llm_proxy(),  # prod→real DIAL LiteLLM; dev/test→stub
        cost_meter=_build_cost_meter(),  # prod→real pi_mono (DIAL-key-normalized); dev/test→stub
        channel_adapters={},
        jwt_verifier=jwt_verifier,
        oidc_policy=oidc_policy,
        nonce_store=InMemoryNonceStore(),  # O-9 Option A — see demo-gap ledger
        webhook_resolver=WebhookSigningKeyResolver(secrets={}),
        policy=policy,
    )
    return gateway, policy


async def compose_auth_quartet() -> tuple[JwtVerifier, OidcPolicy]:
    """Async helper: build the real verifier + OIDC policy from env config."""
    return await _build_oidc_policy()


__all__ = [
    "ConfigurationError",
    "build_runtime_gateway",
    "compose_auth_quartet",
]
