"""Stage 11 Phase A GatewayPort implementation contract tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from praxis.contract_tests.ports.gateway_contract_fakes import (
    make_ctx,
    make_gateway_harness,
    make_intent,
)
from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_errors import GatewayCtxError


def test_M_T_GW_PORT_HANDSHAKE_01_gateway_service_satisfies_protocol(tmp_path) -> None:
    from praxis.kernel.gateway import VerdacaGatewayService

    harness = make_gateway_harness(tmp_path)

    assert isinstance(harness.gateway, GatewayPort)
    assert VerdacaGatewayService.API_VERSION == GatewayPort.API_VERSION


def test_M_T_GATEWAY_EXEC_HAPPY_01_returns_analysis_result(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path)
    result = harness.gateway.execute(make_intent(), make_ctx())

    assert result.session.status == "completed"
    assert result.recommendation == "Use the enterprise buyer path."
    assert result.artifacts[0].kind == "summary"


def test_M_T_GATEWAY_EXEC_IDEMPOTENCY_01_gateway_owns_replay(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path)
    intent = make_intent(idempotency_key="idem-replay")
    ctx = make_ctx()

    first = harness.gateway.execute(intent, ctx)
    second = harness.gateway.execute(intent, ctx)

    assert second == first
    assert len(harness.llm.calls) == 1
    assert harness.session_index.index_calls == 1


def test_M_T_GATEWAY_EXEC_ERROR_01_maps_downstream_failures(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path, fail_llm=True)

    with pytest.raises(GatewayCtxError) as exc_info:
        harness.gateway.execute(make_intent(), make_ctx())

    assert exc_info.value.context_field == "execute:RuntimeError"
    assert exc_info.value.port_name == "gateway"


def test_M_T_GATEWAY_EXEC_COST_01_records_llm_tokens_before_result(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path)

    result = harness.gateway.execute(make_intent(), make_ctx())

    assert len(harness.cost.records) == 1
    assert harness.cost.records[0].input_tokens == 11
    assert harness.cost.records[0].output_tokens == 7
    assert result.cost_usd == Decimal("0.0123")
