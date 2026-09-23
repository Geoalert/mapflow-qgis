import functools
import json
import logging
from enum import Enum
from typing import Callable, Union, Optional

from PyQt5.QtCore import QBuffer, QByteArray, QObject, QTimer, QUrl
from PyQt5.QtNetwork import QHttpMultiPart, QNetworkReply, QNetworkRequest
from qgis.core import QgsNetworkAccessManager, QgsApplication, QgsAuthMethodConfig

from .config import BACKGROUND_RETRY_DELAY_SECONDS, DEFAULT_HTTP_TIMEOUT_SECONDS, POLL_FAILURES_BEFORE_ALERT
from .errors import ErrorMessage, ProxyIsAlreadySet

logger = logging.getLogger(__name__)


class RequestMode(Enum):
    """When a request's transient failure reaches its error handlers (spec/005 § Request modes).

    Every request declares one and there is no default. The mode belongs to what triggered the
    request, not to its endpoint: the same page request is `POLL` from the refresh timer and
    `INTERACTIVE` from the paging button.
    """
    #: The user just triggered it and is waiting on it: every failure is handled at once.
    INTERACTIVE = "interactive"
    #: Nobody is waiting on it: a transient failure is sent once more before it is handled.
    BACKGROUND = "background"
    #: A timer sends it again anyway: a transient failure is handled only once the endpoint keeps failing.
    POLL = "poll"


#: Failures of the connection or the server rather than of the request — the ones asking again can
#: fix. Everything else (401, 403, 404, every other 4xx) is handled at once whatever the mode.
TRANSIENT_ERRORS = frozenset({
    QNetworkReply.OperationCanceledError,  # `send_request` aborts a reply that outlives its timeout
    QNetworkReply.TimeoutError,
    QNetworkReply.RemoteHostClosedError,
    QNetworkReply.ConnectionRefusedError,
    QNetworkReply.HostNotFoundError,
    QNetworkReply.TemporaryNetworkFailureError,
    QNetworkReply.NetworkSessionFailedError,
    QNetworkReply.UnknownNetworkError,  # the connection dropped mid-request
    QNetworkReply.ProxyConnectionClosedError,
    QNetworkReply.ProxyTimeoutError,
    QNetworkReply.InternalServerError,  # 500
    QNetworkReply.ServiceUnavailableError,  # 503
    QNetworkReply.UnknownServerError,  # the other 5xx a gateway returns: 502, 504
})


def _request_path(response: QNetworkReply) -> str:
    """Endpoint path for an error report — path only, never the full URL.

    Query strings can carry ids and tokens, and this string ends up in a mail body the
    user sends to us. The path is enough to locate the call site.
    """
    try:
        return response.request().url().path() or 'the server'
    except (AttributeError, RuntimeError):
        # No reply object, or its C++ side is already gone — this runs while reporting an
        # error, so it must not add one of its own.
        return 'the server'


def response_signature(response: QNetworkReply) -> str:
    """Suppression identity for an HTTP failure (spec/006 § Volume limit): the Qt error code plus
    the query-free endpoint path. There is no raising frame to key on, as there is for an
    exception. Reuses `_request_path` so the signature and the report body carry the same string,
    and no id or token from a query makes each occurrence of one failure look distinct.
    """
    try:
        code = response.error()
    except (AttributeError, RuntimeError):
        code = 'unknown'
    return f'{code}@{_request_path(response)}'


class Http(QObject):
    """"""

    def __init__(self,
                 server: str,
                 plugin_version: str,
                 default_error_handler: Callable) -> None:
        """
        oauth_id is defined if we are using oauth2 configuration
        """
        self.oauth_id = None
        self.server = server
        self.plugin_version = plugin_version
        self._basic_auth = b''
        self._oauth = None
        self.proxy_is_set = False
        self.nam = QgsNetworkAccessManager.instance()
        self.default_error_handler = default_error_handler
        #: Consecutive transient failures of `POLL` requests, by endpoint path.
        self._poll_failures = {}
        #: Timers holding a `BACKGROUND` request's re-send, so logout and `unload` can cancel them.
        self._pending_retries = set()
        #: Set by `close`: the plugin is gone, so a failure arriving late is dropped, not retried.
        self._closed = False

    def setup_auth(self,
                   basic_auth_token: Optional[str] = None,
                   oauth_id: Optional[int] = None):
        if oauth_id:
            if basic_auth_token is not None:
                raise ValueError("Only one auth method (basic auth / oauth2) may be set, got both")
            if self.proxy_is_set:
                # If the proxy is set, the OAuth2 flow will
                raise ProxyIsAlreadySet
            self._setup_oauth(oauth_id)
        elif basic_auth_token:
            # Proxy management blocks oauth2 redirect to browser, so it is activated only for default Basic Auth
            self.nam.setupDefaultProxyAndCache()
            self.proxy_is_set = True
            self.basic_auth = basic_auth_token
        else:
            raise ValueError("One of the auth methods (basic auth / oauth2) must be set, got none")

    def _setup_oauth(self, config_id: str):
        self.oauth_id = config_id
        self._oauth = QgsApplication.authManager()
        auth_config = QgsAuthMethodConfig()
        self._oauth.loadAuthenticationConfig(config_id, auth_config)

    def logout(self):
        if self._oauth:
            self._oauth.clearCachedConfig(self.oauth_id)
            self._oauth = None

        elif self._basic_auth:
            self._basic_auth = b''

    @property
    def basic_auth(self):
        """"""
        return self._basic_auth.decode()

    @basic_auth.setter
    def basic_auth(self, value: str):
        """"""
        self._basic_auth = value.encode()

    def get(self, **kwargs) -> QNetworkReply:
        """Send a GET request."""
        return self.send_request(self.nam.get, **kwargs)

    def post(self, **kwargs) -> QNetworkReply:
        """Send a POST request."""
        return self.send_request(self.nam.post, **kwargs)

    def put(self, **kwargs) -> QNetworkReply:
        """Send a PUT request"""
        return self.send_request(self.nam.put, **kwargs)

    def delete(self, **kwargs) -> QNetworkReply:
        """Send a DELETE request."""
        return self.send_request(self.nam.deleteResource, **kwargs)

    def response_dispatcher(
            self,
            response: QNetworkReply,
            callback: Callable,
            callback_kwargs: dict,
            error_handler: Callable,
            error_handler_kwargs: dict,
            use_default_error_handler: bool,
            mode: RequestMode,
            resend: Optional[Callable],
    ) -> None:
        """Invoke the response callback or the error handler for a finished request.

        Every async response in the plugin passes through here, and it is invoked from
        Qt's event loop via `response.finished`. An exception raised by a callback would
        therefore escape into Qt and surface as QGIS's raw "unhandled exception" dialog,
        which users dismiss without reporting. Guarding at this one point covers every
        network path in the plugin rather than needing a decorator on each callback.

        :param resend: sends this request again; set only on a `BACKGROUND` request's first attempt.
        """
        from .error_guard import call_guarded

        path = _request_path(response)
        if response.error():
            if self._holds_back(response, mode, resend, path):
                return
            if use_default_error_handler:
                if self.default_error_handler(response):
                    return  # a general error occurred and has been handled
            call_guarded(error_handler, f"handling an error response from {path}",
                         self.plugin_version, response, **error_handler_kwargs)
        else:
            # Any success proves the endpoint is back, whichever trigger sent it.
            self._poll_failures.pop(path, None)
            call_guarded(callback, f"processing the response from {path}",
                         self.plugin_version, response, **callback_kwargs)

    def _holds_back(self, response: QNetworkReply, mode: RequestMode, resend: Optional[Callable],
                    path: str) -> bool:
        """Whether this failure is kept from the handlers for now (spec/005 § Request modes).

        Runs outside the guard, on the one connection that is not guarded (`send_request`), so it
        does nothing that can raise beyond reading the reply it was handed.
        """
        error = response.error()
        if mode is RequestMode.INTERACTIVE or error not in TRANSIENT_ERRORS:
            return False
        if mode is RequestMode.BACKGROUND:
            if resend is None:
                return False  # this was the re-send: the failure stands
            if self._closed:
                # A reply that outlived `unload`: there is no plugin left to retry or report for.
                logger.info("Background request to %s failed with Qt error %s after unload; dropped",
                            path, error)
                return True
            logger.warning("Background request to %s failed with Qt error %s; retrying in %s s",
                           path, error, BACKGROUND_RETRY_DELAY_SECONDS)
            self._schedule_resend(resend)
            return True
        failures = self._poll_failures.get(path, 0) + 1
        self._poll_failures[path] = failures
        if failures < POLL_FAILURES_BEFORE_ALERT:
            logger.warning("Polled request to %s failed with Qt error %s (%s in a row); the next "
                           "tick retries", path, error, failures)
            return True
        return False

    def _schedule_resend(self, resend: Callable) -> None:
        from .error_guard import guarded_connect

        timer = QTimer()
        timer.setSingleShot(True)

        def fire():
            self._pending_retries.discard(timer)
            resend()

        guarded_connect(timer.timeout, fire, "retrying a background request", self)
        self._pending_retries.add(timer)
        timer.start(int(BACKGROUND_RETRY_DELAY_SECONDS * 1000))

    def cancel_retries(self) -> None:
        """Drop every scheduled re-send — on logout, where one would go out without credentials."""
        timers, self._pending_retries = self._pending_retries, set()
        for timer in timers:
            timer.stop()

    def close(self) -> None:
        """`unload`'s half: cancel the scheduled re-sends and schedule no more. A re-send firing
        afterwards would run the callbacks of a plugin that has been taken apart
        (spec/007 § The composition root)."""
        self._closed = True
        self.cancel_retries()

    def authorize(self, request: QNetworkRequest, auth: Optional[bytes] = None):
        if auth is not None:
            # Override of autorization, use basic auth
            request.setRawHeader(b'authorization', auth)
        elif self._oauth:
            updated, request = self._oauth.updateNetworkRequest(request, self.oauth_id)
            if not updated:
                raise Exception(f"Failed to apply Auth config to request {request.url}")
        elif self._basic_auth:
            request.setRawHeader(b'authorization', self._basic_auth)
        # else: assume that the request is non-authorized
        return request

    def send_request(
            self,
            method: Callable,
            *,
            mode: RequestMode,
            url: Optional[str] = None,
            path: Optional[str] = None,
            headers: dict = None,
            auth: bytes = None,
            callback: Callable = None,
            callback_kwargs: dict = None,
            error_handler: Optional[Callable] = None,
            error_handler_kwargs: dict = None,
            use_default_error_handler: bool = True,
            timeout: int = DEFAULT_HTTP_TIMEOUT_SECONDS,
            body: Union[QHttpMultiPart, bytes] = None,
            is_resend: bool = False,
    ) -> QNetworkReply:
        """Send an actual request.

        :param mode: when a transient failure reaches the handlers — required, see `RequestMode`.
        :param is_resend: internal; marks a `BACKGROUND` request's second and last attempt.
        """
        if not isinstance(mode, RequestMode):
            raise TypeError(f"mode must be a RequestMode, got {mode!r}")
        if mode is not RequestMode.INTERACTIVE and isinstance(body, QHttpMultiPart):
            raise ValueError("Only an INTERACTIVE request may carry a multipart body: "
                             "the first send consumes it, so it cannot be retried")
        if mode is RequestMode.POLL and error_handler is not None:
            raise ValueError("A POLL request takes no error handler: a dropped failure would "
                             "silently skip it")
        if url is not None and path is not None:
            raise ValueError("Only one of url/path can be specified")
        elif url is None and path is None:
            raise ValueError("url or path must be specified")
        elif path is not None:
            # relative path that is bound to the self.server, allowes to NOT repeat the server loaction
            url = f"{self.server}/{path.lstrip('/')}"

        resend = None
        if mode is RequestMode.BACKGROUND and not is_resend:
            resend = functools.partial(self.send_request, method, mode=mode, url=url, headers=headers,
                                       auth=auth, callback=callback, callback_kwargs=callback_kwargs,
                                       error_handler=error_handler,
                                       error_handler_kwargs=error_handler_kwargs,
                                       use_default_error_handler=use_default_error_handler,
                                       timeout=timeout, body=body, is_resend=True)

        request = QNetworkRequest(QUrl(url))
        if isinstance(body, bytes):
            request.setHeader(QNetworkRequest.ContentTypeHeader, 'application/json')
        if headers:
            for key, value in headers.items():
                request.setRawHeader(key.encode(), value.encode())
        request.setRawHeader(b'x-plugin-version', self.plugin_version.encode())
        try:
            request = self.authorize(request, auth)
        except Exception:
            # Send the request unauthorized; the error response is handled by the caller.
            logger.exception("Request authorization failed, sending unauthorized")

        if method == self.nam.post or method == self.nam.put:
            response = method(request, body)
        elif method == self.nam.deleteResource and body is not None:
            # QNetworkAccessManager.deleteResource() takes no body; a DELETE with a JSON
            # payload (e.g. bulk AOI delete) must go through sendCustomRequest with a
            # QIODevice. Parent the buffer to the reply so it outlives the async request.
            buffer = QBuffer()
            buffer.setData(QByteArray(body))
            buffer.open(QBuffer.ReadOnly)
            response = self.nam.sendCustomRequest(request, b"DELETE", buffer)
            buffer.setParent(response)
        else:
            response = method(request)

        response.finished.connect(lambda response=response,
                                         callback=callback,
                                         callback_kwargs=callback_kwargs or {},
                                         error_handler=error_handler or (lambda _: None),
                                         error_handler_kwargs=error_handler_kwargs or {},
                                         use_default_error_handler=use_default_error_handler,
                                         mode=mode,
                                         resend=resend:
                                  self.response_dispatcher(response=response,
                                                           callback=callback,
                                                           callback_kwargs=callback_kwargs,
                                                           error_handler=error_handler,
                                                           error_handler_kwargs=error_handler_kwargs,
                                                           use_default_error_handler=use_default_error_handler,
                                                           mode=mode,
                                                           resend=resend))

        def abort_request():
            if not response.isFinished():
                response.abort()
        # This closure is also the only thing holding `response` until the timer fires: PyQt exposes
        # a reply that nothing else references as a collectable cycle with its own slots, and a
        # collection mid-request takes the callbacks down with it (see `save_downloaded`, which keeps
        # its replies in a dict for the same reason). Keep an owner if this timer ever goes.
        QTimer.singleShot(timeout * 1000, abort_request)

        return response


def update_processing_limit():
    pass


def default_message_parser(response_body: str) -> str:
    return json.loads(response_body)['message']


def data_catalog_message_parser(response_body: str) -> str:
    error_data = json.loads(response_body)['detail']
    message = ErrorMessage.from_response(error_data)
    return message.to_str()


def api_message_parser(response_body: str) -> str:
    try:
        error_data = json.loads(response_body)
        message = ErrorMessage(code=error_data.get("code", "API_ERROR"),
                            parameters=error_data.get("params", {}),
                            message=error_data.get("message", "Unknown error"))
        return message.to_str()
    except (ValueError, AttributeError, TypeError):
        # Not the standardized error envelope: json.loads raises ValueError
        # (JSONDecodeError) on non-JSON, and .get() raises AttributeError when the payload
        # parses to something other than an object. Callers treat None as "unparseable".
        return None
    except Exception:
        logger.exception("Unexpected error parsing an API error payload")
        return None


#: Report-body formatting moved to `infra/report_body.py` — only one of the two builders was ever
#: about an HTTP response, and neither belongs in the network module. `_request_path`,
#: `response_signature` and the message parsers above stay here: they ARE about a response.
