"""Type registry and ParseResult dataclass for purl parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import unquote

# Type-specific name/namespace separator rules
# key: purl type (lowercase)
# value: dict with 'namespace_sep' (char used to split namespace from name) and 'name_sep' (char for sub-segments within name)
TYPE_REGISTRY: dict[str, dict[str, str | None]] = {
    # npm/pypi/gem: namespace separated by '/', name after last '/'
    "npm": {"namespace_sep": "/", "name_sep": None},
    "pypi": {"namespace_sep": "/", "name_sep": None},
    "gem": {"namespace_sep": "/", "name_sep": None},
    # maven: namespace separated by ':' (org.apache.commons:name:1.2.3), name after last ':'
    "maven": {"namespace_sep": ":", "name_sep": "/"},
    # go/deb/github: '/' used throughout; first segment is namespace
    "go": {"namespace_sep": "/", "name_sep": None},
    "deb": {"namespace_sep": "/", "name_sep": None},
    "github": {"namespace_sep": "/", "name_sep": None},
    "github.com": {"namespace_sep": "/", "name_sep": None},
    # nuget, docker, rpm, etc. fall back to '/' separator
    "nuget": {"namespace_sep": "/", "name_sep": None},
    "docker": {"namespace_sep": "/", "name_sep": None},
    "rpm": {"namespace_sep": "/", "name_sep": None},
    "conda": {"namespace_sep": "/", "name_sep": None},
    "pub": {"namespace_sep": "/", "name_sep": None},
    "hackage": {"namespace_sep": "/", "name_sep": None},
    "cargo": {"namespace_sep": "/", "name_sep": None},
    "hex": {"namespace_sep": "/", "name_sep": None},
}


@dataclass
class ParseResult:
    """Result of parsing a purl string.

    Attributes:
        type: Package type (e.g., 'npm', 'pypi', 'gem', 'maven').
        namespace: Optional namespace segment, lowercased.
        name: Package name, lowercased.
        version: Optional version string, URL-decoded.
        qualifiers: Optional dict of key-value qualifier strings, URL-decoded.
        subpath: Optional subpath fragment, URL-decoded.
    """

    type: str
    name: str
    namespace: str | None = None
    version: str | None = None
    qualifiers: dict[str, str] = field(default_factory=dict)
    subpath: str | None = None

    def __post_init__(self) -> None:
        # Normalize type to lowercase
        object.__setattr__(self, "type", self.type.lower())
        if self.namespace is not None:
            object.__setattr__(self, "namespace", self.namespace.lower())
        object.__setattr__(self, "name", self.name.lower())

    def to_string(self) -> str:
        """Canonicalize back to a purl string.

        Returns:
            A canonical purl string representation.
        """
        # Build canonical purl: pkg:{type}[/{namespace}][/{name}][@{version}][?qualifiers][#subpath]
        # AC10: github.com shorthand uses 'pkg:github.com/...' as canonical form
        type_part = self.type
        if self.type == "github" and self.namespace and self.namespace.startswith("github.com/"):
            type_part = "github.com"
            # namespace for to_string is the part after 'github.com/'
            ns_for_string = self.namespace[len("github.com/"):]
        else:
            ns_for_string = self.namespace

        parts = [f"pkg:{type_part}"]

        if ns_for_string:
            parts.append("/")  # separator between type and namespace
            parts.append(ns_for_string)
            parts.append("/")  # separator between namespace and name
            parts.append(self.name)
        else:
            parts.append("/")
            parts.append(self.name)

        if self.version:
            # Re-encode the version: '@' -> '%40' in to_string.
            # A version starting with '@' (e.g., "@4.17.21") is stored when the original
            # purl used %40 as the version delimiter (AC8).  In canonical form we emit
            # %40 so to_string() round-trips correctly through the parser.
            version = self.version
            version = version.replace("%", "%25")
            version = version.replace("#", "%23")
            if version.startswith("@"):
                version = "%40" + version[1:]
            parts.append(f"@{version}")

        if self.qualifiers:
            qs = "&".join(
                f"{k}={v.replace('%', '%25').replace('#', '%23').replace('&', '%26').replace('=', '%3D')}"
                for k, v in sorted(self.qualifiers.items())
            )
            parts.append(f"?{qs}")

        if self.subpath:
            sp = self.subpath.replace("%", "%25").replace("#", "%23")
            parts.append(f"#{sp}")

        return "".join(parts)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ParseResult):
            return NotImplemented
        return (
            self.type == other.type
            and self.namespace == other.namespace
            and self.name == other.name
            and self.version == other.version
            and self.qualifiers == other.qualifiers
            and self.subpath == other.subpath
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.type,
                self.namespace,
                self.name,
                self.version,
                tuple(sorted(self.qualifiers.items())) if self.qualifiers else None,
                self.subpath,
            )
        )
