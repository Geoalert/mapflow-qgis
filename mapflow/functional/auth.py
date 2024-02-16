from qgis.core import QgsApplication, QgsAuthMethodConfig

def get_auth_id(auth_config_name, auth_config_map):
    """
    Returns Tuple (config_id, reload)
    If reload is True, QGIS restart is required
    """
    auth_manager = QgsApplication.authManager()
    for config_id in auth_manager.configIds():
        auth_config = QgsAuthMethodConfig()
        auth_manager.loadAuthenticationConfig(config_id, auth_config)
        if auth_config.name() == auth_config_name:
            return config_id, False
    return setup_auth_config(auth_config_name, auth_config_map), True

def setup_auth_config(auth_config_name, auth_config_map):
    auth_manager = QgsApplication.authManager()
    config = QgsAuthMethodConfig()
    config.setName(auth_config_name)
    config.setMethod("OAuth2")
    config.setConfig('oauth2config', auth_config_map)
    if config.isValid():
        auth_manager.storeAuthenticationConfig(config)
        config_id = config.id()
        new_config = QgsAuthMethodConfig()
        auth_manager.loadAuthenticationConfig(config_id, new_config, full=True)
        return config_id
    else:
        return None

