import json
from abc import ABC
from typing import Union
from .provider import Provider, SourceType, staticproperty
from ...schema.processing import PostSourceSchema
from ...constants import MAXAR_BASE_URL
from ...functional.layer_utils import add_image_id, add_connect_id, maxar_tile_url
from ...requests.maxar_metadata_request import MAXAR_REQUEST_BODY, MAXAR_META_URL
from ...errors.plugin_errors import ImageIdRequired


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
                 proxy: str,
                 **kwargs):
        super().__init__(name=name,
                         source_type=source_type,
                         is_default=False,
                         **kwargs)
        self.proxy = proxy

    def to_processing_params(self, image_id=None):
        return PostSourceSchema(url=self.url,
                                source_type=self.source_type.value), {}

    @property
    def is_proxy(self):
        return True

    @property
    def is_default(self):
        return True

    @staticproperty
    def option_name():
        return None


class MaxarProxyProvider(ProxyProvider, ABC):
    # Abstract class
    def __init__(self,
                 name: str,
                 proxy: str,
                 **kwargs):
        super().__init__(name=name,
                         source_type=SourceType.xyz,
                         proxy=proxy,
                         url=maxar_tile_url(MAXAR_BASE_URL),
                         **kwargs)

    @property
    def connect_id(self):
        raise NotImplementedError

    def preview_url(self, image_id=None):
        if self.requires_image_id and not image_id:
            raise ImageIdRequired("Preview for {name} is unavailable without image ID!".format(name=self.name))
        url = add_connect_id(f'{self.proxy}/png?TileRow={{y}}&TileCol={{x}}&TileMatrix={{z}}', self.connect_id)
        return add_image_id(url, image_id)

    def proxy_maxar_url(server, image_id):
        """
        When we process a particular image, we use SecureWatch, otherwise - Vivid.
        The name of the service is passed as CONNECTID to our proxy server
        """
        url = f'{server}/png?TileRow={{y}}&TileCol={{x}}&TileMatrix={{z}}' + '&CONNECTID='
        if image_id:
            return add_image_id(url + 'securewatch', image_id)
        else:
            return url + 'vivid'

    def to_processing_params(self, image_id=None):
        if self.requires_image_id and not image_id:
            raise ImageIdRequired("Cannot start processing without image ID!")
        params = PostSourceSchema(url=add_image_id(self.url, image_id),
                                  source_type=self.source_type.value,
                                  crs=self.crs.value)
        meta = {'source': 'maxar',
                'maxar_product': self.connect_id}
        return params, meta

    @property
    def meta_url(self):
        return self.proxy + "/meta"

    def meta_request(self, from_, to, max_cloud_cover, geometry):
        body = json.dumps({
                    'url': MAXAR_META_URL,
                    'body': MAXAR_REQUEST_BODY.format(from_=from_,
                                                      to=to,
                                                      max_cloud_cover=max_cloud_cover,
                                                      geometry=geometry),
                    'connectId': self.connect_id
                }).encode()
        return body

    @property
    def is_payed(self):
        return True
