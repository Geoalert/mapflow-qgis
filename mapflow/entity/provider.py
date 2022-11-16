from typing import Tuple, Optional, Iterable, Union
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


class Provider:
    def __init__(self,
                 name: str,
                 url: str,
                 source_type: Union[SourceType, str] = SourceType.xyz,
                 crs: Optional[Union[CRS, str]] = None,
                 credentials: Optional[Tuple[str, str]] = None,
                 connect_id: Optional[str] = None,
                 api_key: Optional[str] = None,
                 protected: bool = False,
                 editable_fields: Iterable[str] = ('name', 'url', 'type', 'crs')):
        self.name = name
        self.source_type = SourceType(source_type)
        self.url = url
        self.credentials = credentials
        self.connect_id = connect_id
        self.api_key = api_key
        # default value is Web Mercator
        if not crs and self.source_type.requires_crs:
            self.crs = CRS.web_mercator
        elif not self.source_type.requires_crs:
            self.crs = None
        else:
            self.crs = CRS(crs)
        self.protected = protected
        self.editable_fields = editable_fields

    def to_dict(self):
        data = {
                'name': self.name,
                'source_type': self.source_type.value if self.source_type else None,
                'crs': self.crs.value if self.crs else None,
                'url': self.url
            }
        if self.credentials:
            data.update({'credentials': self.credentials})
        if self.connect_id:
            data.update({'connect_id': self.connect_id})
        return data

    @classmethod
    def from_params(cls, params: to_dict, name=None):
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

    @classmethod
    def from_settings(cls, settings, name):
        params = settings.value(PROVIDERS_KEY).get(name)
        if not params:
            raise KeyError('Unknown provider {name}')
        if not params.get('name', ''):
            # guard in case the provider does not contain the name inside the structure, only as a key
            # todo: is it necessary btw?
            params['name'] = name
        return cls.from_params(params)

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
        return Provider(params)


class ProvidersDict(dict):
    @classmethod
    def default_providers(cls):
        return {'Mapbox': Provider(name='mapbox',
                                   url='https://api.tiles.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.jpg?'
                                       'access_token=pk.eyJ1Ijoib3BlbnN0cmVldG1hcCIsImEiOiJja2w5YWt5bnYwNjZmMnFwZjhtbHk1MnA1In0.eq2aumBK6JuRoIuBMm6Gew',
                                   source_type=SourceType.xyz,
                                   crs=CRS.web_mercator)}

    @classmethod
    def from_settings(cls, settings):
        providers_settings = settings.value(PROVIDERS_KEY, None)
        if not providers_settings:
            return ProvidersDict.default_providers()
        dict_ = {name: Provider.from_params(params, name) for name, params in providers_settings.items()}
        return cls(dict_)

    def dict(self):
        return {name: provider.to_dict() for name, provider in self.items()}

    def to_settings(self, settings):
        settings.setValue(PROVIDERS_KEY, self.dict())
