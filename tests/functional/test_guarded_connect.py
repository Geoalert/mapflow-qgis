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


def test_a_report_with_no_version_source_falls_back_to_the_recorded_version(monkeypatch):
    """Dialogs and views hold neither `plugin_version` nor `app_context`, so every report raised
    from a widget slot said "unknown" — the field that makes a report actionable, missing on a whole
    tier of them. `Mapflow.__init__` records the version once and the guard falls back to it."""
    monkeypatch.setattr(error_guard, "_plugin_version", None)
    error_guard.set_plugin_version("3.7.0")
    signal = _FakeSignal()

    def slot(*args):
        raise Boom("x")

    with patch.object(error_guard, "report_unexpected_error") as reported:
        # No version_source at all — the shape every dialog and view conversion uses.
        error_guard.guarded_connect(signal, slot, "editing a name")
        signal.connected()

    assert reported.call_args.args[2] == "3.7.0"


def test_an_explicit_version_source_still_wins_over_the_recorded_one(monkeypatch):
    monkeypatch.setattr(error_guard, "_plugin_version", "3.7.0")
    signal = _FakeSignal()

    class Owner:
        plugin_version = "9.9.9"

    def slot(*args):
        raise Boom("x")

    with patch.object(error_guard, "report_unexpected_error") as reported:
        error_guard.guarded_connect(signal, slot, "x", version_source=Owner())
        signal.connected()

    assert reported.call_args.args[2] == "9.9.9"


def test_a_version_source_that_raises_on_attribute_access_still_reports(monkeypatch):
    """The resolver runs while a failure is already being handled, so it must not add one of its
    own. `getattr(x, name, default)` only swallows AttributeError — a sip-wrapped Qt object whose
    C++ base was never constructed raises RuntimeError, and a property can raise anything. Escaping
    here would take the guard's own report down and reach the event loop unguarded."""
    monkeypatch.setattr(error_guard, "_plugin_version", None)  # no fallback: isolate the resolver
    signal = _FakeSignal()

    class Hostile:
        @property
        def plugin_version(self):
            raise RuntimeError("super-class __init__() was never called")

        @property
        def app_context(self):
            raise RuntimeError("super-class __init__() was never called")

    def slot(*args):
        raise Boom("x")

    with patch.object(error_guard, "report_unexpected_error") as reported:
        error_guard.guarded_connect(signal, slot, "x", version_source=Hostile())
        signal.connected()  # must not raise

    reported.assert_called_once()
    assert reported.call_args.args[2] == "unknown"
