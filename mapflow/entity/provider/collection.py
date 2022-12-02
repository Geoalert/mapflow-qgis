from typing import List
from .provider import Provider, SourceType, CRS, PROVIDERS_KEY
from .proxy_provider import SentinelProvider, MaxarVividProxyProvider, MaxarSecureWatchProxyProvider
from .xyz_provider import MapboxProvider
from .factory import create_provider, create_provider_old
import logging


class ProvidersDict(dict):

    @classmethod
    def from_list(cls, providers: List[Provider]):
        return cls({p.name: p for p in providers})

    @classmethod
    def create_default_providers(cls):
        return cls.from_list([MapboxProvider(),
                              MaxarVividProxyProvider(),
                              MaxarSecureWatchProxyProvider(),
                              SentinelProvider()])

    @classmethod
    def from_settings(cls, settings):
        logging.debug("Creating default providers")
        providers = ProvidersDict.create_default_providers()
        logging.debug(f"Default: {list(providers.keys())}")
        providers_settings = settings.value(PROVIDERS_KEY, None)
        logging.debug(f"Settings: {providers_settings}")
        if providers_settings:
            dict_ = {name: Provider.from_params(params, name) for name, params in providers_settings.items()
                     if name not in providers}  # we don not allow to replace default providers
            providers.update(cls(dict_))
        logging.debug(f"All providers: {list(providers.keys())}")
        return providers

    def dict(self):
        return {name: provider.to_dict() for name, provider in self.items()}

    @property
    def default_providers(self):
        return ProvidersDict({k: v for k, v in self.items() if v.is_default})

    @property
    def users_providers(self):
        return ProvidersDict({k: v for k, v in self.items() if not v.is_default})

    def to_settings(self, settings):
        settings.setValue(PROVIDERS_KEY, self.users_providers.dict())
