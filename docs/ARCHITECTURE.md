# Architecture

`tomlmini` thesis: a small TOML common-subset parser that rejects ambiguous edges loudly.

```mermaid
flowchart LR
    A0["Source Text"]
    A1["Lexer/Parser"]
    A2["Value Parser"]
    A3["Table State"]
    A4["Duplicate/Redefinition Checks"]
    A5["dict Output"]
    A0 --> A1
    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> A5
```

## Design Rules

- Keep the public API small enough to inspect in one sitting.
- Make demos run locally without network credentials.
- Put correctness checks in tests, conformance scripts, or benchmark scripts
  instead of relying on README claims.
- Prefer explicit failure modes over surprising implicit behavior.
