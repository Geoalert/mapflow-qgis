from .provider import ProviderInterface, SourceType
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
                 price: dict):
        super().__init__(name=name)
        self.id = id
        self.api_name = api_name
        self.price = price

    @property
    def preview_url(self, image_id=None):
        # We cannot provide preview via our proxy
        # TODO: add preview url!
        raise NotImplementedError

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
                   price=response.price_dict)

    def to_processing_params(self, image_id=None):
        return PostProviderSchema(data_provider=self.api_name), {}
