import json
import os
from abc import ABC
from typing import Iterable, Union, Optional
from pathlib import Path

from ...schema.provider_types import SourceType, CRS, BasicAuth


class staticproperty(staticmethod):
    def __get__(self, *_):
        return self.__func__()


class ProviderInterface:
    def __init__(self,
                 name: str):
        self.name = name

    @property
    def preview_max_zoom(self):
        return None

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
                             provider_name: Optional[str] = None,
                             zoom: Optional[str] = None):
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
    """Stands in for "no provider selected" — see ProvidersList.__getitem__.

    Answers the questions the UI asks while deciding what to enable, instead of inheriting
    the NotImplementedError versions: it is handed out precisely when the combo has no
    selection, so a caller reaching it is on a normal path, not a broken one.

    to_processing_params is deliberately left raising. Nothing can be processed without a
    real source, and turning that into a silent default would submit a job against the wrong
    imagery.
    """

    def __init__(self):
        super().__init__(name="")

    def __bool__(self):
        return False

    @property
    def is_default(self):
        return False

    @property
    def requires_image_id(self):
        return False

    @property
    def meta_url(self):
        return None

    def preview_url(self, image_id=None):
        return None
