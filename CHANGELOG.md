# Changelog

All notable changes to this project are documented here.

## [0.1.1] - 2026-09-28

### Fixed

- **parse()** now raises `PurlError` on non-str input (closes F-V002 Invariant 21 exception-safety finding from cycle_140/@repo-adversary).
- All 12 internal parse error sites now raise `PurlError` (not bare `ValueError`) — closes F-V003 Invariant 11 advertised-vs-raised consistency. `PurlError` remains a `ValueError` subclass for backward compat.

### Documented Limitations

- F-V001: percent-encoded control characters (`%0A`, `%0D`, `%09`) are NOT rejected at parse time. Out-of-scope for v0.1.1 fix; would require unquote-then-gate refactor with round-trip regression risk. Tracked for future release.

## [0.1.0] - 2026-09-28

### Added

- Initial release. Zero-dependency ECMA-424 / SPDX Package URL (purl) parser for Python stdlib. 216/216 tests passing across 5 test modules (test_core, test_types, test_roundtrip, test_fuzz, test_api_safety).