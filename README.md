# tomlmini

A small, zero-dependency parser for the **common subset** of TOML v1.0.

`tomlmini` covers what almost every real-world `*.toml` config file
needs — keys/values, tables, sub-tables, arrays, arrays of tables,
inline tables, all four string flavours, the full numeric grammar
(decimal, hex, octal, binary, with `_` separators) and offset / local
date and time values — without trying to be a fully spec-compliant
implementation. The result is a parser you can read end to end in one
sitting, vendor in a single file, and trust to fail loudly on the
weird stuff rather than silently produce surprising structures.

```python
import tomlmini

config = tomlmini.loads("""
title = "Forge Pipeline"

[server]
host = "db.internal"
port = 5432
options = { pool = 16, timeout = 30.0 }

[[hooks]]
name = "lint"
cmd  = "ruff check ."

[[hooks]]
name = "test"
cmd  = "pytest -q"
""")

assert config["title"] == "Forge Pipeline"
assert config["server"]["options"]["pool"] == 16
assert [h["name"] for h in config["hooks"]] == ["lint", "test"]
```

## Install

```bash
pip install tomlmini
```

`tomlmini` requires Python 3.10+ and has zero runtime dependencies.

## Public API

```python
import tomlmini

tomlmini.loads(text: str) -> dict[str, Any]
tomlmini.load(path: str | os.PathLike, *, encoding: str = "utf-8") -> dict[str, Any]

tomlmini.TomlError       # base class
tomlmini.ParseError      # subclass; carries .line and .col
```

### `loads(text)`

Parse a TOML document from a string and return the result as a
nested `dict`. Raises `ParseError` with a 1-based line/column on any
syntax problem.

### `load(path, *, encoding="utf-8")`

Convenience wrapper around `loads`: reads the file at *path* with the
given text encoding and parses it. Raises `OSError` if the file
cannot be opened.

### `ParseError`

Subclass of `TomlError`. Exposes `.line` and `.col` (both 1-based) so
callers can report a meaningful location:

```python
try:
    tomlmini.loads(text)
except tomlmini.ParseError as exc:
    print(f"bad config at {exc.line}:{exc.col}: {exc}")
```

## Supported TOML features

| Feature                                | Status |
| -------------------------------------- | ------ |
| Comments                               | ✓      |
| Bare and quoted keys                   | ✓      |
| Dotted keys (`a.b.c = 1`)              | ✓      |
| Basic strings (`"..."`)                | ✓      |
| Literal strings (`'...'`)              | ✓      |
| Multi-line basic strings               | ✓      |
| Multi-line literal strings             | ✓      |
| Standard escapes (`\n`, `\t`, `\u`, `\U`) | ✓   |
| Line-ending backslash trim             | ✓      |
| Decimal / hex / octal / binary ints    | ✓      |
| `_` separators in numeric literals     | ✓      |
| Floats with exponent / `inf` / `nan`   | ✓      |
| Booleans                               | ✓      |
| Local date / time / datetime           | ✓      |
| Offset datetime (`Z` and `±HH:MM`)     | ✓      |
| Arrays (mixed types, nested)           | ✓      |
| Inline tables                          | ✓      |
| Tables (`[name]`)                      | ✓      |
| Arrays of tables (`[[name]]`)          | ✓      |
| Inline-table immutability              | ✓      |
| Duplicate-key / table-redefinition checks | ✓   |

### Non-goals

`tomlmini` deliberately does *not* try to:

- Round-trip TOML (parser only — no `dumps`).
- Resolve every pathological dotted-key + table-header interaction
  the full TOML 1.0 spec normalises away. It rejects the ambiguous
  cases instead of silently merging.
- Provide async / streaming parsing.

If you need a fully spec-compliant parser, use the standard library's
`tomllib` (Python 3.11+) or [`tomli`](https://pypi.org/project/tomli/).

## Errors

All exceptions inherit from `tomlmini.TomlError`. The parser raises
`tomlmini.ParseError` on any of:

- Unterminated string literals (single-line or multi-line).
- Invalid escape sequences (`\q`, `\u12`, etc.).
- Newlines inside single-line strings.
- Numeric literals with leading zeros, double underscores, or
  trailing underscores.
- Invalid date / time / datetime tokens.
- Duplicate keys at the same scope.
- Redefining an already-declared table.
- Extending an inline table with a later `[name]` header or dotted
  key assignment.
- Arrays missing commas or closing brackets; inline tables with
  trailing commas.

## Running tests

```bash
git clone https://github.com/nripankadas07/tomlmini.git
cd tomlmini
pip install -e .[dev]
pytest -q
```

The suite ships **136 tests** covering happy paths, edge cases, and
error reporting, and exercises the parser to ≥95% line coverage.

## License

MIT — see [LICENSE](LICENSE).
