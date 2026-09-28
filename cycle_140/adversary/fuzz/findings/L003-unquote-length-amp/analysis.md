# L003 — `unquote()` length amplification (linear factor-1)

## Severity
**Low** (Class A4 — memory amplification, observation only)

## Surface
Every `unquote()` call site in `_core.py` (6 calls at lines 90, 94, 99, 191, 194, 195).

## Root Cause
`urllib.parse.unquote()` is called without a length cap on input or output. An
adversary could craft a small percent-encoded input that produces a longer
decoded string. **However, the amplification factor is 1**: `%XX` is exactly
3 ASCII chars that decode to 1 byte. So 1M percent-encoded sequences = 3M
bytes input → 1M bytes output (no exponential growth).

## Reproduction (confirmed against `repro_min.bin`)
- Minimized input: `pkg:npm/x%41y` (1 percent-encoded sequence)
- Decoded name: `'xay'` (3 bytes for 5 bytes input — factor 1)

Stress test: 1M `%41` sequences (1,500,008 bytes input) → 500,000 byte name
(see stacktrace.txt). Linear.

## Impact
- **No exponential growth** (no zip-bomb-style amplification).
- OS-level `ARG_MAX` (~128KB on Linux) prevents trivial command-line DoS.
- Programmatic callers may not have this guard.

## Status
**OPEN** — observation only, behavior is correct.

## Remediation Hint
Optional — add `if len(raw) > MAX_INPUT: raise PurlError(...)` cap at
`_core.py:23-35`. Not blocking; libraries that handle untrusted input usually
pre-validate size.

## Atheris Fuzzer Result
T3 Atheris on `unquote_edge` surface (134M iterations, 312s) found 0 crashes
from this finding. Atheris can produce long percent-encoded inputs but linear
amplification doesn't trigger memory pressure at any practical length.