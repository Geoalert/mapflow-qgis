"""Turns an unexpected exception into a report the user can actually send.

Without this, an exception escaping plugin code has two possible fates, and both lose the
bug report:

* it reaches Qt's event loop and QGIS shows its raw "unhandled exception" dialog — a
  stack trace with a Python traceback the user dismisses, and which names *the plugin*
  without telling them what to do about it;
* or it is caught by a broad handler and written to the QGIS log panel, which is closed
  by default, so nobody ever sees it.

Neither reaches the maintainers. This module routes such failures into the same
``ErrorMessageWidget`` + "Send a report" flow the plugin already uses for HTTP errors,
with the traceback pre-filled in the mail body.

Scope note: this is the *unexpected* path only. Expected exceptions stay narrowly caught
and handled where they occur — surfacing those through a report dialog would train users
to ignore it, which defeats the purpose.
"""
import functools
import logging
from typing import Callable, Optional

from .report_throttle import ReportThrottle, exception_signature

logger = logging.getLogger(__name__)

#: Shown above the traceback in the dialog. Deliberately plain: the user did nothing
#: wrong, and the only useful action is sending the report.
DEFAULT_USER_TEXT = (
    "Mapflow hit an unexpected error and could not finish that action.\n\n"
    "The plugin is still running — you can keep working. Sending the report below helps "
    "us fix it."
)

#: Appended when the same failure recurred while suppressed. A single dialog reads as a
#: one-off glitch; the count is what tells the user (and us) it is systematic.
REPEATED_USER_TEXT = "\n\nThis has happened {count} more time(s) since the last message."

#: Process-wide, because the storm it prevents is process-wide: every guarded call site
#: shares one budget. Tests substitute their own instance rather than reaching in here.
_throttle = ReportThrottle()


def _resolve_plugin_version(obj: object) -> str:
    """Best-effort plugin version from a bound instance.

    Deliberately forgiving: this runs while already handling a failure, so a missing
    attribute must not raise a second exception on top of the first.
    """
    for path in (('plugin_version',), ('app_context', 'plugin_version')):
        target = obj
        for attribute in path:
            target = getattr(target, attribute, None)
            if target is None:
                break
        if isinstance(target, str) and target:
            return target
    return 'unknown'


def report_unexpected_error(exception: BaseException,
                            context: str,
                            plugin_version: str = 'unknown',
                            parent=None) -> None:
    """Log with traceback, then offer the user a pre-filled report.

    Never raises. A reporting path that can fail is worse than none: it would replace the
    original exception with its own, losing the very thing being reported.

    Logging happens for every occurrence; only the *dialog* is throttled. The log is where
    a developer reconstructs how often something fired, so thinning it would trade the one
    complete record for nothing the user benefits from.
    """
    logger.error("Unexpected error during %s", context, exc_info=exception)

    suppressed_count = _throttle.should_report(exception_signature(exception))
    if suppressed_count is None:
        return

    try:
        # Imported here, not at module scope: this module is imported early, and the
        # dialog pulls in the Qt widget tree. Keeping it lazy also means a headless
        # context (tests) can call the logging half without a QApplication.
        from PyQt5.QtWidgets import QApplication
        from .dialogs.error_message_widget import ErrorMessageWidget
        from .http import get_exception_report_body

        summary, email_body = get_exception_report_body(exception, plugin_version, context,
                                                        suppressed_count=suppressed_count)
        text = DEFAULT_USER_TEXT
        if suppressed_count:
            text += REPEATED_USER_TEXT.format(count=suppressed_count)
        widget = ErrorMessageWidget(parent=parent or QApplication.activeWindow(),
                                    text=text,
                                    title=summary,
                                    email_body=email_body)
        widget.show()
    except Exception:
        # The original failure is already in the log above; this only records that the
        # user was not shown it.
        logger.exception("Could not present the error report dialog for: %s", context)


def guard_entry_point(context: str, reraise: bool = False) -> Callable:
    """Decorate a user-action entry point so unexpected failures become reports.

    Apply at boundaries where control enters plugin code from Qt — slots, network
    callbacks, timer handlers — not at internal call sites. An internal guard cannot know
    whether aborting is safe; an entry point always can, because there is nothing above it
    but the event loop.

    ``reraise=True`` reports and then re-raises, for callers that still need the exception
    to propagate.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as exception:
                report_unexpected_error(exception, context, _resolve_plugin_version(self))
                if reraise:
                    raise
                return None
        return wrapper
    return decorator


def call_guarded(func: Callable,
                 context: str,
                 plugin_version: str = 'unknown',
                 *args,
                 **kwargs) -> Optional[object]:
    """Invoke a callable, reporting any unexpected exception. Returns None on failure.

    The function form, for dispatch points that receive a callable rather than owning it —
    see ``Http.response_dispatcher``, where every async response in the plugin is invoked.
    """
    try:
        return func(*args, **kwargs)
    except Exception as exception:
        report_unexpected_error(exception, context, plugin_version)
        return None
