"""Atheris harness H2: CLI 'parse' subcommand surface of purl-parse-pure v0.1.0.

Fuzzes the `cmd_parse()` CLI handler with arbitrary byte inputs. Calls the
function directly rather than spawning subprocess (deterministic, fast).
cmd_parse invokes parse() and JSON-dumps the result; on failure prints an
error and returns exit code 1. Only ValueError is expected; anything else
is a finding. Exercises the same parse() surface as H1 but through the CLI
return-code path, catching JSON serialization edge cases.
"""

from __future__ import annotations

import json

import atheris
import sys

from purlparse.__main__ import cmd_parse


def TestOneInput(data: bytes) -> None:
    """Atheris entry point for the CLI parse surface."""
    text = data.decode("utf-8", errors="replace")
    try:
        rc = cmd_parse([text])
        # rc must be 0 (success) or 1 (caught ValueError). Anything else is wrong.
        assert rc in (0, 1), f"cmd_parse returned unexpected exit code {rc!r}"
    except ValueError:
        # cmd_parse catches ValueError itself, but defensive: if a ValueError
        # ever leaks (shouldn't happen), treat it as expected.
        pass
    except Exception:
        # Unhandled TypeError, AttributeError, etc. -- Atheris finding.
        raise


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()