"""The two-way selection sync between the search results table and the footprint layer.

Selecting a row highlights its footprint; selecting a footprint highlights its row. Each direction
writes the selection the other listens to, so both disconnect the opposite handler before touching
a selection and reconnect afterwards — without that, one click ping-pongs until the stack runs out.

Written against `mapflow.py` *before* the move and re-pointed at `SearchController` afterwards,
with the assertions untouched — so a difference here would have meant the move changed behaviour.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt5.QtWidgets import QAbstractItemView, QTableWidget, QTableWidgetItem

from mapflow.config import Config
from mapflow.functional.controller.search_controller import SearchController
from mapflow.functional.view.search_view import SearchView


LOCAL_INDEX_COLUMN = Config.LOCAL_INDEX_COLUMN
ZOOM_COLUMN = Config.ZOOM_COLUMN_INDEX


def _table(rows):
    """A real QTableWidget: the sync code uses findItems, selectRow and selection modes, which
    MagicMock cannot model faithfully enough for these assertions to mean anything."""
    table = QTableWidget(len(rows), max(LOCAL_INDEX_COLUMN, ZOOM_COLUMN) + 1)
    for row, (local_index, zoom) in enumerate(rows):
        table.setItem(row, LOCAL_INDEX_COLUMN, QTableWidgetItem(str(local_index)))
        table.setItem(row, ZOOM_COLUMN, QTableWidgetItem(str(zoom)))
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.ExtendedSelection)
    return table


@pytest.fixture
def plugin():
    """A `SearchController` with a real results table and real `SearchView` widget access.

    The view is real because the sync is almost entirely widget manipulation — selection modes,
    findItems, selectRow. Mocking it would leave the assertions checking the mock.
    """
    dlg = MagicMock()
    dlg.metadataTable = _table([(10, "16"), (11, "17"), (12, "18")])
    dlg.zoomCombo = MagicMock()
    dlg.zoomCombo.findText.return_value = -1

    view = SearchView.__new__(SearchView)
    view.dlg = dlg
    view.config = Config
    view.ensure_search_provider = MagicMock()

    controller = SearchController.__new__(SearchController)
    controller.search_view = view
    controller.provider_service = MagicMock()
    controller.app_context = SimpleNamespace(metadata_layer=MagicMock(),
                                             meta_layer_table_connection=MagicMock())
    controller.area_calculator_service = MagicMock()
    controller.aoi_view = MagicMock()
    # A real connection, not a mock: the layer->table direction disconnects this handle, and Qt
    # raises TypeError if it was never connected. Production always has one — faking it would
    # only prove the fake works.
    controller.connect_table_selection()
    # Kept for the assertions that reach for the dialog directly.
    controller.dlg = dlg
    return controller


# ---------- table -> layer ----------

def test_the_layer_handler_is_disconnected_while_the_table_drives(plugin):
    """The selectByExpression below fires the layer's selectionChanged; if the table handler is
    still attached it calls straight back into this method."""
    plugin.dlg.metadataTable.selectRow(0)

    plugin.sync_table_selection_with_layer()

    layer = plugin.app_context.metadata_layer
    layer.selectionChanged.disconnect.assert_called_once()
    # ...and put back, or the map stops driving the table from here on.
    layer.selectionChanged.connect.assert_called_once()


def test_the_selected_rows_local_indices_reach_the_layer(plugin):
    plugin.dlg.metadataTable.selectRow(1)

    plugin.sync_table_selection_with_layer()

    expression = plugin.app_context.metadata_layer.selectByExpression.call_args.args[0]
    assert "local_index in" in expression
    assert "11" in expression


def test_an_empty_selection_still_reconnects(plugin):
    """Clearing the table selection must not leave the layer handler detached."""
    plugin.dlg.metadataTable.clearSelection()

    plugin.sync_table_selection_with_layer()

    plugin.app_context.metadata_layer.selectionChanged.connect.assert_called_once()


def test_a_missing_layer_returns_without_touching_the_combo(plugin):
    """Before any search there is no metadata layer; the disconnect raises and the method stops."""
    plugin.app_context.metadata_layer = None

    plugin.sync_table_selection_with_layer()  # must not raise

    plugin.dlg.zoomCombo.setCurrentIndex.assert_not_called()


def test_the_zoom_combo_is_written_with_signals_blocked(plugin):
    """zoomCombo.currentIndexChanged -> on_zoom_change fires a second, duplicate cost request,
    and it would use the stale zoom. The block is the fix; this pins it."""
    plugin.dlg.zoomCombo.findText.return_value = 2
    plugin.dlg.metadataTable.selectRow(0)

    plugin.sync_table_selection_with_layer()

    calls = [call.args[0] for call in plugin.dlg.zoomCombo.blockSignals.call_args_list]
    assert calls == [True, False]
    plugin.dlg.zoomCombo.setCurrentIndex.assert_called_once_with(2)


def test_an_unknown_zoom_falls_back_to_the_first_entry(plugin):
    plugin.dlg.zoomCombo.findText.return_value = -1
    plugin.dlg.metadataTable.selectRow(0)

    plugin.sync_table_selection_with_layer()

    plugin.dlg.zoomCombo.setCurrentIndex.assert_called_once_with(0)


def test_the_cost_is_recomputed_after_the_zoom_is_set(plugin):
    plugin.dlg.metadataTable.selectRow(0)

    plugin.sync_table_selection_with_layer()

    plugin.area_calculator_service.calculate_aoi_area_polygon_layer.assert_called_once()


# ---------- layer -> table ----------

def test_selecting_a_footprint_selects_its_row(plugin):
    plugin.app_context.metadata_layer.getFeature.return_value = {"local_index": 12}

    plugin.sync_layer_selection_with_table([7])

    assert {index.row() for index in plugin.dlg.metadataTable.selectionModel().selectedRows()} == {2}


def test_the_table_handler_is_disconnected_while_the_layer_drives(plugin):
    plugin.app_context.metadata_layer.getFeature.return_value = {"local_index": 10}

    plugin.sync_layer_selection_with_table([1])

    # Reconnected in a finally, so it survives an exception mid-selection.
    assert plugin._table_selection_connection is not None
    assert plugin.dlg.metadataTable.selectionMode() == QAbstractItemView.ExtendedSelection


def test_no_selected_features_clears_the_table(plugin):
    plugin.dlg.metadataTable.selectRow(0)

    plugin.sync_layer_selection_with_table([])

    assert plugin.dlg.metadataTable.selectionModel().selectedRows() == []


def test_a_footprint_with_no_matching_row_clears_rather_than_raising(plugin):
    plugin.app_context.metadata_layer.getFeature.return_value = {"local_index": 999}

    plugin.sync_layer_selection_with_table([3])

    assert plugin.dlg.metadataTable.selectionModel().selectedRows() == []


def test_several_footprints_select_several_rows(plugin):
    plugin.app_context.metadata_layer.getFeature.side_effect = [
        {"local_index": 10}, {"local_index": 12}]

    plugin.sync_layer_selection_with_table([1, 3])

    assert {index.row() for index in plugin.dlg.metadataTable.selectionModel().selectedRows()} == {0, 2}


# ---------- image id -> table ----------

def test_an_empty_image_id_clears_the_selection(plugin):
    plugin.dlg.metadataTable.selectRow(0)

    plugin.sync_image_id_with_table("")

    assert plugin.dlg.metadataTable.selectionModel().selectedRows() == []


def test_an_unknown_image_id_clears_the_selection(plugin):
    plugin.dlg.metadataTable.selectRow(0)

    plugin.sync_image_id_with_table("no-such-image")

    assert plugin.dlg.metadataTable.selectionModel().selectedRows() == []
