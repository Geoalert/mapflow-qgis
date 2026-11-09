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
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlencode, urlparse

from qgis.PyQt.QtCore import QByteArray, QFile, QIODevice, QObject, QSaveFile, QTimer, QUrl, pyqtSignal
from qgis.PyQt.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkReply, QNetworkRequest
from qgis.core import Qgis, QgsApplication, QgsMessageLog, QgsNetworkAccessManager

from ..config import PLUGIN_NAME, TIMEOUT_S
from ..core.messages import describe

Callback = Callable[..., None]


@dataclass
class ApiError:
    # auth | forbidden | not_found | client | server | offline | proxy | timeout | cancelled
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
    if timed_out:
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


@dataclass
class _Pending:
    reply: QNetworkReply
    on_success: Optional[Callback]
    on_error: Optional[Callback]
    parse: str
    timer: Optional[QTimer] = None
    timed_out: bool = False
    sink: Optional[QSaveFile] = None
    keep: Any = None              # objects that must live as long as the request (multipart body)
    authorized: bool = False      # carried Mapflow credentials: a 401 means the sign-in has ended


class Http(QObject):
    """`get/post/put/delete` take a path relative to the API root or an absolute URL. Callbacks:
    `on_success(result)` with parsed JSON, text or bytes; `on_error(ApiError)`."""

    unauthorized = pyqtSignal()
    failed = pyqtSignal(object)        # ApiError not handled by a caller

    def __init__(self, server: str, plugin_version: str, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.server = server.rstrip("/")
        self.plugin_version = plugin_version
        self.auth_config_id: Optional[str] = None     # API token: a Basic config in the QGIS auth database
        self.bearer: Optional[str] = None             # browser sign-in: the current access token
        self._nam = QgsNetworkAccessManager.instance()
        self._pending: Dict[int, _Pending] = {}
        self._ids = count(1)
        self._trusted_host = urlparse(self.server).hostname or ""

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
                 on_progress: Optional[Callback] = None) -> int:
        """Stream the body to `target` (atomic: the file appears only when complete)."""
        sink = QSaveFile(target)
        if not sink.open(QIODevice.OpenModeFlag.WriteOnly):
            self._fail(on_error, ApiError("client", f"Can't write {target}: {sink.errorString()}"))
            return 0
        return self._send("GET", path, on_success=on_success, on_error=on_error, timeout=timeout,
                          parse="file", sink=sink, on_progress=on_progress)

    def upload(self, path: str, file_path: str, on_success: Optional[Callback] = None,
               on_error: Optional[Callback] = None, on_progress: Optional[Callback] = None) -> int:
        """Multipart upload of one GeoTIFF, streamed from disk."""
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
                          timeout=0, on_progress=on_progress, upload=True)

    def abort(self, request_id: int) -> None:
        pending = self._pending.get(request_id)
        if pending:
            pending.reply.abort()

    def abort_all(self) -> None:
        for pending in list(self._pending.values()):
            pending.reply.abort()

    # ---------- internals ----------

    def url_for(self, path: str) -> str:
        return path if path.startswith(("http://", "https://")) else f"{self.server}/{path.lstrip('/')}"

    def _send(self, method: str, path: str, body: Any = None, on_success: Optional[Callback] = None,
              on_error: Optional[Callback] = None, timeout: Optional[int] = None, parse: str = "json",
              sink: Optional[QSaveFile] = None, on_progress: Optional[Callback] = None,
              upload: bool = False, authorize: Optional[bool] = None,
              form: Optional[Dict[str, str]] = None) -> int:
        url = self.url_for(path)
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"x-plugin-version", self.plugin_version.encode())
        if authorize is None:
            # Credentials go to Mapflow only, never to a preview or presigned storage URL
            authorize = (urlparse(url).hostname or "") == self._trusted_host
        authorize = bool(authorize and (self.bearer or self.auth_config_id))
        if authorize and self.bearer:
            request.setRawHeader(b"Authorization", f"Bearer {self.bearer}".encode())
        elif authorize:
            result = QgsApplication.authManager().updateNetworkRequest(request, self.auth_config_id)
            updated, request = result if isinstance(result, tuple) else (result, request)
            if not updated:
                QgsMessageLog.logMessage(f"Auth config {self.auth_config_id} was not applied to {url}",
                                         PLUGIN_NAME, Qgis.MessageLevel.Warning)
        data = None
        if form is not None:
            data = QByteArray(urlencode(form).encode())
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/x-www-form-urlencoded")
        elif isinstance(body, (dict, list)):
            data = QByteArray(json.dumps(body).encode())
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        elif isinstance(body, (bytes, bytearray)):
            data = QByteArray(bytes(body))
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")

        if method == "GET":
            reply = self._nam.get(request)
        elif method == "DELETE":
            reply = self._nam.deleteResource(request)
        elif method == "PUT":
            reply = self._nam.put(request, data if data is not None else QByteArray())
        elif upload:
            reply = self._nam.post(request, body)
            body.setParent(reply)
        else:
            reply = self._nam.post(request, data if data is not None else QByteArray())

        key = next(self._ids)
        pending = _Pending(reply, on_success, on_error, parse, sink=sink, keep=body if upload else None,
                           authorized=authorize)
        self._pending[key] = pending
        reply.finished.connect(partial(self._finished, key))
        if sink is not None:
            reply.readyRead.connect(partial(self._drain, key))
        if on_progress is not None:
            signal = reply.uploadProgress if upload else reply.downloadProgress
            signal.connect(lambda done, total, cb=on_progress: cb(done, total))
        seconds = TIMEOUT_S if timeout is None else timeout
        if seconds:
            pending.timer = QTimer(self)
            pending.timer.setSingleShot(True)
            pending.timer.timeout.connect(partial(self._timeout, key))
            pending.timer.start(seconds * 1000)
        return key

    def _drain(self, key: int) -> None:
        pending = self._pending.get(key)
        if pending and pending.sink is not None:
            pending.sink.write(pending.reply.readAll())
            if pending.timer:
                pending.timer.start()   # data is flowing: restart the inactivity timer

    def _timeout(self, key: int) -> None:
        pending = self._pending.get(key)
        if pending and not pending.reply.isFinished():
            pending.timed_out = True
            pending.reply.abort()

    def _finished(self, key: int) -> None:
        pending = self._pending.pop(key, None)
        if pending is None:
            return
        reply = pending.reply
        if pending.timer:
            pending.timer.stop()
            pending.timer.deleteLater()
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError or pending.timed_out:
                body = "" if pending.sink is not None else bytes(reply.readAll()).decode("utf-8", "replace")
                if pending.sink is not None:
                    pending.sink.cancelWriting()
                error = classify(reply.error(), status, body, reply.url().toString(), pending.timed_out)
                QgsMessageLog.logMessage(f"{error.kind} {status} {error.url}: {error.code} {error.body[:500]}",
                                         PLUGIN_NAME, Qgis.MessageLevel.Warning)
                if error.kind == "auth" and pending.authorized:
                    self.unauthorized.emit()
                self._fail(pending.on_error, error)
                return
            if pending.sink is not None:
                pending.sink.write(reply.readAll())
                if not pending.sink.commit():
                    self._fail(pending.on_error,
                               ApiError("client", f"Can't save the file: {pending.sink.errorString()}"))
                    return
                result: Any = pending.sink.fileName()
            else:
                raw = bytes(reply.readAll())
                if pending.parse == "bytes":
                    result = raw
                elif pending.parse == "text":
                    result = raw.decode("utf-8", "replace")
                else:
                    result = json.loads(raw.decode("utf-8")) if raw.strip() else None
            if pending.on_success:
                pending.on_success(result)
        except ValueError as exc:
            self._fail(pending.on_error, ApiError("server", f"Unexpected response from Mapflow: {exc}",
                                                  status, url=reply.url().toString()))
        finally:
            reply.deleteLater()

    def _fail(self, on_error: Optional[Callback], error: ApiError) -> None:
        if error.kind == "cancelled":
            return
        if on_error:
            on_error(error)
        else:
            self.failed.emit(error)
