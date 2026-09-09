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
import inspect
import logging
from typing import Callable, Optional

# The reporting itself lives in the infra report tier, behind a single throttle shared with the
# HTTP report path (spec/006 § Where each tier lives). This module keeps only the entry-point
# guards below; `report_unexpected_error` is re-exported so both the guards here and any
# `from mapflow.error_guard import report_unexpected_error` caller keep resolving the bare name.
from .infra.reporter import report_unexpected_error

logger = logging.getLogger(__name__)

#: The running plugin version, recorded once at startup by `Mapflow.__init__` (it parses
#: metadata.txt). `_resolve_plugin_version` falls back to this when the object a guard was given
#: carries no version of its own: dialogs and views hold neither `plugin_version` nor `app_context`,
#: so every report raised from a widget slot used to arrive saying "unknown" — the one field that
#: makes a report actionable, missing on a whole tier of them.
_plugin_version: Optional[str] = None


def set_plugin_version(version: str) -> None:
    """Record the running plugin version for reports raised where no version source is at hand.

    Module state rather than an argument threaded through every `guarded_connect` call: the version
    is a property of the running plugin, identical for every report, and the alternative is handing
    it to widgets that otherwise have no reason to know it.
    """
    global _plugin_version
    if isinstance(version, str) and version:
        _plugin_version = version


def _attribute_or_none(obj: object, attribute: str):
    """`getattr` that cannot raise.

    `getattr(x, name, default)` only swallows AttributeError, and the default is no help against
    anything else: a sip-wrapped Qt object whose C++ base was never constructed raises RuntimeError
    on any attribute access, and a property can raise whatever it likes. This is reached while a
    failure is already being reported, so an exception escaping here would both replace that failure
    with its own and escape the guard to the event loop — turning one bug into exactly the unguarded
    crash the guard exists to prevent.
    """
    try:
        return getattr(obj, attribute, None)
    except Exception as error:
        # Debug, not error: the report this feeds is already being built for a real failure, and a
        # missing version degrades it rather than breaking it. The trace still says which attribute
        # refused and why.
        logger.debug("Could not read %r for the error report: %s", attribute, error)
        return None


def _resolve_plugin_version(obj: object) -> str:
    """Best-effort plugin version from a bound instance.

    Deliberately forgiving: this runs while already handling a failure, so a missing
    attribute must not raise a second exception on top of the first.
    """
    for path in (('plugin_version',), ('app_context', 'plugin_version')):
        target = obj
        for attribute in path:
            target = _attribute_or_none(target, attribute)
            if target is None:
                break
        if isinstance(target, str) and target:
            return target
    return _plugin_version or 'unknown'


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


def _accepted_positionals(slot: Callable) -> Optional[int]:
    """How many positional arguments `slot` can take, or None for "as many as offered".

    PyQt inspects a slot and passes only the leading signal arguments it can accept, so
    `button.clicked` (which carries a `checked` bool) may be connected to a no-argument method. The
    guard's wrapper below takes `*args`, which makes PyQt hand it the signal's *full* argument list
    — so the wrapper has to reproduce that trimming itself. Without it, guarding a no-argument slot
    turns a working connection into a TypeError on every click.
    """
    try:
        parameters = inspect.signature(slot).parameters.values()
    except (TypeError, ValueError):  # C callables and builtins are not introspectable
        return None
    accepted = 0
    for parameter in parameters:
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            return None  # *args takes whatever it is given
        if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY,
                              inspect.Parameter.POSITIONAL_OR_KEYWORD):
            accepted += 1
    return accepted


def guarded_connect(signal, slot: Callable, context: str = None, version_source: object = None):
    """Connect `slot` to a Qt-owned `signal` so an unexpected failure becomes a report instead of
    escaping to Qt's event loop.

    Use this at every Qt-source connection — a widget/action/timer/layer/project/dialog signal —
    which is where a fresh call stack enters plugin code (`spec/007_architecture.md` § Entry points).
    A slot on a plugin `pyqtSignal` does NOT need it: that signal emits synchronously inside some
    other entry point's stack, so it is already covered.

    Returns whatever `signal.connect()` returns, so a caller that disconnects later can keep the
    token. `context` names the failing operation for the report (defaults to the slot's name);
    `version_source` is any object carrying `plugin_version`/`app_context.plugin_version` for the
    report body, or None for 'unknown'.

    PyQt keeps a strong reference to a connected Python callable for the connection's lifetime, so
    the wrapper is not collected while connected (pinned by `test_guarded_connect`'s keep-alive test).
    """
    resolved_context = context or f"a UI action ({getattr(slot, '__name__', 'slot')})"
    accepted = _accepted_positionals(slot)

    def _guarded(*args, **kwargs):
        if accepted is not None:
            args = args[:accepted]
        return call_guarded(slot, resolved_context, _resolve_plugin_version(version_source),
                            *args, **kwargs)

    return signal.connect(_guarded)
