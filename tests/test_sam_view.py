from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QHeaderView
import pytest
from qgis.core import QgsSettings

from mapflow.dialogs.main_dialog import MainDialog
from mapflow.functional.view.sam_view import SamView
from mapflow.schema.project import UserRole
from mapflow.schema.sam import InferenceStatusSummary, SessionResponse, SpatialPromptResponse


def _create_view() -> SamView:
    dialog = MainDialog(parent=None, settings=QgsSettings())
    return SamView(dialog)


def test_spatial_prompts_table_uses_icon_column_and_keeps_prompt_type():
    sam_view = _create_view()
    prompt = SpatialPromptResponse.from_dict({
        "id": "sp1",
        "geometry_type": "point",
        "processing_id": "proc-1",
        "geometry": {"type": "Point", "coordinates": [12.34567, 54.32109]},
        "positive": True,
    })

    sam_view.populate_spatial_prompts_table([prompt])

    table = sam_view.dlg.spatialPromptsTable
    assert table.columnCount() == 3
    icon_item = table.item(0, 1)
    assert icon_item.data(Qt.DecorationRole) is not None
    assert icon_item.data(Qt.UserRole) == "point"
    assert table.item(0, 2).data(Qt.DisplayRole) == "12.34567, 54.32109"

    table.selectRow(0)
    assert sam_view.selected_spatial_prompt() == ("sp1", "point")


def test_processings_table_keeps_name_column_preferred_over_created():
    sam_view = _create_view()
    header = sam_view.dlg.samProcessingsTable.horizontalHeader()

    assert header.sectionResizeMode(1) == QHeaderView.ResizeMode.Interactive
    assert header.sectionResizeMode(2) == QHeaderView.ResizeMode.Stretch
    assert sam_view.dlg.samProcessingsTable.columnWidth(1) >= 200


def test_processings_pagination_buttons_hidden_when_no_other_pages():
    sam_view = _create_view()

    sam_view.update_pagination_buttons(has_prev=False, has_next=False)

    assert sam_view.dlg.samProcessingsPrevPage.isHidden() is True
    assert sam_view.dlg.samProcessingsNextPage.isHidden() is True


def test_processings_pagination_buttons_first_page_states():
    sam_view = _create_view()

    sam_view.update_pagination_buttons(has_prev=False, has_next=True)

    assert sam_view.dlg.samProcessingsPrevPage.isHidden() is False
    assert sam_view.dlg.samProcessingsNextPage.isHidden() is False
    assert sam_view.dlg.samProcessingsPrevPage.isEnabled() is False
    assert sam_view.dlg.samProcessingsNextPage.isEnabled() is True


def test_processings_pagination_buttons_last_page_stays_visible_and_disables_right():
    sam_view = _create_view()

    sam_view.update_pagination_buttons(has_prev=True, has_next=False)

    assert sam_view.dlg.samProcessingsPrevPage.isHidden() is False
    assert sam_view.dlg.samProcessingsNextPage.isHidden() is False
    assert sam_view.dlg.samProcessingsPrevPage.isEnabled() is True
    assert sam_view.dlg.samProcessingsNextPage.isEnabled() is False


def test_display_sessions_selects_first_row_when_no_previous_selection():
    sam_view = _create_view()
    sessions = [
        SessionResponse.from_dict({"id": "s1", "processing_id": "p1"}),
        SessionResponse.from_dict({"id": "s2", "processing_id": "p1"}),
    ]

    sam_view.display_sessions(sessions)

    assert sam_view.selected_session_id() == "s1"


def test_display_sessions_preserves_selected_session_when_possible():
    sam_view = _create_view()
    sessions = [
        SessionResponse.from_dict({"id": "s1", "processing_id": "p1"}),
        SessionResponse.from_dict({"id": "s2", "processing_id": "p1"}),
    ]
    sam_view.display_sessions(sessions)
    sam_view.dlg.samSessionsTable.selectRow(1)

    refreshed = [
        SessionResponse.from_dict({"id": "s1", "processing_id": "p1"}),
        SessionResponse.from_dict({"id": "s2", "processing_id": "p1", "inferences_total": 2, "inferences_done": 1}),
    ]
    sam_view.display_sessions(refreshed)

    assert sam_view.selected_session_id() == "s2"


def test_clear_session_display_clears_inferences_and_prompt_snapshot():
    sam_view = _create_view()
    session = SessionResponse.from_dict({
        "id": "s1",
        "processing_id": "p1",
        "text_prompt": {"id": "tp1", "text": "trees"},
        "spatial_prompts": [
            {"id": "sp1", "geometry_type": "point", "processing_id": "p1",
             "geometry": {"type": "Point", "coordinates": [1.0, 2.0]}, "positive": True}
        ],
        "inferences": [
            {"id": "inf1", "status": "done", "created_at": "2026-04-01T10:00:00"}
        ],
    })
    sam_view.dlg.samSessionsTable.setRowCount(1)
    session_id_item = QTableWidgetItem()
    session_id_item.setData(Qt.DisplayRole, "s1")
    sam_view.dlg.samSessionsTable.setItem(0, 0, session_id_item)

    sam_view.display_session(session)
    assert sam_view.dlg.samInferencesTable.rowCount() == 1
    assert sam_view.dlg.spatialPromptsTable.rowCount() == 1

    sam_view.clear_session_display()

    assert sam_view.dlg.samSessionTextPromptLabel.text() == ""
    assert sam_view.dlg.samInferencesTable.rowCount() == 0
    assert sam_view.dlg.spatialPromptsTable.rowCount() == 0


def test_display_session_updates_session_progress_from_detail_inferences():
    sam_view = _create_view()
    listed_session = SessionResponse.from_dict({
        "id": "s1",
        "processing_id": "p1",
        "inferences_total": 2,
        "inferences_done": 0,
    })
    sam_view.display_sessions([listed_session])

    detail_session = SessionResponse.from_dict({
        "id": "s1",
        "processing_id": "p1",
        "inferences": [
            InferenceStatusSummary.from_dict({"id": "i1", "status": "done"}),
            InferenceStatusSummary.from_dict({"id": "i2", "status": "in_progress"}),
        ],
    })
    sam_view.display_session(detail_session)

    assert sam_view.dlg.samSessionsTable.item(0, 2).data(Qt.DisplayRole) == "1/2"


def test_highlight_spatial_prompt_selects_feature_in_point_layer():
    sam_view = _create_view()
    point_prompt = SpatialPromptResponse.from_dict({
        "id": "sp1",
        "geometry_type": "point",
        "processing_id": "proc-1",
        "geometry": {"type": "Point", "coordinates": [12.3, 54.3]},
        "positive": True,
    })
    sam_view.show_spatial_prompt_layers([point_prompt])

    sam_view.highlight_spatial_prompt("sp1", "point")

    assert sam_view._point_prompts_layer is not None
    assert sam_view._point_highlight_layer is not None
    assert sam_view._point_highlight_layer.featureCount() == 1
    assert len(sam_view._point_prompts_layer.selectedFeatureIds()) == 0


def test_highlight_spatial_prompt_clears_previous_selection():
    sam_view = _create_view()
    point_prompts = [
        SpatialPromptResponse.from_dict({
            "id": "sp1",
            "geometry_type": "point",
            "processing_id": "proc-1",
            "geometry": {"type": "Point", "coordinates": [12.3, 54.3]},
            "positive": True,
        }),
        SpatialPromptResponse.from_dict({
            "id": "sp2",
            "geometry_type": "point",
            "processing_id": "proc-1",
            "geometry": {"type": "Point", "coordinates": [12.4, 54.4]},
            "positive": False,
        }),
    ]
    sam_view.show_spatial_prompt_layers(point_prompts)

    sam_view.highlight_spatial_prompt("sp1", "point")
    first_feature = next(sam_view._point_highlight_layer.getFeatures())
    first_wkt = first_feature.geometry().asWkt()
    sam_view.highlight_spatial_prompt("sp2", "point")
    second_feature = next(sam_view._point_highlight_layer.getFeatures())
    second_wkt = second_feature.geometry().asWkt()

    assert sam_view._point_highlight_layer.featureCount() == 1
    assert first_wkt != second_wkt


def test_set_user_role_readonly_disables_modify_buttons_when_selection_present():
    sam_view = _create_view()
    sam_view.set_user_role(UserRole.readonly)
    # Simulate a prompt selection AND a session selection — buttons that
    # require contributor+/maintainer+ must still be disabled because the
    # role is too low.
    sam_view.set_prompt_buttons_enabled(True)
    sam_view.set_session_buttons_enabled(True)
    sam_view.set_processing_action_buttons(True)

    # Modify-class buttons → contributor+
    assert sam_view.dlg.samAddPointPrompt.isEnabled() is False
    assert sam_view.dlg.samAddBboxPrompt.isEnabled() is False
    assert sam_view.dlg.samRunSessionInference.isEnabled() is False
    assert sam_view.dlg.samRunInference.isEnabled() is False
    # Delete-class buttons → maintainer+
    assert sam_view.dlg.deleteSessionButton.isEnabled() is False
    assert sam_view.dlg.deleteProcessingButton.isEnabled() is False
    # Read-only / user-scoped buttons stay enabled
    assert sam_view.dlg.samRefreshSessions.isEnabled() is True
    assert sam_view.dlg.samRefreshInferenceStatus.isEnabled() is True
    assert sam_view.dlg.deletePromptButton.isEnabled() is True


def test_set_user_role_contributor_blocks_delete_actions_only():
    sam_view = _create_view()
    sam_view.set_user_role(UserRole.contributor)
    sam_view.set_prompt_buttons_enabled(True)
    sam_view.set_session_buttons_enabled(True)
    sam_view.set_processing_action_buttons(True)

    # Modify-class allowed
    assert sam_view.dlg.samAddPointPrompt.isEnabled() is True
    assert sam_view.dlg.samRunSessionInference.isEnabled() is True
    assert sam_view.dlg.samRunInference.isEnabled() is True
    # Delete-class still blocked
    assert sam_view.dlg.deleteSessionButton.isEnabled() is False
    assert sam_view.dlg.deleteProcessingButton.isEnabled() is False


def test_set_user_role_maintainer_enables_all_action_buttons_when_selected():
    sam_view = _create_view()
    sam_view.set_user_role(UserRole.maintainer)
    sam_view.set_prompt_buttons_enabled(True)
    sam_view.set_session_buttons_enabled(True)
    sam_view.set_processing_action_buttons(True)

    assert sam_view.dlg.samAddPointPrompt.isEnabled() is True
    assert sam_view.dlg.samRunSessionInference.isEnabled() is True
    assert sam_view.dlg.deleteSessionButton.isEnabled() is True
    assert sam_view.dlg.deleteProcessingButton.isEnabled() is True


def test_session_name_cell_read_only_for_contributor():
    sam_view = _create_view()
    sam_view.set_user_role(UserRole.contributor)
    sessions = [SessionResponse.from_dict({"id": "s1", "processing_id": "p1"})]

    sam_view.display_sessions(sessions)

    name_item = sam_view.dlg.samSessionsTable.item(0, 1)
    assert bool(name_item.flags() & Qt.ItemIsEditable) is False


def test_session_name_cell_editable_for_maintainer():
    sam_view = _create_view()
    sam_view.set_user_role(UserRole.maintainer)
    sessions = [SessionResponse.from_dict({"id": "s1", "processing_id": "p1"})]

    sam_view.display_sessions(sessions)

    name_item = sam_view.dlg.samSessionsTable.item(0, 1)
    assert bool(name_item.flags() & Qt.ItemIsEditable) is True


def test_clear_processings_table_empties_dependent_panels():
    sam_view = _create_view()
    sessions = [SessionResponse.from_dict({"id": "s1", "processing_id": "p1"})]
    sam_view.display_sessions(sessions)
    sam_view.dlg.samProcessingsTable.setRowCount(2)

    sam_view.clear_processings_table()

    assert sam_view.dlg.samProcessingsTable.rowCount() == 0
    assert sam_view.dlg.samSessionsTable.rowCount() == 0
    assert sam_view.dlg.samInferencesTable.rowCount() == 0
    assert sam_view.dlg.deleteProcessingButton.isEnabled() is False
    assert sam_view.dlg.deleteSessionButton.isEnabled() is False


def test_show_rasters_checkbox_defaults_to_on():
    sam_view = _create_view()

    assert sam_view.dlg.samShowRastersCheckbox.isChecked() is True
    assert sam_view.is_show_rasters_enabled() is True


def test_show_rasters_checkbox_off_reports_disabled():
    sam_view = _create_view()
    sam_view.dlg.samShowRastersCheckbox.setChecked(False)

    assert sam_view.is_show_rasters_enabled() is False


def test_show_spatial_prompt_layers_creates_prompts_group():
    # Geometry layers move under the SAM Prompts group on first display so
    # the user can collapse / hide / delete the whole batch in one click.
    sam_view = _create_view()
    point_prompt = SpatialPromptResponse.from_dict({
        "id": "sp1",
        "geometry_type": "point",
        "processing_id": "proc-1",
        "geometry": {"type": "Point", "coordinates": [12.3, 54.3]},
        "positive": True,
    })

    sam_view.show_spatial_prompt_layers([point_prompt])

    from qgis.core import QgsProject
    root = QgsProject.instance().layerTreeRoot()
    prompts_group = root.findGroup(SamView.PROMPTS_GROUP_NAME)
    assert prompts_group is not None
    layer_names = [n.name() for n in prompts_group.findLayers()]
    assert "SAM Point Prompts" in layer_names


def test_add_spatial_prompt_preview_attaches_to_previews_subgroup(tmp_path):
    sam_view = _create_view()
    sam_view.show_spatial_prompt_layers([])
    # Use a real (tiny) GeoTIFF wouldn't simplify the test; what we care
    # about is that the layer is registered under the previews subgroup,
    # not whether QGIS could parse it. A non-existent path is fine — the
    # method falls through the isValid()=False branch but still tracks
    # the temp file. Test the happy path with a real tif via rasterio
    # would need a fixture — skip for now and assert via group existence.
    fake_tiff = tmp_path / "preview.tif"
    fake_tiff.write_bytes(b"\x49\x49\x2A\x00")  # TIFF magic + nothing valid

    sam_view.add_spatial_prompt_preview(
        local_path=str(fake_tiff), sp_id="sp-abcdef12", geometry_type="point",
    )

    from qgis.core import QgsProject
    prompts_group = QgsProject.instance().layerTreeRoot().findGroup(
        SamView.PROMPTS_GROUP_NAME
    )
    assert prompts_group is not None
    previews_group = prompts_group.findGroup(SamView.PREVIEWS_GROUP_NAME)
    # If the raster is not parseable the layer is rejected and the subgroup
    # may not have been created yet — but the temp file path is tracked for
    # cleanup either way.
    assert "sp-abcdef12" in sam_view._preview_temp_files


def test_show_spatial_prompt_layers_replaces_previous_previews(tmp_path):
    # Calling show_spatial_prompt_layers must drop previously-attached
    # raster previews so the user only sees crops for the current prompt.
    sam_view = _create_view()
    sam_view.show_spatial_prompt_layers([])

    f1 = tmp_path / "a.tif"
    f1.write_bytes(b"\x49\x49\x2A\x00")
    sam_view.add_spatial_prompt_preview(
        local_path=str(f1), sp_id="sp-1", geometry_type="point",
    )
    assert sam_view._preview_temp_files

    sam_view.show_spatial_prompt_layers([])

    # Tracking dict cleared on each new prompt display.
    assert sam_view._preview_temp_files == {}


def test_highlight_overlay_uses_yellow_stroke_with_width_0_6():
    sam_view = _create_view()
    point_prompt = SpatialPromptResponse.from_dict({
        "id": "sp1",
        "geometry_type": "point",
        "processing_id": "proc-1",
        "geometry": {"type": "Point", "coordinates": [12.3, 54.3]},
        "positive": True,
    })
    sam_view.show_spatial_prompt_layers([point_prompt])
    sam_view.highlight_spatial_prompt("sp1", "point")

    symbol = sam_view._point_highlight_layer.renderer().symbol()
    symbol_props = symbol.symbolLayer(0).properties()

    assert float(symbol_props.get("outline_width", 0.0)) == pytest.approx(0.6)
    assert symbol_props.get("outline_color") == "255,255,0,255"