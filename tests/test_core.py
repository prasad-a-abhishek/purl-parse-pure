"""Test purlparse._core against all 15 spec acceptance criteria."""

import pytest
from purlparse import parse, PurlError


class TestAcceptanceCriteria:
    """All 15 ACs from spec."""

    def test_ac1_basic_npm(self):
        """AC1: parse('pkg:npm/lodash@4.17.21') -> type=npm, name=lodash, version=4.17.21"""
        r = parse("pkg:npm/lodash@4.17.21")
        assert r.type == "npm"
        assert r.name == "lodash"
        assert r.version == "4.17.21"
        assert r.namespace is None

    def test_ac2_npm_scoped(self):
        """AC2: parse('pkg:npm/@babel/cli@7.21.0') -> namespace=@babel, name=cli"""
        r = parse("pkg:npm/@babel/cli@7.21.0")
        assert r.type == "npm"
        assert r.namespace == "@babel"
        assert r.name == "cli"
        assert r.version == "7.21.0"

    def test_ac3_maven_colon_namespace(self):
        """AC3: parse('pkg:maven/org.apache.commons/commons-lang3@1.2.3') -> maven ':' separator"""
        r = parse("pkg:maven/org.apache.commons/commons-lang3@1.2.3")
        assert r.type == "maven"
        assert r.namespace == "org.apache.commons"
        assert r.name == "commons-lang3"
        assert r.version == "1.2.3"

    def test_ac4_qualifiers(self):
        """AC4: parse('pkg:pypi/django@4.2.0?classifier=ORM') -> qualifiers['classifier']='ORM'"""
        r = parse("pkg:pypi/django@4.2.0?classifier=ORM")
        assert r.type == "pypi"
        assert r.name == "django"
        assert r.version == "4.2.0"
        assert r.qualifiers.get("classifier") == "ORM"

    def test_ac5_subpath(self):
        """AC5: parse('pkg:gem/rails@7.0.0#README.md') -> subpath='README.md'"""
        r = parse("pkg:gem/rails@7.0.0#README.md")
        assert r.type == "gem"
        assert r.name == "rails"
        assert r.version == "7.0.0"
        assert r.subpath == "README.md"

    def test_ac6_invalid_raises(self):
        """AC6: parse('invalid') raises ValueError with 'purl' or 'pkg:' in message"""
        with pytest.raises(ValueError) as exc:
            parse("invalid")
        assert "purl" in str(exc.value).lower() or "pkg:" in str(exc.value)

    def test_ac7_roundtrip(self):
        """AC7: ParseResult.to_string() round-trips to same purl (modulo encoding)"""
        inputs = [
            "pkg:npm/lodash@4.17.21",
            "pkg:npm/@babel/cli@7.21.0",
            "pkg:maven/org.apache.commons/commons-lang3@1.2.3",
            "pkg:pypi/django@4.2.0?classifier=ORM",
            "pkg:gem/rails@7.0.0#README.md",
            "pkg:deb/debian/curl@7.88.1",
            "pkg:github.com/package-url/purl-spec@1.0.0",
        ]
        for original in inputs:
            r = parse(original)
            back = r.to_string()
            # Canonical form may differ slightly in encoding; verify parse(back) == original parse
            r2 = parse(back)
            assert r2.type == r.type, f"type mismatch for {original}"
            assert r2.namespace == r.namespace, f"namespace mismatch for {original}"
            assert r2.name == r.name, f"name mismatch for {original}"
            assert r2.version == r.version, f"version mismatch for {original}"
            assert r2.qualifiers == r.qualifiers, f"qualifiers mismatch for {original}"
            assert r2.subpath == r.subpath, f"subpath mismatch for {original}"

    def test_ac8_url_decode_version(self):
        """AC8: parse('pkg:npm/lodash%404.17.21') decodes %40 to @ in version"""
        r = parse("pkg:npm/lodash%404.17.21")
        assert r.type == "npm"
        assert r.name == "lodash"
        assert r.version == "@4.17.21"

    def test_ac9_deb_style(self):
        """AC9: parse('pkg:deb/debian/curl@7.88.1') handles debian-style purl"""
        r = parse("pkg:deb/debian/curl@7.88.1")
        assert r.type == "deb"
        assert r.namespace == "debian"
        assert r.name == "curl"
        assert r.version == "7.88.1"

    def test_ac10_github_shorthand(self):
        """AC10: parse('pkg:github.com/package-url/purl-spec@1.0.0') handles github.com shorthand"""
        r = parse("pkg:github.com/package-url/purl-spec@1.0.0")
        assert r.type == "github"
        assert r.namespace == "github.com/package-url"
        assert r.name == "purl-spec"
        assert r.version == "1.0.0"

    def test_ac11_empty_and_pkg_colon(self):
        """AC11: parse('') and parse('pkg:') raise ValueError"""
        with pytest.raises(ValueError):
            parse("")
        with pytest.raises(ValueError):
            parse("pkg:")
        with pytest.raises(ValueError):
            parse("pkg:npm/")  # empty name

    def test_ac12_equality_and_hash(self):
        """AC12: Two ParseResult from identical purl compare equal and have same hash"""
        r1 = parse("pkg:npm/lodash@4.17.21")
        r2 = parse("pkg:npm/lodash@4.17.21")
        assert r1 == r2
        assert hash(r1) == hash(r2)
        # Also test in set/dict
        s = {r1, r2}
        assert len(s) == 1

    def test_ac13_duplicate_qualifier_delimiter(self):
        """AC13: parse('pkg:npm/lodash@4.17.21?foo=bar?baz=qux') raises ValueError (duplicate ?)"""
        with pytest.raises(ValueError) as exc:
            parse("pkg:npm/lodash@4.17.21?foo=bar?baz=qux")
        assert "?" in str(exc.value) or "multiple" in str(exc.value).lower()

    def test_ac14_qualifier_hash_delimiter(self):
        """AC14: Qualifier values containing '#' correctly stop at '#' delimiter"""
        r = parse("pkg:npm/lodash@4.17.21?foo=bar%23baz#subpath")
        assert r.qualifiers.get("foo") == "bar#baz"
        assert r.subpath == "subpath"

    def test_ac15_case_normalization(self):
        """AC15: Namespace and name containing uppercase are lowercased"""
        r = parse("pkg:npm/@Babel/CLI@7.21.0")
        assert r.namespace == "@babel"
        assert r.name == "cli"
        r2 = parse("pkg:NPM/Lodash@4.17.21")
        assert r2.type == "npm"
        assert r2.name == "lodash"


class TestBasic:
    """Smoke tests for basic parse."""

    def test_parse_returns_parse_result(self):
        from purlparse import ParseResult
        r = parse("pkg:npm/lodash@4.17.21")
        assert isinstance(r, ParseResult)

    def test_pypi_simple(self):
        r = parse("pkg:pypi/requests@2.28.0")
        assert r.type == "pypi"
        assert r.name == "requests"
        assert r.version == "2.28.0"

    def test_go_simple(self):
        r = parse("pkg:go/github.com/golang/mock@1.5.0")
        assert r.type == "go"
        assert r.namespace == "github.com/golang"
        assert r.name == "mock"
        assert r.version == "1.5.0"

    def test_qualifiers_multiple(self):
        r = parse("pkg:pypi/django@4.2.0?classifier=ORM&zip_safe=true")
        assert r.qualifiers["classifier"] == "ORM"
        assert r.qualifiers["zip_safe"] == "true"

    def test_qualifiers_url_decoded(self):
        r = parse("pkg:pypi/django@4.2.0?name=django%2Dcore")
        assert r.qualifiers["name"] == "django-core"

    def test_qualifiers_empty_value(self):
        r = parse("pkg:pypi/django@4.2.0?foo=")
        assert r.qualifiers["foo"] == ""

    def test_subpath_url_decoded(self):
        r = parse("pkg:gem/rails@7.0.0#README%2Emd")
        assert r.subpath == "README.md"

    def test_subpath_only(self):
        r = parse("pkg:npm/lodash#lib/index.js")
        assert r.subpath == "lib/index.js"

    def test_no_version(self):
        r = parse("pkg:npm/lodash")
        assert r.type == "npm"
        assert r.name == "lodash"
        assert r.version is None

    def test_no_namespace(self):
        r = parse("pkg:npm/lodash@1.0.0")
        assert r.namespace is None

    def test_special_chars_in_version(self):
        r = parse("pkg:npm/lodash@4.17.21-beta.1")
        assert r.version == "4.17.21-beta.1"


class TestErrors:
    """Error path tests."""

    def test_missing_scheme(self):
        with pytest.raises(ValueError) as exc:
            parse("npm/lodash@4.17.21")
        assert "pkg:" in str(exc.value)

    def test_missing_type(self):
        with pytest.raises(ValueError):
            parse("pkg:/lodash@4.17.21")

    def test_missing_name(self):
        with pytest.raises(ValueError):
            parse("pkg:npm/")

    def test_missing_name_after_namespace(self):
        with pytest.raises(ValueError):
            parse("pkg:npm/@babel/")

    def test_duplicate_at_sign(self):
        with pytest.raises(ValueError):
            parse("pkg:npm/lodash@@4.17.21")

    def test_qualifier_missing_key(self):
        r = parse("pkg:npm/lodash@4.17.21?=value")
        assert r.qualifiers.get("") == "value"


class TestMaven:
    """Maven-specific tests."""

    def test_maven_no_version(self):
        r = parse("pkg:maven/org.apache.commons/commons-lang3")
        assert r.namespace == "org.apache.commons"
        assert r.name == "commons-lang3"
        assert r.version is None

    def test_maven_with_qualifiers(self):
        r = parse("pkg:maven/org.apache.commons/commons-lang3@1.2.3?type=jar")
        assert r.namespace == "org.apache.commons"
        assert r.name == "commons-lang3"
        assert r.version == "1.2.3"
        assert r.qualifiers["type"] == "jar"


class TestEdgeCases:
    """Edge case tests."""

    def test_version_with_slash(self):
        r = parse("pkg:go/github.com/user/repo@v1.0.0+ds1")
        assert r.version == "v1.0.0+ds1"

    def test_large_qualifier_count(self):
        qs = "&".join(f"k{i}=v{i}" for i in range(20))
        r = parse(f"pkg:npm/lodash@4.17.21?{qs}")
        assert len(r.qualifiers) == 20

    def test_version_with_colon(self):
        r = parse("pkg:maven/a/b@1.0:final")
        assert r.version == "1.0:final"

    def test_npm_scope_without_slash(self):
        with pytest.raises(ValueError):
            parse("pkg:npm/@babelcli")

    def test_type_is_case_insensitive(self):
        r = parse("pkg:NPM/lodash@4.17.21")
        assert r.type == "npm"

    def test_long_name(self):
        r = parse("pkg:npm/somewhatlongpackagename@1.0.0")
        assert r.name == "somewhatlongpackagename"

    def test_numeric_name(self):
        r = parse("pkg:npm/404@4.17.21")
        assert r.name == "404"

    def test_qualified_name_with_dots(self):
        r = parse("pkg:pypi/django.core.handlers@4.2.0")
        assert r.name == "django.core.handlers"
