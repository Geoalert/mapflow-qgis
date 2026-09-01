"""QGIS-tier tests for the local-filter machinery that stays in `mapflow.py`: assembling a
`FilterCriteria` from the widgets + context, and applying the result to the table and layer.

The pure computation (which results fail the filter, and the widen `(!)` comparison) moved to
`LocalFilterService` and is tested in `tests/functional/test_local_filter.py`. What remains here
needs the QGIS runtime and/or real widgets: the provider/product resolution that reads
`app_context`, the `apply_local_filter` orchestration (reorder, re-entrancy guard, skip-unchanged),
the row greying and footprint hiding, and the widen-indicator button toggle.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from qgis.core import QgsDistanceArea, QgsGeometry, QgsProject

from mapflow.functional.service.local_filter_service import LocalFilterService
from mapflow.mapflow import Mapflow


def _square(x0, y0, x1, y1):
    return QgsGeometry.fromWkt(
        f"POLYGON(({x0} {y0},{x1} {y0},{x1} {y1},{x0} {y1},{x0} {y0}))")


def _square_geojson(x0, y0, x1, y1):
    return {"type": "Polygon", "coordinates": [[
        [x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


def _feature(local_index, date, cloud, geom, intersection=None):
    props = {"local_index": local_index, "acquisitionDate": date, "cloudCover": cloud}
    if intersection is not None:
        props["aoiIntersectionPercent"] = intersection
    return {"type": "Feature", "geometry": geom, "properties": props}


def _feature_p(local_index, provider, product_type="OPTICAL"):
    f = _feature(local_index, "2025-03-01T00:00:00Z", 10, _square_geojson(0, 0, 10, 10))
    f["properties"]["providerName"] = provider
    f["properties"]["productType"] = product_type
    return f


def _plugin_regular(min_intersection=50, max_cloud=50, date_from=None, date_to=None):
    date_from = date_from or QDate(2025, 1, 1)
    date_to = date_to or QDate(2025, 12, 31)
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.dlg = MagicMock()
    plugin.dlg.metadataFrom.date.return_value = date_from
    plugin.dlg.metadataTo.date.return_value = date_to
    plugin.dlg.maxCloudCover.value.return_value = max_cloud
    plugin.dlg.minIntersection.value.return_value = min_intersection
    plugin.dlg.off_nadir_range.return_value = (0, 30)
    plugin.dlg.off_nadir_is_full_range.return_value = True
    # The pure computation lives in the service; these mapflow tests exercise the criteria
    # assembly that feeds it, so a real service is wired in.
    plugin.local_filter_service = LocalFilterService()
    plugin._allowed_provider_set = MagicMock(return_value=None)
    plugin._product_category_filter = MagicMock(return_value=None)
    plugin.template_service = SimpleNamespace(in_template_mode=False)
    plugin.app_context = SimpleNamespace(
        metadata_aoi=_square(0, 0, 10, 10),
        project=QgsProject.instance(),
        search_baseline_filters=None,
        search_result_geojson=None,
        metadata_layer=None)
    return plugin


# ---------- _allowed_provider_set / _product_category_filter (criteria assembly) ----------

def test_allowed_provider_set_off_when_unavailable_toggle_off():
    plugin = _plugin_regular()
    del plugin._allowed_provider_set  # use the real method
    plugin.dlg.hideUnavailableResults.isChecked.return_value = False

    assert plugin._allowed_provider_set() is None


def test_allowed_provider_set_uses_checked_when_any():
    plugin = _plugin_regular()
    del plugin._allowed_provider_set  # use the real method
    plugin.dlg.hideUnavailableResults.isChecked.return_value = True
    plugin.dlg.searchProvidersCombo.checkedItemsData.return_value = ["Orbview_SVN1"]

    assert plugin._allowed_provider_set() == {"orbview_svn1"}


def test_allowed_provider_set_falls_back_to_available_when_none_checked():
    # "Search only through available providers" ON, nothing checked -> limit to available list.
    plugin = _plugin_regular()
    del plugin._allowed_provider_set  # use the real method
    plugin.dlg.hideUnavailableResults.isChecked.return_value = True
    plugin.dlg.searchProvidersCombo.checkedItemsData.return_value = []
    plugin.app_context.search_data_providers = ["orbview_svn1", "orbview_svn3"]

    assert plugin._allowed_provider_set() == {"orbview_svn1", "orbview_svn3"}


def test_search_only_available_greys_unavailable_provider():
    # End to end through the wrapper: real assembly + real service. A provider not available to
    # the user is dropped from an otherwise-fit result.
    plugin = _plugin_regular(min_intersection=0, max_cloud=100)
    plugin._product_category_filter = MagicMock(return_value=None)
    plugin.dlg.hideUnavailableResults.isChecked.return_value = True
    plugin.dlg.searchProvidersCombo.checkedItemsData.return_value = []
    plugin.app_context.search_data_providers = ["orbview_svn1"]
    del plugin._allowed_provider_set  # use the real method
    features = [_feature_p(0, "orbview_svn1"), _feature_p(1, "legacy_provider")]

    assert plugin._unfit_local_indices(features) == {1}


def test_product_category_filter_none_when_both_or_neither():
    plugin = _plugin_regular()
    del plugin._product_category_filter  # use the real method
    for mosaic, image in [(True, True), (False, False)]:
        plugin.dlg.searchMosaicCheckBox.isChecked.return_value = mosaic
        plugin.dlg.searchImageCheckBox.isChecked.return_value = image
        assert plugin._product_category_filter() is None
    plugin.dlg.searchMosaicCheckBox.isChecked.return_value = True
    plugin.dlg.searchImageCheckBox.isChecked.return_value = False
    assert plugin._product_category_filter() == {"MOSAIC"}


# ---------- apply_local_filter orchestration ----------

def _geoms(*local_indices):
    return {"features": [{"properties": {"local_index": i}} for i in local_indices]}


def _plugin_orchestration(unfit):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.dlg = MagicMock()
    plugin.template_service = SimpleNamespace(in_template_mode=False)
    layer = MagicMock()
    layer.crs.return_value = "crs"
    plugin.app_context = SimpleNamespace(
        metadata_layer=layer,
        search_result_geojson=_geoms(0, 1, 2, 3),
        search_baseline_filters=None)
    plugin._unfit_local_indices = MagicMock(return_value=set(unfit))
    plugin._mark_unfit_rows = MagicMock()
    plugin._hide_unfit_footprints = MagicMock()
    plugin.search_controller = MagicMock()  # apply_local_filter drives reconnect_cell_preview
    plugin.template_controller = MagicMock()  # ...and apply_new_image_markers in template mode
    plugin._update_widen_indicator = MagicMock()
    plugin._restore_search_sort_indicator = MagicMock()
    return plugin


def test_apply_local_filter_sorts_unfit_rows_to_bottom():
    plugin = _plugin_orchestration(unfit={1, 3})

    plugin.apply_local_filter()

    filled = plugin.dlg.fill_metadata_table.call_args.args[0]
    order = [f["properties"]["local_index"] for f in filled["features"]]
    assert order == [0, 2, 1, 3]  # fit first (original order), then unfit (original order)
    # Built-in column sorting must be OFF for this fill, or the table re-sorts by date and the
    # unfit rows jump back up.
    assert plugin.dlg.fill_metadata_table.call_args.kwargs.get("sort") is False
    plugin._mark_unfit_rows.assert_called_once_with({1, 3})
    plugin._hide_unfit_footprints.assert_called_once()
    plugin._update_widen_indicator.assert_called_once()


def _dated_geoms():
    # Deliberately NOT in date order — mimics a server sort by some other column (e.g. resolution).
    return {"features": [
        {"properties": {"local_index": 0, "acquisitionDate": "2020-01-01T00:00:00Z"}},
        {"properties": {"local_index": 1, "acquisitionDate": "2026-01-01T00:00:00Z"}},
        {"properties": {"local_index": 2, "acquisitionDate": "2023-01-01T00:00:00Z"}},
    ]}


def test_apply_local_filter_preserves_server_order_for_regular_search():
    # Regression: the local filter used to force date-desc, discarding the server's sort order
    # (so a pixel-resolution sort never showed in the table). Regular search must keep server order.
    plugin = _plugin_orchestration(unfit=set())
    plugin.app_context.search_result_geojson = _dated_geoms()

    plugin.apply_local_filter()

    order = [f["properties"]["local_index"]
             for f in plugin.dlg.fill_metadata_table.call_args.args[0]["features"]]
    assert order == [0, 1, 2]  # server order preserved (date-desc would have given [1, 2, 0])


def test_apply_local_filter_preserves_server_order_for_template():
    # Template results are now also sorted server-side (the template-images endpoint takes the
    # same sortBy/sortOrder), so the local filter must preserve their incoming order too.
    plugin = _plugin_orchestration(unfit=set())
    plugin.template_service = SimpleNamespace(in_template_mode=True)
    plugin.app_context.search_result_geojson = _dated_geoms()

    plugin.apply_local_filter()

    order = [f["properties"]["local_index"]
             for f in plugin.dlg.fill_metadata_table.call_args.args[0]["features"]]
    assert order == [0, 1, 2]  # server order preserved (no client date re-sort)


def test_apply_local_filter_is_reentrancy_guarded():
    plugin = _plugin_orchestration(unfit=set())
    # Simulate the nested metadataTableFilled emission during fill_metadata_table.
    plugin.dlg.fill_metadata_table.side_effect = lambda *a, **k: plugin.apply_local_filter()

    plugin.apply_local_filter()

    # The nested call is swallowed: exactly one real fill.
    assert plugin.dlg.fill_metadata_table.call_count == 1
    assert plugin._suppress_local_filter is False


def test_apply_local_filter_skips_refill_when_unchanged():
    plugin = _plugin_orchestration(unfit={2})

    plugin.apply_local_filter()
    plugin.apply_local_filter()  # same unfit set + same geoms object

    assert plugin.dlg.fill_metadata_table.call_count == 1


def test_hide_unfit_footprints_builds_subset_string():
    plugin = Mapflow.__new__(Mapflow)
    layer = MagicMock()

    plugin._hide_unfit_footprints(layer, {3, 1})
    layer.setSubsetString.assert_called_once_with("local_index NOT IN (1, 3)")

    layer.reset_mock()
    plugin._hide_unfit_footprints(layer, set())
    layer.setSubsetString.assert_called_once_with("")


def test_mark_unfit_rows_greys_and_disables_only_unfit():
    plugin = Mapflow.__new__(Mapflow)
    plugin.config = SimpleNamespace(LOCAL_INDEX_COLUMN=0)
    table = QTableWidget(2, 2)
    for row, local_index in enumerate([5, 6]):
        table.setItem(row, 0, QTableWidgetItem(str(local_index)))
        table.setItem(row, 1, QTableWidgetItem("x"))
    plugin.dlg = SimpleNamespace(metadataTable=table)

    plugin._mark_unfit_rows({6})

    fit_item = table.item(0, 1)
    unfit_item = table.item(1, 1)
    assert fit_item.flags() & Qt.ItemIsSelectable
    assert not (unfit_item.flags() & Qt.ItemIsSelectable)
    assert not (unfit_item.flags() & Qt.ItemIsEnabled)


# ---------- widen (!) indicator button ----------

def _plugin_widen(baseline):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.dlg = MagicMock()
    plugin.dlg.metadataFrom.date.return_value = QDate(2025, 1, 1)
    plugin.dlg.metadataTo.date.return_value = QDate(2025, 6, 1)
    plugin.dlg.maxCloudCover.value.return_value = 30
    plugin.dlg.minIntersection.value.return_value = 40
    plugin.dlg.off_nadir_range.return_value = (0, 30)
    plugin.local_filter_service = LocalFilterService()
    plugin.selected_search_product_types = MagicMock(return_value=["IMAGE"])
    plugin.selected_search_providers = MagicMock(return_value=["providerA"])
    plugin.app_context = SimpleNamespace(search_baseline_filters=baseline)
    return plugin


def test_update_widen_indicator_toggles_button_visibility():
    plugin = _plugin_widen(None)  # no baseline -> nothing to warn about
    plugin._update_widen_indicator()
    plugin.dlg.searchWidenWarning.setVisible.assert_called_with(False)

    plugin.app_context.search_baseline_filters = {"max_cloud_cover": 5}
    plugin._update_widen_indicator()
    plugin.dlg.searchWidenWarning.setVisible.assert_called_with(True)
