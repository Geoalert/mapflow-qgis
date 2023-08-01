from .xyz_provider import XYZProvider, SourceType, CRS
from .proxy_provider import ProxyProvider, MaxarProxyProvider
from ...schema.processing import PostSourceSchema, PostProviderSchema
from ...constants import SENTINEL_OPTION_NAME
from ...errors.plugin_errors import PluginError
from ...schema.provider import ProviderReturnSchema


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
            raise PluginError("Sentinel provider must have image ID to launch the processing")
        return PostSourceSchema(url=image_id, source_type=self.source_type.value), {}

    @property
    def meta_url(self):
        return self.proxy + '/meta/skywatch/id'


class MaxarVividProxyProvider(MaxarProxyProvider):
    def __init__(self, proxy):
        super().__init__(name="Maxar Vivid", proxy=proxy)

    @property
    def requires_image_id(self):
        return True

    @property
    def connect_id(self):
        return 'vivid'


class MaxarSecureWatchProxyProvider(MaxarProxyProvider):
    def __init__(self, proxy):
        super().__init__(name="Maxar SecureWatch", proxy=proxy)

    @property
    def requires_image_id(self):
        return True

    @property
    def connect_id(self):
        return 'securewatch'


class DefaultProvider(XYZProvider):
    def __init__(self,
                 id: str,
                 name: str,
                 display_name: str):
        super().__init__(name=name,
                         display_name=display_name,
                         url=None,
                         crs=CRS.web_mercator)
        self.id = id

    @property
    def preview_url(self, image_id=None):
        # We cannot provide preview via our proxy
        # TODO: add preview url!
        raise NotImplementedError

    @property
    def is_default(self):
        return True

    @classmethod
    def from_response(cls, response: ProviderReturnSchema):
        return cls(id=response.id,
                   name=response.name,
                   display_name=response.displayName)

    def to_processing_params(self, image_id=None):
        return PostProviderSchema(data_provider=self.name, year="2022"), {}
