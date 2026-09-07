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

# The reporting itself lives in the infra report tier, behind a single throttle shared with the
# HTTP report path (spec/006 § Where each tier lives). This module keeps only the entry-point
# guards below; `report_unexpected_error` is re-exported so both the guards here and any
# `from mapflow.error_guard import report_unexpected_error` caller keep resolving the bare name.
from .infra.reporter import report_unexpected_error

logger = logging.getLogger(__name__)


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
