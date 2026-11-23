"""Asynchronous HTTP over QGIS's network manager (proxy settings, SSL and auth DB included).

One rule from the current plugin's fixes is built in: every in-flight reply is held by the client
until it finishes, and slots get a key, never the reply itself, so no reply/lambda cycle can be
collected mid-request. Large bodies are streamed to disk instead of read into memory.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import partial
from itertools import count
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import urlencode

from qgis.PyQt.QtCore import QByteArray, QFile, QIODevice, QObject, QSaveFile, QTimer, QUrl, pyqtSignal
from qgis.PyQt.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkReply, QNetworkRequest
from qgis.core import Qgis, QgsApplication, QgsMessageLog, QgsNetworkAccessManager

from ..config import DOMAIN, PLUGIN_NAME, TIMEOUT_S, UPLOAD_TIMEOUT_S
from ..core import guard
from ..core.domain import with_domain
from ..core.guard import guarded
from ..core.messages import describe
from ..core.origin import Origin, carries_credentials
from ..core.report import RequestInfo, hide_tile_source, without_query
from ..core.tile_layers import has_tile_source, hide_address_params

Callback = Callable[..., None]

# Redirects are followed one hop at a time by `Http`, never by Qt: each hop is judged on its own URL, so
# credentials never travel to another origin in a header that Qt copied. MAX_REDIRECTS stops a redirect loop.
MAX_REDIRECTS = 5
_REDIRECT_STATUSES = (301, 302, 303, 307, 308)

RESPONSE_KEPT = 20_000      # bytes of an answer kept for a report; core/report.py cuts it shorter

PLUGIN_FAILED_TEXT = ("Mapflow answered, but the plugin could not process the answer. "
                      "Details are in the Log Messages panel.")


@dataclass
class ApiError:
    # auth | forbidden | not_found | client | server | offline | proxy | timeout | cancelled | plugin
    # (plugin: the answer was fine, the caller's code failed on it; cancelled: the plugin asked for the abort
    # itself, and nobody is told)
    kind: str
    message: str                  # ready to show
    status: Optional[int] = None
    code: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    url: str = ""
    body: str = ""

    def __str__(self) -> str:
        return self.message


_NetworkError = QNetworkReply.NetworkError
_PROXY_ERRORS = {_NetworkError.ProxyConnectionRefusedError, _NetworkError.ProxyConnectionClosedError,
                 _NetworkError.ProxyNotFoundError, _NetworkError.ProxyTimeoutError,
                 _NetworkError.ProxyAuthenticationRequiredError, _NetworkError.UnknownProxyError}
_SERVER_ERRORS = {_NetworkError.ServiceUnavailableError, _NetworkError.InternalServerError,
                  _NetworkError.ConnectionRefusedError, _NetworkError.RemoteHostClosedError,
                  _NetworkError.NetworkSessionFailedError, _NetworkError.TemporaryNetworkFailureError,
                  _NetworkError.UnknownServerError}


def parse_error_body(body: str):
    """(code, message, params) from the API's `{code, message, params}` or the data catalog's
    `{detail: …}` error shapes; plain text falls through as the message."""
    try:
        data = json.loads(body)
    except (ValueError, TypeError):
        return "", body.strip()[:300], {}
    if isinstance(data, dict) and "detail" in data:
        detail = data["detail"]
        if isinstance(detail, dict):
            return (detail.get("code", ""), detail.get("message", ""),
                    detail.get("parameters") or detail.get("params") or {})
        if isinstance(detail, list):  # FastAPI validation errors
            return "", "; ".join(str(d.get("msg", d)) for d in detail if isinstance(d, dict)), {}
        return "", str(detail), {}
    if isinstance(data, dict):
        return data.get("code", ""), data.get("message", ""), data.get("params") or data.get("parameters") or {}
    return "", str(data), {}


def classify(qt_error: int, status: Optional[int], body: str, url: str, timed_out: bool) -> ApiError:
    code, message, params = parse_error_body(body)
    readable = describe(code, params, message) if (code or message) else ""
    # Read at call time, with a default: a Qt build without the name must not make a failed request raise.
    timeout_error = getattr(QNetworkReply.NetworkError, "TimeoutError", None)
    if timed_out or qt_error == timeout_error:
        return ApiError("timeout", "Mapflow did not answer in time. Try again.", status, url=url, body=body)
    if qt_error == QNetworkReply.NetworkError.OperationCanceledError:
        return ApiError("cancelled", "Request cancelled.", status, url=url)
    if status == 401 or qt_error == QNetworkReply.NetworkError.AuthenticationRequiredError:
        return ApiError("auth", "Your Mapflow session has expired. Sign in again.", status, code, params, url, body)
    if status == 403 or qt_error == QNetworkReply.NetworkError.ContentAccessDenied:
        return ApiError("forbidden", readable or "This action is not available for your account.",
                        status, code, params, url, body)
    if status == 404 or qt_error == QNetworkReply.NetworkError.ContentNotFoundError:
        return ApiError("not_found", readable or "Not found. It may have been deleted.", status, code, params, url,
                        body)
    if qt_error == QNetworkReply.NetworkError.HostNotFoundError:
        return ApiError("offline", "Can't reach Mapflow. Check your internet connection.", status, url=url)
    if qt_error in _PROXY_ERRORS:
        return ApiError("proxy", "Proxy error. Check QGIS › Settings › Options › Network.", status, url=url)
    if (status and status >= 500) or qt_error in _SERVER_ERRORS:
        return ApiError("server", readable or "Mapflow is not responding right now. Try again in a minute.",
                        status, code, params, url, body)
    return ApiError("client", readable or f"Request failed ({status or qt_error}).", status, code, params, url, body)


def _status_of(reply: QNetworkReply) -> Optional[int]:
    return reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)


def _is_redirect(reply: QNetworkReply) -> bool:
    return _status_of(reply) in _REDIRECT_STATUSES


def _origin_of(url: QUrl) -> Optional[Origin]:
    """The origin of the URL that Qt will send: the parser that sends is the one that decides."""
    return Origin.from_parts(url.scheme(), url.host(), url.port(-1))


@dataclass
class _Pending:
    reply: Optional[QNetworkReply]    # the reply of the current hop
    on_success: Optional[Callback]
    on_error: Optional[Callback]
    parse: str
    timer: Optional[QTimer] = None
    timed_out: bool = False
    sink: Optional[QSaveFile] = None
    keep: Any = None              # objects that must live as long as the request (multipart body)
    authorized: bool = False      # carried Mapflow credentials: a 401 means the sign-in has ended
    bearer: Optional[str] = None  # …the access token it carried, if any
    method: str = ""
    url: str = ""                 # without the query string: it names the request in reports
    allow_credentials: bool = True    # False: never carries them (the token endpoint)
    data: Optional[QByteArray] = None  # the body of a JSON or form request
    form: bool = False            # …and it is a form
    body: Any = None              # the multipart of an upload
    upload: bool = False
    on_progress: Optional[Callback] = None
    timeout: int = 0              # seconds of inactivity; every request has one
    sent: int = 0                 # bytes of an upload sent so far, as the last progress said
    hops: int = 0                 # redirects followed so far
    redirect_refused: str = ""    # why a redirect was not followed
    aborted: bool = False         # the plugin aborted the reply (`abort`, `abort_all`); any other abort is not its own
    write_error: str = ""         # why the sink refused the body; the reply was aborted for it
    response: str = ""            # the start of a decoded text or JSON answer: a report names it if the callback fails
    sensitive: bool = False       # the body holds a `userDefined` tile source: no answer text is kept or reported


class Http(QObject):
    """`get/post/put/delete` take a path relative to the API root or an absolute URL. Callbacks:
    `on_success(result)` with parsed JSON, text or bytes; `on_error(ApiError)`.

    `answered=True` says the absolute URL comes from a server answer: when the plugin uses another domain
    (`domain`), the host changes to it before the request is built, so the log, the report and the credentials
    rule see the final address. A redirect target is such an address too. Every other URL is used as written."""

    unauthorized = pyqtSignal()
    failed = pyqtSignal(object)        # ApiError not handled by a caller

    def __init__(self, server: str, plugin_version: str, parent: Optional[QObject] = None, domain: str = DOMAIN):
        super().__init__(parent)
        self.server = server.rstrip("/")
        self.domain = domain       # in place of the default one, in the addresses of server answers
        self.plugin_version = plugin_version
        self.auth_config_id: Optional[str] = None     # API token: a Basic config in the QGIS auth database
        self.bearer: Optional[str] = None             # browser sign-in: the current access token
        self._nam = QgsNetworkAccessManager.instance()
        self._pending: Dict[int, _Pending] = {}
        self._stopped = False
        self._ids = count(1)
        self._api_origin = _origin_of(QUrl(self.server))

    # ---------- public ----------

    def get(self, path: str, **kwargs) -> int:
        return self._send("GET", path, **kwargs)

    def post(self, path: str, body: Any = None, **kwargs) -> int:
        return self._send("POST", path, body=body, **kwargs)

    def put(self, path: str, body: Any = None, **kwargs) -> int:
        return self._send("PUT", path, body=body, **kwargs)

    def delete(self, path: str, **kwargs) -> int:
        return self._send("DELETE", path, **kwargs)

    def download(self, path: str, target: str, on_success: Optional[Callback] = None,
                 on_error: Optional[Callback] = None, timeout: Optional[int] = None,
                 on_progress: Optional[Callback] = None, authorize: bool = True, answered: bool = False) -> int:
        """Stream the body to `target` (atomic: the file appears only when complete). A `target` that can't be
        opened fails at once, before any request. `authorize=False`: the request never carries Mapflow credentials,
        whatever its origin."""
        if self._stopped:
            return 0
        sink = QSaveFile(target)
        if not sink.open(QIODevice.OpenModeFlag.WriteOnly):
            self._fail(on_error, ApiError("client", f"Can't write {target}: {sink.errorString()}"))
            return 0
        return self._send("GET", path, on_success=on_success, on_error=on_error, timeout=timeout,
                          parse="file", sink=sink, on_progress=on_progress, authorize=authorize,
                          answered=answered)

    def upload(self, path: str, file_path: str, on_success: Optional[Callback] = None,
               on_error: Optional[Callback] = None, on_progress: Optional[Callback] = None) -> int:
        """Multipart upload of one GeoTIFF, streamed from disk. It ends as a timeout after an hour of silence."""
        multipart = QHttpMultiPart(QHttpMultiPart.ContentType.FormDataType)
        part = QHttpPart()
        part.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "image/tiff")
        name = file_path.replace("\\", "/").split("/")[-1].replace('"', "")
        part.setHeader(QNetworkRequest.KnownHeaders.ContentDispositionHeader,
                       f'form-data; name="file"; filename="{name}"')
        source = QFile(file_path, multipart)
        if not source.open(QIODevice.OpenModeFlag.ReadOnly):
            self._fail(on_error, ApiError("client", f"Can't read {file_path}: {source.errorString()}"))
            return 0
        part.setBodyDevice(source)
        multipart.append(part)
        return self._send("POST", path, body=multipart, on_success=on_success, on_error=on_error,
                          timeout=UPLOAD_TIMEOUT_S, on_progress=on_progress, upload=True)

    def abort(self, request_id: int) -> None:
        pending = self._pending.get(request_id)
        if pending:
            pending.aborted = True
            pending.reply.abort()

    def abort_all(self) -> None:
        for pending in list(self._pending.values()):
            pending.aborted = True
            pending.reply.abort()

    def stop(self) -> None:
        """Unload: end every pending request and its timer, and refuse new ones. No callback runs and nothing is
        reported: the code that waits for an answer is going too."""
        self._stopped = True
        pending, self._pending = list(self._pending.values()), {}     # an aborted reply's `finished` finds no key
        for item in pending:
            if item.timer:
                item.timer.stop()
                item.timer.deleteLater()
            if item.sink is not None:
                item.sink.cancelWriting()
            if item.reply is not None:
                if not item.reply.isFinished():
                    item.reply.abort()
                item.reply.deleteLater()

    # ---------- internals ----------

    def url_for(self, path: str) -> str:
        return path if path.startswith(("http://", "https://")) else f"{self.server}/{path.lstrip('/')}"

    def _send(self, method: str, path: str, body: Any = None, on_success: Optional[Callback] = None,
              on_error: Optional[Callback] = None, timeout: Optional[int] = None, parse: str = "json",
              sink: Optional[QSaveFile] = None, on_progress: Optional[Callback] = None,
              upload: bool = False, authorize: bool = True,
              form: Optional[Dict[str, str]] = None, answered: bool = False) -> int:
        """`answered`: `path` is an address from a server answer (see the class). `authorize` says the request
        may carry credentials; whether it does depends on its origin (`_dispatch`).
        A body that holds a `userDefined` tile source makes the request sensitive: the server's answer may repeat
        the address and the login, so its text reaches no log line and no report, and an error keeps its
        parameters with the addresses cut to their hosts. Every other answer text that is kept (a report, a log
        line) passes through `hide_tile_source` first, as an answer about a processing holds its tile source."""
        if self._stopped:       # silent: the caller is code that outlived the unload, and nobody is left to tell
            return 0
        timeout = TIMEOUT_S if timeout is None else timeout
        if timeout <= 0:    # 0 used to mean "none": a caller that passes it must fail here, not hang later
            raise ValueError("a request needs a timeout")
        url = self.url_for(path)
        if answered:
            url = with_domain(url, DOMAIN, self.domain)
        data = None
        if form is not None:
            data = QByteArray(urlencode(form).encode())
        elif isinstance(body, (dict, list)):
            data = QByteArray(json.dumps(body).encode())
        elif isinstance(body, (bytes, bytearray)):
            data = QByteArray(bytes(body))
        key = next(self._ids)
        pending = _Pending(None, on_success, on_error, parse, sink=sink, keep=body if upload else None,
                           method=method, url=without_query(url), allow_credentials=authorize, data=data,
                           body=body, upload=upload, on_progress=on_progress, form=form is not None,
                           timeout=timeout, sensitive=has_tile_source(body))
        self._pending[key] = pending
        try:
            self._dispatch(key, QUrl(url))
        except Exception:
            del self._pending[key]
            raise
        pending.timer = QTimer(self)
        pending.timer.setSingleShot(True)
        pending.timer.timeout.connect(partial(self._timeout, key))
        pending.timer.start(pending.timeout * 1000)
        return key

    def _dispatch(self, key: int, url: QUrl) -> None:
        """Start the request of one hop (the first, or a redirect's) for the pending `key`."""
        pending = self._pending[key]
        request = QNetworkRequest(url)
        request.setRawHeader(b"x-plugin-version", self.plugin_version.encode())
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
        # Credentials go to the API's own scheme, host and port only, never to a preview or a presigned URL
        authorize = bool(pending.allow_credentials and (self.bearer or self.auth_config_id)
                         and carries_credentials(_origin_of(url), self._api_origin))
        if authorize and self.bearer:
            request.setRawHeader(b"Authorization", f"Bearer {self.bearer}".encode())
        elif authorize:
            result = QgsApplication.authManager().updateNetworkRequest(request, self.auth_config_id)
            updated, request = result if isinstance(result, tuple) else (result, request)
            if not updated:
                QgsMessageLog.logMessage(f"Auth config {self.auth_config_id} was not applied to "
                                         f"{without_query(url.toString())}", PLUGIN_NAME, Qgis.MessageLevel.Warning)
        if pending.data is not None:
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader,
                              "application/x-www-form-urlencoded" if pending.form else "application/json")
        method, data, body = pending.method, pending.data, pending.body
        if method == "GET":
            reply = self._nam.get(request)
        elif method == "DELETE":
            reply = self._nam.deleteResource(request)
        elif method == "PUT":
            reply = self._nam.put(request, data if data is not None else QByteArray())
        elif pending.upload:
            reply = self._nam.post(request, body)
            body.setParent(reply)
        else:
            reply = self._nam.post(request, data if data is not None else QByteArray())
        pending.reply = reply
        pending.authorized = authorize
        pending.bearer = self.bearer if authorize else None
        reply.finished.connect(partial(self._finished, key))
        if pending.sink is not None:
            reply.readyRead.connect(partial(self._drain, key))
        if pending.upload:
            reply.uploadProgress.connect(partial(self._alive, key))
        if pending.on_progress is not None:
            signal = reply.uploadProgress if pending.upload else reply.downloadProgress
            signal.connect(guarded(lambda done, total, cb=pending.on_progress: cb(done, total)))

    @guarded
    def _drain(self, key: int) -> None:
        pending = self._pending.get(key)
        if (pending and pending.sink is not None and not pending.write_error
                and not _is_redirect(pending.reply)):      # a redirect's body is no result
            if (_status_of(pending.reply) or 0) >= 400:     # an error's body is small and `_read` ignores it
                return
            data = pending.reply.readAll()
            if pending.sink.write(data) != len(data):
                # A full disk shows now, not after the last byte of several GB. `abort` ends the reply at once and
                # `_finished` removes the pending entry, so nothing of `pending` is touched after it.
                pending.write_error = pending.sink.errorString() or "the disk write failed"
                pending.aborted = True
                pending.reply.abort()
                return
            if pending.timer:
                pending.timer.start()   # data is flowing: restart the inactivity timer

    @guarded
    def _alive(self, key: int, sent: int, _total: int) -> None:
        """An upload moves bytes: restart its inactivity timer, so only a stalled upload times out."""
        pending = self._pending.get(key)
        if pending and pending.timer and sent > pending.sent:
            pending.sent = sent
            pending.timer.start()

    @guarded
    def _timeout(self, key: int) -> None:
        pending = self._pending.get(key)
        if pending and not pending.reply.isFinished():
            pending.timed_out = True
            pending.reply.abort()

    @guarded
    def _finished(self, key: int) -> None:
        pending = self._pending.get(key)
        if pending is None:
            return
        reply = pending.reply
        status = _status_of(reply)
        if (_is_redirect(reply) and reply.error() == QNetworkReply.NetworkError.NoError
                and not pending.timed_out):
            if self._redirect(key, pending, reply):
                return
        del self._pending[key]
        if pending.timer:
            pending.timer.stop()
            pending.timer.deleteLater()
        reported = False
        try:
            ok, outcome = self._read(pending, reply, status)
        except Exception as exc:  # noqa: BLE001 - plugin code failed while reading; the caller still gets an outcome
            guard.report(exc, f"{pending.method} {pending.url}: reading the answer",
                         RequestInfo(pending.method, pending.url, status, ""))
            ok, outcome, reported = False, ApiError("plugin", PLUGIN_FAILED_TEXT, status, url=pending.url), True
        finally:
            reply.deleteLater()
        if ok:
            self._succeed(pending, outcome, status)
        else:
            self._fail(pending.on_error, outcome, reported, pending)

    def _redirect(self, key: int, pending: _Pending, reply: QNetworkReply) -> bool:
        """Follow the redirect of `reply` as the next hop of the same request. False: it ends here, as an error
        (`_finished` reports it): the answer that is not a redirect, a write, another protocol, a step from https
        to http, a loop."""
        target = reply.attribute(QNetworkRequest.Attribute.RedirectionTargetAttribute)
        target = QUrl(target) if isinstance(target, str) else target
        if not isinstance(target, QUrl) or target.isEmpty():
            return False
        origin_url = reply.url()
        url = origin_url.resolved(target)
        text = url.toString(QUrl.ComponentFormattingOption.FullyEncoded)
        changed = with_domain(text, DOMAIN, self.domain)
        if changed != text:                     # an address that stays is not written again: a presigned one is exact
            url = QUrl(changed)
        if pending.method != "GET":
            reason = "it answered a change with a redirect, which the plugin does not repeat"
        elif url.scheme().lower() not in ("http", "https"):
            reason = "it redirected to an address that is not http or https"
        elif origin_url.scheme().lower() == "https" and url.scheme().lower() == "http":
            reason = "it redirected from https to http"
        elif pending.hops >= MAX_REDIRECTS:
            reason = "it redirected too many times"
        else:
            reason = ""
        if reason:
            pending.redirect_refused = reason
            return False
        pending.hops += 1
        reply.deleteLater()
        if pending.timer:
            pending.timer.start()
        self._dispatch(key, url)
        return True

    def _read(self, pending: _Pending, reply: QNetworkReply, status: Optional[int]) -> Tuple[bool, Any]:
        """(True, the result) or (False, the ApiError). Reading is the only place that turns a bad body into
        "Unexpected response from Mapflow": the caller's callbacks run elsewhere (`_succeed`)."""
        if status in _REDIRECT_STATUSES and reply.error() == QNetworkReply.NetworkError.NoError \
                and not pending.timed_out:
            # A redirect that `_redirect` did not follow
            if pending.sink is not None:
                pending.sink.cancelWriting()
            reason = pending.redirect_refused or "its answer has no address to go to"
            error = ApiError("server", f"Mapflow redirected the request, and the plugin did not follow it: {reason}.",
                             status, url=pending.url)
            QgsMessageLog.logMessage(f"{error.kind} {status} {pending.url}: redirect refused: {reason}",
                                     PLUGIN_NAME, Qgis.MessageLevel.Warning)
            return False, error
        if pending.write_error:
            pending.sink.cancelWriting()
            error = ApiError("client", f"Can't save the file: {pending.write_error}", status, url=pending.url)
            QgsMessageLog.logMessage(f"{error.kind} {status} {pending.url}: {pending.write_error}",
                                     PLUGIN_NAME, Qgis.MessageLevel.Warning)
            return False, error
        if reply.error() != QNetworkReply.NetworkError.NoError or pending.timed_out:
            body = "" if pending.sink is not None else hide_tile_source(
                bytes(reply.readAll()).decode("utf-8", "replace"))
            if pending.sink is not None:
                pending.sink.cancelWriting()
            # An abort that the plugin did not ask for is QGIS's own network timeout (it aborts a reply that made no
            # progress): the request ends as a timeout, through `on_error`, as one of the plugin's timer does
            unasked = (reply.error() == QNetworkReply.NetworkError.OperationCanceledError and not pending.aborted)
            error = classify(reply.error(), status, body, without_query(reply.url().toString()),
                             pending.timed_out or unasked)
            if pending.sensitive:
                error.body, error.params = "", hide_address_params(error.params)
            QgsMessageLog.logMessage(f"{error.kind} {status} {error.url}: {error.code} {error.body[:500]}",
                                     PLUGIN_NAME, Qgis.MessageLevel.Warning)
            # A request sent with an access token renewed since says nothing about the current sign-in
            if error.kind == "auth" and pending.authorized and pending.bearer == self.bearer:
                self.unauthorized.emit()
            return False, error
        if pending.sink is not None:
            data = reply.readAll()
            if pending.sink.write(data) != len(data) or not pending.sink.commit():
                reason = pending.sink.errorString()
                pending.sink.cancelWriting()
                return False, ApiError("client", f"Can't save the file: {reason}")
            return True, pending.sink.fileName()
        raw = bytes(reply.readAll())
        if pending.parse == "bytes":
            return True, raw
        if not pending.sensitive:
            pending.response = hide_tile_source(raw.decode("utf-8", "replace"))[:RESPONSE_KEPT]
        if pending.parse == "text":
            return True, raw.decode("utf-8", "replace")
        try:
            return True, (json.loads(raw.decode("utf-8")) if raw.strip() else None)
        except ValueError as exc:       # JSONDecodeError and UnicodeDecodeError: the body is not the promised JSON
            error = ApiError("server", f"Unexpected response from Mapflow: {exc}", status,
                             url=without_query(reply.url().toString()),
                             body="" if pending.sensitive else hide_tile_source(raw.decode("utf-8", "replace"))[:500])
            QgsMessageLog.logMessage(f"{error.kind} {status} {pending.url}: not JSON: {exc}",
                                     PLUGIN_NAME, Qgis.MessageLevel.Warning)
            return False, error

    def _succeed(self, pending: _Pending, result: Any, status: Optional[int]) -> None:
        if not pending.on_success:
            return
        try:
            pending.on_success(result)
        except Exception as exc:  # noqa: BLE001 - a failure of the caller's code, not of the answer
            guard.report(exc, f"{pending.method} {pending.url}: on_success",
                         RequestInfo(pending.method, pending.url, status, pending.response))
            # The user has been told: the caller's on_error still runs, so its cleanup happens, once
            self._fail(pending.on_error, ApiError("plugin", PLUGIN_FAILED_TEXT, status, url=pending.url),
                       reported=True, pending=pending)

    def _fail(self, on_error: Optional[Callback], error: ApiError, reported: bool = False,
              pending: Optional[_Pending] = None) -> None:
        """`reported`: the guard has already told the user, so `failed` does not say it again. `pending` is the
        request that failed, when there is one: a failing `on_error` is reported with it. A `cancelled` error is an
        abort that the plugin asked for: the code that asked is not waiting for an outcome."""
        if error.kind == "cancelled":
            return
        if on_error:
            try:
                on_error(error)
            except Exception as exc:  # noqa: BLE001 - nothing runs after a failing on_error
                request = (RequestInfo(pending.method, pending.url, error.status, error.body)
                           if pending is not None else None)
                guard.report(exc, f"{error.kind} {without_query(error.url)}: on_error", request)
        elif not reported:
            self.failed.emit(error)
