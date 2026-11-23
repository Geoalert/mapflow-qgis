from qgis.core import QgsApplication, QgsAuthMethodConfig

from ..domain import DEFAULT_DOMAIN, RU_DOMAIN, text_with_domain

OAUTH2_CONFIG_KEY = 'oauth2config'


def get_auth_id(auth_config_name, auth_config_map, domain=DEFAULT_DOMAIN):
    """
    Returns Tuple (config_id, reload)
    If reload is True, QGIS restart is required

    `domain` is the domain in use. A stored configuration keeps its name and its id for both domains, so
    the addresses of the domain in use are written into it when it has the addresses of the other one.
    """
    auth_manager = QgsApplication.authManager()
    for config_id in auth_manager.configIds():
        auth_config = QgsAuthMethodConfig()
        auth_manager.loadAuthenticationConfig(config_id, auth_config)
        if auth_config.name() == auth_config_name:
            sync_auth_config_domain(config_id, domain)
            return config_id, False
    return setup_auth_config(auth_config_name, auth_config_map), True


def config_text_on_domain(text, domain):
    """The text of a sign-in configuration with every Mapflow address on `domain`, whichever of the two
    domains its addresses have now."""
    for other in (DEFAULT_DOMAIN, RU_DOMAIN):
        if other != domain:
            text = text_with_domain(text, domain, other)
    return text


def sync_auth_config_domain(config_id, domain) -> bool:
    """Write the addresses of `domain` into the stored sign-in configuration `config_id` when it has the
    addresses of the other domain. Returns True when the configuration was changed."""
    auth_manager = QgsApplication.authManager()
    auth_config = QgsAuthMethodConfig()
    if not auth_manager.loadAuthenticationConfig(config_id, auth_config, True):
        return False
    stored = auth_config.config(OAUTH2_CONFIG_KEY)
    wanted = config_text_on_domain(stored, domain)
    if not stored or wanted == stored:
        return False
    auth_config.setConfig(OAUTH2_CONFIG_KEY, wanted)
    if not auth_manager.updateAuthenticationConfig(auth_config):
        return False
    # The OAuth2 method keeps the addresses of a configuration that it has used: make it read them again
    auth_manager.clearCachedConfig(config_id)
    return True


def setup_auth_config(auth_config_name, auth_config_map):
    auth_manager = QgsApplication.authManager()
    config = QgsAuthMethodConfig()
    config.setName(auth_config_name)
    config.setMethod("OAuth2")
    config.setConfig(OAUTH2_CONFIG_KEY, auth_config_map)
    if config.isValid():
        auth_manager.storeAuthenticationConfig(config)
        config_id = config.id()
        new_config = QgsAuthMethodConfig()
        auth_manager.loadAuthenticationConfig(config_id, new_config, full=True)
        return config_id
    else:
        return None
