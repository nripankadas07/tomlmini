"""String parsing tests (basic, literal, multi-line, escapes)."""

from __future__ import annotations

import pytest

import tomlmini


def test_basic_string_simple() -> None:
    assert tomlmini.loads('s = "hello"') == {"s": "hello"}


def test_basic_string_escape_sequences() -> None:
    text = r's = "tab\there\nnewline"'
    assert tomlmini.loads(text) == {"s": "tab\there\nnewline"}


def test_basic_string_unicode_short_escape() -> None:
    text = r's = "éclair"'
    assert tomlmini.loads(text) == {"s": "éclair"}


def test_basic_string_unicode_long_escape() -> None:
    text = r's = "\U0001F600"'
    assert tomlmini.loads(text) == {"s": "\U0001f600"}


def test_basic_string_quote_escape() -> None:
    text = r's = "say \"hi\""'
    assert tomlmini.loads(text) == {"s": 'say "hi"'}


def test_basic_string_backslash_escape() -> None:
    text = r's = "C:\\Users"'
    assert tomlmini.loads(text) == {"s": r"C:\Users"}


def test_basic_string_form_feed_and_backspace() -> None:
    text = r's = "\f and \b"'
    assert tomlmini.loads(text) == {"s": "\f and \b"}


def test_basic_string_invalid_escape_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads(r's = "\q"')


def test_basic_string_invalid_unicode_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads(r's = "\uZZZZ"')


def test_basic_string_short_unicode_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads(r's = "\u12"')


def test_basic_string_unterminated_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads('s = "no end')


def test_basic_string_newline_in_single_line_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads('s = "first\nsecond"')


def test_literal_string_simple() -> None:
    assert tomlmini.loads("s = 'hello'") == {"s": "hello"}


def test_literal_string_no_escapes() -> None:
    text = r"s = 'C:\Users\name'"
    assert tomlmini.loads(text) == {"s": r"C:\Users\name"}


def test_literal_string_unterminated_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("s = 'no end")


def test_literal_string_newline_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("s = 'a\nb'")


def test_multiline_basic_string_preserves_newlines() -> None:
    text = 's = """\nfirst\nsecond"""'
    assert tomlmini.loads(text) == {"s": "first\nsecond"}


def test_multiline_basic_string_first_newline_trimmed() -> None:
    text = 's = """\nhello"""'
    assert tomlmini.loads(text) == {"s": "hello"}


def test_multiline_basic_string_no_newline_after_open() -> None:
    text = 's = """hello"""'
    assert tomlmini.loads(text) == {"s": "hello"}


def test_multiline_basic_string_line_ending_backslash_eats_whitespace() -> None:
    text = 's = """\\\n  one \\\n  two"""'
    assert tomlmini.loads(text) == {"s": "one two"}


def test_multiline_basic_string_internal_quotes_allowed() -> None:
    text = 's = """one"two\'three"""'
    assert tomlmini.loads(text) == {"s": "one\"two'three"}


def test_multiline_basic_string_trailing_quotes_kept() -> None:
    text = 's = """foo""""'
    assert tomlmini.loads(text) == {"s": 'foo"'}


def test_multiline_basic_string_unterminated_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads('s = """oops')


def test_multiline_literal_string_preserves_everything() -> None:
    text = "s = '''\\n stays literal'''"
    assert tomlmini.loads(text) == {"s": "\\n stays literal"}


def test_multiline_literal_string_first_newline_trimmed() -> None:
    text = "s = '''\nbody'''"
    assert tomlmini.loads(text) == {"s": "body"}


def test_multiline_literal_string_unterminated_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("s = '''oops")


def test_multiline_literal_string_trailing_quotes_kept() -> None:
    text = "s = '''foo''''"
    assert tomlmini.loads(text) == {"s": "foo'"}


def test_string_in_quoted_key() -> None:
    text = '"weird.key" = "value"'
    assert tomlmini.loads(text) == {"weird.key": "value"}


def test_dangling_escape_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads('s = "abc\\')


def test_multiline_basic_crlf_after_open_trimmed() -> None:
    text = 's = """\r\nbody"""'
    assert tomlmini.loads(text) == {"s": "body"}
