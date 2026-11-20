"""Putting things on the map: the Mapflow layer group, result layers, imagery tiles."""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from qgis.core import (QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsCsException, QgsJsonUtils,
                       QgsLayerTreeGroup,
                       QgsMapLayer,
                       QgsProject, QgsRasterLayer, QgsRectangle, QgsVectorLayer,
                       QgsVectorTileLayer)

from qgis.PyQt.QtGui import QImage

from ..config import LAYER_GROUP_NAME, PREVIEW_PROPERTY, PROCESSING_PROPERTY, RESOURCES
from ..core import filenames
from ..core.models import Mosaic, Processing
from . import styles
from .conversion import GPKG, ConvertTask, Converted, Job, claimed, work_path

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")
WEB_MERCATOR = QgsCoordinateReferenceSystem("EPSG:3857")


def safe_filename(text: str) -> str:
    return re.sub(r"[^\w\-. ]+", "_", text).strip(" .")[:80] or "mapflow"


def xyz_uri(url: str, zmin: int = 0, zmax: int = 21) -> str:
    # QGIS reads this URI unencoded; only the characters that would split it are escaped
    url = url.replace("&", "%26").replace("=", "%3D")
    return f"type=xyz&url={url}&zmin={zmin}&zmax={zmax}"


def geojson_bounds(geometry: Optional[dict]):
    """(west, south, east, north) of a GeoJSON geometry's coordinates, or None."""
    xs, ys = [], []

    def walk(value) -> None:
        if isinstance(value, (list, tuple)) and len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2]):
            xs.append(float(value[0]))
            ys.append(float(value[1]))
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)

    walk((geometry or {}).get("coordinates"))
    if not xs or max(xs) <= min(xs) or max(ys) <= min(ys):
        return None
    return min(xs), min(ys), max(xs), max(ys)


def footprint_corners(geometry: Optional[dict]) -> Optional[List[Tuple[float, float]]]:
    """A quadrilateral footprint's corners as NW, NE, SE, SW; None for any other shape. Scenes are turned
    by less than 45°, so the two northernmost corners are the picture's top ones, whatever order they
    come in."""
    geometry = geometry or {}
    rings = geometry.get("coordinates") or []
    if geometry.get("type") == "MultiPolygon":
        rings = rings[0] if len(rings) == 1 else []
    elif geometry.get("type") != "Polygon":
        return None
    ring = [(float(p[0]), float(p[1])) for p in (rings[0] if rings else [])]
    if len(ring) == 5 and ring[0] == ring[-1]:
        ring = ring[:4]
    if len(ring) != 4 or len(set(ring)) != 4:
        return None
    by_north = sorted(ring, key=lambda p: -p[1])
    (nw, ne), (sw, se) = sorted(by_north[:2]), sorted(by_north[2:])
    return [nw, ne, se, sw]


def bounds_extent(bounds) -> Optional[QgsRectangle]:
    """A tilejson `bounds` [w, s, e, n] in EPSG:3857, the CRS of tile layers; None if they cannot be used."""
    try:
        west, south, east, north = [float(v) for v in bounds]
    except (TypeError, ValueError):
        return None
    transform = QgsCoordinateTransform(WGS84, WEB_MERCATOR, QgsProject.instance().transformContext())
    try:
        return transform.transformBoundingBox(QgsRectangle(west, south, east, north))
    except QgsCsException:      # bounds beyond the map (latitude past 90°) are unusable data, not a plugin failure
        return None


def extent_is_world(extent: QgsRectangle, crs: Optional[QgsCoordinateReferenceSystem] = None) -> bool:
    """Is this the whole-world extent a tile layer has by default (wider than half the globe)?"""
    if extent is None or extent.isEmpty():
        return True
    crs = crs or WEB_MERCATOR
    if crs != WGS84:
        transform = QgsCoordinateTransform(crs, WGS84, QgsProject.instance().transformContext())
        try:
            extent = transform.transformBoundingBox(extent)
        except QgsCsException:
            return True
    return extent.width() > 180 or extent.height() > 85


def features_extent(collection: dict) -> Optional[QgsRectangle]:
    """The bounding box (EPSG:3857) of a GeoJSON FeatureCollection in WGS84."""
    extent = QgsRectangle()
    extent.setMinimal()
    from osgeo import ogr
    for feature in (collection or {}).get("features") or []:
        parsed = ogr.CreateGeometryFromJson(json.dumps(feature.get("geometry"))) if feature.get("geometry") else None
        if parsed is None:
            continue
        west, east, south, north = parsed.GetEnvelope()
        extent.combineExtentWith(QgsRectangle(west, south, east, north))
    if extent.isEmpty() or extent.width() <= 0 and extent.height() <= 0:
        return None
    transform = QgsCoordinateTransform(WGS84, WEB_MERCATOR, QgsProject.instance().transformContext())
    return transform.transformBoundingBox(extent)


class MapLayers:
    def __init__(self, iface, project: Optional[QgsProject] = None):
        self.iface = iface
        self.project = project or QgsProject.instance()
        self._temp: Optional[Path] = None
        self._closed = False

    # ---------- session folder ----------

    def temp_folder(self) -> Optional[Path]:
        """The folder of this session's preview files, made on first use and readable by its owner only.
        None once the session is closed."""
        if self._closed:
            return None
        if self._temp is None:
            self._temp = Path(tempfile.mkdtemp(prefix="mapflow_next_"))
        return self._temp

    def preview_path(self, image_id: str, suffix: str) -> Optional[Path]:
        """A file of the session folder named after `image_id` (made safe first), or None when there is no
        folder or the path would not lie directly in it."""
        folder = self.temp_folder()
        if folder is None:
            return None
        path = folder / f"{filenames.safe_stem(image_id)}{suffix}"
        return path if path.resolve().parent == folder.resolve() else None

    def close(self) -> None:
        """End of the session: the preview layers leave the project and the session folder is removed."""
        self._closed = True
        folder, self._temp = self._temp, None
        if folder is None:
            return
        prefix = str(folder) + os.sep
        stale = [layer.id() for layer in list(self.project.mapLayers().values())
                 if layer.source().startswith(prefix)]
        for layer_id in stale:
            self.project.removeMapLayer(layer_id)
        shutil.rmtree(folder, ignore_errors=True)       # a file still open elsewhere must not break the unload

    # ---------- group ----------

    def group(self) -> QgsLayerTreeGroup:
        root = self.project.layerTreeRoot()
        group = root.findGroup(LAYER_GROUP_NAME)
        if group is None:
            group = root.insertGroup(0, LAYER_GROUP_NAME)
        return group

    def add(self, layer: QgsMapLayer, processing_id: Optional[str] = None, position: int = 0,
            preview: Optional[str] = None) -> QgsMapLayer:
        if processing_id:
            layer.setCustomProperty(PROCESSING_PROPERTY, processing_id)
        if preview:
            layer.setCustomProperty(PREVIEW_PROPERTY, preview)
        self.project.addMapLayer(layer, False)
        self.group().insertLayer(position, layer)
        return layer

    def layers_for(self, processing_id: str) -> List[QgsMapLayer]:
        return [layer for layer in self.project.mapLayers().values()
                if layer.customProperty(PROCESSING_PROPERTY) == processing_id]

    def previews(self, key: Optional[str]) -> List[QgsMapLayer]:
        """The preview layers showing one imagery source (see PREVIEW_PROPERTY)."""
        if not key:
            return []
        return [layer for layer in self.project.mapLayers().values()
                if layer.customProperty(PREVIEW_PROPERTY) == key]

    def remove(self, layers: List[QgsMapLayer]) -> None:
        self.project.removeMapLayers([layer.id() for layer in layers])

    def processing_ids_in_map(self) -> set:
        ids = set()
        for layer in self.project.mapLayers().values():
            value = layer.customProperty(PROCESSING_PROPERTY)
            if value:
                ids.add(str(value))
        return ids

    def zoom_to(self, layers: List[QgsMapLayer]) -> None:
        canvas = self.iface.mapCanvas() if self.iface else None
        if not canvas or not layers:
            return
        extent = QgsRectangle()
        extent.setMinimal()
        for layer in layers:
            # skip layers that know no better than "the whole world" (tile layers without bounds)
            if layer.extent().isEmpty() or extent_is_world(layer.extent(), layer.crs()):
                continue
            transform = QgsCoordinateTransform(layer.crs(), canvas.mapSettings().destinationCrs(),
                                               self.project.transformContext())
            extent.combineExtentWith(transform.transformBoundingBox(layer.extent()))
        if not extent.isEmpty():
            extent.scale(1.1)
            canvas.setExtent(extent)
            canvas.refresh()

    # ---------- imagery ----------

    def tile_raster(self, url: str, name: str, extent: Optional[QgsRectangle] = None,
                    zmax: int = 21) -> Optional[QgsRasterLayer]:
        layer = QgsRasterLayer(xyz_uri(url, 0, zmax), name, "wms")
        if not layer.isValid():
            return None
        if extent is not None:
            layer.setExtent(extent)
        return layer

    def mosaic_layer(self, mosaic: Mosaic) -> Optional[QgsRasterLayer]:
        return self.tile_raster(mosaic.tile_url, f"My imagery · {mosaic.name}") if mosaic.tile_url else None

    def picture_on_footprint(self, data: bytes, footprint: Optional[dict], name: str,
                             image_id: str) -> Optional[QgsRasterLayer]:
        """A catalog image's picture preview (PNG or JPEG) stretched over its footprint: its four corners
        when the footprint is a quadrilateral (a turned scene, Orbview), else its bounding box. A preview,
        not a georeferenced image: close enough to judge the scene against the area."""
        box = geojson_bounds(footprint)
        image = QImage.fromData(data)
        if box is None or image.isNull():
            return None
        jpeg = data[:3] == b"\xff\xd8\xff"
        path = self.preview_path(image_id, ".jpg" if jpeg else ".png")
        if path is None:
            return None
        path.write_bytes(data)
        corners = footprint_corners(footprint)
        if corners:
            return self._picture_on_corners(path, image.width(), image.height(), corners, name)
        west, south, east, north = box
        dx, dy = (east - west) / image.width(), (north - south) / image.height()
        # World file: pixel size, rotations, the upper-left pixel's centre
        path.with_suffix(".jgw" if jpeg else ".pgw").write_text(
            f"{dx}\n0\n0\n{-dy}\n{west + dx / 2}\n{north - dy / 2}\n", encoding="ascii")
        layer = QgsRasterLayer(str(path), name, "gdal")
        if not layer.isValid():
            return None
        layer.setCrs(WGS84)
        return layer

    @staticmethod
    def _picture_on_corners(path: Path, width: int, height: int, corners: List[Tuple[float, float]],
                            name: str) -> Optional[QgsRasterLayer]:
        """The picture warped so its corners land on the footprint's (NW, NE, SE, SW); outside it is clear."""
        from osgeo import gdal
        pixels = ((0, 0), (width, 0), (width, height), (0, height))
        gcps = [gdal.GCP(x, y, 0, px, py) for (x, y), (px, py) in zip(corners, pixels)]
        placed = gdal.Translate(str(path.with_suffix(".vrt")), str(path), format="VRT", GCPs=gcps,
                                outputSRS="EPSG:4326")
        if placed is None:
            return None
        warped = gdal.Warp(str(path.with_suffix(".tif")), placed, format="GTiff", dstSRS="EPSG:4326", dstAlpha=True)
        ok = warped is not None
        del placed, warped                          # closing them writes the files
        layer = QgsRasterLayer(str(path.with_suffix(".tif")), name, "gdal") if ok else None
        return layer if layer is not None and layer.isValid() else None

    def pictures_on_footprints(self, parts: List[Tuple[bytes, Optional[dict]]], name: str,
                               image_id: str) -> Optional[QgsRasterLayer]:
        """A preview in several pictures (Roscosmos), each on its own footprint, joined into one layer."""
        from osgeo import gdal
        placed = [self.picture_on_footprint(data, footprint, name, f"{image_id}_{index}")
                  for index, (data, footprint) in enumerate(parts)]
        if not placed or not all(placed):
            return None
        path = self.preview_path(image_id, ".vrt")
        if path is None:
            return None
        vrt = gdal.BuildVRT(str(path), [layer.source() for layer in placed])
        if vrt is None:
            return None
        del vrt                                     # closing it writes the file
        layer = QgsRasterLayer(str(path), name, "gdal")
        if not layer.isValid():
            return None
        layer.setCrs(WGS84)
        return layer

    def footprints_layer(self, collection: dict, name: str = "Mapflow · search results") -> Optional[QgsVectorLayer]:
        for layer in self.project.mapLayersByName(name):
            self.project.removeMapLayer(layer.id())
        if not collection.get("features"):
            return None
        fields = QgsJsonUtils.stringToFields(json.dumps(collection))
        features = QgsJsonUtils.stringToFeatureList(json.dumps(collection), fields)
        layer = QgsVectorLayer("Polygon?crs=EPSG:4326", name, "memory")
        layer.dataProvider().addAttributes(fields.toList())
        layer.updateFields()
        layer.dataProvider().addFeatures(features)
        layer.updateExtents()
        layer.loadNamedStyle(str(RESOURCES / "styles" / "metadata_footprint.qml"))
        return self.add(layer)

    # ---------- results ----------

    def vector_tiles(self, processing: Processing) -> Optional[QgsVectorTileLayer]:
        if not processing.vector_tile_url:
            return None
        layer = QgsVectorTileLayer(xyz_uri(processing.vector_tile_url, 0, 18), processing.name)
        if not layer.isValid():
            return None
        styles.apply(layer, processing.model_name, processing.style_name)
        return layer

    def convert_results(self, geojson_path: str, processing: Processing, out_dir: Path,
                        on_done: Callable[[ConvertTask], None]) -> ConvertTask:
        """The task that writes the downloaded GeoJSON to a GeoPackage in `out_dir` (see `conversion`). It is not
        started; `on_done(task)` runs on the GUI thread when it ends. Opening what it made is `open_converted`."""
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = f"{safe_filename(processing.name)}_{processing.id[:8]}"
        job = Job(geojson=Path(geojson_path), name=processing.name,
                  work=work_path(Path(geojson_path).parent, processing.id),
                  target=self._unique(out_dir, stem, ".gpkg"), fallback=self._unique(out_dir, stem, ".geojson"),
                  transform_context=self.project.transformContext())
        return ConvertTask(job, on_done)

    @staticmethod
    def open_converted(converted: Converted, processing: Processing) -> List[QgsVectorLayer]:
        """The layers of a finished conversion, styled. Runs on the GUI thread: layers are made where they are used."""
        layers: List[QgsVectorLayer] = []
        for name in converted.layer_names:
            source = f"{converted.path}|layername={name}" if converted.kind == GPKG else str(converted.path)
            layer = QgsVectorLayer(source, name, "ogr")
            if layer.isValid():
                styles.apply(layer, processing.model_name, processing.style_name)
                layers.append(layer)
        return layers

    @staticmethod
    def _unique(folder: Path, stem: str, suffix: str) -> Path:
        candidate = folder / f"{stem}{suffix}"
        index = 1
        while candidate.exists() or claimed(candidate):
            candidate = folder / f"{stem}_{index}{suffix}"
            index += 1
        return candidate
