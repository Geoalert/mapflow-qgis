"""How a failed request reaches its handlers depends on its mode (spec/005 § Request modes).

Every request used to be handled on its first failure, so a single timed-out tick of a 6-second
refresh raised "Mapflow is not responding" although nobody was waiting on it and the next tick would
most likely have succeeded. A button the user just pressed is different: a hidden retry there only
adds seconds of silence before the message. So each request now declares which kind it is.

These drive `Http` itself over a fake network manager, and assert on the two things a user can
observe: whether they are told, and whether the request goes out again.
"""
from unittest.mock import MagicMock, patch

import pytest
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QHttpMultiPart, QNetworkReply
from PyQt5.QtTest import QTest
from qgis.core import QgsNetworkAccessManager

from mapflow import http as http_module
from mapflow.http import Http, RequestMode

URL = "https://example.invalid/rest/projects/p-1/processings/v2/page"


class _Reply(QObject):
    finished = pyqtSignal()

    def __init__(self, request):
        super().__init__()
        self._request = request
        self._error = QNetworkReply.NoError
        self._finished = False

    def error(self):
        return self._error

    def errorString(self):
        return "network error"

    def request(self):
        return self._request

    def readAll(self):
        return b""

    def isFinished(self):
        return self._finished

    def abort(self):
        self._finished = True

    def complete(self, error):
        self._error = error
        self._finished = True
        self.finished.emit()


class _Network:
    """The slice of `QgsNetworkAccessManager` `Http` uses. Replies wait until a test answers them."""

    def __init__(self):
        self.sent = []  # (verb, url, body) per request, in order
        self._pending = []

    def get(self, request):
        return self._send("GET", request, None)

    def post(self, request, body=None):
        return self._send("POST", request, body)

    def put(self, request, body=None):
        return self._send("PUT", request, body)

    def deleteResource(self, request):
        return self._send("DELETE", request, None)

    def _send(self, verb, request, body):
        self.sent.append((verb, request.url().toString(), body))
        reply = _Reply(request)
        self._pending.append(reply)
        return reply

    def answer(self, error=QNetworkReply.NoError):
        """Complete the oldest outstanding request with `error` (NoError is a success)."""
        self._pending.pop(0).complete(error)


@pytest.fixture
def network():
    return _Network()


@pytest.fixture
def http(network, monkeypatch):
    monkeypatch.setattr(http_module, "BACKGROUND_RETRY_DELAY_SECONDS", 0)
    with patch.object(QgsNetworkAccessManager, "instance", staticmethod(lambda: network)):
        instance = Http(server="https://example.invalid/rest", plugin_version="3.7.0",
                        default_error_handler=MagicMock(return_value=True))
    yield instance
    instance.close()


def _let_a_retry_fire():
    QTest.qWait(50)


# ---------- the mode is required ----------

def test_a_request_without_a_mode_is_refused(http, network):
    with pytest.raises(TypeError):
        http.get(url=URL, callback=MagicMock())
    assert network.sent == [], "an unclassified request must not reach the network"


def test_a_mode_that_is_not_a_request_mode_is_refused(http, network):
    with pytest.raises(TypeError):
        http.get(url=URL, callback=MagicMock(), mode="poll")
    assert network.sent == []


# ---------- INTERACTIVE ----------

def test_an_interactive_failure_is_handled_at_once_and_not_sent_again(http, network):
    http.get(url=URL, callback=MagicMock(), mode=RequestMode.INTERACTIVE)

    network.answer(QNetworkReply.OperationCanceledError)
    _let_a_retry_fire()

    http.default_error_handler.assert_called_once()
    assert len(network.sent) == 1


# ---------- BACKGROUND ----------

def test_a_background_failure_is_sent_again_before_anyone_is_told(http, network):
    http.post(url=URL, body=b'{"limit": 20}', headers={"x-test": "1"}, callback=MagicMock(),
              mode=RequestMode.BACKGROUND)

    network.answer(QNetworkReply.ServiceUnavailableError)
    http.default_error_handler.assert_not_called()
    _let_a_retry_fire()

    assert network.sent == [("POST", URL, b'{"limit": 20}')] * 2, "the same request, once more"


def test_a_background_failure_is_handled_once_when_the_retry_fails_too(http, network):
    http.get(url=URL, callback=MagicMock(), mode=RequestMode.BACKGROUND)

    network.answer(QNetworkReply.OperationCanceledError)
    _let_a_retry_fire()
    network.answer(QNetworkReply.OperationCanceledError)
    _let_a_retry_fire()

    http.default_error_handler.assert_called_once()
    assert len(network.sent) == 2, "one retry, not a loop"


def test_a_background_request_whose_retry_succeeds_reaches_only_its_callback(http, network):
    callback = MagicMock()
    error_handler = MagicMock()
    http.get(url=URL, callback=callback, error_handler=error_handler,
             use_default_error_handler=False, mode=RequestMode.BACKGROUND)

    network.answer(QNetworkReply.RemoteHostClosedError)
    _let_a_retry_fire()
    network.answer()

    callback.assert_called_once()
    error_handler.assert_not_called()


def test_a_background_requests_own_error_handler_runs_once_after_the_retry(http, network):
    error_handler = MagicMock()
    http.get(url=URL, callback=MagicMock(), error_handler=error_handler,
             use_default_error_handler=False, mode=RequestMode.BACKGROUND)

    network.answer(QNetworkReply.HostNotFoundError)
    _let_a_retry_fire()
    error_handler.assert_not_called()
    network.answer(QNetworkReply.HostNotFoundError)

    error_handler.assert_called_once()


@pytest.mark.parametrize("error", [
    QNetworkReply.AuthenticationRequiredError,  # 401
    QNetworkReply.ContentAccessDenied,  # 403
    QNetworkReply.ContentNotFoundError,  # 404
    QNetworkReply.UnknownContentError,  # other 4xx
])
def test_a_failure_asking_again_cannot_fix_is_handled_at_once_in_the_background(http, network, error):
    http.get(url=URL, callback=MagicMock(), mode=RequestMode.BACKGROUND)

    network.answer(error)
    _let_a_retry_fire()

    http.default_error_handler.assert_called_once()
    assert len(network.sent) == 1


@pytest.mark.parametrize("stop", ["cancel_retries", "close"])  # logout, unload
def test_a_pending_retry_can_be_cancelled(http, network, monkeypatch, stop):
    monkeypatch.setattr(http_module, "BACKGROUND_RETRY_DELAY_SECONDS", 0.05)
    http.get(url=URL, callback=MagicMock(), mode=RequestMode.BACKGROUND)
    network.answer(QNetworkReply.OperationCanceledError)

    getattr(http, stop)()
    QTest.qWait(150)

    assert len(network.sent) == 1, "a retry after logout or unload runs without a session or a plugin"
    http.default_error_handler.assert_not_called()


def test_a_reply_that_fails_after_unload_is_not_retried(http, network):
    """`close` stops the timers that exist; a request still in flight at unload fails afterwards and
    would otherwise schedule a new one against the dismantled plugin."""
    http.get(url=URL, callback=MagicMock(), mode=RequestMode.BACKGROUND)

    http.close()
    network.answer(QNetworkReply.OperationCanceledError)
    _let_a_retry_fire()

    assert len(network.sent) == 1


def test_logout_does_not_stop_later_requests_from_retrying(http, network):
    http.cancel_retries()
    http.get(url=URL, callback=MagicMock(), mode=RequestMode.BACKGROUND)

    network.answer(QNetworkReply.OperationCanceledError)
    _let_a_retry_fire()

    assert len(network.sent) == 2, "the next session's requests keep their retry"


# ---------- POLL ----------

def test_a_single_poll_failure_is_dropped(http, network):
    callback = MagicMock()
    http.get(url=URL, callback=callback, mode=RequestMode.POLL)

    network.answer(QNetworkReply.OperationCanceledError)
    _let_a_retry_fire()

    http.default_error_handler.assert_not_called()
    callback.assert_not_called()
    assert len(network.sent) == 1, "the timer is the retry; Http sends nothing on its own"


def test_a_poll_failure_is_handled_once_the_next_tick_fails_too(http, network):
    for _ in range(2):  # two ticks
        http.get(url=URL, callback=MagicMock(), mode=RequestMode.POLL)
        network.answer(QNetworkReply.OperationCanceledError)

    http.default_error_handler.assert_called_once()


def test_a_success_in_between_resets_the_count(http, network):
    for outcome in (QNetworkReply.OperationCanceledError, QNetworkReply.NoError,
                    QNetworkReply.OperationCanceledError):
        http.get(url=URL, callback=MagicMock(), mode=RequestMode.POLL)
        network.answer(outcome)

    http.default_error_handler.assert_not_called()


def test_a_success_from_any_trigger_resets_the_count(http, network):
    """The user paging the same table proves the endpoint is back as well as a tick does."""
    http.get(url=URL, callback=MagicMock(), mode=RequestMode.POLL)
    network.answer(QNetworkReply.OperationCanceledError)
    http.get(url=URL, callback=MagicMock(), mode=RequestMode.INTERACTIVE)
    network.answer()
    http.get(url=URL, callback=MagicMock(), mode=RequestMode.POLL)
    network.answer(QNetworkReply.OperationCanceledError)

    http.default_error_handler.assert_not_called()


def test_poll_failures_are_counted_per_endpoint(http, network):
    http.get(url=URL, callback=MagicMock(), mode=RequestMode.POLL)
    network.answer(QNetworkReply.OperationCanceledError)
    http.get(url="https://example.invalid/rest/user/status", callback=MagicMock(),
             mode=RequestMode.POLL)
    network.answer(QNetworkReply.OperationCanceledError)

    http.default_error_handler.assert_not_called()


def test_a_poll_failure_asking_again_cannot_fix_is_handled_at_once(http, network):
    http.get(url=URL, callback=MagicMock(), mode=RequestMode.POLL)

    network.answer(QNetworkReply.ContentAccessDenied)

    http.default_error_handler.assert_called_once()


# ---------- declarations the modes cannot honour ----------

def test_a_poll_request_takes_no_error_handler(http, network):
    """A dropped failure runs neither the callback nor the handler, so cleanup placed in a POLL
    request's handler would silently not run."""
    with pytest.raises(ValueError):
        http.get(url=URL, callback=MagicMock(), error_handler=MagicMock(), mode=RequestMode.POLL)
    assert network.sent == []


@pytest.mark.parametrize("mode", [RequestMode.BACKGROUND, RequestMode.POLL])
def test_only_an_interactive_request_may_carry_a_multipart_body(http, network, mode):
    """The first send consumes a multipart body, so a request carrying one cannot be retried."""
    with pytest.raises(ValueError):
        http.post(url=URL, body=QHttpMultiPart(), callback=MagicMock(), mode=mode)
    assert network.sent == []
