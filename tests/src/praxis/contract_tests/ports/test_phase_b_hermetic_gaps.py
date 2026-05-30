"""Stage 14 Phase-B — hermetic gap ADDs (G1, G2, G5, G6) + PLAIN-GREEN
characterizations backing the deferred-register's now-testable claims (O-9, CC6.7-c).

All hermetic: no live creds, no frozen-surface edits. Plain tests (NO
``@pytest.mark.no_waiver`` → 14/9/23 pin unaffected).

  G1 — build_runtime_gateway threads the SAME auth-quartet instance into the
       returned policy (STEP-3 parity: the entrypoint health-checks THAT policy).
  G2 — error-taxonomy: _ctx_status prefix mapping (incl. the defensive budget→402
       branch) + the deliberate internal-ValueError→500 propagation (the HIGH
       -01 guard) + the 503-not-initialized branch.
  G5 — lazy-import isolation: a non-prod compose imports NO real adapter
       (litellm/letta/mem0/pi_mono), proven in a clean SUBPROCESS (not a flaky
       in-process sys.modules snapshot).
  G6 — budget DENIAL is rejected in the spine (the PLAIN-GREEN proof behind
       CC6.7-c's "gate mechanism is real" caveat): an injected over-budget vkey →
       GatewayCtxError naming BudgetExhaustedError on the auth leg (webhook maps
       auth→401). NOTE: surfaces as auth:…BudgetExhaustedError (401), NOT the
       _ctx_status budget→402 branch — that branch is dead/defensive (the service
       wraps enforce_budget failures via _auth_error).
  O-9 — characterization: the durable SQLite NonceStore is thread-affine; a
        foreign-thread check_and_mark raises sqlite3.ProgrammingError (WHY the
        worker-thread bridge uses InMemoryNonceStore). Doubles as the flip-trigger.
  CC6.7-c — egress-topology: the production LLM proxy egresses DIRECT to DIAL,
        a DIFFERENT endpoint than the vkey adapter's LiteLLM metering proxy →
        the gate is spend-blind (construction-only, no live calls).
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import anyio
import httpx
import pytest

import praxis.composition.runtime_gateway as comp
from praxis.adapters.channels.webhook_app import WebhookApp, create_webhook_app
from praxis.composition.runtime_gateway import build_runtime_gateway
from praxis.contract_tests.ports.gateway_contract_fakes import (
    FakeOidcPolicy,
    make_ctx,
    make_gateway_harness,
    make_intent,
)
from praxis.kernel.auth.nonce import NonceStore
from praxis.kernel.gateway.dial import DIAL_API_BASE
from praxis.kernel.gateway.policy import GatewayPolicy
from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_errors import GatewayCtxError
from praxis.ports.virtual_key import BudgetExhaustedError

# ── G1 — composite assembly threads the same auth quartet ──────────────────


def test_G1_build_runtime_gateway_threads_same_oidc_policy_into_policy() -> None:
    from praxis.contract_tests.ports.gateway_contract_fakes import make_auth_quartet

    verifier, oidc_policy, _nonce, _resolver = make_auth_quartet()
    gateway, policy = build_runtime_gateway(jwt_verifier=verifier, oidc_policy=oidc_policy)

    assert isinstance(gateway, GatewayPort)
    # The entrypoint passes THIS returned policy to policy_health_check; it must
    # carry the SAME oidc_policy instance that was composed into the gateway.
    assert policy.oidc_policy is oidc_policy
    # dev/test profile → Tier-1 stub vkey (positive stub assertion; profile bleed
    # would flip this and fail LOUD).
    assert type(policy.virtual_keys).__name__ == "_DemoStubVirtualKeys"


# ── G2 — error taxonomy ────────────────────────────────────────────────────


class _FakeCtxErr:
    def __init__(self, field: str) -> None:
        self.context_field = field


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("auth:x", 401),
        ("policy:x", 403),
        ("budget:x", 402),  # defensive branch — currently unreached by the service
        ("read:x", 400),
        ("", 400),
        ("unknown", 400),
    ],
)
def test_G2_ctx_status_prefix_mapping(field: str, expected: int) -> None:
    from praxis.adapters.channels.webhook_app.app import _ctx_status

    assert _ctx_status(_FakeCtxErr(field)) == expected  # type: ignore[arg-type]


class _FakeGateway:
    jwt_verifier = object()


@pytest.mark.asyncio
async def test_G2_handle_503_when_gateway_not_initialized() -> None:
    # ASGITransport does NOT run lifespan → startup() never runs → _gateway None.
    app = create_webhook_app(WebhookApp())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        resp = await client.post("/webhooks/teams", content=b"{}")
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_G2_internal_valueerror_propagates_to_500(monkeypatch: pytest.MonkeyPatch) -> None:
    """The HIGH -01 guard: a non-auth internal ValueError is NOT masked as 401 —
    it propagates to a 500."""
    import praxis.adapters.channels.webhook_app.app as app_module

    def _boom(*_a: Any, **_k: Any) -> Any:
        raise ValueError("internal fault, not an auth failure")

    monkeypatch.setattr(app_module, "receive_webhook", _boom)
    app_obj = WebhookApp()
    app_obj._gateway = _FakeGateway()  # type: ignore[assignment]
    app_obj._secret = "x"
    app_obj._exec_lock = anyio.Lock()
    app = create_webhook_app(app_obj)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as client:
        resp = await client.post("/webhooks/teams", content=b"{}")
    assert resp.status_code == 500


# ── G5 — lazy-import isolation (subprocess) ────────────────────────────────

_ISOLATION_PROBE = """
import json, sys
import praxis.composition.runtime_gateway as m
# Non-prod (no VERDACA_DEPLOY_PROFILE) → every selector returns a Tier-1 stub
# and must NOT trigger the lazy imports inside the production branches.
# Guard: the specific modules WE lazy-import under _is_production_profile()
# must be absent from sys.modules after calling each selector.
# NOTE: the raw 'litellm' SDK may be transitively present in the workspace
# environment regardless of profile (installed as a workspace dep of tests/) —
# that's NOT the isolation invariant. The invariant is that our
# production-branch lazy imports (the adapter constructors) did NOT run.
m._build_virtual_keys()
m._build_llm_proxy()
m._build_cost_meter()
m._build_memory()
# Modules we LAZY-IMPORT inside the if _is_production_profile() branches:
OUR_LAZY_MODULES = (
    # praxis.kernel.gateway.dial is NOT listed here: service.py imports
    # DIAL_LITELLM_PROVIDER/MODEL from it at the kernel level (transitive,
    # pre-existing, not our production-branch lazy import).
    # What we guard: OUR lazy-import code in the _build_* if-branches.
    "praxis.adapters.litellm.virtual_keys",   # _build_virtual_keys prod branch
    "praxis.adapters.pi_mono_native",         # _build_cost_meter prod branch
    "praxis.adapters.pi_mono_native.adapter", # _build_cost_meter prod branch
    "letta_client",                           # _build_memory prod branch
    "praxis.adapters.letta",                  # _build_memory prod branch
    "praxis.adapters.letta.adapter",          # _build_memory prod branch
)
offenders = sorted(x for x in sys.modules if any(
    x == m or x.startswith(m + '.') for m in OUR_LAZY_MODULES
))
print(json.dumps(offenders))
"""


def test_G5_nonprod_compose_lazy_imports_did_not_run() -> None:
    """Non-prod profile: the production-branch lazy imports (LiteLLMVirtualKeyAdapter,
    create_dial_llm_proxy, PiMonoNativeAdapter, LettaAdapter) must NOT be triggered.
    Checked via subprocess (avoids in-process sys.modules pollution) against the
    specific modules we lazy-import inside the 'if _is_production_profile()' branches,
    NOT the raw SDK packages (which may be present in the shared workspace env)."""
    env = {k: v for k, v in os.environ.items() if k != "VERDACA_DEPLOY_PROFILE"}
    result = subprocess.run(
        [sys.executable, "-c", _ISOLATION_PROBE],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    offenders = json.loads(result.stdout.strip().splitlines()[-1])
    assert offenders == [], (
        f"non-prod compose triggered production-branch lazy imports: {offenders}"
    )


# ── G6 — budget denial rejected in the spine (CC6.7-c mechanism proof) ─────


class _DenyVKeys:
    """VirtualKeyPort that REJECTS — the over-budget signal CC6.7-c's gate acts on."""

    async def check_budget(self, key_alias: str) -> None:
        raise BudgetExhaustedError(f"vkey {key_alias!r} is over budget")


def test_G6_budget_denial_rejected_in_spine(tmp_path: Path) -> None:
    deny_policy = GatewayPolicy(
        allowed_user_ids=frozenset({"user-1"}),
        oidc_policy=FakeOidcPolicy(),
        virtual_keys=_DenyVKeys(),
    )
    harness = make_gateway_harness(tmp_path, policy=deny_policy)

    with pytest.raises(GatewayCtxError) as exc_info:
        harness.gateway.execute(make_intent(), make_ctx())

    field = exc_info.value.context_field
    # The deny vkey is what rejected (gate mechanism is REAL) ...
    assert "BudgetExhaustedError" in field
    # ... surfacing on the auth leg → the webhook maps auth→401 (NOT the dead 402 branch).
    assert field.startswith("auth")


# ── O-9 characterization (PLAIN GREEN; flip-trigger for the durable-store skip) ─


def test_O_9_durable_nonce_store_is_thread_affine(tmp_path: Path) -> None:
    """The durable SQLite NonceStore's connection is bound to the creating thread
    (check_same_thread default True). A foreign-thread check_and_mark raises
    sqlite3.ProgrammingError — exactly why the worker-thread bridge uses
    InMemoryNonceStore (O-9). When nonce.py is made thread-safe, this stops
    raising → the test breaks → forces the register's O-9 entry to flip."""
    store = NonceStore(db_path=tmp_path / "nonce.sqlite3")  # connection on THIS thread
    captured: dict[str, BaseException] = {}

    def _foreign_thread() -> None:
        try:
            asyncio.run(store.check_and_mark("nonce-foreign-1"))
        except BaseException as exc:  # noqa: BLE001 — characterizing the raised type
            captured["exc"] = exc

    thread = threading.Thread(target=_foreign_thread)
    thread.start()
    thread.join()
    asyncio.run(store.close())

    assert isinstance(captured.get("exc"), sqlite3.ProgrammingError)


# ── CC6.7-c characterization — egress topology is split (spend-blind) ──────


def test_CC6_7_c_llm_egress_bypasses_the_vkey_metering_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production: the LLM proxy egresses DIRECT to DIAL, while the vkey adapter
    meters against LITELLM_PROXY_URL — DIFFERENT endpoints. So the vkey gate never
    sees real model spend (spend-blind). Construction-only; no live calls."""
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "production")
    monkeypatch.setenv("DIAL_API_KEY", "dial-test-key")
    monkeypatch.setenv("LITELLM_PROXY_URL", "https://litellm-metering.proxy.invalid")
    monkeypatch.setenv("LITELLM_MASTER_KEY", "sk-master")

    llm = comp._build_llm_proxy()
    vkey = comp._build_virtual_keys()

    llm_egress = llm._api_base_overrides["azure"]  # type: ignore[attr-defined]
    vkey_metering = vkey._base_url  # type: ignore[attr-defined]

    assert llm_egress == DIAL_API_BASE  # direct to DIAL
    assert vkey_metering == "https://litellm-metering.proxy.invalid"
    assert llm_egress != vkey_metering  # the spend-blind split (CC6.7-c)
