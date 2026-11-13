"""Raster layers of the QGIS project as imagery for a processing.

A layer read from a file (GDAL) can be uploaded to My imagery, if it is a GeoTIFF. A layer of XYZ or
TMS tiles can be processed from the same tiles: Mapflow reads them from the layer's URL (userDefined).
Anything else (WMS, WCS, virtual rasters) is listed with the reason it can't be used.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from qgis.core import QgsProject, QgsProviderRegistry, QgsRasterLayer

GEOTIFF = (".tif", ".tiff")
UPLOAD_LIMIT_GB = 1


@dataclass(frozen=True)
class RasterSource:
    layer_id: str
    name: str
    kind: str                       # file | tiles | other
    path: str = ""                  # file: the GeoTIFF
    url: str = ""                   # tiles: Mapflow's form of the URL ({y} for TMS rows, as Mapflow expects)
    source_type: str = ""           # tiles: XYZ | TMS | QUADKEY
    zmin: int = 0
    zmax: int = 22
    login: str = ""
    password: str = ""
    problem: str = ""               # why it can't be used, if it can't

    @property
    def usable(self) -> bool:
        return not self.problem


def raster_sources(project: Optional[QgsProject] = None) -> List[RasterSource]:
    project = project or QgsProject.instance()
    layers = [layer for layer in project.mapLayers().values() if isinstance(layer, QgsRasterLayer)]
    return [describe(layer) for layer in sorted(layers, key=lambda layer: layer.name().lower())]


def _int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def describe(layer: QgsRasterLayer) -> RasterSource:
    name, layer_id = layer.name(), layer.id()
    provider = layer.providerType()
    if provider == "gdal":
        parts = QgsProviderRegistry.instance().decodeUri("gdal", layer.source())
        path = parts.get("path") or layer.source()
        file = Path(path)
        if not file.is_file():
            return RasterSource(layer_id, name, "other", path=path, problem="not a file on this computer")
        if file.suffix.lower() not in GEOTIFF:
            return RasterSource(layer_id, name, "other", path=path,
                                problem="not a GeoTIFF: export it as GeoTIFF first")
        if file.stat().st_size > UPLOAD_LIMIT_GB * 1024 ** 3:
            return RasterSource(layer_id, name, "other", path=path,
                                problem=f"larger than {UPLOAD_LIMIT_GB} GB: upload it in Mapflow Web")
        return RasterSource(layer_id, name, "file", path=str(file))
    if provider == "wms":
        parts = QgsProviderRegistry.instance().decodeUri("wms", layer.source())
        url = parts.get("url") or ""
        if parts.get("type") != "xyz" or not url:
            return RasterSource(layer_id, name, "other", problem="WMS layers can't be processed")
        if "{-y}" in url:               # QGIS writes TMS rows as {-y}; Mapflow's TMS sources use {y}
            source_type, url = "TMS", url.replace("{-y}", "{y}")
        elif "{q}" in url:
            source_type = "QUADKEY"
        else:
            source_type = "XYZ"
        if parts.get("authcfg"):
            return RasterSource(layer_id, name, "other",
                                problem="it signs in through QGIS, which Mapflow can't do")
        return RasterSource(layer_id, name, "tiles", url=url, source_type=source_type,
                            zmin=_int(parts.get("zmin"), 0), zmax=_int(parts.get("zmax"), 22),
                            login=parts.get("username") or "", password=parts.get("password") or "")
    return RasterSource(layer_id, name, "other", problem=f"{provider} layers can't be processed")
