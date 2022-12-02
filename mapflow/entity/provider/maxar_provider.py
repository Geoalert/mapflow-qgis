from .xyz_provider import XYZProvider, BasicAuth
from .provider import CRS
from ...layer_utils import maxar_tile_url, add_image_id
from ...requests.maxar_metadata_request import MAXAR_REQUEST_BODY, MAXAR_META_URL


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
                 credentials: BasicAuth,
                 image_id=None,
                 **kwargs):
        super().__init__(name=name,
                         url=maxar_tile_url(url, image_id),
                         crs=CRS.web_mercator,
                         credentials=credentials,
                         is_default=False)

    def to_dict(self):
        data = super().to_dict()
        return data


class MaxarSecureWatchProvider(MaxarProvider):
    def __init__(self, name, url, credentials, image_id, **kwargs):
        super().__init__(name=name, url=url, credentials=credentials, image_id=image_id, **kwargs)
        self.image_id = image_id

    @property
    def meta_url(self):
        return MAXAR_META_URL

    @property
    def meta_request(self, **kwargs):
        return MAXAR_REQUEST_BODY.format(**kwargs).encode()

    def to_processing_params(self, image_id=None):
        if not image_id:
            raise ValueError("SecureWatch requires image id")
        return{'url': add_image_id(self.url, image_id),
               'source_type': self.source_type,
               'crs': self.crs.value,
               'credentials': self.credentials.tuple}


class MaxarVividProvider(MaxarProvider):
    def __init__(self, name, url, credentials, **kwargs):
        super().__init__(name=name, url=url, credentials=credentials, image_id=None, **kwargs)

    def to_processing_params(self, image_id=None):
        return {'url': add_image_id(self.url, image_id),
                'connectid': 'securewatch',
                'source_type': self.source_type,
                'crs': self.crs.value,
                'credentials': self.credentials.tuple}
