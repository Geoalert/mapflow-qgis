import html
import json
import logging
import traceback
from typing import Callable, Union, Optional
from urllib.parse import quote

from PyQt5.QtCore import QBuffer, QByteArray, QObject, QTimer, QUrl, qVersion
from PyQt5.QtNetwork import QHttpMultiPart, QNetworkReply, QNetworkRequest
from qgis.core import QgsNetworkAccessManager, Qgis, QgsApplication, QgsAuthMethodConfig

from .config import DEFAULT_HTTP_TIMEOUT_SECONDS
from .errors import ErrorMessage, ProxyIsAlreadySet

logger = logging.getLogger(__name__)


def _request_path(response: QNetworkReply) -> str:
    """Endpoint path for an error report — path only, never the full URL.

    Query strings can carry ids and tokens, and this string ends up in a mail body the
    user sends to us. The path is enough to locate the call site.
    """
    try:
        return response.request().url().path() or 'the server'
    except Exception:
        return 'the server'


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
    ) -> None:
        """Invoke the response callback or the error handler for a finished request.

        Every async response in the plugin passes through here, and it is invoked from
        Qt's event loop via `response.finished`. An exception raised by a callback would
        therefore escape into Qt and surface as QGIS's raw "unhandled exception" dialog,
        which users dismiss without reporting. Guarding at this one point covers every
        network path in the plugin rather than needing a decorator on each callback.
        """
        from .error_guard import call_guarded

        if response.error():
            if use_default_error_handler:
                if self.default_error_handler(response):
                    return  # a general error occurred and has been handled
            call_guarded(error_handler, f"handling an error response from {_request_path(response)}",
                         self.plugin_version, response, **error_handler_kwargs)
        else:
            call_guarded(callback, f"processing the response from {_request_path(response)}",
                         self.plugin_version, response, **callback_kwargs)

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
            body: Union[QHttpMultiPart, bytes] = None
    ) -> QNetworkReply:
        """Send an actual request."""
        if url is not None and path is not None:
            raise ValueError("Only one of url/path can be specified")
        elif url is None and path is None:
            raise ValueError("url or path must be specified")
        elif path is not None:
            # relative path that is bound to the self.server, allowes to NOT repeat the server loaction
            url = f"{self.server}/{path.lstrip('/')}"

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
                                         use_default_error_handler=use_default_error_handler:
                                  self.response_dispatcher(response=response,
                                                           callback=callback,
                                                           callback_kwargs=callback_kwargs,
                                                           error_handler=error_handler,
                                                           error_handler_kwargs=error_handler_kwargs,
                                                           use_default_error_handler=use_default_error_handler))

        def abort_request():
            if not response.isFinished():
                response.abort()
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


#: Cap on the traceback carried in a mailto body. Mail clients truncate long URLs (some
#: around 2 KB), and a silently cut report is worse than a deliberately shortened one:
#: the tail frames are where the failure actually happened, so keep those.
MAX_TRACEBACK_LINES = 40


def _environment_report(plugin_version: str) -> dict:
    """Version fields every report carries, regardless of what failed."""
    return {
        'Plugin version': plugin_version,
        'QGIS version': Qgis.QGIS_VERSION,
        'Qt version': qVersion(),
    }


def _format_email_body(report: dict) -> str:
    """Render a report dict into a percent-encoded mailto body.

    The result is interpolated into a `mailto:...&body=` href, so it must be
    percent-encoded: a raw `&` or `#` in a traceback or response body would terminate the
    body parameter and silently truncate the report.
    """
    body = '\n'.join(f'{key}: {value}' for key, value in report.items())
    return quote(body)


def get_error_report_body(response: QNetworkReply,
                          response_body: str,
                          plugin_version: str,
                          error_message_parser: Optional[Callable] = None):
    if error_message_parser is None:
        error_message_parser = default_message_parser
    if response.error() == QNetworkReply.OperationCanceledError:
        send_error_text = show_error_text = 'Request timed out'
    else:
        try:  # handled standardized backend exception ({"code": <int>, "message": <str>})
            show_error_text = error_message_parser(response_body=response_body)
        except Exception:
            # error_message_parser is caller-supplied, so there is no meaningful set of
            # expected exceptions to narrow to — but a parser that raises is a bug worth
            # seeing rather than silently degrading every error to 'Unknown error'.
            logger.exception("Error message parser raised, falling back to plain text")
            show_error_text = 'Unknown error'
        send_error_text = response_body
    report = {
        # escape in case the error text is HTML
        'Error summary': html.escape(send_error_text),
        'URL': response.request().url().toDisplayString(),
        'HTTP code': response.attribute(QNetworkRequest.HttpStatusCodeAttribute),
        'Qt code': response.error(),
        **_environment_report(plugin_version),
    }
    return show_error_text, _format_email_body(report)


def get_exception_report_body(exception: BaseException,
                              plugin_version: str,
                              context: str = '',
                              suppressed_count: int = 0):
    """Build (user-facing text, mailto body) for an unexpected internal exception.

    The counterpart of get_error_report_body for failures that never reached the network.
    Without it, a bug in plugin code either surfaces as QGIS's raw "unhandled exception"
    dialog — which users dismiss and never report — or is logged to a panel nobody opens.
    Routing it here gives the same "send a report" path an HTTP 500 already has.

    `context` names the operation that failed, in user-facing terms, because the exception
    type alone rarely tells the user what they were doing when it happened.

    `suppressed_count` is how many identical failures were hidden since the last report
    (see report_throttle). It changes the triage completely — a failure that fired 200
    times sits on a timer-driven path, which the single traceback cannot reveal.
    """
    summary = f'{type(exception).__name__}: {exception}'
    traceback_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
    traceback_text = ''.join(traceback_lines).rstrip().splitlines()
    if len(traceback_text) > MAX_TRACEBACK_LINES:
        omitted = len(traceback_text) - MAX_TRACEBACK_LINES
        traceback_text = ([f'... {omitted} earlier frame(s) omitted ...']
                          + traceback_text[-MAX_TRACEBACK_LINES:])

    report = {
        'Error summary': html.escape(summary),
        'Operation': context or 'unspecified',
    }
    if suppressed_count:
        report['Repeated'] = f'{suppressed_count} further occurrence(s) suppressed since the last report'
    report.update(_environment_report(plugin_version))
    report['Traceback'] = '\n' + '\n'.join(traceback_text)
    return summary, _format_email_body(report)
