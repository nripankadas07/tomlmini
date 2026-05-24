# tomlmini quality bar

This project is held to a small-parser quality bar, not a demo-script bar.

## Required checks

- `ruff check .` must pass with no ignored failures.
- `mypy --strict src/tomlmini` must pass.
- `pytest --cov=tomlmini --cov-report=term-missing --cov-fail-under=95` must pass.
- Public behavior must be covered by tests that compare supported TOML v1.0
  cases against Python's standard `tomllib`, with `tomli` covering Python 3.10.
- Error cases must raise `tomlmini.ParseError` with a line and column.

## Scope promises

`tomlmini` is deliberately parser-only. It does not preserve formatting, edit
documents, or emit TOML. The quality target is correctness, predictable failure,
small dependency-free code, and readable implementation.

## Release checklist

- Run the required checks locally.
- Confirm the README feature table matches the implementation.
- Confirm the GitHub Actions `CI` workflow is green on every Python version in
  the matrix.
- Confirm Dependabot and secret scanning have no open alerts.
