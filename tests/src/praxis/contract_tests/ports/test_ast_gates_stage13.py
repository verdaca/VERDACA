"""Stage 13 AST gates A-F plus bare-except auth/crypto invariant."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
CLOSE_MEMO_GLOB = "docs/stage-*-ratified-close-memo.md"
CLAIMS_PATH = ROOT / "kernel" / "auth" / "src" / "praxis" / "kernel" / "auth" / "claims.py"
OIDC_PATH = ROOT / "kernel" / "auth" / "src" / "praxis" / "kernel" / "auth" / "oidc.py"
NONCE_PATH = ROOT / "kernel" / "auth" / "src" / "praxis" / "kernel" / "auth" / "nonce.py"
COMPOSITION_PATH = (
    ROOT / "kernel" / "gateway" / "src" / "praxis" / "kernel" / "gateway" / "composition.py"
)
SERVICE_PATH = ROOT / "kernel" / "gateway" / "src" / "praxis" / "kernel" / "gateway" / "service.py"


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _function(path: Path, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} not found in {path}")


def _class(path: Path, name: str) -> ast.ClassDef:
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise AssertionError(f"{name} not found in {path}")


def _annotation_contains_optional(annotation: ast.expr | None) -> bool:
    if annotation is None:
        return False
    return "Optional" in ast.unparse(annotation) or "None" in ast.unparse(annotation)


def _tracked_close_memos() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", CLOSE_MEMO_GLOB],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        line.strip().replace("\\", "/")
        for line in result.stdout.splitlines()
        if line.strip()
    }


def _on_disk_close_memos() -> set[str]:
    return {path.relative_to(ROOT).as_posix() for path in ROOT.glob(CLOSE_MEMO_GLOB)}


@pytest.mark.no_waiver
def test_gate_a_extract_claims_no_none_default() -> None:
    node = _function(CLAIMS_PATH, "extract_claims")
    verifier = next(arg for arg in node.args.args if arg.arg == "verifier")
    defaults = list(node.args.defaults)
    defaulted_arg_names = [arg.arg for arg in node.args.args[-len(defaults) :]] if defaults else []

    assert "verifier" not in defaulted_arg_names
    assert not _annotation_contains_optional(verifier.annotation)


@pytest.mark.no_waiver
def test_gate_b_oidc_policy_verifier_required() -> None:
    cls = _class(OIDC_PATH, "OidcPolicy")
    init = next(
        node
        for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    )
    all_args = [*init.args.args, *init.args.kwonlyargs]
    verifier = next(arg for arg in all_args if arg.arg == "verifier")
    defaults = list(init.args.defaults)
    defaulted_arg_names = [arg.arg for arg in init.args.args[-len(defaults) :]] if defaults else []
    kw_defaulted_arg_names = [
        arg.arg
        for arg, default in zip(init.args.kwonlyargs, init.args.kw_defaults, strict=True)
        if default is not None
    ]

    assert "verifier" not in defaulted_arg_names
    assert "verifier" not in kw_defaulted_arg_names
    assert not _annotation_contains_optional(verifier.annotation)


@pytest.mark.no_waiver
def test_gate_c_build_gateway_full_deps() -> None:
    node = _function(COMPOSITION_PATH, "build_gateway")

    assert node.args.args == []
    assert [arg.arg for arg in node.args.kwonlyargs] == [
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
    ]
    assert node.args.kw_defaults == [None] * 10


@pytest.mark.no_waiver
def test_gate_d_nonce_store_sqlite_invariants() -> None:
    cls = _class(NONCE_PATH, "NonceStore")
    init = next(
        node
        for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    )
    db_path = next(arg for arg in init.args.kwonlyargs if arg.arg == "db_path")
    text = NONCE_PATH.read_text(encoding="utf-8")

    assert db_path.annotation is not None
    assert "Path" in ast.unparse(db_path.annotation)
    assert "persistent: ClassVar[bool] = True" in text
    assert "PRAGMA journal_mode=WAL" in text
    assert "PRAGMA synchronous=NORMAL" in text
    assert "BEGIN IMMEDIATE" in text


@pytest.mark.no_waiver
def test_gate_e_session_id_min_width() -> None:
    text = SERVICE_PATH.read_text(encoding="utf-8")
    assert "hexdigest()[:16]" not in text
    tree = _tree(SERVICE_PATH)
    widths: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
            value = node.value
            if (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Attribute)
                and value.func.attr == "hexdigest"
                and isinstance(node.slice.upper, ast.Constant)
                and isinstance(node.slice.upper.value, int)
            ):
                widths.append(node.slice.upper.value)
    assert not widths or all(width >= 32 for width in widths)


@pytest.mark.no_waiver
def test_gate_f_close_memo_tracking_symmetry() -> None:
    assert _tracked_close_memos() == _on_disk_close_memos()


@pytest.mark.no_waiver
def test_M_T_NO_BARE_EXCEPT_AUTH_CRYPTO_01_no_bare_except_handlers() -> None:
    offenders: list[str] = []
    for root in (
        ROOT / "kernel" / "auth" / "src" / "praxis" / "kernel" / "auth",
        ROOT / "kernel" / "gateway" / "src" / "praxis" / "kernel" / "gateway",
    ):
        for path in root.rglob("*.py"):
            tree = _tree(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    offenders.append(f"{path.relative_to(ROOT).as_posix()}:{node.lineno}")

    assert offenders == []
