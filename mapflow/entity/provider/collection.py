import json

from .factory import create_provider, create_provider_old
from .provider import NoneProvider
from ...constants import PROVIDERS_KEY


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


class ProvidersList(list):

    @classmethod
    def from_dict(cls, providers_dict):
        return ProvidersList(providers_dict.values())

    @classmethod
    def from_settings(cls, settings):
        errors = []
        providers = {}
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
        return cls.from_dict(providers), errors

    def dict(self):
        return {provider.name: provider.to_dict() for provider in self}

    @property
    def default_providers(self):
        return ProvidersList([provider for provider in self if provider.is_default])

    @property
    def users_providers(self):
        return ProvidersList([provider for provider in self if not provider.is_default])

    def to_settings(self, settings):
        users_providers = self.users_providers.dict()
        settings.setValue(PROVIDERS_KEY, json.dumps(users_providers))

    def __getitem__(self, i):
        if i < 0:
            return NoneProvider()
        else:
            return super().__getitem__(i)
