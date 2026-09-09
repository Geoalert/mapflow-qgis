"""`error_guard.guarded_connect` — the mechanism that guards Qt-source entry points.

It wraps a slot so an unexpected exception becomes a report (via `report_unexpected_error`) instead
of escaping to Qt's event loop, and returns the connection token the caller may keep. These run in
the no-QGIS functional tier with a fake signal; the keep-alive property (PyQt retaining the wrapper)
is checked in the qgis tier with a real signal — see `tests/qgis/test_guarded_connect_keepalive.py`.
"""
from unittest.mock import patch

from mapflow import error_guard


class _FakeSignal:
    """Records the slot connected and returns a token, like `pyqtSignal.connect`."""

    def __init__(self):
        self.connected = None
        self.token = object()

    def connect(self, slot):
        self.connected = slot
        return self.token


class Boom(Exception):
    pass


def test_it_returns_the_connection_token():
    signal = _FakeSignal()
    token = error_guard.guarded_connect(signal, lambda: None, "doing a thing")
    assert token is signal.token


def test_a_raising_slot_is_reported_not_propagated():
    signal = _FakeSignal()

    def slot(*args):
        raise Boom("kaboom")

    with patch.object(error_guard, "report_unexpected_error") as reported:
        error_guard.guarded_connect(signal, slot, "doing a thing")
        signal.connected("arg")  # fire it as Qt would — must not raise

    reported.assert_called_once()
    exception, context = reported.call_args.args[:2]
    assert isinstance(exception, Boom)
    assert context == "doing a thing"


def test_a_successful_slot_runs_and_gets_its_arguments():
    signal = _FakeSignal()
    seen = []
    error_guard.guarded_connect(signal, lambda *a: seen.append(a), "x")

    signal.connected(1, 2)

    assert seen == [(1, 2)]


def test_a_no_argument_slot_is_not_given_the_signals_arguments():
    """PyQt trims a signal's arguments to what the slot accepts, so `clicked(bool)` may be connected
    to a no-argument method. The wrapper takes `*args`, which makes PyQt hand it the full argument
    list — so it must reproduce that trimming, or guarding a working no-argument slot would raise
    TypeError on every emission."""
    signal = _FakeSignal()
    calls = []
    error_guard.guarded_connect(signal, lambda: calls.append("called"), "x")

    signal.connected(True)  # as `clicked` emits

    assert calls == ["called"]


def test_a_slot_gets_only_as_many_arguments_as_it_accepts():
    signal = _FakeSignal()
    seen = []
    error_guard.guarded_connect(signal, lambda first: seen.append(first), "x")

    signal.connected(1, 2, 3)

    assert seen == [1]


def test_a_bound_method_does_not_count_self():
    """The case that broke the poll/submission rollout: a bound method with no parameters beyond
    `self` connected to `clicked`."""
    signal = _FakeSignal()

    class Owner:
        def __init__(self):
            self.calls = []

        def navigate(self):
            self.calls.append("called")

    owner = Owner()
    error_guard.guarded_connect(signal, owner.navigate, "x")

    signal.connected(True)

    assert owner.calls == ["called"]


def test_the_context_defaults_to_the_slot_name():
    signal = _FakeSignal()

    def refresh_table(*args):
        raise Boom("x")

    with patch.object(error_guard, "report_unexpected_error") as reported:
        error_guard.guarded_connect(signal, refresh_table)
        signal.connected()

    assert "refresh_table" in reported.call_args.args[1]


def test_the_plugin_version_comes_from_the_version_source():
    signal = _FakeSignal()

    class Owner:
        plugin_version = "9.9.9"

    def slot(*args):
        raise Boom("x")

    with patch.object(error_guard, "report_unexpected_error") as reported:
        error_guard.guarded_connect(signal, slot, "x", version_source=Owner())
        signal.connected()

    assert reported.call_args.args[2] == "9.9.9"
