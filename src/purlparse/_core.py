"""ECMA-424 purl grammar state machine.

Grammar (simplified):
    purl       = "pkg:" type "/" name ["@" version] ["?" qualifiers] ["#" subpath]
              | "pkg:" type "/" namespace "/" name ...

The state machine:
1. Split off qualifiers (?...) and subpath (#...)
2. Extract type from the "pkg:" prefix
3. Split name/namespace from the remainder using type-specific rules
4. Split version (@...) from the name/namespace portion
5. URL-decode all decoded components
"""

from __future__ import annotations

from urllib.parse import unquote

from ._errors import PurlError
from ._types import TYPE_REGISTRY, ParseResult


def parse(purl: str) -> ParseResult:
    """Parse a purl string into a ParseResult.

    Args:
        purl: A Package URL string (e.g., "pkg:npm/lodash@4.17.21").

    Returns:
        A ParseResult with all parsed components.

    Raises:
        ValueError: If the string does not conform to the purl grammar.
    """
    if not purl:
        raise ValueError("purl cannot be empty")

    # Reject control characters (newline, null byte, tab, etc.)
    for i, ch in enumerate(purl):
        if ch in "\n\r\t\x00":
            raise ValueError(f"purl contains invalid character at position {i}: {purl!r}")

    # Step 1: Verify prefix "pkg:"
    if not purl.startswith("pkg:"):
        raise ValueError(f"purl must start with 'pkg:': {purl!r}")

    rest = purl[4:]  # everything after "pkg:"
    if not rest:
        raise ValueError(f"purl missing type after 'pkg:': {purl!r}")

    # Step 2: Split off qualifiers (?...) and subpath (#...)
    qualifiers: dict[str, str] = {}
    subpath: str | None = None
    qualifiers_raw: str | None = None
    subpath_raw: str | None = None

    qmark = rest.find("?")
    hash_idx = rest.find("#")

    first_special = len(rest)
    for pos in [qmark, hash_idx]:
        if pos != -1 and pos < first_special:
            first_special = pos

    if first_special < len(rest):
        first_char = rest[first_special]
        if first_char == "?":
            qualifiers_raw = rest[first_special + 1:]
            rest = rest[:first_special]
        elif first_char == "#":
            subpath_raw = rest[first_special + 1:]
            rest = rest[:first_special]

    # Step 3: Parse qualifiers
    if qualifiers_raw is not None:
        if "?" in qualifiers_raw:
            raise ValueError(f"purl has multiple '?' delimiters: {purl!r}")
        # AC14: '#' in qualifier value should stop at '#' delimiter
        hash_in_qual = qualifiers_raw.find("#")
        if hash_in_qual != -1:
            if subpath_raw is not None:
                raise ValueError(f"purl has multiple '#' delimiters: {purl!r}")
            subpath_raw = qualifiers_raw[hash_in_qual + 1:]
            qualifiers_raw = qualifiers_raw[:hash_in_qual]
        for pair in qualifiers_raw.split("&"):
            if not pair:
                continue
            eq_idx = pair.find("=")
            if eq_idx == -1:
                k = unquote(pair)
                qualifiers[k] = ""
            else:
                k = unquote(pair[:eq_idx])
                v = unquote(pair[eq_idx + 1:])
                qualifiers[k] = v

    # Step 4: Parse subpath
    if subpath_raw is not None:
        subpath = unquote(subpath_raw)

    # Step 5: Extract type — find first '/' after pkg:
    slash_idx = rest.find("/")
    if slash_idx == -1:
        raise ValueError(f"purl missing '/' after type: {purl!r}")

    type_part = rest[:slash_idx]
    after_type = rest[slash_idx + 1:]

    if not type_part:
        raise ValueError(f"purl type cannot be empty: {purl!r}")
    if not after_type:
        raise ValueError(f"purl missing name after type: {purl!r}")

    type_str = type_part.lower()
    # Normalize 'github.com' shorthand type to 'github' (AC10)
    if type_str == "github.com":
        type_str = "github"

    # Step 6: Split version from name/namespace
    # The version delimiter is '@', but some purls use '%40' instead.
    # Strategy: scan from the end for a bare '@'; if found that's the delimiter.
    # If no bare '@' is found, look for '%40' as the delimiter (AC8).
    version_str: str | None = None
    name_part = after_type

    at_idx = -1
    i = len(name_part) - 1
    while i >= 0:
        if name_part[i] == "@":
            at_idx = i
            break
        i -= 1

    if at_idx == -1:
        idx40 = name_part.rfind("%40")
        if idx40 != -1:
            at_idx = idx40

    if at_idx != -1:
        # If '%40' is the delimiter, keep it in version_str so unquote gives '@'
        if at_idx > 0 and name_part[at_idx] == "%":
            version_str = name_part[at_idx:]  # keep '%40'
        else:
            version_str = name_part[at_idx + 1:]
        name_part = name_part[:at_idx]

    # Step 7: Parse name/namespace using type-specific rules
    name: str = ""
    namespace: str | None = None

    registry_entry = TYPE_REGISTRY.get(type_str, {"namespace_sep": "/", "name_sep": None})
    ns_sep = registry_entry["namespace_sep"]

    if type_str == "maven":
        # Maven: pkg:maven/org.apache.commons/commons-lang3@1.2.3
        # namespace = groupId (org.apache.commons), name = artifactId
        slash_count = name_part.count("/")
        if slash_count == 0:
            raise ValueError(f"purl maven requires namespace/name: {purl!r}")
        elif slash_count == 1:
            ns_part, name = name_part.split("/", 1)
            namespace = ns_part
        else:
            last_slash = name_part.rfind("/")
            namespace = name_part[:last_slash]
            name = name_part[last_slash + 1:]
    elif ns_sep == "/":
        # Most types: namespace/name split at last '/'
        slash_idx = name_part.rfind("/")
        if slash_idx == -1:
            name = name_part
        else:
            namespace = name_part[:slash_idx]
            name = name_part[slash_idx + 1:]
            # AC10: github.com shorthand — namespace is 'github.com/<rest>'
            if type_str == "github" and namespace:
                namespace = "github.com/" + namespace
    else:
        # Fallback: treat entire as name
        name = name_part

    if not name:
        raise ValueError(f"purl name cannot be empty: {purl!r}")
    # Reject duplicate '@' (e.g., lodash@@4.17.21)
    if "@" in name:
        raise ValueError(f"purl has multiple '@' delimiters: {purl!r}")

    # Step 8: URL-decode version
    version: str | None = None
    if version_str is not None:
        version = unquote(version_str)

    # Step 9: URL-decode name and namespace (per spec examples)
    decoded_name = unquote(name)
    decoded_namespace = unquote(namespace) if namespace is not None else None

    return ParseResult(
        type=type_str,
        namespace=decoded_namespace,
        name=decoded_name,
        version=version,
        qualifiers=qualifiers,
        subpath=subpath,
    )
