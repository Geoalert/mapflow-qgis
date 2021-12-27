import re

from qgis.core import (
    QgsMapLayer, QgsGeometry, QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsMapLayerType, QgsWkbTypes
)


PROJECT = QgsProject.instance()
WGS84 = QgsCoordinateReferenceSystem('EPSG:4326')
WEB_MERCATOR = QgsCoordinateReferenceSystem('EPSG:3857')
UUID_REGEX = re.compile(r'[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}\Z')
URL_PATTERN = r'https?://(www\.)?([-\w]{1,256}\.)+[a-zA-Z0-9]{1,6}'  # schema + domains
URL_REGEX = re.compile(URL_PATTERN)
XYZ_REGEX = re.compile(URL_PATTERN + r'(.*\{[xyz]\}){3}.*', re.I)
QUAD_KEY_REGEX = re.compile(URL_PATTERN + r'(.*\{q\}).*', re.I)
SENTINEL_DATETIME_REGEX = re.compile(r'\d{8}T\d{6}', re.I)
SENTINEL_COORDINATE_REGEX = re.compile(r'T\d{2}[A-Z]{3}', re.I)


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


def validate_provider_form(form) -> bool:
    """Return True if input looks valid otherwise return False."""
    name = form.name.text()
    url = form.url.text()
    type_ = form.type.currentText()
    if name and url:  # non-empty
        if type_ in ('xyz', 'tms'):
            return bool(XYZ_REGEX.match(url))
        elif type_ == 'wms':
            return bool(URL_REGEX.match(url))
        else:  # Quad Key
            return bool(QUAD_KEY_REGEX.match(url))
    return False
