# M001 — `to_string()` re-orders qualifiers alphabetically

## Severity
**Medium** (Class A16 — round-trip integrity, observation only)

## Surface
`src/purlparse/_types.py:104` — `for k, v in sorted(self.qualifiers.items())` inside
`ParseResult.to_string()`.

## Root Cause
`to_string()` sorts the qualifiers dict by key before emitting, producing
canonical form per ECMA-424 §4.5. The behavior is **spec-correct** but not
explicitly documented, and the test suite asserts it without a comment — a
future maintainer removing the `sorted()` to "preserve insertion order" would
silently break round-trip from canonical inputs.

## Reproduction (confirmed against `repro_min.bin`)
- Input: `pkg:npm/x@a?b=1&a=1` (b before a in the input)
- Parsed dict (insertion order preserved in input): `{'b': '1', 'a': '1'}`
- `to_string()` output: `pkg:npm/x@a?a=1&b=1` — **alphabetical order**

## Impact
- Round-trip from canonical inputs is correct (input `?arch=x64&os=linux` →
  parse → to_string → `?arch=x64&os=linux`).
- Round-trip from non-canonical inputs is non-identity (input `?os=linux&arch=x64`
  → parse → to_string → `?arch=x64&os=linux`).
- Most callers want canonical form, so this is the **correct** behavior. Flagged
  for documentation completeness and test-comment completeness only.

## Status
**OPEN** — observation only, behavior is correct per spec.

## Remediation Hint
Add an explicit comment in `_types.py:102-106` explaining the sort is
spec-mandated (ECMA-424 §4.5 canonical ordering). Or document the alphabetization
in `to_string()`'s docstring. No code change required.

Estimated fix: 0 LOC of logic change; 1-2 lines of comment/docstring.

## Atheris Fuzzer Result
T3 Atheris: 0 oracle-mismatches across all 5 surfaces (570M iterations). The
alphabetical sort is consistent — fuzzer cannot find a canonical input whose
round-trip diverges.