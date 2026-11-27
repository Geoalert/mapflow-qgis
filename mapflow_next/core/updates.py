"""Is a newer version of the plugin available? Decided from what QGIS's plugin installer knows.

No Qt here: `assess` takes the installer's record of the plugin as a plain dict, so it is testable
without QGIS. The record's fields differ between QGIS versions: 3.34 and later list stable and
experimental versions separately, earlier versions list one version with an experimental flag.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

UPDATE = "update"               # a newer version is in the repositories
LATEST = "latest"               # the installed version is the newest the repositories offer
NOT_LISTED = "not_listed"       # no repository offers this plugin (installed from a ZIP or a folder)
ERROR = "error"                 # the check itself failed


def version_key(version: str) -> Tuple[Tuple[int, ...], int]:
    """Sortable key: '4.0.10' > '4.0.9', and a release > its own pre-release ('4.1.0' > '4.1.0-beta')."""
    match = re.match(r"(\d+(?:\.\d+)*)(.*)", (version or "").strip().lower().lstrip("v"))
    if not match:
        return (0,), 0
    numbers = tuple(int(n) for n in match.group(1).split("."))
    while len(numbers) > 1 and numbers[-1] == 0:
        numbers = numbers[:-1]
    pre_release = 0 if re.search(r"[a-z]", match.group(2).split("+")[0]) else 1
    return numbers, pre_release


def newest_available(record: Dict[str, Any], allow_experimental: bool) -> str:
    """The newest version the repositories offer to this QGIS, given its experimental-plugins setting."""
    stable = record.get("version_available_stable") or ""
    experimental = record.get("version_available_experimental") or ""
    candidates = [stable] + ([experimental] if allow_experimental else [])
    if not stable and not experimental:             # QGIS before 3.34: one version and a flag
        if allow_experimental or not record.get("experimental"):
            candidates.append(record.get("version_available") or "")
    candidates = [c for c in candidates if c]
    return max(candidates, key=version_key) if candidates else ""


@dataclass(frozen=True)
class UpdateCheck:
    state: str
    installed: str
    available: str = ""
    experimental_hidden: bool = False   # not listed, possibly because QGIS hides experimental plugins
    error: str = ""


def assess(installed: str, record: Optional[Dict[str, Any]], allow_experimental: bool,
           experimental_plugin: bool) -> UpdateCheck:
    available = newest_available(record or {}, allow_experimental)
    if not available:
        return UpdateCheck(NOT_LISTED, installed,
                           experimental_hidden=experimental_plugin and not allow_experimental)
    if version_key(available) > version_key(installed):
        return UpdateCheck(UPDATE, installed, available)
    return UpdateCheck(LATEST, installed, available)
