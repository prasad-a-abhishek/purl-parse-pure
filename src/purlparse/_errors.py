"""Zero-dependency ECMA-424 / SPDX Package URL (purl) parser."""

from __future__ import annotations


class PurlError(ValueError):
    """Raised when a string cannot be parsed as a valid purl."""

    pass
