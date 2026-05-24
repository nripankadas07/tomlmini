"""Parse a realistic TOML config and print the normalized structure."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import tomlmini

CONFIG = """
title = "No-Dependency Lab"

[server]
host = "127.0.0.1"
port = 8080

[[checks]]
name = "lint"
cmd = "ruff check ."

[[checks]]
name = "test"
cmd = "pytest -q"
"""


def main() -> None:
    parsed = tomlmini.loads(CONFIG)
    print(parsed["title"])
    print(parsed["server"]["port"])
    print(", ".join(check["name"] for check in parsed["checks"]))


if __name__ == "__main__":
    main()
