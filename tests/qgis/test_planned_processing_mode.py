"""QGIS-tier tests: 'Start planned processing' (button text AND start action) applies only
when a template run would actually happen — a template is selected, the source is imagery
search, and that template's results are open in the search table.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.model.provider.default import ImagerySearchProvider
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.mapflow import Mapflow


def _service(template, processing=None, data_provider=None, open_id=None):
    service = ProcessingService.__new__(ProcessingService)
    service.selected_template = MagicMock(return_value=template)
    service.selected_processing = MagicMock(return_value=processing)
    service.app_context = SimpleNamespace(data_provider=data_provider, open_template_results_id=open_id)
    return service


def _imagery_search():
    return ImagerySearchProvider(proxy="https://example.com/rest")


def test_template_to_run_when_all_conditions_met():
    template = SimpleNamespace(id="t1")
    service = _service(template, data_provider=_imagery_search(), open_id="t1")
    assert service.template_to_run() is template


def test_template_to_run_none_without_template():
    service = _service(None, data_provider=_imagery_search(), open_id="t1")
    assert service.template_to_run() is None


def test_template_to_run_none_when_processing_also_selected():
    template = SimpleNamespace(id="t1")
    service = _service(template, processing=SimpleNamespace(id="p1"),
                       data_provider=_imagery_search(), open_id="t1")
    assert service.template_to_run() is None


def test_template_to_run_none_when_source_is_not_imagery_search():
    template = SimpleNamespace(id="t1")
    service = _service(template, data_provider=object(), open_id="t1")
    assert service.template_to_run() is None


def test_template_to_run_none_when_results_not_open():
    template = SimpleNamespace(id="t1")
    isp = _imagery_search()
    assert _service(template, data_provider=isp, open_id=None).template_to_run() is None
    assert _service(template, data_provider=isp, open_id="other-template").template_to_run() is None


def test_start_button_text_follows_template_to_run():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.dlg = MagicMock()
    plugin.processing_service = MagicMock()

    plugin.processing_service.template_to_run.return_value = SimpleNamespace(id="t1")
    plugin.update_start_processing_button_text()
    plugin.dlg.startProcessing.setText.assert_called_with("Start planned processing")

    plugin.processing_service.template_to_run.return_value = None
    plugin.update_start_processing_button_text()
    plugin.dlg.startProcessing.setText.assert_called_with("Start processing")


def _create_template_service():
    from mapflow.functional.service.template_service import TemplateService
    service = TemplateService.__new__(TemplateService)
    TemplateService.__init__(service, app_context=SimpleNamespace(plugin_version="1.0"),
                             processing_service=MagicMock())
    # Use the real template-response parser (the schema path), not a mock.
    service.processing_service._parse_template_response = ProcessingService._parse_template_response
    return service


def _response(body: bytes):
    response = MagicMock()
    response.readAll.return_value.data.return_value = body
    return response


def _template_body(is_active):
    import json
    return json.dumps({
        "id": "11111111-1111-1111-1111-111111111111", "name": "T", "status": "CREATED",
        "createdAt": "2026-01-01T00:00:00Z", "userId": "22222222-2222-2222-2222-222222222222",
        "searchParams": {"maxCloudCover": 50}, "projectId": "33333333-3333-3333-3333-333333333333",
        "activeUntil": "2026-06-01T00:00:00Z", "isActive": is_active,
    }).encode()


def test_create_template_callback_warns_when_inactive(monkeypatch):
    alerts = []
    monkeypatch.setattr("mapflow.functional.service.template_service.alert_warning", lambda msg, icon=None: alerts.append(msg))
    plugin = _create_template_service()

    plugin.create_search_template_callback(_response(_template_body(is_active=False)))

    assert "inactive" in alerts[0].lower()
    assert "maximum number of active planned processings" in alerts[0].lower()
    plugin.processing_service.get_processings.assert_called_once()


def test_create_template_callback_no_warning_when_active(monkeypatch):
    # An active template creates no inactive warning; the list refresh is the feedback.
    alerts = []
    monkeypatch.setattr("mapflow.functional.service.template_service.alert_warning", lambda msg, icon=None: alerts.append(msg))
    plugin = _create_template_service()

    plugin.create_search_template_callback(_response(_template_body(is_active=True)))

    assert alerts == []
    plugin.processing_service.get_processings.assert_called_once()


def test_create_template_callback_no_warning_when_response_unparseable(monkeypatch):
    # A response that can't be parsed into a template must not raise a false "inactive" warning.
    alerts = []
    monkeypatch.setattr("mapflow.functional.service.template_service.alert_warning", lambda msg, icon=None: alerts.append(msg))
    plugin = _create_template_service()

    plugin.create_search_template_callback(_response(b'{}'))

    assert alerts == []
    plugin.processing_service.get_processings.assert_called_once()


def test_provider_change_refreshes_start_button_text():
    # Switching the data source (e.g. an open template -> My imagery) must re-evaluate the button
    # label, since "planned" only applies to the imagery-search source.
    plugin = Mapflow.__new__(Mapflow)
    provider = MagicMock()  # not an ImagerySearchProvider/MyImageryProvider -> the generic branch
    provider.requires_image_id = False
    plugin.dlg = MagicMock()
    plugin.dlg.providerIndex.return_value = 0
    plugin.provider_service = MagicMock()
    plugin.provider_service.providers = [provider]
    plugin.app_context = SimpleNamespace(data_provider=None)
    plugin.toggle_imagery_search = MagicMock()
    plugin.area_calculator_service = MagicMock()
    plugin.update_start_processing_button_text = MagicMock()

    plugin.on_provider_change()

    assert plugin.app_context.data_provider is provider
    plugin.update_start_processing_button_text.assert_called_once()
