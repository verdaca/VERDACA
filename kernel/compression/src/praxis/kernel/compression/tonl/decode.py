"""TONL decoder — TONL text → Python objects.

Mirrors the encoding produced by ``encode.py``. Perfect round-trip guaranteed:
``decode(encode(x)) == x`` for all supported types.
"""
from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from .errors import TONLParseError, TONLSecurityError
from .security import (
    MAX_ROWS_PER_TABLE,
    check_size,
    check_string_len,
)

MAGIC = "TONL1"
_TABLE_REF_PREFIX = "@TONLT"
_DECIMAL_PREFIX = "@TONLD"
_ESCAPE_PREFIX = "@TONLE"
_FIELD_SEP = "|"
_TABLE_HEADER_RE = re.compile(r"^TABLE(\d+):(\d+):(.+)$")
_UNESCAPE_MAP = {"\\\\": "\\", "\\|": "|", "\\n": "\n"}
_UNESCAPE_RE = re.compile(r"\\[\\|n]")


def _unescape_cell(raw: str) -> str:
    def replace(m: re.Match[str]) -> str:
        return _UNESCAPE_MAP.get(m.group(0), m.group(0))
    return _UNESCAPE_RE.sub(replace, raw)


def _parse_tables(lines: list[str], start: int) -> dict[int, list[dict[str, Any]]]:
    """Parse TABLE sections from *lines* starting at index *start*."""
    tables: dict[int, list[dict[str, Any]]] = {}
    i = start

    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue

        m = _TABLE_HEADER_RE.match(line)
        if not m:
            raise TONLParseError(f"unexpected line in table section: {line!r}")

        table_idx = int(m.group(1))
        row_count = int(m.group(2))
        col_str = m.group(3)
        cols = col_str.split(",")

        if row_count > MAX_ROWS_PER_TABLE:
            raise TONLSecurityError(f"table {table_idx} row count {row_count} exceeds limit")

        rows: list[dict[str, Any]] = []
        for j in range(row_count):
            i += 1
            if i >= len(lines):
                raise TONLParseError(
                    f"table {table_idx}: expected {row_count} rows, found {j}"
                )
            raw_row = lines[i]
            # Split on un-escaped |
            cells = _split_row(raw_row, len(cols))
            row_dict: dict[str, Any] = {}
            for col, cell_raw in zip(cols, cells):
                cell_str = _unescape_cell(cell_raw)
                # Cells were JSON-encoded before escaping
                cell_val = json.loads(cell_str)
                row_dict[col] = cell_val
            rows.append(row_dict)

        tables[table_idx] = rows
        i += 1

    return tables


def _split_row(raw: str, expected_cols: int) -> list[str]:
    """Split a row on un-escaped ``|`` characters."""
    cells: list[str] = []
    current: list[str] = []
    idx = 0
    while idx < len(raw):
        ch = raw[idx]
        if ch == "\\" and idx + 1 < len(raw):
            current.append(ch)
            current.append(raw[idx + 1])
            idx += 2
        elif ch == _FIELD_SEP:
            cells.append("".join(current))
            current = []
            idx += 1
        else:
            current.append(ch)
            idx += 1
    cells.append("".join(current))

    if len(cells) != expected_cols:
        raise TONLParseError(
            f"row has {len(cells)} cells but schema has {expected_cols} columns"
        )
    return cells


def _decode_value(value: Any, tables: dict[int, list[dict[str, Any]]]) -> Any:
    """Recursively decode sentinel strings back to original Python objects."""
    if isinstance(value, str):
        if value.startswith(_ESCAPE_PREFIX):
            # Un-escape: strip the escape prefix, return the original string
            return value[len(_ESCAPE_PREFIX):]
        if value.startswith(_TABLE_REF_PREFIX):
            idx = int(value[len(_TABLE_REF_PREFIX):])
            if idx not in tables:
                raise TONLParseError(f"table reference @TONLT{idx} not found in document")
            # Recursively decode each row so escape prefixes in cell values are resolved
            return [_decode_value(row, tables) for row in tables[idx]]
        if value.startswith(_DECIMAL_PREFIX):
            decimal_str = value[len(_DECIMAL_PREFIX):]
            try:
                return Decimal(decimal_str)
            except InvalidOperation as exc:
                raise TONLParseError(f"invalid Decimal in TONL: {decimal_str!r}") from exc
        return value
    if isinstance(value, dict):
        return {k: _decode_value(v, tables) for k, v in value.items()}
    if isinstance(value, list):
        return [_decode_value(v, tables) for v in value]
    return value


def decode(text: str) -> Any:
    """Decode a TONL-encoded string to a Python object.

    Args:
        text: TONL-encoded string as produced by ``encode()``.

    Returns:
        The original Python object.

    Raises:
        TONLParseError:    if the document is malformed.
        TONLSecurityError: if security limits are violated.
    """
    check_size(text)

    lines = text.rstrip("\n").split("\n")

    if not lines or lines[0] != MAGIC:
        raise TONLParseError(
            f"invalid TONL magic header: expected {MAGIC!r}, got {lines[0]!r}"
        )

    if len(lines) < 2:
        raise TONLParseError("TONL document must have at least a magic line and JSON body")

    json_body = lines[1]
    try:
        raw_parsed = json.loads(json_body)
    except json.JSONDecodeError as exc:
        raise TONLParseError(f"TONL JSON body is malformed: {exc}") from exc

    # Parse table sections (lines[2:])
    tables = _parse_tables(lines, start=2) if len(lines) > 2 else {}

    return _decode_value(raw_parsed, tables)
