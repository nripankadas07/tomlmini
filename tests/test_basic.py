"""Basic key/value and module-level tests."""

from __future__ import annotations

import os

import pytest

import tomlmini


def test_module_exports_public_names() -> None:
    assert tomlmini.__version__
    assert callable(tomlmini.loads)
    assert callable(tomlmini.load)
    assert issubclass(tomlmini.ParseError, tomlmini.TomlError)


def test_loads_empty_input_returns_empty_dict() -> None:
    assert tomlmini.loads("") == {}


def test_loads_blank_lines_returns_empty_dict() -> None:
    assert tomlmini.loads("\n\n   \n\t\n") == {}


def test_loads_only_comments_returns_empty_dict() -> None:
    text = "# hello\n# world\n  # indented\n"
    assert tomlmini.loads(text) == {}


def test_loads_single_string_pair() -> None:
    assert tomlmini.loads('name = "alice"') == {"name": "alice"}


def test_loads_multiple_pairs() -> None:
    text = '\n'.join(['a = 1', 'b = 2', 'c = "three"'])
    assert tomlmini.loads(text) == {"a": 1, "b": 2, "c": "three"}


def test_loads_handles_trailing_newline() -> None:
    assert tomlmini.loads("a = 1\n") == {"a": 1}


def test_loads_handles_crlf_newlines() -> None:
    assert tomlmini.loads("a = 1\r\nb = 2\r\n") == {"a": 1, "b": 2}


def test_loads_inline_comment_after_value() -> None:
    assert tomlmini.loads('x = 1 # trailing comment') == {"x": 1}


def test_loads_strips_bom() -> None:
    text = "﻿foo = 'bar'"
    assert tomlmini.loads(text) == {"foo": "bar"}


def test_loads_rejects_non_string_input() -> None:
    with pytest.raises(TypeError):
        tomlmini.loads(b"x = 1")  # type: ignore[arg-type]


def test_loads_bare_keys_charset() -> None:
    text = "the-key_99 = 1\n"
    assert tomlmini.loads(text) == {"the-key_99": 1}


def test_loads_quoted_keys() -> None:
    text = '"hello world" = 1\n\'literal key\' = 2\n'
    assert tomlmini.loads(text) == {"hello world": 1, "literal key": 2}


def test_loads_dotted_keys_create_nested_tables() -> None:
    text = 'a.b.c = 1\na.b.d = 2\n'
    assert tomlmini.loads(text) == {"a": {"b": {"c": 1, "d": 2}}}


def test_load_reads_file(tmp_path) -> None:
    p = tmp_path / "config.toml"
    p.write_text("name = 'forge'\nport = 8080\n", encoding="utf-8")
    assert tomlmini.load(p) == {"name": "forge", "port": 8080}


def test_load_accepts_pathlike_str(tmp_path) -> None:
    p = tmp_path / "config.toml"
    p.write_text("a = 1\n", encoding="utf-8")
    assert tomlmini.load(os.fspath(p)) == {"a": 1}


def test_load_supports_alternate_encoding(tmp_path) -> None:
    p = tmp_path / "config.toml"
    p.write_bytes("name = 'naïve'\n".encode("latin-1"))
    assert tomlmini.load(p, encoding="latin-1") == {"name": "naïve"}


def test_load_rejects_empty_encoding(tmp_path) -> None:
    with pytest.raises(TypeError):
        tomlmini.load(tmp_path / "x.toml", encoding="")


def test_load_rejects_non_str_encoding(tmp_path) -> None:
    with pytest.raises(TypeError):
        tomlmini.load(tmp_path / "x.toml", encoding=123)  # type: ignore[arg-type]
