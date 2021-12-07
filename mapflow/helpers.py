import re
from pathlib import Path

from qgis.core import (
    QgsMapLayer, QgsMapLayerType, QgsWkbTypes, QgsGeometry, QgsProject,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform
)


PROJECT = QgsProject.instance()
WGS84 = QgsCoordinateReferenceSystem('EPSG:4326')
UUID_REGEX = re.compile('[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}\Z')


def is_geotiff_layer(layer: QgsMapLayer) -> bool:
    """Determine if a layer is loaded from a GeoTIFF file.

    :param layer: A layer to test
    """
    uri = layer.dataProvider().dataSourceUri()
    return Path(uri).suffix.lower() in ('.tif', '.tiff')


def is_polygon_layer(layer: QgsMapLayer) -> bool:
    """Determine if a layer is of vector type and has polygonal geometry.

    :param layer: A layer to test
    """
    return layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PolygonGeometry


def to_wgs84(geometry: QgsGeometry, source_crs: QgsCoordinateReferenceSystem) -> QgsGeometry:
    """Reproject a geometry to WGS84.

    :param geometry: A feature's geometry
    :param source_crs: The current CRS of the passed geometry
    """
    geometry.transform(QgsCoordinateTransform(source_crs, WGS84, PROJECT.transformContext()))
    return geometry


def from_wgs84(geometry: QgsGeometry, target_src: QgsCoordinateReferenceSystem) -> QgsGeometry:
    """Transform a geometry from WGS84.

    :param geometry: A feature's geometry
    :param target_src: The current CRS of the passed geometry
    """
    geometry.transform(QgsCoordinateTransform(WGS84, target_src, PROJECT.transformContext()))
    return geometry


def get_layer_extent(layer: QgsMapLayer) -> QgsGeometry:
    """Get a layer's bounding box aka extent/envelope/bounds.

    :param layer: The layer of interest
    """
    # Create a geometry from the layer's extent
    extent_geometry = QgsGeometry.fromRect(layer.extent())
    # Reproject it to WGS84 if the layer has another CRS
    layer_crs = layer.crs()
    if layer_crs != WGS84:
        extent_geometry = to_wgs84(extent_geometry, layer_crs)
    return extent_geometry


def is_uuid(value: str) -> bool:
    """Validate UUID supplied by the user."""
    return bool(UUID_REGEX.match(value))
