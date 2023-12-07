from qgis.core import QgsApplication, QgsAuthMethodConfig

def get_auth_id(config_name):
    auth_manager = QgsApplication.authManager()
    for config_id in auth_manager.configIds():
        auth_config = QgsAuthMethodConfig()
        auth_manager.loadAuthenticationConfig(config_id, auth_config)
        if auth_config.name() == config_name:
            return config_id
    return None
