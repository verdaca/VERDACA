"""Pi-Mono integration — emit compression tags on LLMRequest objects.

Architecture §4.1: tags are attached to the existing LLMRequest.tags dict.
No new CostEvent type is created (alignment-review §6 contract).
Pi-Mono's frozen model requires model_copy() to update tags.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Add Pi-Mono source to path if not already importable
_PI_MONO_SRC = (
    Path(__file__).resolve().parents[5]
    / "pi-mono" / "src"
)


def _ensure_pi_mono_on_path() -> None:
    pi_mono_str = str(_PI_MONO_SRC)
    if pi_mono_str not in sys.path and _PI_MONO_SRC.exists():
        sys.path.insert(0, pi_mono_str)


_ensure_pi_mono_on_path()

try:
    from praxis.kernel.cost.models import LLMRequest  # type: ignore[import]
    _PI_MONO_AVAILABLE = True
except ImportError:
    _PI_MONO_AVAILABLE = False
    LLMRequest = None  # type: ignore[assignment,misc]

# Tag key constants (architecture §4.1)
TAG_MODE = "compression.mode"
TAG_PIPELINE = "compression.pipeline"
TAG_TOKENS_BEFORE = "compression.tokens.before"
TAG_TOKENS_AFTER = "compression.tokens.after"
TAG_BYTES_BEFORE = "compression.bytes.before"
TAG_BYTES_AFTER = "compression.bytes.after"
TAG_FALLBACK = "compression.fallback"
TAG_TONL_TOKENIZER = "compression.tonl.tokenizer"
TAG_FORGE_COMPACTIONS = "compression.forge.compactions"
TAG_FORGE_TOKENS_SAVED = "compression.forge.tokens_saved"
TAG_CAVEMAN_INTENSITY = "compression.caveman.intensity"
TAG_CAVEMAN_DIALECT = "compression.caveman.dialect"
TAG_CAVEMAN_COST_TOKENS = "compression.caveman.cost_tokens"
TAG_RTK_BYTES_SAVED = "compression.rtk.bytes_saved_prior"

# Tag budget (architecture §4.1 — hard ceiling)
_TAG_CEILING = 28

# Priority order for tag budget enforcement (drop last = lowest priority first)
_TAG_PRIORITY = [
    TAG_MODE,
    TAG_PIPELINE,
    TAG_TOKENS_BEFORE,
    TAG_TOKENS_AFTER,
    TAG_BYTES_BEFORE,
    TAG_BYTES_AFTER,
    TAG_FALLBACK,
    TAG_FORGE_TOKENS_SAVED,
    TAG_FORGE_COMPACTIONS,
    TAG_RTK_BYTES_SAVED,
    TAG_CAVEMAN_COST_TOKENS,
    TAG_CAVEMAN_INTENSITY,
    TAG_CAVEMAN_DIALECT,
    TAG_TONL_TOKENIZER,
]


def merge_compression_tags(
    existing_tags: dict[str, str],
    compression_tags: dict[str, str],
) -> dict[str, str]:
    """Merge *compression_tags* into *existing_tags* respecting the 28-tag ceiling.

    Drops lowest-priority compression tags when budget is exceeded.
    Logs an event when tags are dropped (architecture §4.1 FMEA P.2).
    """
    merged = dict(existing_tags)
    merged.update(compression_tags)

    if len(merged) <= _TAG_CEILING:
        return merged

    # Budget exceeded — drop lowest-priority compression tags
    compression_keys = set(compression_tags.keys())
    to_drop = len(merged) - _TAG_CEILING

    # Drop in reverse priority order (lowest priority = last in _TAG_PRIORITY)
    priority_dict = {k: i for i, k in enumerate(_TAG_PRIORITY)}
    sortable = sorted(
        compression_keys,
        key=lambda k: priority_dict.get(k, -1),
        reverse=True,
    )

    dropped = []
    for key in sortable:
        if to_drop <= 0:
            break
        if key in merged:
            del merged[key]
            dropped.append(key)
            to_drop -= 1

    if dropped:
        logger.warning(
            "orchestrator.tag_budget_exceeded: dropped compression tags %s "
            "(existing=%d, compression=%d, ceiling=%d)",
            dropped,
            len(existing_tags),
            len(compression_tags),
            _TAG_CEILING,
        )

    return merged


def apply_tags_to_request(request: object, compression_tags: dict[str, str]) -> object:
    """Return a new LLMRequest with compression tags merged in.

    If Pi-Mono is not importable (test environments without Pi-Mono on path),
    returns the original request unchanged and logs a warning.
    """
    if not _PI_MONO_AVAILABLE or LLMRequest is None:
        logger.debug("Pi-Mono not available — skipping tag attachment")
        return request

    if not isinstance(request, LLMRequest):
        logger.warning(
            "apply_tags_to_request: expected LLMRequest, got %s — skipping",
            type(request).__name__,
        )
        return request

    merged = merge_compression_tags(dict(request.tags), compression_tags)
    return request.model_copy(update={"tags": merged})
