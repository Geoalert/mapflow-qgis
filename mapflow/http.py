from typing import Callable, Union

from PyQt5.QtCore import QObject, QTimer, QUrl
from PyQt5.QtNetwork import QHttpMultiPart, QNetworkReply, QNetworkRequest
from qgis.core import QgsNetworkAccessManager

from . import config


class Http(QObject):
    """"""

    def __init__(self, plugin_version: str, default_error_handler: Callable) -> None:
        """"""
        self.nam = QgsNetworkAccessManager.instance()
        self.nam.setupDefaultProxyAndCache()
        self.plugin_version = plugin_version
        self._basic_auth = b''
        self.default_error_handler = default_error_handler

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
        use_default_error_handler: bool
    ) -> None:
        """"""
        if response.error():
            if use_default_error_handler:
                if self.default_error_handler(response):
                    return  # a general error occurred and has been handled
            error_handler(response, **error_handler_kwargs)  # handle specific errors
        else:
            callback(response, **callback_kwargs)

    def send_request(
        self,
        method: Callable,
        url: str,
        headers: dict = None,
        auth: bytes = None,
        callback: Callable = None,
        callback_kwargs: dict = None,
        error_handler: Callable = None,
        error_handler_kwargs: dict = None,
        use_default_error_handler: bool = True,
        timeout: int = config.MAPFLOW_DEFAULT_TIMEOUT,
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
        request.setRawHeader(b'authorization', auth or self._basic_auth)
        response = method(request, body) if method == self.nam.post else method(request)
        QTimer.singleShot(timeout * 1000, response.abort)
        response.finished.connect(
            lambda
            response=response,
            callback=callback,
            callback_kwargs=callback_kwargs or {},
            error_handler=error_handler or (lambda _: None),
            error_handler_kwargs=error_handler_kwargs or {},
            use_default_error_handler=use_default_error_handler:
            self.response_dispatcher(
                response,
                callback,
                callback_kwargs,
                error_handler,
                error_handler_kwargs,
                use_default_error_handler
            )
        )
        return response
