# L001 — Error messages echo full `purl!r` (input echo)

## Severity
**Low** (Class A2 — info leak, observation only)

## Surface
Every `raise ValueError(f"...: {purl!r}")` in `_core.py` (12 raise sites).

## Root Cause
The error message format strings include the full input via Python's `{purl!r}`
format spec. The echo is **helpful for debugging** (caller sees exactly what
was rejected and at what position), but in a context where the error message is
shown to untrusted parties (logged to a public channel, returned in an API
response), the input string is leaked verbatim.

## Reproduction (confirmed against `repro_min.bin`)
- Minimized input: `x` (1 byte; read by reproduce script)
- Error message: `purl must start with 'pkg:': 'x'`
- The `x` input is echoed verbatim in the error

## Impact
None in normal use (the input was already known to the caller). The echo is
helpful for debugging. Called out for completeness only.

## Status
**OPEN** — observation only, behavior is intentional.

## Remediation Hint
None required. If hardening, add a `safe_repr` helper that truncates long inputs
or hashes them for logging.

## Atheris Fuzzer Result
T3 Atheris: 0 oracle-mismatches. Echo is consistent across all inputs.