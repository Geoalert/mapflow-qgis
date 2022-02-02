from abc import ABC, abstractmethod

from mapflow import regex


class Provider(ABC):
    """An abstract base class for imagery providers."""

    @abstractmethod
    def __init__(self):
        self.url_regex = regex.URL

    @property
    @abstractmethod
    def metadata_url(self):
        return self._metadata_url

    @metadata_url.setter
    @abstractmethod
    def metadata_url(self, url: str):
        self._metadata_url = url

    @abstractmethod
    def get_metadata(self):
        pass

    # @abstractmethod
    # def preview(self):
    #     pass
