from xyz_provider import XYZProvider, TMSProvider, QuadkeyProvider
from proxy_provider import SentinelProvider, MaxarVividProxyProvider, MaxarSecureWatchProxyProvider


def create_provider(provider_class,
                    **kwargs):

    providers = {
        "xyz": XYZProvider,
        "tms": TMSProvider,
        "quadkey": QuadkeyProvider,
        "sentinel": SentinelProvider,
        "proxy_vivid": MaxarVividProxyProvider,
        "proxy_securewatch": MaxarSecureWatchProxyProvider
    }
    provider = providers[provider_class]
    return provider(**kwargs)


def create_provider_old(name,
                             url,
                             source_type,
                             credentials,
                             connect_id,
                             is_maxar: bool,
                             **kwargs):

    if source_type == "sentinel_l2a":
        return SentinelProvider()

    if "vivid" in name.lower() and is_maxar:
            return MaxarVividProxyProvider()
    elif "securewatch" in name.lower and is_maxar:
            return MaxarSecureWatchProxyProvider()
    else:  # not proxied XYZ provider
        if source_type == 'xyz':
            return XYZProvider(name=name, url=url, credentials=credentials)
        elif source_type == 'tms':
            return TMSProvider(name=name, url=url, credentials=credentials)
        elif source_type == "quadkey":
            return QuadkeyProvider(name=name, url=url, credentials=credentials)
