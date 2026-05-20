"""Pydantic v2 data models for Pi-Mono. Pure — no Praxis imports."""
from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


class ProviderName(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    FAKE = "fake"


class TokenClass(StrEnum):
    INPUT = "input"
    OUTPUT = "output"
    CACHE_READ = "cache_read"
    CACHE_WRITE = "cache_write"


class CacheRetention(StrEnum):
    NONE = "none"
    SHORT = "short"
    LONG = "long"


class Currency(StrEnum):
    USD = "USD"


class AggregationScope(StrEnum):
    REQUEST = "request"
    SESSION = "session"
    WORKFLOW = "workflow"
    AGENT = "agent"
    PROVIDER = "provider"
    ALL = "all"


def _reject_float(value: Any) -> Any:
    """Decimal fields reject bare float inputs.

    Blocks the `Decimal(float_value)` foot-gun at the model boundary per §6.4 T5.
    """
    if isinstance(value, float):
        raise ValueError(
            "float input not allowed for Decimal fields; pass str or Decimal"
        )
    return value


DecimalField = Annotated[Decimal, BeforeValidator(_reject_float)]


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=False)


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware (UTC)")
    if value.utcoffset() != value.utcoffset().__class__(0) and value.tzinfo != UTC:
        return value.astimezone(UTC)
    return value


class ModelPricing(_FrozenModel):
    provider: ProviderName
    model_id: str
    cache_retention_key: CacheRetention = CacheRetention.NONE
    currency: Currency = Currency.USD
    input_rate: DecimalField
    output_rate: DecimalField
    cache_read_rate: DecimalField
    cache_write_rate: DecimalField
    effective_from: datetime
    effective_until: datetime | None = None
    source_url: str | None = None
    snapshot_sha256: str | None = None

    @field_validator("effective_from", "effective_until")
    @classmethod
    def _tz_aware(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return None
        return _require_utc(v)

    @model_validator(mode="after")
    def _check(self) -> "ModelPricing":
        for name, rate in [
            ("input_rate", self.input_rate),
            ("output_rate", self.output_rate),
            ("cache_read_rate", self.cache_read_rate),
            ("cache_write_rate", self.cache_write_rate),
        ]:
            if rate < 0:
                raise ValueError(f"{name} must be >= 0")
        if self.effective_until is not None and self.effective_until <= self.effective_from:
            raise ValueError("effective_until must be > effective_from")
        return self


class LLMRequest(_FrozenModel):
    request_id: str
    provider: ProviderName
    model_id: str
    session_id: str | None = None
    workflow_id: str | None = None
    agent: str | None = None
    parent_request_id: str | None = None
    cache_retention: CacheRetention = CacheRetention.NONE
    tags: dict[str, str] = Field(default_factory=dict)
    started_at: datetime

    @field_validator("request_id", "parent_request_id")
    @classmethod
    def _ulid_shape(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not ULID_RE.match(v):
            raise ValueError(f"not a valid ULID: {v!r}")
        return v

    @field_validator("started_at")
    @classmethod
    def _tz_aware(cls, v: datetime) -> datetime:
        return _require_utc(v)

    @field_validator("tags")
    @classmethod
    def _tag_bounds(cls, v: dict[str, str]) -> dict[str, str]:
        if len(v) > 32:
            raise ValueError("tags may not exceed 32 keys")
        for k, val in v.items():
            if len(k) > 128 or len(val) > 128:
                raise ValueError("tag keys and values may not exceed 128 chars")
        return v


StopReason = Literal["stop", "length", "tool_use", "error", "aborted"]


class LLMResponse(_FrozenModel):
    request_id: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_read_tokens: int = Field(ge=0, default=0)
    cache_write_tokens: int = Field(ge=0, default=0)
    finished_at: datetime
    stop_reason: StopReason
    error_message: str | None = None

    @field_validator("request_id")
    @classmethod
    def _ulid_shape(cls, v: str) -> str:
        if not ULID_RE.match(v):
            raise ValueError(f"not a valid ULID: {v!r}")
        return v

    @field_validator("finished_at")
    @classmethod
    def _tz_aware(cls, v: datetime) -> datetime:
        return _require_utc(v)

    @model_validator(mode="after")
    def _check_error(self) -> "LLMResponse":
        if self.stop_reason in ("error", "aborted") and not self.error_message:
            raise ValueError("error_message required when stop_reason is error/aborted")
        return self


class CostAmount(_FrozenModel):
    input: DecimalField
    output: DecimalField
    cache_read: DecimalField
    cache_write: DecimalField
    total: DecimalField
    currency: Currency = Currency.USD

    @model_validator(mode="after")
    def _check(self) -> "CostAmount":
        for name, val in [
            ("input", self.input),
            ("output", self.output),
            ("cache_read", self.cache_read),
            ("cache_write", self.cache_write),
            ("total", self.total),
        ]:
            if val < 0:
                raise ValueError(f"{name} must be >= 0")
        expected = self.input + self.output + self.cache_read + self.cache_write
        if expected != self.total:
            raise ValueError(
                f"total mismatch: {self.total} != sum of components ({expected})"
            )
        return self


class CostRecord(_FrozenModel):
    record_id: str
    request_id: str
    provider: ProviderName
    model_id: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_read_tokens: int = Field(ge=0)
    cache_write_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cost: CostAmount
    pricing_effective_from: datetime
    pricing_snapshot_sha256: str
    session_id: str | None = None
    workflow_id: str | None = None
    agent: str | None = None
    parent_request_id: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    started_at: datetime
    finished_at: datetime
    latency_ms: int = Field(ge=0)
    stop_reason: StopReason
    error_message: str | None = None
    cache_retention: CacheRetention = CacheRetention.NONE
    created_at: datetime

    @field_validator("record_id", "request_id", "parent_request_id")
    @classmethod
    def _ulid_shape(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not ULID_RE.match(v):
            raise ValueError(f"not a valid ULID: {v!r}")
        return v

    @field_validator("started_at", "finished_at", "pricing_effective_from", "created_at")
    @classmethod
    def _tz_aware(cls, v: datetime) -> datetime:
        return _require_utc(v)

    @model_validator(mode="after")
    def _check(self) -> "CostRecord":
        expected = (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_write_tokens
        )
        if expected != self.total_tokens:
            raise ValueError(
                f"total_tokens mismatch: {self.total_tokens} != {expected}"
            )
        if self.finished_at < self.started_at:
            raise ValueError("finished_at must be >= started_at")
        return self


class TimeRange(_FrozenModel):
    start: datetime
    end: datetime

    @field_validator("start", "end")
    @classmethod
    def _tz_aware(cls, v: datetime) -> datetime:
        return _require_utc(v)

    @model_validator(mode="after")
    def _check(self) -> "TimeRange":
        if self.end <= self.start:
            raise ValueError("end must be > start")
        return self


class Filter(_FrozenModel):
    provider: ProviderName | None = None
    model_id: str | None = None
    session_id: str | None = None
    workflow_id: str | None = None
    agent: str | None = None
    time_range: TimeRange | None = None
    tag_match: dict[str, str] = Field(default_factory=dict)
    stop_reason: str | None = None


class CostSummary(_FrozenModel):
    scope: AggregationScope
    scope_id: str
    input_tokens: int = Field(ge=0, default=0)
    output_tokens: int = Field(ge=0, default=0)
    cache_read_tokens: int = Field(ge=0, default=0)
    cache_write_tokens: int = Field(ge=0, default=0)
    total_tokens: int = Field(ge=0, default=0)
    cost: CostAmount
    request_count: int = Field(ge=0, default=0)
    error_count: int = Field(ge=0, default=0)
    first_request_at: datetime | None = None
    last_request_at: datetime | None = None
    computed_at: datetime

    @field_validator("first_request_at", "last_request_at", "computed_at")
    @classmethod
    def _tz_aware(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return None
        return _require_utc(v)

    @model_validator(mode="after")
    def _check(self) -> "CostSummary":
        if self.error_count > self.request_count:
            raise ValueError("error_count must be <= request_count")
        expected = (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_write_tokens
        )
        if expected != self.total_tokens:
            raise ValueError("total_tokens mismatch")
        return self


class CostEvent(_FrozenModel):
    event_id: str
    event_type: Literal["record_created", "record_amended", "reconciliation_drift"]
    emitted_at: datetime
    record: CostRecord | None = None
    drift: "ReconciliationDrift | None" = None

    @field_validator("emitted_at")
    @classmethod
    def _tz_aware(cls, v: datetime) -> datetime:
        return _require_utc(v)

    @model_validator(mode="after")
    def _check(self) -> "CostEvent":
        payload_count = sum([self.record is not None, self.drift is not None])
        if payload_count != 1:
            raise ValueError("CostEvent must carry exactly one payload")
        if self.event_type == "reconciliation_drift" and self.drift is None:
            raise ValueError("reconciliation_drift event requires drift payload")
        if self.event_type in ("record_created", "record_amended") and self.record is None:
            raise ValueError(f"{self.event_type} event requires record payload")
        return self


class InvoiceLine(_FrozenModel):
    provider: ProviderName
    model_id: str
    period_start: datetime
    period_end: datetime
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_read_tokens: int = Field(ge=0, default=0)
    cache_write_tokens: int = Field(ge=0, default=0)
    amount: DecimalField
    currency: Currency = Currency.USD

    @field_validator("period_start", "period_end")
    @classmethod
    def _tz_aware(cls, v: datetime) -> datetime:
        return _require_utc(v)


class Invoice(_FrozenModel):
    invoice_id: str
    provider: ProviderName
    period_start: datetime
    period_end: datetime
    lines: list[InvoiceLine]
    total: DecimalField
    source_file: str | None = None
    source_sha256: str | None = None

    @field_validator("period_start", "period_end")
    @classmethod
    def _tz_aware(cls, v: datetime) -> datetime:
        return _require_utc(v)

    @model_validator(mode="after")
    def _check(self) -> "Invoice":
        if not self.lines:
            raise ValueError("invoice must have at least one line")
        if self.period_end <= self.period_start:
            raise ValueError("period_end must be > period_start")
        line_sum = sum((line.amount for line in self.lines), Decimal("0"))
        if line_sum != self.total:
            raise ValueError(f"invoice total {self.total} != sum of lines {line_sum}")
        return self


class ReconciliationDrift(_FrozenModel):
    provider: ProviderName
    model_id: str
    period_start: datetime
    period_end: datetime
    internal_tokens_by_class: dict[TokenClass, int]
    invoice_tokens_by_class: dict[TokenClass, int]
    token_delta_by_class: dict[TokenClass, int]
    internal_cost: DecimalField
    invoice_cost: DecimalField
    cost_delta: DecimalField
    drift_pct: DecimalField

    @field_validator("period_start", "period_end")
    @classmethod
    def _tz_aware(cls, v: datetime) -> datetime:
        return _require_utc(v)


class ReconciliationReport(_FrozenModel):
    invoice_id: str
    reconciled_at: datetime
    lines: list[ReconciliationDrift]
    total_internal: DecimalField
    total_invoice: DecimalField
    total_delta: DecimalField
    total_drift_pct: DecimalField
    status: Literal["clean", "within_tolerance", "drift_detected", "critical_drift"]

    @field_validator("reconciled_at")
    @classmethod
    def _tz_aware(cls, v: datetime) -> datetime:
        return _require_utc(v)


CostEvent.model_rebuild()
