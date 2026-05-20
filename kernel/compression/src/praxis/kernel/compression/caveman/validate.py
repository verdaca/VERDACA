"""Caveman quality validators S1-S4 (100% line + branch coverage required per Murat §0.1).

S1: Structural integrity (headings, code blocks, URLs, paths, bullets)
S2: Numeric literal preservation
S3: Polarity pair preservation (CM5 — RPN-9 BLOCK risk)
S4: Imperative inversion detection (FMEA V.3)
"""
from __future__ import annotations

import re

from .boundary import extract_code_blocks, extract_paths, extract_urls
from .models import SemanticError, StructuralError, ValidationReport

# ---------------------------------------------------------------------------
# Structural validator (architecture §3.4.4)
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^#{1,6}\s+\S", re.MULTILINE)
_BULLET_RE = re.compile(r"^[ \t]*[-*+]\s+\S", re.MULTILINE)
_NUMERIC_RE = re.compile(r"\b\d+(?:\.\d+)?\b")

_BULLET_DRIFT_THRESHOLD: float = 0.15  # placeholder; recalibrated by harness (§10.11)


def _heading_count(text: str) -> int:
    return len(_HEADING_RE.findall(text))


def _bullet_count(text: str) -> int:
    return len(_BULLET_RE.findall(text))


def validate_structural(
    original: str,
    compressed: str,
    *,
    bullet_drift_threshold: float = _BULLET_DRIFT_THRESHOLD,
) -> list[StructuralError]:
    """Return a list of structural validation errors (empty = passed)."""
    errors: list[StructuralError] = []

    # H1: heading count
    orig_h = _heading_count(original)
    comp_h = _heading_count(compressed)
    if orig_h != comp_h:
        errors.append(StructuralError(
            kind="heading_count_mismatch",
            detail=f"original={orig_h}, compressed={comp_h}",
        ))

    # H2: code block byte-exact match
    orig_blocks = extract_code_blocks(original)
    comp_blocks = extract_code_blocks(compressed)
    if orig_blocks != comp_blocks:
        errors.append(StructuralError(
            kind="code_block_corruption",
            detail=f"original_count={len(orig_blocks)}, compressed_count={len(comp_blocks)}",
        ))

    # H3: URL set match
    orig_urls = extract_urls(original)
    comp_urls = extract_urls(compressed)
    if orig_urls != comp_urls:
        added = comp_urls - orig_urls
        removed = orig_urls - comp_urls
        errors.append(StructuralError(
            kind="url_drift",
            detail=f"removed={sorted(removed)}, added={sorted(added)}",
        ))

    # H4: file-path set match
    orig_paths = extract_paths(original)
    comp_paths = extract_paths(compressed)
    if orig_paths != comp_paths:
        errors.append(StructuralError(
            kind="path_drift",
            detail=f"removed={sorted(orig_paths - comp_paths)}, added={sorted(comp_paths - orig_paths)}",
        ))

    # H5: bullet count within tolerance
    bb = _bullet_count(original)
    cb = _bullet_count(compressed)
    if bb > 0:
        drift_ratio = abs(bb - cb) / bb
        if drift_ratio > bullet_drift_threshold:
            errors.append(StructuralError(
                kind="bullet_count_drift",
                detail=f"ratio={drift_ratio:.3f}, threshold={bullet_drift_threshold}",
            ))

    return errors


# ---------------------------------------------------------------------------
# Semantic validator (architecture §3.4.5)
# ---------------------------------------------------------------------------

_NEGATION_TOKENS: frozenset[str] = frozenset({
    "not", "no", "never", "without", "except", "unless", "cannot",
    "shouldn't", "don't", "doesn't", "isn't", "wasn't", "won't", "can't",
    "needn't", "mustn't", "shan't", "hadn't", "hasn't", "haven't",
})

_POLARITY_PAIRS: list[tuple[str, str]] = [
    ("safe", "unsafe"), ("recommended", "discouraged"), ("allow", "deny"),
    ("enable", "disable"), ("required", "optional"), ("valid", "invalid"),
    ("trusted", "untrusted"), ("supported", "unsupported"), ("public", "private"),
    ("include", "exclude"), ("accept", "reject"), ("approve", "reject"),
    ("possible", "impossible"), ("correct", "incorrect"), ("expected", "unexpected"),
    ("secure", "insecure"), ("authorized", "unauthorized"), ("encrypted", "unencrypted"),
    ("successful", "unsuccessful"), ("verified", "unverified"), ("protected", "unprotected"),
]

_IMPERATIVE_POSITIVE: frozenset[str] = frozenset({
    "do", "use", "run", "call", "include", "set", "enable", "apply", "add",
    "grant", "install", "allow", "create", "start", "deploy",
})
_IMPERATIVE_NEGATIVE: frozenset[str] = frozenset({
    "don't", "avoid", "skip", "exclude", "disable", "never", "remove", "omit",
    "deny", "revoke", "uninstall", "stop", "drop", "delete",
})


def _count_tokens_ci(text: str, token_set: frozenset[str]) -> int:
    words = re.findall(r"\b\w+(?:'\w+)?\b", text.lower())
    return sum(1 for w in words if w in token_set)


def _extract_numeric_literals(text: str) -> frozenset[str]:
    return frozenset(_NUMERIC_RE.findall(text))


def validate_semantic(original: str, compressed: str) -> list[SemanticError]:
    """Return a list of semantic validation errors (empty = passed)."""
    errors: list[SemanticError] = []

    # S1: negation token count
    orig_neg = _count_tokens_ci(original, _NEGATION_TOKENS)
    comp_neg = _count_tokens_ci(compressed, _NEGATION_TOKENS)
    if abs(orig_neg - comp_neg) > 1:
        errors.append(SemanticError(
            kind="negation_drift",
            detail=f"original={orig_neg}, compressed={comp_neg}",
        ))

    # S2: numeric literal preservation
    orig_numbers = _extract_numeric_literals(original)
    comp_numbers = _extract_numeric_literals(compressed)
    missing = orig_numbers - comp_numbers
    if missing:
        errors.append(SemanticError(
            kind="number_loss",
            detail=f"missing={sorted(missing)[:10]}",
        ))

    # S3: polarity pair preservation (CM5 RPN-9 BLOCK)
    for positive, negative in _POLARITY_PAIRS:
        orig_bias = (
            _count_tokens_ci(original, frozenset({positive}))
            - _count_tokens_ci(original, frozenset({negative}))
        )
        comp_bias = (
            _count_tokens_ci(compressed, frozenset({positive}))
            - _count_tokens_ci(compressed, frozenset({negative}))
        )
        if orig_bias != 0 and ((orig_bias > 0) != (comp_bias > 0)):
            errors.append(SemanticError(
                kind="polarity_flip",
                detail=f"pair=({positive},{negative}), orig_bias={orig_bias}, comp_bias={comp_bias}",
            ))

    # S4: imperative inversion
    orig_imp = (
        _count_tokens_ci(original, _IMPERATIVE_POSITIVE)
        - _count_tokens_ci(original, _IMPERATIVE_NEGATIVE)
    )
    comp_imp = (
        _count_tokens_ci(compressed, _IMPERATIVE_POSITIVE)
        - _count_tokens_ci(compressed, _IMPERATIVE_NEGATIVE)
    )
    if abs(orig_imp - comp_imp) > 1:
        errors.append(SemanticError(
            kind="imperative_drift",
            detail=f"original={orig_imp}, compressed={comp_imp}",
        ))

    return errors


def validate_all(
    original: str,
    compressed: str,
    *,
    bullet_drift_threshold: float = _BULLET_DRIFT_THRESHOLD,
) -> ValidationReport:
    """Run S1+S2+S3+S4 validators and return a combined ValidationReport."""
    structural = validate_structural(
        original, compressed, bullet_drift_threshold=bullet_drift_threshold
    )
    semantic = validate_semantic(original, compressed)
    return ValidationReport(structural_errors=structural, semantic_errors=semantic)
