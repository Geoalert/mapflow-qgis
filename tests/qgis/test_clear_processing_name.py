"""QGIS-tier regression test for clearing the processing-name field after start.

After a processing starts, the name field is cleared only when it still holds the just-started
name (the user has not typed a new one). A refactor dropped the ``()`` on ``processingName.text``,
so the check compared a bound method to a string — always False — and the field never cleared.
"""
from types import SimpleNamespace

from PyQt5.QtWidgets import QLineEdit

from mapflow.functional.view.processing_view import ProcessingView


def _view(current_text):
    view = ProcessingView.__new__(ProcessingView)
    field = QLineEdit()
    field.setText(current_text)
    view.dlg = SimpleNamespace(processingName=field)
    return view


def test_clears_when_field_still_holds_started_name():
    view = _view("Run 1")
    view.clear_processing_name("Run 1")
    assert view.dlg.processingName.text() == ""


def test_preserves_when_user_typed_a_new_name():
    view = _view("Run 2 (editing)")
    view.clear_processing_name("Run 1")
    assert view.dlg.processingName.text() == "Run 2 (editing)"
