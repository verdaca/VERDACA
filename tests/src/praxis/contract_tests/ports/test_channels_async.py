"""Stage 13 channel adapter async-post MAC-Ts."""

from __future__ import annotations

import ast
import asyncio
import logging
from decimal import Decimal
from pathlib import Path

import pytest

from praxis.adapters.channels.slack.adapter import SlackAdapter
from praxis.adapters.channels.teams.adapter import TeamsAdapter
from praxis.ports.gateway_dto import AnalysisResult, ArtifactRef, SessionHandle

ROOT = Path(__file__).parents[5]
TEAMS_ADAPTER = (
    ROOT / "adapters" / "channels" / "teams" / "src" / "praxis"
    / "adapters" / "channels" / "teams" / "adapter.py"
)
SLACK_ADAPTER = (
    ROOT / "adapters" / "channels" / "slack" / "src" / "praxis"
    / "adapters" / "channels" / "slack" / "adapter.py"
)


def _result() -> AnalysisResult:
    return AnalysisResult(
        session=SessionHandle(session_id="session-1", status="complete", source_uri="channel://x"),
        recommendation="Proceed.",
        cited_tradeoffs=(),
        artifacts=(
            ArtifactRef(
                artifact_id="artifact-1",
                session_id="session-1",
                kind="summary",
                uri="artifact://session-1/artifact-1",
            ),
        ),
        cost_usd=Decimal("0.01"),
    )


class _FailingAsyncClient:
    async def post(self, url: str, *, json: object) -> object:
        raise RuntimeError(f"post failed:{url}")


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


@pytest.mark.parametrize(
    ("adapter", "url", "expected_log"),
    (
        (TeamsAdapter(http_client=_FailingAsyncClient()), "https://teams.example/post", "Teams"),
        (SlackAdapter(http_client=_FailingAsyncClient()), "https://slack.example/post", "Slack"),
    ),
)
@pytest.mark.asyncio
async def test_M_T_CHANNEL_POST_RESULT_ERROR_OBSERVED_01_in_loop_failure_is_logged(
    adapter: TeamsAdapter | SlackAdapter,
    url: str,
    expected_log: str,
    caplog,
) -> None:
    caplog.set_level(logging.ERROR)

    adapter._dispatch_post_result(url, _result())

    await asyncio.gather(*adapter._post_tasks, return_exceptions=True)
    await asyncio.sleep(0)

    assert adapter._post_tasks == set()
    assert f"{expected_log} post_result failed" in caplog.text
    assert "post failed:" in caplog.text
