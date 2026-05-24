# Security policy

## Supported versions

The `main` branch is the supported development line.

## Reporting a vulnerability

Please report parser denial-of-service concerns, dependency issues, or malformed
input crashes through GitHub's private vulnerability reporting when available,
or by opening a minimal public issue without exploit payloads.

For untrusted TOML input, limit document size before parsing. Like Python's
standard `tomllib`, this parser reads the full document into memory.
