"""Core TOML parser.

Implements the common subset of TOML v1.0:

- Comments (``# ...``)
- Bare and quoted keys; dotted keys
- Strings: basic, literal, and both multi-line variants
- Integers (decimal / hex / octal / binary, with ``_`` separators)
- Floats (with exponents, ``inf`` and ``nan``)
- Booleans
- Datetimes: offset datetime, local datetime, local date, local time
- Arrays
- Inline tables ``{ a = 1, b = 2 }``
- Tables ``[name]`` and arrays of tables ``[[name]]``

It deliberately rejects pathological dotted-key + table redefinitions
that the full TOML 1.0 spec normalises away — the goal is a small,
predictable parser for everyday config files.
"""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from ._errors import ParseError


# ---------------------------------------------------------------------------
# helpers


_BARE_KEY_RE = re.compile(r"[A-Za-z0-9_-]+")
_INT_DEC_RE = re.compile(r"[+-]?(?:0|[1-9](?:_?[0-9])*)$")
_INT_HEX_RE = re.compile(r"0x[0-9A-Fa-f](?:_?[0-9A-Fa-f])*$")
_INT_OCT_RE = re.compile(r"0o[0-7](?:_?[0-7])*$")
_INT_BIN_RE = re.compile(r"0b[01](?:_?[01])*$")

_FLOAT_RE = re.compile(
    r"""
    ^[+-]?
    (?:0|[1-9](?:_?[0-9])*)
    (?:
        \.[0-9](?:_?[0-9])*
    )?
    (?:
        [eE][+-]?[0-9](?:_?[0-9])*
    )?
    $
    """,
    re.VERBOSE,
)

_DATETIME_RE = re.compile(
    r"""
    ^
    (\d{4})-(\d{2})-(\d{2})
    (?:
        [T\ ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?
        (Z|[+-]\d{2}:\d{2})?
    )?
    $
    """,
    re.VERBOSE,
)

_TIME_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?$")


_BASIC_ESCAPES = {
    '"': '"',
    "\\": "\\",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


# ---------------------------------------------------------------------------
# scanner


class _Scanner:
    """Single-pass character scanner with line / column tracking."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1

    # -- low-level position primitives ------------------------------------

    def eof(self) -> bool:
        return self.pos >= len(self.text)

    def peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx >= len(self.text):
            return ""
        return self.text[idx]

    def starts_with(self, literal: str) -> bool:
        return self.text.startswith(literal, self.pos)

    def advance(self, count: int = 1) -> str:
        chunk = self.text[self.pos : self.pos + count]
        for ch in chunk:
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
        self.pos += count
        return chunk

    # -- whitespace & comments --------------------------------------------

    def skip_inline_ws(self) -> None:
        while not self.eof() and self.peek() in " \t":
            self.advance()

    def skip_inline_ws_and_comment(self) -> None:
        self.skip_inline_ws()
        if not self.eof() and self.peek() == "#":
            while not self.eof() and self.peek() != "\n":
                self.advance()

    def consume_newline(self) -> bool:
        if self.eof():
            return False
        if self.peek() == "\n":
            self.advance()
            return True
        if self.peek() == "\r" and self.peek(1) == "\n":
            self.advance(2)
            return True
        return False

    # -- error helper ------------------------------------------------------

    def error(self, message: str) -> ParseError:
        return ParseError(message, line=self.line, col=self.col)


# ---------------------------------------------------------------------------
# parser


class _Parser:
    """Drives the scanner and builds the resulting Python dict."""

    def __init__(self, text: str) -> None:
        # Normalise BOM.
        if text.startswith("﻿"):
            text = text[1:]
        self.scan = _Scanner(text)
        self.root: dict[str, Any] = {}
        # Tables that were declared with [name] or [[name]] headers.
        self._declared: set[tuple[str, ...]] = set()
        # Keys whose value was set directly (cannot be re-declared).
        self._direct: set[tuple[str, ...]] = set()
        # Tables created implicitly by dotted keys (cannot be redeclared
        # as ordinary [tables], but may host further keys).
        self._implicit: set[tuple[str, ...]] = set()
        # Tables that came from inline {} literals (immutable).
        self._inline: set[tuple[str, ...]] = set()
        # Path of the current [table] header (None means root).
        self._current_path: tuple[str, ...] = ()
        # Side channel for `_parse_value` to flag when the value it just
        # produced came from an inline-table literal.
        self._last_value_was_inline: bool = False

    # -- top-level ---------------------------------------------------------

    def parse(self) -> dict[str, Any]:
        s = self.scan
        while not s.eof():
            s.skip_inline_ws()
            if s.eof():
                break
            ch = s.peek()
            if ch == "#":
                s.skip_inline_ws_and_comment()
            elif ch in "\r\n":
                s.consume_newline()
            elif ch == "[":
                self._parse_table_header()
            else:
                self._parse_key_value()
                s.skip_inline_ws_and_comment()
                if not s.eof() and not self._at_line_break():
                    raise s.error("expected newline after key/value")
                s.consume_newline()
        return self.root

    def _at_line_break(self) -> bool:
        ch = self.scan.peek()
        return ch == "\n" or (ch == "\r" and self.scan.peek(1) == "\n")

    # -- table headers -----------------------------------------------------

    def _parse_table_header(self) -> None:
        s = self.scan
        is_array = s.starts_with("[[")
        s.advance(2 if is_array else 1)
        s.skip_inline_ws()
        path = self._parse_key_path()
        s.skip_inline_ws()
        closing = "]]" if is_array else "]"
        if not s.starts_with(closing):
            raise s.error(f"expected '{closing}' to close table header")
        s.advance(len(closing))
        s.skip_inline_ws_and_comment()
        if not s.eof() and not self._at_line_break():
            raise s.error("expected newline after table header")
        s.consume_newline()
        if is_array:
            self._open_array_table(path)
        else:
            self._open_table(path)

    def _open_table(self, path: tuple[str, ...]) -> None:
        if path in self._declared and path not in self._implicit:
            raise self.scan.error(
                f"table '{'.'.join(path)}' already defined"
            )
        if path in self._inline:
            raise self.scan.error(
                f"cannot extend inline table '{'.'.join(path)}'"
            )
        node = self._descend_path(path, for_table_header=True)
        if not isinstance(node, dict):
            raise self.scan.error(
                f"key '{'.'.join(path)}' has a non-table value"
            )
        self._declared.add(path)
        self._implicit.discard(path)
        self._current_path = path

    def _open_array_table(self, path: tuple[str, ...]) -> None:
        if path in self._inline:
            raise self.scan.error(
                f"cannot extend inline table '{'.'.join(path)}'"
            )
        parent = self._descend_path(path[:-1], for_table_header=True)
        if not isinstance(parent, dict):
            raise self.scan.error(
                f"key '{'.'.join(path[:-1])}' has a non-table value"
            )
        last = path[-1]
        existing = parent.get(last)
        if existing is None:
            arr: list[dict[str, Any]] = []
            parent[last] = arr
        elif isinstance(existing, list):
            arr = existing
            if path in self._direct:
                raise self.scan.error(
                    f"cannot redefine value '{'.'.join(path)}' as array of tables"
                )
        else:
            raise self.scan.error(
                f"cannot redefine '{'.'.join(path)}' as array of tables"
            )
        new_table: dict[str, Any] = {}
        arr.append(new_table)
        self._declared.add(path)
        # Each new array element starts with a clean slate so that keys
        # like ``name`` can be reused inside successive ``[[table]]``
        # blocks without colliding with the previous element's entries.
        self._forget_descendants(path)
        self._current_path = path

    # -- key/value pairs ---------------------------------------------------

    def _parse_key_value(self) -> None:
        s = self.scan
        path = self._parse_key_path()
        s.skip_inline_ws()
        if s.peek() != "=":
            raise s.error("expected '=' after key")
        s.advance()
        s.skip_inline_ws()
        self._last_value_was_inline = False
        value = self._parse_value()
        full_path = self._current_path + path
        self._assign(full_path, value)
        if self._last_value_was_inline and isinstance(value, dict):
            self._mark_inline_recursive(full_path, value)
        self._last_value_was_inline = False

    def _mark_inline_recursive(
        self, path: tuple[str, ...], value: dict[str, Any]
    ) -> None:
        self._inline.add(path)
        for key, sub in value.items():
            if isinstance(sub, dict):
                self._mark_inline_recursive(path + (key,), sub)

    def _forget_descendants(self, prefix: tuple[str, ...]) -> None:
        n = len(prefix)
        self._direct = {p for p in self._direct if not (len(p) > n and p[:n] == prefix)}
        self._declared = {p for p in self._declared if not (len(p) > n and p[:n] == prefix)}
        self._implicit = {p for p in self._implicit if not (len(p) > n and p[:n] == prefix)}
        self._inline = {p for p in self._inline if not (len(p) > n and p[:n] == prefix)}

    def _assign(self, full_path: tuple[str, ...], value: Any) -> None:
        if full_path in self._direct:
            raise self.scan.error(
                f"key '{'.'.join(full_path)}' already defined"
            )
        if full_path in self._declared:
            raise self.scan.error(
                f"key '{'.'.join(full_path)}' conflicts with a table"
            )
        # Walk to the parent, creating implicit tables as needed.
        parent = self.root
        for i, segment in enumerate(full_path[:-1]):
            sub_path = full_path[: i + 1]
            if sub_path in self._inline:
                raise self.scan.error(
                    f"cannot extend inline table '{'.'.join(sub_path)}'"
                )
            existing = parent.get(segment)
            if existing is None:
                new_dict: dict[str, Any] = {}
                parent[segment] = new_dict
                self._implicit.add(sub_path)
                parent = new_dict
            elif isinstance(existing, dict):
                parent = existing
            elif isinstance(existing, list) and existing and isinstance(existing[-1], dict):
                parent = existing[-1]
            else:
                raise self.scan.error(
                    f"key '{'.'.join(sub_path)}' has a non-table value"
                )
        last = full_path[-1]
        if last in parent:
            raise self.scan.error(
                f"key '{'.'.join(full_path)}' already defined"
            )
        parent[last] = value
        self._direct.add(full_path)

    # -- key parsing -------------------------------------------------------

    def _parse_key_path(self) -> tuple[str, ...]:
        parts: list[str] = [self._parse_key_segment()]
        s = self.scan
        while True:
            s.skip_inline_ws()
            if s.peek() == ".":
                s.advance()
                s.skip_inline_ws()
                parts.append(self._parse_key_segment())
            else:
                break
        return tuple(parts)

    def _parse_key_segment(self) -> str:
        s = self.scan
        ch = s.peek()
        if ch == '"':
            return self._parse_basic_string(multiline=False)
        if ch == "'":
            return self._parse_literal_string(multiline=False)
        match = _BARE_KEY_RE.match(s.text, s.pos)
        if not match or match.end() == s.pos:
            raise s.error("expected key")
        s.advance(match.end() - s.pos)
        return match.group(0)

    # -- value dispatch ----------------------------------------------------

    def _parse_value(self) -> Any:
        s = self.scan
        ch = s.peek()
        if not ch:
            raise s.error("expected value")
        if ch == '"':
            multiline = s.starts_with('"""')
            return self._parse_basic_string(multiline=multiline)
        if ch == "'":
            multiline = s.starts_with("'''")
            return self._parse_literal_string(multiline=multiline)
        if ch == "[":
            return self._parse_array()
        if ch == "{":
            self._last_value_was_inline = True
            return self._parse_inline_table()
        if ch in "tf":
            return self._parse_bool()
        # Number, date, time, +/-/inf/nan/integer/float.
        return self._parse_atom()

    # -- strings -----------------------------------------------------------

    def _parse_basic_string(self, *, multiline: bool) -> str:
        s = self.scan
        if multiline:
            s.advance(3)
            if s.peek() == "\n":
                s.advance()
            elif s.peek() == "\r" and s.peek(1) == "\n":
                s.advance(2)
            return self._collect_basic_string(multiline=True)
        s.advance(1)
        return self._collect_basic_string(multiline=False)

    def _collect_basic_string(self, *, multiline: bool) -> str:
        s = self.scan
        out: list[str] = []
        while True:
            if s.eof():
                raise s.error("unterminated basic string")
            ch = s.peek()
            if ch == "\\":
                out.append(self._read_basic_escape(multiline=multiline))
                continue
            if ch == '"':
                if multiline and s.starts_with('"""'):
                    # Allow up to two quotes immediately before the closing fence.
                    extra = 0
                    while s.peek(3 + extra) == '"' and extra < 2:
                        extra += 1
                    out.append('"' * extra)
                    s.advance(3 + extra)
                    return "".join(out)
                if not multiline:
                    s.advance()
                    return "".join(out)
                out.append(s.advance())
                continue
            if ch == "\n" and not multiline:
                raise s.error("newline in single-line basic string")
            out.append(s.advance())

    def _read_basic_escape(self, *, multiline: bool) -> str:
        s = self.scan
        s.advance()  # consume backslash
        if s.eof():
            raise s.error("dangling escape at end of string")
        ch = s.peek()
        if ch in _BASIC_ESCAPES:
            s.advance()
            return _BASIC_ESCAPES[ch]
        if ch == "u":
            s.advance()
            return self._read_unicode_escape(4)
        if ch == "U":
            s.advance()
            return self._read_unicode_escape(8)
        if multiline and (ch == "\n" or ch in " \t" or (ch == "\r" and s.peek(1) == "\n")):
            # Line-ending backslash: skip whitespace including newlines.
            while not s.eof() and s.peek() in " \t\r\n":
                s.advance()
            return ""
        raise s.error(f"invalid escape sequence '\\{ch}'")

    def _read_unicode_escape(self, width: int) -> str:
        s = self.scan
        digits = s.text[s.pos : s.pos + width]
        if len(digits) < width or any(c not in "0123456789abcdefABCDEF" for c in digits):
            raise s.error("invalid unicode escape")
        s.advance(width)
        try:
            return chr(int(digits, 16))
        except (ValueError, OverflowError) as exc:
            raise s.error("invalid unicode codepoint") from exc

    def _parse_literal_string(self, *, multiline: bool) -> str:
        s = self.scan
        if multiline:
            s.advance(3)
            if s.peek() == "\n":
                s.advance()
            elif s.peek() == "\r" and s.peek(1) == "\n":
                s.advance(2)
            out: list[str] = []
            while True:
                if s.eof():
                    raise s.error("unterminated literal string")
                if s.starts_with("'''"):
                    extra = 0
                    while s.peek(3 + extra) == "'" and extra < 2:
                        extra += 1
                    out.append("'" * extra)
                    s.advance(3 + extra)
                    return "".join(out)
                out.append(s.advance())
        s.advance(1)
        out_single: list[str] = []
        while True:
            if s.eof():
                raise s.error("unterminated literal string")
            ch = s.peek()
            if ch == "'":
                s.advance()
                return "".join(out_single)
            if ch == "\n":
                raise s.error("newline in single-line literal string")
            out_single.append(s.advance())

    # -- atoms (numbers, datetimes, bool/special) --------------------------

    def _parse_bool(self) -> bool:
        s = self.scan
        if s.starts_with("true"):
            s.advance(4)
            return True
        if s.starts_with("false"):
            s.advance(5)
            return False
        raise s.error("expected boolean")

    def _read_datetime_atom(self) -> str:
        """Greedy reader for date / datetime tokens.

        Allows a single space (TOML's permitted alternative to ``T``)
        between the date and time portions; otherwise the standard atom
        reader would split the value at the space.
        """

        s = self.scan
        start = s.pos
        # YYYY-MM-DD (already validated as a date prefix by the caller).
        s.advance(10)
        # Optional time component.
        if not s.eof():
            sep = s.peek()
            following = s.peek(1)
            if sep in ("T", "t", " ") and following.isdigit():
                s.advance(1)
                # HH:MM:SS — exactly 8 chars.
                s.advance(8)
                if not s.eof() and s.peek() == ".":
                    s.advance()
                    while not s.eof() and s.peek().isdigit():
                        s.advance()
                if not s.eof() and s.peek() == "Z":
                    s.advance()
                elif not s.eof() and s.peek() in "+-":
                    s.advance(6)
        return s.text[start : s.pos]

    def _read_atom_token(self) -> str:
        # Read until a delimiter. Allow ':' to support time / datetime values.
        s = self.scan
        start = s.pos
        while not s.eof():
            ch = s.peek()
            if ch in " \t\n\r,]}#":
                break
            s.advance()
        return s.text[start : s.pos]

    def _parse_atom(self) -> Any:
        s = self.scan
        # Detect dates/datetimes by inspecting the next 10 chars.
        snippet = s.text[s.pos : s.pos + 10]
        if len(snippet) >= 10 and snippet[4] == "-" and snippet[7] == "-":
            # Could be a date or a (possibly offset) datetime.
            return self._parse_date_or_datetime()
        snippet_t = s.text[s.pos : s.pos + 8]
        if len(snippet_t) >= 8 and snippet_t[2] == ":" and snippet_t[5] == ":":
            return self._parse_local_time()
        token = self._read_atom_token()
        if not token:
            raise s.error("expected value")
        return self._convert_number(token)

    def _convert_number(self, token: str) -> Any:
        # Special floats.
        if token in ("inf", "+inf"):
            return float("inf")
        if token == "-inf":
            return float("-inf")
        if token in ("nan", "+nan", "-nan"):
            return float("nan")
        if _INT_HEX_RE.match(token):
            return int(token[2:].replace("_", ""), 16)
        if _INT_OCT_RE.match(token):
            return int(token[2:].replace("_", ""), 8)
        if _INT_BIN_RE.match(token):
            return int(token[2:].replace("_", ""), 2)
        if _INT_DEC_RE.match(token):
            cleaned = token.replace("_", "")
            return int(cleaned)
        if _FLOAT_RE.match(token):
            return float(token.replace("_", ""))
        raise self.scan.error(f"invalid value: {token!r}")

    def _parse_local_time(self) -> time:
        token = self._read_atom_token()
        match = _TIME_RE.match(token)
        if not match:
            raise self.scan.error(f"invalid time: {token!r}")
        hour, minute, second, frac = match.groups()
        micro = 0
        if frac:
            micro = int((frac + "000000")[:6])
        try:
            return time(int(hour), int(minute), int(second), micro)
        except ValueError as exc:
            raise self.scan.error(f"invalid time: {token!r}") from exc

    def _parse_date_or_datetime(self) -> date | datetime:
        token = self._read_datetime_atom()
        match = _DATETIME_RE.match(token)
        if not match:
            raise self.scan.error(f"invalid date/datetime: {token!r}")
        y, mo, d, hh, mm, ss, frac, off = match.groups()
        if hh is None:
            try:
                return date(int(y), int(mo), int(d))
            except ValueError as exc:
                raise self.scan.error(f"invalid date: {token!r}") from exc
        micro = 0
        if frac:
            micro = int((frac + "000000")[:6])
        tz = None
        if off == "Z":
            tz = timezone.utc
        elif off:
            sign = 1 if off[0] == "+" else -1
            hours = int(off[1:3])
            minutes = int(off[4:6])
            tz = timezone(sign * timedelta(hours=hours, minutes=minutes))
        try:
            return datetime(
                int(y), int(mo), int(d), int(hh), int(mm), int(ss), micro, tz
            )
        except ValueError as exc:
            raise self.scan.error(f"invalid datetime: {token!r}") from exc

    # -- arrays & inline tables --------------------------------------------

    def _parse_array(self) -> list[Any]:
        s = self.scan
        s.advance()  # '['
        items: list[Any] = []
        self._skip_array_ws()
        if s.peek() == "]":
            s.advance()
            return items
        while True:
            self._skip_array_ws()
            value = self._parse_value()
            items.append(value)
            self._skip_array_ws()
            if s.peek() == ",":
                s.advance()
                self._skip_array_ws()
                if s.peek() == "]":
                    s.advance()
                    return items
                continue
            if s.peek() == "]":
                s.advance()
                return items
            raise s.error("expected ',' or ']' in array")

    def _skip_array_ws(self) -> None:
        s = self.scan
        while not s.eof():
            ch = s.peek()
            if ch in " \t":
                s.advance()
            elif ch == "\n" or (ch == "\r" and s.peek(1) == "\n"):
                s.consume_newline()
            elif ch == "#":
                while not s.eof() and s.peek() != "\n":
                    s.advance()
            else:
                break

    def _parse_inline_table(self) -> dict[str, Any]:
        s = self.scan
        s.advance()  # '{'
        s.skip_inline_ws()
        result: dict[str, Any] = {}
        seen: set[tuple[str, ...]] = set()
        if s.peek() == "}":
            s.advance()
            return result
        while True:
            s.skip_inline_ws()
            path = self._parse_key_path()
            if path in seen:
                raise s.error(
                    f"key '{'.'.join(path)}' already defined in inline table"
                )
            s.skip_inline_ws()
            if s.peek() != "=":
                raise s.error("expected '=' in inline table entry")
            s.advance()
            s.skip_inline_ws()
            value = self._parse_value()
            self._inline_assign(result, path, value, seen)
            seen.add(path)
            s.skip_inline_ws()
            if s.peek() == ",":
                s.advance()
                s.skip_inline_ws()
                if s.peek() == "}":
                    raise s.error("trailing comma in inline table")
                continue
            if s.peek() == "}":
                s.advance()
                return result
            raise s.error("expected ',' or '}' in inline table")

    def _inline_assign(
        self,
        target: dict[str, Any],
        path: tuple[str, ...],
        value: Any,
        seen: set[tuple[str, ...]],
    ) -> None:
        node: dict[str, Any] = target
        for i, segment in enumerate(path[:-1]):
            sub = path[: i + 1]
            if sub in seen:
                existing = node.get(segment)
                if not isinstance(existing, dict):
                    raise self.scan.error(
                        f"key '{'.'.join(sub)}' is not a table"
                    )
                node = existing
                continue
            existing = node.get(segment)
            if existing is None:
                new_dict: dict[str, Any] = {}
                node[segment] = new_dict
                node = new_dict
            elif isinstance(existing, dict):
                node = existing
            else:
                raise self.scan.error(
                    f"key '{'.'.join(sub)}' is not a table"
                )
        last = path[-1]
        if last in node:
            raise self.scan.error(
                f"key '{'.'.join(path)}' already defined in inline table"
            )
        node[last] = value

    # -- table descent -----------------------------------------------------

    def _descend_path(
        self, path: tuple[str, ...], *, for_table_header: bool
    ) -> dict[str, Any]:
        node: dict[str, Any] = self.root
        for i, segment in enumerate(path):
            sub = path[: i + 1]
            if sub in self._inline:
                raise self.scan.error(
                    f"cannot extend inline table '{'.'.join(sub)}'"
                )
            existing = node.get(segment)
            if existing is None:
                new_dict: dict[str, Any] = {}
                node[segment] = new_dict
                if for_table_header and i < len(path) - 1:
                    self._implicit.add(sub)
                node = new_dict
            elif isinstance(existing, dict):
                node = existing
            elif isinstance(existing, list):
                if not existing or not isinstance(existing[-1], dict):
                    raise self.scan.error(
                        f"key '{'.'.join(sub)}' is not a table"
                    )
                node = existing[-1]
            else:
                raise self.scan.error(
                    f"key '{'.'.join(sub)}' is not a table"
                )
        return node


# ---------------------------------------------------------------------------
# public API


def loads(text: str) -> dict[str, Any]:
    """Parse a TOML document from a string and return a dict.

    Raises :class:`ParseError` on invalid input.
    """

    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    parser = _Parser(text)
    result = parser.parse()
    # Mark inline tables produced during parsing so future overrides
    # cannot mutate them; this is already enforced inline, but the
    # resulting dict is otherwise an ordinary mapping for the caller.
    return result


__all__ = ["loads", "_Parser"]
