"""
Direct use of MAXAR vivid/secureWatch with user's credentials
"""
from .xyz_provider import XYZProvider, BasicAuth
from .provider import CRS
from ...layer_utils import maxar_tile_url


class MaxarProvider(XYZProvider):
    def __init__(self,
                 name,
                 url,
                 credentials: BasicAuth,
                 **kwargs):
        super().__init__(name=name, url=maxar_tile_url(url), crs=CRS.web_mercator, credentials=credentials)

    def to_dict(self):
        data = super().to_dict()
        return data
