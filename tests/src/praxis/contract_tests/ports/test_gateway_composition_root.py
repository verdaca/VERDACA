"""Stage 13 composition-root MAC-Ts."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from praxis.contract_tests.ports.gateway_contract_fakes import (
    FakeCompaction,
    FakeCostMeter,
    FakeLLMProxy,
    FakeMemory,
    make_auth_quartet,
)
from praxis.kernel.gateway.composition import build_gateway
from praxis.kernel.session_index.sqlite_store import SqliteSessionIndex
from praxis.ports.gateway import GatewayPort

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
    }


@pytest.mark.no_waiver
def test_M_T_AUTH_VERIFIER_WIRED_AT_COMPOSITION_01_canonical_factory_requires_auth_quartet(
    tmp_path,
) -> None:
    assert build_gateway.__module__ == "praxis.kernel.gateway.composition"

    deps = _deps(tmp_path)
    gateway = build_gateway(**deps)

    assert isinstance(gateway, GatewayPort)
    assert gateway.jwt_verifier is deps["jwt_verifier"]
    sig = inspect.signature(build_gateway)
    for param in sig.parameters.values():
        assert param.kind is inspect.Parameter.KEYWORD_ONLY
        assert param.default is inspect.Parameter.empty


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
