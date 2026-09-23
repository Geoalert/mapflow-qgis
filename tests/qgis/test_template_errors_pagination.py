"""QGIS-tier tests: meaningful translatable errors for failed template actions, and
clearing the template search-results pagination on exit / fresh load."""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.service import processing_service as ps_mod
from mapflow.functional.service import template_service as ts_mod
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.config import Config, ConfigColumns
from mapflow.functional.controller.template_controller import TemplateController
from mapflow.functional.service.search_service import SearchService
from mapflow.functional.service.template_service import TemplateService
from mapflow.functional.view.search_view import SearchView


def _search_service():
    """Real, not mocked: these tests assert on the paging state it owns."""
    return SearchService(iface=MagicMock(),
                         app_context=MagicMock(),
                         http=MagicMock(),
                         plugin_dir="",
                         config=Config,
                         config_search_columns=ConfigColumns(),
                         result_loader=MagicMock(),
                         provider_service=MagicMock())


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
    service = TemplateService(app_context=MagicMock(), processing_service=MagicMock())

    text = service._error_text(
        _error_response("You have reached the maximum number of active templates")
    )

    assert "maximum number of active planned processings" in text


def test_resume_error_handler_shows_meaningful_message(monkeypatch):
    """The run-state actions are TemplateService's; the body parse is still ProcessingService's
    (its AOI handler needs the same one), so this drives the real pair."""
    processing_service = ProcessingService.__new__(ProcessingService)
    processing_service.tr = lambda text: text
    service = TemplateService(app_context=MagicMock(), processing_service=processing_service)
    service._resume_template_state = {"template_id": "t-1"}
    alerts = []
    monkeypatch.setattr(ts_mod, "alert", lambda *a, **k: alerts.append(a[0]))

    service.resume_template_error_handler(
        _error_response("You have reached the maximum number of active templates")
    )

    assert service._resume_template_state == {}
    assert any("maximum number of active planned processings" in a for a in alerts)


def test_template_error_text_falls_back_to_unknown_on_bad_body():
    service = TemplateService(app_context=MagicMock(), processing_service=MagicMock())
    response = MagicMock()
    response.readAll.return_value.data.return_value = b"not json"

    assert service._error_text(response) == "Unknown server error"


def _template_service(page_offset=0, page_limit=30):
    search_service = _search_service()
    search_service.page_offset = page_offset
    search_service.page_limit = page_limit
    return TemplateService(app_context=SimpleNamespace(open_template_results_id="x",
                                                       search_result_geojson={},
                                                       search_baseline_filters={}),
                           processing_service=MagicMock(),
                           search_service=search_service)


def test_on_template_closed_resets_search_pagination():
    service = _template_service(page_offset=60)
    service.search_aoi_filter = "aoi-1"
    dlg = MagicMock()
    controller = TemplateController.__new__(TemplateController)
    controller.template_service = service
    controller.template_view = MagicMock()
    controller.search_view = SearchView(dlg=dlg, config=MagicMock())
    controller.aoi_service = MagicMock()

    controller.on_template_closed(None)

    assert service.search_service.page_offset == 0
    assert service.search_aoi_filter is None
    assert service.app_context.open_template_results_id is None
    dlg.enable_search_pages.assert_called_once_with(False)


def test_load_search_starts_from_first_page():
    service = _template_service(page_offset=30, page_limit=30)
    service._aoi_ids_from_template = MagicMock(return_value=[])

    service.load_search(SimpleNamespace(id="t-1"))

    assert service.search_service.page_offset == 0
    kwargs = service.processing_service.api.get_template_images.call_args.kwargs
    assert kwargs["offset"] == 0
