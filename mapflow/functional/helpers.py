import re
from pathlib import Path
from typing import Tuple, Union, Optional

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from qgis.core import (
    QgsGeometry, QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsRasterLayer
)

from ..config import config
from ..entity.billing import BillingType
from ..schema.project import UserRole

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


def raster_layer_is_allowed(layer: QgsRasterLayer):
    filepath = Path(layer.dataProvider().dataSourceUri())
    res = layer.crs().isValid() \
        and (layer.width() < config.MAX_FILE_SIZE_PIXELS) \
        and (layer.height() < config.MAX_FILE_SIZE_PIXELS) \
        and filepath.suffix.lower() in ('.tif', '.tiff') \
        and filepath.exists() \
        and filepath.stat().st_size < config.MAX_FILE_SIZE_BYTES
    return res


def check_aoi(aoi: Union[QgsGeometry, None]) -> bool:
    """Check if aoi is within the limits of [[-360:360] [-90:90]]"""
    if not aoi:
        return False
    b_box = aoi.boundingBox()
    x_max, x_min, y_max, y_min = b_box.xMaximum(), b_box.xMinimum(), b_box.yMaximum(), b_box.yMinimum()
    if x_max > 360 or x_max < -360 or x_min > 360 or x_min < -360:
        return False
    if y_max > 90 or y_max < -90 or y_min > 90 or y_min < -90:
        return False
    return True


def open_url(url: str):
    url = QUrl(url)
    QDesktopServices.openUrl(url)


def open_model_info(model_name: str):
    """Open model info page in browser"""
    if 'aerial' in model_name.lower() or 'uav' in model_name.lower():
        section = "buildings-aerial-imagery"
    elif 'roads' in model_name.lower():
        section = "roads"
    elif 'fields' in model_name.lower():
        section = "agriculture-fields"
    elif 'constructions' in model_name.lower():
        section = "constructions"
    elif "forest" in model_name.lower():
        section = "forest"
    elif "dense" in model_name.lower():
        section = "high-density-housing"
    elif 'buildings' in model_name.lower():
        section = "buildings"
    else:
        section = ""
    open_url(f"{config.MODEL_DOCS_URL}#{section}")


def check_processing_limit(billing_type: BillingType,
                           remaining_limit: Optional[float],
                           remaining_credits: Optional[int],
                           aoi_size: float,
                           processing_cost: int):
    """Check if the user has exceeded the processing limit."""
    if billing_type == BillingType.area:
        return remaining_limit >= aoi_size
    elif billing_type == BillingType.credits:
        return remaining_credits >= processing_cost
    else: # billing_type == BillingType.none
        return True


def generate_plugin_header(plugin_name: str, 
                           env: Optional[str], 
                           project_name: Optional[str], 
                           user_role: Optional[str],
                           project_owner: Optional[str]) -> str:
        header = plugin_name
        if env and env != "production":
            header = header + f" {env}"
        if project_name and project_name != "Default":
            header = header + f" | Project: {project_name}"
        if user_role and project_owner:
            if user_role != UserRole.owner:
                header = header + f" ({user_role}, owner: {project_owner})"
        return header
