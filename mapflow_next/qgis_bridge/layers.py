"""Putting things on the map: the Mapflow layer group, result layers, imagery tiles."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from qgis.core import (QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsCsException, QgsJsonUtils,
                       QgsLayerTreeGroup,
                       QgsMapLayer,
                       QgsProject, QgsRasterLayer, QgsRectangle, QgsVectorFileWriter, QgsVectorLayer,
                       QgsVectorTileLayer)

from ..config import LAYER_GROUP_NAME, PREVIEW_PROPERTY, PROCESSING_PROPERTY, RESOURCES
from ..core.models import Mosaic, Processing
from . import styles

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")
WEB_MERCATOR = QgsCoordinateReferenceSystem("EPSG:3857")


def safe_filename(text: str) -> str:
    return re.sub(r"[^\w\-. ]+", "_", text).strip(" .")[:80] or "mapflow"


def xyz_uri(url: str, zmin: int = 0, zmax: int = 21) -> str:
    # QGIS reads this URI unencoded; only the characters that would split it are escaped
    url = url.replace("&", "%26").replace("=", "%3D")
    return f"type=xyz&url={url}&zmin={zmin}&zmax={zmax}"


def bounds_extent(bounds) -> Optional[QgsRectangle]:
    """A tilejson `bounds` [w, s, e, n] in EPSG:3857, the CRS of tile layers."""
    try:
        west, south, east, north = [float(v) for v in bounds]
    except (TypeError, ValueError):
        return None
    transform = QgsCoordinateTransform(WGS84, WEB_MERCATOR, QgsProject.instance().transformContext())
    return transform.transformBoundingBox(QgsRectangle(west, south, east, north))


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

    def save_results(self, geojson_path: str, processing: Processing, out_dir: Path) -> List[QgsVectorLayer]:
        """Write the downloaded GeoJSON to a GeoPackage (one layer per geometry type) and open it.
        Falls back to the GeoJSON file itself if the GeoPackage can't be written."""
        out_dir.mkdir(parents=True, exist_ok=True)
        target = self._unique(out_dir, f"{safe_filename(processing.name)}_{processing.id[:8]}", ".gpkg")
        _normalise_json_fields(geojson_path)
        layers: List[QgsVectorLayer] = []
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        first = True
        for geometry_type in ("Polygon", "LineString", "Point"):
            source = QgsVectorLayer(f"{geojson_path}|geometrytype={geometry_type}", "source", "ogr")
            if not source.isValid() or source.featureCount() == 0:
                continue
            layer_name = (processing.name if geometry_type == "Polygon"
                          else f"{processing.name} ({geometry_type.lower()}s)")
            options.layerName = layer_name
            options.actionOnExistingFile = (QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile if first
                                            else QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer)
            error, message, *_ = QgsVectorFileWriter.writeAsVectorFormatV3(
                source, str(target), self.project.transformContext(), options)
            if error != QgsVectorFileWriter.WriterError.NoError:
                return self._open_geojson(geojson_path, processing, out_dir)
            first = False
            layer = QgsVectorLayer(f"{target}|layername={layer_name}", layer_name, "ogr")
            if layer.isValid():
                styles.apply(layer, processing.model_name, processing.style_name)
                layers.append(layer)
        return layers

    def _open_geojson(self, geojson_path: str, processing: Processing, out_dir: Path) -> List[QgsVectorLayer]:
        target = self._unique(out_dir, f"{safe_filename(processing.name)}_{processing.id[:8]}", ".geojson")
        Path(geojson_path).replace(target)
        layer = QgsVectorLayer(str(target), processing.name, "ogr")
        if not layer.isValid():
            return []
        styles.apply(layer, processing.model_name, processing.style_name)
        return [layer]

    @staticmethod
    def _unique(folder: Path, stem: str, suffix: str) -> Path:
        candidate = folder / f"{stem}{suffix}"
        index = 1
        while candidate.exists():
            candidate = folder / f"{stem}_{index}{suffix}"
            index += 1
        return candidate


def _normalise_json_fields(path: str) -> None:
    """Nested objects (e.g. Open Data `bbox`) become strings: GeoPackage has no JSON type.
    Very large results skip this (they come from models that return flat attributes)."""
    try:
        if Path(path).stat().st_size > 200 * 1024 * 1024:
            return

        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return
    changed = False
    for feature in data.get("features") or []:
        properties: Dict = feature.get("properties") or {}
        for key, value in list(properties.items()):
            if isinstance(value, (dict, list)):
                properties[key] = json.dumps(value)
                changed = True
    if changed:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
