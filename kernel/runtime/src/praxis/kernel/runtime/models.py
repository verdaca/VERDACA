"""Praxis Runtime — shared data types.

This module is the canonical location for cross-module runtime types.

Public surface:
  AgentDefinition  — frozen Pydantic model mirroring agent-manifest.csv
  AgentRole        — spawn-time role enum (moved here from proxies._base)
  AgentModule      — BMAD module origin enum

Architecture references:
  architecture.md §2.1 (AgentDefinition schema)
  architecture.md §4.1.1 (AgentRole)
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentModule(StrEnum):
    """BMAD module origin — groups agents by lineage."""

    BMM = "bmm"  # Business/Market/Methodology agents
    CIS = "cis"  # Creative Innovation Studio agents
    TEA = "tea"  # Test Architecture agents


class AgentRole(StrEnum):
    """Role assigned to a spawned agent at construction time.

    PRODUCER — the agent can read from Memory and write outcomes / facts /
               decisions.  Receives a ProducerMemoryProxy.
    REVIEWER — the agent can only write decisions and flag/quarantine entries.
               Receives a ReviewerMemoryProxy.  All read paths are absent
               (AttributeError at Python interpreter level, §9.1.1).

    NOTE: This enum was relocated from proxies._base to runtime.models to
    prevent directional coupling between loader/registry and proxies.
    proxies._base re-exports AgentRole from here for backward compatibility.
    """

    PRODUCER = "producer"
    REVIEWER = "reviewer"


class AgentDefinition(BaseModel):
    """Frozen, validated, typed representation of a BMAD agent.

    One-to-one reflection of ``_bmad/_config/agent-manifest.csv`` columns
    with validation rules applied at load time.  Application code never
    instantiates this directly — the Loader (loader/manifest.py) owns
    construction.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Identity
    name: str = Field(..., min_length=1, description="Stable slug, e.g. 'bmad-agent-architect'")
    display_name: str = Field(..., min_length=1, description="Human-readable name, e.g. 'Winston'")
    title: str = Field(..., min_length=1, description="Role title, e.g. 'Architect'")
    icon: str = Field(..., description="Emoji or short glyph for UX surfaces")

    # Capability surface (the retrieval target for the Registry)
    capabilities: tuple[str, ...] = Field(
        ...,
        description="Normalized lowercase capability tokens",
    )

    # Persona (drives system-prompt assembly; not used for matching)
    role: str = Field(..., min_length=1, description="One-line role description")
    identity: str = Field(..., description="Multi-sentence identity/background")
    communication_style: str = Field(..., description="Tone, voice, interaction norms")
    principles: str = Field(..., description="Operating principles")

    # Provenance
    module: AgentModule = Field(..., description="Originating BMAD module")
    path: Path = Field(..., description="Relative path to agent skill dir under _bmad/")
    canonical_id: str = Field(default="", description="Optional canonical identifier")

    @field_validator("capabilities", mode="before")
    @classmethod
    def _normalize_capabilities(cls, v: Any) -> tuple[str, ...]:
        """Parse CSV cell or sequence into normalized lowercase token tuple."""
        if isinstance(v, str):
            tokens = tuple(t.strip().lower() for t in v.split(",") if t.strip())
            if not tokens:
                raise ValueError("capabilities must contain at least one token")
            return tokens
        if isinstance(v, (list, tuple)):
            tokens = tuple(t.strip().lower() for t in v if isinstance(t, str) and t.strip())
            if not tokens:
                raise ValueError("capabilities must contain at least one token")
            return tokens
        raise TypeError(f"capabilities must be str, list, or tuple; got {type(v).__name__}")

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        """Name must match BMAD slug convention: alphanumeric + hyphen/underscore."""
        clean = v.replace("-", "").replace("_", "")
        if not clean.isalnum():
            raise ValueError(
                f"name {v!r} contains invalid characters; "
                "expected alphanumeric + hyphen/underscore only"
            )
        return v

    @field_validator("path")
    @classmethod
    def _validate_path(cls, v: Path) -> Path:
        """Path must be relative (resolved at load time against _bmad/ root).

        Catches both POSIX-absolute (/foo/bar) and drive-absolute (C:/foo)
        paths on any platform.
        """
        # is_absolute() catches C:/foo on Windows and /foo on Unix.
        # str check catches /foo on Windows where is_absolute() returns False
        # because there is no drive letter — still rooted, still invalid.
        if v.is_absolute() or str(v).startswith("/") or str(v).startswith("\\"):
            raise ValueError(f"path {v!r} must be relative to _bmad/")
        return v


__all__ = ["AgentDefinition", "AgentModule", "AgentRole"]
