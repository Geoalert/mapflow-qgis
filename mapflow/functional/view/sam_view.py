"""SAM Interactive tab view — UI state management.

Handles display of processings table, prompts table, workflows,
prompt map visualization, and debug output.
No business logic or API calls.
"""
import json
from typing import List, Optional, Tuple

import sip
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsField,
    QgsSymbol,
    QgsFillSymbol,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsPointXY,
)

from ...dialogs.main_dialog import MainDialog
from ...dialogs import icons

from ...schema.sam import (
    GeometryType,
    ProcessingSummaryResponse,
    ProcessingDetailResponse,
    WorkflowSummaryResponse,
    PromptResponse,
    PromptDetailResponse,
    SpatialPromptResponse,
    SessionResponse,
    InferenceResponse,
)


class SamView(QObject):
    def __init__(self, dlg: MainDialog):
        super().__init__()
        self.dlg = dlg
        self.dlg.samRefreshProcessings.setIcon(icons.refresh_icon)
        self.dlg.samRefreshPrompts.setIcon(icons.refresh_icon)
        self.dlg.samRefreshSessions.setIcon(icons.refresh_icon)
        self.dlg.samRefreshInferenceStatus.setIcon(icons.refresh_icon)

        self._setup_processings_table()
        self._setup_prompts_table()
        self._setup_sessions_table()
        self._setup_spatial_prompts_table()
        self._setup_initial_button_states()
        self._point_prompts_layer = None
        self._bbox_prompts_layer = None
        self._workflows_layer = None
        self._result_layer = None

    def _setup_processings_table(self):
        table = self.dlg.samProcessingsTable
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Name", "Status", "Created"])
        table.setColumnHidden(0, True)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def _setup_prompts_table(self):
        table = self.dlg.samPromptsTable
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["ID", "Text Prompt"])
        table.setColumnHidden(0, True)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def _setup_sessions_table(self):
        table = self.dlg.samSessionsTable
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["ID", "Name", "Text Prompt"])
        table.setColumnHidden(0, True)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def _setup_spatial_prompts_table(self):
        table = self.dlg.spatialPromptsTable
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Type", "Positive", "Geometry"])
        table.setColumnHidden(0, True)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

    def _setup_initial_button_states(self):
        """Disable buttons that require a selection or prior action."""
        # Require prompt selection
        self.dlg.samAddPointPrompt.setEnabled(False)
        self.dlg.samAddBboxPrompt.setEnabled(False)
        # Require session selection
        self.dlg.samRunSessionInference.setEnabled(False)
        self.dlg.samRefreshSessions.setEnabled(False)
        # Require prior inference
        self.dlg.samRefreshInferenceStatus.setEnabled(False)

    def set_prompt_buttons_enabled(self, enabled: bool):
        self.dlg.samAddPointPrompt.setEnabled(enabled)
        self.dlg.samAddBboxPrompt.setEnabled(enabled)
        self.dlg.deletePromptButton.setEnabled(enabled)

    def set_session_buttons_enabled(self, enabled: bool):
        self.dlg.samRunSessionInference.setEnabled(enabled)
        self.dlg.deleteSessionButton.setEnabled(enabled)

    def set_inference_refresh_enabled(self, enabled: bool):
        self.dlg.samRefreshInferenceStatus.setEnabled(enabled)

    # ------------------------------------------------------------------
    # Processings
    # ------------------------------------------------------------------

    def display_processings(self, items: List[ProcessingSummaryResponse]):
        table = self.dlg.samProcessingsTable
        table.setRowCount(len(items))
        for row, proc in enumerate(items):
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, proc.id)
            table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem()
            name_item.setData(Qt.DisplayRole, proc.name)
            table.setItem(row, 1, name_item)

            status_item = QTableWidgetItem()
            status_item.setData(Qt.DisplayRole, proc.status)
            table.setItem(row, 2, status_item)

            created_item = QTableWidgetItem()
            created_item.setData(Qt.DisplayRole, proc.created_at or "")
            table.setItem(row, 3, created_item)

    def selected_processing_id(self) -> Optional[str]:
        table = self.dlg.samProcessingsTable
        selected = table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        item = table.item(row, 0)
        return item.data(Qt.DisplayRole) if item else None

    def display_processing_detail(self, detail: ProcessingDetailResponse):
        pass

    def populate_workflow_combo(self, workflows: List[WorkflowSummaryResponse]):
        """Populate the workflow combo box without adding map layers."""
        self.dlg.samInferenceWorkflowCombo.clear()
        for wf in workflows:
            label = f"{wf.id[:8]}... ({wf.status})"
            self.dlg.samInferenceWorkflowCombo.addItem(label, wf.id)

    def show_workflow_layers(self, workflows: List[WorkflowSummaryResponse]):
        """Add workflow geometry layers to the map."""
        self._display_workflow_geometries(workflows)
        # Highlight selected workflow when combo changes
        try:
            self.dlg.samInferenceWorkflowCombo.currentIndexChanged.disconnect(
                self._highlight_selected_workflow)
        except TypeError:
            pass
        self.dlg.samInferenceWorkflowCombo.currentIndexChanged.connect(
            self._highlight_selected_workflow)
        self._highlight_selected_workflow()

    def selected_workflow_id(self) -> Optional[str]:
        comboBox = self.dlg.samInferenceWorkflowCombo
        data = comboBox.currentData()
        return str(data) if data else None

    # ------------------------------------------------------------------
    # Workflow geometry layer
    # ------------------------------------------------------------------

    def _display_workflow_geometries(self, workflows: List[WorkflowSummaryResponse]):
        """Replace existing workflows layer with a new one showing workflow polygons."""
        self._remove_workflows_layer()

        layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "SAM Workflows", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("id", QVariant_String()),
            QgsField("selected", QVariant_String()),
        ])
        layer.updateFields()

        for wf in workflows:
            if wf.geometry is None:
                continue
            feature = QgsFeature(layer.fields())
            feature.setAttribute("id", wf.id)
            feature.setAttribute("selected", "false")
            geometry = QgsGeometry.fromWkt(_geojson_to_wkt(wf.geometry))
            if geometry and not geometry.isNull():
                feature.setGeometry(geometry)
                provider.addFeatures([feature])

        # Normal: 90% transparent fill, thin border
        normal_symbol = QgsFillSymbol.createSimple({
            "color": "100,100,255,25",       # ~90% transparent blue
            "outline_color": "100,100,255,180",
            "outline_width": "0.3",
        })
        # Selected/highlighted: more visible
        selected_symbol = QgsFillSymbol.createSimple({
            "color": "255,200,0,80",
            "outline_color": "255,160,0,255",
            "outline_width": "0.8",
        })
        categories = [
            QgsRendererCategory("false", normal_symbol, "Workflow"),
            QgsRendererCategory("true", selected_symbol, "Selected"),
        ]
        renderer = QgsCategorizedSymbolRenderer("selected", categories)
        layer.setRenderer(renderer)

        QgsProject.instance().addMapLayer(layer)
        self._workflows_layer = layer

    def _highlight_selected_workflow(self):
        """Update the 'selected' attribute to highlight the current combo selection."""
        if not self._layer_alive(self._workflows_layer):
            return
        layer = self._workflows_layer
        selected_id = self.selected_workflow_id()
        layer.startEditing()
        idx = layer.fields().indexOf("selected")
        for feature in layer.getFeatures():
            is_selected = "true" if feature["id"] == selected_id else "false"
            layer.changeAttributeValue(feature.id(), idx, is_selected)
        layer.commitChanges()
        layer.triggerRepaint()

    def _remove_workflows_layer(self):
        """Remove existing workflows layer from the project."""
        if self._layer_alive(self._workflows_layer):
            QgsProject.instance().removeMapLayer(self._workflows_layer.id())
        self._workflows_layer = None

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    def display_prompts(self, items: List[PromptResponse]):
        table = self.dlg.samPromptsTable
        table.setRowCount(len(items))
        for row, prompt in enumerate(items):
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, prompt.id)
            table.setItem(row, 0, id_item)

            text_item = QTableWidgetItem()
            text_item.setData(Qt.DisplayRole, prompt.text_prompt or "")
            table.setItem(row, 1, text_item)


    def selected_prompt_id(self) -> Optional[str]:
        table = self.dlg.samPromptsTable
        selected = table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        item = table.item(row, 0)
        return item.data(Qt.DisplayRole) if item else None

    def populate_spatial_prompts_table(self, spatial_prompts: List[SpatialPromptResponse]):
        """Populate spatialPromptsTable without adding map layers."""
        table = self.dlg.spatialPromptsTable
        table.setRowCount(len(spatial_prompts))
        for row, sp in enumerate(spatial_prompts):
            type_label = sp.geometry_type.capitalize()  # "point" -> "Point", "bbox" -> "Bbox"
            self._set_spatial_prompt_row(table, row, sp, type_label)
        self.dlg.deleteSpatialPrompt.setEnabled(len(spatial_prompts) > 0)

    def show_spatial_prompt_layers(self, spatial_prompts: List[SpatialPromptResponse]):
        """Add spatial prompt features to map layers."""
        self._clear_prompts_layers()
        for sp in spatial_prompts:
            geom_type = "Point" if sp.geometry_type == GeometryType.POINT.value else "Polygon"
            self._add_spatial_prompt_feature(sp, geom_type)

    @staticmethod
    def _set_spatial_prompt_row(table, row: int, prompt: SpatialPromptResponse, type_label: str):
        id_item = QTableWidgetItem()
        id_item.setData(Qt.DisplayRole, prompt.id)
        table.setItem(row, 0, id_item)

        type_item = QTableWidgetItem()
        type_item.setData(Qt.DisplayRole, type_label)
        table.setItem(row, 1, type_item)

        pos_item = QTableWidgetItem()
        pos_item.setData(Qt.DisplayRole, "+" if prompt.positive else "-")
        table.setItem(row, 2, pos_item)

        geom_item = QTableWidgetItem()
        geom_summary = ""
        if prompt.geometry:
            coords = prompt.geometry.get("coordinates", [])
            geom_type = prompt.geometry.get("type", "")
            if geom_type == "Point" and len(coords) >= 2:
                geom_summary = f"{coords[0]:.5f}, {coords[1]:.5f}"
            elif geom_type == "Polygon" and coords:
                geom_summary = f"Polygon ({len(coords[0])} pts)"
        geom_item.setData(Qt.DisplayRole, geom_summary)
        table.setItem(row, 3, geom_item)

    def selected_spatial_prompt(self) -> Tuple[Optional[str], Optional[str]]:
        table = self.dlg.spatialPromptsTable
        selected = table.selectionModel().selectedRows()
        if not selected:
            return None, None
        row = selected[0].row()
        prompt_type = str(table.item(row, 1).data(Qt.DisplayRole)).lower()
        spatial_prompt_id = str(table.item(row, 0).data(Qt.DisplayRole)).lower()
        return spatial_prompt_id, prompt_type

    def add_prompt_to_map(self, prompt: SpatialPromptResponse):
        if prompt.geometry is None:
            return
        geom_type = prompt.geometry.get("type", "Point")
        self._add_spatial_prompt_feature(prompt, geom_type)

    # ------------------------------------------------------------------
    # Map layers for prompt visualization
    # ------------------------------------------------------------------

    def _create_prompts_layer(self, geom_type: str, name: str) -> QgsVectorLayer:
        layer = QgsVectorLayer(
            f"{geom_type}?crs=EPSG:4326",
            name,
            "memory",
        )
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("id", QVariant_String()),
            QgsField("positive", QVariant_String()),
        ])
        layer.updateFields()

        positive_symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        positive_symbol.setColor(QColor(0, 200, 0, 180))
        negative_symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        negative_symbol.setColor(QColor(200, 0, 0, 180))

        categories = [
            QgsRendererCategory("true", positive_symbol, "Positive"),
            QgsRendererCategory("false", negative_symbol, "Negative"),
        ]
        renderer = QgsCategorizedSymbolRenderer("positive", categories)
        layer.setRenderer(renderer)

        QgsProject.instance().addMapLayer(layer)
        return layer

    @staticmethod
    def _layer_alive(layer) -> bool:
        return layer is not None and not sip.isdeleted(layer) and layer.isValid()

    def _get_or_create_point_layer(self) -> QgsVectorLayer:
        if not self._layer_alive(self._point_prompts_layer):
            self._point_prompts_layer = self._create_prompts_layer("Point", "SAM Point Prompts")
        return self._point_prompts_layer

    def _get_or_create_bbox_layer(self) -> QgsVectorLayer:
        if not self._layer_alive(self._bbox_prompts_layer):
            self._bbox_prompts_layer = self._create_prompts_layer("Polygon", "SAM Bbox Prompts")
        return self._bbox_prompts_layer

    def _add_spatial_prompt_feature(self, prompt: SpatialPromptResponse, geom_type: str):
        if prompt.geometry is None:
            return

        if geom_type == "Point":
            layer = self._get_or_create_point_layer()
        else:
            layer = self._get_or_create_bbox_layer()

        feature = QgsFeature(layer.fields())
        feature.setAttribute("id", prompt.id)
        feature.setAttribute("positive", str(prompt.positive).lower())

        geometry = QgsGeometry.fromWkt(_geojson_to_wkt(prompt.geometry))
        if geometry and not geometry.isNull():
            feature.setGeometry(geometry)
            layer.dataProvider().addFeatures([feature])
            layer.triggerRepaint()

    def _clear_prompts_layers(self):
        for layer in (self._point_prompts_layer, self._bbox_prompts_layer):
            if self._layer_alive(layer):
                layer.dataProvider().truncate()
                layer.triggerRepaint()

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def display_sessions(self, sessions: List[SessionResponse]):
        table = self.dlg.samSessionsTable
        table.setRowCount(len(sessions))
        for row, sess in enumerate(sessions):
            self._set_session_row(table, row, sess)

    def add_session_to_table(self, session: SessionResponse):
        table = self.dlg.samSessionsTable
        row = table.rowCount()
        table.insertRow(row)
        self._set_session_row(table, row, session)
        table.selectRow(row)

    @staticmethod
    def _set_session_row(table, row: int, sess: SessionResponse):
        id_item = QTableWidgetItem()
        id_item.setData(Qt.DisplayRole, sess.id)
        table.setItem(row, 0, id_item)

        name_item = QTableWidgetItem()
        name_item.setData(Qt.DisplayRole, sess.name or sess.id[:12])
        table.setItem(row, 1, name_item)

        text_item = QTableWidgetItem()
        text_item.setData(Qt.DisplayRole, sess.text_prompt or "")
        table.setItem(row, 2, text_item)

    def selected_session_id(self) -> Optional[str]:
        table = self.dlg.samSessionsTable
        selected = table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        item = table.item(row, 0)
        return item.data(Qt.DisplayRole) if item else None

    def display_session_detail(self, session: SessionResponse):
        """Show session detail in debug; populate inference combo with inferences."""
        pass

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def display_inference_status(self, inference: InferenceResponse):
        self.dlg.samInferenceIdValue.setText(inference.id or "-")
        self.dlg.samInferenceStatusValue.setText(inference.status or "-")

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def load_result_layer(self, data: dict):
        """Load GeoJSON result as a vector layer on the map."""
        geojson_str = json.dumps(data)
        layer = QgsVectorLayer(geojson_str, "SAM Result", "ogr")
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
        self._result_layer = layer

    # ------------------------------------------------------------------
    # Debug output
    # ------------------------------------------------------------------

    def append_debug(self, title: str, data):
        try:
            debug_text = json.dumps(data, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            debug_text = str(data)
        self.dlg.samDebugOutput.append(f"--- {title} ---\n{debug_text}\n")

    def update_pagination_buttons(self, has_prev: bool, has_next: bool,
                                  offset: int, limit: int, total: int):
        pass


def QVariant_String():
    """Return QVariant.String without importing QVariant at module level."""
    from PyQt5.QtCore import QVariant
    return QVariant.String


def _geojson_to_wkt(geojson: dict) -> str:
    """Convert a GeoJSON geometry dict to WKT string."""
    geom_type = geojson.get("type", "")
    coords = geojson.get("coordinates", [])

    if geom_type == "Point":
        return f"POINT({coords[0]} {coords[1]})"
    elif geom_type == "Polygon":
        rings = []
        for ring in coords:
            points = ", ".join(f"{c[0]} {c[1]}" for c in ring)
            rings.append(f"({points})")
        return f"POLYGON({', '.join(rings)})"
    return ""
