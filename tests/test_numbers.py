"""Integer / float parsing tests."""

from __future__ import annotations

import math

import pytest

import tomlmini


def test_integer_zero() -> None:
    assert tomlmini.loads("a = 0") == {"a": 0}


def test_integer_positive_and_negative() -> None:
    assert tomlmini.loads("a = 42\nb = -7") == {"a": 42, "b": -7}


def test_integer_with_underscores() -> None:
    assert tomlmini.loads("a = 1_000_000") == {"a": 1_000_000}


def test_integer_explicit_plus_sign() -> None:
    assert tomlmini.loads("a = +12") == {"a": 12}


def test_integer_hex() -> None:
    assert tomlmini.loads("a = 0xff\nb = 0xDEAD_BEEF") == {
        "a": 255,
        "b": 0xDEADBEEF,
    }


def test_integer_octal() -> None:
    assert tomlmini.loads("a = 0o755") == {"a": 0o755}


def test_integer_binary() -> None:
    assert tomlmini.loads("a = 0b1010_1010") == {"a": 0b10101010}


def test_float_simple() -> None:
    assert tomlmini.loads("a = 1.5") == {"a": 1.5}


def test_float_with_underscores() -> None:
    assert tomlmini.loads("a = 1_000.5") == {"a": 1000.5}


def test_float_with_exponent() -> None:
    assert tomlmini.loads("a = 6.022e23") == {"a": 6.022e23}


def test_float_negative_exponent() -> None:
    assert tomlmini.loads("a = 1.5e-3") == {"a": 0.0015}


def test_float_inf_positive() -> None:
    assert tomlmini.loads("a = inf")["a"] == float("inf")


def test_float_inf_negative() -> None:
    assert tomlmini.loads("a = -inf")["a"] == float("-inf")


def test_float_inf_explicit_plus() -> None:
    assert tomlmini.loads("a = +inf")["a"] == float("inf")


def test_float_nan() -> None:
    assert math.isnan(tomlmini.loads("a = nan")["a"])


def test_float_signed_nan() -> None:
    assert math.isnan(tomlmini.loads("a = +nan")["a"])
    assert math.isnan(tomlmini.loads("a = -nan")["a"])


def test_invalid_number_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = 12abc")


def test_integer_leading_zero_rejected() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = 007")


def test_empty_value_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a =")


def test_hex_uppercase_prefix_rejected() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = 0X10")


def test_double_underscore_in_integer_rejected() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = 1__000")


def test_trailing_underscore_in_integer_rejected() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("a = 1_")
