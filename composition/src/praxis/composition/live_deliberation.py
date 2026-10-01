"""Live wiring for model-backed deliberation.

Connects the MAC ``IterationController.run_deliberation`` to real model calls
through the existing ``LiteLLMAdapter`` (LLMProxyPort) and prices each call
through the existing ``PiMonoNativeAdapter`` (CostMeterPort).

Credentials: the Anthropic key is read from the repo's gitignored ``.env`` with
``dotenv_values`` (it is NOT exported into the process environment) and handed
to the adapter explicitly. Provider is fixed to ``anthropic`` with no
``api_base`` override, so a call can never be routed to the EPAM DIAL gateway.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from praxis.adapters.litellm import LiteLLMAdapter
from praxis.adapters.pi_mono_native import PiMonoNativeAdapter
from praxis.kernel.mac.cycle import IterationController
from praxis.kernel.mac.deliberation import (
    CostFn,
    DeliberationRequest,
    DeliberationRoles,
    EvidenceSpan,
    ModelReply,
)
from praxis.ports.common import Message
from praxis.ports.cost_meter import BudgetScope, CostEvent, CostMeterPort, PricingTableMismatch
from praxis.ports.llm_proxy import LLMProxyPort, LLMRequest

DEFAULT_PROVIDER = "anthropic"
KEY_NAME = "ANTHROPIC_API_KEY"

Deliberator = Callable[[str, list[dict[str, str]]], Awaitable[dict[str, Any]]]


class MissingApiKeyError(RuntimeError):
    pass


def load_anthropic_key(env_path: Path) -> str:
    """Read the Anthropic key from ``env_path`` only (never from ``os.environ``)."""
    key = (dotenv_values(env_path).get(KEY_NAME) or "").strip()
    if not key:
        raise MissingApiKeyError(f"{KEY_NAME} not set in {env_path}")
    return key


class LiteLLMModelCaller:
    """``ModelCaller`` over an ``LLMProxyPort``; roles may be routed to different models."""

    def __init__(
        self,
        *,
        adapter: LLMProxyPort,
        default_model: str,
        role_models: Mapping[str, str] | None = None,
        provider: str = DEFAULT_PROVIDER,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> None:
        self._adapter = adapter
        self._default_model = default_model
        self._role_models = dict(role_models or {})
        self._provider = provider
        self._max_tokens = max_tokens
        self._temperature = temperature

    async def __call__(self, *, role: str, system: str, user: str) -> ModelReply:
        model = self._role_models.get(role, self._default_model)
        cid = uuid.uuid4().hex
        request = LLMRequest(
            schema_version=1,
            correlation_id=cid,
            idempotency_key=cid,
            provider=self._provider,
            model=model,
            messages=[
                Message(schema_version=1, correlation_id=cid, role="system", content=system),
                Message(schema_version=1, correlation_id=cid, role="user", content=user),
            ],
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            compression_hint="none",
        )
        response = await asyncio.to_thread(self._adapter.call, request)
        return ModelReply(
            content=response.content,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            model=model,
            provider=self._provider,
            response_id=response.raw_response_id,
            stop_reason=response.finish_reason,
        )


def make_price_fn(meter: CostMeterPort, *, scope_id: str = "deliberation") -> CostFn:
    """Price a reply through the cost-meter port; unknown models price to ``None``."""

    def price(reply: ModelReply) -> Decimal | None:
        key = uuid.uuid4().hex
        event = CostEvent(
            schema_version=1,
            correlation_id=key,
            idempotency_key=key,
            provider=reply.provider,
            model=reply.model,
            input_tokens=reply.input_tokens,
            output_tokens=reply.output_tokens,
            occurred_at=datetime.now(timezone.utc),
            scope=BudgetScope(
                schema_version=1,
                correlation_id=key,
                scope_kind="session",
                scope_id=scope_id,
            ),
        )
        try:
            return meter.record(event).cost_usd
        except PricingTableMismatch:
            return None

    return price


def build_deliberator(
    *, caller: LiteLLMModelCaller, price: CostFn | None, receipts_dir: Path
) -> Deliberator:
    """Return ``async (question, evidence) -> {"receipt": ..., "receipt_path": ...}``.

    A fresh ``IterationController`` is built per call (one controller, one run).
    """

    async def deliberate(question: str, evidence: list[dict[str, str]]) -> dict[str, Any]:
        request = DeliberationRequest(
            question=question,
            evidence=tuple(EvidenceSpan(**e) for e in evidence),
        )
        receipt = await IterationController().run_deliberation(
            request, DeliberationRoles(call=caller, price=price)
        )
        receipts_dir.mkdir(parents=True, exist_ok=True)
        path = receipts_dir / f"receipt-{receipt.receipt_id}.json"
        path.write_text(receipt.model_dump_json(indent=2) + "\n", encoding="utf-8")
        return {"receipt": receipt.model_dump(mode="json"), "receipt_path": str(path)}

    return deliberate


DEFAULT_MODEL = "claude-haiku-4-5"
# The Anthropic API rejects `temperature` for these models (observed 2026-10-01).
OMIT_TEMPERATURE_MODELS = frozenset({"claude-sonnet-5-5"})


def build_live_deliberator(
    *,
    env_path: Path,
    receipts_dir: Path,
    producer_model: str = DEFAULT_MODEL,
    reviewer_model: str = DEFAULT_MODEL,
    synthesizer_model: str = DEFAULT_MODEL,
) -> Deliberator:
    """Anthropic via LiteLLM, priced by the in-tree cost meter. Raises
    :class:`MissingApiKeyError` if the key is absent from ``env_path``."""
    adapter = LiteLLMAdapter(
        api_keys={DEFAULT_PROVIDER: load_anthropic_key(env_path)},
        omit_temperature_models=OMIT_TEMPERATURE_MODELS,
    )
    caller = LiteLLMModelCaller(
        adapter=adapter,
        default_model=producer_model,
        role_models={
            "reviewer_counter": reviewer_model,
            "reviewer_critique": reviewer_model,
            "synthesizer": synthesizer_model,
        },
    )
    return build_deliberator(
        caller=caller, price=make_price_fn(PiMonoNativeAdapter()), receipts_dir=receipts_dir
    )
