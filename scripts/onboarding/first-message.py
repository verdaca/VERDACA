#!/usr/bin/env python
"""Onboarding step 4 — drive one synthetic message through the auth-first spine.

Composes the runtime gateway (``compose_auth_quartet`` → ``build_runtime_gateway``)
and executes one synthetic request, asserting the full traversal order:
bearer → ``OidcPolicy.authenticate`` → nonce → budget gate → execute → memory →
LLM. Prints round-trip time and cost. The model output, cost, memory and
virtual-key budget are Tier-1 demo stubs on this path (see the demo-gap ledger
in ``build_runtime_gateway``); the auth-first spine runs for real.

Real onboarding supplies a live OIDC token in ``VERDACA_SMOKE_BEARER``. The
test injects a gateway composed against a local OIDC stub.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal

from praxis.adapters.mcp_server.composition import (
    build_runtime_gateway,
    compose_auth_quartet,
)
from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_dto import (
    AnalysisResult,
    AuthClaims,
    CallerKind,
    ChannelContext,
    ChannelKind,
    StartAnalysisRequest,
)


@dataclass(frozen=True)
class SmokeOutcome:
    result: AnalysisResult
    elapsed_ms: float
    cost_usd: Decimal | None


def build_request(
    *,
    question: str,
    user_id: str,
    workspace_id: str,
    bearer_token: str,
) -> tuple[StartAnalysisRequest, ChannelContext]:
    """Build a synthetic intent + channel context carrying the bearer."""
    activity_id = str(uuid.uuid4())
    intent = StartAnalysisRequest(
        question=question,
        requester_user_id=user_id,
        workspace_id=workspace_id,
        idempotency_key=activity_id,
    )
    ctx = ChannelContext(
        caller_id=user_id,
        caller_kind=CallerKind.HUMAN,
        auth_claims=AuthClaims(_claims={}),
        channel=ChannelKind.TEAMS,
        channel_session_id=f"smoke-{activity_id}",
        request_id=str(uuid.uuid4()),
        trace_id=activity_id,
        rate_limit_token=bearer_token,
    )
    return intent, ctx


def run_first_message(
    gateway: GatewayPort,
    intent: StartAnalysisRequest,
    ctx: ChannelContext,
) -> SmokeOutcome:
    """Execute one request through the auth-first spine and time it."""
    start = time.perf_counter()
    result = gateway.execute(intent, ctx)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return SmokeOutcome(result=result, elapsed_ms=elapsed_ms, cost_usd=result.cost_usd)


def compose_from_env() -> GatewayPort:
    """Build the runtime gateway from env config (real OIDC discovery)."""
    jwt_verifier, oidc_policy = asyncio.run(compose_auth_quartet())
    gateway, _policy = build_runtime_gateway(
        jwt_verifier=jwt_verifier, oidc_policy=oidc_policy
    )
    return gateway


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    bearer = os.environ.get("VERDACA_SMOKE_BEARER")
    if not bearer:
        print("ERROR: VERDACA_SMOKE_BEARER (an OIDC token for the smoke caller) is required")
        return 1
    user_id = os.environ.get("VERDACA_SMOKE_USER_ID", "user-1")
    workspace_id = os.environ.get("VERDACA_SMOKE_WORKSPACE_ID", "tenant-1")
    question = args[0] if args else "Which buyer path should we evaluate first?"

    gateway = compose_from_env()
    intent, ctx = build_request(
        question=question,
        user_id=user_id,
        workspace_id=workspace_id,
        bearer_token=bearer,
    )
    outcome = run_first_message(gateway, intent, ctx)
    print(
        f"first-message: {outcome.result.recommendation[:80]!r} "
        f"in {outcome.elapsed_ms:.1f}ms cost={outcome.cost_usd}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
