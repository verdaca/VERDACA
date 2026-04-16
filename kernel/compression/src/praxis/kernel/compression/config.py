"""Compression layer configuration — single source of truth for all thresholds and flags."""
from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TONLConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    tokenizer_pinning: Literal["strict", "lenient"] = "strict"
    optimizer_strategies: list[str] = Field(
        default_factory=lambda: ["tabular", "delta", "column_reorder"]
    )
    max_depth: int = 50
    max_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    max_string_len: int = 1 * 1024 * 1024   # 1 MB


class ForgeConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    token_threshold: int = 140_000        # ~70% of 200K context
    turn_threshold: int = 30
    message_threshold: int = 60
    retention_window: int = 6
    eviction_window: Decimal = Decimal("0.2")
    on_turn_end: bool = True


class CavemanGateConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    min_tokens: int = 500
    break_even_reads: int = 3
    max_calibration_age_seconds: int = 7 * 24 * 3600  # 7 days
    prediction_error_median_threshold_pct: int = 30
    bullet_drift_threshold: float = 0.15  # placeholder; recalibrated by harness


class CavemanConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = False  # OFF by default — P0 per elicitation §5.1
    default_intensity: str = "moderate"
    default_dialect: str = "caveman_english"
    accept_wenyan: bool = False
    max_retries: int = 2
    gate: CavemanGateConfig = Field(default_factory=CavemanGateConfig)
    structural_bullet_drift_threshold: float = 0.15


class RTKConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    binary_override_path: str | None = None
    timeout_s: float = 30.0
    orphan_timeout_s: float = 60.0


class CompressionConfig(BaseModel):
    """Top-level compression configuration consumed by CompressionLayer / Orchestrator."""

    model_config = ConfigDict(frozen=True)

    mode: Literal["on", "off"] = "on"
    tonl: TONLConfig = Field(default_factory=TONLConfig)
    forge: ForgeConfig = Field(default_factory=ForgeConfig)
    caveman: CavemanConfig = Field(default_factory=CavemanConfig)
    rtk: RTKConfig = Field(default_factory=RTKConfig)

    @property
    def is_enabled(self) -> bool:
        return self.mode == "on"
