"""Stage 11 GatewayPort read API refreeze contract tests."""

from __future__ import annotations

import json

from praxis.contract_tests.ports.gateway_contract_fakes import (
    make_ctx,
    make_gateway_harness,
    make_intent,
)


def test_M_T_GATEWAY_READ_SUMMARY_01_delegates_to_session_index(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path)
    result = harness.gateway.execute(make_intent(), make_ctx())

    summary = json.loads(harness.gateway.get_session_summary(result.session.session_id))

    assert harness.session_index.get_session_calls == 1
    assert summary == {
        "artifact_ids": [result.artifacts[0].artifact_id],
        "session_id": result.session.session_id,
        "source_uri": result.session.source_uri,
        "status": "completed",
        "title": "Which buyer path should we take?",
    }


def test_M_T_GATEWAY_READ_TRANSCRIPT_01_delegates_to_session_index(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path)
    result = harness.gateway.execute(make_intent(), make_ctx())

    transcript = json.loads(harness.gateway.get_session_transcript(result.session.session_id))

    assert harness.session_index.get_session_calls == 1
    assert transcript["session_id"] == result.session.session_id
    assert transcript["user_id"] == "user-1"
    assert transcript["title"] == "Which buyer path should we take?"
    assert transcript["skill_ids"] == ["stage11-gateway"]
    assert transcript["artifact_ids"] == [result.artifacts[0].artifact_id]


def test_M_T_GATEWAY_READ_ARTIFACT_01_delegates_to_session_index(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path)
    result = harness.gateway.execute(make_intent(), make_ctx())
    expected_artifact = result.artifacts[0]

    artifact = harness.gateway.get_artifact(
        result.session.session_id,
        expected_artifact.artifact_id,
    )

    assert harness.session_index.get_artifact_calls == 1
    assert artifact.artifact_id == expected_artifact.artifact_id
    assert artifact.session_id == result.session.session_id
    assert artifact.kind == "summary"
    assert artifact.uri == expected_artifact.uri


def test_M_T_GATEWAY_READ_LIST_01_delegates_with_workspace_filter_and_limit(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path)
    workspace_1_a = harness.gateway.execute(
        make_intent("idem-1", workspace_id="workspace-1"),
        make_ctx("req-1"),
    )
    workspace_2 = harness.gateway.execute(
        make_intent("idem-2", workspace_id="workspace-2"),
        make_ctx("req-2"),
    )
    workspace_1_b = harness.gateway.execute(
        make_intent("idem-3", workspace_id="workspace-1"),
        make_ctx("req-3"),
    )

    workspace_handles = harness.gateway.list_sessions(workspace_id="workspace-1", limit=10)
    limited_handles = harness.gateway.list_sessions(workspace_id="workspace-1", limit=1)
    all_handles = harness.gateway.list_sessions()

    assert harness.session_index.list_sessions_calls == 3
    assert {handle.session_id for handle in workspace_handles} == {
        workspace_1_a.session.session_id,
        workspace_1_b.session.session_id,
    }
    assert workspace_2.session.session_id not in {
        handle.session_id for handle in workspace_handles
    }
    assert len(limited_handles) == 1
    assert len(all_handles) == 3
    assert harness.session_index.list_sessions_criteria[0] is not None
    assert (
        harness.session_index.list_sessions_criteria[0].source_uri_prefix
        == "gateway://workspaces/workspace-1/"
    )
    assert all(
        handle.source_uri.startswith("gateway://workspaces/workspace-1/")
        for handle in workspace_handles
    )
