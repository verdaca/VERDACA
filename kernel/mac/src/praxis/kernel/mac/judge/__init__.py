"""MAC judge subpackage — arch §6.4 + §6.7.

Holds :class:`LLMJudgeClient` (production path with
``call_live()`` excluded from coverage per test-strategy v0.3 §13.5
and pi-mono §7 generated-file precedent).
"""

from __future__ import annotations

from praxis.kernel.mac.judge.llm_judge_client import LLMJudgeClient

__all__ = ("LLMJudgeClient",)
