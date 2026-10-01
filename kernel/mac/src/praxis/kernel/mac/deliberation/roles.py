"""Model-call seam for the deliberation roles.

The MAC kernel does not import any provider SDK. Callers inject a
:class:`ModelCaller` (LiteLLM-backed in composition, scripted in tests) and an
optional :class:`CostFn` that turns a reply's token counts into USD.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

# Roles the controller invokes, in order. The caller may route each to a
# different model (e.g. reviewer on another vendor than producer).
ROLE_PRODUCER = "producer"
ROLE_REVIEWER_COUNTER = "reviewer_counter"
ROLE_REVIEWER_CRITIQUE = "reviewer_critique"
ROLE_SYNTHESIZER = "synthesizer"


@dataclass(frozen=True)
class ModelReply:
    content: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: str
    response_id: str


class ModelCaller(Protocol):
    async def __call__(self, *, role: str, system: str, user: str) -> ModelReply: ...


class CostFn(Protocol):
    def __call__(self, reply: ModelReply) -> Decimal | None:
        """USD for this reply, or None when the model has no known price."""


@dataclass(frozen=True)
class DeliberationRoles:
    call: ModelCaller
    price: CostFn | None = None
