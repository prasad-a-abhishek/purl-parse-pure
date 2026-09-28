# purl-parse-pure

**Zero-dependency ECMA-424 Package URL (purl) parser for Python stdlib.**

`pkg:npm/lodash@4.17.21` → `{type: "npm", name: "lodash", version: "4.17.21"}`

[![Python](https://img.shields.io/pypi/pyversions/purl-parse-pure.svg)](https://github.com/prasad-a-abhishek/purl-parse-pure)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-216%20passing-brightgreen.svg)](https://github.com/prasad-a-abhishek/purl-parse-pure)

## Quick Start

```bash
pip install git+https://github.com/prasad-a-abhishek/purl-parse-pure.git
```

```python
from purlparse import parse, ParseResult

# Basic parse
result = parse("pkg:npm/lodash@4.17.21")
assert result.type == "npm"
assert result.name == "lodash"
assert result.version == "4.17.21"

# Scoped npm packages
r = parse("pkg:npm/@babel/cli@7.21.0")
assert r.namespace == "@babel"
assert r.name == "cli"

# Maven (groupId:artifactId)
r = parse("pkg:maven/org.apache.commons/commons-lang3@1.2.3")
assert r.namespace == "org.apache.commons"
assert r.name == "commons-lang3"

# Round-trip back to string
result = parse("pkg:gem/rails@7.0.0#README.md")
assert result.to_string() == "pkg:gem/rails@7.0.0#README.md"

# Invalid purl raises ValueError
try:
    parse("not-a-purl")
except ValueError as e:
    assert "pkg:" in str(e)
```

## CLI

```bash
python -m purlparse parse    "pkg:gem/rails@7.0.0"
python -m purlparse decode   "pkg:npm/lodash%404.17.21"
python -m purlparse validate "pkg:pypi/django@4.2.0"
```

## Why purl-parse-pure?

Existing purl libraries (`pypurl`, `python-purl`, `packageurl-python`) require third-party dependencies (`packaging`, `requests`, `certifi`). This package implements the full ECMA-424 purl grammar in **pure Python standard library** (`urllib.parse`, `dataclasses`) — zero runtime dependencies.

| Feature | purl-parse-pure | python-purl | packageurl-python |
|---------|-----------------|-------------|-------------------|
| Dependencies | **0** | 3+ | 2+ |
| Stdlib only | **Yes** | No | No |
| LOC | **~470** | 2000+ | 1000+ |
| Round-trip | **Yes** | Yes | Yes |

## Key Features

- **Zero dependencies** — `urllib.parse` + `dataclasses` only
- **Full ECMA-424 grammar** — type-specific namespace/name separators (npm, pypi, maven, go, deb, github, ...)
- **URL decoding** — qualifiers, subpaths, and version strings
- **Round-trip** — `to_string()` produces canonical form that re-parses identically
- **Equality & hash** — `ParseResult` usable in `set`/`dict`
- **CLI** — `parse`, `decode`, `validate` subcommands
- **216 tests** — 100% pytest pass, full AC coverage (174 original + 42 API-safety regression tests)

## Install

```bash
pip install git+https://github.com/prasad-a-abhishek/purl-parse-pure.git
```

## Limitations

The following known limitations are documented per the cycle_140 adversary audit
(severity: Low/Medium). Remediation is deferred to future cycles unless exploitable
evidence emerges.

- **Percent-encoded control characters in name/version/namespace are accepted
  (F-V001, severity: Medium).** Inputs like `pkg:npm/foo%00`, `pkg:npm/foo%0A`,
  `pkg:npm/foo%0D`, `pkg:npm/foo%09` decode NUL/LF/CR/TAB into the parsed fields
  rather than being rejected. The raw-input control-character gate checks the
  pre-decode string, but percent-encoded equivalents bypass it. Fix requires an
  unquote-then-gate refactor or a pre-scan regex (>10 LOC, risk of round-trip
  regressions). Tracked at `cycle_140/adversary/fuzz/findings/V001-pct-ctrl-chars/`.
- **`PurlError` is the recommended catch class.** `PurlError` subclasses
  `ValueError` so legacy `except ValueError:` blocks keep working, but new code
  should catch `PurlError` directly to distinguish purl-parsing failures.
- **Non-string inputs to `parse()` raise `PurlError`.** `parse(b'pkg:npm/foo')`,
  `parse(123)`, `parse(None)` etc. raise `PurlError` (not `TypeError`) per
  Invariant 21 (total public API exception safety).

## License

MIT — see LICENSE file.
