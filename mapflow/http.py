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

    def send_request(
        self,
        method: Callable,
        url: str,
        callback: Callable = None,
        error_handler: Callable = None,
        basic_auth: bytes = None,
        timeout: int = config.MAPFLOW_DEFAULT_TIMEOUT,
        body: Union[QHttpMultiPart, bytes] = None
    ) -> QNetworkReply:
        """Send an actual request."""
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, 'application/json')
        request.setRawHeader(b'X-Plugin-Version', self.plugin_version.encode())
        request.setRawHeader(b'Authorization', basic_auth or self._basic_auth)
        timer = QTimer()
        timer.setSingleShot(True)
        timer.setInterval(timeout * 1000)  # seconds -> milliseconds
        response = method(request, body) if method == self.nam.post else method(request)
        response.finished.connect(callback)
        response.finished.connect(error_handler or self.default_error_handler)
        return response
