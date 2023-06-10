import json
from pyproj import Proj, transform
from PyQt5.QtNetwork import QNetworkReply
from qgis.core import (QgsRectangle,
                       QgsRasterLayer,
                       QgsFeature,
                       QgsMapLayer,
                       QgsGeometry,
                       QgsMapLayerType,
                       QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsDistanceArea)
from .geometry import clip_aoi_to_image_extent
from .helpers import WGS84, to_wgs84, WGS84_ELLIPSOID


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


def generate_xyz_layer_definition(url, username, password, max_zoom, source_type):
    """
    It includes quadkey, tms and xyz layers, because QGIS treats them the same
    """
    if source_type == 'tms':
        # that is how QGIS understands that this is TMS basemap
        url = url.replace('{y}', '{-y}')
    url = url.replace('&', '%26').replace('=', '%3D')
    params = {
        'type': 'xyz',  # QGIS shows quadkey, tms, xyz - all as xyz layer
        'url': url,
        'zmin': 0,
        'zmax': max_zoom,
        'username': username,
        'password': password
    }
    uri = '&'.join(f'{key}={val}' for key, val in params.items())  # don't url-encode it
    return uri


def maxar_tile_url(base_url, image_id=None):
    """
    base_url is copied from maxar website and looks like
    https://securewatch.digitalglobe.com/earthservice/wmtsaccess?connectid=<UUID>
    we need to return TileUrl with TileMatrix set and so on
    """
    if not base_url.endswith('?'):
        # case when this is not the first arguments in layer
        base_url = base_url + '&'
    url = base_url + "SERVICE=WMTS" \
                      "&VERSION=1.0.0" \
                      "&STYLE=" \
                      "&REQUEST=GetTile" \
                      "&LAYER=DigitalGlobe:ImageryTileService" \
                      "&FORMAT=image/jpeg" \
                      "&TileRow={y}" \
                      "&TileCol={x}" \
                      "&TileMatrixSet=EPSG:3857" \
                      "&TileMatrix=EPSG:3857:{z}"
    url = add_image_id(url, image_id)
    return url


def add_image_id(url: str, image_id: str):
    if not image_id:
        return url
    if not url.endswith('?'):
        url = url + '&'
    return url + f'CQL_FILTER=feature_id=\'{image_id}\''


def add_connect_id(url: str, connect_id: str):
    if not url.endswith('?'):
        url = url + '&'
    return url + f'CONNECTID={connect_id}'


def get_bounding_box_from_tile_json(response: QNetworkReply) -> QgsRectangle:
    """Construct bounding box from response got from tile server as tile_json.
    As tile server returns tile_json in epsg:4326, first transform it to epsg:3857.
    :param: response: QNetworkReply, response got from tile server, tile_json.
    :return: QgsRectangle
    """
    bounds = json.loads(response.readAll().data()).get('bounds')
    out_proj = Proj(init='epsg:3857')
    in_proj = Proj(init='epsg:4326')

    xmin, ymin = transform(in_proj, out_proj, bounds[0], bounds[1])
    xmax, ymax = transform(in_proj, out_proj, bounds[2], bounds[3])

    return QgsRectangle(xmin, ymin, xmax, ymax)


def get_raster_aoi(raster_layer: QgsRasterLayer,
                   selected_aoi: QgsFeature,
                   use_image_extent_as_aoi: bool) -> QgsGeometry:
    layer_extent = QgsFeature()
    layer_extent.setGeometry(get_layer_extent(raster_layer))
    if not use_image_extent_as_aoi:
        # If we do not use the layer extent as aoi, we still create it and use it to crop the selected AOI
        try:
            feature = next(clip_aoi_to_image_extent(aoi_geometry=selected_aoi,
                                                    extent=layer_extent))
        except StopIteration:
            return None
    else:
        feature = layer_extent
    return feature.geometry()


def is_polygon_layer(layer: QgsMapLayer) -> bool:
    """Determine if a layer is of vector type and has polygonal geometry.
    :param layer: A layer to test
    """
    return layer.type() == QgsMapLayerType.VectorLayer and layer.geometryType() == QgsWkbTypes.PolygonGeometry


def calculate_aoi_area(aoi: QgsGeometry,
                       project_crs: QgsCoordinateReferenceSystem) -> float:
    calculator = QgsDistanceArea()
    calculator.setEllipsoid(WGS84_ELLIPSOID)
    calculator.setSourceCrs(WGS84, project_crs)
    aoi_size = calculator.measureArea(aoi) / 10 ** 6  # sq. m to sq.km
    return aoi_size


def collect_geometry_from_layer(layer: QgsMapLayer) -> QgsGeometry:
    features = list(layer.getSelectedFeatures()) or list(layer.getFeatures())
    if len(features) == 1:
        aoi = features[0].geometry()
    else:
        aoi = QgsGeometry.collectGeometry([feature.geometry() for feature in features])
    return aoi


def calculate_layer_area(layer: QgsMapLayer,
                         project_crs: QgsCoordinateReferenceSystem) -> float:
    crs = layer.crs()
    aoi = collect_geometry_from_layer(layer)
    if crs != WGS84:
        aoi = to_wgs84(aoi, crs)

    return calculate_aoi_area(aoi,
                              crs,
                              project_crs)