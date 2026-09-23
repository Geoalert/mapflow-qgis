"""QGIS-tier tests for provider serialization during template creation.

An empty provider selection must be omitted from the request, not sent as
``dataProviders: []`` — the backend reads ``[]`` literally as "search no
providers" and rejects template creation.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from qgis.core import QgsGeometry

from mapflow.functional.controller.template_controller import TemplateController
from mapflow.functional.service.aoi_service import AoiService
from mapflow.functional.service.template_service import TemplateService
from mapflow.functional.view.search_view import SearchView


def _controller_ready_to_create_template(checked_providers):
    """The provider serialization now runs through SearchView.template_search_params (real, over
    a mock dlg) and the create call through TemplateService; TemplateController assembles them."""
    dlg = MagicMock()
    dlg.processingName.text.return_value = "My template"
    dlg.metadataFrom.dateTime.return_value.toUTC.return_value.toString.return_value = "2022-09-24T17:00:00.000Z"
    dlg.metadataTo.dateTime.return_value.toUTC.return_value.toString.return_value = "2026-09-24T17:00:00.000Z"
    dlg.maxCloudCover.value.return_value = 50
    dlg.minIntersection.value.return_value = 20
    dlg.hideUnavailableResults.isChecked.return_value = True
    dlg.searchProvidersCombo.checkedItemsData.return_value = checked_providers

    app_context = SimpleNamespace(
        aoi=QgsGeometry.fromWkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
        aoi_size=10.0, template_area_limit=0.0, project_id="project-1",
        current_project=SimpleNamespace(id="project-1"), plugin_name="Mapflow")

    controller = TemplateController.__new__(TemplateController)
    controller.template_service = TemplateService(app_context=app_context,
                                                  processing_service=MagicMock())
    controller.template_view = MagicMock()
    controller.template_view.template_name.return_value = "My template"
    controller.search_view = SearchView(dlg=dlg, config=MagicMock())
    controller.aoi_view = MagicMock()
    controller.aoi_view.current_layer.return_value = None  # fall back to app_context.aoi
    controller.aoi_service = AoiService(iface=MagicMock(), app_context=MagicMock(), plugin_dir="",
                                        result_loader=MagicMock(),
                                        data_catalog_service=MagicMock(),
                                        processing_service=MagicMock())
    controller.provider_service = MagicMock()  # ensure_search_provider is a no-op (meta_url set)
    controller.app_context = app_context
    return controller


def _created_search_params(controller):
    controller.create_search_template()
    api = controller.template_service.processing_service.api
    data = api.create_template.call_args.kwargs["data"]
    return json.loads(data.as_json())["searchParams"]


def test_no_selected_providers_omits_data_providers():
    plugin = _controller_ready_to_create_template(checked_providers=[])

    search_params = _created_search_params(plugin)

    assert "dataProviders" not in search_params


def test_none_returned_providers_omits_data_providers():
    plugin = _controller_ready_to_create_template(checked_providers=None)

    search_params = _created_search_params(plugin)

    assert "dataProviders" not in search_params


def test_selected_providers_are_sent():
    plugin = _controller_ready_to_create_template(checked_providers=["arcgis_world_imagery"])

    search_params = _created_search_params(plugin)

    assert search_params["dataProviders"] == ["arcgis_world_imagery"]


def test_providers_omitted_when_available_filter_is_off_even_if_selected():
    # "Search only through available providers" OFF -> the (hidden) selection must NOT be sent.
    controller = _controller_ready_to_create_template(checked_providers=["arcgis_world_imagery"])
    controller.search_view.dlg.hideUnavailableResults.isChecked.return_value = False

    search_params = _created_search_params(controller)

    assert "dataProviders" not in search_params


def test_selected_search_providers_respects_available_filter_checkbox():
    dlg = MagicMock()
    view = SearchView(dlg=dlg, config=MagicMock())
    dlg.searchProvidersCombo.checkedItemsData.return_value = ["arcgis_world_imagery"]

    dlg.hideUnavailableResults.isChecked.return_value = False
    assert view.search_providers() is None  # filter off -> nothing sent

    dlg.hideUnavailableResults.isChecked.return_value = True
    assert view.search_providers() == ["arcgis_world_imagery"]

    dlg.searchProvidersCombo.checkedItemsData.return_value = []
    assert view.search_providers() is None  # empty selection -> omitted
