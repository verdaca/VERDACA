"""Stage 13 composition-root MAC-Ts."""

from __future__ import annotations

import ast
import inspect
from dataclasses import replace
from pathlib import Path

import pytest

from praxis.contract_tests.ports.gateway_contract_fakes import (
    FakeCompaction,
    FakeCostMeter,
    FakeLLMProxy,
    FakeMemory,
    FakeVirtualKeys,
    make_auth_quartet,
    make_ctx,
    make_intent,
)
from praxis.kernel.auth import AuthClaims
from praxis.kernel.gateway import GatewayPolicy
from praxis.kernel.gateway.composition import build_gateway
from praxis.kernel.session_index.sqlite_store import SqliteSessionIndex
from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_errors import GatewayCtxError

ROOT = Path(__file__).parents[5]
COMPOSITION_PATH = (
    ROOT / "kernel" / "gateway" / "src" / "praxis" / "kernel" / "gateway" / "composition.py"
)


def _deps(tmp_path):
    jwt_verifier, oidc_policy, nonce_store, webhook_resolver = make_auth_quartet()
    return {
        "session_index": SqliteSessionIndex(tmp_path / "session-index.sqlite3"),
        "compaction": FakeCompaction(),
        "memory": FakeMemory(),
        "llm_proxy": FakeLLMProxy(),
        "cost_meter": FakeCostMeter(),
        "channel_adapters": {},
        "jwt_verifier": jwt_verifier,
        "oidc_policy": oidc_policy,
        "nonce_store": nonce_store,
        "webhook_resolver": webhook_resolver,
        "policy": GatewayPolicy(
            allowed_user_ids=frozenset({"user-1"}),
            oidc_policy=oidc_policy,
            virtual_keys=FakeVirtualKeys(),
        ),
    }


class _TracingOidcPolicy:
    def __init__(self, order: list[str]) -> None:
        self.order = order
        self.tokens: list[str] = []

    async def authenticate(self, bearer_token: str) -> AuthClaims:
        self.order.append("auth")
        self.tokens.append(bearer_token)
        return AuthClaims(
            _claims={
                "aud": "api://verdaca",
                "exp": "1790784000",
                "iat": "1767225600",
                "iss": "https://issuer.example.invalid",
                "nonce": f"nonce:{bearer_token}",
                "sub": "user-1",
            }
        )


class _TracingNonceStore:
    persistent = False

    def __init__(self, order: list[str]) -> None:
        self.order = order
        self.nonces: list[str] = []

    async def check_and_mark(self, nonce: str) -> None:
        self.order.append("nonce")
        self.nonces.append(nonce)


class _TracingMemory(FakeMemory):
    def __init__(self, order: list[str]) -> None:
        super().__init__()
        self.order = order

    def query(self, q):
        self.order.append("memory")
        return super().query(q)


class _TracingVirtualKeys:
    def __init__(self, order: list[str]) -> None:
        self.order = order
        self.checked: list[str] = []

    async def check_budget(self, key_alias: str) -> None:
        self.order.append("budget")
        self.checked.append(key_alias)


@pytest.mark.no_waiver
def test_M_T_GATEWAY_EXECUTE_AUTH_FIRST_01_canonical_factory_invokes_auth_before_downstream(
    tmp_path,
) -> None:
    assert build_gateway.__module__ == "praxis.kernel.gateway.composition"

    deps = _deps(tmp_path)
    order: list[str] = []
    oidc_policy = _TracingOidcPolicy(order)
    nonce_store = _TracingNonceStore(order)
    memory = _TracingMemory(order)
    virtual_keys = _TracingVirtualKeys(order)
    deps["oidc_policy"] = oidc_policy
    deps["nonce_store"] = nonce_store
    deps["memory"] = memory
    deps["policy"] = GatewayPolicy(
        allowed_user_ids=frozenset({"user-1"}),
        oidc_policy=oidc_policy,
        virtual_keys=virtual_keys,
    )
    gateway = build_gateway(**deps)

    assert isinstance(gateway, GatewayPort)
    assert gateway.jwt_verifier is deps["jwt_verifier"]
    result = gateway.execute(make_intent(), make_ctx())

    assert result.session.status == "completed"
    assert order[:3] == ["auth", "nonce", "budget"]
    assert "memory" in order
    assert order.index("budget") < order.index("memory")
    assert oidc_policy.tokens == ["token-req-1"]
    assert nonce_store.nonces == ["nonce:token-req-1"]
    assert virtual_keys.checked == ["user-1"]

    missing_bearer_ctx = replace(make_ctx("req-missing"), rate_limit_token=None)
    order.clear()
    with pytest.raises(GatewayCtxError) as exc_info:
        gateway.execute(make_intent(idempotency_key="missing-bearer"), missing_bearer_ctx)

    assert exc_info.value.context_field == "auth:builtins.ValueError"
    assert order == []
    assert len(memory.queries) == 1


def test_M_T_AUTH_VERIFIER_WIRED_AT_COMPOSITION_01_canonical_factory_requires_auth_quartet(
    tmp_path,
) -> None:
    deps = _deps(tmp_path)
    gateway = build_gateway(**deps)

    assert isinstance(gateway, GatewayPort)
    assert gateway.jwt_verifier is deps["jwt_verifier"]
    sig = inspect.signature(build_gateway)
    for param in sig.parameters.values():
        assert param.kind is inspect.Parameter.KEYWORD_ONLY
        assert param.default is inspect.Parameter.empty


def test_M_T_GATEWAY_COMPOSITION_POLICY_CONFIGURED_01_factory_uses_supplied_policy(
    tmp_path,
) -> None:
    deps = _deps(tmp_path)
    order: list[str] = []
    oidc_policy = _TracingOidcPolicy(order)
    deps["oidc_policy"] = oidc_policy
    deps["nonce_store"] = _TracingNonceStore(order)
    deps["policy"] = GatewayPolicy(
        allowed_user_ids=frozenset({"user-1"}),
        oidc_policy=oidc_policy,
        virtual_keys=FakeVirtualKeys(),
    )
    gateway = build_gateway(**deps)

    assert gateway.execute(make_intent(), make_ctx()).session.status == "completed"

    with pytest.raises(GatewayCtxError) as exc_info:
        gateway.execute(
            replace(
                make_intent(idempotency_key="blocked", workspace_id="workspace-1"),
                requester_user_id="blocked-user",
            ),
            replace(make_ctx("req-blocked"), caller_id="blocked-user"),
        )

    assert exc_info.value.context_field == "policy:user_not_allowlisted"


def test_M_T_COMPOSITION_NO_NONE_DEFAULT_01_build_gateway_has_no_optional_defaults() -> None:
    sig = inspect.signature(build_gateway)

    assert set(sig.parameters) == {
        "session_index",
        "compaction",
        "memory",
        "llm_proxy",
        "cost_meter",
        "channel_adapters",
        "jwt_verifier",
        "oidc_policy",
        "nonce_store",
        "webhook_resolver",
        "policy",
    }
    assert all(param.default is inspect.Parameter.empty for param in sig.parameters.values())


def test_M_T_COMPOSITION_NO_INTERNAL_IMPORT_01_composition_imports_public_surfaces() -> None:
    tree = ast.parse(COMPOSITION_PATH.read_text(encoding="utf-8"))
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert all("._internal" not in module for module in imports)
    assert all(
        module.startswith(("praxis.ports", "praxis.kernel.auth", "praxis.kernel.gateway"))
        or module in {"__future__", "collections.abc", "praxis.kernel.session_index.port"}
        for module in imports
    )
