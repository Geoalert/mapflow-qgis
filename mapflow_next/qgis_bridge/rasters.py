"""Raster layers of the QGIS project as imagery for a processing.

A layer read from a file (GDAL) can be uploaded to My imagery, if it is a GeoTIFF. A layer of XYZ or
TMS tiles can be processed from the same tiles: Mapflow reads them from the layer's URL (userDefined).
Anything else (WMS, WCS, virtual rasters) is listed with the reason it can't be used.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from qgis.core import QgsProject, QgsProviderRegistry, QgsRasterLayer

GEOTIFF = (".tif", ".tiff")
UPLOAD_LIMIT_GB = 2               # as Mapflow's upload accepts (3.x checked the same limits)
MAX_SIDE_PIXELS = 30_000
BANDS = (1, 3, 4)                 # what Mapflow's models read from your own imagery


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


def _dtype(layer: QgsRasterLayer, band: int) -> str:
    kind = layer.dataProvider().dataType(band)
    name = getattr(kind, "name", None) or str(kind).split(".")[-1]
    return {"Byte": "uint8", "UInt16": "uint16", "Int16": "int16", "UInt32": "uint32", "Int32": "int32",
            "Float32": "float32", "Float64": "float64", "Int8": "int8"}.get(name, name.lower())


def geotiff_metadata(path: str) -> Tuple[dict, str]:
    """What Mapflow needs to know about a GeoTIFF before it's uploaded, as GET /rasters/image/{id} lists it,
    and the reason it can't be uploaded (empty if it can)."""
    file = Path(path)
    meta = {"filename": file.name}
    if not file.is_file():
        return meta, "the file isn't there"
    if file.suffix.lower() not in GEOTIFF:
        return meta, "it isn't a GeoTIFF (.tif)"
    size = file.stat().st_size
    meta["file_size"] = size
    if size > UPLOAD_LIMIT_GB * 1024 ** 3:
        return meta, f"it's larger than {UPLOAD_LIMIT_GB} GB: upload it in Mapflow Web"
    layer = QgsRasterLayer(str(file), file.stem, "gdal")
    if not layer.isValid():
        return meta, "QGIS can't read it as a raster"
    count = layer.bandCount()
    meta.update(width=layer.width(), height=layer.height(), count=count,
                dtypes=[_dtype(layer, band) for band in range(1, count + 1)],
                pixel_size=[abs(layer.rasterUnitsPerPixelX()), abs(layer.rasterUnitsPerPixelY())],
                crs=layer.crs().authid() if layer.crs().isValid() else "")
    if not layer.crs().isValid():
        return meta, "it isn't georeferenced (no coordinate system)"
    if max(layer.width(), layer.height()) >= MAX_SIDE_PIXELS:
        return meta, f"it's {layer.width():,} × {layer.height():,} px; the limit is {MAX_SIDE_PIXELS:,} px a side"
    if count not in BANDS:
        return meta, f"it has {count} bands; Mapflow takes 1, 3 or 4"
    return meta, ""


def mixed(metadata: List[dict]) -> str:
    """Images of one collection must share the coordinate system, the number of bands and the pixel size."""
    first = metadata[0]
    for meta in metadata[1:]:
        for key, what in (("crs", "coordinate system"), ("count", "number of bands")):
            if meta.get(key) != first.get(key):
                return f"{meta['filename']} has another {what} than {first['filename']}"
        a, b = first.get("pixel_size") or [0, 0], meta.get("pixel_size") or [0, 0]
        if a[0] and abs(b[0] - a[0]) > a[0] * 0.01:
            return f"{meta['filename']} has another pixel size than {first['filename']}"
    return ""
