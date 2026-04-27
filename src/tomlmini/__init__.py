"""tomlmini — zero-dependency TOML v1.0 common-subset parser.

Public API:

- :func:`loads` — parse a TOML string into a dict.
- :func:`load`  — parse a TOML file (path-like) into a dict.
- :class:`TomlError` and :class:`ParseError` — exception types.
"""

from __future__ import annotations

import os
from typing import Any

from ._core import loads
from ._errors import ParseError, TomlError


def load(
    path: str | os.PathLike[str], *, encoding: str = "utf-8"
) -> dict[str, Any]:
    """Parse the TOML file at *path* and return a dict.

    Reads the entire file into memory before parsing. Raises ``OSError``
    if the file cannot be opened and :class:`ParseError` if the contents
    are not valid TOML.
    """

    if not isinstance(encoding, str) or not encoding:
        raise TypeError("encoding must be a non-empty str")
    with open(path, "r", encoding=encoding) as handle:
        text = handle.read()
    return loads(text)


__version__ = "0.1.0"

__all__ = [
    "ParseError",
    "TomlError",
    "load",
    "loads",
    "__version__",
]
