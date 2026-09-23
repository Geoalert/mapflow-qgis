"""The message tier (`mapflow/infra/alert_service.py`) is throttled too (error-reporting step 5).

`alert()` opens a modal `exec()` — a nested event loop — so an informational alert on a polled path
stacks exactly like an unthrottled report dialog and locks QGIS (spec/006 § Volume limit). It now
shares the same suppression mechanism as the report tier, keyed on the icon + message text, with the
hidden-occurrence count carried into the next message it lets through. Interactive dialogs
(`Question`) are never suppressed — they must return a real answer.

Runs in the no-QGIS functional tier: the throttle is Qt-free and the dialog is patched out.
"""
from unittest.mock import MagicMock

import pytest
from PyQt5.QtWidgets import QMessageBox

from mapflow.infra import alert_service
from mapflow.report_throttle import ReportThrottle


class _Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return _Clock()


@pytest.fixture(autouse=True)
def fresh_throttle(monkeypatch, clock):
    """A private budget per test — the production throttle is process-wide. Global floor 0 so these
    tests exercise the per-signature window without the cross-signature floor getting in the way."""
    monkeypatch.setattr(alert_service, "_throttle",
                        ReportThrottle(global_floor=0.0, clock=clock))


@pytest.fixture(autouse=True)
def no_real_dialog(monkeypatch):
    """Replace the dialog class so nothing tries to build a QMessageBox without a QApplication. The
    fake keeps the real `Question` enum so alert()'s exemption check still compares correctly."""
    fake = MagicMock()
    fake.Question = QMessageBox.Question
    monkeypatch.setattr(alert_service, "QMessageBox", fake)
    monkeypatch.setattr(alert_service, "QApplication", MagicMock())
    return fake


@pytest.fixture
def service():
    return alert_service.AlertService("Mapflow")


def test_a_repeated_message_shows_once(service, no_real_dialog):
    service.alert("Mapflow is not responding")
    service.alert("Mapflow is not responding")

    assert no_real_dialog.call_count == 1  # the second is suppressed within the window


def test_a_different_message_is_not_suppressed(service, no_real_dialog):
    service.alert("Mapflow is not responding")
    service.alert("Something else failed")

    assert no_real_dialog.call_count == 2  # a different signature always shows


def test_a_question_is_never_suppressed(service, no_real_dialog):
    service.alert("Delete this project?", QMessageBox.Question)
    service.alert("Delete this project?", QMessageBox.Question)

    assert no_real_dialog.call_count == 2  # interactive: both must ask for a real answer


def test_the_suppressed_count_is_carried_into_the_next_message(service, no_real_dialog, clock):
    service.alert("Mapflow is not responding")   # shown
    service.alert("Mapflow is not responding")   # suppressed -> counted
    clock.now += 61.0                            # the 60s window elapses
    service.alert("Mapflow is not responding")   # shown again, now with the count

    shown_message = no_real_dialog.call_args.args[2]  # QMessageBox(icon, name, message, ...)
    assert "Repeated" in shown_message and "1" in shown_message


def test_configure_throttle_replaces_the_message_budget():
    alert_service.configure_throttle(first_window=5.0, max_window=50.0,
                                     global_floor=1.0, backoff=3.0)
    budget = alert_service._throttle

    assert (budget._first_window, budget._max_window,
            budget._global_floor, budget._backoff) == (5.0, 50.0, 1.0, 3.0)
