"""`guarded_connect`'s wrapper must survive GC while the connection is live (qgis tier: real signal).

The helper connects a closure it does not itself retain. PyQt keeps a strong reference to a connected
Python callable for the connection's lifetime, so the wrapper is not collected — this pins that, so
the helper never needs a retention set of its own (unlike C3.4's widget). If PyQt's behaviour ever
changed, a guarded slot would silently stop firing; this test would catch it.
"""
import gc

from PyQt5.QtCore import QObject, pyqtSignal

from mapflow import error_guard


class _Emitter(QObject):
    fired = pyqtSignal(int)


def test_the_wrapper_still_fires_after_collection():
    emitter = _Emitter()
    seen = []
    error_guard.guarded_connect(emitter.fired, lambda value: seen.append(value), "x")

    gc.collect()  # the wrapper closure has no local reference here — only the connection holds it
    emitter.fired.emit(7)

    assert seen == [7], "the guarded wrapper was collected before the signal fired"
