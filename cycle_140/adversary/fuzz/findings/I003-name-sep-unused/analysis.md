# I003 — TYPE_REGISTRY: `name_sep` defined for maven but never consumed

## Severity
**Info** (design smell — dead field)

## Surface
- Definition: `src/purlparse/_types.py:17` — `"maven": {"namespace_sep": ":", "name_sep": "/"}`
- Default fallback: `src/purlparse/_core.py:151` — `TYPE_REGISTRY.get(type_str, {"namespace_sep": "/", "name_sep": None})`

## Root Cause
`maven` (and only maven) has `name_sep='/'` defined, suggesting multi-segment
name support (e.g., `pkg:maven/org.apache.commons/commons-lang3`). However, the
core parser **never reads the `name_sep` value** when constructing the result.
The single reference to "name_sep" in `_core.py` (line 151) is constructing a
fallback default dict for unknown types — not reading the maven entry's
`name_sep` value.

## Reproduction (confirmed against `stacktrace.txt`)
- TYPE_REGISTRY entry: `maven: name_sep='/'`
- References to `name_sep` in `_core.py`: **1** (line 151, in default-construction — not a read)

## Impact
- **Dead field** in the data model.
- Could mislead future maintainers into thinking multi-segment names are
  supported when they aren't.

## Status
**INFO** — design observation.

## Remediation Hint
Remove `name_sep` from the registry, or document it as reserved-for-future-use.