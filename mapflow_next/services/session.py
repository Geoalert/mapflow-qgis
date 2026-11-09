"""Who is signed in, their balance and limits, and the current project."""
from __future__ import annotations

import time
from typing import List, Optional

from qgis.PyQt.QtCore import QObject, QTimer, pyqtSignal

from ..api import auth
from ..api.client import MapflowApi
from ..api.http import ApiError, Http
from ..api.oauth import BrowserSignIn, refresh_tokens
from ..config import STATUS_INTERVAL_MS, Config
from ..core.models import Project, UserStatus
from ..core.oauth import Tokens

SIGNED_OUT, SIGNING_IN, SIGNED_IN = "signed_out", "signing_in", "signed_in"
BROWSER, TOKEN = "browser", "token"
_TRANSIENT = ("offline", "proxy", "timeout", "server")
RETRY_REFRESH_MS = 30_000


class Session(QObject):
    stateChanged = pyqtSignal(str)
    statusChanged = pyqtSignal(object)        # UserStatus
    projectsChanged = pyqtSignal(list)        # [Project]
    projectChanged = pyqtSignal(object)       # Project
    error = pyqtSignal(str)

    def __init__(self, config: Config, http: Http, api: MapflowApi, settings, parent=None):
        super().__init__(parent)
        self.config, self.http, self.api, self.settings = config, http, api, settings
        self.state = SIGNED_OUT
        self.method: Optional[str] = None
        self.email = ""
        self.status: Optional[UserStatus] = None
        self.projects: List[Project] = []
        self.project: Optional[Project] = None
        self.tokens: Optional[Tokens] = None
        self._silent = False
        self._refreshing = False
        self._forced_refresh_at = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(STATUS_INTERVAL_MS)
        self._timer.timeout.connect(self.refresh_status)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.refresh_sign_in)
        self.browser = BrowserSignIn(config, http, self)
        self.browser.succeeded.connect(self._on_tokens)
        self.browser.failed.connect(self._browser_failed)
        http.unauthorized.connect(self._on_unauthorized)

    # ---------- signing in and out ----------

    def restore(self) -> None:
        """Pick up the last sign-in quietly. Never opens the browser on its own."""
        method = self.settings.value("auth_method", "")
        if method == BROWSER:
            refresh = auth.load_refresh_token(self.config)
            if refresh:
                self.method, self._silent = BROWSER, True
                self._set_state(SIGNING_IN)
                self.tokens = Tokens("", refresh, 0, 0)
                self.refresh_sign_in()
                return
        elif method == TOKEN:
            config_id = self.settings.value("auth_config_id", "")
            if config_id and config_id in auth._manager().configIds():
                self._connect_token(config_id, silent=True)
                return
        self._set_state(SIGNED_OUT)

    def sign_in_browser(self) -> None:
        """Open the Mapflow sign-in page; the session continues when the browser comes back."""
        self.method, self._silent = BROWSER, False
        self._clear_credentials()
        self.browser.start()
        if self.browser.active:
            self._set_state(SIGNING_IN)

    def cancel_sign_in(self) -> None:
        if self.state == SIGNING_IN:
            self.browser.cancel()
            self.http.abort_all()
            self._clear_credentials()
            self._set_state(SIGNED_OUT)

    def sign_in_token(self, token: str) -> None:
        try:
            config_id = auth.store_token(self.config, token)
        except (ValueError, auth.AuthSetupError) as exc:
            self.error.emit(str(exc))
            return
        self._connect_token(config_id)

    def sign_out(self) -> None:
        self._timer.stop()
        self.browser.cancel()
        self.http.abort_all()
        if self.method == TOKEN:
            auth.forget_token(self.http.auth_config_id)
        auth.forget_refresh_token(self.config)
        self._clear_credentials()
        for key in ("auth_config_id", "auth_method"):
            self.settings.remove(key)
        self.status, self.project, self.projects, self.method, self.email = None, None, [], None, ""
        self._set_state(SIGNED_OUT)

    def stop(self) -> None:
        """Plugin unload: stop timers and the sign-in listener, keep the saved sign-in."""
        self._timer.stop()
        self._refresh_timer.stop()
        self.browser.cancel()

    def _clear_credentials(self) -> None:
        self._refresh_timer.stop()
        self._refreshing = False
        self.tokens = None
        self.http.bearer = None
        self.http.auth_config_id = None

    def _connect_token(self, config_id: str, silent: bool = False) -> None:
        self._clear_credentials()
        self.http.auth_config_id = config_id
        self.method, self._silent = TOKEN, silent
        self._set_state(SIGNING_IN)
        self.api.default_project(self._signed_in, self._sign_in_failed)

    # ---------- browser sign-in tokens ----------

    def _on_tokens(self, tokens: Tokens) -> None:
        if self.method != BROWSER or self.state == SIGNED_OUT:
            return                                   # cancelled or signed out meanwhile
        self._refreshing = False
        self.tokens = tokens
        self.http.auth_config_id = None
        self.http.bearer = tokens.access
        if tokens.refresh:
            auth.store_refresh_token(self.config, tokens.refresh)
        self._refresh_timer.start(int(tokens.refresh_delay() * 1000))
        if self.state == SIGNING_IN:
            self.api.default_project(self._signed_in, self._sign_in_failed)

    def refresh_sign_in(self) -> None:
        """Renew the access token before it expires (and after a restart)."""
        if self.method != BROWSER or not self.tokens or not self.tokens.refresh or self._refreshing:
            return
        self._refreshing = True
        refresh_tokens(self.http, self.config, self.tokens.refresh, self._on_tokens, self._refresh_failed)

    def _refresh_failed(self, error: ApiError) -> None:
        self._refreshing = False
        if error.kind in _TRANSIENT:
            if self.state == SIGNED_IN:
                self._refresh_timer.start(RETRY_REFRESH_MS)  # keep the session through a network hiccup
            elif self.state == SIGNING_IN:
                self._clear_credentials()                 # offline at start: keep the saved sign-in for later
                self._set_state(SIGNED_OUT)
            return
        auth.forget_refresh_token(self.config)
        if self.state == SIGNED_IN:
            self.sign_out()
            self.error.emit("Your Mapflow session has expired. Sign in again.")
        elif self.state == SIGNING_IN:
            self._clear_credentials()
            self._set_state(SIGNED_OUT)               # the saved sign-in ran out: show the sign-in page

    def _browser_failed(self, message: str) -> None:
        if self.state != SIGNED_IN and self.method == BROWSER:
            self._clear_credentials()
            self._set_state(SIGNED_OUT)
            self.error.emit(message)

    # ---------- after the credentials are in place ----------

    def _signed_in(self, data: dict) -> None:
        data = data or {}
        user = data.get("user") or {}
        self.email = user.get("email") or (auth.token_login(self.http.auth_config_id) if self.method == TOKEN else "")
        self.settings.setValue("auth_method", self.method)
        if self.method == TOKEN:
            self.settings.setValue("auth_config_id", self.http.auth_config_id)
        else:
            self.settings.remove("auth_config_id")
        default = Project.from_api(data, self.email)
        self.projects = [default]
        self._set_state(SIGNED_IN)
        self.refresh_status()
        self._timer.start()
        wanted = self.settings.value("project_id", "") or default.id
        if wanted == default.id:
            self._set_project(default)
        else:
            self.select_project(wanted, fallback=default)
        self.load_projects()

    def _sign_in_failed(self, error: ApiError) -> None:
        method = self.method
        self._clear_credentials()
        self._set_state(SIGNED_OUT)
        if error.kind == "auth":
            if method == TOKEN:
                auth.forget_token(self.settings.value("auth_config_id", ""))
            else:
                auth.forget_refresh_token(self.config)
        if not self._silent:
            message = error.message
            if error.kind == "auth":
                message = ("Mapflow didn't accept this token. Copy a new one from your Mapflow account."
                           if method == TOKEN else "Mapflow didn't accept the sign-in. Try again.")
            self.error.emit(message)

    def _on_unauthorized(self) -> None:
        if self.state != SIGNED_IN:
            return
        if self.method == BROWSER and time.time() - self._forced_refresh_at > 60:
            # The access token may have run out early (a sleeping laptop): renew once before giving up
            self._forced_refresh_at = time.time()
            self.refresh_sign_in()
            return
        self.sign_out()
        self.error.emit("Your Mapflow session has expired. Sign in again.")

    def _set_state(self, state: str) -> None:
        if state != self.state:
            self.state = state
            self.stateChanged.emit(state)

    # ---------- account and projects ----------

    def refresh_status(self) -> None:
        if self.state != SIGNED_IN:
            return
        self.api.user_status(self._on_status, on_error=lambda e: None)   # periodic: stay quiet on errors

    def _on_status(self, status: UserStatus) -> None:
        self.status = status
        self.statusChanged.emit(status)

    def load_projects(self) -> None:
        self.api.projects(self.email, self._on_projects, on_error=lambda e: None)

    def _on_projects(self, projects: List[Project]) -> None:
        if projects:
            self.projects = projects
            self.projectsChanged.emit(projects)

    def select_project(self, project_id: str, fallback: Optional[Project] = None) -> None:
        def failed(error: ApiError):
            if fallback is not None:
                self._set_project(fallback)
            else:
                self.error.emit(error.message)
        self.api.project(project_id, self.email, self._set_project, failed)

    def _set_project(self, project: Project) -> None:
        self.project = project
        self.settings.setValue("project_id", project.id)
        self.projectChanged.emit(project)
