# V001 — Percent-encoded control characters bypass pre-decode control-char gate

## Severity
**High** (Class A2 + A8 — null/control-char injection + encoding boundary)

## Surface
- Gate: `src/purlparse/_core.py:35-41` (control-char rejection operates on raw `purl` string)
- Bypass: `src/purlparse/_core.py:90, 94, 99, 191, 194, 195` (all `unquote()` call sites on name/namespace/version/qualifier/subpath)

## Root Cause
The control-character rejection at `_core.py:35-41` iterates the **raw** input string
and rejects any character where `ord(ch) < 32 or ord(ch) == 127`. The comment on line 38
explicitly states the intent: "Reject control characters (newline, null byte, tab, etc.)".

However, the percent-encoded forms (`%00`, `%0A`, `%0D`, `%09`, `%01`, `%1F`, `%7F`)
are themselves ASCII printable characters (digits, letters, `%`) and therefore
**pass the control-char gate**. After the gate runs, `unquote()` is called on the
relevant substring, decoding `%00` to `\x00` AFTER the gate has already approved
the input. The resulting `ParseResult.name` (or `namespace`, `version`, etc.)
contains the embedded control byte — exactly the bytes the gate was supposed
to reject.

## Reproduction (confirmed against `repro_min.bin`)
- Input: `pkg:npm/x%00y` (raw bytes: `706b673a6e706d2f7825303079`)
- Parsed name: `'x\x00y'` (contains literal NUL byte — see stacktrace.txt for full evidence)
- Round-trip via `to_string()`: `'pkg:npm/x\x00y'` — control byte is **NOT** re-encoded

Control-character equivalents all bypass identically:
| Input | Parsed `name` |
|---|---|
| `pkg:npm/foo%00bar` | `'foo\x00bar'` |
| `pkg:npm/foo%0Abar` | `'foo\nbar'` |
| `pkg:npm/foo%0Dbar` | `'foo\rbar'` |
| `pkg:npm/foo%09bar` | `'foo\tbar'` |

By contrast, the **literal**-byte equivalents are correctly rejected:
- `parse('pkg:npm/x\x00y')` → `ValueError: purl contains invalid character at position 9`
- `parse('pkg:npm/x\nbar')` → `ValueError: purl contains invalid character at position 9`

## Impact
A `ParseResult.name` containing `\x00` is itself dangerous when passed to downstream
consumers that write to logs, terminals, databases, or shells. Even though
`purl-parse-pure` itself does no I/O, the library's stated purpose (per README) is
to "parse a Package URL string into a ParseResult" — callers reasonably assume the
result is safe for logging and storage.

The control-byte ban is **explicitly** documented in the L38 comment ("Reject control
characters (newline, null byte, tab, etc.)") — the bypass is a clear
intent/implementation mismatch.

`to_string()` does not re-encode these bytes either (`_types.py:95-96` only handles
`%` and `#`, not `\x00`/`\n`/`\r`/`\t`), so round-trip perpetuates the embedded
control bytes indefinitely.

## Status
**OPEN** — bug confirmed, no fix applied in T4 (T4 is observation-only per V5).

## Remediation Hint (for T5 closure / future fix card)
Move the control-char check to **after** `unquote()` decoding (each substring
individually), OR expand the pre-decode check to scan for percent-encoded
sequences matching `%[0-9A-Fa-f]{2}` whose value decodes to `ord < 32 or 127`.

A third option: enforce `urllib.parse.quote_from_bytes(..., safe='', errors='strict')`
round-trip — `ParseResult` invariants should guarantee no embedded control bytes
regardless of how they entered.

Estimated fix: 5–10 LOC at `_core.py:35-41` plus `unquote()` call sites.

## Citations
- `src/purlparse/_core.py:35-41` — control-char gate (intent)
- `src/purlparse/_core.py:90, 94, 99, 191, 194, 195` — `unquote()` calls (bypass)
- `src/purlparse/_types.py:95-96` — `to_string()` re-encoding (silent round-trip)
- `cycle_140/adversary/fuzz/VULN_AUDIT.md` lines 122-175 — original VULN_AUDIT narrative

## Atheris Fuzzer Result
T3 Atheris run on `core_parse` surface (134,217,728 iterations, 312s) and 4 other
surfaces found **0 crashes** from this finding — the embedded null byte does not
crash the parser (the parser stores it as a regular string byte). The bypass is a
**silent correctness violation**, not a crash, which is why Atheris did not flag it.