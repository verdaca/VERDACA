"""Unit tests — TONL round-trip edge cases (Pipeline gate §2.4).

Required by Pipeline: "Round-trip tests pass on all TONL edge cases":
- Empty table (single-row, no savings — not encoded as table)
- Single-row table
- Deeply nested dicts
- Pipe | in content (cell escape)
- Newline in content (escape)
- Sentinel collision escape (\x01, \x02)
- Decimal round-trip
- All-None values
- Unicode surrogate-safe text
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from praxis.kernel.compression.tonl.decode import decode
from praxis.kernel.compression.tonl.encode import encode


def rt(value):
    """Encode then decode; assert equality."""
    result = decode(encode(value))
    assert result == value, f"Round-trip failed: {value!r} → {result!r}"
    return result


# ---------------------------------------------------------------------------
# Table path — edge cases
# ---------------------------------------------------------------------------

class TestTableEdgeCases:
    def test_single_row_not_encoded_as_table(self):
        payload = [{"role": "user", "content": "hello"}]
        encoded = encode(payload)
        # Single row → below min_rows=2 → not a table
        assert "TABLE0:" not in encoded
        rt(payload)

    def test_empty_list_round_trips(self):
        rt([])

    def test_two_row_minimum_table(self):
        payload = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
        encoded = encode(payload)
        assert "TABLE0:" in encoded
        rt(payload)

    def test_table_with_empty_string_values(self):
        payload = [{"a": "", "b": ""}, {"a": "", "b": ""}]
        rt(payload)

    def test_table_with_none_values(self):
        payload = [{"a": None, "b": "x"}, {"a": None, "b": "y"}]
        rt(payload)

    def test_table_with_bool_values(self):
        payload = [{"ok": True, "n": 1}, {"ok": False, "n": 2}]
        rt(payload)

    def test_table_with_integer_values(self):
        payload = [{"id": i, "val": i * 10} for i in range(5)]
        rt(payload)


# ---------------------------------------------------------------------------
# Cell escape edge cases
# ---------------------------------------------------------------------------

class TestCellEscapeEdgeCases:
    def test_pipe_in_table_cell(self):
        payload = [{"a": "x|y|z", "b": "1"}, {"a": "p|q", "b": "2"}]
        rt(payload)

    def test_newline_in_table_cell(self):
        payload = [{"a": "line1\nline2", "b": "x"}, {"a": "line3\nline4", "b": "y"}]
        rt(payload)

    def test_backslash_in_table_cell(self):
        payload = [{"path": "C:\\Users\\test"}, {"path": "D:\\data"}]
        rt(payload)

    def test_sentinel_collision_escape(self):
        # Values containing the TONL sentinel characters must survive round-trip
        payload = [{"a": "\x01abc", "b": "x"}, {"a": "\x02def", "b": "y"}]
        rt(payload)

    def test_pipe_and_newline_combined(self):
        payload = [{"x": "a|b\nc|d", "y": "1"}, {"x": "e|f\ng|h", "y": "2"}]
        rt(payload)

    def test_all_special_chars_in_value(self):
        special = "pipe| newline\n backslash\\ sentinel\x01\x02 end"
        payload = [{"text": special, "n": 1}, {"text": "clean", "n": 2}]
        rt(payload)


# ---------------------------------------------------------------------------
# Deeply nested dicts
# ---------------------------------------------------------------------------

class TestDeeplyNestedDicts:
    def test_nested_three_levels(self):
        rt({"a": {"b": {"c": 42}}})

    def test_nested_five_levels(self):
        rt({"l1": {"l2": {"l3": {"l4": {"l5": "deep"}}}}})

    def test_nested_with_list_inside(self):
        rt({"meta": {"messages": [{"role": "user"}, {"role": "assistant"}]}})

    def test_nested_with_table_inside(self):
        rt({
            "session": "abc",
            "data": {
                "messages": [
                    {"role": "user", "content": "hello"},
                    {"role": "assistant", "content": "hi"},
                ]
            }
        })

    def test_dict_with_list_of_dicts_non_uniform(self):
        # Non-uniform list → not table-encoded, must still round-trip
        rt({"items": [{"a": 1}, {"b": 2}]})


# ---------------------------------------------------------------------------
# Decimal round-trip
# ---------------------------------------------------------------------------

class TestDecimalRoundTrip:
    def test_simple_decimal(self):
        rt({"cost": Decimal("1.23")})

    def test_high_precision_decimal(self):
        rt({"price": Decimal("0.00000001")})

    def test_large_decimal(self):
        rt({"amount": Decimal("9999999999.99")})

    def test_negative_decimal(self):
        rt({"balance": Decimal("-42.50")})

    def test_decimal_in_table(self):
        rt([{"cost": Decimal("1.00")}, {"cost": Decimal("2.50")}])

    def test_zero_decimal(self):
        rt({"x": Decimal("0")})


# ---------------------------------------------------------------------------
# Scalar and misc edge cases
# ---------------------------------------------------------------------------

class TestMiscEdgeCases:
    def test_empty_dict(self):
        rt({})

    def test_none_value(self):
        rt({"x": None})

    def test_all_none_dict(self):
        rt({"a": None, "b": None, "c": None})

    def test_unicode_text(self):
        rt({"msg": "Héllo wörld 日本語 emoji 🎉"})

    def test_large_integer(self):
        rt({"n": 2**53 - 1})

    def test_negative_integer(self):
        rt({"n": -1000000})

    def test_boolean_true_false(self):
        rt({"t": True, "f": False})

    def test_mixed_types_in_dict(self):
        rt({"s": "text", "n": 42, "b": True, "null": None})
