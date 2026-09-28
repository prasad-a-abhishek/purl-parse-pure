# I001 — POSITIVE: No regex use anywhere (A1 / ReDoS = structurally impossible)

## Severity
**Info** (positive finding — defense-in-depth)

## Surface
`src/purlparse/_core.py`, `src/purlparse/_types.py`, `src/purlparse/_errors.py` — entire source.

## Root Cause
**No `re` module use anywhere in the source.** The entire parser is implemented
via `str.find()`, `str.split()`, `str.startswith()`, `str.rfind()`, and
`str.count()`. None of these exhibit catastrophic backtracking. **A1 (Regex
ReDoS) is structurally impossible.**

## Reproduction (confirmed against `stacktrace.txt`)
```
inspect.getsource(purlparse._core)  -> 0 regex calls
inspect.getsource(purlparse._types) -> 0 regex calls
inspect.getsource(purlparse._errors)-> 0 regex calls
```

Pattern searched: `re.(?:compile|search|match|findall|sub|split|fullmatch)`

## Impact
**Positive** — eliminates an entire class of DoS attack. Any input size up to
ARG_MAX is processed in O(n) string operations.

## Status
**INFO / n/a** — positive observation.