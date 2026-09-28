"""Atheris harness H3: CLI 'decode' subcommand surface of purl-parse-pure v0.1.0.

Fuzzes the `cmd_decode()` CLI handler. The decode subcommand URL-decodes
percent-encoded characters in the purl string and outputs JSON. cmd_decode
itself wraps parse() (which performs percent-decoding internally). This
harness exercises the URL-decoding edge cases -- truncated % sequences,
stray '%' at end of string, %00 null byte, multi-byte UTF-8 percent sequences.
"""

from __future__ import annotations

import atheris
import sys

from purlparse.__main__ import cmd_decode


def TestOneInput(data: bytes) -> None:
    """Atheris entry point for the CLI decode surface."""
    text = data.decode("utf-8", errors="replace")
    try:
        rc = cmd_decode([text])
        assert rc in (0, 1), f"cmd_decode returned unexpected exit code {rc!r}"
    except ValueError:
        pass
    except Exception:
        raise


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()