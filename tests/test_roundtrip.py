"""Round-trip tests: parse(s).to_string() == canonical(s)."""

import pytest
from purlparse import parse, ParseResult


ROUNDTRIP_CASES = [
    # Basic cases
    "pkg:npm/lodash@4.17.21",
    "pkg:pypi/django@4.2.0",
    "pkg:gem/rails@7.0.0",
    # Scoped npm
    "pkg:npm/@babel/cli@7.21.0",
    "pkg:npm/@types/node@18.0.0",
    # Maven
    "pkg:maven/org.apache.commons/commons-lang3@1.2.3",
    "pkg:maven/junit/junit@4.13.2",
    # Qualifiers
    "pkg:pypi/django@4.2.0?classifier=ORM",
    "pkg:pypi/django@4.2.0?classifier=ORM&zip_safe=true",
    "pkg:npm/lodash@4.17.21?foo=bar",
    # Subpath
    "pkg:gem/rails@7.0.0#README.md",
    "pkg:npm/lodash#lib/index.js",
    # Deb
    "pkg:deb/debian/curl@7.88.1",
    "pkg:deb/debian/apt@2.4.0",
    # GitHub
    "pkg:github.com/package-url/purl-spec@1.0.0",
    "pkg:github.com/package-url/purl-spec@v2.0.0-rc.1",
    # Go
    "pkg:go/github.com/golang/mock@1.5.0",
    "pkg:go/github.com/user/repo@latest",
    # No version
    "pkg:npm/lodash",
    "pkg:pypi/django",
    # No namespace
    "pkg:gem/rails",
    # Type variations
    "pkg:nuget/newtonsoft.json@13.0.1",
    "pkg:docker/nginx@latest",
    "pkg:rpm/epel-release@9.0",
    "pkg:conda/conda@4.12.0",
    "pkg:pub/http@0.13.0",
    "pkg:hackage/containers@0.6.5",
    "pkg:cargo/rand@0.8.4",
    "pkg:hex/potion@0.12.0",
]


class TestRoundtrip:
    """AC7: to_string() round-trip."""

    @pytest.mark.parametrize("purl", ROUNDTRIP_CASES)
    def test_roundtrip(self, purl):
        """parse(purl).to_string() is stable and re-parses to the same result."""
        r = parse(purl)
        back = r.to_string()
        r2 = parse(back)
        assert r == r2, f"round-trip failed for {purl!r}: got {back!r}"


class TestRoundtripEdge:
    """Additional round-trip edge cases."""

    def test_percent_encoded_version(self):
        # %40 is @ in the version string
        r = parse("pkg:npm/lodash%404.17.21")
        assert r.version == "@4.17.21"
        back = r.to_string()
        r2 = parse(back)
        assert r2.version == r.version

    def test_percent_encoded_qualifier_value(self):
        r = parse("pkg:npm/lodash@4.17.21?foo=bar%2Dbaz")
        assert r.qualifiers["foo"] == "bar-baz"

    def test_percent_encoded_subpath(self):
        r = parse("pkg:npm/lodash#lib%2Findex.js")
        assert r.subpath == "lib/index.js"

    def test_qualifier_hash_in_value(self):
        r = parse("pkg:npm/lodash@4.17.21?foo=bar%23baz#sub")
        assert r.qualifiers["foo"] == "bar#baz"
        assert r.subpath == "sub"

    def test_complex_qualifiers(self):
        purl = "pkg:pypi/django@4.2.0?classifier=ORM&zip_safe=true&python_version=3.10"
        r = parse(purl)
        back = r.to_string()
        r2 = parse(back)
        assert r.qualifiers == r2.qualifiers

    def test_empty_qualifiers(self):
        r = ParseResult(type="npm", name="lodash", qualifiers={})
        assert "?" not in r.to_string()

    def test_empty_subpath(self):
        r = ParseResult(type="npm", name="lodash", subpath="")
        # empty subpath should not produce '#'
        assert "#" not in r.to_string()
