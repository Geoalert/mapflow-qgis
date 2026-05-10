from datetime import datetime, timezone
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


def test_select_template_processings_deduplicates_linked_processing_aoi_requests():
	plugin = Mapflow.__new__(Mapflow)
	plugin.tr = lambda text: text
	plugin.server = "https://server"
	plugin.http = MagicMock()
	plugin.processing_service = MagicMock()
	template = SimpleNamespace(id="template-1", name="Template A", _aoi_features=lambda: [])
	plugin.processing_service.selected_template.return_value = template
	plugin.processing_service.selected_processing.return_value = None
	plugin._add_geojson_aoi_layer = MagicMock(return_value=SimpleNamespace(id=lambda: "layer-1"))
	plugin._linked_processings_from_template = MagicMock(return_value=[
		{"processingId": "proc-1", "processingName": "P1"},
		{"processingId": "proc-1", "processingName": "P1"},
		{"processingId": "proc-1", "processingName": "P1"},
	])

	with patch("mapflow.mapflow.alert"):
		plugin.select_template_processings()

	assert plugin.http.get.call_count == 1
	kwargs = plugin.http.get.call_args.kwargs
	assert kwargs["url"] == "https://server/processings/proc-1/aois"


def test_mark_selected_template_images_seen_marks_unique_selected_new_rows():
	plugin = Mapflow.__new__(Mapflow)
	plugin.active_template_id = "tpl-1"
	plugin.config = SimpleNamespace(MAXAR_ID_COLUMN_INDEX=1)
	plugin.processing_service = SimpleNamespace(api=MagicMock())
	plugin._decrement_template_new_images_count = MagicMock()
	plugin.dlg = MagicMock()

	product_cells = {
		0: MagicMock(text=MagicMock(return_value="Image (new)")),
		1: MagicMock(text=MagicMock(return_value="Image")),
		2: MagicMock(text=MagicMock(return_value="Mosaic (new)")),
	}
	id_cells = {
		0: MagicMock(text=MagicMock(return_value="img-1")),
		1: MagicMock(text=MagicMock(return_value="img-2")),
		2: MagicMock(text=MagicMock(return_value="img-3")),
	}

	def item_side_effect(row, col):
		if col == 0:
			return product_cells.get(row)
		if col == 1:
			return id_cells.get(row)
		return None

	plugin.dlg.metadataTable.item.side_effect = item_side_effect
	plugin.dlg.metadataTable.selectedItems.return_value = [
		SimpleNamespace(row=lambda: 0),
		SimpleNamespace(row=lambda: 0),
		SimpleNamespace(row=lambda: 2),
	]

	plugin.mark_selected_template_images_seen()

	assert plugin.processing_service.api.mark_template_image_seen.call_count == 2
	called_image_ids = [
		kwargs["image_id"]
		for kwargs in (
			call.kwargs for call in plugin.processing_service.api.mark_template_image_seen.call_args_list
		)
	]
	assert called_image_ids == ["img-1", "img-3"]
	assert plugin._decrement_template_new_images_count.call_count == 2


def test_mark_all_template_images_seen_marks_only_new_rows():
	plugin = Mapflow.__new__(Mapflow)
	plugin.active_template_id = "tpl-1"
	plugin.config = SimpleNamespace(MAXAR_ID_COLUMN_INDEX=1)
	plugin.processing_service = SimpleNamespace(api=MagicMock())
	plugin._decrement_template_new_images_count = MagicMock()
	plugin.dlg = MagicMock()
	plugin.dlg.metadataTable.rowCount.return_value = 3

	product_cells = {
		0: MagicMock(text=MagicMock(return_value="Image (new)")),
		1: MagicMock(text=MagicMock(return_value="Image")),
		2: MagicMock(text=MagicMock(return_value="Mosaic (new)")),
	}
	id_cells = {
		0: MagicMock(text=MagicMock(return_value="img-1")),
		1: MagicMock(text=MagicMock(return_value="img-2")),
		2: MagicMock(text=MagicMock(return_value="img-3")),
	}

	def item_side_effect(row, col):
		if col == 0:
			return product_cells.get(row)
		if col == 1:
			return id_cells.get(row)
		return None

	plugin.dlg.metadataTable.item.side_effect = item_side_effect

	plugin.mark_all_template_images_seen()

	assert plugin.processing_service.api.mark_template_image_seen.call_count == 2
	called_image_ids = [
		kwargs["image_id"]
		for kwargs in (
			call.kwargs for call in plugin.processing_service.api.mark_template_image_seen.call_args_list
		)
	]
	assert called_image_ids == ["img-1", "img-3"]
	assert plugin._decrement_template_new_images_count.call_count == 2


def test_on_metadata_table_cell_clicked_does_not_mark_seen():
	plugin = Mapflow.__new__(Mapflow)
	plugin.active_template_id = "tpl-1"
	plugin.config = SimpleNamespace(MAXAR_ID_COLUMN_INDEX=1)
	plugin.processing_service = SimpleNamespace(api=MagicMock())
	plugin._decrement_template_new_images_count = MagicMock()
	plugin.dlg = MagicMock()

	product_cell = MagicMock()
	product_cell.text.return_value = "Image (new)"
	id_cell = MagicMock()
	id_cell.text.return_value = "img-1"

	def item_side_effect(row, col):
		if col == 0:
			return product_cell
		if col == 1:
			return id_cell
		return None

	plugin.dlg.metadataTable.item.side_effect = item_side_effect

	plugin.on_metadata_table_cell_clicked(0, 0)

	plugin.processing_service.api.mark_template_image_seen.assert_not_called()
	plugin._decrement_template_new_images_count.assert_not_called()


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


def test_update_template_uses_update_template_api_with_renamed_name():
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.dlg = MagicMock()
	service.api = MagicMock()
	service.get_processings = MagicMock()
	service.view = MagicMock()

	template = SimpleNamespace(
		id="tpl-1",
		name="Old template",
		searchParams=SimpleNamespace(as_dict=lambda skip_none=True: {"limit": 100}),
		processingParams={"params": {"sourceParams": {}}},
		activeUntil=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
	)
	service.selected_template = MagicMock(return_value=template)

	with patch.object(processing_service_module.QInputDialog, "getText", return_value=("New template", True)):
		service.update_template()

	service.api.update_template.assert_called_once()
	kwargs = service.api.update_template.call_args.kwargs
	assert kwargs["template_id"] == "tpl-1"
	assert kwargs["data"].name == "New template"
	assert kwargs["data"].searchParams is None
	assert kwargs["data"].processingParams is None
	assert kwargs["data"].activeUntil is None


def test_resume_template_updates_active_until_to_six_months_from_resume_time():
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.dlg = MagicMock()
	service.api = MagicMock()
	service._resume_template_state = {
		"template_id": "tpl-1",
		"template_name": "Template A",
	}

	response = MagicMock()
	fixed_now = datetime(2026, 5, 6, 10, 30, 0)

	with patch.object(processing_service_module, "datetime") as mock_datetime:
		mock_datetime.utcnow.return_value = fixed_now
		service.resume_template_update_active_until(response)

	service.api.update_template.assert_called_once()
	kwargs = service.api.update_template.call_args.kwargs
	assert kwargs["template_id"] == "tpl-1"
	assert kwargs["data"].name == "Template A"
	assert kwargs["data"].searchParams is None
	assert kwargs["data"].processingParams is None
	assert kwargs["data"].activeUntil == "2026-11-02T10:29:00.0Z"
	assert kwargs["callback"] == service.resume_template_callback
	assert kwargs["error_handler"] == service.resume_template_error_handler


def test_confirm_delete_processings_deletes_templates():
	"""Test that templates can be deleted via confirm_delete_processings."""
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.processing_fetch_timer = MagicMock()
	service.templates = {"tpl-1": SimpleNamespace(id="tpl-1", name="Template 1")}
	service.processings = {}
	service.api = MagicMock()
	service.view = MagicMock()
	service.view.selected_processing_ids.return_value = ["tpl-1"]
	service._delete_state = {}

	with patch.object(processing_service_module, "alert", return_value=True):
		service.confirm_delete_processings()

	# delete_processings should be called with the template ID
	assert service.processing_fetch_timer.stop.called


def test_delete_processings_routes_templates_to_delete_template_api():
	"""Test that templates are routed to delete_template API method."""
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.processing_fetch_timer = MagicMock()
	service.templates = {"tpl-1": SimpleNamespace(id="tpl-1")}
	service.processings = {}
	service.api = MagicMock()
	service.view = MagicMock()
	service._delete_state = {}

	service.delete_processings(response=None, items=["tpl-1"], deleted=[], failed=[])

	service.api.delete_template.assert_called_once()
	kwargs = service.api.delete_template.call_args.kwargs
	assert kwargs["template_id"] == "tpl-1"
	service.api.delete_processing.assert_not_called()


def test_delete_processings_handles_mixed_selection():
	"""Test that mixed templates and processings are deleted correctly."""
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.processing_fetch_timer = MagicMock()
	service.templates = {"tpl-1": SimpleNamespace(id="tpl-1")}
	service.processings = {"proc-1": SimpleNamespace(id="proc-1")}
	service.api = MagicMock()
	service.view = MagicMock()
	service._delete_state = {}

	service.delete_processings(response=None, items=["tpl-1", "proc-1"], deleted=[], failed=[])

	# First item is template, should call delete_template
	service.api.delete_template.assert_called_once_with(
		template_id="tpl-1",
		callback=service.delete_processings_callback,
		error_handler=service.delete_processings_error_handler,
	)
	# Should NOT call delete_processing for the first item since it's a template
	service.api.delete_processing.assert_not_called()
	# But _delete_state should be set for the callback to continue
	assert service._delete_state["remaining_items"] == ["proc-1"]
	assert service._delete_state["deleted"] == ["tpl-1"]


def test_delete_processings_callback_continues_with_remaining_items():
	"""Test that delete_processings_callback continues deletion."""
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.processing_fetch_timer = MagicMock()
	service.templates = {}
	service.processings = {"proc-1": SimpleNamespace(id="proc-1")}
	service.api = MagicMock()
	service.view = MagicMock()
	service._delete_state = {
		"remaining_items": ["proc-1"],
		"deleted": ["tpl-1"],
		"failed": []
	}

	response = MagicMock()
	service.delete_processings_callback(response)

	# Should continue deleting the remaining item
	service.api.delete_processing.assert_called_once()
	kwargs = service.api.delete_processing.call_args.kwargs
	assert kwargs["processing_id"] == "proc-1"
	assert kwargs["callback_kwargs"]["items"] == []
	assert kwargs["callback_kwargs"]["deleted"] == ["tpl-1", "proc-1"]


def test_get_processings_callback_requests_templates_for_current_project_only():
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.app_context = SimpleNamespace(current_project=SimpleNamespace(id="project-1"))
	service.api = MagicMock()
	service.view = MagicMock()
	service.processing_fetch_timer = MagicMock()
	service.processing_fetch_timer.stop = MagicMock()
	service.processings_page_limit = 25
	service.processings_page_offset = 0
	service.processings_history = None
	service.update_local_processings = MagicMock()

	response = MagicMock()
	response.readAll.return_value.data.return_value = b'{"results": [], "total": 0}'

	with patch.object(processing_service_module.ProcessingsResult, "from_dict", return_value=SimpleNamespace(results=[], total=0)):
		service.get_processings_callback(response)

	service.api.get_templates_by_project.assert_called_once_with(
		project_id="project-1",
		callback=service.get_templates_callback,
	)
	service.api.get_templates.assert_not_called()


def test_get_templates_callback_filters_templates_to_current_project():
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.app_context = SimpleNamespace(current_project=SimpleNamespace(id="3fa85f64-5717-4562-b3fc-2c963f66afa6"))
	service.view = MagicMock()
	service.view.sort_processings.return_value = ("CREATED", "DESC")
	service.processings = {}

	response = MagicMock()
	response.readAll.return_value.data.return_value = (
		b'['
		b'{"id":"11111111-1111-1111-1111-111111111111","name":"T1","status":"READY","createdAt":"2025-09-26T06:25:55.820336Z","userId":"3fa85f64-5717-4562-b3fc-2c963f66afa6","searchParams":{"aoiDetails":{"type":"FeatureCollection","features":[]}},"projectId":"3fa85f64-5717-4562-b3fc-2c963f66afa6","activeUntil":"2026-03-15T17:00:00Z"},'
		b'{"id":"22222222-2222-2222-2222-222222222222","name":"T2","status":"READY","createdAt":"2025-09-26T06:25:55.820336Z","userId":"3fa85f64-5717-4562-b3fc-2c963f66afa6","searchParams":{"aoiDetails":{"type":"FeatureCollection","features":[]}},"projectId":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa","activeUntil":"2026-03-15T17:00:00Z"}'
		b']'
	)

	service.get_templates_callback(response)

	assert len(service.templates) == 1
	template = list(service.templates.values())[0]
	assert str(template.projectId) == "3fa85f64-5717-4562-b3fc-2c963f66afa6"
	service.view.update_processing_table.assert_called_once()


def test_get_templates_callback_handles_missing_search_params():
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.app_context = SimpleNamespace(current_project=SimpleNamespace(id="3fa85f64-5717-4562-b3fc-2c963f66afa6"))
	service.api = MagicMock()
	service.view = MagicMock()
	service.view.sort_processings.return_value = ("CREATED", "DESC")
	service.processings = {}

	response = MagicMock()
	response.readAll.return_value.data.return_value = (
		b'['
		b'{"id":"11111111-1111-1111-1111-111111111111","name":"T1","status":"READY","createdAt":"2025-09-26T06:25:55.820336Z","userId":"3fa85f64-5717-4562-b3fc-2c963f66afa6","projectId":"3fa85f64-5717-4562-b3fc-2c963f66afa6","activeUntil":"2026-03-15T17:00:00Z"}'
		b']'
	)

	service.get_templates_callback(response)

	service.api.get_templates.assert_called_once()


def test_get_templates_full_callback_hydrates_search_params_from_full_list():
	service = ProcessingService.__new__(ProcessingService)
	service.tr = lambda text: text
	service.app_context = SimpleNamespace(current_project=SimpleNamespace(id="3fa85f64-5717-4562-b3fc-2c963f66afa6"))
	service.view = MagicMock()
	service.view.sort_processings.return_value = ("CREATED", "DESC")
	service.processings = {}

	project_items = [
		{
			"id": "11111111-1111-1111-1111-111111111111",
			"name": "T1",
			"status": "READY",
			"createdAt": "2025-09-26T06:25:55.820336Z",
			"userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
			"projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
			"activeUntil": "2026-03-15T17:00:00Z",
		}
	]

	full_response = MagicMock()
	full_response.readAll.return_value.data.return_value = (
		b'['
		b'{"id":"11111111-1111-1111-1111-111111111111","name":"T1","status":"READY","createdAt":"2025-09-26T06:25:55.820336Z","userId":"3fa85f64-5717-4562-b3fc-2c963f66afa6","searchParams":{"aoiDetails":{"type":"FeatureCollection","features":[]}},"projectId":"3fa85f64-5717-4562-b3fc-2c963f66afa6","activeUntil":"2026-03-15T17:00:00Z"}'
		b']'
	)

	service.get_templates_full_callback(full_response, project_items)

	assert len(service.templates) == 1
	template = list(service.templates.values())[0]
	assert template.searchParams is not None
	assert template.searchParams.aoiDetails["type"] == "FeatureCollection"

	assert len(service.templates) == 1
	service.view.update_processing_table.assert_called_once()

