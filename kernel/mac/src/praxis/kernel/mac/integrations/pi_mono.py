"""Pi-Mono cost-tracking integration — arch §10.1.

The MAC emits a :class:`CostEvent` per LLM call via
``CostTracker.track_cost(LLMRequest, LLMResponse)``. Budget enforcement is
Runtime's responsibility, NOT Pi-Mono's (per arch §10.1 line 22 binding
correction + Runtime §4.3 ResourceBudget).

The :class:`CostTracker` type is declared as a Protocol here so MAC tests
can pass :class:`FakeCostTracker` without installing the real Pi-Mono
package. Production wiring at step 6 or Stage 7 substitutes the real
``praxis.kernel.cost.tracker.CostTracker`` at construction time.

Binding anchors:
  - mac/architecture.md §10.1 Pi-Mono Integration
  - pi-mono/architecture.md §4.2 CostTracker hot path
  - mac/test-strategy.md v0.3 §6.1 MAC-T-INT-COSTTRACKER-01..03
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class LLMRequest:
    """Shape-compatible with ``praxis.kernel.cost.models.LLMRequest`` (arch §10.1).

    The field set is intentionally minimal — only what the MAC hot-path
    populates at every emit. Step 6 rebinds to the Pi-Mono canonical type.
    """

    request_id: str
    """``f"mac:{cycle_id}:{cycle_phase}:{call_seq}"`` per arch §10.1 line 1522."""

    model: str
    prompt_tokens: int = 0


@dataclass(frozen=True)
class LLMResponse:
    """Shape-compatible with ``praxis.kernel.cost.models.LLMResponse`` (arch §10.1)."""

    request_id: str
    completion_tokens: int = 0
    usd_cost: float = 0.0


@runtime_checkable
class CostTrackerProtocol(Protocol):
    """Shape of the Pi-Mono :class:`CostTracker` that MAC consumes.

    The real CostTracker (``praxis.kernel.cost.tracker.CostTracker``) has
    many more methods; MAC only uses :meth:`track_cost`. This Protocol
    pins exactly that surface.
    """

    async def track_cost(
        self, request: LLMRequest, response: LLMResponse
    ) -> None: ...


@dataclass
class FakeCostTracker:
    """In-memory :class:`CostTrackerProtocol` for tests.

    Captures every ``track_cost`` call as a ``(request, response)`` tuple
    so assertions can verify the xmin-outbox hot-path semantics
    (``MAC-T-INT-COSTTRACKER-03``) and the per-cycle emission count
    (``MAC-T-INT-COSTTRACKER-01/02``).
    """

    events: list[tuple[LLMRequest, LLMResponse]] = field(default_factory=list)

    async def track_cost(
        self, request: LLMRequest, response: LLMResponse
    ) -> None:
        self.events.append((request, response))

    @property
    def total_cost_usd(self) -> float:
        return sum(resp.usd_cost for _, resp in self.events)

    @property
    def total_tokens(self) -> int:
        return sum(
            req.prompt_tokens + resp.completion_tokens for req, resp in self.events
        )

    def reset(self) -> None:
        self.events.clear()


class MacCostHook:
    """Wraps every MAC LLM call to emit a :class:`CostEvent` via
    ``CostTracker.track_cost``.

    Arch §10.1 specifies that ``track_cost`` emits a ``CostRecord`` to
    ``cost_records`` AND a ``CostEvent`` to ``events_outbox`` in the same
    transaction — both succeed or both roll back. That atomicity is
    Pi-Mono's guarantee, not MAC's. MAC's job is to call ``track_cost``
    exactly once per LLM call with a correctly-formed
    :class:`LLMRequest`/:class:`LLMResponse` pair.

    The ``request_id`` construction is the one place where MAC enforces
    cross-stage traceability per arch §10.1 line 1522:
    ``f"mac:{cycle_id}:{cycle_phase}:{call_seq}"``.
    """

    def __init__(self, cost_tracker: CostTrackerProtocol) -> None:
        self._cost_tracker = cost_tracker

    async def emit_cycle_cost(
        self,
        *,
        cycle_id: str,
        cycle_phase: str,
        call_seq: int,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        usd_cost: float,
    ) -> None:
        """Call :meth:`CostTrackerProtocol.track_cost` once for the given
        cycle + phase + call sequence. The caller owns the ``call_seq``
        counter.
        """
        request_id = self._format_request_id(cycle_id, cycle_phase, call_seq)
        request = LLMRequest(
            request_id=request_id, model=model, prompt_tokens=prompt_tokens
        )
        response = LLMResponse(
            request_id=request_id,
            completion_tokens=completion_tokens,
            usd_cost=usd_cost,
        )
        await self._cost_tracker.track_cost(request=request, response=response)

    @staticmethod
    def _format_request_id(cycle_id: str, cycle_phase: str, call_seq: int) -> str:
        """Per arch §10.1 line 1522: request IDs are
        ``f"mac:{cycle_id}:{cycle_phase}:{call_seq}"``. This format is a
        downstream join key — downstream cost reports filter by MAC cycle
        via a prefix match on this string."""
        return f"mac:{cycle_id}:{cycle_phase}:{call_seq}"


__all__ = (
    "CostTrackerProtocol",
    "FakeCostTracker",
    "LLMRequest",
    "LLMResponse",
    "MacCostHook",
)
