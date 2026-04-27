"""Datetime / date / time parsing tests."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import pytest

import tomlmini


def test_local_date() -> None:
    assert tomlmini.loads("d = 2026-04-26") == {"d": date(2026, 4, 26)}


def test_local_time() -> None:
    assert tomlmini.loads("t = 13:45:30") == {"t": time(13, 45, 30)}


def test_local_time_with_microseconds() -> None:
    parsed = tomlmini.loads("t = 13:45:30.500000")
    assert parsed["t"] == time(13, 45, 30, 500000)


def test_local_datetime() -> None:
    assert tomlmini.loads("dt = 2026-04-26T13:45:30") == {
        "dt": datetime(2026, 4, 26, 13, 45, 30)
    }


def test_local_datetime_with_space_separator() -> None:
    assert tomlmini.loads("dt = 2026-04-26 13:45:30") == {
        "dt": datetime(2026, 4, 26, 13, 45, 30)
    }


def test_offset_datetime_z() -> None:
    parsed = tomlmini.loads("dt = 2026-04-26T13:45:30Z")
    assert parsed["dt"] == datetime(2026, 4, 26, 13, 45, 30, 0, timezone.utc)


def test_offset_datetime_plus_offset() -> None:
    parsed = tomlmini.loads("dt = 2026-04-26T13:45:30+05:30")
    expected = datetime(
        2026, 4, 26, 13, 45, 30, 0, timezone(timedelta(hours=5, minutes=30))
    )
    assert parsed["dt"] == expected


def test_offset_datetime_negative_offset() -> None:
    parsed = tomlmini.loads("dt = 2026-04-26T13:45:30-08:00")
    expected = datetime(
        2026, 4, 26, 13, 45, 30, 0, timezone(timedelta(hours=-8))
    )
    assert parsed["dt"] == expected


def test_datetime_with_fractional_seconds() -> None:
    parsed = tomlmini.loads("dt = 2026-04-26T13:45:30.123Z")
    assert parsed["dt"] == datetime(
        2026, 4, 26, 13, 45, 30, 123000, timezone.utc
    )


def test_invalid_date_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("d = 2026-13-40")


def test_invalid_time_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("t = 25:00:00")


def test_invalid_datetime_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("dt = 2026-04-26T25:00:00")


def test_malformed_date_token_raises() -> None:
    with pytest.raises(tomlmini.ParseError):
        tomlmini.loads("d = 2026-04-26X")
