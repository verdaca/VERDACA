"""Decimal cost math. The single source of truth for `tokens * rate` → USD.

Every cost calculation in Pi-Mono flows through `compute_cost`. This module
has zero internal imports — it is pure Decimal arithmetic.
"""
from __future__ import annotations

from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from .models import CostAmount, LLMResponse, ModelPricing

COST_PRECISION = 28
QUANTUM_PLACES = 10
QUANTUM = Decimal("1e-10")
MILLION = Decimal("1000000")
ZERO = Decimal("0")

COST_CONTEXT = Context(
    prec=COST_PRECISION,
    rounding=ROUND_HALF_EVEN,
)


def compute_cost(response: LLMResponse, pricing: ModelPricing) -> CostAmount:
    """Compute a CostAmount from raw token counts and a pricing row.

    Invariants:
      - All arithmetic runs inside a local Decimal context (never the global).
      - Every component is quantized to QUANTUM using banker's rounding.
      - total == sum of four quantized components (exact Decimal equality).
    """
    with localcontext(COST_CONTEXT):
        input_c = Decimal(response.input_tokens) * pricing.input_rate / MILLION
        output_c = Decimal(response.output_tokens) * pricing.output_rate / MILLION
        cread_c = Decimal(response.cache_read_tokens) * pricing.cache_read_rate / MILLION
        cwrite_c = Decimal(response.cache_write_tokens) * pricing.cache_write_rate / MILLION

        input_q = input_c.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
        output_q = output_c.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
        cread_q = cread_c.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
        cwrite_q = cwrite_c.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)

        total_q = (input_q + output_q + cread_q + cwrite_q).quantize(
            QUANTUM, rounding=ROUND_HALF_EVEN
        )

    return CostAmount(
        input=input_q,
        output=output_q,
        cache_read=cread_q,
        cache_write=cwrite_q,
        total=total_q,
        currency=pricing.currency,
    )


def quantize(value: Decimal) -> Decimal:
    """Quantize a Decimal to the storage/display quantum using banker's rounding."""
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
