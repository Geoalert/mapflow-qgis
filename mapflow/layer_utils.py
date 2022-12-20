from typing import Optional


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
