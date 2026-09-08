"""The report tier of `spec/006_error_reporting.md`: the single place that turns a failure — an
unexpected exception, or an HTTP error response — into a "Send a report" dialog, under one
suppression budget.

Both report paths live here, behind one `_throttle`, because the volume contract's global floor
holds "between any two reports regardless of signature": an HTTP error and an exception can rotate
through the same poll callback, and two separate throttles would let both fire inside the floor.
One budget needs one owner.

Qt-free at import time on purpose (only `report_throttle` + typing): it is imported early and by
`error_guard`, and the dialog it eventually shows is pulled in lazily inside the functions, so a
headless context can call the logging/throttle half without a QApplication.
"""
import logging
from typing import Callable, Optional

from ..report_throttle import ReportThrottle, exception_signature
from ..http import response_signature
from .report_body import get_error_report_body, get_exception_report_body

logger = logging.getLogger(__name__)

#: Shown above the traceback in the dialog. Deliberately plain: the user did nothing wrong, and the
#: only useful action is sending the report.
DEFAULT_USER_TEXT = (
    "Mapflow hit an unexpected error and could not finish that action.\n\n"
    "The plugin is still running — you can keep working. Sending the report below helps "
    "us fix it."
)

#: Appended when the same failure recurred while suppressed. A single dialog reads as a one-off
#: glitch; the count is what tells the user (and us) it is systematic.
REPEATED_USER_TEXT = "\n\nThis has happened {count} more time(s) since the last message."

#: Process-wide, shared by BOTH report paths — that is what makes the global floor hold across
#: tiers. Tests substitute their own instance rather than reaching in here.
_throttle = ReportThrottle()


def configure_throttle(first_window: float, max_window: float,
                       global_floor: float, backoff: float) -> None:
    """Rebuild the report-tier budget from config values; called once at startup by the composition
    root. Qt-free like the rest of this module — it only constructs a ReportThrottle, and the caller
    passes the numbers because this module cannot import the QGIS-bound config itself.
    """
    global _throttle
    _throttle = ReportThrottle(first_window=first_window, max_window=max_window,
                               global_floor=global_floor, backoff=backoff)


def _present(text: str, title: str = None, email_body: str = '', parent=None) -> None:
    """Show the report dialog. Never raises — it runs while already handling a failure, so an
    exception escaping here would replace the failure being reported with its own.

    The widget import stays local: it is the reporter's one true Qt-widget-tree dependency, and
    keeping it here lets the report logic above (throttle, signature, body) be imported and
    unit-tested with no widget/.ui machinery — the tests patch this function. The widget retains
    itself until closed (see `ErrorMessageWidget`), so nothing here keeps a reference.
    """
    try:
        from PyQt5.QtWidgets import QApplication
        from ..dialogs.error_message_widget import ErrorMessageWidget
        ErrorMessageWidget(parent=parent or QApplication.activeWindow(),
                           text=text,
                           title=title,
                           email_body=email_body).show()
    except Exception:
        logger.exception("Could not present the error report dialog")


def report_unexpected_error(exception: BaseException,
                            context: str,
                            plugin_version: str = 'unknown',
                            parent=None) -> None:
    """Log with traceback, then offer the user a pre-filled report.

    Logging happens for every occurrence; only the *dialog* is throttled. The log is where a
    developer reconstructs how often something fired, so thinning it would trade the one complete
    record for nothing the user benefits from.
    """
    logger.error("Unexpected error during %s", context, exc_info=exception)

    suppressed_count = _throttle.should_report(exception_signature(exception))
    if suppressed_count is None:
        return

    try:
        summary, email_body = get_exception_report_body(exception, plugin_version, context,
                                                        suppressed_count=suppressed_count)
        text = DEFAULT_USER_TEXT
        if suppressed_count:
            text += REPEATED_USER_TEXT.format(count=suppressed_count)
        _present(text=text, title=summary, email_body=email_body, parent=parent)
    except Exception:
        # The original failure is already in the log above; this only records that the user was
        # not shown it.
        logger.exception("Could not build the error report for: %s", context)


def report_http_error(response,
                      plugin_version: str,
                      title: str = None,
                      error_message_parser: Optional[Callable] = None,
                      response_body: Optional[str] = None) -> None:
    """Report an HTTP error response, throttled by the same budget as the exception path.

    `response_body` lets a caller that has already read the reply hand it over: `readAll()` drains
    the buffer, so a caller that inspected the body itself must pass it here or the report would
    decode an empty one.
    """
    signature = response_signature(response)
    # Log every occurrence, before the throttle — suppression governs the dialog, never the log.
    logger.error("HTTP error: %s", signature)

    suppressed_count = _throttle.should_report(signature)
    if suppressed_count is None:
        return

    try:
        body = response.readAll().data().decode() if response_body is None else response_body
        error_summary, email_body = get_error_report_body(
            response=response,
            response_body=body,
            plugin_version=plugin_version,
            error_message_parser=error_message_parser,
            suppressed_count=suppressed_count)
        if suppressed_count:
            error_summary += REPEATED_USER_TEXT.format(count=suppressed_count)
        _present(text=error_summary, title=title, email_body=email_body)
    except Exception:
        logger.exception("Could not present the HTTP error report: %s", signature)
