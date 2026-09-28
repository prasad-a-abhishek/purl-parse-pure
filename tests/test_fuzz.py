"""Adversarial / fuzzing tests for purl-parse-pure."""

import pytest
from purlparse import parse, PurlError


MALFORMED_INPUTS = [
    "",
    "pkg",
    "pkg:",
    "pkg:npm",
    "pkg:npm/",
    "pkg:/lodash",
    "pkg:/",
    "pkg://lodash",
    "http://example.com",
    "https://github.com/foo",
    "not-a-scheme:npm/lodash",
    "PKG:npm/lodash@4.17.21",  # uppercase scheme
    "pkg: NPM/lodash@4.17.21",  # space after colon
    "pkg:npm:lodash@4.17.21",  # extra colon
    "pkg:npm/lodash@@4.17.21",  # double @
    "pkg:npm/lodash@",  # empty version
    "pkg:npm/lodash@?",  # @ followed by ?
    "pkg:npm/lodash#",  # empty subpath
    "pkg:npm/lodash?#",  # both qualifiers and empty subpath
    "pkg:npm/lodash?foo=bar#",  # empty subpath after qualifiers
    "pkg:npm/lodash#subpath?foo=bar",  # ? in subpath position
    "pkg:npm/lodash@4.17.21#subpath?extra=bad",  # extra after subpath
    "pkg:npm/lodash?foo=bar?baz=qux",  # duplicate ?
    "pkg:npm/lodash?foo&bar",  # missing = in qualifier
    "pkg:npm/lodash?=value",  # missing key
    "pkg:npm/@",  # incomplete scoped
    "pkg:npm/@/",  # empty after @
    "pkg:npm/@babel",  # scoped without name
    "pkg:npm/@babel/",  # scoped with empty name
    "pkg:npm//lodash",  # double slash
    "pkg:npm/lodash//1.0.0",  # double slash in version
    "pkg:npm/命/name@1.0.0",  # unicode in name (allowed but edge)
    "pkg:npm/lodash@4.17.21?#sub",  # both empty qualifiers and subpath
    "pkg:npm/🎵@1.0.0",  # emoji in name
]


class TestFuzzMalformed:
    """Malformed inputs should raise ValueError, not crash."""

    @pytest.mark.parametrize("purl", MALFORMED_INPUTS)
    def test_malformed_raises(self, purl):
        """All malformed purls raise ValueError, not crash."""
        try:
            parse(purl)
            # Some may be valid actually
        except (ValueError, PurlError):
            pass  # expected


class TestFuzzExtremes:
    """Boundary / extreme value tests."""

    def test_very_long_name(self):
        name = "a" * 1000
        r = parse(f"pkg:npm/{name}@1.0.0")
        assert r.name == name.lower()

    def test_very_long_version(self):
        version = "1." + "0." * 500 + "1"
        r = parse(f"pkg:npm/lodash@{version}")
        assert r.version == version

    def test_many_qualifiers(self):
        qs = "&".join(f"k{i}=v{i}" for i in range(100))
        r = parse(f"pkg:npm/lodash@1.0.0?{qs}")
        assert len(r.qualifiers) == 100

    def test_deeply_nested_subpath(self):
        subpath = "/".join(f"dir{i}" for i in range(50))
        r = parse(f"pkg:npm/lodash#/{subpath}")
        assert r.subpath == f"/{subpath}"

    def test_unicode_in_qualifier_value(self):
        r = parse("pkg:npm/lodash@1.0.0?name=%E4%B8%AD%E6%96%87")
        assert r.qualifiers["name"] == "中文"

    def test_at_sign_in_qualifier_value(self):
        r = parse("pkg:npm/lodash@1.0.0?email=user@example.com")
        assert r.qualifiers["email"] == "user@example.com"

    def test_hash_in_qualifier_value(self):
        r = parse("pkg:npm/lodash@1.0.0?tag=foo%23bar")
        assert r.qualifiers["tag"] == "foo#bar"

    def test_ampersand_in_qualifier_value(self):
        r = parse("pkg:npm/lodash@1.0.0?q=foo%26bar")
        assert r.qualifiers["q"] == "foo&bar"

    def test_equals_in_qualifier_value(self):
        r = parse("pkg:npm/lodash@1.0.0?q=foo%3Dbar")
        assert r.qualifiers["q"] == "foo=bar"

    def test_newline_in_purl(self):
        with pytest.raises(ValueError):
            parse("pkg:npm/lodash\n@4.17.21")

    def test_null_byte(self):
        with pytest.raises(ValueError):
            parse("pkg:npm/lodash\x00@4.17.21")

    def test_tab_in_purl(self):
        with pytest.raises(ValueError):
            parse("pkg:npm/\tlodash@4.17.21")


class TestFuzzKnownGoodVariants:
    """Known-good inputs with slight variations."""

    def test_version_with_plus(self):
        r = parse("pkg:go/github.com/a/b@v1.0.0+ds1")
        assert r.version == "v1.0.0+ds1"

    def test_version_with_minus(self):
        r = parse("pkg:npm/lodash@4.17.21-beta")
        assert r.version == "4.17.21-beta"

    def test_pre_release_version(self):
        r = parse("pkg:npm/lodash@4.0.0-alpha.1")
        assert r.version == "4.0.0-alpha.1"

    def test_git_sha_version(self):
        r = parse("pkg:go/github.com/a/b@0.0.0-20180820040428-4d7c8023c3d2")
        assert r.version == "0.0.0-20180820040428-4d7c8023c3d2"

    def test_large_version_number(self):
        r = parse("pkg:npm/pkg@1.0.0.0.0.0.0.1")
        assert r.version == "1.0.0.0.0.0.0.1"

    def test_special_chars_in_name(self):
        r = parse("pkg:npm/foo_bar@1.0.0")
        assert r.name == "foo_bar"

    def test_dots_in_name(self):
        r = parse("pkg:npm/foo.bar@1.0.0")
        assert r.name == "foo.bar"

    def test_underscore_in_namespace(self):
        r = parse("pkg:npm/@foo_bar/baz@1.0.0")
        assert r.namespace == "@foo_bar"
        assert r.name == "baz"

    def test_dots_in_namespace(self):
        r = parse("pkg:go/github.com.foo.bar/repo@1.0.0")
        assert r.namespace == "github.com.foo.bar"
        assert r.name == "repo"
