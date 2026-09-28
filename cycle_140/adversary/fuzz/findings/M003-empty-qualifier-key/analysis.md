# M003 — Empty qualifier key silently accepted

## Severity
**Medium** (Class A11 — empty qualifier value/key, spec-compliance gap)

## Surface
`src/purlparse/_core.py:91, 95` — no length check on `k` after unquote.

## Root Cause
The qualifier parser splits on `&` then on `=`, with no check that the key is
non-empty or that the value (if present) has the expected shape. Per ECMA-424,
`qualifier_key = ALPHA (ALPHA / DIGIT / "-" / "." / "_")*` — empty keys are
structurally invalid by the grammar production. The current parser happily
accepts `?=v` and stores `{'': 'v'}`.

## Reproduction (confirmed against `repro_min.bin`)
- Input: `pkg:npm/x?=1`
- Result: `{'': '1'}` — **empty key stored**

Matrix (verified):
```
'pkg:npm/foo?a='   -> {'a': ''}     # empty value, non-empty key (debatable)
'pkg:npm/foo?a&b=1' -> {'a': '', 'b': '1'}  # mixed
'pkg:npm/foo?=v'   -> {'': 'v'}     # EMPTY KEY (invalid per ECMA-424)
'pkg:npm/foo?=&'   -> {'': ''}      # empty key + empty value
```

## Impact
- An empty-key qualifier dict (`{'': 'v'}`) is structurally invalid per ECMA-424.
- `to_string()` round-trips it without error.
- Downstream consumers iterating `qualifiers.items()` may crash on empty keys
  when constructing cache keys or logging.

## Status
**OPEN** — confirmed, no fix applied in T4.

## Remediation Hint
Reject empty keys with `PurlError("qualifier key cannot be empty: {raw!r}")` at
`_core.py:91, 95` (before assignment). Empty values (`a=`) are arguably OK but
should be documented.

Estimated fix: 2-3 LOC at `_core.py:91, 95`.

## Atheris Fuzzer Result
T3 Atheris on all 5 surfaces (570M iterations) found 0 oracle-mismatches. The
empty-key case is structurally deterministic but Atheris random strings rarely
hit `?=` immediately after `?`.