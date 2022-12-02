import json
from abc import ABC
from typing import Union, Iterable
from .provider import Provider, CRS, SourceType
from ...config import SERVER, SENTINEL_OPTION_NAME
from ...requests.maxar_metadata_request import MAXAR_REQUEST_BODY
from ...layer_utils import add_image_id


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
                         url=SERVER.format(env='production'),
                         source_type=source_type,
                         editable_fields=(),
                         is_default=False)

    def to_processing_params(self):
        params = {
            'url': self.url,
            'source_type': self.source_type
        }
        return params

    @property
    def is_proxy(self):
        return True

    @property
    def is_default(self):
        return True


class SentinelProvider(ProxyProvider):
    def __init__(self,
                 **kwargs):
        name = SENTINEL_OPTION_NAME
        super().__init__(name=name, source_type=SourceType.sentinel_l2a)

    @property
    def requires_image_id(self):
        return True

    def to_processing_params(self, image_id):
        return{'url': image_id,
               'source_type': self.source_type}


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

    def to_processing_params(self, image_id=None):
        return{'url': self.url,
               'connectid': 'vivid',
               'source_type': self.source_type,
               'crs': self.crs.value}


class MaxarSecureWatchProxyProvider(MaxarProxyProvider):
    def __init__(self,
                 **kwargs):
        super().__init__(name="Maxar SecureWatch",
                 **kwargs)

    @property
    def requires_image_id(self):
        return True

    @property
    def meta_url(self):
        return self.url + "/meta"

    @property
    def meta_request(self):
        return json.dumps({
            'url': "",
            'body': MAXAR_REQUEST_BODY,
            'connectId': 'securewatch'
        }).encode()

    def to_processing_params(self, image_id=None):
        if not image_id:
            raise ValueError("SecureWatch requires image id")
        return{'url': add_image_id(self.url, image_id),
               'connectid': 'securewatch',
               'source_type': self.source_type,
               'crs': self.crs.value}