"""Unit tests — TONL encode/decode round-trip and specific behaviours."""
from __future__ import annotations

import pytest
from decimal import Decimal

from praxis.kernel.compression.tonl.encode import encode, MAGIC
from praxis.kernel.compression.tonl.decode import decode
from praxis.kernel.compression.tonl.errors import (
    TONLParseError,
    TONLSecurityError,
    TONLTypeError,
    TONLValidationError,
)
from praxis.kernel.compression.tonl.schema import is_uniform_dict_array


# ---------------------------------------------------------------------------
# Schema detection
# ---------------------------------------------------------------------------

class TestIsUniformDictArray:
    def test_uniform(self):
        lst = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        assert is_uniform_dict_array(lst) is True

    def test_single_element_below_min(self):
        lst = [{"a": 1}]
        assert is_uniform_dict_array(lst) is False  # min_rows=2

    def test_single_element_above_min(self):
        lst = [{"a": 1}, {"a": 2}]
        assert is_uniform_dict_array(lst) is True

    def test_mixed_keys(self):
        lst = [{"a": 1}, {"b": 2}]
        assert is_uniform_dict_array(lst) is False

    def test_non_dict_elements(self):
        lst = ["hello", "world"]
        assert is_uniform_dict_array(lst) is False

    def test_empty_list(self):
        assert is_uniform_dict_array([]) is False

    def test_empty_dicts(self):
        lst = [{}, {}]
        assert is_uniform_dict_array(lst) is False

    def test_partial_uniform(self):
        lst = [{"a": 1, "b": 2}, {"a": 3, "b": 4}, {"a": 5, "c": 6}]
        assert is_uniform_dict_array(lst) is False


# ---------------------------------------------------------------------------
# Encode produces TONL magic
# ---------------------------------------------------------------------------

class TestEncodeBasics:
    def test_magic_header(self):
        result = encode({"x": 1})
        assert result.startswith(MAGIC)

    def test_scalar_int(self):
        assert decode(encode(42)) == 42

    def test_scalar_str(self):
        assert decode(encode("hello")) == "hello"

    def test_scalar_bool_true(self):
        assert decode(encode(True)) is True

    def test_scalar_bool_false(self):
        assert decode(encode(False)) is False

    def test_scalar_none(self):
        assert decode(encode(None)) is None

    def test_decimal(self):
        d = Decimal("3.14159")
        assert decode(encode(d)) == d

    def test_simple_dict(self):
        payload = {"key": "value", "number": 99}
        assert decode(encode(payload)) == payload

    def test_rejects_float(self):
        with pytest.raises(TONLValidationError, match="float"):
            encode({"cost": 1.5})

    def test_rejects_unknown_type(self):
        class Weird:
            pass
        with pytest.raises(TONLTypeError):
            encode(Weird())


# ---------------------------------------------------------------------------
# Uniform array → table compression
# ---------------------------------------------------------------------------

class TestUniformArrayTable:
    def test_messages_encoded_as_table(self):
        payload = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
            {"role": "user", "content": "bye"},
        ]
        encoded = encode(payload)
        assert "TABLE0:" in encoded
        decoded = decode(encoded)
        assert decoded == payload

    def test_round_trip_uniform_array(self, uniform_messages):
        encoded = encode({"messages": uniform_messages})
        decoded = decode(encoded)
        assert decoded == {"messages": uniform_messages}

    def test_table_is_smaller_than_json(self, uniform_messages):
        import json
        payload = {"messages": uniform_messages}
        tonl = encode(payload)
        json_size = len(json.dumps(payload, separators=(",", ":")))
        assert len(tonl) < json_size * 1.2  # TONL should be close to or smaller than JSON

    def test_nested_uniform_arrays(self):
        payload = {
            "batch1": [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}, {"id": 3, "val": "c"}],
            "batch2": [{"x": 10, "y": 20}, {"x": 30, "y": 40}, {"x": 50, "y": 60}],
        }
        assert decode(encode(payload)) == payload


# ---------------------------------------------------------------------------
# Special character escaping in cells
# ---------------------------------------------------------------------------

class TestCellEscaping:
    def test_pipe_in_content(self):
        payload = [
            {"col": "val|with|pipes"},
            {"col": "another|value"},
            {"col": "third"},
        ]
        assert decode(encode(payload)) == payload

    def test_newline_in_content(self):
        payload = [
            {"text": "line1\nline2"},
            {"text": "no newline"},
            {"text": "another\nnewline"},
        ]
        assert decode(encode(payload)) == payload

    def test_backslash_in_content(self):
        payload = [
            {"path": "C:\\Windows\\System32"},
            {"path": "/usr/local/bin"},
            {"path": "relative\\path"},
        ]
        assert decode(encode(payload)) == payload

    def test_sentinel_collision_escape(self):
        # String starting with @TONLT should be escaped and round-trip correctly
        payload = {"value": "@TONLT0_should_be_escaped"}
        assert decode(encode(payload)) == payload

    def test_decimal_sentinel_collision_escape(self):
        payload = {"value": "@TONLD123.45_should_be_escaped"}
        assert decode(encode(payload)) == payload


# ---------------------------------------------------------------------------
# Security limits
# ---------------------------------------------------------------------------

class TestSecurityLimits:
    def test_depth_limit(self):
        # Build deeply nested dict: depth=60 > MAX_NESTING_DEPTH=50
        payload: dict = {}
        node = payload
        for i in range(60):
            node["child"] = {}
            node = node["child"]
        with pytest.raises(TONLSecurityError, match="depth"):
            encode(payload)

    def test_string_size_limit(self):
        from praxis.kernel.compression.tonl.security import MAX_STRING_LEN
        big_str = "x" * (MAX_STRING_LEN + 1)
        with pytest.raises(TONLSecurityError):
            encode(big_str)

    def test_invalid_magic_header(self):
        with pytest.raises(TONLParseError, match="magic"):
            decode("NOTTONL1\n{}")

    def test_malformed_json_body(self):
        with pytest.raises(TONLParseError, match="malformed"):
            decode("TONL1\n{not valid json}")


# ---------------------------------------------------------------------------
# Decimal round-trip
# ---------------------------------------------------------------------------

class TestDecimalRoundTrip:
    def test_decimal_in_dict(self):
        d = {"cost": Decimal("0.0000050000"), "tokens": 100}
        assert decode(encode(d)) == d

    def test_decimal_in_table(self):
        rows = [
            {"amount": Decimal("1.23"), "label": "a"},
            {"amount": Decimal("4.56"), "label": "b"},
            {"amount": Decimal("7.89"), "label": "c"},
        ]
        assert decode(encode(rows)) == rows
