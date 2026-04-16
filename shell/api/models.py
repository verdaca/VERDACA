"""Pydantic request/response models — arch §3.2.

Binding anchors:
  - shell/architecture.md §3.2 Core Data Models
  - shell/architecture.md §3.3 Error Response Format
  - shell/architecture.md §7.2 DL-15 rendering_mode routing
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class SessionDepth(str, Enum):
    QUICK = "quick"
    DEEP = "deep"


class SessionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RenderingMode(str, Enum):
    """DL-15 resolution: expose all 3 modes to user."""

    POSITION_TO_HOLD = "position_to_hold"
    DECISION_FRAMEWORK = "decision_framework"
    FIRM_VOICE = "firm_voice"


class CreateSessionRequest(BaseModel):
    question: str = Field(..., min_length=20, max_length=10000)
    context: str | None = Field(None, max_length=5000)
    depth: SessionDepth = SessionDepth.DEEP
    rendering_mode: RenderingMode = RenderingMode.POSITION_TO_HOLD


class SessionResponse(BaseModel):
    id: str
    workspace_id: str
    status: SessionStatus
    depth: SessionDepth
    rendering_mode: RenderingMode
    question: str
    context: str | None
    cost_usd: Decimal | None
    started_at: datetime
    completed_at: datetime | None
    result_url: str | None

    model_config = {"from_attributes": True}


class ErrorDetail(BaseModel):
    """Arch §3.3 error response shape."""

    code: str
    message: str
    detail: str | None = None
    session_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class UsageResponse(BaseModel):
    total_sessions: int
    total_cost_usd: Decimal
    sessions_this_month: int


class PublicStatsResponse(BaseModel):
    """Arch §8.1 public dashboard data."""

    total_sessions: int
    avg_cost_usd: float
    avg_duration_seconds: float
    sessions_today: int
    insufficient_data: bool = False
