"""
Basic, non-authentification XYZ provider
"""
from typing import Union, Iterable
from .provider import SourceType, CRS, Provider, BasicAuth


class BasemapProvider(Provider):
    def __init__(self,
                 name: str,
                 url: str,
                 source_type: Union[SourceType, str],
                 crs: [Union[CRS, str]] = CRS.web_mercator,
                 credentials: BasicAuth = BasicAuth(),
                 editable_fields: Iterable[str] = ('name', 'url', 'source_type', 'crs', 'credentials')):
        super().__init__(name=name,
                         url=url,
                         source_type=source_type,
                         crs=crs,
                         is_default=False,
                         credentials=credentials,
                         editable_fields=editable_fields)
        # default value is Web Mercator
        self.credentials = credentials

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

    @property
    def is_proxy(self):
        return False

    @property
    def is_default(self):
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


class MapboxProvider(XYZProvider):
    def __init__(self):
        super().__init__(name="Mapbox",
                         url="https://api.tiles.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.jpg?access_token="
                             "pk.eyJ1Ijoib3BlbnN0cmVldG1hcCIsImEiOiJja2w5YWt5bnYwNjZmMnFwZjhtbHk1MnA1In0.eq2aumBK6JuRoIuBMm6Gew",
                         crs=CRS.web_mercator)

    @property
    def is_default(self):
        return True