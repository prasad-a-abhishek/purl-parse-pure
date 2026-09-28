# cycle_140 — Adversary Remediation Log

Audit-trail of remediations applied to the cycle_140 adversary findings
(`cycle_140/adversary/fuzz/findings.jsonl` + `cycle_140/adversary/fuzz/FUZZING_REPORT.md`).

## fix1 — V002 + V003 closed; V001 documented-accepted

**Fix card**: t_f8221868 (parent: t_ba2594ba T5 FUZZING_REPORT)
**Cycle**: 140
**Repo**: purl-parse-pure
**Scope**: Invariant 21 (Total Public API Exception Safety) + PurlError contract drift

### Findings closed in this fix

| ID  | Severity | Class                                          | Status before | Status after fix1                       |
|-----|----------|------------------------------------------------|---------------|------------------------------------------|
| F-V002 | High | Invariant 21 — `parse()` not total over non-str input | OPEN      | **CLOSED — isinstance(str) guard added at `parse()` entry** |
| F-V003 | High | Invariant 11 — `PurlError` exported but never raised   | OPEN      | **CLOSED — all 12 `raise ValueError(...)` sites swapped to `raise PurlError(...)`** |

### Findings NOT closed in this fix (deferred per V2 scope)

| ID  | Severity | Status | Reason |
|-----|----------|--------|--------|
| F-V001 | High | DOCUMENTED_ACCEPTED | Percent-encoded control chars (`%00`, `%0A`, `%0D`, `%09`) bypass the raw-input control-char gate. Remediation requires either an unquote-then-gate refactor or a pre-scan regex (both >10 LOC, risk introducing round-trip regressions). Deferred to a future cycle if exploitable evidence emerges. Will be added to README Limitations section at ship-time. |

### Code changes (commit `fix1` on `wt/cycle140-fix1`)

```
src/purlparse/_core.py     | +13 / -12   (1 isinstance guard + 12 raise-site swaps)
tests/test_api_safety.py  | +171 / -0   (NEW: 42 parametrize-cases covering F-V002, F-V003, backward compat, valid-input regression)
cycle_140/adversary/fuzz/REMEDIATION_LOG.md  | +N / -0  (NEW: this file)
```

### Verification summary

All 8 V3 sub-checks PASS (see fix1 completion metadata for full output):

1. F-V002 reproducer (non-str inputs) → now raises PurlError, NOT TypeError/AttributeError
2. F-V003 reproducer (bad-purl inputs) → now raises PurlError, NOT raw ValueError
3. RFC 3986 §2.1 percent-encoding behavior unchanged for valid purls (AC1-AC10 still pass)
4. New regression tests added (`tests/test_api_safety.py`, 42 cases)
5. `pytest -q` → 216/216 pass (was 174 before fix1)
6. CLI exit codes unchanged for happy path (0) and bad input (1 with `PurlError:` on stderr)
7. Fresh-venv install in `/tmp/purlparse-fix1-venv` → works
8. Secret-scan CLEAN; `dependencies = []` preserved

### Backward compatibility statement

`PurlError` is defined as `class PurlError(ValueError): ...` in `src/purlparse/_errors.py`. This relationship is **unchanged** by fix1. Pre-existing user code that catches `ValueError` continues to work; new code can specifically catch `PurlError` to distinguish purl-parsing failures from other validation errors. `test_purlerror_is_valueerror_subclass` and `test_parse_badspec_is_catchable_as_valueerror` lock this invariant.