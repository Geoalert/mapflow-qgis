from typing import Optional, List

from .provider import BasicAuth
from .provider import ProviderInterface, SourceType, CRS
from ...constants import SENTINEL_OPTION_NAME, SEARCH_OPTION_NAME, CATALOG_OPTION_NAME
from ...errors.plugin_errors import ImageIdRequired
from ...schema import (PostSourceSchema, 
                       PostProviderSchema, 
                       DataProviderParams,
                       MyImageryParams,
                       ImagerySearchParams,
                       ProcessingParams,)
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

    def to_processing_params(self,
                             provider_name: Optional[str] = None,
                             zoom: Optional[str] = None):
        if not image_id and requires_id is True:
            raise ImageIdRequired("Sentinel provider must have image ID to launch the processing")
        return PostSourceSchema(url=image_id,
                                source_type=SourceType.sentinel_l2a), {}

    @property
    def meta_url(self):
        return self.proxy + '/meta/skywatch/id'

    @property
    def is_default(self):
        return True


class ImagerySearchProvider(ProviderInterface):
    """
    Represents imagery-based providers that are accessible via Mapflow API
    It allows to search the images based on metadata, see their footprings on the map,
    and order processing with particular image.

    It works with all the providers that are linked to the user via the same interface, regardless of
    real data provider
    """

    def __init__(self,
                 proxy,
                 **kwargs):
        super().__init__(name=SEARCH_OPTION_NAME)
        self.proxy = proxy
        self.requires_id: Optional[bool] = None
        self.image_id: Optional[List[str]] = None

    def preview_url(self, image_id=None):
        return None

    @property
    def requires_image_id(self):
        return self.requires_id

    def to_processing_params(self,
                             provider_name: Optional[str] = None,
                             zoom: Optional[str] = None):
        if not self.image_id and self.requires_id is True:
            raise ImageIdRequired("Search provider must have image ID to launch the processing")
        return ProcessingParams(sourceParams=ImagerySearchParams(dataProvider=provider_name,
                                                                 imageIds=self.image_id,
                                                                 zoom=zoom)), {}

    @property
    def meta_url(self):
        return self.proxy + '/catalog/meta'

    @property
    def is_default(self):
        return True


class MyImageryProvider(ProviderInterface):
    """
    Allows to create mosaics and upload user's imagery 
    to later run a processing using it
    """

    def __init__(self):
        super().__init__(name=CATALOG_OPTION_NAME)
        self.mosaic_id: Optional[str] = None
        self.image_ids: Optional[List[str]] = None

    @property
    def meta_url(self):
        return None

    @property
    def is_default(self):
        return True
    
    @property
    def requires_image_id(self):
        return False
    
    def to_processing_params(self,
                             provider_name: Optional[str] = None,
                             zoom: Optional[str] = None):
        return ProcessingParams(sourceParams=MyImageryParams(imageIds=self.image_ids, 
                                                             mosaicId=self.mosaic_id)), {}

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

    def to_processing_params(self,
                             provider_name: Optional[str] = None,
                             zoom: Optional[str] = None):
        return ProcessingParams(sourceParams=DataProviderParams(providerName=provider_name, 
                                                                zoom=zoom)), {}
