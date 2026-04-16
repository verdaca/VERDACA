"""CostEvent namespace prefix discipline — architecture §8.2.

All CostEvent types emitted by Runtime must start with exactly one of:
  memory.*   — originated in Memory layer
  runtime.*  — originated in Runtime layer
  compression.* — originated in Compression layer (future)
"""

from __future__ import annotations

_ALLOWED_PREFIXES = ("memory.", "runtime.", "compression.")

EXPECTED_COST_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "memory.retention_action",
        "memory.record_created",
        "memory.retrieval_cache_hit",
        "runtime.agent_spawn",
        "runtime.agent_terminate",
        "runtime.tool_call.class_a",
        "runtime.tool_call.class_b",
        "runtime.tool_call.class_c",
        "runtime.tool_call.class_d",
        "runtime.budget_exceeded",
        "runtime.registry_llm_rerank",
        "runtime.agent_result_lost",
        "runtime.compression",
    }
)


def validate_namespace(event_type: str) -> bool:
    """Return True iff event_type starts with an allowed namespace prefix.

    Architecture §8.2 taxonomy discipline.
    """
    return any(event_type.startswith(p) for p in _ALLOWED_PREFIXES)


__all__ = ["validate_namespace", "EXPECTED_COST_EVENT_TYPES"]
