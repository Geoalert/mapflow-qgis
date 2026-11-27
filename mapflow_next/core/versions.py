"""The plugin version that the backend expects, against the plugin's own.

No Qt here. Only a higher major number blocks the plugin. A higher minor or patch number, an equal or lower
version, a pre-release suffix, an empty text and a text that is not a version do not: when unsure, the plugin works.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

_VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)((?:[-+][0-9A-Za-z.+-]*)?)")


def _match(text: Optional[str]):
    return _VERSION.fullmatch((text or "").strip())


def parse_version(text: Optional[str]) -> Optional[Tuple[int, int, int]]:
    """`MAJOR.MINOR.PATCH` with an optional `-pre-release` or `+build` suffix, as three numbers; None otherwise."""
    found = _match(text)
    return tuple(int(n) for n in found.groups()[:3]) if found else None


def format_version(text: Optional[str]) -> str:
    """The version text without the white space around it; empty when the text is not a version."""
    return (text or "").strip() if _match(text) else ""


def requires_upgrade(own: Optional[str], expected: Optional[str]) -> bool:
    """True when the expected version has a higher major number than the plugin's own."""
    own_numbers, expected_numbers = parse_version(own), parse_version(expected)
    if own_numbers is None or expected_numbers is None:
        return False
    return expected_numbers[0] > own_numbers[0]
