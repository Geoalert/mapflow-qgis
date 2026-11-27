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
FILES, TILES = "file", "tiles"        # how results arrive: GeoPackage files or vector tiles (Settings, Results)
# Custom property set on every layer the plugin adds, so a processing's layers can be found again
PROCESSING_PROPERTY = "mapflow_next/processing_id"
# Set on an imagery preview layer: which source it shows ("mosaic:<id>", "provider:<name>", "catalog:<id>")
PREVIEW_PROPERTY = "mapflow_next/preview"

# The default domain of every Mapflow address, and the one the QGIS variable `mapflow_ru` switches to. These are the
# only places in the plugin code with an address of either: every link comes from `Config.links`.
DOMAIN = "mapflow.ai"
RU_DOMAIN = "mapflow.ru"
# Host prefix of Mapflow Web in each environment (mapflow_env). One not listed here opens production's, unless
# the `mapflow_next/web_url` setting says where it is.
WEB_PREFIXES = {"production": "app", "duty": "duty"}
MY_DATA_PATH = "/my-data"          # My imagery collections in Mapflow Web
MOSAICS_REFRESH_MS = 30_000        # My imagery collections, asked for again while the panel is open
STORAGE_REFRESH_MS = 20_000        # storage usage while My imagery is visible
SUPPORT_EMAIL = "help@geoalert.io"
RELEASES_URL = "https://github.com/Geoalert/mapflow-qgis/releases"

POLL_INTERVAL_MS = 6_000          # processings list while something runs
# Failures of a timer's request in a row before the user is told, once. A first guess: live use moves it.
POLL_FAILURES_BEFORE_ALERT = 3
STATUS_INTERVAL_MS = 5_000        # balance and limits, while the Mapflow panel is open
STATUS_IDLE_INTERVAL_MS = 60_000  # …and while it is closed
COST_DEBOUNCE_MS = 400            # wait for the form to settle before asking /cost
PROCESSINGS_SEARCH_DEBOUNCE_MS = 400   # wait for typing to pause before the search goes to the server
TIMEOUT_S = 30
RESULT_TIMEOUT_S = 600
# An upload may be silent for an hour: the timer restarts while bytes move, so a slow, healthy one is not cut
UPLOAD_TIMEOUT_S = 3600
# …and so may the download of an original image: seconds of silence, restarted whenever bytes arrive, so a
# download of several GB is not cut while it moves and only a stalled one ends
IMAGE_DOWNLOAD_TIMEOUT_S = 3600
# What an upload may be when Mapflow's answer (GET rasters/memory) is missing; the account's own limits replace them
UPLOAD_LIMIT_BYTES = 2 * 1024 ** 3
MAX_SIDE_PIXELS = 30_000
PROCESSINGS_PAGE_SIZE = 30
PROJECTS_PAGE_SIZE = 50
SEARCH_PAGE_SIZE = 50
MOSAICS_PAGE_SIZE = 50              # My imagery collections listed at a time ("Show more" for the next)
MIN_BILLED_AREA_KM2 = 1.0         # areas under 1 km² are billed as 1 km²

# Browser sign-in: Mapflow's public OAuth2 client for QGIS (the one the current plugin uses).
# The client accepts one redirect address, so the plugin listens there for the sign-in code and
# then sends the browser on to Mapflow Web.
_AUTH_REALMS = {
    "production": ("auth", "mapflow"),
    "staging": ("auth-staging", "mapflow-staging"),
    "internal": ("auth-internal", "mapflow-internal"),
    "duty": ("auth-duty", "mapflow-duty"),
}
OAUTH_CLIENT_ID = "qgis"
OAUTH_SCOPE = ""                  # as in the current plugin
REDIRECT_PORT = 7070
REDIRECT_PATH = "/qgis"           # → http://127.0.0.1:7070/qgis
SIGN_IN_TIMEOUT_S = 300           # how long to wait for the browser


def auth_url_for(env: str, domain: str = DOMAIN) -> str:
    prefix, realm = _AUTH_REALMS.get(env, _AUTH_REALMS["production"])
    return f"https://{prefix}.{domain}/auth/realms/{realm}/protocol/openid-connect"


@dataclass(frozen=True)
class Links:
    """Every Mapflow address that the plugin shows or opens, for one domain."""
    web: str
    my_data: str
    top_up: str
    ai_agent: str
    api_token: str
    sign_up: str
    projects: str                 # sharing happens here (project card ⋯ → Share)
    team: str                     # to verify: the docs name the Team page but not its address
    pricing: str
    docs: str
    terms: str
    models_docs: str
    custom_models: str

    @classmethod
    def of(cls, domain: str = DOMAIN) -> "Links":
        web = f"https://app.{domain}"
        return cls(web=web, my_data=f"{web}{MY_DATA_PATH}", top_up=f"{web}/account/balance",
                   ai_agent=f"{web}/#home-top", api_token=f"{web}/account/api", sign_up=web,
                   projects=f"{web}/en/projects", team=f"{web}/en/team", pricing=f"https://{domain}/pricing",
                   docs=f"https://docs.{domain}/api/qgis_mapflow.html",
                   terms=f"https://{domain}/terms-of-use-en.pdf",
                   models_docs=f"https://docs.{domain}/userguides/pipelines.html",
                   custom_models=f"https://{domain}/custom-models")


@dataclass(frozen=True)
class Config:
    env: str
    server: str
    auth_url: str = ""            # OpenID Connect base; empty means the environment's default
    web: str = ""                 # Mapflow Web; empty means the environment's default
    domain: str = DOMAIN          # RU_DOMAIN when the QGIS variable `mapflow_ru` is true

    @property
    def links(self) -> Links:
        return Links.of(self.domain)

    @property
    def web_url(self) -> str:
        prefix = WEB_PREFIXES.get(self.env, WEB_PREFIXES["production"])
        return (self.web or f"https://{prefix}.{self.domain}").rstrip("/")

    @property
    def signed_in_url(self) -> str:
        """Where the browser lands once QGIS has the sign-in code."""
        return self.links.web

    @property
    def my_data_url(self) -> str:
        return f"{self.web_url}{MY_DATA_PATH}"

    @property
    def oidc(self) -> str:
        return (self.auth_url or auth_url_for(self.env, self.domain)).rstrip("/")

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
    The global variable `mapflow_ru`, `true` in any case, switches every address to the domain `mapflow.ru`;
    any other value, or none, keeps `mapflow.ai`.
    `mapflow_next/server`, `mapflow_next/auth_url` and `mapflow_next/web_url` override the API, sign-in
    and Mapflow Web addresses for testing against a local or staging server; they are used as written."""
    if settings is None:
        from qgis.core import QgsSettings
        settings = QgsSettings()
    env = (settings.value("variables/mapflow_env", "") or "production").strip().lower()
    on = str(settings.value("variables/mapflow_ru", "") or "").strip().lower() == "true"
    domain = RU_DOMAIN if on else DOMAIN
    override = settings.value(f"{SETTINGS_GROUP}/server", "") or ""
    server = override.rstrip("/") or f"https://whitemaps-{env}.{domain}/rest"
    return Config(env=env, server=server, auth_url=settings.value(f"{SETTINGS_GROUP}/auth_url", "") or "",
                  web=settings.value(f"{SETTINGS_GROUP}/web_url", "") or "", domain=domain)
