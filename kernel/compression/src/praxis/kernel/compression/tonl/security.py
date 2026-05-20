"""TONL security guards — size limits, nesting depth, ReDoS protection."""
from __future__ import annotations

from .errors import TONLSecurityError

# Hard limits (architecture §3.1.5)
MAX_NESTING_DEPTH: int = 50
MAX_SIZE_BYTES: int = 10 * 1024 * 1024    # 10 MB
MAX_STRING_LEN: int = 1 * 1024 * 1024     # 1 MB
MAX_FIELDS_PER_ROW: int = 1_000
MAX_ROWS_PER_TABLE: int = 100_000


def check_size(data: str | bytes, *, context: str = "payload") -> None:
    """Raise TONLSecurityError if data exceeds MAX_SIZE_BYTES."""
    size = len(data) if isinstance(data, bytes) else len(data.encode("utf-8"))
    if size > MAX_SIZE_BYTES:
        raise TONLSecurityError(
            f"{context} size {size} bytes exceeds limit {MAX_SIZE_BYTES} bytes"
        )


def check_string_len(s: str, *, context: str = "string") -> None:
    """Raise TONLSecurityError if string exceeds MAX_STRING_LEN."""
    if len(s.encode("utf-8")) > MAX_STRING_LEN:
        raise TONLSecurityError(
            f"{context} length {len(s)} chars exceeds limit {MAX_STRING_LEN} bytes"
        )


def check_depth(depth: int) -> None:
    """Raise TONLSecurityError if nesting exceeds MAX_NESTING_DEPTH."""
    if depth > MAX_NESTING_DEPTH:
        raise TONLSecurityError(
            f"nesting depth {depth} exceeds limit {MAX_NESTING_DEPTH}"
        )


def check_fields_per_row(n: int) -> None:
    """Raise TONLSecurityError if too many columns in a table row."""
    if n > MAX_FIELDS_PER_ROW:
        raise TONLSecurityError(
            f"row field count {n} exceeds limit {MAX_FIELDS_PER_ROW}"
        )


def check_rows_per_table(n: int) -> None:
    """Raise TONLSecurityError if a table has too many rows."""
    if n > MAX_ROWS_PER_TABLE:
        raise TONLSecurityError(
            f"row count {n} exceeds limit {MAX_ROWS_PER_TABLE}"
        )
