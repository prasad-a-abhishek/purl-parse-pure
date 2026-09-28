"""API-safety regression tests for purl-parse-pure.

These tests lock down the Invariant 21 (Total Public API Exception Safety)
and PurlError-only contract fixes introduced after cycle_140/adversary.
They guarantee that:

* F-V002 stays fixed: ``parse()`` is total over arbitrary input — passing
  ``None``, ``bytes``, ``int``, ``float``, or ``bool`` raises
  ``PurlError``, never ``TypeError`` / ``AttributeError``.
* F-V003 stays fixed: every documented parser failure raises the
  exported ``PurlError`` type, not a raw ``ValueError``.
* Backward compatibility is preserved: ``PurlError`` is a ``ValueError``
  subclass so existing ``except ValueError:`` handlers keep catching it.
"""

from __future__ import annotations

from typing import Any

import pytest

from purlparse import PurlError, parse


class TestPurlErrorIsValueError:
    """PurlError MUST remain a ValueError subclass (backward compat)."""

    def test_purlerror_is_valueerror_subclass(self):
        assert issubclass(PurlError, ValueError)

    def test_purlerror_instance_is_valueerror(self):
        # Direct construction is allowed and produces an instance that
        # is also catchable as ValueError.
        err = PurlError("synthetic")
        assert isinstance(err, ValueError)
        assert isinstance(err, PurlError)
        assert str(err) == "synthetic"


class TestNonStrInputsRaisePurlError:
    """F-V002 regression: parse() must be total over arbitrary input."""

    @pytest.mark.parametrize(
        "bad_input",
        [
            None,
            b"pkg:npm/foo",
            b"",
            123,
            0,
            -1,
            3.14,
            float("inf"),
            float("nan"),
            True,
            False,
            ["pkg:npm/foo"],
            {"purl": "pkg:npm/foo"},
            ("pkg:npm/foo",),
        ],
    )
    def test_parse_non_str_returns_purlerror(self, bad_input):
        """Non-str inputs must raise PurlError, NOT TypeError/AttributeError.

        ``bad_input: Any`` is intentional — we deliberately violate the
        static type contract of ``parse(purl: str)`` to verify the
        Invariant-21 total-over-arbitrary-input guard."""
        with pytest.raises(PurlError):
            parse(bad_input)  # type: ignore[arg-type]

    def test_parse_none_does_not_raise_typeerror(self):
        """Specifically guard the F-V002 reproducer: ``parse(None)`` must
        raise PurlError, not the raw ``TypeError`` that motivated the fix.
        The ``# type: ignore[arg-type]`` is intentional: the whole point of
        the test is to violate the static type contract of ``parse()``."""
        try:
            parse(None)  # type: ignore[arg-type]
        except PurlError:
            pass  # expected after fix1
        except TypeError as e:  # pragma: no cover -- regression marker
            pytest.fail(
                f"F-V002 regression: parse(None) raised raw TypeError: {e!r}"
            )
        else:  # pragma: no cover -- regression marker
            pytest.fail("F-V002 regression: parse(None) did not raise")

    def test_parse_bytes_does_not_raise_typeerror(self):
        """The original F-V002 reproducer: ``parse(b'pkg:npm/foo')``.
        ``# type: ignore[arg-type]`` intentional — see test_parse_none."""
        try:
            parse(b"pkg:npm/foo")  # type: ignore[arg-type]
        except PurlError:
            pass
        except TypeError as e:  # pragma: no cover -- regression marker
            pytest.fail(
                f"F-V002 regression: parse(bytes) raised raw TypeError: {e!r}"
            )
        else:  # pragma: no cover -- regression marker
            pytest.fail("F-V002 regression: parse(bytes) did not raise")


class TestParseRaisesPurlErrorNotBareValueError:
    """F-V003 regression: parse() must raise PurlError, not raw ValueError."""

    @pytest.mark.parametrize(
        "bad_purl,expected_substring",
        [
            ("not a purl", "must start with 'pkg:'"),
            ("", "cannot be empty"),
            ("pkg:", "missing type after"),
            ("pkg:npm", "missing '/'"),
            ("pkg:npm/", "missing name after"),
            ("pkg:npm/lodash@@4.17.21", "multiple '@'"),
            ("pkg:npm/lodash?foo=bar?baz=qux", "multiple '?'"),
            # Note: 'multiple #'' raise site at _core.py:90 is unreachable
            # because first_special picks the EARLIEST delimiter, so '#' before '?'
            # captures everything as subpath and never re-enters qualifier parsing.
            ("pkg:npm/lodash\n@4.17.21", "invalid character"),
            ("pkg:npm/lodash\x00@4.17.21", "invalid character"),
            ("pkg:npm/\tlodash@4.17.21", "invalid character"),
            ("pkg:maven/lodash@1.0.0", "maven requires namespace"),
        ],
    )
    def test_parse_raises_purlerror_not_valueerror(
        self, bad_purl, expected_substring
    ):
        """Every documented parser failure raises PurlError, and the message
        matches the original ``ValueError`` text (only the type changed)."""
        with pytest.raises(PurlError) as exc_info:
            parse(bad_purl)
        # Message string unchanged from the pre-fix ValueError site.
        assert expected_substring in str(exc_info.value)

    def test_parse_badspec_is_catchable_as_valueerror(self):
        """Backward compat: pre-fix code that wrote ``except ValueError``
        must still catch the new ``PurlError``. Since ``PurlError`` IS a
        ``ValueError`` subclass, a single ``except ValueError`` catches both —
        no order gymnastics needed."""
        with pytest.raises(ValueError) as exc_info:
            parse("not a purl")
        # And that same exception is also a PurlError (subtype relationship).
        assert exc_info.type is PurlError

    def test_parse_raises_purlerror_not_bare_valueerror_class(self):
        """Specifically assert that the raised exception's *class* is
        ``PurlError`` (or a subclass thereof), not the bare ``ValueError``.
        We catch ``PurlError`` first because it is a ``ValueError`` subclass,
        so ``except ValueError`` after it would be unreachable."""
        try:
            parse("not a purl")
        except PurlError:
            return  # success
        # If we get here, the raised exception was NOT a PurlError.
        # Re-run with a bare ``ValueError`` catch to surface the bug:
        with pytest.raises(ValueError) as exc_info:
            parse("not a purl")
        # The raised class must be PurlError, not bare ValueError.
        assert exc_info.type is PurlError, (
            f"F-V003 regression: parse() raised {exc_info.type.__name__}, "
            f"expected PurlError. value={exc_info.value!r}"
        )


class TestRoundTripStillPassesForValidInputs:
    """The fix must NOT regress valid-input parsing (RFC 3986 §2.1)."""

    @pytest.mark.parametrize(
        "purl",
        [
            "pkg:npm/lodash@4.17.21",
            "pkg:pypi/django@4.2",
            "pkg:maven/org.apache.commons/commons-lang3@1.2.3",
            "pkg:go/github.com/a/b@v1.0.0",
            "pkg:deb/debian/curl@7.50.3-1",
            "pkg:github/a/b@1",
            "pkg:npm/lodash@4.17.21?os=linux&arch=x64",
            "pkg:npm/lodash@4.17.21#src/index.js",
            "pkg:npm/lodash@4.17.21?download_count=1#lib/lodash.js",
            "pkg:npm/lodash@4.17.21?name=%E4%B8%AD%E6%96%87",
            "pkg:go/github.com/a/b@0.0.0-20180820040428-4d7c8023c3d2",
        ],
    )
    def test_valid_purls_still_parse(self, purl):
        """Valid purls from the existing AC1-AC10 corpus must still parse."""
        result = parse(purl)
        assert result.type != ""
        assert result.name != ""