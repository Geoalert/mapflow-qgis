import json
import os
from abc import ABC
from enum import Enum
from typing import Iterable, Union, Optional
from pathlib import Path


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


class ProviderInterface:
    def __init__(self,
                 name: str):
        self.name = name

    @property
    def is_default(self):
        raise NotImplementedError

    @property
    def requires_image_id(self):
        raise NotImplementedError

    @property
    def meta_url(self):
        raise NotImplementedError

    @property
    def is_payed(self):
        return False

    def preview_url(self, image_id=None):
        raise NotImplementedError

    def to_processing_params(self,
                             image_id: Optional[str] = None,
                             provider_name: Optional[str] = None,
                             url: Optional[str] = None,
                             zoom: Optional[str] = None,
                             requires_id: Optional[bool] = False):
        """ You cannot create a processing with generic provider without implementation"""
        raise NotImplementedError

    @property
    def metadata_layer_name(self):
        if not self.meta_url:
            return None
        else:
            return f"{self.name} imagery search"

    def save_search_layer(self, folder, data: dict) -> Optional[str]:
        """
        saves to file (a single file specific to the provider) in specified folder, to be loaded later;
        """
        if not self.metadata_layer_name or not data:
            return
        with open(Path(folder, self.metadata_layer_name), 'w') as saved_results:
            saved_results.write(json.dumps(data))
        return str(Path(folder, self.metadata_layer_name))

    def load_search_layer(self, folder) -> Optional[dict]:
        """
        loads geometries as geojson dict
        Returns nothing if the provider does not support metadata search, or if the file does not exist
        """
        if not self.metadata_layer_name or not folder:
            return None
        try:
            with open(os.path.join(folder, self.metadata_layer_name), 'r') as saved_results:
                return json.load(saved_results)
        except FileNotFoundError:
            return None

    def clear_saved_search(self, folder) -> None:
        if not self.metadata_layer_name or not folder:
            return
        try:
            os.remove(os.path.join(folder, self.metadata_layer_name))
        except OSError:
            pass


class UsersProvider(ProviderInterface, ABC):
    def __init__(self,
                 name: str,
                 url: str,
                 source_type: Union[SourceType, str] = SourceType.xyz,
                 crs: Optional[Union[CRS, str]] = CRS.web_mercator,
                 credentials: Union[BasicAuth, Iterable[str]] = BasicAuth(),
                 save_credentials: bool = False,
                 **kwargs):
        super().__init__(name=name)
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
        """
        Used to save it to the settinigs
        """
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

    @staticproperty
    def option_name():
        """
        Used to display the provider type in the interface
        """
        raise NotImplementedError


class NoneProvider(ProviderInterface):
    def __init__(self):
        super().__init__(name="")

    def __bool__(self):
        return False
