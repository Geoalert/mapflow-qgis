"""The source/provider combo pair keeps syncing after a failure (entry-point rollout, 4-PR6).

The two combos mirror each other, so each handler takes the *other* one's connection down while it
drives and restores it afterwards. That restore used to sit at the tail of the method, after a
`setCurrentText` and a `rasterSourceChanged.emit()` that runs plugin handlers — so one raising
handler left the pair permanently disconnected, and the combos silently stopped following each
other for the rest of the session. Now that these slots are guarded the raise is swallowed too,
which would have made the loss invisible (spec/006 § a guarded callback is interrupted).

The restore is in a `finally` now. These tests force a failure inside the guarded block and check
the connection comes back.
"""
from unittest.mock import MagicMock

import pytest

from mapflow.dialogs.main_dialog import MainDialog


def _dialog():
    """A partial dialog: only what the combo-sync methods touch. Building the real MainDialog would
    pull in the whole .ui tree for a two-attribute test."""
    dlg = MainDialog.__new__(MainDialog)
    dlg.current_raster_source = "old source"
    dlg.provider_raster_connection = object()
    dlg.raster_provider_connection = object()
    dlg.providerCombo = MagicMock()
    dlg.sourceCombo = MagicMock()
    # Bound slots the reconnect passes to guarded_connect.
    dlg.switch_raster_combo = MagicMock()
    dlg.switch_provider_combo = MagicMock()
    return dlg


def test_switch_provider_combo_reconnects_the_sibling_when_the_body_raises():
    dlg = _dialog()
    dlg.providerCombo.setCurrentText.side_effect = RuntimeError("a handler failed")

    with pytest.raises(RuntimeError):
        MainDialog.switch_provider_combo(dlg, "new source")

    dlg.providerCombo.currentTextChanged.disconnect.assert_called_once()
    # Restored despite the raise — without this the provider combo stops driving the source combo.
    dlg.providerCombo.currentTextChanged.connect.assert_called_once()


def test_switch_raster_combo_reconnects_the_sibling_when_the_body_raises():
    dlg = _dialog()
    dlg.sourceCombo.setCurrentText.side_effect = RuntimeError("a handler failed")

    with pytest.raises(RuntimeError):
        MainDialog.switch_raster_combo(dlg, "new source")

    dlg.sourceCombo.currentTextChanged.disconnect.assert_called_once()
    dlg.sourceCombo.currentTextChanged.connect.assert_called_once()


def test_set_raster_sources_reconnects_both_combos_when_repopulating_raises():
    dlg = _dialog()
    dlg.sourceCombo.addItem.side_effect = RuntimeError("bad provider list")

    with pytest.raises(RuntimeError):
        MainDialog.set_raster_sources(dlg, {"Mapflow": "mapflow"}, ["Mapflow"])

    # Both were deliberately deaf for the repopulate; both must come back.
    dlg.providerCombo.currentTextChanged.connect.assert_called_once()
    dlg.sourceCombo.currentTextChanged.connect.assert_called_once()
