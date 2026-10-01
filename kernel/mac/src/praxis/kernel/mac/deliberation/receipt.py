"""Deliberation receipt: the JSON artefact a run leaves behind.

``content_sha256`` is a plain SHA-256 over the canonical JSON of every other
field. It makes edits detectable; it is NOT a signature and proves nothing
about who produced the receipt.

Schema history: ``/1`` had no ``stop_reason`` per call and no
``truncated_calls``. Verify a stored receipt with :func:`verify_receipt_json`,
which hashes the JSON exactly as written, so ``/1`` files still verify.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict

SCHEMA_VERSION = "verdaca.receipt/2"


class Outcome(str, Enum):
    ANSWER = "answer"
    CLARIFY = "clarify"
    ABSTAIN = "abstain"
    ESCALATE = "escalate"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class EvidenceSpan(_Frozen):
    id: str
    source: str
    text: str


class DeliberationRequest(_Frozen):
    question: str
    evidence: tuple[EvidenceSpan, ...]


class Critique(_Frozen):
    counterargument: str
    blocking: bool
    issues: tuple[str, ...]
    summary: str


class FinalAnswer(_Frozen):
    outcome: Outcome
    answer: str
    cited_evidence_ids: tuple[str, ...]
    rationale: str


class Round(_Frozen):
    draft: str
    critique: Critique


class CallRecord(_Frozen):
    seq: int
    role: str
    cycle: str
    provider: str
    model: str
    response_id: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal | None
    cost_status: Literal["priced", "unpriced"]
    latency_seconds: float
    prompt_sha256: str
    stop_reason: str | None = None


class Receipt(_Frozen):
    schema_version: str = SCHEMA_VERSION
    receipt_id: str
    created_at: datetime
    question: str
    evidence: tuple[EvidenceSpan, ...]
    draft: str | None
    critique: Critique | None
    superseded_rounds: tuple[Round, ...]
    final: FinalAnswer | None
    diff: str
    outcome: Outcome
    terminal_reason: str | None
    terminal_detail: str | None = None
    backtrack_count: int
    state_log: list[str]
    calls: tuple[CallRecord, ...]
    truncated_calls: tuple[int, ...] | None = None
    """``seq`` of every call that stopped on its max_tokens limit. ``None`` means not
    recorded (schema ``/1``), which is different from ``()`` (none truncated)."""
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: Decimal | None
    content_sha256: str = ""


def _hash_body(body: dict) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_receipt_hash(receipt: Receipt) -> str:
    return _hash_body(receipt.model_dump(mode="json", exclude={"content_sha256"}))


def verify_receipt_hash(receipt: Receipt) -> bool:
    return receipt.content_sha256 == compute_receipt_hash(receipt)


def verify_receipt_json(text: str) -> bool:
    """Verify a stored receipt as written (any schema version)."""
    body = json.loads(text)
    claimed = body.pop("content_sha256", None)
    return claimed == _hash_body(body)
