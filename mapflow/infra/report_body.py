"""Formatting a failure into a report body (`spec/006_error_reporting.md`, the report tier).

Both builders live here, next to the reporter that uses them, rather than in `http`: only one of
them is about an HTTP response, and the other — an internal exception with a traceback — has nothing
to do with the network. What they share is turning a failure into the percent-encoded mailto body
the "send a report" dialog carries. `http` keeps the pieces that ARE about a response (`_request_path`,
`response_signature`, the message parsers); this imports the two it needs from there.
"""
import html
import logging
import traceback
from typing import Callable, Optional
from urllib.parse import quote

from PyQt5.QtCore import qVersion
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest
from qgis.core import Qgis

from ..http import _request_path, default_message_parser

logger = logging.getLogger(__name__)

#: Cap on the traceback carried in a mailto body. Mail clients truncate long URLs (some around
#: 2 KB), and a silently cut report is worse than a deliberately shortened one: the tail frames are
#: where the failure actually happened, so keep those.
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

    The result is interpolated into a `mailto:...&body=` href, so it must be percent-encoded: a raw
    `&` or `#` in a traceback or response body would terminate the body parameter and silently
    truncate the report.
    """
    body = '\n'.join(f'{key}: {value}' for key, value in report.items())
    return quote(body)


def get_error_report_body(response: QNetworkReply,
                          response_body: str,
                          plugin_version: str,
                          error_message_parser: Optional[Callable] = None,
                          suppressed_count: int = 0):
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
        # The path only, never the full URL: the signature keys on this same string, and a query
        # would carry ids and tokens into a mail body the user sends us (see `_request_path`).
        'URL': _request_path(response),
        'HTTP code': response.attribute(QNetworkRequest.HttpStatusCodeAttribute),
        'Qt code': response.error(),
    }
    # Same wording as the exception path: a failure that fired 200 times sits on a timer, which a
    # single dialog cannot reveal.
    if suppressed_count:
        report['Repeated'] = f'{suppressed_count} further occurrence(s) suppressed since the last report'
    report.update(_environment_report(plugin_version))
    return show_error_text, _format_email_body(report)


def get_exception_report_body(exception: BaseException,
                              plugin_version: str,
                              context: str = '',
                              suppressed_count: int = 0):
    """Build (user-facing text, mailto body) for an unexpected internal exception.

    The counterpart of get_error_report_body for failures that never reached the network. Without
    it, a bug in plugin code either surfaces as QGIS's raw "unhandled exception" dialog — which
    users dismiss and never report — or is logged to a panel nobody opens. Routing it here gives the
    same "send a report" path an HTTP 500 already has.

    `context` names the operation that failed, in user-facing terms, because the exception type
    alone rarely tells the user what they were doing when it happened.

    `suppressed_count` is how many identical failures were hidden since the last report (see
    report_throttle). It changes the triage completely — a failure that fired 200 times sits on a
    timer-driven path, which the single traceback cannot reveal.
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
