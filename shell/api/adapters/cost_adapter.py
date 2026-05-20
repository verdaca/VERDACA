"""ShellCostAdapter — arch §5.3.

Adapts MAC's internal cost events to Pi-Mono's canonical contracts.

C-2 resolution: mints a ULID for Pi-Mono, stashes MAC's
"mac:{cycle_id}:{phase}:{seq}" in tags["mac_request_id"].

C-3 resolution: strips usd_cost from MAC's LLMResponse before
forwarding to Pi-Mono. Pi-Mono computes cost from its pricing
snapshot — that's the contract.

Binding anchors:
  - shell/architecture.md §5.3 Pi-Mono Integration (C-2 / C-3 Adapter)
  - shell/architecture.md §5.4 Session Cost Tracking
  - mac/architecture.md §10.1 Pi-Mono Integration (contract source)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

import ulid


# Pi-Mono canonical ULID pattern: exactly 26 chars from Crockford base-32
ULID_REGEX = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


@dataclass(frozen=True)
class PiMonoLLMRequest:
    """Shape-compatible with Pi-Mono's LLMRequest contract.

    Fields match the canonical Pi-Mono contract — NOT MAC's local
    LLMRequest which uses a mac: prefix request_id.
    """

    request_id: str  # ULID
    provider: str
    model_id: str
    session_id: str
    workflow_id: str
    agent: str = "mac"
    tags: dict[str, str] = field(default_factory=dict)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class PiMonoLLMResponse:
    """Shape-compatible with Pi-Mono's LLMResponse contract.

    C-3: NO usd_cost field. Pi-Mono computes cost from its pricing
    snapshot. Only integer token counts are sent.
    """

    request_id: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    finished_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stop_reason: str = "stop"


@dataclass(frozen=True)
class CostRecord:
    """Return type from track_cost — the Pi-Mono cost record."""

    request_id: str
    session_id: str
    cost_usd: float = 0.0


@runtime_checkable
class CostTrackerProtocol(Protocol):
    """Pi-Mono CostTracker surface used by ShellCostAdapter."""

    async def track_cost(
        self, request: PiMonoLLMRequest, response: PiMonoLLMResponse
    ) -> CostRecord: ...


class ShellCostAdapter:
    """Adapts MAC's internal cost events to Pi-Mono's canonical contracts.

    C-2 resolution: mints a ULID for Pi-Mono, stashes MAC's
    "mac:{cycle_id}:{phase}:{seq}" in tags["mac_request_id"].

    C-3 resolution: strips usd_cost from MAC's LLMResponse before
    forwarding to Pi-Mono. Pi-Mono computes cost from its pricing
    snapshot — that's the contract.
    """

    def __init__(self, tracker: CostTrackerProtocol) -> None:
        self._tracker = tracker

    async def track_mac_call(
        self,
        *,
        mac_request_id: str,
        provider: str,
        model_id: str,
        session_id: str,
        workflow_id: str,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> CostRecord:
        now = datetime.now(timezone.utc)

        # C-2: mint a ULID for Pi-Mono, stash MAC ID in tags
        pi_mono_request_id = str(ulid.ULID())

        request = PiMonoLLMRequest(
            request_id=pi_mono_request_id,
            provider=provider,
            model_id=model_id,
            session_id=session_id,
            workflow_id=workflow_id,
            agent="mac",
            tags={"mac_request_id": mac_request_id},
            started_at=started_at or now,
        )

        # C-3: LLMResponse with token counts ONLY — no usd_cost
        response = PiMonoLLMResponse(
            request_id=pi_mono_request_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            finished_at=finished_at or now,
            stop_reason="stop",
        )

        return await self._tracker.track_cost(request, response)

    async def track_session(
        self, session_id: str, cost_events: list[dict[str, Any]]
    ) -> float:
        """Track all cost events for a session, return total cost."""
        total = 0.0
        for event in cost_events:
            record = await self.track_mac_call(
                mac_request_id=event.get("mac_request_id", "unknown"),
                provider=event.get("provider", "anthropic"),
                model_id=event.get("model_id", "unknown"),
                session_id=session_id,
                workflow_id=event.get("workflow_id", ""),
                input_tokens=event.get("input_tokens", 0),
                output_tokens=event.get("output_tokens", 0),
                cache_read_tokens=event.get("cache_read_tokens", 0),
                cache_write_tokens=event.get("cache_write_tokens", 0),
            )
            total += record.cost_usd
        return total
