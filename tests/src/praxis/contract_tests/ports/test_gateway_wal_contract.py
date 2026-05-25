"""Stage 11 gateway WAL contract tests."""

from __future__ import annotations

import subprocess
import sys
import textwrap

from praxis.contract_tests.ports.gateway_contract_fakes import (
    make_ctx,
    make_gateway_harness,
    make_intent,
)


def test_M_T_GW_WAL_CRASH_REPLAY_01_recovers_abandoned_attempt(tmp_path) -> None:
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
