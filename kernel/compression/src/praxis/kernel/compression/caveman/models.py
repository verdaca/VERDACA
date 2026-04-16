"""Caveman data models."""
from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Intensity(StrEnum):
    LITE = "lite"
    MILD = "mild"
    MODERATE = "moderate"
    HEAVY = "heavy"
    EXTREME = "extreme"
    ULTRA = "ultra"
    FULL = "moderate"  # alias for MODERATE — default intensity


class Dialect(StrEnum):
    CAVEMAN_ENGLISH = "caveman_english"
    WENYAN = "wenyan"


class ContentType(StrEnum):
    PROSE_DOMINANT = "prose_dominant"
    CODE_DOMINANT = "code_dominant"
    MIXED = "mixed"
    STRUCTURED = "structured"


class CompressionRequest(BaseModel):
    """Input to compress_output()."""

    model_config = ConfigDict(frozen=True)

    text: str
    intensity: Intensity = Intensity.FULL  # type: ignore[assignment]
    dialect: Dialect = Dialect.CAVEMAN_ENGLISH
    expected_downstream_reads: int = 0
    accept_wenyan: bool = False

    @property
    def text_length_tokens(self) -> int:
        """Rough token count (4 chars/token heuristic)."""
        return max(1, len(self.text) // 4)



class StructuralError(BaseModel):
    """A single structural validation failure."""

    model_config = ConfigDict(frozen=True)

    kind: str
    detail: str = ""


class SemanticError(BaseModel):
    """A single semantic validation failure."""

    model_config = ConfigDict(frozen=True)

    kind: str
    detail: str = ""


class ValidationReport(BaseModel):
    """Combined structural + semantic validation result."""

    model_config = ConfigDict(frozen=True)

    structural_errors: list[StructuralError] = Field(default_factory=list)
    semantic_errors: list[SemanticError] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.structural_errors and not self.semantic_errors

    @property
    def all_errors(self) -> list[str]:
        return (
            [e.kind for e in self.structural_errors]
            + [e.kind for e in self.semantic_errors]
        )


class CompressionResult(BaseModel):
    """Output of compress_output()."""

    model_config = ConfigDict(frozen=True)

    text_in: str
    text_out: str
    compressed: bool
    fallback_reason: str | None = None
    gate_denied_reason: str | None = None
    validation_report: ValidationReport | None = None
    net_savings_tokens: int = 0
    compression_cost_tokens: int = 0
    retry_count: int = 0
    caveman_tags: dict[str, str] = Field(default_factory=dict)
