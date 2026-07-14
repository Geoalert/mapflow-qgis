from .basemap_provider import XYZProvider, TMSProvider, QuadkeyProvider

provider_options = {XYZProvider.option_name: XYZProvider,
                    TMSProvider.option_name: TMSProvider,
                    QuadkeyProvider.option_name: QuadkeyProvider}


def create_provider(option_name,
                    **kwargs):
    provider = provider_options[option_name]
    return provider(**kwargs)


def create_provider_old(name, source_type, url, login, password, connect_id):
    """
    Load the list of the providers saved in old format, to not remove old user's providers
    """
    if source_type == 'xyz':
        return XYZProvider(name=name, url=url)
    elif source_type == 'tms':
        return TMSProvider(name=name, url=url)
    elif source_type == "quadkey":
        return QuadkeyProvider(name=name, url=url)
    else:
        return None
