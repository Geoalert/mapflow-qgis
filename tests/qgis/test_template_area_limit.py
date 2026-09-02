"""QGIS-tier tests for the planned-processing (template) area limit.

Behaviour under test:
* ``/user/status`` exposes ``templateAreaLimit`` -> stored on app_context,
* template creation is forbidden client-side when the AOI exceeds that limit,
* a zero/unknown limit lets the request through (backend stays the source of truth).
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt5.QtCore import QObject
from qgis.core import QgsGeometry

from mapflow.functional.app_context import AppContext
from mapflow.functional.service.account_service import AccountService
from mapflow.functional.service.template_service import TemplateService


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


def _account_service():
    service = AccountService.__new__(AccountService)
    QObject.__init__(service)
    service.tr = lambda text: text
    service.plugin_name = "Mapflow"
    service.config = SimpleNamespace(MAX_AOIS_PER_PROCESSING=1)
    service.app_context = AppContext()
    return service


def test_template_area_limit_is_stored_in_sq_km():
    service = _account_service()

    service.apply_status(_user_status_response())

    assert service.app_context.template_area_limit == 2.0


def test_template_area_limit_defaults_to_zero_when_absent():
    service = _account_service()

    response = _user_status_response()
    payload = json.loads(response.readAll.return_value.data.return_value)
    payload.pop("templateAreaLimit")
    response.readAll.return_value.data.return_value = json.dumps(payload).encode()

    service.apply_status(response)

    assert service.app_context.template_area_limit == 0.0


def _template_service(app_context):
    return TemplateService(app_context=app_context, processing_service=MagicMock())


def test_create_search_template_blocks_when_aoi_exceeds_template_area_limit(monkeypatch):
    alerts = []
    monkeypatch.setattr("mapflow.functional.service.template_service.alert",
                        lambda msg, *a, **k: alerts.append(msg) or True)
    service = _template_service(SimpleNamespace(
        aoi=MagicMock(),  # truthy AOI
        aoi_size=120.0,
        template_area_limit=50.0,
        project_id="project-1",
        current_project=SimpleNamespace(id="project-1"),
    ))

    service.create_search_template("My template", aoi_details={"features": [1]},
                                   search_params=MagicMock())

    service.processing_service.api.create_template.assert_not_called()
    assert len(alerts) == 1
    assert "50" in alerts[0] and "planned processing" in alerts[0].lower()


def test_create_search_template_proceeds_when_limit_is_unknown(monkeypatch):
    monkeypatch.setattr("mapflow.functional.service.template_service.alert",
                        lambda *a, **k: True)
    service = _template_service(SimpleNamespace(
        aoi=QgsGeometry.fromWkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
        aoi_size=10.0,
        template_area_limit=0.0,  # unknown -> client-side check disabled
        project_id="project-1",
        current_project=SimpleNamespace(id="project-1"),
        plugin_name="Mapflow",
    ))

    service.create_search_template("My template", aoi_details={"features": [1]},
                                   search_params=MagicMock())

    service.processing_service.api.create_template.assert_called_once()
