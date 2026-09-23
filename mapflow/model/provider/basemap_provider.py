"""
Basic, non-authentification XYZ provider
"""
from abc import ABC
from typing import Optional

from .provider import UsersProvider, staticproperty
from ...schema.provider_types import SourceType
from ...schema.processing import UserDefinedParams, UserDefinedSchema, ProcessingParams


class BasemapProvider(UsersProvider, ABC):
    def to_processing_params(self,
                             provider_name: Optional[str] = None,
                             zoom: Optional[str] = None):
        params = {
            'sourceType': self.source_type.value.upper(),
            'url': self.url,
            'zoom': zoom,
            'crs': self.crs.value.lower(),
            'rasterLogin': None,
            'rasterPassword': None
        }
        if self.credentials:
            params.update(rasterLogin=self.credentials.login,
                          rasterPassword=self.credentials.password)
        return ProcessingParams(sourceParams=UserDefinedParams(UserDefinedSchema(**params))), {}

    @property
    def requires_image_id(self):
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
    def __init__(self, **kwargs):
        kwargs.update(source_type=SourceType.xyz)
        super().__init__(**kwargs)

    @staticproperty
    def option_name():
        return 'xyz'

    @property
    def meta_url(self):
        return None


class TMSProvider(BasemapProvider):
    def __init__(self, **kwargs):
        kwargs.update(source_type=SourceType.tms)
        super().__init__(**kwargs)

    @staticproperty
    def option_name():
        return 'tms'

    @property
    def meta_url(self):
        return None


class QuadkeyProvider(BasemapProvider):
    def __init__(self, **kwargs):
        kwargs.update(source_type=SourceType.quadkey)
        super().__init__(**kwargs)

    @staticproperty
    def option_name():
        return 'quadkey'

    @property
    def meta_url(self):
        return None
