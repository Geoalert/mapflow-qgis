"""QGIS-tier tests for provider serialization during template creation.

An empty provider selection must be omitted from the request, not sent as
``dataProviders: []`` — the backend reads ``[]`` literally as "search no
providers" and rejects template creation.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.mapflow import Mapflow


def _plugin_ready_to_create_template(checked_providers):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.replace_search_provider_index = MagicMock()
    plugin.alert = MagicMock()
    plugin.iface = MagicMock()
    plugin.selected_search_product_types = MagicMock(return_value=["IMAGE"])
    plugin.processing_service = MagicMock()
    plugin.app_context = SimpleNamespace(
        aoi=MagicMock(asJson=MagicMock(return_value='{"type":"Polygon","coordinates":[]}')),
        aoi_size=10.0,
        template_area_limit=0.0,
        project_id="project-1",
        plugin_name="Mapflow",
    )

    plugin.dlg = MagicMock()
    plugin.dlg.processingName.text.return_value = "My template"
    plugin.dlg.metadataFrom.dateTime.return_value.toUTC.return_value.toString.return_value = "2022-09-24T17:00:00.000Z"
    plugin.dlg.metadataTo.dateTime.return_value.toUTC.return_value.toString.return_value = "2026-09-24T17:00:00.000Z"
    plugin.dlg.maxCloudCover.value.return_value = 50
    plugin.dlg.minIntersection.value.return_value = 20
    plugin.dlg.hideUnavailableResults.isChecked.return_value = True
    plugin.dlg.searchProvidersCombo.checkedItemsData.return_value = checked_providers
    return plugin


def _created_search_params(plugin):
    plugin.create_search_template()
    data = plugin.processing_service.api.create_template.call_args.kwargs["data"]
    return json.loads(data.as_json())["searchParams"]


def test_no_selected_providers_omits_data_providers():
    plugin = _plugin_ready_to_create_template(checked_providers=[])

    search_params = _created_search_params(plugin)

    assert "dataProviders" not in search_params


def test_none_returned_providers_omits_data_providers():
    plugin = _plugin_ready_to_create_template(checked_providers=None)

    search_params = _created_search_params(plugin)

    assert "dataProviders" not in search_params


def test_selected_providers_are_sent():
    plugin = _plugin_ready_to_create_template(checked_providers=["arcgis_world_imagery"])

    search_params = _created_search_params(plugin)

    assert search_params["dataProviders"] == ["arcgis_world_imagery"]
