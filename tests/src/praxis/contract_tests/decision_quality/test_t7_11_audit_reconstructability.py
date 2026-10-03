"""T7.11 Audit reconstructability — Governance & Decision-Quality (T7) tier.

Literature source: Mokander et al. (2023) three-layered LLM audit
(verdaca-literature-review.md §"Assessment Approaches to Carry Forward for
Murat", row "Audit evidence cannot be reconstructed"). The lever: for every
run, the auditor must be able to reconstruct session ID, caller/channel, auth
path, evidence artifacts, model calls, cost, gate outcomes, and the final
result.

Verdaca operationalization: after a single ``gateway.execute`` run, each of the
eight audit dimensions is queryable from the persisted SessionIndex (the
governance/application audit substrate) plus the gateway's recorded
auth/cost/model seams:

    1. session ID      → AnalysisResult.session.session_id == indexed record
    2. caller          → SessionIndex transcript user_id
    3. channel         → source_uri encodes channel + channel_session_id
    4. auth path       → OIDC authenticate + nonce check both fired
    5. evidence        → artifact ref queryable via get_artifact / memory query
    6. model calls     → exactly one LLM call recorded
    7. cost            → ledger record + result cost summary
    8. gate outcomes   → run reached "completed" (policy allow gate passed)
    + final result     → recommendation present and queryable

PASS: all eight dimensions + final result reconstructable from a single run.
Hermetic — real SqliteSessionIndex + contract fakes, no creds. Plain tests
(NO @pytest.mark.no_waiver; 14/9/23 pin untouched).
"""

from __future__ import annotations

import json

from praxis.contract_tests.ports.gateway_contract_fakes import (
    make_ctx,
    make_gateway_harness,
    make_intent,
)


def test_T7_11_AUDIT_session_id_reconstructable(tmp_path) -> None:
    """Dimension 1 — session ID: the result's session id is the key under
    which the run is indexed and re-fetchable from SessionIndex."""
    harness = make_gateway_harness(tmp_path)
    result = harness.gateway.execute(make_intent(), make_ctx())

    record = harness.session_index.get_session(result.session.session_id)
    assert record is not None
    assert record.session_id == result.session.session_id


def test_T7_11_AUDIT_caller_and_channel_reconstructable(tmp_path) -> None:
    """Dimensions 2+3 — caller + channel: the SessionIndex transcript carries
    the caller (user_id) and the source_uri encodes the channel and the
    channel session id."""
    harness = make_gateway_harness(tmp_path)
    ctx = make_ctx()
    result = harness.gateway.execute(make_intent(), ctx)

    transcript = json.loads(
        harness.gateway.get_session_transcript(result.session.session_id)
    )
    assert transcript["user_id"] == "user-1"  # caller
    # channel + channel_session_id are encoded in the persisted source_uri.
    assert f"/channels/{ctx.channel.value}/" in transcript["source_uri"]
    assert f"/sessions/{ctx.channel_session_id}" in transcript["source_uri"]


def test_T7_11_AUDIT_auth_path_reconstructable(tmp_path) -> None:
    """Dimension 4 — auth path: the OIDC authenticate step and the nonce
    single-use check both fired for the run (the governance-layer audit
    trail), evidenced by the recorded seams."""
    harness = make_gateway_harness(tmp_path)
    ctx = make_ctx()
    harness.gateway.execute(make_intent(), ctx)

    # FakeOidcPolicy records the bearer it authenticated.
    oidc = harness.gateway.oidc_policy
    assert oidc.tokens == [ctx.rate_limit_token]  # type: ignore[attr-defined]
    # The nonce store marked the request nonce (replay defense fired). The
    # FakeOidcPolicy mints nonce "nonce:<bearer>" for the verified claims.
    nonce_store = harness.gateway.nonce_store
    assert f"nonce:{ctx.rate_limit_token}" in nonce_store._seen  # type: ignore[attr-defined]


def test_T7_11_AUDIT_evidence_artifacts_reconstructable(tmp_path) -> None:
    """Dimension 5 — evidence: the run's artifact ref is queryable from
    SessionIndex, and the evidence-gathering (memory query) seam fired."""
    harness = make_gateway_harness(tmp_path)
    result = harness.gateway.execute(make_intent(), make_ctx())

    artifact_id = result.artifacts[0].artifact_id
    artifact = harness.gateway.get_artifact(result.session.session_id, artifact_id)
    assert artifact.artifact_id == artifact_id
    assert artifact.session_id == result.session.session_id
    # Evidence was gathered: the memory port was queried during the run.
    assert len(harness.memory.queries) == 1


def test_T7_11_AUDIT_model_calls_and_cost_reconstructable(tmp_path) -> None:
    """Dimensions 6+7 — model calls + cost: exactly one LLM call was made and
    its cost was recorded on the ledger and summarized on the result."""
    harness = make_gateway_harness(tmp_path)
    result = harness.gateway.execute(make_intent(), make_ctx())

    assert len(harness.llm.calls) == 1  # model calls
    assert len(harness.cost.records) == 1  # cost ledger
    assert result.cost_usd is not None  # cost summary


def test_T7_11_AUDIT_gate_outcome_and_final_result_reconstructable(tmp_path) -> None:
    """Dimension 8 + final result — gate outcomes + final result: reaching the
    persisted "completed" status proves the policy allow-gate passed, and the
    recommendation (final result) is reconstructable from SessionIndex."""
    harness = make_gateway_harness(tmp_path)
    result = harness.gateway.execute(make_intent(), make_ctx())

    record = harness.session_index.get_session(result.session.session_id)
    assert record is not None
    assert record.status == "completed"  # gate passed → completed
    assert result.recommendation.strip()  # final result present


def test_T7_11_AUDIT_full_eight_dimension_reconstruction_pass_criterion(tmp_path) -> None:
    """PASS criterion: a single run yields all eight audit dimensions + the
    final result, all reconstructable from SessionIndex + recorded seams."""
    harness = make_gateway_harness(tmp_path)
    ctx = make_ctx()
    result = harness.gateway.execute(make_intent(), ctx)

    record = harness.session_index.get_session(result.session.session_id)
    assert record is not None
    transcript = json.loads(
        harness.gateway.get_session_transcript(result.session.session_id)
    )

    dimensions = {
        "session_id": record.session_id == result.session.session_id,
        "caller": transcript["user_id"] == "user-1",
        "channel": f"/channels/{ctx.channel.value}/" in transcript["source_uri"],
        "auth_path": harness.gateway.oidc_policy.tokens  # type: ignore[attr-defined]
        == [ctx.rate_limit_token],
        "evidence": len(result.artifacts) >= 1 and len(harness.memory.queries) == 1,
        "model_calls": len(harness.llm.calls) == 1,
        "cost": len(harness.cost.records) == 1 and result.cost_usd is not None,
        "gate_outcome": record.status == "completed",
        "final_result": bool(result.recommendation.strip()),
    }
    missing = [name for name, ok in dimensions.items() if not ok]
    assert not missing, f"audit reconstruction incomplete (FAIL): {missing}"
