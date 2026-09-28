"""Atheris harness H5: URL-decode / unquote edge cases for purl-parse-pure v0.1.0.

The package's percent-decoding chain uses stdlib urllib.parse.unquote at six
sites (name, namespace, version, subpath, qualifier keys, qualifier values).
This harness exercises ALL of those sites by feeding parse() inputs that
contain adversarial percent-encoding patterns:

- Truncated '%' at end of string
- '%' followed by non-hex chars ('%zz', '%1', '%XY')
- Stray '%' in the middle of a name ('a%b')
- High-percent character sequences that could trigger overlong UTF-8
- Valid percent sequences ('%40' = '@', '%2F' = '/', '%3F' = '?')

Property: parse() must either raise ValueError (with a message) or return
a ParseResult whose .to_string() does not raise. A crash on any of these
inputs is a finding -- the percent-decoding chain must be total on byte input.
"""

from __future__ import annotations

import atheris
import sys

from purlparse import ParseResult, parse


def TestOneInput(data: bytes) -> None:
    """Atheris entry point for unquote edge-case fuzzing."""
    text = data.decode("utf-8", errors="replace")
    try:
        result = parse(text)
        # If parse succeeded, to_string must also succeed (idempotent property).
        if isinstance(result, ParseResult):
            rendered = result.to_string()
            assert isinstance(rendered, str), (
                f"to_string() returned non-str: type={type(rendered).__name__!r}"
            )
    except ValueError:
        # Expected: malformed purl with undecodable percent -> ValueError
        pass
    except Exception:
        # Unhandled crash in percent-decoding chain -> Atheris finding.
        raise


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()