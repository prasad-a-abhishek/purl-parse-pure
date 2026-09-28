"""CLI smoke tests for purl-parse-pure."""

import json
import subprocess
import sys

import pytest


class TestCLIParse:
    """python -m purlparse parse"""

    def test_parse_valid(self):
        result = subprocess.run(
            [sys.executable, "-m", "purlparse", "parse", "pkg:gem/rails@7.0.0"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["type"] == "gem"
        assert data["name"] == "rails"
        assert data["version"] == "7.0.0"

    def test_parse_invalid(self):
        result = subprocess.run(
            [sys.executable, "-m", "purlparse", "parse", "invalid"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "pkg:" in result.stderr.lower() or "purl" in result.stderr.lower()

    def test_parse_missing_arg(self):
        result = subprocess.run(
            [sys.executable, "-m", "purlparse", "parse"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1


class TestCLIDecode:
    """python -m purlparse decode"""

    def test_decode_valid(self):
        result = subprocess.run(
            [sys.executable, "-m", "purlparse", "decode", "pkg:npm/lodash%404.17.21"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["version"] == "@4.17.21"

    def test_decode_invalid(self):
        result = subprocess.run(
            [sys.executable, "-m", "purlparse", "decode", "not-a-purl"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1


class TestCLIValidate:
    """python -m purlparse validate"""

    def test_validate_valid(self):
        result = subprocess.run(
            [sys.executable, "-m", "purlparse", "validate", "pkg:pypi/django@4.2.0"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid"] is True

    def test_validate_invalid(self):
        result = subprocess.run(
            [sys.executable, "-m", "purlparse", "validate", "not-a-purl"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["valid"] is False


class TestCLIHelp:
    """--help and unknown commands."""

    def test_no_args_shows_usage(self):
        result = subprocess.run(
            [sys.executable, "-m", "purlparse"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Usage" in result.stdout or "command" in result.stdout

    def test_unknown_command(self):
        result = subprocess.run(
            [sys.executable, "-m", "purlparse", "unknown", "pkg:npm/lodash"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Unknown command" in result.stderr


class TestCLIOutputs:
    """Verify CLI outputs are valid JSON."""

    def test_parse_json_structure(self):
        result = subprocess.run(
            [sys.executable, "-m", "purlparse", "parse", "pkg:npm/@babel/cli@7.21.0"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        # All expected keys present
        assert "type" in data
        assert "namespace" in data
        assert "name" in data
        assert "version" in data
        assert "qualifiers" in data
        assert "subpath" in data

    def test_validate_json_structure(self):
        result = subprocess.run(
            [sys.executable, "-m", "purlparse", "validate", "pkg:gem/rails@7.0.0"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "valid" in data
        assert "purl" in data
