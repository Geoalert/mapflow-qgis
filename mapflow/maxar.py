import json
from base64 import b64encode

from qgis.core import QgsGeometry

from mapflow import regex
from mapflow.http import Http
from mapflow.config import TIMEZONE
from mapflow.provider import Provider


class Maxar(Provider):
    """"""
    TYPE = 'xyz'
    SUPPORTED_PRODUCTS = 'Maxar SecureWatch', 'Maxar Vivid', 'Maxar Basemaps'
    IMAGERY_DIRECT_URL = (
        'https://securewatch.maxar.com/earthservice/wmtsaccess?' +
        '&'.join(f'{key}={value}' for key, value in {
            'SERVICE': 'WMTS', 
            'VERSION': '1.0.0',
            'STYLE': '',
            'REQUEST': 'GetTile',
            'LAYER': 'DigitalGlobe:ImageryTileService',
            'FORMAT': 'image/jpeg',
            'TileRow': '{y}',
            'TileCol': '{x}',
            'TileMatrixSet': 'EPSG:3857',
            'TileMatrix': 'EPSG:3857:{z}'
        })
    )
    METADATA_ATTRIBUTES = 'productType', 'colorBandOrder', 'cloudCover', 'offNadirAngle', 'acquisitionDate', 'featureId'
    METADATA_DIRECT_URL = (
        'https://securewatch.maxar.com/catalogservice/wfsaccess' +
        '&'.join(f'{key}={value}' for key, value in {
            'SERVICE': 'WFS',
            'VERSION': '2.0.0',
            'REQUEST': 'GetFeature',
            'TYPENAME': 'DigitalGlobe:FinishedFeature',
            'SRSNAME': 'urn:ogc:def:crs:EPSG::3857',
            'WIDTH': 3000,
            'HEIGHT': 3000,
            'SORTBY': 'acquisitionDate+D',
            'PROPERTYNAME': ','.join((*METADATA_ATTRIBUTES, 'geometry'))
        }.items())
    )
    MAX_FREE_ZOOM = 12
    ID_COLUMN_INDEX = METADATA_ATTRIBUTES.index('featureId')
    METADATA_COLUMN_NAMES = (
        'Product Type',
        'Band Order',
        'Cloud %',
        '\N{DEGREE SIGN} Off Nadir',
        f'Date & Time ({TIMEZONE})',
        'Image ID'
    )
    DATETIME_COLUMN_INDEX = METADATA_COLUMN_NAMES.index(f'Date & Time ({TIMEZONE})')
    CLOUD_COLUMN_INDEX = METADATA_COLUMN_NAMES.index(f'Cloud %')

    def __init__(
        self,
        connect_ids: dict,
        mapflow_base_url: str,
        current_product: str,
        username: str = None,
        password: str = None,
    ) -> None:
        """"""
        super().__init__()
        self.products = tuple(connect_ids.keys())
        self.current_product = current_product
        self.connect_ids = connect_ids
        if username is None and password is None:
            self._metadata_url = mapflow_base_url + '/meta'
            self.proxy_via_mapflow = True
        elif username is not None and password is not None:
            self._metadata_url = self.METADATA_DIRECT_URL
            self.proxy_via_mapflow = False
            self.set_auth(username, password)

    @property
    def connect_id(self):
        """Each Maxar product (SecureWatch/Vivid/Basemaps) has its own ConnectID."""
        return self._connect_id

    @connect_id.setter
    def connect_id(self, connect_id):
        if regex.UUID.match(connect_id):
            self._connect_id = connect_id
            return True
        return False

    @property
    def metadata_url(self):
        """The URL used to fetch metadata."""
        return self._metadata_url

    @metadata_url.setter
    def metadata_url(self, url: str):
        match = self.url_regex.match(url)
        if match is None:
            raise ValueError(f'"{url}" is not a valid URL')
        self._metadata_url = url

    def set_auth(self, username: str, password: str, connect_id: str) -> None:
        """"""
        self.connect_id = connect_id
        credentials_base64 = b64encode(f'{username}:{password}'.encode()).decode()
        self._basic_auth = f'Basic {credentials_base64}'.encode()

    def get_metadata(
        self, *,
        aoi: QgsGeometry,
        from_: str,
        to: str,
        max_cloud_cover: int,
        min_intersection: int
    ):
        """Get SecureWatch image metadata."""
        self.metadata_aoi = aoi
        filter_params = (
            f'intersects(geometry,srid=4326;{aoi.asWkt(precision=6).replace(" ", "+")})',
            f'acquisitionDate>={from_}',
            f'acquisitionDate<={to}'
        )
        cql_filter = '&CQL_FILTER=(' + 'and'.join(f'({param})' for param in filter_params) + ')'
        url = self._metadata_url + '&' + cql_filter
        callback_kwargs = {
            'product': self.product,
            'min_intersection': min_intersection,
            'max_cloud_cover': max_cloud_cover
        }
        if self.proxy_via_mapflow:
            self.http.post(
                url=self.url,
                callback=self.get_maxar_metadata_callback,
                callback_kwargs=callback_kwargs,
                body=json.dumps({
                    'url': url,
                    'connectId': self.current_product.split()[1].lower()
                }).encode(),
                timeout=7
            )
        else:
            # if not regex.UUID.match(connect_id):
            #     self.show_connect_id_dialog(self.product)
            #     return
            self.http.get(
                url=f'{url}&CONNECTID={self.connect_ids[self.current_product]}',
                auth=self._basic_auth,
                callback=self.get_maxar_metadata_callback,
                callback_kwargs=callback_kwargs,
                error_handler=self.get_maxar_metadata_error_handler,
                use_default_error_handler=False
            )
