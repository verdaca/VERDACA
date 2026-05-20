"""Praxis Runtime loader — CSV manifest → AgentDefinition collection.

Architecture references:
  architecture.md §2.3 (AgentLoader design)
  architecture.md §2.5 (validation rules)
"""

from __future__ import annotations

import csv
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from praxis.kernel.runtime.models import AgentDefinition, AgentModule

# ---------------------------------------------------------------------------
# Runtime config (schema bindings + tool allowlist)
# ---------------------------------------------------------------------------


class AgentInputSchema(BaseModel):
    """Base class for agent input payloads."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class AgentOutputSchema(BaseModel):
    """Base class for agent output payloads."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class GenericTaskInput(AgentInputSchema):
    """Default input schema for agents that ship no custom schema."""

    task_description: str
    context_budget_tokens: int = 100_000
    reference_bundle: dict[str, Any] | None = None


class GenericTaskOutput(AgentOutputSchema):
    """Default output schema."""

    summary: str
    artifacts: tuple[Path, ...] = ()
    decisions: tuple[str, ...] = ()
    follow_ups: tuple[str, ...] = ()


class AgentRuntimeConfig(BaseModel):
    """Runtime-layer configuration bound to an AgentDefinition at load time.

    Holds schema bindings, model selection, and MCP tool allowlist.
    Populated by AgentLoader; consumed by the Spawner and Registry.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent: AgentDefinition
    input_schema: type[AgentInputSchema] = GenericTaskInput
    output_schema: type[AgentOutputSchema] = GenericTaskOutput
    tool_allowlist: frozenset[str] = frozenset()
    model_preference: str = "claude-sonnet-4-6"
    thinking_level: str = "high"


# ---------------------------------------------------------------------------
# AgentLoaderError
# ---------------------------------------------------------------------------


class AgentLoaderError(Exception):
    """Raised when manifest parsing or validation fails."""


# ---------------------------------------------------------------------------
# AgentLoader
# ---------------------------------------------------------------------------


def _default_tool_allowlist(agent: AgentDefinition) -> frozenset[str]:
    """Default-deny per architecture §2.3 / §9.2.

    Every tool grant is explicit and auditable; default is empty.
    """
    return frozenset()


def _row_to_model_kwargs(row: Mapping[str, str]) -> dict[str, Any]:
    """Translate CSV column names (camelCase) → Pydantic field names (snake_case)."""
    return {
        "name": row["name"],
        "display_name": row["displayName"],
        "title": row["title"],
        "icon": row["icon"],
        "capabilities": row["capabilities"],
        "role": row["role"],
        "identity": row["identity"],
        "communication_style": row["communicationStyle"],
        "principles": row["principles"],
        "module": AgentModule(row["module"]),
        "path": Path(row["path"]),
        "canonical_id": row.get("canonicalId", ""),
    }


class AgentLoader:
    """Load the BMAD agent manifest from CSV and produce AgentRuntimeConfig objects.

    Responsibilities:
    - Parse ``_bmad/_config/agent-manifest.csv``
    - Validate each row via Pydantic (AgentDefinition)
    - Detect duplicate names
    - Attach runtime configs (schemas, empty tool allowlists)
    - Provide reload support for development mode
    """

    def __init__(
        self,
        manifest_path: Path,
        schemas_module: str | None = None,
        default_tool_allowlist_fn: Any = None,
    ) -> None:
        self._manifest_path = manifest_path
        self._schemas_module = schemas_module
        self._default_allowlist_fn = default_tool_allowlist_fn or _default_tool_allowlist
        self._cache: dict[str, AgentRuntimeConfig] | None = None

    def load(self) -> Mapping[str, AgentRuntimeConfig]:
        """Parse the manifest and return an immutable mapping keyed by agent name."""
        if self._cache is not None:
            return self._cache
        self._cache = dict(self._parse())
        return self._cache

    def reload(self) -> Mapping[str, AgentRuntimeConfig]:
        """Force re-parse. Intended for development; production uses load()."""
        self._cache = None
        return self.load()

    def _parse(self) -> Iterator[tuple[str, AgentRuntimeConfig]]:
        seen: set[str] = set()
        with self._manifest_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row_idx, row in enumerate(reader, start=1):
                try:
                    kwargs = _row_to_model_kwargs(row)
                    definition = AgentDefinition(**kwargs)
                except Exception as exc:
                    raise AgentLoaderError(f"row {row_idx}: {exc}") from exc

                if definition.name in seen:
                    raise AgentLoaderError(
                        f"duplicate agent name {definition.name!r} at row {row_idx}"
                    )
                seen.add(definition.name)

                runtime_config = self._bind_runtime_config(definition)
                yield definition.name, runtime_config

    def _bind_runtime_config(self, agent: AgentDefinition) -> AgentRuntimeConfig:
        input_schema, output_schema = self._resolve_schemas(agent)
        tool_allowlist = self._default_allowlist_fn(agent)
        return AgentRuntimeConfig(
            agent=agent,
            input_schema=input_schema,
            output_schema=output_schema,
            tool_allowlist=tool_allowlist,
        )

    def _resolve_schemas(
        self, agent: AgentDefinition
    ) -> tuple[type[AgentInputSchema], type[AgentOutputSchema]]:
        if self._schemas_module is None:
            return GenericTaskInput, GenericTaskOutput
        try:
            mod = __import__(
                f"{self._schemas_module}.{agent.name.replace('-', '_')}",
                fromlist=["*"],
            )
            return (
                getattr(mod, "input_schema", GenericTaskInput),
                getattr(mod, "output_schema", GenericTaskOutput),
            )
        except ImportError:
            return GenericTaskInput, GenericTaskOutput


__all__ = [
    "AgentLoader",
    "AgentLoaderError",
    "AgentRuntimeConfig",
    "AgentInputSchema",
    "AgentOutputSchema",
    "GenericTaskInput",
    "GenericTaskOutput",
]
