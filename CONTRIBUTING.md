# Contributing

Thanks for considering a contribution. `tomlmini` is intentionally small, so
changes should keep the parser readable and strict.

## Local setup

```bash
python -m pip install -e ".[dev]"
ruff check .
mypy --strict src/tomlmini
pytest --cov=tomlmini --cov-report=term-missing --cov-fail-under=95
```

## Contribution rules

- Add tests for every parser behavior change.
- Compare supported TOML behavior with `tomllib` when possible.
- Prefer explicit parse errors over surprising coercions.
- Keep runtime dependencies at zero.
- Keep public API changes documented in `README.md`.
