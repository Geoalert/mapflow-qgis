"""QGIS-tier tests for the planned-processing (template) area limit.

Behaviour under test:
* ``/user/status`` exposes ``templateAreaLimit`` -> stored on app_context,
* template creation is forbidden client-side when the AOI exceeds that limit,
* a zero/unknown limit lets the request through (backend stays the source of truth).
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.app_context import AppContext
from mapflow.mapflow import Mapflow


def _user_status_response(**overrides):
    payload = {
        "billingType": "AREA",
        "remainingArea": 5_000_000,
        "remainingCredits": 0,
        "templateAreaLimit": 2_000_000,
        "maxAoisPerProcessing": 3,
    }
    payload.update(overrides)
    response = MagicMock()
    response.readAll.return_value.data.return_value = json.dumps(payload).encode()
    return response


def test_set_processing_limit_stores_template_area_limit_in_sq_km():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.plugin_name = "Mapflow"
    plugin.config = SimpleNamespace(MAX_AOIS_PER_PROCESSING=1)
    plugin.app_context = AppContext()
    plugin.dlg = MagicMock()

    plugin.set_processing_limit(_user_status_response())

    assert plugin.app_context.template_area_limit == 2.0


def test_set_processing_limit_defaults_template_area_limit_to_zero_when_absent():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.plugin_name = "Mapflow"
    plugin.config = SimpleNamespace(MAX_AOIS_PER_PROCESSING=1)
    plugin.app_context = AppContext()
    plugin.dlg = MagicMock()

    response = _user_status_response()
    payload = json.loads(response.readAll.return_value.data.return_value)
    payload.pop("templateAreaLimit")
    response.readAll.return_value.data.return_value = json.dumps(payload).encode()

    plugin.set_processing_limit(response)

    assert plugin.app_context.template_area_limit == 0.0


def test_create_search_template_blocks_when_aoi_exceeds_template_area_limit():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.replace_search_provider_index = MagicMock()
    plugin.alert = MagicMock()
    plugin.dlg = MagicMock()
    plugin.processing_service = MagicMock()
    plugin.app_context = SimpleNamespace(
        aoi=MagicMock(),  # truthy AOI
        aoi_size=120.0,
        template_area_limit=50.0,
        project_id="project-1",
        current_project=SimpleNamespace(id="project-1"),
    )

    plugin.create_search_template()

    plugin.processing_service.api.create_template.assert_not_called()
    plugin.alert.assert_called_once()
    message = plugin.alert.call_args.args[0]
    assert "50" in message
    assert "planned processing" in message.lower()


def test_create_search_template_proceeds_when_limit_is_unknown():
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
        template_area_limit=0.0,  # unknown -> client-side check disabled
        project_id="project-1",
        current_project=SimpleNamespace(id="project-1"),
        plugin_name="Mapflow",
    )

    plugin.dlg = MagicMock()
    plugin.dlg.processingName.text.return_value = "My template"
    plugin.dlg.searchProvidersCombo.checkedItemsData.return_value = ["arcgis_world_imagery"]
    plugin.dlg.maxCloudCover.value.return_value = 50
    plugin.dlg.minIntersection.value.return_value = 20
    plugin.dlg.hideUnavailableResults.isChecked.return_value = True

    plugin.create_search_template()

    plugin.alert.assert_not_called()
    plugin.processing_service.api.create_template.assert_called_once()
