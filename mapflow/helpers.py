import re

from qgis.core import (
    QgsMapLayer, QgsGeometry, QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsMapLayerType, QgsWkbTypes
)
from typing import Tuple


PROJECT = QgsProject.instance()
WGS84 = QgsCoordinateReferenceSystem('EPSG:4326')
WGS84_ELLIPSOID = WGS84.ellipsoidAcronym()
WEB_MERCATOR = QgsCoordinateReferenceSystem('EPSG:3857')
UUID_REGEX = re.compile(r'[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}\Z')
URL_PATTERN = r'https?://(www\.)?([-\w]{1,256}\.)+[a-zA-Z0-9]{1,6}'  # schema + domains
URL_REGEX = re.compile(URL_PATTERN)
XYZ_REGEX = re.compile(URL_PATTERN + r'(.*\{[xyz]\}){3}.*', re.I)
QUAD_KEY_REGEX = re.compile(URL_PATTERN + r'(.*\{q\}).*', re.I)
MAXAR_PROVIDER_REGEX = re.compile(URL_PATTERN)  # todo: make actual regex
SENTINEL_DATETIME_REGEX = re.compile(r'\d{8}T\d{6}', re.I)
SENTINEL_COORDINATE_REGEX = re.compile(r'T\d{2}[A-Z]{3}', re.I)
SENTINEL_PRODUCT_NAME_REGEX = re.compile(r'\/(?:20[0-2][0-9])\/(?:1[0-2]|0?[1-9])\/(?:0?[1-9]|[1-2]\d|3[0-1])\/(\d{1,2})\/$')


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
    spherical_geometry = QgsGeometry(geometry)  # clone
    spherical_geometry.transform(QgsCoordinateTransform(source_crs, WGS84, PROJECT.transformContext()))
    return spherical_geometry


def from_wgs84(geometry: QgsGeometry, target_crs: QgsCoordinateReferenceSystem) -> QgsGeometry:
    """Transform a geometry from WGS84.

    :param geometry: A feature's geometry
    :param target_crs: The current CRS of the passed geometry
    """
    projected_geometry = QgsGeometry(geometry)  # clone
    projected_geometry.transform(QgsCoordinateTransform(WGS84, target_crs, PROJECT.transformContext()))
    return projected_geometry


def get_layer_extent(layer: QgsMapLayer) -> QgsGeometry:
    """Get a layer's bounding box aka extent/envelope
    /bounds.

    :param layer: The layer of interest
    """
    # Create a geometry from the layer's extent
    extent_geometry = QgsGeometry.fromRect(layer.extent())
    # Reproject it to WGS84 if the layer has another CRS
    layer_crs = layer.crs()
    if layer_crs != WGS84:
        extent_geometry = to_wgs84(extent_geometry, layer_crs)
    return extent_geometry


def check_version(local_version: str,
                  server_version: str,
                  latest_reported_version: str) -> Tuple[bool, bool]:
    """
    Returns: (force_upgrade, recommend_upgrade)
        force_upgrade is True if the user MUST reinstall/upgrade plugin to work with the server
        recommend_upgrade is True if the user MAY reinstall if he wants to have fixes/new features
    """
    if server_version == 1:
        return False, False
        # Legacy for current, before-versioning server behavior
    if server_version == latest_reported_version:
        # we have already reported the version on the server
        # should we expect the situation when the reported version can be higher than the current server version?
        # probably not
        return False, False

    loc_major, loc_minor, loc_patch = local_version.split('.')
    try:
        srv_major, srv_minor, srv_patch = server_version.split('.')
    except ValueError as e:
        # Means that server has wrong format of version, so we ignore this message
        return False, False

    major_changed = srv_major > loc_major
    minor_changed = loc_major == srv_major and loc_minor < srv_minor
    patch_changed = loc_major == srv_major and loc_minor == srv_minor and loc_patch < srv_patch
    return major_changed, (minor_changed or patch_changed)
