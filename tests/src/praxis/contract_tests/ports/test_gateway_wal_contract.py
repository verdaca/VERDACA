"""Stage 11 gateway WAL contract tests."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from decimal import Decimal

from praxis.contract_tests.ports.gateway_contract_fakes import (
    make_ctx,
    make_gateway_harness,
    make_intent,
)
from praxis.kernel.gateway import GatewayWalConfig, GatewayWalStore
from praxis.ports.gateway_dto import AnalysisResult, ArtifactRef, SessionHandle


def test_M_T_GW_WAL_RECOVERS_FROM_ORPHANED_IN_PROGRESS_01_recovers_attempt(tmp_path) -> None:
    # Binding: orphaned in_progress WAL rows recover to one completed result on replay.
    # This does not cover mid-execute process death after LLM cost is burned; that risk
    # is routed to STAGE-11-DEBT-WAL-MID-EXEC-CRASH-01.
    child_script = tmp_path / "begin_attempt_then_wait.py"
    wal_path = tmp_path / "gateway-idempotency.sqlite3"
    child_script.write_text(
        textwrap.dedent(
            """
            import os
            import sys
            import time
            from pathlib import Path

            from praxis.kernel.gateway import GatewayWalConfig, GatewayWalStore

            store = GatewayWalStore(GatewayWalConfig(database_path=Path(sys.argv[1])))
            store.begin_attempt("idem-crash")
            print("ready", flush=True)
            time.sleep(60)
            os._exit(0)
            """
        ),
        encoding="utf-8",
    )

    proc = subprocess.Popen(
        [sys.executable, str(child_script), str(wal_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout is not None
    assert proc.stdout.readline().strip() == "ready"
    proc.kill()
    proc.wait(timeout=30)

    harness = make_gateway_harness(tmp_path)
    intent = make_intent(idempotency_key="idem-crash")
    first = harness.gateway.execute(intent, make_ctx(request_id="req-crash-1"))

    replay_harness = make_gateway_harness(tmp_path)
    replay = replay_harness.gateway.execute(intent, make_ctx(request_id="req-crash-2"))

    assert replay == first
    assert replay_harness.session_index.index_calls == 0
    assert len(replay_harness.llm.calls) == 0
    assert len(harness.session_index.list_sessions()) == 1


def test_gateway_wal_store_closes_sqlite_connections_after_repeated_access(tmp_path) -> None:
    wal_path = tmp_path / "gateway-idempotency.sqlite3"

    for index in range(100):
        store = GatewayWalStore(GatewayWalConfig(database_path=wal_path))
        idempotency_key = f"idem-{index}"
        store.begin_attempt(idempotency_key)
        store.complete_attempt(idempotency_key, _wal_result(f"session-{index}"))
        assert store.get_result(idempotency_key) is not None

    for suffix in ("", "-wal", "-shm"):
        wal_path.with_name(f"{wal_path.name}{suffix}").unlink(missing_ok=True)


def _wal_result(session_id: str) -> AnalysisResult:
    return AnalysisResult(
        session=SessionHandle(
            session_id=session_id,
            status="completed",
            source_uri=f"gateway://workspaces/workspace-1/sessions/{session_id}",
        ),
        recommendation="Use the enterprise buyer path.",
        cited_tradeoffs=("cost_meter_recorded",),
        artifacts=(
            ArtifactRef(
                artifact_id=f"{session_id}-summary",
                session_id=session_id,
                kind="summary",
                uri=f"session://{session_id}/artifacts/{session_id}-summary",
                title="Gateway analysis summary",
            ),
        ),
        cost_usd=Decimal("0.01"),
    )
