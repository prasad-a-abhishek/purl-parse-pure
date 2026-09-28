"""Atheris harness H4: CLI 'validate' subcommand surface of purl-parse-pure v0.1.0.

Fuzzes the `cmd_validate()` CLI handler. Validate is a boolean predicate:
exit 0 means valid purl, exit 1 means invalid. This exercises the same
parse() engine but through a different code path (it calls result.to_string()
on success). Ensures to_string() never raises on a successfully parsed purl.
"""

from __future__ import annotations

import atheris
import sys

from purlparse.__main__ import cmd_validate


def TestOneInput(data: bytes) -> None:
    """Atheris entry point for the CLI validate surface."""
    text = data.decode("utf-8", errors="replace")
    try:
        rc = cmd_validate([text])
        assert rc in (0, 1), f"cmd_validate returned unexpected exit code {rc!r}"
    except ValueError:
        pass
    except Exception:
        raise


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()