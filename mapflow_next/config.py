"""Static configuration: environments, URLs, timings. Nothing here touches QGIS state at import time."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PLUGIN_NAME = "Mapflow Next"
PLUGIN_SHORT_NAME = "Mapflow"      # toolbar, message bar
PLUGIN_DIR = Path(__file__).parent
RESOURCES = PLUGIN_DIR / "resources"
SETTINGS_GROUP = "mapflow_next"
LAYER_GROUP_NAME = "Mapflow"
# Custom property set on every layer the plugin adds, so a processing's layers can be found again
PROCESSING_PROPERTY = "mapflow_next/processing_id"
# Set on an imagery preview layer: which source it shows ("mosaic:<id>", "provider:<name>", "catalog:<id>")
PREVIEW_PROPERTY = "mapflow_next/preview"

WEB_URL = "https://app.mapflow.ai"
# Mapflow Web of each environment (mapflow_env). One not listed here opens production's, unless the
# `mapflow_next/web_url` setting says where it is.
WEB_URLS = {"production": WEB_URL}
MY_DATA_PATH = "/my-data"          # My imagery collections in Mapflow Web
TOP_UP_URL = f"{WEB_URL}/account/balance"
API_TOKEN_URL = f"{WEB_URL}/account/api"
SIGN_UP_URL = WEB_URL
PROJECTS_URL = f"{WEB_URL}/en/projects"    # sharing happens here (project card ⋯ → Share)
TEAM_URL = f"{WEB_URL}/en/team"            # to verify: the docs name the Team page but not its address
DOCS_URL = "https://docs.mapflow.ai/api/qgis_mapflow.html"
MODELS_DOCS_URL = "https://docs.mapflow.ai/userguides/pipelines.html"
CUSTOM_MODELS_URL = "https://mapflow.ai/custom-models"
RELEASES_URL = "https://github.com/Geoalert/mapflow-qgis/releases"

POLL_INTERVAL_MS = 6_000          # processings list while something runs
STATUS_INTERVAL_MS = 30_000       # balance and limits
COST_DEBOUNCE_MS = 400            # wait for the form to settle before asking /cost
TIMEOUT_S = 30
RESULT_TIMEOUT_S = 600
PROCESSINGS_PAGE_SIZE = 30
PROJECTS_PAGE_SIZE = 50
SEARCH_PAGE_SIZE = 50
MIN_BILLED_AREA_KM2 = 1.0         # areas under 1 km² are billed as 1 km²

# Browser sign-in: Mapflow's public OAuth2 client for QGIS (the one the current plugin uses).
# The client accepts one redirect address, so the plugin listens there for the sign-in code and
# then sends the browser on to Mapflow Web.
_AUTH_REALMS = {
    "production": ("auth.mapflow.ai", "mapflow"),
    "staging": ("auth.mapflow.ai", "mapflow-staging"),
    "internal": ("auth.mapflow.ai", "mapflow-internal"),
    "duty": ("auth-duty.mapflow.ai", "mapflow-duty"),
}
OAUTH_CLIENT_ID = "qgis"
OAUTH_SCOPE = ""                  # as in the current plugin
REDIRECT_PORT = 7070
REDIRECT_PATH = "/qgis"           # → http://127.0.0.1:7070/qgis
SIGNED_IN_URL = WEB_URL           # where the browser lands once QGIS has the sign-in code
SIGN_IN_TIMEOUT_S = 300           # how long to wait for the browser


def auth_url_for(env: str) -> str:
    host, realm = _AUTH_REALMS.get(env, _AUTH_REALMS["production"])
    return f"https://{host}/auth/realms/{realm}/protocol/openid-connect"


@dataclass(frozen=True)
class Config:
    env: str
    server: str
    auth_url: str = ""            # OpenID Connect base; empty means the environment's default
    web: str = ""                 # Mapflow Web; empty means the environment's default

    @property
    def web_url(self) -> str:
        return (self.web or WEB_URLS.get(self.env, WEB_URL)).rstrip("/")

    @property
    def my_data_url(self) -> str:
        return f"{self.web_url}{MY_DATA_PATH}"

    @property
    def oidc(self) -> str:
        return (self.auth_url or auth_url_for(self.env)).rstrip("/")

    @property
    def authorize_url(self) -> str:
        return f"{self.oidc}/auth"

    @property
    def token_url(self) -> str:
        return f"{self.oidc}/token"

    @property
    def redirect_uri(self) -> str:
        return f"http://127.0.0.1:{REDIRECT_PORT}{REDIRECT_PATH}"

    @property
    def token_config_name(self) -> str:
        return f"mapflow_next_token_{self.env}"

    @property
    def refresh_token_key(self) -> str:
        """Encrypted entry in the QGIS authentication database that keeps the browser sign-in."""
        return f"mapflow_next/{self.env}/refresh_token"


def load_config(settings=None) -> Config:
    """Environment from the QGIS global variable `mapflow_env` (as in the current plugin).
    `mapflow_next/server`, `mapflow_next/auth_url` and `mapflow_next/web_url` override the API, sign-in
    and Mapflow Web addresses for testing against a local or staging server."""
    if settings is None:
        from qgis.core import QgsSettings
        settings = QgsSettings()
    env = (settings.value("variables/mapflow_env", "") or "production").strip().lower()
    override = settings.value(f"{SETTINGS_GROUP}/server", "") or ""
    server = override.rstrip("/") or f"https://whitemaps-{env}.mapflow.ai/rest"
    return Config(env=env, server=server, auth_url=settings.value(f"{SETTINGS_GROUP}/auth_url", "") or "",
                  web=settings.value(f"{SETTINGS_GROUP}/web_url", "") or "")
