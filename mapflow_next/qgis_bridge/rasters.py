"""GeoTIFFs checked before they are uploaded to My imagery: the limits Mapflow's upload accepts, and the
metadata it validates."""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from qgis.core import QgsRasterLayer

GEOTIFF = (".tif", ".tiff")
UPLOAD_LIMIT_GB = 2               # as Mapflow's upload accepts (3.x checked the same limits)
MAX_SIDE_PIXELS = 30_000
BANDS = (1, 3, 4)                 # what Mapflow's models read from your own imagery


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
