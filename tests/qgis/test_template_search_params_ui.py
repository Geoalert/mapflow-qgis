"""QGIS-tier tests for populating the Imagery Search filters from a template's
``searchParams`` (round-2 feedback 3, web parity: opening a template shows the search
filters it was created with; the widgets stay editable and affect only the current
search view, never the stored template)."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt5.QtCore import QDate, Qt

from mapflow.mapflow import Mapflow
from mapflow.schema.template import SearchParams


def _plugin():
    plugin = Mapflow.__new__(Mapflow)
    plugin.dlg = MagicMock()
    # on_template_opened clears the retained results/baseline (so interim widget-set signals
    # don't compare against a stale search baseline).
    plugin.app_context = SimpleNamespace(search_result_geojson=None, search_baseline_filters=None)
    return plugin


def _search_params(**overrides):
    params = dict(
        acquisitionDateFrom="2025-01-02T10:20:30.000Z",
        acquisitionDateTo="2025-03-04T10:20:30.000Z",
        maxCloudCover=42,
        minAoiIntersectionPercent=17,
        hideUnavailable=True,
        productTypes=["IMAGE"],
        dataProviders=["providerB"],
    )
    params.update(overrides)
    return SearchParams(**params)


def _providers_combo(plugin, items):
    combo = plugin.dlg.searchProvidersCombo
    combo.count.return_value = len(items)
    combo.itemData.side_effect = lambda index: items[index]
    return combo


def test_apply_search_params_sets_all_filter_widgets():
    plugin = _plugin()
    _providers_combo(plugin, ["providerA", "providerB"])

    plugin.apply_search_params_to_ui(_search_params())

    plugin.dlg.metadataFrom.setDate.assert_called_once_with(QDate(2025, 1, 2))
    plugin.dlg.metadataTo.setDate.assert_called_once_with(QDate(2025, 3, 4))
    plugin.dlg.maxCloudCover.setValue.assert_called_once_with(42)
    plugin.dlg.minIntersection.setValue.assert_called_once_with(17)
    plugin.dlg.hideUnavailableResults.setChecked.assert_called_once_with(True)
    plugin.dlg.searchImageCheckBox.setChecked.assert_called_once_with(True)
    plugin.dlg.searchMosaicCheckBox.setChecked.assert_called_once_with(False)


def test_apply_search_params_accepts_dict_payload():
    plugin = _plugin()
    _providers_combo(plugin, [])

    plugin.apply_search_params_to_ui({"maxCloudCover": 55, "hideUnavailable": False})

    plugin.dlg.maxCloudCover.setValue.assert_called_once_with(55)
    plugin.dlg.hideUnavailableResults.setChecked.assert_called_once_with(False)
    plugin.dlg.metadataFrom.setDate.assert_not_called()
    plugin.dlg.metadataTo.setDate.assert_not_called()


def test_apply_search_params_none_is_noop():
    plugin = _plugin()

    plugin.apply_search_params_to_ui(None)

    plugin.dlg.metadataFrom.setDate.assert_not_called()
    plugin.dlg.maxCloudCover.setValue.assert_not_called()
    plugin.dlg.hideUnavailableResults.setChecked.assert_not_called()
    plugin.dlg.searchProvidersCombo.deselectAllOptions.assert_not_called()


def test_apply_search_params_missing_fields_leave_widgets_untouched():
    plugin = _plugin()
    _providers_combo(plugin, [])

    plugin.apply_search_params_to_ui(SearchParams())

    plugin.dlg.metadataFrom.setDate.assert_not_called()
    plugin.dlg.metadataTo.setDate.assert_not_called()
    plugin.dlg.maxCloudCover.setValue.assert_not_called()
    plugin.dlg.minIntersection.setValue.assert_not_called()
    plugin.dlg.hideUnavailableResults.setChecked.assert_not_called()
    plugin.dlg.searchImageCheckBox.setChecked.assert_not_called()
    plugin.dlg.searchMosaicCheckBox.setChecked.assert_not_called()


def test_apply_search_params_checks_matching_providers_only():
    plugin = _plugin()
    combo = _providers_combo(plugin, ["providerA", "providerB"])

    plugin.apply_search_params_to_ui(_search_params(dataProviders=["providerB"]))

    combo.deselectAllOptions.assert_called_once()
    combo.setItemCheckState.assert_called_once_with(1, Qt.Checked)


def test_apply_search_params_without_providers_clears_combo():
    plugin = _plugin()
    combo = _providers_combo(plugin, ["providerA", "providerB"])

    plugin.apply_search_params_to_ui(_search_params(dataProviders=None))

    combo.deselectAllOptions.assert_called_once()
    combo.setItemCheckState.assert_not_called()


def test_on_template_opened_populates_search_filters():
    plugin = _plugin()
    plugin.apply_search_params_to_ui = MagicMock()
    plugin._load_template_search = MagicMock()
    plugin._load_template_layers = MagicMock()
    search_params = _search_params()
    template = SimpleNamespace(id="tpl-1", name="T1", searchParams=search_params)

    plugin.on_template_opened(template)

    plugin.apply_search_params_to_ui.assert_called_once_with(search_params)
    plugin._load_template_search.assert_called_once_with(template)
    plugin._load_template_layers.assert_called_once_with(template)
