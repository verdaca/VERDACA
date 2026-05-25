"""Stage 11 gateway composition contract tests."""

from __future__ import annotations

from praxis.contract_tests.ports.gateway_contract_fakes import (
    CountingSqliteSessionIndex,
    make_ctx,
    make_gateway_harness,
    make_intent,
)


def test_M_T_GATEWAY_COMPOSE_LLM_01_calls_llm_proxy_port(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path)

    harness.gateway.execute(make_intent(), make_ctx())

    assert len(harness.llm.calls) == 1
    assert harness.llm.calls[0].provider == "azure"
    assert harness.llm.calls[0].model == "gpt-4o"


def test_M_T_GATEWAY_COMPOSE_MEMORY_01_queries_and_stores_via_memory_port(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path)

    harness.gateway.execute(make_intent(), make_ctx())

    assert len(harness.memory.queries) == 1
    assert len(harness.memory.stores) == 1


def test_M_T_GATEWAY_COMPOSE_COMPACTION_01_delegates_payload_shaping(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path)

    harness.gateway.execute(make_intent(), make_ctx())

    assert len(harness.compaction.compactions) == 1
    assert harness.compaction.compactions[0].payload.payload_kind == "gateway_prompt"


def test_M_T_GW_SESSIONINDEX_BIND_01_uses_real_stage10_session_index(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path)

    result = harness.gateway.execute(make_intent(), make_ctx())

    assert isinstance(harness.session_index, CountingSqliteSessionIndex)
    assert harness.session_index.index_calls == 1
    assert harness.session_index.get_session(result.session.session_id) is not None
