"""Suppression policy for repeated error reports.

An error dialog is shown from paths that can fire on a timer. `AlertService.alert` and
`ErrorMessageWidget` both open on top of QGIS's event loop, and a modal `exec()` runs a
*nested* event loop — so QTimer keeps firing while a dialog is up, and dialogs stack rather
than queue. One recurring failure in a poll callback therefore does not produce one dialog;
it produces a new one every few seconds until QGIS is unusable.

This module decides whether a given failure has already been reported recently enough to
stay quiet about. It holds no Qt or QGIS imports on purpose: it must be usable from the
earliest-imported modules, and it is the kind of arithmetic that should be testable without
a QApplication.
"""
import time
import traceback
from typing import Callable, Dict, Optional

#: Gap before the same failure may be shown again. Above the slowest poll
#: (`config.py` USER_STATUS_UPDATE_INTERVAL, 30s), so a recurring failure in any poll
#: callback cannot produce a second dialog on the following tick.
FIRST_WINDOW_SECONDS = 60.0

#: Ceiling for the doubling below. A persistent failure still resurfaces a couple of times
#: an hour: going permanently silent would leave the user with broken behaviour and no
#: remaining prompt to report it.
MAX_WINDOW_SECONDS = 30 * 60.0

#: Minimum gap between any two reports, whatever failed. Per-signature suppression alone
#: does not stop several *different* exceptions rotating through the same callback — with
#: PROCESSING_TABLE_REFRESH_INTERVAL at 6s, three alternating bugs would still yield a
#: dialog every 6 seconds while each individual signature stayed within its window.
GLOBAL_FLOOR_SECONDS = 10.0


def exception_signature(exception: BaseException) -> str:
    """Identity of a failure for suppression purposes: type plus the line it failed on.

    Excludes the exception *message*, which routinely embeds ids, paths and counts — the
    same bug would present a new signature on every occurrence and never be suppressed.
    Excludes the operation context too: one failing line reached from two call paths is one
    bug, and reporting it twice tells the maintainer nothing extra.
    """
    name = type(exception).__name__
    traceback_object = getattr(exception, '__traceback__', None)
    if traceback_object is None:
        return name
    frames = traceback.extract_tb(traceback_object)
    if not frames:
        return name
    last_frame = frames[-1]
    return f'{name}@{last_frame.filename}:{last_frame.lineno}'


class _SignatureState:
    """Per-signature bookkeeping. `shown_at` is None until the first report is shown."""

    __slots__ = ('shown_at', 'window', 'suppressed')

    def __init__(self, window: float) -> None:
        self.shown_at: Optional[float] = None
        self.window = window
        self.suppressed = 0


class ReportThrottle:
    """Decides which error reports reach the user, and counts the ones that do not.

    Every method is total — no input makes it raise. It is consulted while the plugin is
    already handling a failure, so an exception escaping from here would replace the error
    being reported with its own.

    Unsynchronised on purpose: every caller is a Qt slot or a network-reply handler, all of
    which run on the main thread. A lock here would guard against nothing.

    Per-signature state is kept for the life of the session and never evicted. Signatures
    are source locations, so the dictionary is bounded by the number of distinct raise
    sites in the plugin — expiring entries would only discard the suppression counts that
    make a report worth reading.
    """

    def __init__(self,
                 first_window: float = FIRST_WINDOW_SECONDS,
                 max_window: float = MAX_WINDOW_SECONDS,
                 global_floor: float = GLOBAL_FLOOR_SECONDS,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self._first_window = first_window
        self._max_window = max_window
        self._global_floor = global_floor
        self._clock = clock
        self._states: Dict[str, _SignatureState] = {}
        self._last_shown_at: Optional[float] = None

    def should_report(self, signature: str) -> Optional[int]:
        """Return None to suppress, otherwise how many occurrences were suppressed since
        the last shown report of this signature.

        A suppressed occurrence is still counted, so the next dialog can say how much was
        hidden. Callers log unconditionally — suppression governs the dialog, never the log.
        """
        now = self._clock()
        state = self._states.get(signature)
        if state is None:
            state = _SignatureState(window=self._first_window)
            self._states[signature] = state
        elif state.shown_at is not None and now - state.shown_at < state.window:
            state.suppressed += 1
            return None

        if self._last_shown_at is not None and now - self._last_shown_at < self._global_floor:
            state.suppressed += 1
            return None

        if state.shown_at is not None:
            # Doubling starts only from the second report: the first one defines the
            # baseline window rather than consuming it.
            state.window = min(state.window * 2, self._max_window)
        state.shown_at = now
        self._last_shown_at = now

        suppressed = state.suppressed
        state.suppressed = 0
        return suppressed
