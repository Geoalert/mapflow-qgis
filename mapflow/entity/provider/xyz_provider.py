"""
Basic, non-authentification XYZ provider
"""
from typing import Union, Iterable
from provider import SourceType, CRS, Provider


class BasicAuth:
    def __init__(self, login: str = "", password: str = ""):
        if not isinstance(login, str) or not isinstance(password, str):
            raise TypeError("Login and password must be string")
        self.login = login
        self.password = password

    @property
    def tuple(self):
        return self.login, self.password

    def __bool__(self):
        return bool(self.login) or bool(self.password)


class BasemapProvider:
    def __init__(self,
                 name: str,
                 url: str,
                 source_type: Union[SourceType, str],
                 crs: [Union[CRS, str]] = CRS.web_mercator,
                 credentials: BasicAuth = BasicAuth(),
                 editable_fields: Iterable[str] = ('name', 'url', 'source_type', 'crs', 'credentials')):
        self.name = name
        self.source_type = SourceType(source_type)
        self.url = url
        # default value is Web Mercator
        if not crs and self.source_type.requires_crs:
            self.crs = CRS.web_mercator
        elif not self.source_type.requires_crs:
            self.crs = None
        else:
            self.crs = CRS(crs)
        self.credentials = credentials
        self.editable_fields = editable_fields

    def to_dict(self):
        data = {
            'name': self.name,
            'url': self.url,
            'source_type': self.source_type.value if self.source_type else None,
            'crs': self.crs.value,
            'credentials': self.credentials.tuple
            }
        return data

    def to_processing_params(self):
        params = {
            'url': self.url,
            'crs': self.crs.value,
            'source_type': self.source_type,
            'credentials': self.credentials.tuple
        }
        return params

    @property
    def requires_image_id(self):
        return False


class XYZProvider(BasemapProvider):
    def __init__(self,
                 name: str,
                 url: str,
                 crs: [Union[CRS, str]] = CRS.web_mercator,
                 credentials: BasicAuth = BasicAuth(),
                 editable_fields: Iterable[str] = ('name', 'url', 'crs', 'credentials')):
        super().__init__(name=name,
                         url=url,
                         source_type=SourceType.xyz,
                         crs=crs,
                         credentials=credentials,
                         editable_fields=editable_fields)


class TMSProvider(BasemapProvider):
    def __init__(self,
                 name: str,
                 url: str,
                 crs: [Union[CRS, str]] = CRS.web_mercator,
                 credentials: BasicAuth = BasicAuth(),
                 editable_fields: Iterable[str] = ('name', 'url', 'crs', 'credentials')):
        super().__init__(name=name,
                         url=url,
                         source_type=SourceType.tms,
                         crs=crs,
                         credentials=credentials,
                         editable_fields=editable_fields)


class QuadkeyProvider(BasemapProvider):
    def __init__(self,
                 name: str,
                 url: str,
                 crs: [Union[CRS, str]] = CRS.web_mercator,
                 credentials: BasicAuth = BasicAuth(),
                 editable_fields: Iterable[str] = ('name', 'url', 'crs', 'credentials')):
        super().__init__(name=name,
                         url=url,
                         source_type=SourceType.quadkey,
                         crs=crs,
                         credentials=credentials,
                         editable_fields=editable_fields)