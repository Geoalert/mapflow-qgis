"""GeoTIFFs checked before they are uploaded to My imagery: the limits Mapflow's upload accepts, and the
metadata it validates."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from qgis.core import (QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsDistanceArea, QgsMapLayer,
                       QgsPointXY, QgsProject, QgsRasterLayer)

GEOTIFF = (".tif", ".tiff")
UPLOAD_LIMIT_GB = 2               # as Mapflow's upload accepts (3.x checked the same limits)
MAX_SIDE_PIXELS = 30_000
BANDS = (1, 3, 4)                 # what Mapflow's models read from your own imagery
# Data types rasters/validate-image-metadata accepts (its request schema's enum)
DTYPES = ("uint8", "uint16", "int16", "float32", "int32")
WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")


def geotiff_path(layer: Optional[QgsMapLayer]) -> str:
    """The file a raster layer reads when it is a local GeoTIFF; "" for anything else (XYZ/TMS tiles, WMS,
    other formats, a file that has moved): those can't be uploaded from QGIS."""
    if not isinstance(layer, QgsRasterLayer) or not layer.isValid() or layer.providerType() != "gdal":
        return ""
    path = layer.source().split("|")[0]
    return path if path.lower().endswith(GEOTIFF) and Path(path).is_file() else ""


def geotiff_layers(project: Optional[QgsProject] = None) -> List[QgsRasterLayer]:
    project = project or QgsProject.instance()
    layers = [layer for layer in project.mapLayers().values() if geotiff_path(layer)]
    return sorted(layers, key=lambda layer: layer.name().lower())


def _dtype(layer: QgsRasterLayer, band: int) -> str:
    kind = layer.dataProvider().dataType(band)
    name = getattr(kind, "name", None) or str(kind).split(".")[-1]
    return {"Byte": "uint8", "UInt16": "uint16", "Int16": "int16", "UInt32": "uint32", "Int32": "int32",
            "Float32": "float32", "Float64": "float64", "Int8": "int8"}.get(name, name.lower())


def _footprint(layer: QgsRasterLayer) -> dict:
    """The image's four corners in WGS84, as a GeoJSON polygon."""
    extent = layer.extent()
    to_wgs84 = QgsCoordinateTransform(layer.crs(), WGS84, QgsProject.instance())
    ring = [to_wgs84.transform(QgsPointXY(x, y)) for x, y in (
        (extent.xMinimum(), extent.yMinimum()), (extent.xMaximum(), extent.yMinimum()),
        (extent.xMaximum(), extent.yMaximum()), (extent.xMinimum(), extent.yMaximum()))]
    coordinates = [[round(point.x(), 8), round(point.y(), 8)] for point in ring]
    return {"type": "Polygon", "coordinates": [coordinates + coordinates[:1]]}


def _pixel_size_meters(layer: QgsRasterLayer) -> List[float]:
    """One pixel's width and height on the ground at the image's centre, whatever units its CRS uses."""
    centre = layer.extent().center()
    dx, dy = abs(layer.rasterUnitsPerPixelX()), abs(layer.rasterUnitsPerPixelY())
    to_wgs84 = QgsCoordinateTransform(layer.crs(), WGS84, QgsProject.instance())
    calculator = QgsDistanceArea()
    calculator.setSourceCrs(WGS84, QgsProject.instance().transformContext())
    calculator.setEllipsoid(WGS84.ellipsoidAcronym() or "EPSG:7030")
    origin = to_wgs84.transform(centre)
    across = to_wgs84.transform(QgsPointXY(centre.x() + dx, centre.y()))
    down = to_wgs84.transform(QgsPointXY(centre.x(), centre.y() + dy))
    return [round(calculator.measureLine(origin, across), 4), round(calculator.measureLine(origin, down), 4)]


def geotiff_metadata(path: str) -> Tuple[dict, str]:
    """What the plugin and Mapflow need to know about a GeoTIFF before it's uploaded, and the reason it can't
    be uploaded (empty if it can). `validation_request` turns it into the check Mapflow takes."""
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
    crs = layer.crs()
    meta.update(width=layer.width(), height=layer.height(), count=count,
                dtypes=[_dtype(layer, band) for band in range(1, count + 1)],
                pixel_size=[abs(layer.rasterUnitsPerPixelX()), abs(layer.rasterUnitsPerPixelY())],
                crs=(crs.authid() or crs.toWkt()) if crs.isValid() else "")
    if not crs.isValid():
        return meta, "it isn't georeferenced (no coordinate system)"
    if max(layer.width(), layer.height()) >= MAX_SIDE_PIXELS:
        return meta, f"it's {layer.width():,} × {layer.height():,} px; the limit is {MAX_SIDE_PIXELS:,} px a side"
    if count not in BANDS:
        return meta, f"it has {count} bands; Mapflow takes 1, 3 or 4"
    if meta["dtypes"][0] not in DTYPES:
        return meta, f"its pixels are {meta['dtypes'][0]}; Mapflow takes {', '.join(DTYPES)}"
    meta.update(footprint=_footprint(layer), pixel_size_meters=_pixel_size_meters(layer))
    return meta, ""


def validation_request(meta: dict) -> dict:
    """The body of POST rasters/validate-image-metadata. Its schema forbids other fields."""
    return {"width": meta["width"], "height": meta["height"], "channels": meta["count"],
            "dtype": meta["dtypes"][0], "crs": meta["crs"], "pixel_size_meters": meta["pixel_size_meters"],
            "footprint": meta["footprint"], "file_size_bytes": meta["file_size"]}


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
