from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QHeaderView
import pytest
from qgis.core import QgsSettings

from mapflow.dialogs.main_dialog import MainDialog
from mapflow.functional.view.sam_view import SamView
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


def test_processings_pagination_buttons_hidden_when_page_not_full():
    sam_view = _create_view()

    sam_view.update_pagination_buttons(
        has_prev=False,
        has_next=False,
        offset=0,
        limit=100,
        total=80,
    )

    assert sam_view.dlg.samProcessingsPrevPage.isHidden() is True
    assert sam_view.dlg.samProcessingsNextPage.isHidden() is True


def test_processings_pagination_buttons_first_full_page_states():
    sam_view = _create_view()

    sam_view.update_pagination_buttons(
        has_prev=False,
        has_next=True,
        offset=0,
        limit=100,
        total=230,
    )

    assert sam_view.dlg.samProcessingsPrevPage.isHidden() is False
    assert sam_view.dlg.samProcessingsNextPage.isHidden() is False
    assert sam_view.dlg.samProcessingsPrevPage.isEnabled() is False
    assert sam_view.dlg.samProcessingsNextPage.isEnabled() is True


def test_processings_pagination_buttons_last_partial_page_stays_visible_and_disables_right():
    sam_view = _create_view()

    sam_view.update_pagination_buttons(
        has_prev=True,
        has_next=False,
        offset=200,
        limit=100,
        total=230,
    )

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