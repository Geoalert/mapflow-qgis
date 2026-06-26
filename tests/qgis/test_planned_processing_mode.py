"""QGIS-tier tests: 'Start planned processing' (button text AND start action) applies only
when a template run would actually happen — a template is selected, the source is imagery
search, and that template's results are open in the search table.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.entity.provider.default import ImagerySearchProvider
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
