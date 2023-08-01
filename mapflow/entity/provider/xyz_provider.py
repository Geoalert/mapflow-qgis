"""
Basic, non-authentification XYZ provider
"""
from typing import Union, Iterable
from urllib.parse import urlparse, parse_qs
from .provider import SourceType, CRS, Provider, BasicAuth, staticproperty
from ...schema.processing import PostSourceSchema
from ...functional.layer_utils import maxar_tile_url, add_connect_id
from ...requests.maxar_metadata_request import MAXAR_REQUEST_BODY, MAXAR_META_URL


class BasemapProvider(Provider):
    def __init__(self,
                 name: str,
                 url: str,
                 source_type: Union[SourceType, str],
                 crs: [Union[CRS, str]] = CRS.web_mercator,
                 credentials: Union[BasicAuth, Iterable[str]] = BasicAuth(),
                 save_credentials: bool = False,
                 **kwargs):
        super().__init__(name=name,
                         url=url,
                         source_type=source_type,
                         crs=crs,
                         is_default=False,
                         credentials=credentials,
                         save_credentials=save_credentials)

    def to_processing_params(self, image_id=None):
        params = {
            'url': self.url,
            'projection': self.crs.value.lower(),
            'source_type': self.source_type.value
        }
        if self.credentials:
            params.update(raster_login=self.credentials.login,
                          raster_password=self.credentials.password)
        return PostSourceSchema(**params), {}

    @property
    def requires_image_id(self):
        return False

    @property
    def is_proxy(self):
        return False

    def preview_url(self, image_id=None):
        return self.url

    @property
    def is_default(self):
        return False

    @staticproperty
    def option_name():
        # option for interface and settings
        raise NotImplementedError


class XYZProvider(BasemapProvider):
    def __init__(self,
                 name: str,
                 url: str,
                 crs: [Union[CRS, str]] = CRS.web_mercator,
                 credentials: Union[BasicAuth, Iterable[str]] = BasicAuth(),
                 save_credentials: bool = False,
                 **kwargs):
        super().__init__(name=name,
                         url=url,
                         source_type=SourceType.xyz,
                         crs=crs,
                         credentials=credentials,
                         save_credentials=save_credentials)

    @staticproperty
    def option_name():
        return 'xyz'


class TMSProvider(BasemapProvider):
    def __init__(self,
                 name: str,
                 url: str,
                 crs: [Union[CRS, str]] = CRS.web_mercator,
                 credentials: Union[BasicAuth, Iterable[str]] = BasicAuth(),
                 save_credentials: bool = False,
                 **kwargs):
        super().__init__(name=name,
                         url=url,
                         source_type=SourceType.tms,
                         crs=crs,
                         credentials=credentials,
                         save_credentials=save_credentials)

    @staticproperty
    def option_name():
        return 'tms'


class QuadkeyProvider(BasemapProvider):
    def __init__(self,
                 name: str,
                 url: str,
                 crs: [Union[CRS, str]] = CRS.web_mercator,
                 credentials: Union[BasicAuth, Iterable[str]] = BasicAuth(),
                 save_credentials: bool = False,
                 **kwargs):
        super().__init__(name=name,
                         url=url,
                         source_type=SourceType.quadkey,
                         crs=crs,
                         credentials=credentials,
                         save_credentials=save_credentials)

    @staticproperty
    def option_name():
        return 'quadkey'


class MaxarProvider(XYZProvider):
    """
    Direct use of MAXAR vivid/secureWatch with user's credentials
    This is a case of WMTS provider, and in the future we will add general WMTSProvider which will include it,
    but currently the parameters are fixed for just Maxar SecureWatch and Vivid, and form a XYZ link
    from a Maxar WMTS link with connectId
    """
    def __init__(self,
                 name,
                 url,
                 credentials: Union[BasicAuth, Iterable[str]],
                 save_credentials: bool = False,
                 **kwargs):
        super().__init__(name=name,
                         url=url,
                         crs=CRS.web_mercator,
                         credentials=credentials,
                         save_credentials=save_credentials)

        try:
            self.connect_id = parse_qs(urlparse(self.url.lower()).query)['connectid'][0]
        except (KeyError, IndexError):
            # could not extract connectId from URL!
            raise ValueError("Maxar provider link must contain your ConnectID parameter")

    @staticproperty
    def option_name():
        return 'Maxar WMTS'

    @property
    def meta_url(self):
        return add_connect_id(MAXAR_META_URL, self.connect_id)

    def meta_request(self, from_, to, max_cloud_cover, geometry):
        return MAXAR_REQUEST_BODY.format(from_=from_,
                                         to=to,
                                         max_cloud_cover=max_cloud_cover,
                                         geometry=geometry).encode()

    def to_processing_params(self, image_id=None):
        params = PostSourceSchema(url=maxar_tile_url(self.url, image_id),
                                  source_type=self.source_type,
                                  projection=self.crs.value,
                                  raster_login=self.credentials.login,
                                  raster_password=self.credentials.password)
        return params, {}

    def preview_url(self, image_id=None):
        return maxar_tile_url(self.url, image_id)



