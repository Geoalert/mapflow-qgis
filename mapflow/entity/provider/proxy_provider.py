from abc import ABC
from typing import Union, Iterable
from provider import Provider, CRS, SourceType

SERVER = "https://api.mapflow.ai/rest/"


class ProxyProvider(Provider, ABC):
    """
    Abstract class
    Provider which is proxied via our server
    It does not have 'URL' because it uses system-wide url and our API
    Currently it does have subclasses because of different API, but in the future it will be unified
    """
    def __init__(self,
                 name: str,
                 source_type: Union[SourceType, str],
                 **kwargs):
        super().__init__(name=name,
                         url=SERVER,
                         source_type=source_type,
                         editable_fields=())

    def to_processing_params(self):
        params = {
            'url': self.url,
            'source_type': self.source_type
        }
        return params


class SentinelProvider(ProxyProvider):
    def __init__(self,
                 **kwargs):
        name = 'Sentinel-2'
        super().__init__(name=name, source_type=SourceType.sentinel_l2a)

    @property
    def requires_image_id(self):
        return True

    def search_request(self):
        return {}


class MaxarProxyProvider(ProxyProvider, ABC):
    # Abstract class
    def __init__(self, name: str,
                 **kwargs):
        super().__init__(name=name, source_type=SourceType.xyz)


class MaxarVividProxyProvider(MaxarProxyProvider):
    def __init__(self,
                 **kwargs):
        super().__init__(name="Maxar Vivid",
                         **kwargs)

    @property
    def requires_image_id(self):
        return False


class MaxarSecureWatchProxyProvider(MaxarProxyProvider):
    def __init__(self,
                 **kwargs):
        super().__init__(name="Maxar SecureWatch",
                 **kwargs)
    @property
    def requires_image_id(self):
        return True

    def search_request(self):
        return {}
