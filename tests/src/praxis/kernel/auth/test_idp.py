"""Stage 12 H#3.4 AST gate for the bounded IdP discovery API."""

from __future__ import annotations

import ast
from pathlib import Path

IDP_MODULE = (
    Path(__file__).parents[5]
    / "kernel"
    / "auth"
    / "src"
    / "praxis"
    / "kernel"
    / "auth"
    / "idp.py"
)


def _public_alias(alias: ast.alias) -> str | None:
    name = alias.asname or alias.name.rsplit(".", maxsplit=1)[-1]
    if name.startswith("_"):
        return None
    return name


def _public_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update(
                name
                for alias in node.names
                if (name := _public_alias(alias)) is not None
            )
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            if not node.name.startswith("_"):
                names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if not node.target.id.startswith("_"):
                names.add(node.target.id)
    return names


def test_M_T_AUTH_IDP_DISCOVER_SOLE_EXPORT_01_idp_module_has_one_public_name() -> None:
    tree = ast.parse(IDP_MODULE.read_text(encoding="utf-8"))

    assert _public_names(tree) == {"discover"}
