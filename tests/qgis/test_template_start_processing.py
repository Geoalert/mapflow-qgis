import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from mapflow.functional.controller.template_controller import TemplateController
from mapflow.functional.service import processing_service as processing_service_module
from mapflow.functional.service import template_service as template_service_module
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.functional.service.template_service import TemplateService
from mapflow.functional.view.template_view import TemplateView
from mapflow.mapflow import Mapflow
from mapflow.schema.processing import PostProcessingSchemaV2
from mapflow.schema.template import RunTemplateProcessingSchema


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
    # A template run happens iff template_to_run() resolves (template + imagery-search source + open results).
    service.template_to_run = MagicMock(return_value=SimpleNamespace(id="template-1"))

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
    # Planned image gate applies only when a planned start applies (template_to_run resolves).
    service.template_to_run = MagicMock(return_value=SimpleNamespace(id="template-1"))

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

    plugin.app_context = SimpleNamespace(user_role=None)  # non-contributor: delete-button update is a no-op
    plugin.on_processings_selection_changed()

    plugin.dlg.startProcessing.setText.assert_called_with("Start planned processing")
    plugin.dlg.disable_processing_start.assert_called_once()


def test_on_processings_selection_changed_restores_default_start_button_text_without_template():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.dlg = MagicMock()
    plugin.dlg.processingProblemsLabel.text.return_value = (
        "Select one or more images in search results to start planned processing"
    )
    plugin.processing_service = MagicMock()
    plugin.processing_service.selected_template.return_value = None
    plugin.processing_service.template_to_run.return_value = None
    plugin.processing_service.planned_processing_selection_error.return_value = None

    plugin.app_context = SimpleNamespace(user_role=None)  # non-contributor: delete-button update is a no-op
    plugin.on_processings_selection_changed()

    plugin.dlg.startProcessing.setText.assert_called_with("Start processing")
    plugin.dlg.startProcessing.setEnabled.assert_called_with(True)
    plugin.dlg.processingProblemsLabel.clear.assert_called_once()
    plugin.dlg.disable_processing_start.assert_not_called()


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
    # A processing is also selected -> not a planned start.
    plugin.processing_service.template_to_run.return_value = None
    plugin.processing_service.planned_processing_selection_error.return_value = None

    plugin.app_context = SimpleNamespace(user_role=None)  # non-contributor: delete-button update is a no-op
    plugin.on_processings_selection_changed()

    plugin.dlg.startProcessing.setText.assert_called_with("Start processing")
    plugin.dlg.startProcessing.setEnabled.assert_called_with(True)
    plugin.dlg.processingProblemsLabel.clear.assert_called_once()
    plugin.dlg.disable_processing_start.assert_not_called()


def test_load_results_double_click_template_enters_template_view():
    """Double-clicking a template navigates 'one step right' via the controller."""
    plugin = Mapflow.__new__(Mapflow)
    plugin.processing_service = MagicMock()
    template = SimpleNamespace(id="template-1")
    plugin.processing_service.selected_template.return_value = template
    plugin.project_processing_controller = MagicMock()

    plugin.load_results()

    plugin.project_processing_controller.enter_template.assert_called_once_with(template)


def test_enter_template_view_hydrated_skips_refetch():
    """A template that already carries its AOIs is entered without a refetch."""
    service = ProcessingService.__new__(ProcessingService)
    service.api = MagicMock()
    service.templates = {}
    service._do_enter_template = MagicMock()
    template = SimpleNamespace(id="template-1", aoi_dtos=lambda: [object()])

    service.enter_template_view(template)

    service._do_enter_template.assert_called_once_with(template)
    service.api.get_template.assert_not_called()


def test_enter_template_view_unhydrated_fetches_then_enters():
    """A template missing its AOIs (project poll omits searchParams) is hydrated first."""
    service = ProcessingService.__new__(ProcessingService)
    service.api = MagicMock()
    service.templates = {}
    service._do_enter_template = MagicMock()
    template = SimpleNamespace(id="template-1", aoi_dtos=lambda: [])

    service.enter_template_view(template)

    service.api.get_template.assert_called_once()
    assert service.api.get_template.call_args.kwargs["template_id"] == "template-1"
    service._do_enter_template.assert_not_called()

    hydrated_payload = {
        "template": {
            "id": "template-1",
            "name": "T1",
            "status": "READY",
            "createdAt": "2025-09-26T06:25:55.820336Z",
            "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "searchParams": {"aoiDetails": {"type": "FeatureCollection", "features": []}},
            "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "activeUntil": "2026-03-15T17:00:00Z",
        }
    }
    response = MagicMock()
    response.readAll.return_value.data.return_value = json.dumps(hydrated_payload).encode()
    callback = service.api.get_template.call_args.kwargs["callback"]

    callback(response)

    assert "template-1" in service.templates
    service._do_enter_template.assert_called_once()


def test_load_template_layers_builds_per_aoi_subgroups_from_aoidetails():
    """Each AOI becomes a subgroup with its polygon (blue) + its processings (green),
    all from aoiDetails — no per-processing AOI requests."""
    from mapflow.schema.template import AoiProcessingLink, TemplateAoiDTO

    service = TemplateService(app_context=MagicMock(), processing_service=MagicMock())
    service.add_geojson_aoi_layer = MagicMock()

    geom = {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [0, 0]]]}
    proc_geom = {"type": "Polygon", "coordinates": [[[0, 0], [0, 2], [2, 2], [0, 0]]]}
    aoi = TemplateAoiDTO(
        id="a1", name="North", geometry=geom,
        processings=[AoiProcessingLink(processingId="p1", processingName="P1", geometry=proc_geom)],
    )
    template = SimpleNamespace(name="Template A", aoi_dtos=lambda: [aoi])

    service.load_template_layers(template)

    # One AOI (blue) layer + one processing (green) layer, both in the AOI's subgroup.
    assert service.add_geojson_aoi_layer.call_count == 2
    styles = [c.kwargs["style_name"] for c in service.add_geojson_aoi_layer.call_args_list]
    assert styles == ["aoi_template_blue.qml", "aoi_template_processing_green.qml"]
    subgroups = {c.kwargs["subgroup_name"] for c in service.add_geojson_aoi_layer.call_args_list}
    assert subgroups == {"AOI: North"}


# ---------- seen markers: TemplateService (DTO+api) + TemplateController (loop) + TemplateView (icons) ----------

def _seen_setup(selected_rows=None, open_id="tpl-1", active_template=None):
    """Rows 0 (img-1, new), 1 (img-2, seen), 2 (img-3, new). Real service + view (mock dlg) +
    controller; the icon set is what the tests observe, so the view is real."""
    dlg = MagicMock()
    dlg.metadataTable.rowCount.return_value = 3
    dlg.metadataTable.columnCount.return_value = 3
    dlg.metadataTable.isColumnHidden.return_value = False
    id_cells = {0: MagicMock(text=MagicMock(return_value="img-1")),
                1: MagicMock(text=MagicMock(return_value="img-2")),
                2: MagicMock(text=MagicMock(return_value="img-3"))}
    marker_cells = {0: MagicMock(), 1: MagicMock(), 2: MagicMock()}
    dlg.metadataTable.item.side_effect = (
        lambda row, col: id_cells.get(row) if col == 1 else marker_cells.get(row) if col == 0 else None)
    if selected_rows is not None:
        dlg.metadataTable.selectedItems.return_value = [
            SimpleNamespace(row=lambda r=r: r) for r in selected_rows]

    config = SimpleNamespace(SEARCH_ID_COLUMN_INDEX=1, NEW_IMAGE_MARKER_COLUMN_INDEX=0)
    app_context = SimpleNamespace(open_template_results_id=open_id, plugin_name="Mapflow")
    # The in-memory template DTO whose newImagesCount the seen flow decrements.
    template_dto = SimpleNamespace(id=open_id or (active_template.id if active_template else None),
                                   newImagesCount=2)
    processing_service = SimpleNamespace(api=MagicMock(), active_template=active_template,
                                         templates={template_dto.id: template_dto})
    service = TemplateService(app_context=app_context, processing_service=processing_service)
    service.template_search_images = {
        "img-1": SimpleNamespace(id="img-1", isNew=True, productType="Image"),
        "img-2": SimpleNamespace(id="img-2", isNew=False, productType="Image"),
        "img-3": SimpleNamespace(id="img-3", isNew=True, productType="Mosaic")}
    view = TemplateView(dlg=dlg, iface=MagicMock(), config=config)
    controller = TemplateController.__new__(TemplateController)
    controller.template_service = service
    controller.template_view = view
    template_dto = processing_service.templates[template_dto.id]
    return controller, service, view, marker_cells, template_dto


def test_mark_selected_template_images_seen_requests_only_new_rows_and_defers_update():
    # Select rows 0 (new), 1 (SEEN — must be skipped), 2 (new).
    controller, service, view, marker_cells, template = _seen_setup(selected_rows=[0, 1, 2])
    api = service.processing_service.api

    controller.mark_selected_images_seen()

    # A request per selected NEW row only — the seen row (img-2) is gated out; update deferred.
    assert [c.kwargs["image_id"] for c in api.mark_template_image_seen.call_args_list] == ["img-1", "img-3"]
    marker_cells[0].setIcon.assert_not_called()
    assert template.newImagesCount == 2  # not decremented until the requests succeed

    for c in api.mark_template_image_seen.call_args_list:
        c.kwargs["callback"](MagicMock())

    # Marker cleared per row after its request succeeds; counter decremented once per success.
    assert marker_cells[0].setIcon.call_args.args[0].isNull()
    assert marker_cells[2].setIcon.call_args.args[0].isNull()
    assert service.template_search_images["img-1"].isNew is False
    assert service.template_search_images["img-3"].isNew is False
    assert template.newImagesCount == 0  # 2 - 2 successes


def test_mark_all_template_images_seen_uses_single_endpoint_and_defers_update():
    controller, service, view, marker_cells, _ = _seen_setup()
    api = service.processing_service.api

    controller.mark_all_images_seen()

    api.mark_all_template_images_seen.assert_called_once()
    assert api.mark_all_template_images_seen.call_args.kwargs["template_id"] == "tpl-1"
    api.mark_template_image_seen.assert_not_called()
    marker_cells[0].setIcon.assert_not_called()

    api.mark_all_template_images_seen.call_args.kwargs["callback"](MagicMock())

    # Only the NEW rows (0, 2) get their marker icon cleared; the seen row (1) is untouched.
    assert marker_cells[0].setIcon.call_args.args[0].isNull()
    assert marker_cells[2].setIcon.call_args.args[0].isNull()
    marker_cells[1].setIcon.assert_not_called()


def test_seen_works_inside_the_template_view():
    """Regression: the template id used to come from the processings-table selection, which is
    None inside the in-template view — so Seen / Seen all silently sent no request. It must
    resolve from the results actually on screen."""
    controller, service, _, _, _ = _seen_setup(selected_rows=[0],
                                            active_template=SimpleNamespace(id="tpl-1"))
    api = service.processing_service.api

    controller.mark_all_images_seen()
    controller.mark_selected_images_seen()

    api.mark_all_template_images_seen.assert_called_once()
    assert api.mark_all_template_images_seen.call_args.kwargs["template_id"] == "tpl-1"
    assert api.mark_template_image_seen.call_count > 0


def test_seen_falls_back_to_the_open_template_when_results_id_missing():
    controller, service, _, _, _ = _seen_setup(open_id=None,
                                            active_template=SimpleNamespace(id="tpl-7"))

    controller.mark_all_images_seen()

    kwargs = service.processing_service.api.mark_all_template_images_seen.call_args.kwargs
    assert kwargs["template_id"] == "tpl-7"


def test_seen_noop_without_any_template_context():
    controller, service, _, _, _ = _seen_setup(selected_rows=[0], open_id=None, active_template=None)

    controller.mark_all_images_seen()
    controller.mark_selected_images_seen()

    service.processing_service.api.mark_all_template_images_seen.assert_not_called()
    service.processing_service.api.mark_template_image_seen.assert_not_called()


def test_mark_seen_error_leaves_marker_and_counter_untouched():
    controller, service, view, marker_cells, _ = _seen_setup(selected_rows=[0])
    warnings = []
    service.warningMessage.connect(warnings.append)
    api = service.processing_service.api

    controller.mark_selected_images_seen()
    api.mark_template_image_seen.call_args.kwargs["error_handler"](MagicMock())

    marker_cells[0].setIcon.assert_not_called()
    assert service.template_search_images["img-1"].isNew is True
    assert len(warnings) == 1


def test_apply_new_image_markers_sets_icon_only_on_new_rows():
    controller, service, view, marker_cells, _ = _seen_setup()

    controller.apply_new_image_markers()

    assert not marker_cells[0].setIcon.call_args.args[0].isNull()  # new image -> exclamation icon
    assert marker_cells[1].setIcon.call_args.args[0].isNull()      # seen image -> icon cleared
    assert not marker_cells[2].setIcon.call_args.args[0].isNull()


def test_new_image_marker_column_skips_hidden_leftmost_column():
    dlg = MagicMock()
    dlg.metadataTable.columnCount.return_value = 4
    # User hid column 0 -> marker falls back to the leftmost visible column (1).
    dlg.metadataTable.isColumnHidden.side_effect = lambda col: col == 0
    view = TemplateView(dlg=dlg, iface=MagicMock(),
                        config=SimpleNamespace(NEW_IMAGE_MARKER_COLUMN_INDEX=0))

    assert view._new_image_marker_column() == 1


def test_on_metadata_table_cell_clicked_does_not_mark_seen():
    plugin = Mapflow.__new__(Mapflow)
    plugin.app_context = SimpleNamespace(open_template_results_id="tpl-1")
    plugin.processing_service = SimpleNamespace(api=MagicMock(), active_template=None)
    plugin._decrement_template_new_images_count = MagicMock()
    plugin.dlg = MagicMock()

    plugin.on_metadata_table_cell_clicked(0, 0)

    # Clicking a cell is passive; marking is only via the Seen / Seen all actions.
    plugin.processing_service.api.mark_template_image_seen.assert_not_called()
    plugin.processing_service.api.mark_all_template_images_seen.assert_not_called()
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


def _rename_service(name="Old template"):
    template = SimpleNamespace(
        id="tpl-1",
        name=name,
        searchParams=SimpleNamespace(as_dict=lambda skip_none=True: {"limit": 100}),
        processingParams={"params": {"sourceParams": {}}},
        activeUntil=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    processing_service = SimpleNamespace(
        selected_template=lambda: template, api=MagicMock(),
        get_processings=MagicMock(), templates={})
    return TemplateService(app_context=MagicMock(), processing_service=processing_service)


def test_rename_template_uses_update_template_api_with_renamed_name(monkeypatch):
    service = _rename_service()
    monkeypatch.setattr(template_service_module, "ask_text",
                        lambda *a, **k: ("New template", True))

    service.rename_template()

    service.processing_service.api.update_template.assert_called_once()
    kwargs = service.processing_service.api.update_template.call_args.kwargs
    assert kwargs["template_id"] == "tpl-1"
    assert kwargs["data"].name == "New template"
    assert kwargs["data"].searchParams is None
    assert kwargs["data"].processingParams is None
    assert kwargs["data"].activeUntil is None


def test_rename_template_asks_through_the_message_tier_not_a_dialog(monkeypatch):
    """The service holds no widget, so the name is asked for through AlertService."""
    service = _rename_service()
    asked = []
    monkeypatch.setattr(template_service_module, "ask_text",
                        lambda *a, **k: (asked.append((a, k)), ("New", True))[1])

    service.rename_template()

    assert asked, "the new name must come from the message tier"
    assert asked[0][1]["default"] == "Old template"  # pre-filled with the current name


def test_rename_template_cancelled_sends_nothing(monkeypatch):
    service = _rename_service()
    monkeypatch.setattr(template_service_module, "ask_text", lambda *a, **k: ("Whatever", False))

    service.rename_template()

    service.processing_service.api.update_template.assert_not_called()


def test_rename_template_rejects_a_blank_name(monkeypatch):
    service = _rename_service()
    monkeypatch.setattr(template_service_module, "ask_text", lambda *a, **k: ("   ", True))
    warnings = []
    monkeypatch.setattr(template_service_module, "alert_warning", warnings.append)

    service.rename_template()

    service.processing_service.api.update_template.assert_not_called()
    assert warnings


def test_rename_template_unchanged_name_sends_nothing(monkeypatch):
    service = _rename_service()
    monkeypatch.setattr(template_service_module, "ask_text", lambda *a, **k: ("Old template", True))

    service.rename_template()

    service.processing_service.api.update_template.assert_not_called()


def _renamed_template_payload(name="New template"):
    return {
        "id": "tpl-1",
        "name": name,
        "status": "READY",
        "createdAt": "2025-09-26T06:25:55.820336Z",
        "userId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "projectId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "activeUntil": "2026-03-15T17:00:00Z",
    }


def test_rename_callback_shows_the_new_name_before_the_list_refreshes():
    """The renamed row is updated straight away; the controller drives the view from this."""
    service = _rename_service()
    renamed = []
    service.templateRenamed.connect(lambda tid, name: renamed.append((tid, name)))
    response = MagicMock()
    response.readAll.return_value.data.return_value = json.dumps(
        _renamed_template_payload()).encode()

    service.rename_template_callback(response)

    assert renamed == [("tpl-1", "New template")]
    assert service.processing_service.templates["tpl-1"].name == "New template"
    service.processing_service.get_processings.assert_called_once()


def test_rename_callback_accepts_the_wrapped_template_shape():
    """The endpoint may answer either bare or wrapped in a `template` key."""
    service = _rename_service()
    renamed = []
    service.templateRenamed.connect(lambda tid, name: renamed.append((tid, name)))
    response = MagicMock()
    response.readAll.return_value.data.return_value = json.dumps(
        {"template": _renamed_template_payload("Wrapped")}).encode()

    service.rename_template_callback(response)

    assert renamed == [("tpl-1", "Wrapped")]


def test_rename_callback_survives_a_body_that_is_not_json():
    service = _rename_service()
    renamed = []
    service.templateRenamed.connect(lambda tid, name: renamed.append((tid, name)))
    response = MagicMock()
    response.readAll.return_value.data.return_value = b"not json"

    service.rename_template_callback(response)

    assert renamed == []
    service.processing_service.get_processings.assert_called_once()  # still refreshes


# ---------- pause / resume / restart ----------

def _run_state_service(is_active=True, is_failed=False):
    template = SimpleNamespace(id="tpl-1", name="T", isActive=is_active, is_failed=is_failed)
    processing_service = SimpleNamespace(
        selected_template=lambda: template, api=MagicMock(),
        get_processings=MagicMock(), templates={},
        _template_error_text=lambda response: "boom")
    return TemplateService(app_context=MagicMock(), processing_service=processing_service)


def test_pause_stops_an_active_template():
    service = _run_state_service(is_active=True)

    service.pause_template()

    assert service.processing_service.api.stop_template.call_args.kwargs["template_id"] == "tpl-1"


def test_pause_refuses_an_inactive_template(monkeypatch):
    service = _run_state_service(is_active=False)
    monkeypatch.setattr(template_service_module, "alert_info", lambda *a, **k: None)

    service.pause_template()

    service.processing_service.api.stop_template.assert_not_called()


def test_resume_extends_active_until_after_the_resume_succeeds():
    """Resume is a two-step: POST /resume, then a PUT that pushes activeUntil out 6 months."""
    service = _run_state_service(is_active=False)

    service.resume_template()
    assert service.processing_service.api.resume_template.call_args.kwargs["template_id"] == "tpl-1"

    service.resume_template_update_active_until(MagicMock())

    kwargs = service.processing_service.api.update_template.call_args.kwargs
    assert kwargs["template_id"] == "tpl-1"
    assert kwargs["data"].name == "T"  # the name is carried across, the POST returns none
    assert kwargs["data"].activeUntil is not None


def test_resume_refuses_an_active_template(monkeypatch):
    service = _run_state_service(is_active=True)
    monkeypatch.setattr(template_service_module, "alert_info", lambda *a, **k: None)

    service.resume_template()

    service.processing_service.api.resume_template.assert_not_called()


def test_resume_forgets_its_state_once_it_finishes(monkeypatch):
    """Otherwise a later resume that fails to record state would extend the wrong template."""
    service = _run_state_service(is_active=False)
    monkeypatch.setattr(template_service_module, "alert_info", lambda *a, **k: None)
    service.resume_template()

    service.resume_template_callback(MagicMock())

    assert service._resume_template_state == {}


def test_restart_only_applies_to_a_failed_template(monkeypatch):
    monkeypatch.setattr(template_service_module, "alert_info", lambda *a, **k: None)
    failed = _run_state_service(is_failed=True)
    failed.restart_template()
    assert failed.processing_service.api.restart_template.call_args.kwargs["template_id"] == "tpl-1"

    healthy = _run_state_service(is_failed=False)
    healthy.restart_template()
    healthy.processing_service.api.restart_template.assert_not_called()


def test_a_failed_action_reports_the_servers_reason(monkeypatch):
    service = _run_state_service()
    alerts = []
    monkeypatch.setattr(template_service_module, "alert", lambda message, *a, **k: alerts.append(message))

    service.pause_template_error_handler(MagicMock())

    assert alerts == ["Error pausing template: boom"]


def test_resume_template_updates_active_until_to_six_months_from_resume_time():
    service = _run_state_service(is_active=False)
    service._resume_template_state = {
        "template_id": "tpl-1",
        "template_name": "Template A",
    }

    response = MagicMock()
    fixed_now = datetime(2026, 5, 6, 10, 30, 0)

    with patch.object(template_service_module, "datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = fixed_now
        service.resume_template_update_active_until(response)

    api = service.processing_service.api
    api.update_template.assert_called_once()
    kwargs = api.update_template.call_args.kwargs
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
    # The table render is deferred to the combined render after templates resolve,
    # so the poll never flashes through a processings-only state.
    service.view.update_processing_table.assert_not_called()


def test_get_templates_callback_filters_templates_to_current_project():
    service = ProcessingService.__new__(ProcessingService)
    service.tr = lambda text: text
    service.app_context = SimpleNamespace(current_project=SimpleNamespace(id="3fa85f64-5717-4562-b3fc-2c963f66afa6"))
    service.view = MagicMock()
    service.view.sort_processings.return_value = ("CREATED", "DESC")
    service.processings = {}
    service.in_template_mode = False
    service.processing_fetch_timer = MagicMock()

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


def test_get_templates_callback_builds_templates_without_hydration_request():
    """Project list omits searchParams; the poll must NOT fall back to the full list."""
    service = ProcessingService.__new__(ProcessingService)
    service.tr = lambda text: text
    service.app_context = SimpleNamespace(current_project=SimpleNamespace(id="3fa85f64-5717-4562-b3fc-2c963f66afa6"))
    service.api = MagicMock()
    service.view = MagicMock()
    service.view.sort_processings.return_value = ("CREATED", "DESC")
    service.processings = {}
    service.in_template_mode = False
    service.processing_fetch_timer = MagicMock()

    response = MagicMock()
    response.readAll.return_value.data.return_value = (
        b'['
        b'{"id":"11111111-1111-1111-1111-111111111111","name":"T1","status":"READY","createdAt":"2025-09-26T06:25:55.820336Z","userId":"3fa85f64-5717-4562-b3fc-2c963f66afa6","projectId":"3fa85f64-5717-4562-b3fc-2c963f66afa6","activeUntil":"2026-03-15T17:00:00Z"}'
        b']'
    )

    service.get_templates_callback(response)

    # No second request, and the template is still built and rendered once.
    service.api.get_templates.assert_not_called()
    assert len(service.templates) == 1
    service.view.update_processing_table.assert_called_once()

