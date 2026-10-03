"""Stage 12 H#5 AST gates for auth and channel-adapter boundaries."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[4]
POLICY_PATH = ROOT / "kernel" / "gateway" / "src" / "praxis" / "kernel" / "gateway" / "policy.py"
AUTH_ROOT = ROOT / "kernel" / "auth" / "src" / "praxis" / "kernel" / "auth"
CHANNELS_ROOT = ROOT / "adapters" / "channels"


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def _literal_strings(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def _is_ignored_repo_path(path: Path) -> bool:
    ignored_parts = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "__pycache__"}
    return bool(ignored_parts.intersection(path.parts)) or path.parts[0] in {
        "_bmad-output",
        "graphify-out",
    }


def test_M_T_GATEWAY_POLICY_NO_DIRECT_ADAPTER_IMPORT_01_policy_imports_no_adapters() -> None:
    assert not {
        module
        for module in _imports(POLICY_PATH)
        if module == "praxis.adapters" or module.startswith("praxis.adapters.")
    }


@pytest.mark.no_waiver
def test_M_T_AUTH_KERNEL_NO_ADAPTER_IMPORT_01_auth_kernel_imports_no_adapters() -> None:
    offenders = {
        str(path.relative_to(ROOT)): module
        for path in _python_files(AUTH_ROOT)
        for module in _imports(path)
        if module == "praxis.adapters" or module.startswith("praxis.adapters.")
    }

    assert offenders == {}


def test_M_T_WEBHOOK_SIG_ISOLATION_01_signing_imports_only_in_webhook_modules() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for path in _python_files(CHANNELS_ROOT)
        if path.name != "webhook.py"
        if {"hmac", "hashlib"}.intersection(_imports(path))
    ]

    assert offenders == []


def test_M_T_AUTH_NO_HARDCODED_DISCOVERY_URL_01_no_vendor_discovery_literals() -> None:
    forbidden_fragments = (
        ".well-known/openid-configuration",
        "login.microsoftonline.com",
        "accounts.google.com",
        "auth0.com",
        "okta",
    )
    offenders = [
        str(path.relative_to(ROOT))
        for root in (AUTH_ROOT, CHANNELS_ROOT)
        for path in _python_files(root)
        for literal in _literal_strings(path)
        if "://" in literal and any(fragment in literal for fragment in forbidden_fragments)
    ]

    assert offenders == []


def test_M_T_NO_STAR_IMPORT_GATEWAY_01_no_gateway_star_imports() -> None:
    offenders: list[str] = []
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT)
        if _is_ignored_repo_path(rel):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module in {"praxis.kernel.gateway", "praxis.ports.gateway"}
                and any(alias.name == "*" for alias in node.names)
            ):
                offenders.append(str(rel))

    assert offenders == []


def test_M_T_SDK_VERSION_PINNED_01_channel_external_dependencies_are_bounded() -> None:
    offenders: list[str] = []
    for pyproject in (
        ROOT / "adapters" / "channels" / "teams" / "pyproject.toml",
        ROOT / "adapters" / "channels" / "slack" / "pyproject.toml",
    ):
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        for dep in data["project"]["dependencies"]:
            if dep.startswith("praxis-"):
                continue
            if not any(operator in dep for operator in ("==", ">=", "~=", "<")):
                offenders.append(f"{pyproject.relative_to(ROOT)}:{dep}")

    assert offenders == []


def test_M_T_GATEWAY_WIRING_NO_AUTH_LOGIC_01_policy_has_no_low_level_auth_imports() -> None:
    forbidden = {"authlib", "cryptography", "hashlib", "hmac"}
    offenders = {
        module
        for module in _imports(POLICY_PATH)
        if module in forbidden or any(module.startswith(f"{name}.") for name in forbidden)
    }

    assert offenders == set()
