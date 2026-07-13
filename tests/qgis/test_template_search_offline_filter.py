"""QGIS-tier tests for the offline metadata filter behaviour in template mode
(round-2 feedback 2). Template search results are filtered server-side by the template's
stored ``searchParams`` (spec 002_F: AOI filtering uses ``aoiIds`` on the images request).
The client-side ``filter_metadata`` — which tests each image against a SINGLE AOI — must
NOT run for templates, otherwise images intersecting the template's other AOIs are dropped
whenever ``minIntersection > 0`` (only the first AOI's results are shown)."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.mapflow import Mapflow


def _plugin(in_template_mode):
    plugin = Mapflow.__new__(Mapflow)
    plugin.dlg = MagicMock()
    plugin.calculator = MagicMock()
    plugin.config = MagicMock()
    plugin.preview_search_from_cell = MagicMock()
    plugin.processing_service = SimpleNamespace(in_template_mode=in_template_mode)
    metadata_layer = MagicMock()
    metadata_layer.crs.return_value = MagicMock()
    plugin.app_context = SimpleNamespace(metadata_layer=metadata_layer, metadata_aoi=None)
    plugin.dlg.metadataTable.rowCount.return_value = 3
    return plugin


def test_template_mode_skips_offline_intersection_filter():
    plugin = _plugin(in_template_mode=True)

    plugin.filter_metadata(min_intersection=50)

    # No offline filtering: the single-AOI intersection maths must never run.
    plugin.calculator.measureArea.assert_not_called()
    # The server's results are shown verbatim: subset cleared, all rows visible.
    plugin.app_context.metadata_layer.setSubsetString.assert_called_once_with('')
    assert plugin.dlg.metadataTable.setRowHidden.call_count == 3
    for call in plugin.dlg.metadataTable.setRowHidden.call_args_list:
        assert call.args[1] is False
    # Preview clicking is still wired up for template results.
    plugin.dlg.metadataTable.cellClicked.connect.assert_called_once_with(
        plugin.preview_search_from_cell)


def test_template_mode_reconnect_does_not_stack_preview_connections():
    plugin = _plugin(in_template_mode=True)
    plugin.cell_preview_connection = object()

    plugin.filter_metadata(min_intersection=10)

    # A previous preview connection is disconnected before reconnecting.
    plugin.dlg.metadataTable.disconnect.assert_called_once()


def test_template_mode_does_not_read_regular_search_filters():
    """The template guard returns before the regular path reads the date/AOI widgets."""
    plugin = _plugin(in_template_mode=True)

    plugin.filter_metadata(min_intersection=50)

    plugin.dlg.metadataFrom.date.assert_not_called()


def test_non_template_mode_enters_regular_offline_path():
    """Outside template mode the guard is skipped, so the regular offline filter runs
    (it reads the date widgets that the template branch never touches)."""
    plugin = _plugin(in_template_mode=False)
    plugin.dlg.maxCloudCover.value.return_value = 100
    plugin.dlg.minIntersection.value.return_value = 0
    try:
        plugin.filter_metadata(min_intersection=0)
    except Exception:
        pass  # real geometry maths is out of scope; we only assert the branch taken
    plugin.dlg.metadataFrom.date.assert_called()
