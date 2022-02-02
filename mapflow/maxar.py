from qgis.core import QgsGeometry

from mapflow.http import Http
from mapflow.config import TIMEZONE
from mapflow.provider import Provider


class Maxar(Provider):
    """"""
    metadata_attributes = {
        'Product Type': 'productType',
        'Band Order': 'colorBandOrder',
        'Cloud %': 'cloudCover',
        f'\N{DEGREE SIGN} Off Nadir': 'offNadirAngle',
        f'Date & Time ({TIMEZONE})': 'acquisitionDate',
        'Image ID': 'featureId'
    }
    metadata_static_request_params = {
        'SERVICE': 'WFS',
        'VERSION': '2.0.0',
        'REQUEST': 'GetFeature',
        'TYPENAME': 'DigitalGlobe:FinishedFeature',
        'SRSNAME': 'urn:ogc:def:crs:EPSG::3857',
        'WIDTH': 3000,
        'HEIGHT': 3000,
        'SORTBY': 'acquisitionDate+D',
        'PROPERTYNAME': ','.join((*metadata_attributes.values(), 'geometry'))
    }
    metadata_static_query_params = '&'.join(f'{key}={value}' for key, value in metadata_request_params.items())

    def __init__(self, username: str = None, password: str = None, mapflow_base_url: str = None) -> None:
        super().__init__()
        if username is None and password is None:
            if not mapflow_base_url:
                raise ValueError('Neither user credentials nor Mapflow URL was provided')
            self._metadata_url = mapflow_base_url + '/meta'
            self.proxy_via_mapflow = True
        elif username is not None and password is not None:
            self._metadata_url = 'https://securewatch.digitalglobe.com/catalogservice/wfsaccess'
            self.proxy_via_mapflow = False
            self.username = username
            self.password = password

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

    def get_metadata(
        self,
        aoi: QgsGeometry,
        product: str,
        from_: str,
        to: str,
        max_cloud_cover: int,
        min_intersection: int
    ):
        """Get SecureWatch image metadata."""
        self.save_provider_auth()
        self.metadata_aoi = aoi
        filter_params = (
            f'intersects(geometry,srid=4326;{aoi.asWkt(precision=6).replace(" ", "+")})',
            f'acquisitionDate>={from_}',
            f'acquisitionDate<={to}'
        )
        url = (
            self.metadata_url + '?' + 
            + '&CQL_FILTER=(' + 'and'.join(f'({param})' for param in filter_params) + ')'
        )
        callback_kwargs = {
            'product': product,
            'min_intersection': min_intersection,
            'max_cloud_cover': max_cloud_cover
        }
        if self.dlg.providerAuthGroup.isChecked():  # user's own account
            connect_id = self.settings.value('providers')[product]['connectId']
            if not regex.UUID.match(connect_id):
                self.show_connect_id_dialog(product)
                return
            url += '&CONNECTID=' + connect_id
            encoded_credentials = b64encode(':'.join((
                self.dlg.providerUsername.text(),
                self.dlg.providerPassword.text()
            )).encode())
            self.http.get(
                url=url,
                auth=f'Basic {encoded_credentials.decode()}'.encode(),
                callback=self.get_maxar_metadata_callback,
                callback_kwargs=callback_kwargs,
                error_handler=self.get_maxar_metadata_error_handler,
                use_default_error_handler=False
            )
        else:  # assume user wants to use our account, proxy thru Mapflow
            self.http.post(
                url=f'{self.server}/meta',
                callback=self.get_maxar_metadata_callback,
                callback_kwargs=callback_kwargs,
                body=json.dumps({
                    'url': url,
                    'connectId': product.split()[1].lower()
                }).encode(),
                timeout=7
            )
