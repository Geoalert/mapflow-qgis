"""QGIS-tier tests for populating the Imagery Search filters from a template's
``searchParams`` (round-2 feedback 3, web parity: opening a template shows the search
filters it was created with; the widgets stay editable and affect only the current
search view, never the stored template).

Owners after the search extraction: the widget writes are `SearchView.apply_search_params`,
and `TemplateController.on_template_opened` is what calls it when a template is entered.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt5.QtCore import QDate, Qt

from mapflow.functional.controller.template_controller import TemplateController
from mapflow.functional.view.search_view import SearchView
from mapflow.schema.template import SearchParams


def _view():
    return SearchView(dlg=MagicMock(), config=MagicMock())


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


def _providers_combo(view, items):
    combo = view.dlg.searchProvidersCombo
    combo.count.return_value = len(items)
    combo.itemData.side_effect = lambda index: items[index]
    return combo


def test_apply_search_params_sets_all_filter_widgets():
    view = _view()
    _providers_combo(view, ["providerA", "providerB"])

    view.apply_search_params(_search_params())

    view.dlg.metadataFrom.setDate.assert_called_once_with(QDate(2025, 1, 2))
    view.dlg.metadataTo.setDate.assert_called_once_with(QDate(2025, 3, 4))
    view.dlg.maxCloudCover.setValue.assert_called_once_with(42)
    view.dlg.minIntersection.setValue.assert_called_once_with(17)
    view.dlg.hideUnavailableResults.setChecked.assert_called_once_with(True)
    view.dlg.searchImageCheckBox.setChecked.assert_called_once_with(True)
    view.dlg.searchMosaicCheckBox.setChecked.assert_called_once_with(False)


def test_apply_search_params_accepts_dict_payload():
    view = _view()
    _providers_combo(view, [])

    view.apply_search_params({"maxCloudCover": 55, "hideUnavailable": False})

    view.dlg.maxCloudCover.setValue.assert_called_once_with(55)
    view.dlg.hideUnavailableResults.setChecked.assert_called_once_with(False)
    view.dlg.metadataFrom.setDate.assert_not_called()
    view.dlg.metadataTo.setDate.assert_not_called()


def test_apply_search_params_none_is_noop():
    view = _view()

    view.apply_search_params(None)

    view.dlg.metadataFrom.setDate.assert_not_called()
    view.dlg.maxCloudCover.setValue.assert_not_called()
    view.dlg.hideUnavailableResults.setChecked.assert_not_called()
    view.dlg.searchProvidersCombo.deselectAllOptions.assert_not_called()


def test_apply_search_params_missing_fields_leave_widgets_untouched():
    view = _view()
    _providers_combo(view, [])

    view.apply_search_params(SearchParams())

    view.dlg.metadataFrom.setDate.assert_not_called()
    view.dlg.metadataTo.setDate.assert_not_called()
    view.dlg.maxCloudCover.setValue.assert_not_called()
    view.dlg.minIntersection.setValue.assert_not_called()
    view.dlg.hideUnavailableResults.setChecked.assert_not_called()
    view.dlg.searchImageCheckBox.setChecked.assert_not_called()
    view.dlg.searchMosaicCheckBox.setChecked.assert_not_called()


def test_apply_search_params_checks_matching_providers_only():
    view = _view()
    combo = _providers_combo(view, ["providerA", "providerB"])

    view.apply_search_params(_search_params(dataProviders=["providerB"]))

    combo.deselectAllOptions.assert_called_once()
    combo.setItemCheckState.assert_called_once_with(1, Qt.Checked)


def test_apply_search_params_without_providers_clears_combo():
    view = _view()
    combo = _providers_combo(view, ["providerA", "providerB"])

    view.apply_search_params(_search_params(dataProviders=None))

    combo.deselectAllOptions.assert_called_once()
    combo.setItemCheckState.assert_not_called()


def _controller():
    controller = TemplateController.__new__(TemplateController)
    controller.template_service = MagicMock()
    controller.template_view = MagicMock()
    controller.search_view = MagicMock()
    controller.aoi_service = MagicMock()
    return controller


def test_on_template_opened_populates_search_filters_and_loads_results():
    controller = _controller()
    search_params = _search_params()
    template = SimpleNamespace(id="tpl-1", name="T1", searchParams=search_params)

    controller.on_template_opened(template)

    controller.search_view.apply_search_params.assert_called_once_with(search_params)
    controller.template_service.load_search.assert_called_once_with(template)
    # Entering a template also draws its layers and shows the "Update template" button.
    controller.template_service.load_template_layers.assert_called_once_with(template)
    controller.template_view.set_update_template_visible.assert_called_once_with(True)


def test_on_template_opened_clears_the_previous_views_results_first():
    """Otherwise the widget writes below fire the local filter against a stale baseline."""
    controller = _controller()
    calls = []
    controller.template_service.clear_search_state.side_effect = lambda: calls.append("clear")
    controller.search_view.apply_search_params.side_effect = lambda _p: calls.append("apply")
    controller.template_service.load_search.side_effect = lambda _t: calls.append("load")

    controller.on_template_opened(SimpleNamespace(id="tpl-1", name="T1", searchParams=None))

    assert calls == ["clear", "apply", "load"]
