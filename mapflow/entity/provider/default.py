from typing import Optional
from .provider import ProviderInterface, SourceType, CRS
from .basemap_provider import BasicAuth
from ...schema.processing import PostSourceSchema, PostProviderSchema
from ...constants import SENTINEL_OPTION_NAME
from ...errors.plugin_errors import PluginError
from ...schema.provider import ProviderReturnSchema


class SentinelProvider(ProviderInterface):
    def __init__(self,
                 proxy,
                 **kwargs):
        super().__init__(name=SENTINEL_OPTION_NAME)
        self.proxy = proxy

    def preview_url(self, image_id=None):
        return None

    @property
    def requires_image_id(self):
        return True

    def to_processing_params(self, image_id=None):
        if not image_id:
            raise PluginError("Sentinel provider must have image ID to launch the processing")
        return PostSourceSchema(url=image_id,
                                source_type=SourceType.sentinel_l2a), {}

    @property
    def meta_url(self):
        return self.proxy + '/meta/skywatch/id'

    @property
    def is_default(self):
        return True


class DefaultProvider(ProviderInterface):
    """
    Represents a tile-based (mosaic) data provider returned by the server.
    "Tile-based" means that the provider does not support imagery search and selection,
    and has only one mosaic for any place
    They are "default" in the sense that they are not set up by user.
    """

    def __init__(self,
                 id: str,
                 name: str,
                 api_name: str,
                 price: dict,
                 preview_url: Optional[str] = None,
                 source_type: SourceType = SourceType.xyz,
                 credentials: BasicAuth = BasicAuth()):
        super().__init__(name=name)
        self.id = id
        self.api_name = api_name
        self.price = price
        self._preview_url = preview_url

        # In the default (server-side) providers these params are for preview only
        # By now, this is the only option for the server-side providers.
        # If this will change, we will initialize this from api request
        self.source_type = source_type
        self.credentials = credentials
        self.crs = CRS.web_mercator

    def preview_url(self, image_id=None):
        # We cannot provide preview via our proxy
        if not self._preview_url:
            raise NotImplementedError
        return self._preview_url

    @property
    def is_default(self):
        return True

    @property
    def is_payed(self):
        return any(value > 0 for value in self.price.values())

    @property
    def meta_url(self):
        return None

    @property
    def requires_image_id(self):
        return False

    @classmethod
    def from_response(cls, response: ProviderReturnSchema):
        return cls(id=response.id,
                   name=response.displayName,
                   api_name=response.name,
                   price=response.price_dict,
                   preview_url=response.previewUrl)

    def to_processing_params(self, image_id=None):
        return PostProviderSchema(data_provider=self.api_name), {}
