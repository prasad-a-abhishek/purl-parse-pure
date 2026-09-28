# L002 — CLI catches `ValueError` but not `TypeError` (WITHDRAWN at CLI level)

## Severity
**Low** — **DOWNGRADED** to **informational** after re-analysis (see below).

## Surface (originally)
`src/purlparse/__main__.py:39, 54, 69` — `except ValueError as e:`

## Re-Analysis (T4 finding)
The original VULN_AUDIT concern was that the CLI subcommands catch only
`ValueError`, so a programmatic caller passing bytes to `cmd_parse` would
trigger an uncaught `TypeError` (from V002).

**However, this finding does NOT apply at the CLI boundary**:
- `sys.argv` is always `list[str]` at the OS level (Python guarantees this).
- The CLI's own `argparse` only ever passes `str` to `cmd_parse`, `cmd_decode`,
  `cmd_validate`.
- Verified: `python3 -m purlparse parse pkg:npm/foo` → clean JSON output
  (see stacktrace.txt).

The library-surface risk (V002) is the correct location for the fix. **This
finding is WITHDRAWN** at the CLI level. The `cmd_parse`/`cmd_decode`/`cmd_validate`
exception handlers remain safe in their actual CLI invocation context.

## Reproduction (confirms CLI safety)
- Invocation: `python3 -m purlparse parse pkg:npm/foo`
- Exit code: 0
- stdout: valid JSON `{"type": "npm", "name": "foo", ...}`
- stderr: empty (no traceback)

## Status
**WITHDRAWN** — finding does not apply at the CLI surface; library-surface
risk is covered by V002.

## Remediation Hint
None required at the CLI level. (V002 fix at library level also makes the
library safer for programmatic CLI invocations.)