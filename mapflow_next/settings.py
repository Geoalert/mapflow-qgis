"""Plugin settings in the QGIS profile, under the `mapflow_next/` group. Credentials are never stored here."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from qgis.PyQt.QtCore import QStandardPaths
from qgis.core import QgsSettings

from .config import SETTINGS_GROUP


def default_output_dir() -> Path:
    documents = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation) or str(Path.home())
    return Path(documents) / "Mapflow"


class Settings:
    def __init__(self, group: str = SETTINGS_GROUP):
        self._settings = QgsSettings()
        self._prefix = group.rstrip("/") + "/"

    def value(self, key: str, default: Any = None) -> Any:
        return self._settings.value(self._prefix + key, default)

    def flag(self, key: str, default: bool = False) -> bool:
        value = self._settings.value(self._prefix + key, default)
        return value if isinstance(value, bool) else str(value).lower() in ("true", "1", "yes")

    def setValue(self, key: str, value: Any) -> None:
        self._settings.setValue(self._prefix + key, value)

    def remove(self, key: str) -> None:
        self._settings.remove(self._prefix + key)
