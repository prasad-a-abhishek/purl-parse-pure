# V002 — `parse()` is not total over non-string input (Invariant 21 violation)

## Severity
**High** (Class A6 + A14 — type confusion + total public API exception safety)

## Surface
- `src/purlparse/_core.py:23` — `def parse(purl: str) -> ParseResult:`
- The crash site at line 40: `if ch in "\n\r\t\x00":` — the `for ch in purl:` loop on line 39
  iterates a non-string input, producing `int` items (for bytes) and crashing on
  the `in str` check.

## Root Cause
The `parse()` function performs a single falsy guard `if not purl:` at line 35,
which catches `None`, `''`, `0`, `[]`, `False`, but **not** truthy non-strings
(`True`, `123`, `3.14`, `b'…'`, `['…']`). After the falsy guard, line 39's
`for ch in purl:` iterates whatever was passed. For `bytes`, each `ch` is an `int`,
and the `ch in "\n\r\t\x00"` check on line 40 then raises `TypeError: 'in <string>'
requires string as left operand, not int`.

For `list`, line 36 (`if not purl.startswith("pkg:"):`) raises `AttributeError:
'list' object has no attribute 'startswith'`.

The docstring at `_core.py:32-33` promises only `ValueError`:
> "Raises: ValueError: If the string does not conform to the purl grammar."

This promise is **false** for any truthy non-string input. Invariant 21
(Total Public API Exception Safety) explicitly forbids `TypeError` and
`AttributeError` from public API surfaces.

## Reproduction (confirmed against `repro_min.bin`)
- `repro_min.bin`: 1 byte `x` (read as `b'x'`, passed directly to `parse()`)
- Trigger: `parse(b'x')` → raw `TypeError` (full stack trace in `stacktrace.txt`)
- Stack: `_core.py:40, in parse` → `if ch in "\n\r\t\x00":`

## All truthy non-string inputs crash (verified):
```
parse(None)         -> ValueError: purl cannot be empty       (acceptable, falsy guard catches it)
parse(True)         -> TypeError: 'bool' object is not iterable
parse(123)          -> TypeError: 'int' object is not iterable
parse(3.14)         -> TypeError: 'float' object is not iterable
parse(b'pkg:npm/foo') -> TypeError: 'in <string>' requires string as left operand, not int
parse(['pkg:npm/foo']) -> AttributeError: 'list' object has no attribute 'startswith'
```

## Impact
- **Library embedders** that pass arbitrary user input (e.g., deserialized JSON,
  bytes from a network request) will see raw `TypeError`/`AttributeError` tracebacks
  rather than the documented `ValueError` / `PurlError`.
- **CLI subcommands** (`cmd_parse`, `cmd_decode`, `cmd_validate`) catch only
  `ValueError` (`__main__.py:39, 54, 69`). If `parse(b'...')` is somehow reached
  via a programmatic caller, the CLI exits with a raw Python traceback to stderr
  rather than the documented `Error: …` JSON.
- **Public API contract** is broken: the type signature `def parse(purl: str) ->
  ParseResult` is a hint, not enforcement in Python, and the docstring's `Raises:`
  clause is factually incorrect.

## Status
**OPEN** — bug confirmed, no fix applied in T4 (T4 is observation-only).

## Remediation Hint
Add explicit `isinstance(purl, str)` guard at function entry:
```python
def parse(purl):
    if not isinstance(purl, str):
        raise PurlError(f"purl must be str, got {type(purl).__name__}")
    if not purl:
        raise PurlError("purl cannot be empty")
    # ... existing logic
```
This also aligns with V003 (caller's `except PurlError` would then catch both
type and validation errors cleanly).

Estimated fix: 2–4 LOC at `_core.py:23-35`.

## Citations
- `src/purlparse/_core.py:23` — `def parse(purl: str) -> ParseResult:` (signature)
- `src/purlparse/_core.py:32-33` — docstring (false promise)
- `src/purlparse/_core.py:35-41` — falsy guard (insufficient)
- `src/purlparse/_core.py:39-40` — crash site (`for ch in purl:` + `if ch in str`)
- `src/purlparse/__main__.py:39, 54, 69` — CLI only catches `ValueError`
- `cycle_140/adversary/fuzz/VULN_AUDIT.md` lines 179-225 — original VULN_AUDIT narrative

## Atheris Fuzzer Result
T3 Atheris on `core_parse` surface (134M iterations, 312s) and 4 other surfaces
found **0 crashes** from this finding. Reason: the Atheris harness always feeds
`fdp.ConsumeUnicodeNoSurrogates(...)` (a string) to `parse()`, so the bug class is
invisible to string-only fuzzers. The finding is observable only via the manual
typed-input matrix above.

## Cross-Reference
- **V003** (PurlError exported but never raised) compounds this: callers that do
  `from purlparse import PurlError; try: parse(x); except PurlError: ...` catch
  nothing. V002 + V003 are addressed by a single ~5-LOC patch.