"""QGIS-tier tests for the local filter, now that it belongs to `SearchController`.

The pure computation (which results fail the filter, and the widen `(!)` comparison) is
`LocalFilterService`'s and is tested in `tests/functional/test_local_filter.py`. What is here needs
the QGIS runtime and/or real widgets: the criteria assembly that reads the widgets and
`app_context`, the `apply_local_filter` orchestration (reorder, re-entrancy guard, skip-unchanged),
the row greying, the footprint hiding, and the widen-indicator toggle.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt5.QtCore import QDate, QObject, Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from qgis.core import QgsGeometry, QgsProject

from mapflow.functional.controller.search_controller import SearchController
from mapflow.functional.service.local_filter_service import LocalFilterService
from mapflow.functional.service.search_service import SearchService
from mapflow.functional.view.search_view import SearchView


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


def _view(dlg=None):
    """A real `SearchView` over a mock dialog, so the widget reads under test are the real ones."""
    return SearchView(dlg=dlg or MagicMock(), config=SimpleNamespace(LOCAL_INDEX_COLUMN=0))


def _controller(search_view=None, app_context=None):
    controller = SearchController.__new__(SearchController)
    QObject.__init__(controller)
    controller.tr = lambda t: t
    controller.search_view = search_view or MagicMock()
    controller.search_service = MagicMock()
    controller.local_filter_service = LocalFilterService()
    controller.app_context = app_context or SimpleNamespace(
        search_baseline_filters=None, search_result_geojson=None, search_data_providers=None)
    controller._suppress_local_filter = False
    controller._last_unfit_set = None
    controller._last_filtered_geoms = None
    controller._widen_details = []
    return controller


def _filter_dlg(min_intersection=50, max_cloud=50, date_from=None, date_to=None):
    dlg = MagicMock()
    dlg.metadataFrom.date.return_value = date_from or QDate(2025, 1, 1)
    dlg.metadataTo.date.return_value = date_to or QDate(2025, 12, 31)
    dlg.maxCloudCover.value.return_value = max_cloud
    dlg.minIntersection.value.return_value = min_intersection
    dlg.off_nadir_range.return_value = (0, 30)
    dlg.off_nadir_is_full_range.return_value = True
    return dlg


# ---------- criteria assembly: which providers a result may come from ----------

def test_allowed_provider_set_off_when_unavailable_toggle_off():
    dlg = _filter_dlg()
    dlg.hideUnavailableResults.isChecked.return_value = False
    controller = _controller(search_view=_view(dlg))

    assert controller._allowed_provider_set() is None


def test_allowed_provider_set_uses_checked_when_any():
    dlg = _filter_dlg()
    dlg.hideUnavailableResults.isChecked.return_value = True
    dlg.searchProvidersCombo.checkedItemsData.return_value = ["Orbview_SVN1"]
    controller = _controller(search_view=_view(dlg))

    assert controller._allowed_provider_set() == {"orbview_svn1"}


def test_allowed_provider_set_falls_back_to_available_when_none_checked():
    # "Search only through available providers" ON, nothing checked -> limit to available list.
    dlg = _filter_dlg()
    dlg.hideUnavailableResults.isChecked.return_value = True
    dlg.searchProvidersCombo.checkedItemsData.return_value = []
    controller = _controller(
        search_view=_view(dlg),
        app_context=SimpleNamespace(search_data_providers=["orbview_svn1", "orbview_svn3"],
                                    search_baseline_filters=None, search_result_geojson=None))

    assert controller._allowed_provider_set() == {"orbview_svn1", "orbview_svn3"}


def test_search_only_available_greys_unavailable_provider():
    # End to end through the assembly + the real service: a provider not available to the user is
    # dropped from an otherwise-fit result.
    dlg = _filter_dlg(min_intersection=0, max_cloud=100)
    dlg.hideUnavailableResults.isChecked.return_value = True
    dlg.searchProvidersCombo.checkedItemsData.return_value = []
    dlg.searchMosaicCheckBox.isChecked.return_value = True
    dlg.searchImageCheckBox.isChecked.return_value = True  # both -> no product filter
    controller = _controller(
        search_view=_view(dlg),
        app_context=SimpleNamespace(search_data_providers=["orbview_svn1"],
                                    metadata_aoi=QgsGeometry.fromWkt(
                                        "POLYGON((0 0,10 0,10 10,0 10,0 0))"),
                                    project=QgsProject.instance(),
                                    search_baseline_filters=None, search_result_geojson=None))
    features = [_feature_p(0, "orbview_svn1"), _feature_p(1, "legacy_provider")]

    unfit = controller.local_filter_service.unfit_indices(features, controller._filter_criteria())

    assert unfit == {1}


def test_product_category_filter_none_when_both_or_neither():
    dlg = _filter_dlg()
    view = _view(dlg)
    for mosaic, image in [(True, True), (False, False)]:
        dlg.searchMosaicCheckBox.isChecked.return_value = mosaic
        dlg.searchImageCheckBox.isChecked.return_value = image
        assert view.product_category_filter() is None
    dlg.searchMosaicCheckBox.isChecked.return_value = True
    dlg.searchImageCheckBox.isChecked.return_value = False
    assert view.product_category_filter() == {"MOSAIC"}


# ---------- apply_local_filter orchestration ----------

def _geoms(*local_indices):
    return {"features": [{"properties": {"local_index": i}} for i in local_indices]}


def _orchestration_controller(unfit, geoms=None):
    controller = _controller(app_context=SimpleNamespace(
        search_result_geojson=geoms or _geoms(0, 1, 2, 3),
        search_baseline_filters=None,
        search_data_providers=None))
    controller.local_filter_service = MagicMock()
    controller.local_filter_service.unfit_indices.return_value = set(unfit)
    controller.local_filter_service.widen_messages.return_value = []
    # The criteria assembly has its own tests above; here the orchestration is what matters.
    controller._filter_criteria = MagicMock()
    controller.reconnect_cell_preview = MagicMock()
    controller.restore_sort_indicator = MagicMock()
    return controller


def test_apply_local_filter_sorts_unfit_rows_to_bottom():
    controller = _orchestration_controller(unfit={1, 3})

    controller.apply_local_filter()

    filled = controller.search_view.fill_table.call_args.args[0]
    order = [f["properties"]["local_index"] for f in filled["features"]]
    assert order == [0, 2, 1, 3]  # fit first (original order), then unfit (original order)
    # Built-in column sorting must be OFF for this fill, or the table re-sorts by date and the
    # unfit rows jump back up.
    assert controller.search_view.fill_table.call_args.kwargs.get("sort") is False
    controller.search_view.mark_unfit_rows.assert_called_once_with({1, 3})
    controller.search_service.hide_unfit_footprints.assert_called_once_with({1, 3})
    controller.restore_sort_indicator.assert_called_once()


def _dated_geoms():
    # Deliberately NOT in date order — mimics a server sort by some other column (e.g. resolution).
    return {"features": [
        {"properties": {"local_index": 0, "acquisitionDate": "2020-01-01T00:00:00Z"}},
        {"properties": {"local_index": 1, "acquisitionDate": "2026-01-01T00:00:00Z"}},
        {"properties": {"local_index": 2, "acquisitionDate": "2023-01-01T00:00:00Z"}},
    ]}


def test_apply_local_filter_preserves_server_order():
    # Regression: the local filter used to force date-desc, discarding the server's sort order (so
    # a pixel-resolution sort never showed in the table). Both regular and template results are
    # sorted server-side, so the incoming order must survive.
    controller = _orchestration_controller(unfit=set(), geoms=_dated_geoms())

    controller.apply_local_filter()

    order = [f["properties"]["local_index"]
             for f in controller.search_view.fill_table.call_args.args[0]["features"]]
    assert order == [0, 1, 2]  # server order preserved (date-desc would have given [1, 2, 0])


def test_apply_local_filter_is_reentrancy_guarded():
    controller = _orchestration_controller(unfit=set())
    # Simulate the nested metadataTableFilled emission during the fill.
    controller.search_view.fill_table.side_effect = lambda *a, **k: controller.apply_local_filter()

    controller.apply_local_filter()

    # The nested call is swallowed: exactly one real fill.
    assert controller.search_view.fill_table.call_count == 1
    assert controller._suppress_local_filter is False


def test_apply_local_filter_skips_refill_when_unchanged():
    controller = _orchestration_controller(unfit={2})

    controller.apply_local_filter()
    controller.apply_local_filter()  # same unfit set + same geoms object

    assert controller.search_view.fill_table.call_count == 1


def test_apply_local_filter_with_no_results_still_refreshes_the_indicator():
    controller = _orchestration_controller(unfit=set(), geoms={"features": []})

    controller.apply_local_filter()

    controller.search_view.fill_table.assert_not_called()
    controller.reconnect_cell_preview.assert_called_once()


# ---------- what the filter does to the table and the map ----------

def test_hide_unfit_footprints_builds_subset_string():
    service = SearchService.__new__(SearchService)
    layer = MagicMock()
    service.app_context = SimpleNamespace(metadata_layer=layer)

    service.hide_unfit_footprints({3, 1})
    layer.setSubsetString.assert_called_once_with("local_index NOT IN (1, 3)")

    layer.reset_mock()
    service.hide_unfit_footprints(set())
    layer.setSubsetString.assert_called_once_with("")


def test_hide_unfit_footprints_survives_a_missing_layer():
    service = SearchService.__new__(SearchService)
    service.app_context = SimpleNamespace(metadata_layer=None)

    service.hide_unfit_footprints({1})  # must not raise


def test_mark_unfit_rows_greys_and_disables_only_unfit():
    table = QTableWidget(2, 2)
    for row, local_index in enumerate([5, 6]):
        table.setItem(row, 0, QTableWidgetItem(str(local_index)))
        table.setItem(row, 1, QTableWidgetItem("x"))
    view = _view(SimpleNamespace(metadataTable=table))

    view.mark_unfit_rows({6})

    fit_item = table.item(0, 1)
    unfit_item = table.item(1, 1)
    assert fit_item.flags() & Qt.ItemIsSelectable
    assert not (unfit_item.flags() & Qt.ItemIsSelectable)
    assert not (unfit_item.flags() & Qt.ItemIsEnabled)


# ---------- widen (!) indicator button ----------

def _widen_controller(baseline):
    dlg = _filter_dlg(min_intersection=40, max_cloud=30,
                      date_from=QDate(2025, 1, 1), date_to=QDate(2025, 6, 1))
    dlg.searchMosaicCheckBox.isChecked.return_value = False
    dlg.searchImageCheckBox.isChecked.return_value = True
    dlg.hideUnavailableResults.isChecked.return_value = True
    dlg.searchProvidersCombo.checkedItemsData.return_value = ["providerA"]
    controller = _controller(
        search_view=_view(dlg),
        app_context=SimpleNamespace(search_baseline_filters=baseline,
                                    search_result_geojson=None, search_data_providers=None))
    return controller, dlg


def test_update_widen_indicator_toggles_button_visibility():
    controller, dlg = _widen_controller(None)  # no baseline -> nothing to warn about
    controller.update_widen_indicator()
    dlg.searchWidenWarning.setVisible.assert_called_with(False)

    controller.app_context.search_baseline_filters = {"max_cloud_cover": 5}
    controller.update_widen_indicator()
    dlg.searchWidenWarning.setVisible.assert_called_with(True)


def test_the_widen_tooltip_names_what_will_not_apply():
    controller, dlg = _widen_controller({"max_cloud_cover": 5})

    controller.update_widen_indicator()

    tooltip = dlg.searchWidenWarning.setToolTip.call_args.args[0]
    assert "Run a new Search" in tooltip
    assert "cloud" in tooltip.lower()


# ---------- resetting the filters ----------

def test_reset_filters_puts_the_widgets_back_and_refilters():
    controller = _controller()
    controller.app_context.search_baseline_filters = {"max_cloud_cover": 20}
    controller.apply_local_filter = MagicMock()

    controller.reset_filters()

    controller.search_view.apply_baseline.assert_called_once_with({"max_cloud_cover": 20})
    # Some setters may not change a value, so their change-signal would not fire the filter.
    controller.apply_local_filter.assert_called_once()


def test_reset_filters_without_a_baseline_does_nothing():
    controller = _controller()
    controller.apply_local_filter = MagicMock()

    controller.reset_filters()

    controller.search_view.apply_baseline.assert_not_called()
    controller.apply_local_filter.assert_not_called()
