"""QGIS-tier tests: meaningful translatable errors for failed template actions, and
clearing the template search-results pagination on exit / fresh load."""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.service import processing_service as ps_mod
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.mapflow import Mapflow


def _error_response(message, code="BAD_REQUEST"):
    response = MagicMock()
    response.readAll.return_value.data.return_value = json.dumps(
        {"code": code, "message": message, "params": None}
    ).encode()
    return response


def test_max_active_templates_message_is_translated():
    from mapflow.errors.errors import ErrorMessage
    text = ErrorMessage(
        code="BAD_REQUEST",
        parameters=None,
        message="You have reached the maximum number of active templates",
    ).to_str()
    assert "maximum number of active planned processings" in text


def test_template_error_text_parses_response_body():
    service = ProcessingService.__new__(ProcessingService)
    service.tr = lambda text: text

    text = service._template_error_text(
        _error_response("You have reached the maximum number of active templates")
    )

    assert "maximum number of active planned processings" in text


def test_resume_error_handler_shows_meaningful_message(monkeypatch):
    service = ProcessingService.__new__(ProcessingService)
    service.tr = lambda text: text
    service._resume_template_state = {"template_id": "t-1"}
    alerts = []
    monkeypatch.setattr(ps_mod, "alert", lambda *a, **k: alerts.append(a[0]))

    service.resume_template_error_handler(
        _error_response("You have reached the maximum number of active templates")
    )

    assert service._resume_template_state == {}
    assert any("maximum number of active planned processings" in a for a in alerts)


def test_template_error_text_falls_back_to_unknown_on_bad_body():
    service = ProcessingService.__new__(ProcessingService)
    service.tr = lambda text: text
    response = MagicMock()
    response.readAll.return_value.data.return_value = b"not json"

    assert service._template_error_text(response) == "Unknown server error"


def test_on_template_closed_resets_search_pagination():
    plugin = Mapflow.__new__(Mapflow)
    plugin.app_context = SimpleNamespace(open_template_results_id="x")
    plugin._template_search_aoi_filter = "aoi-1"
    plugin.search_page_offset = 60
    plugin.dlg = MagicMock()
    plugin._remove_template_group = MagicMock()

    plugin.on_template_closed(None)

    assert plugin.search_page_offset == 0
    plugin.dlg.enable_search_pages.assert_called_once_with(False)


def test_load_template_search_starts_from_first_page():
    plugin = Mapflow.__new__(Mapflow)
    plugin.search_page_offset = 30
    plugin.search_page_limit = 30
    plugin.dlg = MagicMock()
    plugin.processing_service = MagicMock()
    plugin._aoi_ids_from_template = MagicMock(return_value=[])

    plugin._load_template_search(SimpleNamespace(id="t-1"))

    assert plugin.search_page_offset == 0
    assert plugin.processing_service.api.get_template_images.call_args.kwargs["offset"] == 0
