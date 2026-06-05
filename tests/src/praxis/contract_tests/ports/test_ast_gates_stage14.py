"""Stage 14 AST gates: A-S14 (JWKS wired in OidcPolicy), B-S14 (no double
decode + no channel-audience literal), C-S14 (no_waiver constant pin)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
OIDC_PATH = ROOT / "kernel" / "auth" / "src" / "praxis" / "kernel" / "auth" / "oidc.py"
CLAIMS_PATH = (
    ROOT / "kernel" / "auth" / "src" / "praxis" / "kernel" / "auth" / "claims.py"
)
CHANNELS_ROOT = ROOT / "adapters" / "channels"


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _function(path: Path, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in ast.walk(_tree(path)):
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name == name
        ):
            return node
    raise AssertionError(f"{name} not found in {path}")


def _method(
    path: Path, class_name: str, method_name: str
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if (
                    isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
                    and item.name == method_name
                ):
                    return item
    raise AssertionError(f"{class_name}.{method_name} not found in {path}")


@pytest.mark.no_waiver
def test_gate_a_s14_jwks_wired_in_oidc_policy() -> None:
    """OidcPolicy.authenticate body must reference JwksCache surfaces."""
    node = _method(OIDC_PATH, "OidcPolicy", "authenticate")
    refs: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Attribute) and sub.attr in {
            "get_key",
            "get_or_fetch",
            "_jwks_cache",
        }:
            refs.add(sub.attr)
    assert refs, (
        "OidcPolicy.authenticate must reference JwksCache "
        "(_jwks_cache attribute + get_key/get_or_fetch call); "
        f"observed attrs: {sorted(refs)}"
    )


@pytest.mark.no_waiver
def test_gate_b_s14_no_double_decode_and_no_channel_audience_literal() -> None:
    """extract_claims body must NOT call authlib raw (self._jwt.decode or
    JsonWebToken.decode); must call verifier.decode (orchestrator delegation,
    >= 1 call); literal 'verdaca-channel-adapter' must NOT appear in
    production paths."""

    # Part 1: AST scan of extract_claims body
    node = _function(CLAIMS_PATH, "extract_claims")
    forbidden_hits: list[str] = []
    verifier_decode_hits = 0
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
            if sub.func.attr == "decode":
                receiver = sub.func.value
                if isinstance(receiver, ast.Attribute) and receiver.attr == "_jwt":
                    forbidden_hits.append(ast.unparse(sub.func))
                elif (
                    isinstance(receiver, ast.Name) and receiver.id == "JsonWebToken"
                ):
                    forbidden_hits.append(ast.unparse(sub.func))
                elif isinstance(receiver, ast.Name) and receiver.id == "verifier":
                    verifier_decode_hits += 1
    assert not forbidden_hits, (
        f"extract_claims must NOT call authlib raw decode; observed: {forbidden_hits}"
    )
    assert verifier_decode_hits >= 1, (
        "extract_claims body must call verifier.decode at least once "
        "(orchestrator-level delegation)"
    )

    # Part 2: literal "verdaca-channel-adapter" absent from production paths
    offenders: list[str] = []
    paths_to_check: list[Path] = [CLAIMS_PATH]
    if CHANNELS_ROOT.is_dir():
        paths_to_check.extend(
            p
            for p in CHANNELS_ROOT.rglob("*.py")
            if "__pycache__" not in p.parts
        )
    for path in paths_to_check:
        text = path.read_text(encoding="utf-8")
        if "verdaca-channel-adapter" in text:
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == [], (
        "Literal 'verdaca-channel-adapter' must not appear in production "
        f"paths (audience must be threaded via config, not hardcoded): {offenders}"
    )


@pytest.mark.no_waiver
def test_gate_c_s14_no_waiver_constant_pin() -> None:
    """STAGE14_RUNTIME_NO_WAIVER_COUNT must equal 14; tree-walked discovered
    set cardinality must equal that constant (decomposes as 4 Stage 13 NEW
    runtime + 1 Stage 14 NEW runtime + 6 Stage 13 AST gates + 3 Stage 14
    AST gates = 14 distinct marker IDs)."""
    from praxis.contract_tests.test_stage14_no_waiver_count import (
        STAGE14_RUNTIME_NO_WAIVER_COUNT,
        collect_stage14_runtime_no_waiver_ids,
    )

    assert STAGE14_RUNTIME_NO_WAIVER_COUNT == 14
    observed = collect_stage14_runtime_no_waiver_ids()
    assert len(observed) == STAGE14_RUNTIME_NO_WAIVER_COUNT
