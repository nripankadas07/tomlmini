"""Spec-backed checks against Python's standard TOML parser."""

from __future__ import annotations

from datetime import date, datetime, time, timezone

import pytest

import tomlmini

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10 CI
    import tomli as tomllib


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("title = 'TOML Example'\n", {"title": "TOML Example"}),
        ("fruit.apple.color = 'red'\nfruit.apple.taste.sweet = true\n", None),
        ("points = [{ x = 1, y = 2 }, { x = 3, y = 4 }]\n", None),
        ("d = 1979-05-27\nt = 07:32:00\ndt = 1979-05-27T07:32:00Z\n", None),
        ("hex = 0xDEAD_BEEF\noct = 0o755\nbin = 0b1101_0010\n", None),
    ],
)
def test_matches_tomllib_for_supported_toml(
    source: str, expected: dict[str, object] | None
) -> None:
    parsed = tomlmini.loads(source)
    assert parsed == tomllib.loads(source)
    if expected is not None:
        assert parsed == expected


def test_toml_type_mapping_is_standard() -> None:
    parsed = tomlmini.loads(
        """
enabled = true
count = 42
ratio = 1.25
born = 1979-05-27
alarm = 07:32:00
seen = 1979-05-27T07:32:00Z
"""
    )

    assert isinstance(parsed["enabled"], bool)
    assert isinstance(parsed["count"], int)
    assert isinstance(parsed["ratio"], float)
    assert parsed["born"] == date(1979, 5, 27)
    assert parsed["alarm"] == time(7, 32)
    assert parsed["seen"] == datetime(1979, 5, 27, 7, 32, tzinfo=timezone.utc)


def test_rejects_invalid_inputs_that_tomllib_rejects() -> None:
    invalid = [
        "key = 007",
        "key = 1__000",
        "key = \"unterminated",
        "[table]\n[table]\n",
    ]

    for source in invalid:
        with pytest.raises(tomlmini.ParseError):
            tomlmini.loads(source)
        with pytest.raises(tomllib.TOMLDecodeError):
            tomllib.loads(source)
