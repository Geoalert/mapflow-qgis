"""`Mapflow.default_error_handler` sorts a network error into a tier (error-reporting Fix E).

spec/006 reserves the report tier ("Send a report") for unexpected failures — the plugin being
wrong. A dropped connection, an unreachable server, a proxy misconfiguration or a rights refusal is
expected and user-actionable, so it belongs in the message tier (a plain, throttled alert). Before
this, most of them opened a report dialog, and `UnknownNetworkError` — Qt's catch-all for a
connection lost mid-request — was mislabelled "Proxy error" for users who had no proxy at all.

Only a genuinely unclassified error still offers a report.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt5.QtNetwork import QNetworkReply

from mapflow.mapflow import Mapflow


def _plugin():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.alert = MagicMock()
    plugin.report_http_error = MagicMock()
    return plugin


def _response(error):
    response = MagicMock()
    response.error.return_value = error
    response.errorString.return_value = "network error"
    return response


CONNECTIVITY_ERRORS = [
    QNetworkReply.OperationCanceledError,     # timeout
    QNetworkReply.ServiceUnavailableError,    # 503
    QNetworkReply.InternalServerError,        # 500 — message tier by user decision, not a report
    QNetworkReply.ConnectionRefusedError,
    QNetworkReply.RemoteHostClosedError,
    QNetworkReply.NetworkSessionFailedError,
    QNetworkReply.HostNotFoundError,          # offline
    QNetworkReply.UnknownNetworkError,        # connection lost mid-request
    QNetworkReply.ProxyConnectionRefusedError,
    QNetworkReply.ProxyAuthenticationRequiredError,
]


@pytest.mark.parametrize("error", CONNECTIVITY_ERRORS)
def test_connectivity_errors_use_the_message_tier_not_a_report(error):
    plugin = _plugin()

    handled = plugin.default_error_handler(_response(error))

    assert handled is True
    plugin.alert.assert_called_once()             # message tier — a plain alert
    plugin.report_http_error.assert_not_called()  # never the report tier's "Send a report"


def test_unknown_network_error_does_not_blame_the_proxy():
    plugin = _plugin()

    plugin.default_error_handler(_response(QNetworkReply.UnknownNetworkError))

    message = plugin.alert.call_args.args[0]
    assert "proxy" not in message.lower()  # it is a lost connection, not a proxy problem


def test_content_access_denied_uses_the_message_tier():
    plugin = _plugin()
    plugin.app_context = SimpleNamespace(
        user_role=SimpleNamespace(can_delete_rename_project=True, value="viewer"),
        current_project=SimpleNamespace(name="Shared project"))

    handled = plugin.default_error_handler(_response(QNetworkReply.ContentAccessDenied))

    assert handled is True
    plugin.alert.assert_called_once()
    plugin.report_http_error.assert_not_called()


def test_an_unclassified_error_still_offers_a_report():
    plugin = _plugin()

    handled = plugin.default_error_handler(_response(QNetworkReply.UnknownContentError))

    assert handled is False                          # unhandled -> the request's own handler runs
    plugin.report_http_error.assert_called_once()    # genuinely unexpected -> report tier
    plugin.alert.assert_not_called()
