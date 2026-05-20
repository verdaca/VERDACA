"""A/B harness workload definitions and fixtures."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkloadRequest:
    """A single request in a workload replay."""

    payload: Any
    session_id: str = "harness-default"
    description: str = ""


@dataclass(frozen=True)
class Workload:
    """A named workload for A/B benchmarking."""

    name: str
    requests: list[WorkloadRequest]
    seed: int = 42
    description: str = ""


# ---------------------------------------------------------------------------
# Sample workload fixtures (architecture §6.1)
# ---------------------------------------------------------------------------

def make_tonl_heavy_workload() -> Workload:
    """A workload dominated by large uniform message arrays (exercises TONL)."""
    messages = [
        {"role": "user", "content": f"Query {i}: What is the capital of country {i}?"}
        for i in range(50)
    ] + [
        {"role": "assistant", "content": f"Answer {i}: The capital is City {i}."}
        for i in range(50)
    ]
    return Workload(
        name="tonl_heavy",
        description="Large uniform message array — exercises TONL tabular encoding",
        requests=[
            WorkloadRequest(
                payload={"messages": messages, "session_id": "tonl-sess"},
                description="50-message array",
            )
        ],
    )


def make_prose_heavy_workload() -> Workload:
    """A workload with long prose output (exercises Caveman gate)."""
    long_prose = (
        "This is a comprehensive analysis of the system's current state. "
        "The recommended approach is to use the recommended configuration. "
        "Do not disable the safety checks. The system is safe and supported. "
        "All features are enabled and valid. The configuration is correct. "
        "Please include all required dependencies and exclude deprecated ones. "
        "The public API allows all valid requests and accepts standard formats. "
    ) * 20  # ~1400 tokens
    return Workload(
        name="prose_heavy",
        description="Long prose response — exercises Caveman net-positive gate",
        requests=[
            WorkloadRequest(
                payload={"response": long_prose},
                description="~1400-token prose response",
            )
        ],
    )


def make_forge_heavy_workload() -> Workload:
    """A workload with a long conversation history (exercises Forge compaction)."""
    from praxis.kernel.compression.forge.models import ConversationMessage, Role

    messages = []
    for i in range(70):
        role = Role.USER if i % 2 == 0 else Role.ASSISTANT
        messages.append(
            ConversationMessage(
                role=role,
                content=f"Turn {i}: {'User query about topic ' + str(i) if role == Role.USER else 'Assistant detailed response covering many aspects of topic ' + str(i) + ' with full context.'}",
            )
        )
    return Workload(
        name="forge_heavy",
        description="70-turn conversation — triggers Forge compaction",
        requests=[
            WorkloadRequest(
                payload={"turn_count": 70},
                description="Long conversation history",
                session_id="forge-sess",
            )
        ],
    )


def make_mixed_workload() -> Workload:
    """A mixed workload exercising all compression layers."""
    messages = [
        {"role": "user", "content": "Explain the deployment process in detail."},
        {"role": "assistant", "content": "The deployment process involves: 1. Building the artifact. 2. Running tests. 3. Pushing to registry. 4. Deploying to staging. 5. Running smoke tests. 6. Promoting to production."},
        {"role": "user", "content": "What are the rollback procedures?"},
        {"role": "assistant", "content": "Rollback procedure: Run git revert, tag the rollback commit, push to registry, deploy previous version."},
    ]
    return Workload(
        name="mixed",
        description="Mixed workload: TONL + Forge-capable conversation",
        requests=[
            WorkloadRequest(
                payload={"messages": messages},
                description="4-turn deployment Q&A",
                session_id="mixed-sess",
            )
        ],
    )


ALL_WORKLOADS: list[Workload] = [
    make_tonl_heavy_workload(),
    make_prose_heavy_workload(),
    make_forge_heavy_workload(),
    make_mixed_workload(),
]
