"""CLI entry point for purl-parse-pure.

Usage:
    python -m purlparse parse    "pkg:npm/lodash@4.17.21"
    python -m purlparse decode   "pkg:npm/lodash%404.17.21"
    python -m purlparse validate  "pkg:pypi/django@4.2.0"
"""

from __future__ import annotations

import json
import sys

from ._core import parse
from ._errors import PurlError


def _result_dict(result):
    return {
        "type": result.type,
        "namespace": result.namespace,
        "name": result.name,
        "version": result.version,
        "qualifiers": result.qualifiers,
        "subpath": result.subpath,
    }


def cmd_parse(args: list[str]) -> int:
    """Parse a purl string and output JSON."""
    if len(args) < 1:
        print("Error: 'parse' requires a purl argument", file=sys.stderr)
        return 1
    purl = args[0]
    try:
        result = parse(purl)
        print(json.dumps(_result_dict(result), indent=2))
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_decode(args: list[str]) -> int:
    """URL-decode a purl string and output JSON."""
    if len(args) < 1:
        print("Error: 'decode' requires a purl argument", file=sys.stderr)
        return 1
    purl = args[0]
    try:
        result = parse(purl)
        print(json.dumps(_result_dict(result), indent=2))
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_validate(args: list[str]) -> int:
    """Validate a purl string (exit 0 if valid, 1 if invalid)."""
    if len(args) < 1:
        print("Error: 'validate' requires a purl argument", file=sys.stderr)
        return 1
    purl = args[0]
    try:
        result = parse(purl)
        print(json.dumps({"valid": True, "purl": result.to_string()}, indent=2))
        return 0
    except ValueError as e:
        print(json.dumps({"valid": False, "error": str(e)}, indent=2))
        return 1


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 1:
        print("Usage: python -m purlparse <command> [args]")
        print("Commands: parse, decode, validate")
        return 1

    cmd = argv[0]
    args = argv[1:]

    if cmd == "parse":
        return cmd_parse(args)
    elif cmd == "decode":
        return cmd_decode(args)
    elif cmd == "validate":
        return cmd_validate(args)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print("Commands: parse, decode, validate")
        return 1


if __name__ == "__main__":
    sys.exit(main())
