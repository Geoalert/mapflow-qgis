"""QGIS-tier tests for instant local filtering of imagery-search / template results.

The filter widgets (date range, cloud cover, min intersection %) filter the already-fetched
results on the client on every change — no server request. Unfit rows are not removed: they are
greyed-out, made non-selectable and sorted to the bottom, and their footprints hidden from the
result layer. A widen (!) indicator warns when the current widgets ask for MORE than was
fetched (which local filtering cannot surface without a new Search).

Templates are filtered client-side too (no server-side Filter button); min intersection uses the
union of the SELECTED AOIs, and is skipped when none is selected (provisional rule)."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from qgis.core import QgsDistanceArea, QgsGeometry, QgsProject

from mapflow.mapflow import Mapflow


def _square(x0, y0, x1, y1):
    return QgsGeometry.fromWkt(
        f"POLYGON(({x0} {y0},{x1} {y0},{x1} {y1},{x0} {y1},{x0} {y0}))")


def _square_geojson(x0, y0, x1, y1):
    return {"type": "Polygon", "coordinates": [[
        [x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


def _feature(local_index, date, cloud, geom):
    return {"type": "Feature", "geometry": geom,
            "properties": {"local_index": local_index, "acquisitionDate": date, "cloudCover": cloud}}


def _features():
    """GeoJSON results (same shape as fills the table): index 0 fits; 1 out of date range;
    2 too cloudy; 3 barely overlaps the AOI (~1%)."""
    return [
        _feature(0, "2025-03-01T00:00:00Z", 10, _square_geojson(0, 0, 10, 10)),
        _feature(1, "2020-01-01T00:00:00Z", 5, _square_geojson(0, 0, 10, 10)),
        _feature(2, "2025-03-01T00:00:00Z", 90, _square_geojson(0, 0, 10, 10)),
        _feature(3, "2025-03-01T00:00:00Z", 10, _square_geojson(9, 9, 11, 11)),
    ]


def _plugin_regular(min_intersection=50, max_cloud=50,
                    date_from=None, date_to=None):
    date_from = date_from or QDate(2025, 1, 1)
    date_to = date_to or QDate(2025, 12, 31)
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.calculator = QgsDistanceArea()
    plugin.dlg = MagicMock()
    plugin.dlg.metadataFrom.date.return_value = date_from
    plugin.dlg.metadataTo.date.return_value = date_to
    plugin.dlg.maxCloudCover.value.return_value = max_cloud
    plugin.dlg.minIntersection.value.return_value = min_intersection
    # No provider / product-type filter by default; overridden in the relevant tests.
    plugin._allowed_provider_set = MagicMock(return_value=None)
    plugin._product_category_filter = MagicMock(return_value=None)
    plugin.processing_service = SimpleNamespace(in_template_mode=False)
    plugin.app_context = SimpleNamespace(
        metadata_aoi=_square(0, 0, 10, 10),
        project=QgsProject.instance(),
        search_baseline_filters=None,
        search_result_geojson=None,
        metadata_layer=None)
    return plugin


# ---------- _unfit_local_indices / _intersection_reference ----------

def test_unfit_indices_reject_date_cloud_and_intersection():
    plugin = _plugin_regular()

    unfit = plugin._unfit_local_indices(_features())

    # 0 passes; 1 (date), 2 (cloud), 3 (intersection) fail.
    assert unfit == {1, 2, 3}


def test_unfit_matches_displayed_cloud_value():
    # Greying must track the exact Cloud % shown in the table: at 50% the 90-cloud image is out
    # and the 10-cloud one stays, regardless of any layer field typing.
    plugin = _plugin_regular(min_intersection=0, max_cloud=50)

    unfit = plugin._unfit_local_indices(_features())

    assert 2 in unfit and 0 not in unfit


def test_unfit_handles_string_cloud_without_crashing():
    # Cloud arriving as a string must not abort the whole pass (which used to freeze the greying).
    plugin = _plugin_regular(min_intersection=0, max_cloud=50)
    features = _features()
    features[2]["properties"]["cloudCover"] = "90"  # string, still > 50

    unfit = plugin._unfit_local_indices(features)

    assert 2 in unfit


def test_intersection_not_applied_when_min_is_zero():
    plugin = _plugin_regular(min_intersection=0)

    unfit = plugin._unfit_local_indices(_features())

    # Only date (1) and cloud (2) fail; the tiny-overlap image (3) now passes.
    assert unfit == {1, 2}


def test_cloud_100_disables_cloud_filter():
    plugin = _plugin_regular(min_intersection=0, max_cloud=100)

    unfit = plugin._unfit_local_indices(_features())

    # Cloud no longer filters (image 2 passes); only the out-of-range date (1) fails.
    assert unfit == {1}


# ---------- My Imagery: missing metadata matches any filter ----------

def _my_imagery_feature(local_index):
    """A My Imagery row: no acquisition date, no cloud cover, covers the AOI."""
    return _feature(local_index, None, None, _square_geojson(0, 0, 10, 10))


def test_missing_date_passes_date_filter():
    # Active date range that a real date would have to fall in; the null-date row must stay fit.
    plugin = _plugin_regular(min_intersection=0, max_cloud=100)

    unfit = plugin._unfit_local_indices([_my_imagery_feature(0)])

    assert unfit == set()


def test_missing_cloud_passes_cloud_filter():
    plugin = _plugin_regular(min_intersection=0, max_cloud=30)  # < 100, so cloud is filtered

    unfit = plugin._unfit_local_indices([_my_imagery_feature(0)])

    assert unfit == set()


def test_missing_date_and_cloud_pass_with_both_filters_active():
    plugin = _plugin_regular(min_intersection=0, max_cloud=30,
                             date_from=QDate(2025, 1, 1), date_to=QDate(2025, 2, 1))

    unfit = plugin._unfit_local_indices([_my_imagery_feature(0)])

    assert unfit == set()


def test_populated_values_still_filter_both_directions():
    # Guard against over-correcting into "never filter": real out-of-range values must still fail.
    plugin = _plugin_regular(min_intersection=0, max_cloud=50,
                             date_from=QDate(2025, 1, 1), date_to=QDate(2025, 12, 31))
    features = [
        _feature(0, "2025-06-01T00:00:00Z", 10, _square_geojson(0, 0, 10, 10)),   # in range, clear
        _feature(1, "2019-06-01T00:00:00Z", 10, _square_geojson(0, 0, 10, 10)),   # date too old
        _feature(2, "2025-06-01T00:00:00Z", 80, _square_geojson(0, 0, 10, 10)),   # too cloudy
    ]

    unfit = plugin._unfit_local_indices(features)

    assert unfit == {1, 2}


def test_passes_optional_rule():
    assert Mapflow._passes_optional(None, lambda v: False) is True   # missing -> always passes
    assert Mapflow._passes_optional(5, lambda v: v < 10) is True
    assert Mapflow._passes_optional(50, lambda v: v < 10) is False



def test_template_intersection_skipped_without_selected_aoi():
    plugin = _plugin_regular(min_intersection=50)
    plugin.processing_service.in_template_mode = True
    plugin._union_of_selected_aoi_geometries = MagicMock(return_value=None)

    aoi, min_area = plugin._intersection_reference(50)

    assert aoi is None and min_area == 0
    plugin._union_of_selected_aoi_geometries.assert_called_once()


def test_template_intersection_uses_selected_aoi_union():
    plugin = _plugin_regular(min_intersection=50)
    plugin.processing_service.in_template_mode = True
    plugin._union_of_selected_aoi_geometries = MagicMock(return_value=_square(0, 0, 10, 10))

    unfit = plugin._unfit_local_indices(_features())

    # Same outcome as regular search against the same AOI: 1 (date), 2 (cloud), 3 (intersection).
    assert unfit == {1, 2, 3}


# ---------- provider / product-type filtering ----------

def _feature_p(local_index, provider, product_type="OPTICAL"):
    f = _feature(local_index, "2025-03-01T00:00:00Z", 10, _square_geojson(0, 0, 10, 10))
    f["properties"]["providerName"] = provider
    f["properties"]["productType"] = product_type
    return f


def test_provider_filter_greys_disallowed_providers():
    plugin = _plugin_regular(min_intersection=0, max_cloud=100)
    plugin._allowed_provider_set = MagicMock(return_value={"orbview_svn1"})
    features = [_feature_p(0, "orbview_svn1"), _feature_p(1, "orbview_svn3")]

    assert plugin._unfit_local_indices(features) == {1}  # svn3 not allowed


def test_provider_filter_is_case_insensitive():
    plugin = _plugin_regular(min_intersection=0, max_cloud=100)
    plugin._allowed_provider_set = MagicMock(return_value={"orbview_svn1"})

    assert plugin._unfit_local_indices([_feature_p(0, "OrbView_SVN1")]) == set()


def test_provider_filter_off_shows_all():
    plugin = _plugin_regular(min_intersection=0, max_cloud=100)
    plugin._allowed_provider_set = MagicMock(return_value=None)
    features = [_feature_p(0, "orbview_svn1"), _feature_p(1, "orbview_svn3")]

    assert plugin._unfit_local_indices(features) == set()


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
    plugin = _plugin_regular(min_intersection=0, max_cloud=100)
    plugin._product_category_filter = MagicMock(return_value=None)
    plugin.dlg.hideUnavailableResults.isChecked.return_value = True
    plugin.dlg.searchProvidersCombo.checkedItemsData.return_value = []
    plugin.app_context.search_data_providers = ["orbview_svn1"]
    del plugin._allowed_provider_set  # use the real method
    features = [_feature_p(0, "orbview_svn1"), _feature_p(1, "legacy_provider")]

    # legacy_provider is not available to the user -> greyed.
    assert plugin._unfit_local_indices(features) == {1}


def test_product_type_mosaic_only_greys_images():
    plugin = _plugin_regular(min_intersection=0, max_cloud=100)
    plugin._product_category_filter = MagicMock(return_value={"MOSAIC"})
    features = [_feature_p(0, "p", product_type="Mosaic"),
                _feature_p(1, "p", product_type="OPTICAL")]

    assert plugin._unfit_local_indices(features) == {1}  # OPTICAL -> Image, filtered out


def test_product_type_image_only_greys_mosaics():
    plugin = _plugin_regular(min_intersection=0, max_cloud=100)
    plugin._product_category_filter = MagicMock(return_value={"IMAGE"})
    features = [_feature_p(0, "p", product_type="Mosaic"),
                _feature_p(1, "p", product_type="OPTICAL")]

    assert plugin._unfit_local_indices(features) == {0}  # the Mosaic is filtered out


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


def test_product_category_maps_mosaic_else_image():
    assert Mapflow._product_category("Mosaic") == "MOSAIC"
    assert Mapflow._product_category("mosaic") == "MOSAIC"
    assert Mapflow._product_category("OPTICAL") == "IMAGE"
    assert Mapflow._product_category("") == "IMAGE"
    assert Mapflow._product_category(None) == "IMAGE"


# ---------- reset filters ----------

def _plugin_reset(baseline):
    plugin = Mapflow.__new__(Mapflow)
    plugin.dlg = MagicMock()
    plugin.apply_local_filter = MagicMock()
    plugin._apply_search_providers_to_combo = MagicMock()
    plugin.app_context = SimpleNamespace(search_baseline_filters=baseline)
    return plugin


def test_reset_filters_restores_baseline_and_refilters():
    plugin = _plugin_reset({
        "date_from": QDate(2025, 1, 1), "date_to": QDate(2025, 6, 1),
        "max_cloud_cover": 30, "min_intersection": 40,
        "product_types": ["MOSAIC"], "data_providers": ["providerA"],
        "hide_unavailable": True})

    plugin.reset_filters()

    plugin.dlg.metadataFrom.setDate.assert_called_once_with(QDate(2025, 1, 1))
    plugin.dlg.maxCloudCover.setValue.assert_called_once_with(30)
    plugin.dlg.minIntersection.setValue.assert_called_once_with(40)
    plugin.dlg.searchMosaicCheckBox.setChecked.assert_called_once_with(True)
    plugin.dlg.searchImageCheckBox.setChecked.assert_called_once_with(False)
    plugin.dlg.hideUnavailableResults.setChecked.assert_called_once_with(True)
    plugin._apply_search_providers_to_combo.assert_called_once_with(["providerA"])
    plugin.apply_local_filter.assert_called_once()


def test_reset_filters_leaves_params_the_template_did_not_set():
    # None baseline fields (params the template did not carry) must not touch their widgets.
    plugin = _plugin_reset({
        "date_from": None, "date_to": None, "max_cloud_cover": 20,
        "min_intersection": None, "product_types": None, "data_providers": None,
        "hide_unavailable": None})

    plugin.reset_filters()

    plugin.dlg.maxCloudCover.setValue.assert_called_once_with(20)
    plugin.dlg.minIntersection.setValue.assert_not_called()
    plugin.dlg.metadataFrom.setDate.assert_not_called()
    plugin.dlg.searchMosaicCheckBox.setChecked.assert_not_called()
    plugin.dlg.hideUnavailableResults.setChecked.assert_not_called()
    plugin._apply_search_providers_to_combo.assert_not_called()
    plugin.apply_local_filter.assert_called_once()


# ---------- apply_local_filter orchestration ----------

def _geoms(*local_indices):
    return {"features": [{"properties": {"local_index": i}} for i in local_indices]}


def _plugin_orchestration(unfit):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.dlg = MagicMock()
    plugin.processing_service = SimpleNamespace(in_template_mode=False)
    layer = MagicMock()
    layer.crs.return_value = "crs"
    plugin.app_context = SimpleNamespace(
        metadata_layer=layer,
        search_result_geojson=_geoms(0, 1, 2, 3),
        search_baseline_filters=None)
    plugin._unfit_local_indices = MagicMock(return_value=set(unfit))
    plugin._mark_unfit_rows = MagicMock()
    plugin._hide_unfit_footprints = MagicMock()
    plugin._reconnect_cell_preview = MagicMock()
    plugin._update_widen_indicator = MagicMock()
    plugin._apply_new_image_markers = MagicMock()
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
    plugin.processing_service.in_template_mode = True
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


# ---------- widen (!) indicator ----------

def _plugin_widen(baseline):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.dlg = MagicMock()
    plugin.dlg.metadataFrom.date.return_value = QDate(2025, 1, 1)
    plugin.dlg.metadataTo.date.return_value = QDate(2025, 6, 1)
    plugin.dlg.maxCloudCover.value.return_value = 30
    plugin.dlg.minIntersection.value.return_value = 40
    plugin.selected_search_product_types = MagicMock(return_value=["IMAGE"])
    plugin.selected_search_providers = MagicMock(return_value=["providerA"])
    plugin.app_context = SimpleNamespace(search_baseline_filters=baseline)
    return plugin


def test_no_widen_when_widgets_match_baseline():
    plugin = _plugin_widen({
        "date_from": QDate(2025, 1, 1), "date_to": QDate(2025, 6, 1),
        "max_cloud_cover": 30, "min_intersection": 40,
        "product_types": ["IMAGE"], "data_providers": ["providerA"]})

    assert plugin._widened_filter_messages() == []


def test_widen_detects_wider_cloud_and_earlier_date():
    plugin = _plugin_widen({
        "date_from": QDate(2025, 2, 1), "date_to": QDate(2025, 6, 1),
        "max_cloud_cover": 10, "min_intersection": 40,
        "product_types": ["IMAGE"], "data_providers": ["providerA"]})

    messages = plugin._widened_filter_messages()

    # Start date earlier (Jan < Feb) and cloud higher (30 > 10) are both flagged.
    assert any("Start date" in m for m in messages)
    assert any("cloud cover" in m for m in messages)
    assert not any("End date" in m for m in messages)


def test_widen_detects_lower_intersection_and_extra_provider():
    plugin = _plugin_widen({
        "date_from": QDate(2025, 1, 1), "date_to": QDate(2025, 6, 1),
        "max_cloud_cover": 30, "min_intersection": 80,
        "product_types": ["IMAGE"], "data_providers": ["providerB"]})

    messages = plugin._widened_filter_messages()

    assert any("intersection" in m for m in messages)      # 40 < 80
    assert any("Provider" in m for m in messages)          # providerA not in [providerB]


def test_update_widen_indicator_toggles_button_visibility():
    plugin = _plugin_widen(None)  # no baseline -> nothing to warn about
    plugin._update_widen_indicator()
    plugin.dlg.searchWidenWarning.setVisible.assert_called_with(False)

    plugin.app_context.search_baseline_filters = {"max_cloud_cover": 5}
    plugin._update_widen_indicator()
    plugin.dlg.searchWidenWarning.setVisible.assert_called_with(True)
