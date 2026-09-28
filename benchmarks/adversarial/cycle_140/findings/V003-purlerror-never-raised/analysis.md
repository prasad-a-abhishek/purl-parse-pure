# V003 — `PurlError` exported but never raised (public API contract drift)

## Severity
**High** (Class A5 / public-API contract — silently broken API)

## Surface
- Class definition: `src/purlparse/_errors.py:6-9` (`class PurlError(ValueError): pass`)
- Public export: `src/purlparse/__init__.py:11` (`__all__ = ["parse", "ParseResult", "PurlError", "TYPE_REGISTRY", "__version__"]`)
- Implementation: `src/purlparse/_core.py` — imports `PurlError` at line 19, raises bare `ValueError` 12 times, never instantiates `PurlError`.

## Root Cause
`PurlError` is documented as "Raised when a string cannot be parsed as a valid purl"
(`_errors.py:7`) and re-exported in `__init__.py`'s `__all__` list. The class IS-A
`ValueError` (subclass), so semantically a caller might do:

```python
from purlparse import parse, PurlError
try:
    parse(s)
except PurlError:
    print("invalid")
```

…but `parse()` only raises plain `ValueError`. `except PurlError` catches nothing
because the subclass is never actually instantiated anywhere in `_core.py`,
`__main__.py`, or `_types.py`. The exception hierarchy is dead code.

## Reproduction (confirmed via `stacktrace.txt`)
- **Static evidence**: `inspect.getsource(_core)` shows `PurlError` referenced 1 time
  (the import at line 19) and `raise ValueError` 12 times. `raise PurlError` appears
  0 times.
- **Behavioral evidence**: 5 invalid inputs were tested; **all** raised plain
  `ValueError`, **none** raised `PurlError`. Confirmed: `except PurlError` is dead code.

Tested inputs:
```
parse('')             -> ValueError: purl cannot be empty
parse('not-a-purl')   -> ValueError: purl must start with 'pkg:'
parse('pkg:npm')      -> ValueError: purl missing '/' after type
parse('pkg:///')      -> ValueError: purl type cannot be empty
parse('pkg:npm/foo?') -> ValueError: purl has trailing '?' with no qualifiers
```

## Impact
- **Public API contract drift**: a documented exception type that is exported but
  never raised is worse than not exporting it — it misleads callers into writing
  defensive code that does nothing.
- **Catching semantics**: callers can do `except (PurlError, ValueError)` (which works
  because `PurlError IS-A ValueError`), but `except PurlError` alone fails silently.
- **Documentation**: README.md / `__init__.py` advertise `PurlError` as the error type
  to catch. The implementation contradicts this.

## Status
**OPEN** — bug confirmed, no fix applied in T4 (T4 is observation-only).

## Remediation Hint
Two options:

**(a) Recommended**: Replace all 12 `raise ValueError(...)` in `_core.py` with
`raise PurlError(...)` (single token change). Update the docstring at
`_core.py:32-33` to say "Raises: PurlError". ~12 token replacements + 1 docstring
update.

**(b) Alternative**: Keep `ValueError` everywhere, remove `PurlError` from `__all__`
in `__init__.py:11`, and document that callers should
`except (PurlError, ValueError)` (or just `except ValueError` since the former is
redundant given the subclass relationship). ~1 line removal.

Option (a) is cleaner and aligns with the documented intent. **A single combined
patch (V002 + V003) is feasible in ~5–7 LOC.**

## Citations
- `src/purlparse/_errors.py:6-9` — `class PurlError(ValueError): pass`
- `src/purlparse/__init__.py:11` — `__all__ = [..., "PurlError", ...]`
- `src/purlparse/_core.py:19` — `from ._errors import PurlError` (only reference)
- `src/purlparse/_core.py:23` — `def parse(purl: str) -> ParseResult:`
- `src/purlparse/_core.py:36, 38, 40, 43, 47, 49, 53, 57, 61, 65, 67, 79` — 12 raise ValueError sites
- `cycle_140/adversary/fuzz/VULN_AUDIT.md` lines 229-263 — original VULN_AUDIT narrative

## Atheris Fuzzer Result
T3 Atheris on all 5 surfaces (570M iterations, 18m 56s) found **0 crashes** from
this finding. Reason: a `try/except` that catches the wrong class is a logic
bug, not a runtime crash. Atheris is the wrong tool for this class.

## Cross-Reference
- **V002** (non-string raw TypeError) is also unreachable by string fuzzers, and is
  fixed by the same patch (add isinstance guard + raise PurlError).
- A single 5-7 LOC patch at `_core.py:23-43` closes both V002 and V003.