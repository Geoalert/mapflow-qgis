from typing import List
from .factory import create_provider, create_provider_old
from .provider import Provider
from .default import SentinelProvider, MaxarVividProxyProvider, MaxarSecureWatchProxyProvider, MapboxProvider
from ...constants import PROVIDERS_KEY, LEGACY_PROVIDERS_KEY, LEGACY_PROVIDER_LOGIN_KEY, LEGACY_PROVIDER_PASSWORD_KEY

import json


def decorate(base_name, existing_names):
    """
    Transform `name` -> `name (i)` with first non-occupied i
    """
    i = 1
    name = base_name + f' ({i})'
    while name in existing_names:
        name = base_name + f' ({i})'
        i += 1
    return name


class ProvidersDict(dict):

    @classmethod
    def from_list(cls, providers: List[Provider]):
        return cls({p.name: p for p in providers})

    @classmethod
    def create_default_providers(cls, server):
        return cls.from_list([MapboxProvider(),
                              MaxarVividProxyProvider(proxy=server),
                              MaxarSecureWatchProxyProvider(proxy=server),
                              SentinelProvider(proxy=server)])

    @classmethod
    def from_settings(cls, settings, server):
        errors = []
        providers = ProvidersDict.create_default_providers(server=server)
        providers_settings = json.loads(settings.value(PROVIDERS_KEY, "{}"))
        if providers_settings:
            for name, params in providers_settings.items():
                if name in providers.keys():
                    name = decorate(name, providers.keys())
                    params["name"] = name
                try:
                    providers.update({name: create_provider(**params)})
                except Exception as e:
                    errors.append(name)
        # Importing providers from old plugin settings
        old_login = settings.value(LEGACY_PROVIDER_LOGIN_KEY, "")
        old_password = settings.value(LEGACY_PROVIDER_PASSWORD_KEY, "")
        old_providers = settings.value(LEGACY_PROVIDERS_KEY, {})
        for name, params in old_providers.items():
            if any(key not in params.keys() for key in ('type', 'url')):
                # settings are not understandable
                errors.append(name)
            provider = create_provider_old(name=name,
                                           source_type=params.get("type"),
                                           url=params.get("url"),
                                           login=old_login,
                                           password=old_password,
                                           connect_id=params.get("connectId", ""))
            if not provider:
                # this means that the provider should not be added
                continue
            if name in providers.keys():
                name = decorate(name, providers.keys())
                provider.name = name
            providers.update({name: provider})
        # clear old providers so that they will not be loaded again
        settings.remove(LEGACY_PROVIDERS_KEY)
        settings.remove(LEGACY_PROVIDER_PASSWORD_KEY)
        settings.remove(LEGACY_PROVIDER_LOGIN_KEY)

        return providers, errors

    def dict(self):
        return {name: provider.to_dict() for name, provider in self.items()}

    @property
    def default_providers(self):
        return ProvidersDict({k: v for k, v in self.items() if v.is_default})

    @property
    def users_providers(self):
        return ProvidersDict({k: v for k, v in self.items() if not v.is_default})

    def to_settings(self, settings):
        users_providers = self.users_providers.dict()
        settings.setValue(PROVIDERS_KEY, json.dumps(users_providers))
