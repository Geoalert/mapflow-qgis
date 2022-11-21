from typing import Iterable, Union
from enum import Enum

PROVIDERS_KEY = 'providers'


class StrEnum(str, Enum):
    pass


class SourceType(StrEnum):
    xyz = 'xyz'
    tms = 'tms'
    quadkey = 'quadkey'
    sentinel_l2a = 'sentinel_l2a'

    @property
    def requires_crs(self):
        return self.value in (self.xyz, self.tms, self.quadkey)


class CRS(StrEnum):
    web_mercator = 'EPSG:3857'
    world_mercator = 'EPSG:3395'


def provider_factory(**kwargs):
    return Provider.from_params(kwargs)


class Provider:
    def __init__(self,
                 name: str,
                 url: str,
                 source_type: Union[SourceType, str] = SourceType.xyz,
                 editable_fields: Iterable[str] = ('name', 'url', 'type'),
                 **kwargs):
        self.name = name
        self.source_type = SourceType(source_type)
        self.url = url
        self.editable_fields = editable_fields

    def to_dict(self):
        data = {
            'name': self.name,
            'source_type': self.source_type.value,
            'url': self.url,
            'editable_fields': list(self.editable_fields)
            }
        return data

    @property
    def requires_image_id(self):
        raise NotImplementedError

    @classmethod
    def from_params(cls, params: dict, name=None):
        """
        a method that fixes old and deprecated params before creating class; necessary for seamless migration of user's
        current providers
        """
        if not name and 'name' not in params:
            raise ValueError('Must have name in params keys or separately')
        elif 'name' not in params:
            params.update(name=name)
        if 'connectId' in params:
            params['connect_id'] = params.pop('connectId')
        if 'type' in params:
            params['source_type'] = params.pop('type')
        if 'token' in params:
            params['api_key'] = params.pop('token')
        if 'crs' in params:
            # truncate invalid CRS and replace with web mercator
            try:
                CRS('crs')
            except:
                params['crs'] = CRS.web_mercator
        return cls(**params)

    def to_processing_params(self):
        """ You cannot create a processing with generic provider without implementation"""
        raise NotImplementedError

    @classmethod
    def from_settings(cls, settings, name):
        params = settings.value(PROVIDERS_KEY).get(name)
        if not params:
            raise KeyError('Unknown provider {name}')
        return provider_factory(**params)

    def to_settings(self, settings):
        providers = settings.value(PROVIDERS_KEY)
        providers.update({self.name: self.to_dict()})
        settings.setValue(PROVIDERS_KEY, providers)

    def remove_from_settings(self, settings):
        providers = settings.value(PROVIDERS_KEY)
        providers.pop(self.name)
        settings.setValue(PROVIDERS_KEY, providers)

    def update(self, **kwargs):
        non_editable_keys = [k for k in kwargs.keys() if k not in self.editable_fields]
        if non_editable_keys:
            raise PermissionError("You are not allowed to change"
                                  " {non_editable_keys} in {provider}".format(non_editable_keys=non_editable_keys,
                                                                              provider=self.name))
        params = self.to_dict()
        params.update(kwargs)
        return provider_factory(**params)


