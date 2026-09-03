"""QGIS-tier tests for the 'Plan Search' prompt when the AOI is too large for an immediate
search (round-2 feedback 7). /user/status exposes searchAreaLimit; above it the regular
search offers to create a Planned Search (a template auto-named "Searching <date time>") in
the selected project. The existing templateAreaLimit block still applies to that creation."""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt5.QtCore import QObject

from mapflow.functional.app_context import AppContext
from mapflow.functional.service.account_service import AccountService
from mapflow.functional.service.template_service import TemplateService
from mapflow.mapflow import Mapflow


def _user_status_response(**overrides):
    payload = {
        "billingType": "AREA",
        "remainingArea": 5_000_000,
        "remainingCredits": 0,
        "templateAreaLimit": 2_000_000,
        "searchAreaLimit": 1_000_000,
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


def test_search_area_limit_is_stored_in_sq_km():
    service = _account_service()

    service.apply_status(_user_status_response())

    assert service.app_context.search_area_limit == 1.0


def test_search_area_limit_defaults_to_zero_when_absent():
    service = _account_service()

    response = _user_status_response()
    payload = json.loads(response.readAll.return_value.data.return_value)
    payload.pop("searchAreaLimit")
    response.readAll.return_value.data.return_value = json.dumps(payload).encode()

    service.apply_status(response)

    assert service.app_context.search_area_limit == 0.0


# ---------- the plan-search gating moved to TemplateService / TemplateController ----------

def _service(search_area_limit, aoi_size):
    return TemplateService(
        app_context=SimpleNamespace(search_area_limit=search_area_limit, aoi_size=aoi_size),
        processing_service=MagicMock())


def test_search_area_exceeds_limit_true_when_over():
    assert _service(search_area_limit=1.0, aoi_size=2.0).search_area_exceeds_limit() is True


def test_search_area_exceeds_limit_false_when_under_or_unknown():
    assert _service(search_area_limit=1.0, aoi_size=0.5).search_area_exceeds_limit() is False
    assert _service(search_area_limit=0.0, aoi_size=99.0).search_area_exceeds_limit() is False


def test_search_area_at_exactly_the_limit_does_not_exceed():
    """The boundary: an AOI exactly at the limit is allowed an immediate search — `>`, not `>=`.
    Without this case a `>=` off-by-one passes every other test."""
    assert _service(search_area_limit=1.0, aoi_size=1.0).search_area_exceeds_limit() is False


def _dispatch_plugin(exceeds, mode="search"):
    """`handle_metadata_button_click` stays in mapflow.py — it dispatches to the template
    controller (plan / too-large) or to SearchController.run_search."""
    plugin = Mapflow.__new__(Mapflow)
    plugin.search_view = MagicMock()
    plugin.search_view.search_mode = mode
    plugin.search_controller = MagicMock()
    plugin.template_service = MagicMock()
    plugin.template_service.in_template_mode = False
    plugin.template_service.search_area_exceeds_limit.return_value = exceeds
    plugin.template_controller = MagicMock()
    return plugin


def test_button_click_offers_plan_search_when_area_too_large():
    plugin = _dispatch_plugin(exceeds=True)

    plugin.handle_metadata_button_click()

    plugin.template_controller.prompt_plan_search.assert_called_once()
    plugin.search_controller.run_search.assert_not_called()


def test_button_click_runs_search_when_within_limit():
    plugin = _dispatch_plugin(exceeds=False)

    plugin.handle_metadata_button_click()

    plugin.search_controller.run_search.assert_called_once()
    plugin.template_controller.prompt_plan_search.assert_not_called()


def test_button_click_in_plan_mode_creates_template_directly():
    plugin = _dispatch_plugin(exceeds=True, mode="plan")

    plugin.handle_metadata_button_click()

    plugin.template_controller.create_search_template.assert_called_once()
    plugin.template_controller.prompt_plan_search.assert_not_called()
    plugin.search_controller.run_search.assert_not_called()


def test_planned_search_default_name_has_prefix():
    name = _service(0, 0).planned_search_default_name()
    assert name.startswith("Searching ")


# ---------- the prompt dialog itself moved to TemplateView; the controller drives it ----------

def _controller(plan_confirmed):
    from mapflow.functional.controller.template_controller import TemplateController
    controller = TemplateController.__new__(TemplateController)
    controller.template_service = MagicMock()
    controller.template_service.in_template_mode = False
    controller.template_service.planned_search_default_name.return_value = "Searching 2026-07-14 10:00"
    controller.template_view = MagicMock()
    controller.template_view.prompt_plan_search.return_value = plan_confirmed
    controller.app_context = SimpleNamespace(plugin_name="Mapflow")
    controller.create_search_template = MagicMock()
    return controller


def test_prompt_plan_search_creates_template_on_confirm():
    controller = _controller(plan_confirmed=True)

    controller.prompt_plan_search()

    controller.create_search_template.assert_called_once_with(
        name_override="Searching 2026-07-14 10:00")


def test_prompt_plan_search_cancel_does_nothing():
    controller = _controller(plan_confirmed=False)

    controller.prompt_plan_search()

    controller.create_search_template.assert_not_called()
