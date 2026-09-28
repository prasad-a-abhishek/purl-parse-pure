# purl-parse-pure

**Zero-dependency ECMA-424 Package URL (purl) parser for Python stdlib.**

`pkg:npm/lodash@4.17.21` → `{type: "npm", name: "lodash", version: "4.17.21"}`

[![PyPI version](https://img.shields.io/pypi/v/purl-parse-pure.svg)](https://pypi.org/project/purl-parse-pure/)
[![Python](https://img.shields.io/pypi/pyversions/purl-parse-pure.svg)](https://pypi.org/project/purl-parse-pure/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Quick Start

```bash
pip install purl-parse-pure
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
| LOC | **~340** | 2000+ | 1000+ |
| Round-trip | **Yes** | Yes | Yes |

## Key Features

- **Zero dependencies** — `urllib.parse` + `dataclasses` only
- **Full ECMA-424 grammar** — type-specific namespace/name separators (npm, pypi, maven, go, deb, github, ...)
- **URL decoding** — qualifiers, subpaths, and version strings
- **Round-trip** — `to_string()` produces canonical form that re-parses identically
- **Equality & hash** — `ParseResult` usable in `set`/`dict`
- **CLI** — `parse`, `decode`, `validate` subcommands
- **174 tests** — 100% pytest pass, full AC coverage

## Install

```bash
pip install purl-parse-pure
```

For GitHub install (pre-PyPI):

```bash
pip install git+https://github.com/prasad-a-abhishek/purl-parse-pure.git
```

## License

MIT — see LICENSE file.
