# I002 — Subpath may contain `..` and `;` segments (parser is data-only)

## Severity
**Info** (design observation — consumer responsibility)

## Surface
`src/purlparse/_core.py:99, 170-186` — subpath parser retains `..` and `;`
segments verbatim.

## Root Cause
The parser is **data-only**: it does not interpret the subpath as a filesystem
path. `..` and `;` are accepted because ECMA-424 does not forbid them.

## Reproduction (confirmed against `repro_min.bin`)
- Minimized input: `pkg:npm/x#..`
- Parsed subpath: `'..'`

Matrix (verified):
```
'pkg:npm/foo#../../../etc/passwd'   -> '../../../etc/passwd'
'pkg:npm/foo#a;b;../../etc/passwd'  -> 'a;b;../../etc/passwd'
'pkg:npm/foo#'                      -> ''
'pkg:npm/foo#normal/path'           -> 'normal/path'
```

## Impact
- **Consumer concern, not library concern**: a consumer that uses the `subpath`
  field to construct a file path could be vulnerable to path traversal.
- `purl-parse-pure` does no I/O; it is a parser, not a loader.

## Status
**INFO** — documented in README implicitly.

## Remediation Hint
Add a one-line security note in README: "Consumers that interpret subpath for
filesystem I/O must sanitize the value themselves."