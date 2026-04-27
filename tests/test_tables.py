"""Table, sub-table, array-of-tables and inline-table tests."""

from __future__ import annotations

import pytest

import tomlmini


def test_simple_table() -> None:
    text = """
[server]
host = "localhost"
port = 8080
"""
    assert tomlmini.loads(text) == {
        "server": {"host": "localhost", "port": 8080}
    }


def test_subtable_with_dotted_header() -> None:
    text = """
[a.b.c]
x = 1
"""
    assert tomlmini.loads(text) == {"a": {"b": {"c": {"x": 1}}}}


def test_table_after_top_level_keys() -> None:
    text = """
title = "demo"

[section]
value = 1
"""
    assert tomlmini.loads(text) == {
        "title": "demo",
        "section": {"value": 1},
    }


def test_array_of_tables() -> None:
    text = """
[[items]]
name = "first"

[[items]]
name = "second"
"""
    assert tomlmini.loads(text) == {
        "items": [{"name": "first"}, {"name": "second"}]
    }


def test_array_of_tables_with_subtable() -> None:
    text = """
[[items]]
name = "first"

[items.config]
flag = true

[[items]]
name = "second"
"""
    parsed = tomlmini.loads(text)
    assert parsed == {
        "items": [
            {"name": "first", "config": {"flag": True}},
            {"name": "second"},
        ]
    }


def test_inline_table() -> None:
    text = 'point = { x = 1, y = 2 }'
    assert tomlmini.loads(text) == {"point": {"x": 1, "y": 2}}


def test_inline_table_empty() -> None:
    assert tomlmini.loads("p = {}") == {"p": {}}


def test_inline_table_with_dotted_key() -> None:
    text = 'p = { a.b = 1, c = 2 }'
    assert tomlmini.loads(text) == {"p": {"a": {"b": 1}, "c": 2}}


def test_inline_table_trailing_comma_rejected() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("p = {x = 1,}")


def test_inline_table_unterminated_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("p = {x = 1")


def test_inline_table_duplicate_key_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("p = {x = 1, x = 2}")


def test_inline_table_cannot_be_extended_via_table_header() -> None:
    text = """
p = { x = 1 }
[p]
y = 2
"""
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads(text)


def test_inline_table_cannot_be_extended_via_dotted_key() -> None:
    text = """
p = { x = 1 }
p.y = 2
"""
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads(text)


def test_table_redefinition_rejected() -> None:
    text = """
[a]
x = 1
[a]
y = 2
"""
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads(text)


def test_implicit_table_can_be_completed_by_header() -> None:
    text = """
[a.b]
x = 1
[a]
y = 2
"""
    assert tomlmini.loads(text) == {"a": {"b": {"x": 1}, "y": 2}}


def test_array_of_tables_redefinition_as_value_rejected() -> None:
    text = """
items = 1
[[items]]
x = 1
"""
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads(text)


def test_dotted_key_into_array_of_tables_targets_last_table() -> None:
    text = """
[[items]]
[[items]]
sub.x = 1
"""
    parsed = tomlmini.loads(text)
    # Dotted keys inside ``[[items]]`` are interpreted relative to the
    # most recently created array-of-tables element.
    assert parsed == {"items": [{}, {"sub": {"x": 1}}]}


def test_quoted_keys_in_inline_table() -> None:
    text = 'p = { "with space" = 1 }'
    assert tomlmini.loads(text) == {"p": {"with space": 1}}


def test_table_header_missing_close_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("[[a")


def test_table_header_must_end_line() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("[a] x = 1")
