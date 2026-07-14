"""QGIS-tier tests for search-results display refresh. All imagery search goes through the
Mapflow catalog, which filters (intersection, cloud, dates, resolution) server-side and
returns the paginated result; the plugin no longer re-filters offline (that used to shrink
the paginated page and break the page count, and for templates dropped images intersecting
the other AOIs — round-2 feedback 2/6). ``refresh_search_display`` just shows the server's
rows verbatim and (re)wires the preview-cell click."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.mapflow import Mapflow


def _plugin():
    plugin = Mapflow.__new__(Mapflow)
    plugin.dlg = MagicMock()
    plugin.calculator = MagicMock()
    plugin.preview_search_from_cell = MagicMock()
    metadata_layer = MagicMock()
    plugin.app_context = SimpleNamespace(metadata_layer=metadata_layer)
    plugin.dlg.metadataTable.rowCount.return_value = 3
    return plugin


def test_display_shows_all_rows_and_clears_subset_without_offline_filtering():
    plugin = _plugin()

    plugin.refresh_search_display()

    # No offline filtering: the intersection/area maths must never run.
    plugin.calculator.measureArea.assert_not_called()
    # Server results shown verbatim: subset cleared, all rows visible.
    plugin.app_context.metadata_layer.setSubsetString.assert_called_once_with('')
    assert plugin.dlg.metadataTable.setRowHidden.call_count == 3
    for call in plugin.dlg.metadataTable.setRowHidden.call_args_list:
        assert call.args[1] is False
    # Preview clicking is (re)wired.
    plugin.dlg.metadataTable.cellClicked.connect.assert_called_once_with(
        plugin.preview_search_from_cell)


def test_reconnect_does_not_stack_preview_connections():
    plugin = _plugin()
    plugin.cell_preview_connection = object()

    plugin.refresh_search_display()

    plugin.dlg.metadataTable.disconnect.assert_called_once()


def test_noop_when_no_metadata_layer():
    plugin = _plugin()
    plugin.app_context.metadata_layer.setSubsetString.side_effect = RuntimeError

    plugin.refresh_search_display()  # must not raise

    plugin.dlg.metadataTable.setRowHidden.assert_not_called()
