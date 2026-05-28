"""Stage 13 channel adapter async-post MAC-Ts."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[5]
TEAMS_ADAPTER = (
    ROOT / "adapters" / "channels" / "teams" / "src" / "praxis"
    / "adapters" / "channels" / "teams" / "adapter.py"
)
SLACK_ADAPTER = (
    ROOT / "adapters" / "channels" / "slack" / "src" / "praxis"
    / "adapters" / "channels" / "slack" / "adapter.py"
)


def _class_method(path: Path, class_name: str, method_name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if (
                    isinstance(item, ast.AsyncFunctionDef | ast.FunctionDef)
                    and item.name == method_name
                ):
                    return item
    raise AssertionError(f"{class_name}.{method_name} not found")


def test_M_T_CHANNELS_TEAMS_POST_RESULT_ASYNC_01_post_result_is_async() -> None:
    assert isinstance(
        _class_method(TEAMS_ADAPTER, "TeamsAdapter", "post_result"),
        ast.AsyncFunctionDef,
    )


def test_M_T_CHANNELS_SLACK_POST_RESULT_ASYNC_01_post_result_is_async() -> None:
    assert isinstance(
        _class_method(SLACK_ADAPTER, "SlackAdapter", "post_result"),
        ast.AsyncFunctionDef,
    )


def test_M_T_CHANNELS_HTTPX_ASYNCCLIENT_01_sync_client_absent_from_adapter_bodies() -> None:
    for path in (TEAMS_ADAPTER, SLACK_ADAPTER):
        text = path.read_text(encoding="utf-8")
        assert "httpx.AsyncClient" in text
        assert "httpx.Client" not in text
