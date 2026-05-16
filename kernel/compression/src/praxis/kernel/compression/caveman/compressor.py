"""Caveman compressor — main compress_output orchestrator (architecture §3.4).

Ships behind feature flag compression.caveman.enabled (default OFF per §5.1).
"""
from __future__ import annotations

import logging

from praxis.ports.llm_proxy import LLMProxyPort

from .dialects.caveman_english import CavemanEnglishDialect
from .dialects.wenyan import WenyanDialect
from .errors import CavemanGateDenied, CavemanProviderError, CavemanValidationError
from .gate import GateConfig, should_compress
from .models import (
    CompressionRequest,
    CompressionResult,
    Dialect,
    ValidationReport,
)
from .provider import HaikuProvider
from .validate import validate_all

logger = logging.getLogger(__name__)

_DIALECT_MAP = {
    Dialect.CAVEMAN_ENGLISH: CavemanEnglishDialect(),
    Dialect.WENYAN: WenyanDialect(),
}


async def compress_output(
    request: CompressionRequest,
    *,
    max_retries: int = 2,
    gate_config: GateConfig | None = None,
    provider: HaikuProvider | None = None,
    llm_proxy: LLMProxyPort | None = None,
) -> CompressionResult:
    """Compress *request.text* via Haiku, with validation and retry.

    Fallback policy (architecture §3.4.6/§3.4.7):
    - Gate denied → return original, tag gate_denied_reason
    - Provider error → return original, tag fallback_reason=provider_error
    - Validation exhausted → return original, tag fallback_reason=structural|semantic
    - Pathological expansion → return original, tag fallback_reason=expansion
    """
    cfg = gate_config or GateConfig()

    # Gate check
    ok, gate_reason = should_compress(
        text=request.text,
        dialect=request.dialect,
        expected_downstream_reads=request.expected_downstream_reads,
        accept_wenyan=request.accept_wenyan,
        config=cfg,
    )
    if not ok:
        logger.debug("caveman gate denied: %s", gate_reason)
        return CompressionResult(
            text_in=request.text,
            text_out=request.text,
            compressed=False,
            gate_denied_reason=gate_reason,
            caveman_tags={"compression.caveman.gate_denied": gate_reason},
        )

    dialect_impl = _DIALECT_MAP.get(request.dialect, _DIALECT_MAP[Dialect.CAVEMAN_ENGLISH])
    system_prompt = dialect_impl.system_prompt(request.intensity.value)

    # Provider resolution (after the gate — gate-denied requests never need one).
    # No provider and no port wired → graceful fallback, consistent with §3.4.6/§3.4.7.
    if provider is not None:
        prov = provider
    elif llm_proxy is not None:
        prov = HaikuProvider(llm_proxy=llm_proxy)
    else:
        logger.debug("caveman: no provider or llm_proxy configured")
        return CompressionResult(
            text_in=request.text,
            text_out=request.text,
            compressed=False,
            fallback_reason="provider_unconfigured",
            caveman_tags={"compression.caveman.fallback": "provider_unconfigured"},
        )

    # Compression + retry loop (architecture §3.4.6)
    current_text = request.text
    total_input_tokens = 0
    total_output_tokens = 0
    last_report: ValidationReport | None = None

    for attempt in range(max_retries + 1):
        try:
            if attempt == 0:
                compressed, input_tok, output_tok = await prov.compress(
                    request.text, system_prompt
                )
            else:
                # Targeted-fix retry
                error_names = last_report.all_errors if last_report else []
                compressed, input_tok, output_tok = await prov.compress_with_fix(
                    request.text, current_text, error_names, system_prompt
                )
            total_input_tokens += input_tok
            total_output_tokens += output_tok
        except CavemanProviderError as exc:
            logger.warning("caveman provider error (attempt %d): %s", attempt, exc)
            return CompressionResult(
                text_in=request.text,
                text_out=request.text,
                compressed=False,
                fallback_reason="provider_error",
                retry_count=attempt,
                caveman_tags={"compression.caveman.fallback": "provider_error"},
            )

        # Pathological expansion guard
        if len(compressed) >= len(request.text):
            logger.debug("caveman: expansion detected on attempt %d", attempt)
            current_text = request.text  # reset for retry or fallback
            if attempt == max_retries:
                return CompressionResult(
                    text_in=request.text,
                    text_out=request.text,
                    compressed=False,
                    fallback_reason="expansion",
                    retry_count=attempt + 1,
                    compression_cost_tokens=total_input_tokens + total_output_tokens,
                    caveman_tags={
                        "compression.caveman.fallback": "expansion",
                        "compression.caveman.cost_tokens": str(
                            total_input_tokens + total_output_tokens
                        ),
                    },
                )
            continue

        # Validate
        report = validate_all(request.text, compressed)
        last_report = report

        if report.passed:
            # Success
            tokens_in = request.text_length_tokens
            tokens_out = max(1, len(compressed) // 4)
            net_savings = tokens_in - tokens_out - (total_input_tokens + total_output_tokens)

            return CompressionResult(
                text_in=request.text,
                text_out=compressed,
                compressed=True,
                validation_report=report,
                net_savings_tokens=max(0, net_savings),
                compression_cost_tokens=total_input_tokens + total_output_tokens,
                retry_count=attempt,
                caveman_tags={
                    "compression.caveman.intensity": request.intensity.value,
                    "compression.caveman.dialect": request.dialect.value,
                    "compression.caveman.cost_tokens": str(
                        total_input_tokens + total_output_tokens
                    ),
                },
            )

        # Validation failed — set up for retry
        current_text = compressed
        logger.debug(
            "caveman validation failed on attempt %d: %s", attempt, report.all_errors
        )

    # Exhausted retries
    return CompressionResult(
        text_in=request.text,
        text_out=request.text,
        compressed=False,
        fallback_reason=last_report.all_errors[0] if last_report else "unknown",
        validation_report=last_report,
        retry_count=max_retries,
        compression_cost_tokens=total_input_tokens + total_output_tokens,
        caveman_tags={
            "compression.caveman.fallback": (
                last_report.all_errors[0] if last_report else "unknown"
            ),
            "compression.caveman.cost_tokens": str(
                total_input_tokens + total_output_tokens
            ),
        },
    )
