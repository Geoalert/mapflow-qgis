from typing import Tuple, Optional
from enum import Enum

PROVIDERS_KEY = 'providers'

class StrEnum(str, Enum):
    pass


class SourceType(StrEnum):
    xyz = 'xyz'
    tms = 'tms'
    quadkey = 'quadkey'
    sentinel_l2a = 'sentinel_l2a'


class CRS(StrEnum):
    web_mercator = 'EPSG:3857'
    world_mercator = 'EPSG:3395'


class Provider:
    def __init__(self,
                 name: str,
                 source_type: SourceType,
                 url: str,
                 crs: Optional[CRS],
                 credentials: Optional[Tuple[str, str]] = None,
                 connect_id: str = None,
                 protected: bool = False):
        self.name = name
        self.source_type = source_type
        self.url = url
        self.credentials = credentials
        self.connect_id = connect_id
        self.crs = crs
        # default value is Web Mercator - for all that were added before
        if self.source_type in [SourceType.xyz, SourceType.tms, SourceType.quadkey] and not self.crs:
            self.CRS = CRS.web_mercator
        self.protected = protected

    def dict(self):
        data = {
                'name': self.name,
                'source_type': self.source_type.value,
                'crs': self.source_type.value,
                'url': self.url
            }
        if self.credentials:
            data.update({'credentials': self.credentials})
        if self.connect_id:
            data.update({'connect_id': self.connect_id})
        return {self.name: data}

    @classmethod
    def from_settings(cls, settings, name):
        data = settings.value(PROVIDERS_KEY).get(name)
        if not data:
            raise KeyError('Unknown provider {name}')
        if not data.get('name', ''):
            # guard in case the provider does not contain the name inside the structure, only as a key
            # todo: is it necessary btw?
            data['name'] = name
        return cls(**data)

    def to_settings(self, settings):
        providers = settings.value(PROVIDERS_KEY)
        providers.update(self.dict())
        settings.setValue(PROVIDERS_KEY, providers)
