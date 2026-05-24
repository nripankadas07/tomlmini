"""Hard-edge parser behavior that keeps the common subset predictable."""

from __future__ import annotations

import pytest

import tomlmini


def test_whitespace_only_document_returns_empty_dict() -> None:
    assert tomlmini.loads(" \t  ") == {}


def test_array_of_tables_cannot_extend_inline_table() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("items = {name = 'x'}\n[[items]]\nname = 'y'\n")


def test_array_of_tables_cannot_reuse_direct_array_value() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("items = []\n[[items]]\nname = 'x'\n")


def test_dotted_key_requires_segment_after_dot() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a. = 1\n")


def test_unicode_escape_rejects_codepoints_outside_unicode_range() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads(r's = "\U00110000"')


def test_multiline_literal_string_trims_opening_crlf() -> None:
    assert tomlmini.loads("s = '''\r\nbody'''") == {"s": "body"}


def test_bad_boolean_prefix_is_not_accepted_as_atom() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("enabled = truthy\n")


def test_local_time_with_trailing_garbage_is_rejected() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("t = 12:00:00x\n")


def test_datetime_with_incomplete_time_is_rejected() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("dt = 2024-01-01T12\n")


def test_inline_table_entry_requires_equals() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("point = { x 1 }\n")


def test_inline_table_reuses_existing_dotted_parent() -> None:
    assert tomlmini.loads("point = { x.y = 1, x.z = 2 }\n") == {
        "point": {"x": {"y": 1, "z": 2}}
    }


def test_inline_table_rejects_duplicate_nested_leaf() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("point = { x.y = 1, x.y.z = 2 }\n")


def test_table_header_cannot_extend_inline_table_child() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = { b = { c = 1 } }\n[a.b]\nd = 2\n")


def test_table_header_cannot_descend_through_empty_array() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = []\n[a.b]\nc = 1\n")


def test_table_header_cannot_descend_through_scalar() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = 1\n[a.b]\nc = 1\n")
