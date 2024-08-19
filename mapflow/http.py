import html
import json
from typing import Callable, Union, Optional

from PyQt5.QtCore import QObject, QTimer, QUrl, qVersion
from PyQt5.QtNetwork import QHttpMultiPart, QNetworkReply, QNetworkRequest
from qgis.core import QgsNetworkAccessManager, Qgis, QgsApplication, QgsAuthMethodConfig

from .constants import DEFAULT_HTTP_TIMEOUT_SECONDS
from .errors import ErrorMessage, ProxyIsAlreadySet


class Http(QObject):
    """"""

    def __init__(self,
                 plugin_version: str,
                 default_error_handler: Callable) -> None:
        """
        oauth_id is defined if we are using oauth2 configuration
        """
        self.oauth_id = None
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
        """"""
        if response.error():
            if use_default_error_handler:
                if self.default_error_handler(response):
                    return  # a general error occurred and has been handled
            error_handler(response,
                          **error_handler_kwargs)  # handle specific errors
        else:
            callback(response, **callback_kwargs)

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
            url: str,
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
        request = QNetworkRequest(QUrl(url))
        if isinstance(body, bytes):
            request.setHeader(QNetworkRequest.ContentTypeHeader, 'application/json')
        if headers:
            for key, value in headers.items():
                request.setRawHeader(key.encode(), value.encode())
        request.setRawHeader(b'x-plugin-version', self.plugin_version.encode())
        try:
            request = self.authorize(request, auth)
        except Exception as e:
            # We skip the exception handling, then the request goes out unauthorized and the error response is handled
            pass

        response = method(request, body) if (method == self.nam.post or method == self.nam.put) else method(request)

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
    error_data = json.loads(response_body)
    message = ErrorMessage(code=error_data.get("code", "API_ERROR"),
                           parameters=error_data.get("parameters", {}),
                           message=error_data.get("message", "Unknown error"))
    return message.to_str()


def securewatch_message_parser(response_body: str) -> str:
    # todo: parse this HTML page for useful info, or display it as is?
    return response_body


def get_error_report_body(response: QNetworkReply,
                          plugin_version: str,
                          error_message_parser: Optional[Callable] = None):
    if error_message_parser is None:
        error_message_parser = default_message_parser
    if response.error() == QNetworkReply.OperationCanceledError:
        send_error_text = show_error_text = 'Request timed out'
    else:
        response_body = response.readAll().data().decode()
        try:  # handled standardized backend exception ({"code": <int>, "message": <str>})
            show_error_text = error_message_parser(response_body=response_body)
        except:  # unhandled error - plain text
            show_error_text = 'Unknown error'
        send_error_text = response_body
    report = {
        # escape in case the error text is HTML
        'Error summary': html.escape(send_error_text),
        'URL': response.request().url().toDisplayString(),
        'HTTP code': response.attribute(QNetworkRequest.HttpStatusCodeAttribute),
        'Qt code': response.error(),
        'Plugin version': plugin_version,
        'QGIS version': Qgis.QGIS_VERSION,
        'Qt version': qVersion(),
    }
    email_body = '%0a'.join(f'{key}: {value}' for key, value in report.items())

    return show_error_text, email_body
