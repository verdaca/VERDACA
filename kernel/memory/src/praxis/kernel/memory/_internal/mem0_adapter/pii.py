"""Stub PII redactor for the Mem0 adapter write boundary (§4.5 #5).

This is a minimum-viable stub for Phase 3B-ii. The real implementation
(the same redactor used by seed corpus ingest per architecture §4.5) is
Phase 3C or later territory. The stub is:

- Deterministic — same input always produces the same output, so
  round-trip tests can assert on exact content.
- Non-destructive on non-PII — a fact like "ICP segment converts at 3×"
  passes through unchanged.
- Redacts the obvious — a literal email pattern and a literal SSN
  pattern get replaced with canonical placeholders so the write path is
  demonstrably running through a redactor, not a pass-through.

When the real redactor lands, swap the `redact` implementation;
callers (`Mem0Adapter.store_fact`) do not need to change.
"""

from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def redact(text: str) -> str:
    """Return `text` with obvious PII patterns replaced by placeholders.

    Phase 3B-ii stub. Real redactor lives elsewhere and will replace this.
    """
    text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = _SSN_RE.sub("[REDACTED_SSN]", text)
    return text


__all__ = ["redact"]
