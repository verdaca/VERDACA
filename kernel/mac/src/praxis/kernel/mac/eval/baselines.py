"""Benchmark baseline prompts — verbatim from benchmark-questions.md §6 Step 1.

Three baselines per arch §9.3 / ADR-1:
  - **Vanilla:** standard analytical prompt
  - **Enhanced:** explicit chain-of-thought + steelman + dissent instruction
  - **MAC:** standard MAC task intake via Task Interpreter (no special instructions)

The MAC baseline has no prompt string — it's triggered by the normal
``deliberate(task)`` path.

Binding anchors:
  - mac/architecture.md §9.3 The 3 Baseline Conditions
  - mac/benchmark-questions.md §6 Step 1 Preparation (verbatim source)
"""

from __future__ import annotations


BASELINE_VANILLA_PROMPT: str = (
    "You are a strategic advisor. A client asks: {question}. Provide your analysis."
)
"""benchmark-questions.md §6 Step 1 verbatim."""


BASELINE_ENHANCED_PROMPT: str = (
    "You are a strategic advisor. A client asks: {question}. "
    "In your analysis: (a) explicitly steelman the strongest opposing "
    "recommendation; (b) present any significant minority views from "
    "different stakeholder perspectives; (c) show your reasoning chain "
    "explicitly."
)
"""benchmark-questions.md §6 Step 1 enhanced baseline verbatim."""


__all__ = ("BASELINE_ENHANCED_PROMPT", "BASELINE_VANILLA_PROMPT")
