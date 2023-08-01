from typing import Iterable, Union, Optional
from enum import Enum


class staticproperty(staticmethod):
    def __get__(self, *_):
        return self.__func__()


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


class BasicAuth:
    def __init__(self, login: str = "", password: str = ""):
        if not isinstance(login, str) or not isinstance(password, str):
            raise TypeError("Login and password must be string")
        self.login = login
        self.password = password

    def __iter__(self):
        # to convert to tuple/list
        yield self.login
        yield self.password

    def __bool__(self):
        return bool(self.login) or bool(self.password)

    def __str__(self):
        return f'{self.login}:{self.password}'


class Provider:
    def __init__(self,
                 name: str,
                 url: str,
                 source_type: Union[SourceType, str] = SourceType.xyz,
                 crs: Optional[Union[CRS, str]] = None,
                 credentials: Union[BasicAuth, Iterable[str]] = BasicAuth(),
                 save_credentials: bool=True,
                 display_name: Optional[str] = None,
                 **kwargs):
        self.name = name
        if display_name:
            self.display_name = display_name
        else:
            self.display_name = name
        self.source_type = SourceType(source_type)
        self.url = url
        if not crs and self.source_type.requires_crs:
            self.crs = CRS.web_mercator
        elif not self.source_type.requires_crs:
            self.crs = None
        else:
            self.crs = CRS(crs)
        if isinstance(credentials, BasicAuth):
            self.credentials = credentials
        else:
            self.credentials = BasicAuth(*credentials)
        self.save_credentials = save_credentials

    def to_dict(self):
        if self.save_credentials:
            credentials = tuple(self.credentials)
        else:
            credentials = ("", "")
        if self.crs:
            crs = self.crs.value
        else:
            crs = None
        data = {
            'name': self.name,
            'source_type': self.source_type.value,
            'option_name': self.option_name,
            'url': self.url,
            'credentials': credentials,
            'save_credentials': self.save_credentials,
            'crs': crs
            }
        return data

    @property
    def is_default(self):
        raise NotImplementedError

    @property
    def is_proxy(self):
        raise NotImplementedError

    @property
    def requires_image_id(self):
        raise NotImplementedError

    @property
    def meta_url(self):
        raise NotImplementedError

    @staticproperty
    def option_name():
        # option for interface and settings
        raise NotImplementedError

    @property
    def is_payed(self):
        return False

    def preview_url(self, image_id=None):
        raise NotImplementedError

    def to_processing_params(self, image_id=None):
        """ You cannot create a processing with generic provider without implementation"""
        raise NotImplementedError
