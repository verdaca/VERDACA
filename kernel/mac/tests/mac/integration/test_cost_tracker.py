"""Pi-Mono CostTracker integration tests — mac/test-strategy.md v0.3 §6.1.

Covers ``MAC-T-INT-COSTTRACKER-01/02/03``. The step-3 implementation uses
:class:`FakeCostTracker` (arch §10.1 Protocol-compatible) rather than the
real Pi-Mono installation; the contract surface tested here is exactly
the ``track_cost(LLMRequest, LLMResponse)`` call signature and the
canonical ``request_id`` format from arch §10.1 line 1522. Step 6 or
Stage 7 POV Harness rebinds to the real
``praxis.kernel.cost.tracker.CostTracker`` at construction time.

Anchors:
  - mac/architecture.md §10.1 Pi-Mono Integration
  - pi-mono/architecture.md §4.2 CostTracker hot path
  - runtime/test-strategy.md §7.2 F-13.C1 xmin identity (inherited semantic)
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.integrations.pi_mono import (
    FakeCostTracker,
    LLMRequest,
    LLMResponse,
    MacCostHook,
)


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_int_costtracker_01_events_outbox_write_per_llm_call() -> None:
    """MAC-T-INT-COSTTRACKER-01 — every LLM call produces one CostEvent write.

    The :class:`MacCostHook` calls ``CostTracker.track_cost`` exactly once
    per LLM call. The FakeCostTracker captures the call as a
    ``(LLMRequest, LLMResponse)`` tuple in :attr:`events`. After N calls,
    ``len(events) == N``.

    This is the ``events_outbox write on every LLM call`` property —
    arch §10.1 guarantees atomicity at the Pi-Mono side (cost_records +
    events_outbox in the same transaction). MAC's job is to call
    ``track_cost`` exactly once per LLM call; the outbox write is
    downstream.
    """
    tracker = FakeCostTracker()
    hook = MacCostHook(cost_tracker=tracker)

    # Emit 3 distinct cost events.
    for phase, seq, cost in (
        ("produce", 0, 0.45),
        ("review", 0, 0.30),
        ("review", 1, 0.25),
    ):
        await hook.emit_cycle_cost(
            cycle_id="01HX000000000000000000000A",
            cycle_phase=phase,
            call_seq=seq,
            model="claude-opus-4-6",
            prompt_tokens=500,
            completion_tokens=250,
            usd_cost=cost,
        )

    assert len(tracker.events) == 3
    # Each captured event is a (LLMRequest, LLMResponse) pair with matching request_id.
    for req, resp in tracker.events:
        assert isinstance(req, LLMRequest)
        assert isinstance(resp, LLMResponse)
        assert req.request_id == resp.request_id


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_int_costtracker_02_cost_aggregation_matches() -> None:
    """MAC-T-INT-COSTTRACKER-02 — ``CostTracker.total_cost`` = Σ per-call costs.

    After N emitted events, the tracker's total USD cost equals the sum
    of individual event costs. Trivial arithmetic but load-bearing:
    Stage 5.6 pre-sales reports aggregate cost across a benchmark run
    via exactly this sum.
    """
    tracker = FakeCostTracker()
    hook = MacCostHook(cost_tracker=tracker)

    costs = [0.10, 0.25, 0.15, 0.30, 0.20]
    for i, c in enumerate(costs):
        await hook.emit_cycle_cost(
            cycle_id="01HX000000000000000000000A",
            cycle_phase="produce",
            call_seq=i,
            model="claude-opus-4-6",
            prompt_tokens=100,
            completion_tokens=50,
            usd_cost=c,
        )

    assert tracker.total_cost_usd == pytest.approx(sum(costs))
    assert tracker.total_tokens == len(costs) * (100 + 50)


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_int_costtracker_03_request_id_format_is_xmin_compatible() -> None:
    """MAC-T-INT-COSTTRACKER-03 — request_id format preserves downstream joins.

    The canonical format ``f"mac:{cycle_id}:{cycle_phase}:{call_seq}"`` per
    arch §10.1 line 1522 makes every MAC-emitted request_id a prefix-join
    candidate for downstream cost-report filters. This test verifies the
    format is applied uniformly across phases and sequence numbers and
    that the MAC namespace prefix (``mac:``) is always first.

    **xmin identity note:** arch §10.1 inherits the F-13.C1 xmin identity
    guarantee from Runtime's Path A outbox (runtime/test-strategy.md §7.2).
    The full identity proof requires a real Postgres outbox with xmin
    inspection — deferred to step 6 / Stage 7. Step 3 asserts only the
    request_id format contract; full xmin verification is out of scope
    for the Protocol-based integration layer.
    """
    tracker = FakeCostTracker()
    hook = MacCostHook(cost_tracker=tracker)

    for phase in ("produce", "review", "publish"):
        for seq in range(3):
            await hook.emit_cycle_cost(
                cycle_id="01HXABCDEF0123456789ABCDEF",
                cycle_phase=phase,
                call_seq=seq,
                model="claude-opus-4-6",
                prompt_tokens=100,
                completion_tokens=50,
                usd_cost=0.01,
            )

    # Every request_id starts with "mac:".
    for req, _ in tracker.events:
        assert req.request_id.startswith("mac:")
        # Format: "mac:{cycle_id}:{phase}:{seq}"
        parts = req.request_id.split(":")
        assert len(parts) == 4
        assert parts[0] == "mac"
        assert parts[1] == "01HXABCDEF0123456789ABCDEF"
        assert parts[2] in {"produce", "review", "publish"}
        assert parts[3].isdigit()

    # All request_ids are unique (prefix-join de-duplication contract).
    request_ids = [req.request_id for req, _ in tracker.events]
    assert len(set(request_ids)) == len(request_ids)
