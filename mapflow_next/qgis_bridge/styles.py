"""Which bundled QML style fits a result layer (rules carried over from the current plugin)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from qgis.core import QgsVectorLayer, QgsVectorTileLayer

from ..config import RESOURCES
from .compat import POINT_GEOMETRY, POLYGON_GEOMETRY

FILE_STYLES = RESOURCES / "styles" / "file"
TILE_STYLES = RESOURCES / "styles" / "tiles"


def _family(model_name: str, style_name: Optional[str]) -> str:
    """buildings | forest | roads | landuse | construction | open_data | default"""
    if style_name:
        mapped = {"combo": "landuse", "buildings": "buildings", "building_heights": "buildings",
                  "forest": "forest", "roads": "roads", "construction": "construction",
                  "open_data": "open_data"}.get(style_name)
        if mapped:
            return mapped
    name = (model_name or "").lower()
    if "building" in name and "road" in name:
        return "landuse"
    if "building" in name:
        return "buildings"
    if "forest" in name or "tree" in name:
        return "forest"
    if "road" in name:
        return "roads"
    if "construction" in name:
        return "construction"
    if "open data" in name or "download" in name:
        return "open_data"
    return "default"


def file_style(layer: QgsVectorLayer, model_name: str, style_name: Optional[str] = None) -> Path:
    family = _family(model_name, style_name)
    fields = set(layer.fields().names())
    if family == "buildings":
        if {"class_id", "building_height"} <= fields:
            name = "building_heights_class"
        elif "building_height" in fields:
            name = "building_heights"
        elif "class_id" in fields:
            name = "buildings"
        else:
            name = "buildings_noclass"
    elif family == "forest":
        if layer.geometryType() == POINT_GEOMETRY:
            name = "forest_crowns_points"
        elif "class_id" in fields:
            name = "forest_with_heights"
        else:
            name = "forest"
    elif family == "open_data":
        name = "open_data_polygon" if layer.geometryType() == POLYGON_GEOMETRY else "open_data_line"
    else:
        name = family
    path = FILE_STYLES / f"{name}.qml"
    return path if path.exists() else FILE_STYLES / "default.qml"


def tile_style(model_name: str, style_name: Optional[str] = None) -> Path:
    family = _family(model_name, style_name)
    name = {"buildings": "buildings", "forest": "forest", "roads": "roads",
            "construction": "construction"}.get(family, "default")
    if family == "buildings" and "height" in (model_name or "").lower():
        name = "building_heights"
    return TILE_STYLES / f"{name}.qml"


def apply(layer, model_name: str, style_name: Optional[str] = None) -> None:
    if isinstance(layer, QgsVectorTileLayer):
        layer.loadNamedStyle(str(tile_style(model_name, style_name)))
    elif isinstance(layer, QgsVectorLayer):
        layer.loadNamedStyle(str(file_style(layer, model_name, style_name)))
