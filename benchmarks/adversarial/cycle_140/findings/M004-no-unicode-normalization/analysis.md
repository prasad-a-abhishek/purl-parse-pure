# M004 — No Unicode normalization (NFC vs NFKC vs NFD)

## Severity
**Medium** (Class A7 — unicode normalization, semantic ambiguity)

## Surface
`src/purlparse/_core.py:194` — `decoded_name = unquote(name)` (and similar at
lines 90, 94, 99, 191) — no `unicodedata.normalize(...)` step after `unquote()`.

## Root Cause
`urllib.parse.unquote()` decodes percent-encoded bytes but does NOT normalize
the resulting Unicode string. The same visual character can be encoded as:
- Single codepoint (NFC composed): `é` = `U+00E9`
- Multi-codepoint (NFD decomposed): `é` = `U+0065 U+0301`

Two parses of "the same" purl by different clients produce **non-equal**
`ParseResult` objects (and unequal hashes), defeating deduplication and equality
checks.

## Reproduction (confirmed against `repro_min.bin`)
- Minimized input: `pkg:npm/xé` (NFC: 2 bytes in name, `c3 a9` = U+00E9)
- NFD equivalent: `pkg:npm/xe\xcc\x81` (4 bytes in name: `65 cc 81` = U+0065 U+0301)
- Both parse successfully, both produce `name='é'` visually identical
- `r1 == r2` returns **False** (verified); `hash(r1) != hash(r2)`

## Impact
- **Deduplication failure**: a package-URL deduplication service using
  `ParseResult.__eq__` will treat the two forms as different packages,
  producing false negatives.
- **Caching miss**: caches keyed by `ParseResult` will store both forms as
  separate entries.
- **Spec compliance gap**: ECMA-424 is silent on normalization form, but
  NFKC/NFC is the de facto industry convention (used by package-url/python-packageurl).

## Status
**OPEN** — confirmed, no fix applied in T4.

## Remediation Hint
Apply `unicodedata.normalize("NFKC", ...)` in `ParseResult.__post_init__`
for `name`, `namespace`, `version`, and qualifier keys/values. Document the
chosen normalization form in the README.

Estimated fix: 4-6 LOC at `_types.py:55-60` (post_init) plus
`import unicodedata` at top of file.

## Atheris Fuzzer Result
T3 Atheris on all 5 surfaces (570M iterations) found 0 oracle-mismatches.
Atheris generates random bytes that occasionally include UTF-8 multi-byte
sequences, but the dedup-collision is a property of two separate parses, not a
single parse — not what Atheris tests for.