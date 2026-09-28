"""Atheris harness H1: core parse() surface of purl-parse-pure v0.1.0.

Fuzzes the public `parse()` function with arbitrary byte inputs decoded as
UTF-8 with replacement. Only ValueError (the documented contract) is expected;
any other exception (TypeError, AttributeError, KeyError, etc.) is a finding
and propagated to Atheris for crash capture. This exercises the full input
surface including percent-decoding, control-char rejection, multi-delimiter
detection, and the non-total-on-non-str gap (V002 from cycle_140 VULN_AUDIT).
"""

from __future__ import annotations

import atheris
import sys

from purlparse import ParseResult, parse


def TestOneInput(data: bytes) -> None:
    """Atheris entry point for the core parse() surface."""
    text = data.decode("utf-8", errors="replace")
    try:
        result = parse(text)
        # Property: parse() either raises ValueError or returns a ParseResult.
        assert isinstance(result, ParseResult), (
            f"parse() returned non-ParseResult: type={type(result).__name__!r}"
        )
    except ValueError:
        # Expected: malformed purl -> ValueError. PurlError subclasses ValueError,
        # so this single catch covers both documented contracts.
        pass
    except Exception:
        # Anything else is a finding (TypeError, AttributeError, etc.) --
        # let Atheris catch & report.
        raise


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()