# tomlmini: a beautiful small reference parser

This is a launch-ready technical article draft for the repository. It is meant
to explain the idea, not inflate traction.

## The Problem

Config parsers often trade readability for total spec coverage. This repo chooses a practical subset and explicit errors.

## The Core Idea

Keep parser state visible: parse values, maintain table context, reject duplicate or ambiguous writes.

## Conformance

Supported cases are cross-checked against `tomllib`/`tomli`; unsupported edge cases are documented as non-goals.

## Limitations

It is parser-only and not a round-trip formatter. If you need every TOML 1.0 corner, use the standard parser.

## Try It

Run the README demo from a clean checkout. If the demo needs credentials, it is
not a good flagship demo.
