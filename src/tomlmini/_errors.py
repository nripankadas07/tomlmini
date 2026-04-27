"""Exception hierarchy for tomlmini."""

from __future__ import annotations


class TomlError(Exception):
    """Base class for all tomlmini errors."""


class ParseError(TomlError):
    """Raised when the TOML input cannot be parsed.

    The error message includes the 1-based line and column where the
    problem was detected, plus a short human-readable description.
    """

    def __init__(self, message: str, *, line: int, col: int) -> None:
        self.line = line
        self.col = col
        super().__init__(f"line {line}, column {col}: {message}")


__all__ = ["TomlError", "ParseError"]
