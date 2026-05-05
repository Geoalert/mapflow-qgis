from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from mapflow.functional.service import processing_service as processing_service_module
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.mapflow import Mapflow
from mapflow.schema.processing import PostProcessingSchemaV2, RunTemplateProcessingSchema


def _processing_payload():
	return PostProcessingSchemaV2(
		name="Run 1",
		description=None,
		projectId="project-1",
		wdId="wd-1",
		geometry={"type": "Polygon", "coordinates": []},
		params={"sourceParams": {"imagerySearch": {"dataProvider": "orbview", "imageIds": ["img-1"], "zoom": 18}}},
		meta={},
		blocks=[{"name": "Block 1", "enabled": True, "displayName": "Block 1"}],
	)


def test_handle_processing_submission_uses_template_run_when_template_selected():
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.dlg = MagicMock()
	service.dlg.cornfirmProcessingStart.isChecked.return_value = False
	service.dlg.modelCombo.currentText.return_value = "Buildings"
	service.iface = MagicMock()
	service.app_context = SimpleNamespace(plugin_name="Mapflow")
	service.api = MagicMock()
	service.start_processing_callback = MagicMock()
	service.start_processing_error_handler = MagicMock()
	service.selected_template = MagicMock(return_value=SimpleNamespace(id="template-1"))

	service.handle_processing_submission(_processing_payload())

	service.api.run_template_processing.assert_called_once()
	kwargs = service.api.run_template_processing.call_args.kwargs
	assert kwargs["template_id"] == "template-1"
	assert isinstance(kwargs["data"], RunTemplateProcessingSchema)
	assert kwargs["data"].wdId == "wd-1"
	assert kwargs["data"].wdName is None
	assert kwargs["data"].updateTemplateGeometry is False
	service.api.create_processing.assert_not_called()


def test_handle_processing_submission_uses_regular_processing_when_no_template_selected():
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.dlg = MagicMock()
	service.dlg.cornfirmProcessingStart.isChecked.return_value = False
	service.iface = MagicMock()
	service.app_context = SimpleNamespace(plugin_name="Mapflow")
	service.api = MagicMock()
	service.start_processing_callback = MagicMock()
	service.start_processing_error_handler = MagicMock()
	service.selected_template = MagicMock(return_value=None)

	payload = _processing_payload()
	service.handle_processing_submission(payload)

	service.api.create_processing.assert_called_once_with(
		payload,
		service.start_processing_callback,
		service.start_processing_error_handler,
	)
	service.api.run_template_processing.assert_not_called()


def test_planned_processing_selection_error_requires_selected_metadata_rows():
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.dlg = MagicMock()
	service.selected_template = MagicMock(return_value=SimpleNamespace(id="template-1"))
	service.selected_processing = MagicMock(return_value=None)

	service.dlg.metadataTable.selectedItems.return_value = []
	assert service.planned_processing_selection_error() == (
		"Select one or more images in search results to start planned processing"
	)

	selected_item = MagicMock()
	selected_item.row.return_value = 0
	service.dlg.metadataTable.selectedItems.return_value = [selected_item]
	assert service.planned_processing_selection_error() is None


def test_on_processings_selection_changed_sets_planned_start_button_text():
	plugin = Mapflow.__new__(Mapflow)
	plugin.tr = lambda text: text
	plugin.dlg = MagicMock()
	plugin.processing_service = MagicMock()
	plugin.processing_service.selected_template.return_value = SimpleNamespace(id="template-1")
	plugin.processing_service.selected_processing.return_value = None
	plugin.processing_service.planned_processing_selection_error.return_value = (
		"Select one or more images in search results to start planned processing"
	)

	plugin.on_processings_selection_changed()

	plugin.dlg.startProcessing.setText.assert_called_with("Start planned processing")
	plugin.dlg.disable_processing_start.assert_called_once()
	assert plugin.active_template_id == "template-1"


def test_on_processings_selection_changed_restores_default_start_button_text_without_template():
	plugin = Mapflow.__new__(Mapflow)
	plugin.tr = lambda text: text
	plugin.dlg = MagicMock()
	plugin.dlg.processingProblemsLabel.text.return_value = (
		"Select one or more images in search results to start planned processing"
	)
	plugin.processing_service = MagicMock()
	plugin.processing_service.selected_template.return_value = None
	plugin.processing_service.selected_processing.return_value = None
	plugin.processing_service.planned_processing_selection_error.return_value = None

	plugin.on_processings_selection_changed()

	plugin.dlg.startProcessing.setText.assert_called_with("Start processing")
	plugin.dlg.startProcessing.setEnabled.assert_called_with(True)
	plugin.dlg.processingProblemsLabel.clear.assert_called_once()
	plugin.dlg.disable_processing_start.assert_not_called()
	assert plugin.active_template_id is None


def test_on_processings_selection_changed_restores_default_when_processing_selected():
	plugin = Mapflow.__new__(Mapflow)
	plugin.tr = lambda text: text
	plugin.dlg = MagicMock()
	plugin.dlg.processingProblemsLabel.text.return_value = (
		"Select one or more images in search results to start planned processing"
	)
	plugin.processing_service = MagicMock()
	plugin.processing_service.selected_template.return_value = SimpleNamespace(id="template-1")
	plugin.processing_service.selected_processing.return_value = SimpleNamespace(id="processing-1")
	plugin.processing_service.planned_processing_selection_error.return_value = None

	plugin.on_processings_selection_changed()

	plugin.dlg.startProcessing.setText.assert_called_with("Start processing")
	plugin.dlg.startProcessing.setEnabled.assert_called_with(True)
	plugin.dlg.processingProblemsLabel.clear.assert_called_once()
	plugin.dlg.disable_processing_start.assert_not_called()


def test_load_results_double_click_template_triggers_both_actions():
	plugin = Mapflow.__new__(Mapflow)
	plugin.processing_service = MagicMock()
	plugin.processing_service.selected_template.return_value = SimpleNamespace(id="template-1")
	plugin.select_template_processings = MagicMock()
	plugin.show_template_search_results = MagicMock()

	plugin.load_results()

	plugin.select_template_processings.assert_called_once()
	plugin.show_template_search_results.assert_called_once()


def test_start_processing_callback_refreshes_processings_for_regular_response():
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.dlg = MagicMock()
	service.view = MagicMock()
	service.processing_fetch_timer = MagicMock()
	service.processings = {}
	service.processings_history = MagicMock()
	service.get_processings = MagicMock()

	response = MagicMock()
	response.readAll.return_value.data.return_value = b'{"id": "proc-1", "name": "Run 1"}'
	mock_processing = SimpleNamespace(id="proc-1", name="Run 1", status=SimpleNamespace())

	with patch.object(processing_service_module, "alert"), \
			patch.object(processing_service_module.ProcessingDTO, "from_dict", return_value=mock_processing):
		service.start_processing_callback(response)

	service.get_processings.assert_called_once()
	service.view.add_new_processing.assert_called_once()
	service.dlg.startProcessing.setEnabled.assert_called_with(True)


def test_start_processing_callback_refreshes_processings_for_template_response_shape():
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.dlg = MagicMock()
	service.view = MagicMock()
	service.processing_fetch_timer = MagicMock()
	service.processings = {}
	service.processings_history = MagicMock()
	service.get_processings = MagicMock()

	response = MagicMock()
	response.readAll.return_value.data.return_value = b'{"template": {"id": "tpl-1"}, "searchResults": []}'

	with patch.object(processing_service_module, "alert"):
		service.start_processing_callback(response)

	service.get_processings.assert_called_once()
	service.view.add_new_processing.assert_not_called()
	service.dlg.startProcessing.setEnabled.assert_called_with(True)


def test_disable_processing_start_uses_fallback_when_api_message_is_none():
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.view = MagicMock()
	service.app_context = SimpleNamespace(
		user_role=SimpleNamespace(can_start_processing=True, value="owner")
	)

	response = MagicMock()
	response.readAll.return_value.data.return_value = b"{}"
	response.errorString.return_value = ""

	with patch.object(processing_service_module, "api_message_parser", return_value=None):
		service.disable_processing_start(response)

	service.view.disable_processing_start.assert_called_once_with(
		"Processing cost is not available:\nUnknown server error",
		clear_area=False,
	)
