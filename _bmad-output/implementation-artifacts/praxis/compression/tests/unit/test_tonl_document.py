"""Unit tests — TONLDocument query/mutation API.

Covers: TONLDocument.parse, query (plain key, nested, wildcard, index),
        insert, delete, to_text, and the _resolve helper edge cases.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from praxis.kernel.compression.tonl.document import TONLDocument
from praxis.kernel.compression.tonl.errors import TONLParseError
from praxis.kernel.compression.tonl.encode import encode
from praxis.kernel.compression.tonl.decode import decode


# ---------------------------------------------------------------------------
# Construction & parse
# ---------------------------------------------------------------------------

class TestTONLDocumentConstruct:
    def test_parse_from_dict(self):
        payload = {"a": 1, "b": "hello"}
        text = encode(payload)
        doc = TONLDocument.parse(text)
        assert doc.data == payload

    def test_parse_from_list(self):
        payload = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
        text = encode(payload)
        doc = TONLDocument.parse(text)
        assert doc.data == payload

    def test_data_property(self):
        doc = TONLDocument({"x": 42})
        assert doc.data == {"x": 42}

    def test_parse_invalid_text_raises(self):
        with pytest.raises(Exception):
            TONLDocument.parse("this is not valid TONL")


# ---------------------------------------------------------------------------
# query — plain key
# ---------------------------------------------------------------------------

class TestTONLDocumentQueryPlainKey:
    def test_top_level_key(self):
        doc = TONLDocument({"name": "alice", "age": 30})
        assert doc.query("name") == ["alice"]

    def test_missing_key_returns_empty(self):
        doc = TONLDocument({"a": 1})
        assert doc.query("b") == []

    def test_query_on_non_dict_root(self):
        doc = TONLDocument([1, 2, 3])
        assert doc.query("x") == []

    def test_nested_key_traversal(self):
        doc = TONLDocument({"outer": {"inner": "value"}})
        assert doc.query("outer.inner") == ["value"]

    def test_deep_nested_key(self):
        doc = TONLDocument({"a": {"b": {"c": 99}}})
        assert doc.query("a.b.c") == [99]

    def test_missing_intermediate_key(self):
        doc = TONLDocument({"a": {"b": 1}})
        assert doc.query("a.c.d") == []


# ---------------------------------------------------------------------------
# query — wildcard and index
# ---------------------------------------------------------------------------

class TestTONLDocumentQueryWildcard:
    def test_wildcard_returns_all_items(self):
        doc = TONLDocument({"items": [1, 2, 3]})
        assert doc.query("items[*]") == [1, 2, 3]

    def test_wildcard_nested_field(self):
        doc = TONLDocument({
            "messages": [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
            ]
        })
        result = doc.query("messages[*].role")
        assert result == ["user", "assistant"]

    def test_wildcard_on_non_list(self):
        doc = TONLDocument({"items": "not a list"})
        assert doc.query("items[*]") == []

    def test_index_zero(self):
        doc = TONLDocument({"msgs": [{"role": "user"}, {"role": "assistant"}]})
        assert doc.query("msgs[0].role") == ["user"]

    def test_index_last(self):
        doc = TONLDocument({"msgs": [{"role": "user"}, {"role": "assistant"}]})
        assert doc.query("msgs[1].role") == ["assistant"]

    def test_index_out_of_range(self):
        doc = TONLDocument({"msgs": [{"role": "user"}]})
        assert doc.query("msgs[5]") == []

    def test_index_on_non_list(self):
        doc = TONLDocument({"items": "string"})
        assert doc.query("items[0]") == []

    def test_empty_path_returns_empty(self):
        doc = TONLDocument({"a": 1})
        # "".split(".") == [""] — looks up key "" which doesn't exist
        result = doc.query("")
        assert result == []


# ---------------------------------------------------------------------------
# insert
# ---------------------------------------------------------------------------

class TestTONLDocumentInsert:
    def test_insert_new_key(self):
        doc = TONLDocument({"a": 1})
        doc.insert("a", 99)
        assert doc.data["a"] == 99

    def test_insert_nested_key(self):
        doc = TONLDocument({"outer": {"inner": 1}})
        doc.insert("outer.inner", 42)
        assert doc.data["outer"]["inner"] == 42

    def test_insert_path_not_found_raises(self):
        doc = TONLDocument({"a": 1})
        with pytest.raises(TONLParseError):
            doc.insert("x.y", 99)

    def test_insert_on_non_dict_parent_raises(self):
        doc = TONLDocument({"a": [1, 2, 3]})
        with pytest.raises(TONLParseError):
            doc.insert("a.b", 99)


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestTONLDocumentDelete:
    def test_delete_key(self):
        doc = TONLDocument({"a": 1, "b": 2})
        doc.delete("a")
        assert "a" not in doc.data

    def test_delete_nested_key(self):
        doc = TONLDocument({"outer": {"inner": 1, "other": 2}})
        doc.delete("outer.inner")
        assert "inner" not in doc.data["outer"]
        assert doc.data["outer"]["other"] == 2

    def test_delete_missing_path_raises(self):
        doc = TONLDocument({"a": 1})
        with pytest.raises(TONLParseError):
            doc.delete("x.y")

    def test_delete_missing_key_raises(self):
        doc = TONLDocument({"a": 1})
        with pytest.raises(TONLParseError):
            doc.delete("b")


# ---------------------------------------------------------------------------
# to_text / round-trip
# ---------------------------------------------------------------------------

class TestTONLDocumentToText:
    def test_to_text_round_trips_dict(self):
        original = {"session": "s1", "count": 5}
        doc = TONLDocument(original)
        text = doc.to_text()
        recovered = decode(text)
        assert recovered == original

    def test_to_text_after_mutation(self):
        doc = TONLDocument({"a": 1, "b": 2})
        doc.insert("a", 99)
        text = doc.to_text()
        recovered = decode(text)
        assert recovered["a"] == 99

    def test_to_text_round_trips_table(self):
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "world"},
            {"role": "user", "content": "foo"},
        ]
        doc = TONLDocument(messages)
        text = doc.to_text()
        recovered = decode(text)
        assert recovered == messages

    def test_to_text_with_decimal(self):
        doc = TONLDocument({"cost": Decimal("1.23")})
        text = doc.to_text()
        recovered = decode(text)
        assert recovered["cost"] == Decimal("1.23")
