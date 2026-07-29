"""QGIS-tier tests for the Off-Nadir two-boundary filter (QgsRangeSlider, 0-30°).

Covers the widget actually building/syncing in the real dialog and the API-bounds helper
(full range -> no server filter).
"""
from unittest.mock import MagicMock

from qgis.core import QgsSettings

from mapflow.dialogs.main_dialog import MainDialog
from mapflow.mapflow import Mapflow


def _dialog():
    return MainDialog(None, QgsSettings())


def test_off_nadir_widget_builds_full_range_by_default():
    dlg = _dialog()
    assert dlg.off_nadir_range() == (0, 30)
    assert dlg.off_nadir_is_full_range() is True


def test_slider_change_updates_spinboxes():
    dlg = _dialog()
    dlg.set_off_nadir_range(5, 20)
    assert dlg.off_nadir_range() == (5, 20)
    assert dlg.minOffNadirSpinBox.value() == 5
    assert dlg.maxOffNadirSpinBox.value() == 20
    assert dlg.off_nadir_is_full_range() is False


def test_spinbox_change_updates_slider():
    dlg = _dialog()
    dlg.minOffNadirSpinBox.setValue(8)
    dlg.maxOffNadirSpinBox.setValue(22)
    assert dlg.off_nadir_range() == (8, 22)


def test_inverted_spinboxes_are_ordered():
    dlg = _dialog()
    dlg.minOffNadirSpinBox.setValue(20)
    dlg.maxOffNadirSpinBox.setValue(10)  # lower than min -> range is ordered, not broken
    lower, upper = dlg.off_nadir_range()
    assert lower <= upper


def _plugin(full_range, bounds=(5, 20)):
    plugin = Mapflow.__new__(Mapflow)
    plugin.dlg = MagicMock()
    plugin.dlg.off_nadir_is_full_range.return_value = full_range
    plugin.dlg.off_nadir_range.return_value = bounds
    return plugin


def test_request_bounds_none_at_full_range():
    assert _plugin(full_range=True)._off_nadir_request_bounds() == (None, None)


def test_request_bounds_sends_values_when_narrowed():
    assert _plugin(full_range=False, bounds=(5, 20))._off_nadir_request_bounds() == (5, 20)
