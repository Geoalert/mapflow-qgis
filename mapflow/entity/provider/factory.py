from .basemap_provider import XYZProvider, TMSProvider, QuadkeyProvider, MaxarProvider
from ...constants import MAXAR_BASE_URL
from ...functional.layer_utils import add_connect_id

provider_options = {XYZProvider.option_name: XYZProvider,
                    TMSProvider.option_name: TMSProvider,
                    QuadkeyProvider.option_name: QuadkeyProvider,
                    MaxarProvider.option_name: MaxarProvider}


def create_provider(option_name,
                    **kwargs):
    provider = provider_options[option_name]
    return provider(**kwargs)


def create_provider_old(name, source_type, url, login, password, connect_id):
    """
    Load the list of the providers saved in old format, to not remove old user's providers
    """
    # connectid, login and password are only for maxar providers with user's own credentials

    if "securewatch" in name.lower() or "vivid" in name.lower() or "basemaps" in name.lower():
        if bool(connect_id):
            return MaxarProvider(name=name,
                                 url=add_connect_id(MAXAR_BASE_URL, connect_id),
                                 credentials=(login, password),
                                 save_credentials=bool(login) and bool(password))
        else:
            # this means default provider Maxar SecureWatch which now is not saved in settings
            return None
    elif "sentinel" in name.lower():
        # Sentinel provider is a default one and is not allowed for adding
        return None
    else:  # not proxied XYZ provider
        if source_type == 'xyz':
            return XYZProvider(name=name, url=url)
        elif source_type == 'tms':
            return TMSProvider(name=name, url=url)
        elif source_type == "quadkey":
            return QuadkeyProvider(name=name, url=url)
        else:
            return None
