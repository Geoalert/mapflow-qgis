"""Area of interest from QGIS layers: geometry in WGS84 and its measurements.

Measurement rules are carried over from the current plugin (spec 002_B): the geometry is sent as
collected, but its area is measured on the union of its parts (each part repaired on its own first),
and the plan limit applies both to the total and to each polygon's lat-lon bounding box.
"""
from __future__ import annotations

import json
from typing import List, Optional

from qgis.core import (QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsDistanceArea, QgsFeature,
                       QgsGeometry, QgsMapLayer, QgsProject, QgsVectorLayer)

from ..config import RESOURCES
from ..core.draft import AreaOfInterest
from .compat import POLYGON_GEOMETRY

WGS84 = QgsCoordinateReferenceSystem("EPSG:4326")


def is_polygon_layer(layer: Optional[QgsMapLayer]) -> bool:
    return (isinstance(layer, QgsVectorLayer) and layer.isValid()
            and layer.geometryType() == POLYGON_GEOMETRY)


def polygon_layers(project: Optional[QgsProject] = None) -> List[QgsVectorLayer]:
    project = project or QgsProject.instance()
    layers = [layer for layer in project.mapLayers().values() if is_polygon_layer(layer)]
    return sorted(layers, key=lambda layer: layer.name().lower())


def to_wgs84(geometry: QgsGeometry, crs: QgsCoordinateReferenceSystem) -> QgsGeometry:
    geometry = QgsGeometry(geometry)
    if crs != WGS84:
        geometry.transform(QgsCoordinateTransform(crs, WGS84, QgsProject.instance().transformContext()))
    return geometry


def _unusable(geometry: Optional[QgsGeometry]) -> bool:
    return geometry is None or geometry.isNull() or geometry.isEmpty()


def _parts(geometry: QgsGeometry) -> List[QgsGeometry]:
    return [part for part in (geometry.asGeometryCollection() or [geometry]) if not _unusable(part)]


def union_parts(geometry: QgsGeometry) -> QgsGeometry:
    """The footprint whose area the backend charges for: overlapping parts dissolved."""
    if _unusable(geometry) or (not geometry.isMultipart() and geometry.isGeosValid()):
        return geometry
    repaired = []
    for part in _parts(geometry):
        if not part.isGeosValid():
            fixed = part.makeValid()
            part = part if _unusable(fixed) else fixed
        repaired.append(part)
    dissolved = QgsGeometry.unaryUnion(repaired)
    return geometry if _unusable(dissolved) else dissolved


def _calculator() -> QgsDistanceArea:
    calculator = QgsDistanceArea()
    calculator.setSourceCrs(WGS84, QgsProject.instance().transformContext())
    calculator.setEllipsoid(WGS84.ellipsoidAcronym() or "EPSG:7030")
    return calculator


def measure(geometry_wgs84: QgsGeometry):
    """(area km², largest per-polygon bbox km², polygon count)."""
    calculator = _calculator()
    area = calculator.measureArea(union_parts(geometry_wgs84)) / 1e6
    parts = _parts(geometry_wgs84)
    biggest_bbox = max((calculator.measureArea(QgsGeometry.fromRect(p.boundingBox())) for p in parts), default=0.0)
    return area, biggest_bbox / 1e6, len(parts)


def collect(layer: QgsVectorLayer, selected_only: bool = False) -> QgsGeometry:
    features = list(layer.getSelectedFeatures()) if selected_only else []
    if not features:
        features = list(layer.getFeatures())
    geometries = [f.geometry() for f in features if not _unusable(f.geometry())]
    if not geometries:
        return QgsGeometry()
    return geometries[0] if len(geometries) == 1 else QgsGeometry.collectGeometry(geometries)


def aoi_from_layer(layer: QgsVectorLayer, selected_only: bool = True) -> Optional[AreaOfInterest]:
    """The layer's polygons as the area. With `selected_only` (the default, as in the current plugin),
    a selection on the layer narrows the area to the selected polygons; no selection means all of them."""
    geometry = collect(layer, selected_only)
    if _unusable(geometry):
        return None
    wgs84 = to_wgs84(geometry, layer.crs())
    area, bbox, polygons = measure(wgs84)
    selected = layer.selectedFeatureCount() if selected_only else 0
    return AreaOfInterest(name=layer.name(), geometry=json.loads(wgs84.asJson(6)), area_km2=area,
                          max_bbox_km2=bbox, polygons=polygons, layer_id=layer.id(),
                          layer_features=layer.featureCount(), selected=selected)


def memory_layer(geometry: QgsGeometry, crs: QgsCoordinateReferenceSystem, name: str) -> QgsVectorLayer:
    """A one-feature polygon layer for a drawn or extent-based area."""
    layer = QgsVectorLayer(f"Polygon?crs={crs.authid() or 'EPSG:4326'}", name, "memory")
    feature = QgsFeature()
    feature.setGeometry(geometry)
    layer.dataProvider().addFeatures([feature])
    layer.updateExtents()
    layer.loadNamedStyle(str(RESOURCES / "styles" / "aoi.qml"))
    return layer


def geojson_layer(collection: dict, name: str) -> Optional[QgsVectorLayer]:
    """A memory layer from a GeoJSON FeatureCollection in WGS84 (a processing's saved AOI)."""
    geometries = [QgsGeometry.fromWkt(_geojson_to_wkt(f.get("geometry"))) for f in collection.get("features") or []]
    geometries = [g for g in geometries if not _unusable(g)]
    if not geometries:
        return None
    geometry = geometries[0] if len(geometries) == 1 else QgsGeometry.collectGeometry(geometries)
    return memory_layer(geometry, WGS84, name)


def _geojson_to_wkt(geometry: Optional[dict]) -> str:
    from osgeo import ogr  # bundled with QGIS
    if not geometry:
        return ""
    ogr_geometry = ogr.CreateGeometryFromJson(json.dumps(geometry))
    return ogr_geometry.ExportToWkt() if ogr_geometry else ""


# ---------- My imagery footprints ----------

def footprint(wkts: List[str]) -> Optional[QgsGeometry]:
    """The imagery's footprint in WGS84: the union of the given WKT polygons (a collection's, or its
    images'). None when none of them is usable."""
    parts = []
    for wkt in wkts:
        geometry = QgsGeometry.fromWkt(wkt or "")
        if _unusable(geometry):
            continue
        if not geometry.isGeosValid():
            fixed = geometry.makeValid()
            geometry = geometry if _unusable(fixed) else fixed
        parts.append(geometry)
    if not parts:
        return None
    merged = parts[0] if len(parts) == 1 else QgsGeometry.unaryUnion(parts)
    return None if _unusable(merged) else _polygons(merged)


def geometry_from_geojson(geometry: dict) -> Optional[QgsGeometry]:
    from osgeo import ogr
    parsed = ogr.CreateGeometryFromJson(json.dumps(geometry)) if geometry else None
    if parsed is None:
        return None
    result = QgsGeometry.fromWkt(parsed.ExportToWkt())
    return None if _unusable(result) else result


def _polygons(geometry: QgsGeometry) -> Optional[QgsGeometry]:
    """Only the polygon parts (an intersection can add the odd shared edge or corner)."""
    if geometry.type() == POLYGON_GEOMETRY and not geometry.isEmpty():
        return geometry
    kept = [p for p in geometry.asGeometryCollection() if p.type() == POLYGON_GEOMETRY and not p.isEmpty()]
    if not kept:
        return None
    return kept[0] if len(kept) == 1 else QgsGeometry.collectGeometry(kept)


def clip_to(aoi: AreaOfInterest, imagery: QgsGeometry) -> Optional[AreaOfInterest]:
    """The part of the area inside the imagery, measured; None when they don't overlap."""
    area = geometry_from_geojson(aoi.geometry)
    if area is None:
        return None
    if not area.isGeosValid():
        area = union_parts(area)
    if not area.intersects(imagery):
        return None
    inside = area.intersection(imagery)
    inside = None if _unusable(inside) else _polygons(inside)
    if inside is None:
        return None
    size, bbox, polygons = measure(inside)
    if size <= 0:
        return None
    return AreaOfInterest(name=aoi.name, geometry=json.loads(inside.asJson(6)), area_km2=size,
                          max_bbox_km2=bbox, polygons=polygons, layer_id=aoi.layer_id,
                          layer_features=aoi.layer_features, selected=aoi.selected)


def extent_layer(imagery: QgsGeometry, name: str) -> QgsVectorLayer:
    """The imagery's extent as an editable area layer."""
    return memory_layer(imagery, WGS84, name)
