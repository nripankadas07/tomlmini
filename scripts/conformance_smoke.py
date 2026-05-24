"""Cross-check supported TOML shapes against tomllib."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 support.
    try:
        import tomli as tomllib
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Python 3.11+ or the 'tomli' dev dependency is required. "
            "Run: python -m pip install -e '.[dev]'"
        ) from exc

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import tomlmini

CASES = [
    'title = "demo"\n[server]\nport = 8080\n',
    'nums = [1, 0x10, 0o10, 0b10]\n',
    'when = 2026-05-24T12:30:00Z\n',
]


def main() -> None:
    for case in CASES:
        assert tomlmini.loads(case) == tomllib.loads(case)
    print(f"conformance_smoke={len(CASES)} cases")


if __name__ == "__main__":
    main()
