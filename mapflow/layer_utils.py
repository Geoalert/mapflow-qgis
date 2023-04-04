import json
from pyproj import Proj, transform
from PyQt5.QtNetwork import QNetworkReply
from qgis.core import QgsRectangle


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
