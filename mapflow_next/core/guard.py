"""The guard: no exception escapes from an entry point that Qt calls into.

Slots, timers, `lambda`s connected to signals and the callbacks `Http` runs are wrapped with `guarded`.
An exception is reported through one reporter and swallowed, so QGIS never shows its raw error dialog and
the plugin keeps working.

This module is in `core/`, and has no Qt and no qgis import, because `core/` is the one package that every
layer may import (the controller, the services, `plugin.py`, `api/http.py` and `ui/`). The reporter is the
Qt side: `plugin.py` installs one that writes to the QGIS log and shows the Critical line with its
"Send a report" button on the message bar. Do not import Qt here to
report directly: `api/` and `ui/` import this module, and the layer rules of `spec/007` would break.
"""
from __future__ import annotations

import functools
import inspect
import sys
import traceback
from typing import Callable, Optional

from .report import RequestInfo

# (the exception, its details, the request that failed or None)
Reporter = Callable[[BaseException, str, Optional[RequestInfo]], None]

_reporter: Optional[Reporter] = None


def set_reporter(reporter: Reporter) -> None:
    global _reporter
    _reporter = reporter


def clear_reporter(reporter: Reporter) -> None:
    """Remove `reporter` only if it is the installed one: a plugin that is reloaded builds the new
    instance before the old one unloads, and the old `unload` must not remove the new reporter."""
    global _reporter
    if _reporter == reporter:
        _reporter = None


def report(exc: BaseException, where: str = "", request: Optional[RequestInfo] = None) -> None:
    """Hand `exc` to the reporter, with the request that failed when there is one (the report carries its method,
    URL without query, status and response body). Never raises: without a reporter, or when the reporter itself
    fails, the details go to stderr."""
    details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    if where:
        details = f"{where}\n{details}"
    reporter = _reporter
    try:
        if reporter is None:
            raise RuntimeError("no reporter installed")
        reporter(exc, details, request)
    except Exception:  # noqa: BLE001 - the guard is the last line: it must not raise
        print(details, file=sys.stderr)


def _positional_limit(fn) -> Optional[int]:
    """How many positional arguments `fn` takes; None for any number."""
    try:
        parameters = inspect.signature(fn).parameters.values()
    except (TypeError, ValueError):
        return None
    limit = 0
    for parameter in parameters:
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            return None
        if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            limit += 1
    return limit


def guarded(fn):
    """Wrap `fn` so that an `Exception` is reported and swallowed (`None` is returned). Use it as `@guarded`
    on a method, or as `guarded(lambda ...)` / `guarded(other.method)` at a connection site.

    Arguments beyond what `fn` takes are dropped. PyQt retries a plain slot with fewer arguments when the
    signal sends more than the slot takes (`lambda: ...` on `clicked(bool)`); a `*args` wrapper would hide
    that retry, and the resulting `TypeError` would be reported as a failure."""
    limit = _positional_limit(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*(args if limit is None else args[:limit]), **kwargs)
        except Exception as exc:  # noqa: BLE001 - the last line of defence for Qt entry points
            report(exc, getattr(fn, "__qualname__", repr(fn)))
            return None
    return wrapper
