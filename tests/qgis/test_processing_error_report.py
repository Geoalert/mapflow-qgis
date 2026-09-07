"""QGIS-tier tests: ProcessingService reports HTTP errors through the infra reporter, not by
building the dialog itself (error-reporting phase, MR-2).

`start_processing_error_handler` used to construct `ErrorMessageWidget` inline — a service reaching
for a dialog. It now hands the failure to `report_http_error` in `mapflow.infra`. The subtlety this
pins: the handler reads the reply body itself (to spot the "data provider" case), and `readAll`
drains the buffer, so it must pass that body to the reporter rather than let it re-read an empty one.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PyQt5.QtCore import QObject
from PyQt5.QtNetwork import QNetworkReply

from mapflow.functional.service import processing_service as processing_service_module
from mapflow.functional.service.processing_service import ProcessingService


def _service():
    service = ProcessingService.__new__(ProcessingService)
    QObject.__init__(service)
    service.tr = lambda text: text
    service.app_context = SimpleNamespace(plugin_version="9.9.9",
                                          allow_enable_processing={"aoi_loaded": True})
    return service


def _response(body: bytes, error=QNetworkReply.UnknownContentError):
    response = MagicMock()
    response.error.return_value = error
    response.readAll.return_value.data.return_value = body
    return response


def test_a_generic_error_is_reported_through_the_infra_reporter():
    service = _service()
    response = _response(b'{"code": "BAD_REQUEST", "message": "no"}')

    with patch.object(processing_service_module, "report_http_error") as report:
        service.start_processing_error_handler(response)

    report.assert_called_once()
    kwargs = report.call_args.kwargs
    assert kwargs["response"] is response
    assert kwargs["plugin_version"] == "9.9.9"
    # The body was read once by the handler and handed over, not re-read (readAll has drained it).
    assert kwargs["response_body"] == '{"code": "BAD_REQUEST", "message": "no"}'
    assert kwargs["error_message_parser"] is processing_service_module.api_message_parser


def test_the_data_provider_case_alerts_and_does_not_report():
    """An unavailable data provider is an expected, actionable message — an info alert, not a
    'something went wrong, mail us' report."""
    service = _service()
    response = _response(b'the data provider is not on your plan',
                         error=QNetworkReply.ContentAccessDenied)
    alerts = []

    with patch.object(processing_service_module, "report_http_error") as report, \
            patch.object(processing_service_module, "alert_info", lambda *a, **k: alerts.append(a)):
        service.start_processing_error_handler(response)

    report.assert_not_called()
    assert alerts  # the upgrade-your-plan message was shown


def test_the_button_is_re_enabled_after_a_report():
    service = _service()
    in_flight = []
    service.submissionInFlight.connect(in_flight.append)

    with patch.object(processing_service_module, "report_http_error"):
        service.start_processing_error_handler(_response(b"{}"))

    assert in_flight == [False]
