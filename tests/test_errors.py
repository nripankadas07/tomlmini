"""Error handling tests."""

from __future__ import annotations

import pytest

import tomlmini


def test_parse_error_records_line_and_column() -> None:
    with pytest.raises(tomlmini.ParseError) as info:
        tomlmini.loads("a = 1\nb = ?")
    assert info.value.line == 2
    assert info.value.col >= 1
    assert "line 2" in str(info.value)


def test_duplicate_key_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = 1\na = 2")


def test_assigning_into_value_raises() -> None:
    text = """
a = 1
a.b = 2
"""
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads(text)


def test_value_required_after_equals() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a =\n")


def test_missing_equals_in_pair_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a 1")


def test_missing_value_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = ")


def test_garbage_after_value_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = 1 garbage")


def test_garbage_after_string_value_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads('a = "x" extra')


def test_table_header_with_value_after_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("[a] = 1")


def test_unknown_atom_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = ?")


def test_redefining_table_as_value_raises() -> None:
    text = """
[a]
x = 1
a = 2
"""
    # 'a' is a key inside the [a] table here so it's actually fine —
    # the equivalent of mapping a.a = 2.  But trying to assign at the
    # root would conflict.  This case stays valid.
    parsed = tomlmini.loads(text)
    assert parsed == {"a": {"x": 1, "a": 2}}


def test_assigning_into_table_after_header_conflicts() -> None:
    text = """
[a]
x = 1
[b]
a = 1
a.deep = 2
"""
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads(text)


def test_duplicate_key_inside_table_raises() -> None:
    text = """
[a]
x = 1
x = 2
"""
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads(text)


def test_dotted_key_through_inline_table_raises() -> None:
    text = """
[a]
b = { c = 1 }
b.d = 2
"""
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads(text)


def test_string_key_with_invalid_escape_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads('"\\q" = 1')


def test_inline_table_descends_into_value_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("p = { a = 1, a.b = 2 }")
