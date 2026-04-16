"""Caveman content boundary detection — classify text as prose/code/structured."""
from __future__ import annotations

import re

from .models import ContentType

# Patterns for code/structured content
_FENCED_CODE_RE = re.compile(r"```[\w]*\n.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*?\}", re.DOTALL)
_YAML_KEY_RE = re.compile(r"^\s*\w+:\s+\S", re.MULTILINE)
_SQL_KEYWORD_RE = re.compile(
    r"\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|FROM|WHERE|JOIN)\b",
    re.IGNORECASE,
)
_XML_TAG_RE = re.compile(r"<[a-zA-Z][a-zA-Z0-9]*[^>]*>")


def classify_content(text: str) -> ContentType:
    """Classify *text* into a content type.

    Rules (architecture §3.4.2 V-C7):
    - CODE_DOMINANT: >= 30% of text is inside fenced code blocks
    - STRUCTURED: detected JSON/YAML/SQL/XML structure dominant
    - MIXED: some code/structure but prose majority
    - PROSE_DOMINANT: everything else (safe to compress)
    """
    if not text:
        return ContentType.PROSE_DOMINANT

    total_len = len(text)
    if total_len == 0:
        return ContentType.PROSE_DOMINANT

    # Measure fenced code block coverage
    code_chars = sum(len(m.group(0)) for m in _FENCED_CODE_RE.finditer(text))
    code_ratio = code_chars / total_len

    if code_ratio >= 0.30:
        return ContentType.CODE_DOMINANT

    # Check structured content signals
    sql_hits = len(_SQL_KEYWORD_RE.findall(text))
    xml_hits = len(_XML_TAG_RE.findall(text))
    yaml_hits = len(_YAML_KEY_RE.findall(text))

    structured_score = sql_hits * 3 + xml_hits + yaml_hits
    if structured_score >= 5:
        return ContentType.STRUCTURED

    if code_ratio >= 0.10 or structured_score >= 2:
        return ContentType.MIXED

    return ContentType.PROSE_DOMINANT


def extract_code_blocks(text: str) -> list[str]:
    """Return all fenced code block contents (byte-exact for comparison)."""
    return [m.group(0) for m in _FENCED_CODE_RE.finditer(text)]


def extract_urls(text: str) -> set[str]:
    """Return the set of URLs present in *text*."""
    url_re = re.compile(r"https?://[^\s\)\"'>]+")
    return set(url_re.findall(text))


def extract_paths(text: str) -> set[str]:
    """Return the set of file paths present in *text*."""
    path_re = re.compile(r"(?:/[\w./\-_]+(?:\.\w+)?|[A-Za-z]:\\[\w\\./\-_]+)")
    return set(path_re.findall(text))
