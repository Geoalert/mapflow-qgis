from .provider import Provider, SourceType, CRS, PROVIDERS_KEY
from .factory import create_provider, create_provider_old


class ProvidersDict(dict):
    @classmethod
    def default_providers(cls):
        {create_provider(**kwargs)}

    @classmethod
    def from_settings(cls, settings):
        providers_settings = settings.value(PROVIDERS_KEY, None)
        if not providers_settings:
            return ProvidersDict.default_providers()
        dict_ = {name: Provider.from_params(params, name) for name, params in providers_settings.items()}
        return cls(dict_)

    def dict(self):
        return {name: provider.to_dict() for name, provider in self.items()}

    def to_settings(self, settings):
        settings.setValue(PROVIDERS_KEY, self.dict())
