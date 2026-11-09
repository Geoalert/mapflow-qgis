"""Browser sign-in to Mapflow, run by the plugin (not by QGIS's OAuth2 auth method).

QGIS's OAuth2 method answers the browser with its own fixed page and listens on every network
interface. Here the plugin keeps the same Mapflow client and redirect address
(http://127.0.0.1:7070/qgis), listens on the loopback interface only and for one sign-in at a time,
and answers the browser with a redirect to Mapflow Web as soon as the code arrives.
"""
from __future__ import annotations

from functools import partial
from itertools import count
from typing import Callable, Dict, List, Optional

from qgis.PyQt.QtCore import QObject, QTimer, QUrl, pyqtSignal
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtNetwork import QHostAddress, QTcpServer, QTcpSocket

from .. import config as cfg
from ..config import Config
from ..core import oauth
from ..core.oauth import Tokens
from .http import ApiError, Http


def open_in_browser(url: str) -> bool:
    """Replaceable in tests."""
    return QDesktopServices.openUrl(QUrl(url))


def exchange_code(http: Http, config: Config, code: str, verifier: str,
                  on_success: Callable[[Tokens], None], on_error: Callable[[ApiError], None]) -> int:
    form = oauth.code_form(code, verifier, cfg.OAUTH_CLIENT_ID, config.redirect_uri)
    return http.post(config.token_url, form=form, authorize=False,
                     on_success=lambda data: on_success(Tokens.from_response(data)), on_error=on_error)


def refresh_tokens(http: Http, config: Config, refresh_token: str,
                   on_success: Callable[[Tokens], None], on_error: Callable[[ApiError], None]) -> int:
    form = oauth.refresh_form(refresh_token, cfg.OAUTH_CLIENT_ID)
    return http.post(config.token_url, form=form, authorize=False,
                     on_success=lambda data: on_success(Tokens.from_response(data, refresh_token)),
                     on_error=on_error)


class BrowserSignIn(QObject):
    """One browser sign-in: open the Mapflow sign-in page, wait for the code on the loopback address,
    send the browser on to Mapflow Web, exchange the code for tokens."""

    succeeded = pyqtSignal(object)     # Tokens
    failed = pyqtSignal(str)

    def __init__(self, config: Config, http: Http, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.config, self.http = config, http
        self._server: Optional[QTcpServer] = None
        self._sockets: Dict[int, List] = {}          # key → [socket, received bytes]
        self._ids = count(1)
        self._verifier = self._state = ""
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._timed_out)

    @property
    def active(self) -> bool:
        return bool(self._state)

    def start(self) -> None:
        self.cancel()
        server = QTcpServer(self)
        if not server.listen(QHostAddress(QHostAddress.SpecialAddress.LocalHost), cfg.REDIRECT_PORT):
            server.deleteLater()
            self.failed.emit(f"Can't finish the browser sign-in: port {cfg.REDIRECT_PORT} is used by another "
                             "program. Close it and try again, or sign in with an API token.")
            return
        server.newConnection.connect(self._accept)
        self._server = server
        self._verifier, challenge = oauth.pkce_pair()
        self._state = oauth.new_state()
        self._timer.start(cfg.SIGN_IN_TIMEOUT_S * 1000)
        url = oauth.authorize_url(self.config.authorize_url, cfg.OAUTH_CLIENT_ID, self.config.redirect_uri,
                                  self._state, challenge, cfg.OAUTH_SCOPE)
        if not open_in_browser(url):
            self._stop()
            self.failed.emit("Couldn't open your browser. Sign in with an API token instead.")

    def cancel(self) -> None:
        self._stop()
        for key in list(self._sockets):
            self._sockets.pop(key)[0].abort()

    # ---------- the loopback listener ----------

    def _stop(self) -> None:
        """Stop listening. Sockets already answering finish on their own."""
        self._timer.stop()
        self._state = ""
        if self._server is not None:
            self._server.close()
            self._server.deleteLater()
            self._server = None

    def _accept(self) -> None:
        server = self._server
        while server is not None and server.hasPendingConnections():
            socket = server.nextPendingConnection()
            socket.setParent(self)               # outlives the server once it stops listening
            key = next(self._ids)
            self._sockets[key] = [socket, b""]
            socket.readyRead.connect(partial(self._read, key))
            socket.disconnected.connect(partial(self._drop, key))

    def _drop(self, key: int) -> None:
        entry = self._sockets.pop(key, None)
        if entry:
            entry[0].deleteLater()

    def _answer(self, socket: QTcpSocket, response: bytes) -> None:
        socket.write(response)
        socket.disconnectFromHost()              # closes after the answer is written

    def _read(self, key: int) -> None:
        entry = self._sockets.get(key)
        if entry is None:
            return
        socket = entry[0]
        entry[1] += bytes(socket.readAll())
        if len(entry[1]) > oauth.MAX_REQUEST_BYTES:
            socket.abort()
            return
        if b"\r\n\r\n" not in entry[1] and b"\n\n" not in entry[1]:
            return                               # the request head isn't complete yet
        if not self.active:
            self._answer(socket, oauth.http_response("410 Gone", oauth.page(
                "This sign-in has ended", "Return to QGIS and sign in again.")))
            return
        redirect = oauth.read_redirect(entry[1], cfg.REDIRECT_PATH, self._state)
        if redirect.kind == "other":
            self._answer(socket, oauth.http_response("404 Not Found"))
        elif redirect.kind == "stale":
            # Not this sign-in's answer (an old tab, or someone else): ignore it and keep waiting
            self._answer(socket, oauth.http_response("400 Bad Request", oauth.page(
                "This sign-in link is out of date", "Return to QGIS and use the browser tab it opened.")))
        elif redirect.kind == "error":
            self._stop()
            self._answer(socket, oauth.http_response("200 OK", oauth.page(
                "Sign-in didn't complete", "Return to QGIS and try again.", cfg.SIGNED_IN_URL, "Open Mapflow Web")))
            self.failed.emit(f"Sign-in didn't complete ({redirect.value}). Try again.")
        else:
            verifier = self._verifier
            self._stop()
            self._answer(socket, oauth.http_response("302 Found", oauth.page(
                "You're signed in", "Return to QGIS to continue.", cfg.SIGNED_IN_URL, "Open Mapflow Web"),
                location=cfg.SIGNED_IN_URL))
            exchange_code(self.http, self.config, redirect.value, verifier, self.succeeded.emit, self._exchange_failed)

    def _exchange_failed(self, error: ApiError) -> None:
        if error.kind in ("offline", "proxy", "timeout"):
            self.failed.emit(error.message)
        else:
            self.failed.emit("Mapflow didn't accept the sign-in. Try again.")

    def _timed_out(self) -> None:
        if self.active:
            self.cancel()
            self.failed.emit("The browser sign-in wasn't finished in time. Try again.")
