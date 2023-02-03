from .provider import staticproperty
from .xyz_provider import XYZProvider, SourceType, CRS
from .proxy_provider import ProxyProvider, MaxarProxyProvider
from ...config import SENTINEL_OPTION_NAME


class SentinelProvider(ProxyProvider):
    def __init__(self,
                 proxy,
                 **kwargs):
        name = SENTINEL_OPTION_NAME
        super().__init__(name=name,
                         url=None,
                         source_type=SourceType.sentinel_l2a,
                         proxy=proxy,
                         **kwargs)

    @property
    def requires_image_id(self):
        return True

    def to_processing_params(self, image_id=None):
        if not image_id:
            raise ValueError("Sentinel provider must have image ID to launch the processing")
        return{'url': image_id,
               'source_type': self.source_type.value}, {}


class MaxarVividProxyProvider(MaxarProxyProvider):
    def __init__(self, proxy):
        super().__init__(name="Maxar Vivid", proxy=proxy)

    @property
    def requires_image_id(self):
        return False

    @property
    def connect_id(self):
        return 'vivid'


class MaxarSecureWatchProxyProvider(MaxarProxyProvider):
    def __init__(self, proxy):
        super().__init__(name="Maxar SecureWatch", proxy=proxy)

    @property
    def requires_image_id(self):
        return False

    @property
    def connect_id(self):
        return 'securewatch'


class MapboxProvider(XYZProvider):
    def __init__(self):
        super().__init__(name="Mapbox",
                         url=None, #  'https://api.tiles.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.jpg?access_token={token}',
                         crs=CRS.web_mercator)
    @property
    def preview_url(self, image_id=None):
        return None

    def to_processing_params(self, image_id=None):
        # This is a default provider which is supplied on server
        return {}, {}

    @property
    def is_default(self):
        return True
