"""Who is logged in: the auth method, the credentials, and ending the session.

Holds no widget (`spec/007_architecture.md` § Layer rules). The login dialog's inputs arrive as
arguments — the typed token, the auth-method toggle — and the effects it must cause leave as
signals. `mapflow.py` keeps the dialog and the wiring, as the composition root.

What is deliberately NOT here is `log_in_callback`: it is the startup sequence, ordering the
project fetch, the models, the processings table and the first status poll. That is orchestration
across every region, so it stays in `mapflow.py` beside `on_account_status`, for the same reason
that one did.
"""
import logging
from base64 import b64decode
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal

from ..app_context import AppContext
from ..auth import get_auth_id
from ...config import Config
from ...errors import ProxyIsAlreadySet
from ...http import Http
# The icon-carrying helpers rather than `alert(..., icon=QMessageBox.X)`: naming an icon would
# mean importing PyQt5.QtWidgets, which a service may not do (`spec/007_architecture.md`).
from .alert_service import alert_info, alert_warning

logger = logging.getLogger(__name__)


class SessionService(QObject):
    """Logging in (basic token or OAuth), and logging out."""

    #: The login dialog's "invalid token" line should be shown or hidden.
    tokenRejected = pyqtSignal(bool)
    #: Credentials are missing or were refused — the login dialog should be shown.
    loginRequired = pyqtSignal()
    #: The auth method changed: (use_oauth, saved token). The dialog swaps its input for it.
    authTypeChanged = pyqtSignal(bool, str)
    #: The session ended. Listeners stop their polling and close the main window.
    loggedOut = pyqtSignal()

    def __init__(self,
                 http: Http,
                 app_context: AppContext,
                 config: Optional[Config] = None,
                 on_authenticated=None):
        super().__init__()
        self.http = http
        self.app_context = app_context
        self.config = config or Config
        #: Called with the `/projects/default` response once credentials are accepted. It is the
        #: startup sequence, which lives in `mapflow.py` — passed in as a plain callable so this
        #: service does not import it.
        self.on_authenticated = on_authenticated

    # ---------- which auth method ----------

    @property
    def use_oauth(self) -> bool:
        return str(self.app_context.settings.value("use_oauth", "false")).lower() == "true"

    def set_auth_type(self, use_oauth: bool = False) -> None:
        self.app_context.settings.setValue("use_oauth", str(use_oauth).lower())
        self.authTypeChanged.emit(bool(use_oauth), self.saved_token)

    @property
    def saved_token(self) -> str:
        return self.app_context.settings.value("token", "") or ""

    # ---------- logging in ----------

    def authenticate(self, typed_token: Optional[str] = None) -> None:
        """Log in with whichever method is selected. ``typed_token`` is what the user typed, read
        from the dialog by the caller — a service may not read a widget.

        The default is None rather than "": bandit reads a credential-named parameter with a
        string default as a hardcoded password (B107), and "nothing was supplied" is what None
        means anyway."""
        if self.use_oauth:
            self.login_with_auth_config()
            return
        if not typed_token:
            return
        self.login_basic(self.pad_token(typed_token))

    @staticmethod
    def pad_token(auth_data: str) -> str:
        """Base64 needs a length that is a multiple of four; the token as issued may not be."""
        return auth_data + "=" * ((4 - len(auth_data) % 4) % 4)

    def login_with_auth_config(self) -> None:
        """Resolve QGIS's stored auth config, creating it on first use, then log in with it."""
        auth_id, new_auth = get_auth_id(self.config.AUTH_CONFIG_NAME, self.config.AUTH_CONFIG_MAP)
        if new_auth:
            alert_info(self.tr("We have just set the authentication config for you. \n"
                               " You may need to restart QGIS to apply it so you could log in"))
        if not auth_id:
            self.tokenRejected.emit(True)
            return
        self.tokenRejected.emit(False)
        self.login_oauth(auth_id)

    def login_oauth(self, oauth_id) -> None:
        try:
            self.http.setup_auth(oauth_id=oauth_id)
        except ProxyIsAlreadySet:
            alert_warning(self.tr("Please restart QGIS before using OAuth2 login."))
            return
        except Exception as e:
            # The auth config is QGIS-managed and can be corrupted in ways this plugin cannot
            # enumerate, so the message tells the user how to recreate it rather than guessing.
            logger.exception("OAuth setup failed")
            alert_warning(self.tr("Error while trying to send authorization request: {error}. "
                                  "It is possible that your auth config is corrupted. "
                                  "Remove auth config named {name} and restart QGIS "
                                  "for the plugin to recreate it. "
                                  "If it does not help, contact us").format(
                                      error=e, name=self.config.AUTH_CONFIG_NAME))
            return
        self._request_default_project()

    def login_basic(self, token) -> None:
        """Log in with a Basic-auth token, saving it so the next launch starts logged in."""
        # Saved before it is validated, so a new token always replaces the old one — otherwise a
        # rejected login leaves the previous token in settings and the next launch retries it.
        self.app_context.settings.setValue('token', token)
        try:
            self.app_context.username, self.app_context.password = b64decode(token).decode().split(':')
        except (ValueError, TypeError):
            # A malformed token, which is the whole point of this handler. ValueError covers
            # all three ways it can be malformed: binascii.Error (not base64) and
            # UnicodeDecodeError (not utf-8) both subclass it, and so does the unpack when
            # the decoded text has no ':'. TypeError covers a non-str/bytes token.
            self.app_context.username = self.app_context.password = ''  # nosec B105  # clearing creds, not a secret
            self.loginRequired.emit()
            alert_warning(self.tr('Wrong token. '
                                  'Visit "<a href=\"https://app.mapflow.ai/account/api\">mapflow.ai</a>" '
                                  'to get a new one'))
            self.tokenRejected.emit(True)
            return
        self.http.setup_auth(basic_auth_token=f'Basic {token}')
        self._request_default_project()

    def _request_default_project(self) -> None:
        """The login request proper: user info and the default project ride on one response."""
        self.http.get(
            url=f'{self.config.SERVER}/projects/default',
            callback=self.on_authenticated,
            use_default_error_handler=True
        )

    # ---------- logging out ----------

    def logout(self) -> None:
        """End the session and clear the credentials from settings and from `Http`."""
        self.app_context.settings.setValue('token', '')
        self.app_context.logged_in = False
        self.http.logout()
        self.loggedOut.emit()
        self.loginRequired.emit()

    def reject_saved_token(self) -> None:
        """The server refused credentials that were never validated in this session — an admin
        changed the environment, or the token was revoked between launches."""
        alert_warning(self.tr('Wrong token. '
                              'Visit "<a href=\"https://app.mapflow.ai/account/api\">mapflow.ai</a>" '
                              'to get a new one'))
        self.loginRequired.emit()
