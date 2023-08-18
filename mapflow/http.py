import html
import json
from typing import Callable, Union, Optional

from PyQt5.QtCore import QObject, QTimer, QUrl, qVersion
from PyQt5.QtNetwork import QHttpMultiPart, QNetworkReply, QNetworkRequest
from qgis.core import QgsNetworkAccessManager, Qgis


import logging
from .constants import DEFAULT_HTTP_TIMEOUT_SECONDS
from .errors import ErrorMessage, ErrorMessageList


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
        error_message_parser: Optional[Callable] = None,
    ) -> None:
        """"""
        if response.error():
            if use_default_error_handler:
                if self.default_error_handler(response,
                                              error_message_parser=error_message_parser):
                    return  # a general error occurred and has been handled
            error_handler(response,
                          error_message_parser=error_message_parser,
                          **error_handler_kwargs)  # handle specific errors
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
        error_handler: Optional[Callable] = None,
        error_message_parser: Optional[Callable] = None,
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
        request.setRawHeader(b'authorization', auth or self._basic_auth)
        response = method(request, body) if (method == self.nam.post or method == self.nam.put) else method(request)
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
                error_message_parser,
                error_handler_kwargs,
                use_default_error_handler
            )
        )
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