# M002 — Duplicate qualifier keys: silent last-write-wins

## Severity
**Medium** (Class A10 — duplicate qualifier keys, spec-compliance gap)

## Surface
`src/purlparse/_core.py:91, 95` — `qualifiers[k] = ""` / `qualifiers[k] = v` inside
the qualifier-parse loop. Both assignments overwrite any existing entry for the
same key without warning.

## Root Cause
The qualifier-parse loop splits on `&` then on `=`, building a dict via repeated
assignment. Per ECMA-424, duplicate qualifier keys should be a parse error. The
current implementation silently accepts them and keeps the **last** value seen
("last-write-wins" semantics). ECMA-424 explicitly states duplicate keys are an
error.

## Reproduction (confirmed against `repro_min.bin`)
- Input: `pkg:npm/x?a=1&a=2`
- Result: `{'a': '2'}` — the value `1` is silently overwritten by `2`

Order-dependence matrix (verified):
```
'pkg:npm/foo?a=1&a=2'  -> {'a': '2'}    # last wins
'pkg:npm/foo?a=2&a=1'  -> {'a': '1'}    # last wins (different result!)
'pkg:npm/foo?a&a=2'    -> {'a': '2'}    # last wins (mixes empty+non-empty)
```

## Impact
- **Interop risk**: two spec-compliant purl parsers may disagree on which value
  "wins" for `?a=1&a=2`. Downstream equality checks (`purl1 == purl2`) between
  two parses of the same string by different tools could yield false negatives.
- **Semantic ambiguity**: the parser does not surface which value is "correct"
  when the input is ambiguous.

## Status
**OPEN** — confirmed, no fix applied in T4.

## Remediation Hint
Per ECMA-424, raise `PurlError("duplicate qualifier key: {k!r}")` instead of
silently overwriting. ~5 LOC at `_core.py:91, 95`. **This fix would also leverage
V003's PurlError** — a single combined patch closes V003 + M002 + M003.

Estimated fix: 5 LOC at `_core.py:91-95` plus 1 raise site.

## Atheris Fuzzer Result
T3 Atheris on all 5 surfaces (570M iterations) found 0 oracle-mismatches or
crashes from this finding. Reason: Atheris's `ConsumeUnicodeNoSurrogates`
typically doesn't produce structured qualifier pairs with duplicates; the bug is
deterministic but invisible to random string generation.