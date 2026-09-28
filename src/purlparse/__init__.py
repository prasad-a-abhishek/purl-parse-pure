"""Zero-dependency ECMA-424 / SPDX Package URL (purl) parser."""

from __future__ import annotations

from ._core import parse
from ._errors import PurlError
from ._types import TYPE_REGISTRY, ParseResult

__version__ = "0.1.1"

__all__ = ["parse", "ParseResult", "PurlError", "TYPE_REGISTRY", "__version__"]
