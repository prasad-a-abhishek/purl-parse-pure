"""Tests for ParseResult dataclass and TYPE_REGISTRY."""

import pytest
from purlparse import ParseResult, TYPE_REGISTRY


class TestParseResultDataclass:
    """ParseResult creation and basic properties."""

    def test_create_minimal(self):
        r = ParseResult(type="npm", name="lodash")
        assert r.type == "npm"
        assert r.name == "lodash"
        assert r.namespace is None
        assert r.version is None
        assert r.qualifiers == {}
        assert r.subpath is None

    def test_create_full(self):
        r = ParseResult(
            type="pypi",
            namespace="django",
            name="django",
            version="4.2.0",
            qualifiers={"classifier": "ORM"},
            subpath="README.md",
        )
        assert r.type == "pypi"
        assert r.namespace == "django"
        assert r.name == "django"
        assert r.version == "4.2.0"
        assert r.qualifiers["classifier"] == "ORM"
        assert r.subpath == "README.md"

    def test_type_lowercased(self):
        r = ParseResult(type="NPM", name="Lodash")
        assert r.type == "npm"
        assert r.name == "lodash"

    def test_namespace_lowercased(self):
        r = ParseResult(type="npm", namespace="@Babel", name="cli")
        assert r.namespace == "@babel"

    def test_name_lowercased(self):
        r = ParseResult(type="npm", name="CLI")
        assert r.name == "cli"


class TestParseResultEquality:
    """AC12: equality and hash."""

    def test_equal_identical(self):
        r1 = ParseResult(type="npm", name="lodash", version="4.17.21")
        r2 = ParseResult(type="npm", name="lodash", version="4.17.21")
        assert r1 == r2
        assert hash(r1) == hash(r2)

    def test_equal_from_parsed(self):
        from purlparse import parse
        r1 = parse("pkg:npm/lodash@4.17.21")
        r2 = parse("pkg:npm/lodash@4.17.21")
        assert r1 == r2
        assert hash(r1) == hash(r2)

    def test_not_equal_different_version(self):
        r1 = ParseResult(type="npm", name="lodash", version="4.17.21")
        r2 = ParseResult(type="npm", name="lodash", version="4.17.20")
        assert r1 != r2

    def test_not_equal_different_name(self):
        r1 = ParseResult(type="npm", name="lodash", version="4.17.21")
        r2 = ParseResult(type="npm", name="underscore", version="4.17.21")
        assert r1 != r2

    def test_not_equal_different_namespace(self):
        r1 = ParseResult(type="npm", namespace="@babel", name="cli")
        r2 = ParseResult(type="npm", namespace="@foo", name="cli")
        assert r1 != r2

    def test_not_equal_different_qualifiers(self):
        r1 = ParseResult(type="npm", name="lodash", qualifiers={"foo": "bar"})
        r2 = ParseResult(type="npm", name="lodash", qualifiers={"foo": "baz"})
        assert r1 != r2

    def test_not_equal_different_subpath(self):
        r1 = ParseResult(type="npm", name="lodash", subpath="a")
        r2 = ParseResult(type="npm", name="lodash", subpath="b")
        assert r1 != r2

    def test_not_equal_wrong_type(self):
        r1 = ParseResult(type="npm", name="lodash")
        assert r1 != "npm/lodash"
        assert r1 != 42

    def test_hash_in_set(self):
        r1 = ParseResult(type="npm", name="lodash", version="4.17.21")
        r2 = ParseResult(type="npm", name="lodash", version="4.17.21")
        s = {r1, r2}
        assert len(s) == 1

    def test_hash_in_dict_key(self):
        r1 = ParseResult(type="npm", name="lodash", version="4.17.21")
        r2 = ParseResult(type="npm", name="underscore", version="1.0.0")
        d = {r1: "lodash", r2: "underscore"}
        assert d[r1] == "lodash"
        assert d[r2] == "underscore"

    def test_hash_qualifiers_order_independent(self):
        r1 = ParseResult(type="npm", name="lodash", qualifiers={"a": "1", "b": "2"})
        r2 = ParseResult(type="npm", name="lodash", qualifiers={"b": "2", "a": "1"})
        assert r1 == r2
        assert hash(r1) == hash(r2)


class TestTypeRegistry:
    """TYPE_REGISTRY entries."""

    def test_npm_entry(self):
        entry = TYPE_REGISTRY["npm"]
        assert entry["namespace_sep"] == "/"

    def test_pypi_entry(self):
        entry = TYPE_REGISTRY["pypi"]
        assert entry["namespace_sep"] == "/"

    def test_maven_entry(self):
        entry = TYPE_REGISTRY["maven"]
        assert entry["namespace_sep"] == ":"
        assert entry["name_sep"] == "/"

    def test_go_entry(self):
        entry = TYPE_REGISTRY["go"]
        assert entry["namespace_sep"] == "/"

    def test_deb_entry(self):
        entry = TYPE_REGISTRY["deb"]
        assert entry["namespace_sep"] == "/"

    def test_github_entry(self):
        entry = TYPE_REGISTRY["github"]
        assert entry["namespace_sep"] == "/"

    def test_unknown_type_fallback(self):
        from purlparse import parse
        # Unknown types fall back to '/' separator
        r = parse("pkg:unknown/type/name@1.0.0")
        assert r.type == "unknown"
        assert r.namespace == "type"
        assert r.name == "name"
        assert r.version == "1.0.0"


class TestToString:
    """ParseResult.to_string() tests."""

    def test_minimal(self):
        r = ParseResult(type="npm", name="lodash")
        assert r.to_string() == "pkg:npm/lodash"

    def test_with_version(self):
        r = ParseResult(type="npm", name="lodash", version="4.17.21")
        assert r.to_string() == "pkg:npm/lodash@4.17.21"

    def test_with_namespace(self):
        r = ParseResult(type="npm", namespace="@babel", name="cli")
        assert r.to_string() == "pkg:npm/@babel/cli"

    def test_with_namespace_and_version(self):
        r = ParseResult(type="npm", namespace="@babel", name="cli", version="7.21.0")
        assert r.to_string() == "pkg:npm/@babel/cli@7.21.0"

    def test_with_qualifiers(self):
        r = ParseResult(type="npm", name="lodash", qualifiers={"foo": "bar"})
        assert "pkg:npm/lodash?foo=bar" == r.to_string()

    def test_with_subpath(self):
        r = ParseResult(type="npm", name="lodash", subpath="lib/index.js")
        assert r.to_string() == "pkg:npm/lodash#lib/index.js"

    def test_qualifiers_sorted(self):
        r = ParseResult(type="npm", name="lodash", qualifiers={"z": "1", "a": "2", "m": "3"})
        s = r.to_string()
        # Should be sorted alphabetically
        assert "a=2" in s
        assert "m=3" in s
        assert "z=1" in s
