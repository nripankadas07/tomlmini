"""Array value tests."""

from __future__ import annotations

import pytest

import tomlmini


def test_empty_array() -> None:
    assert tomlmini.loads("a = []") == {"a": []}


def test_array_of_integers() -> None:
    assert tomlmini.loads("a = [1, 2, 3]") == {"a": [1, 2, 3]}


def test_array_of_strings() -> None:
    assert tomlmini.loads('a = ["x", "y"]') == {"a": ["x", "y"]}


def test_nested_arrays() -> None:
    assert tomlmini.loads("a = [[1, 2], [3, 4]]") == {"a": [[1, 2], [3, 4]]}


def test_mixed_value_array() -> None:
    parsed = tomlmini.loads('a = [1, "two", 3.0, true]')
    assert parsed == {"a": [1, "two", 3.0, True]}


def test_array_with_trailing_comma() -> None:
    assert tomlmini.loads("a = [1, 2, 3,]") == {"a": [1, 2, 3]}


def test_array_spans_multiple_lines() -> None:
    text = """
a = [
  1,
  2,
  3,
]
"""
    assert tomlmini.loads(text) == {"a": [1, 2, 3]}


def test_array_with_inline_comments() -> None:
    text = """
a = [
  1, # one
  2, # two
]
"""
    assert tomlmini.loads(text) == {"a": [1, 2]}


def test_array_unterminated_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = [1, 2")


def test_array_missing_comma_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = [1 2]")


def test_array_with_inline_table_elements() -> None:
    parsed = tomlmini.loads("a = [{x = 1}, {x = 2}]")
    assert parsed == {"a": [{"x": 1}, {"x": 2}]}


def test_array_of_booleans() -> None:
    assert tomlmini.loads("a = [true, false, true]") == {
        "a": [True, False, True]
    }


def test_array_in_nested_key() -> None:
    parsed = tomlmini.loads('s.list = ["a", "b"]')
    assert parsed == {"s": {"list": ["a", "b"]}}
