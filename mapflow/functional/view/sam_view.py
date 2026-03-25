"""SAM Interactive tab view — UI state management.

Handles display of processings table, prompts table, workflows,
prompt map visualization, and debug output.
No business logic or API calls.
"""
import json
from typing import List, Optional

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
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
    QgsPointXY,
)

from ...dialogs.main_dialog import MainDialog
from ...schema.sam import (
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
        self._setup_processings_table()
        self._setup_prompts_table()
        self._setup_sessions_table()
        self._prompts_layer = None
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
        table.setHorizontalHeaderLabels(["ID", "Processing ID", "Prompt ID"])
        table.setColumnHidden(0, True)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    # ------------------------------------------------------------------
    # Processings
    # ------------------------------------------------------------------

    def display_processings(self, items: List[ProcessingSummaryResponse]):
        table = self.dlg.samProcessingsTable
        table.setRowCount(len(items))
        self.dlg.samSessionProcessingCombo.clear()
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

            # Populate session creation combo
            label = f"{proc.name} ({proc.id[:8]}...)" if proc.name else proc.id
            self.dlg.samSessionProcessingCombo.addItem(label, proc.id)

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

    def display_workflows(self, workflows: List[WorkflowSummaryResponse]):
        self.dlg.samInferenceWorkflowCombo.clear()
        for wf in workflows:
            label = f"{wf.id[:8]}... ({wf.status})"
            self.dlg.samInferenceWorkflowCombo.addItem(label, wf.id)

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    def display_prompts(self, items: List[PromptResponse]):
        table = self.dlg.samPromptsTable
        table.setRowCount(len(items))
        self.dlg.samSessionPromptCombo.clear()
        for row, prompt in enumerate(items):
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, prompt.id)
            table.setItem(row, 0, id_item)

            text_item = QTableWidgetItem()
            text_item.setData(Qt.DisplayRole, prompt.text_prompt or "")
            table.setItem(row, 1, text_item)

            # Populate session creation combo
            label = prompt.text_prompt or prompt.id
            self.dlg.samSessionPromptCombo.addItem(label, prompt.id)

    def selected_prompt_id(self) -> Optional[str]:
        table = self.dlg.samPromptsTable
        selected = table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        item = table.item(row, 0)
        return item.data(Qt.DisplayRole) if item else None

    def display_prompt_detail(self, detail: PromptDetailResponse):
        self._clear_prompts_layer()
        for pt in detail.point_prompts:
            self._add_spatial_prompt_feature(pt, "point")
        for bx in detail.bbox_prompts:
            self._add_spatial_prompt_feature(bx, "polygon")

    def add_prompt_to_map(self, prompt: SpatialPromptResponse):
        if prompt.geometry is None:
            return
        geom_type = prompt.geometry.get("type", "")
        if geom_type == "Point":
            self._add_spatial_prompt_feature(prompt, "point")
        else:
            self._add_spatial_prompt_feature(prompt, "polygon")

    # ------------------------------------------------------------------
    # Map layer for prompt visualization
    # ------------------------------------------------------------------

    def _get_or_create_prompts_layer(self, geom_type: str) -> QgsVectorLayer:
        """Get or create a memory layer for displaying SAM prompts."""
        if self._prompts_layer is not None and self._prompts_layer.isValid():
            return self._prompts_layer

        layer = QgsVectorLayer(
            f"{geom_type}?crs=EPSG:4326",
            "SAM Prompts",
            "memory",
        )
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("id", QVariant_String()),
            QgsField("positive", QVariant_String()),
            QgsField("type", QVariant_String()),
        ])
        layer.updateFields()

        # Categorized renderer: green for positive, red for negative
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
        self._prompts_layer = layer
        return layer

    def _add_spatial_prompt_feature(self, prompt: SpatialPromptResponse, geom_type: str):
        if prompt.geometry is None:
            return

        layer = self._get_or_create_prompts_layer(geom_type)
        feature = QgsFeature(layer.fields())
        feature.setAttribute("id", prompt.id)
        feature.setAttribute("positive", str(prompt.positive).lower())
        feature.setAttribute("type", geom_type)

        geom_json = json.dumps(prompt.geometry)
        geometry = QgsGeometry.fromWkt(_geojson_to_wkt(prompt.geometry))
        if geometry and not geometry.isNull():
            feature.setGeometry(geometry)
            layer.dataProvider().addFeatures([feature])
            layer.triggerRepaint()

    def _clear_prompts_layer(self):
        if self._prompts_layer is not None and self._prompts_layer.isValid():
            self._prompts_layer.dataProvider().truncate()
            self._prompts_layer.triggerRepaint()

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def display_sessions(self, sessions: List[SessionResponse]):
        table = self.dlg.samSessionsTable
        table.setRowCount(len(sessions))
        for row, sess in enumerate(sessions):
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, sess.id)
            table.setItem(row, 0, id_item)

            proc_item = QTableWidgetItem()
            proc_item.setData(Qt.DisplayRole, sess.processing_id)
            table.setItem(row, 1, proc_item)

            prompt_item = QTableWidgetItem()
            prompt_item.setData(Qt.DisplayRole, sess.prompt_id)
            table.setItem(row, 2, prompt_item)

        # Also populate session combos (inference + result)
        self._populate_session_combos(sessions)

    def _populate_session_combos(self, sessions: List[SessionResponse]):
        for combo in (self.dlg.samInferenceSessionCombo,
                      self.dlg.samResultSessionCombo):
            combo.clear()
            for sess in sessions:
                combo.addItem(sess.id, sess.id)

    def add_session_to_combos(self, session_id: str):
        """Add a newly created/copied session to inference + result combos."""
        for combo in (self.dlg.samInferenceSessionCombo,
                      self.dlg.samResultSessionCombo):
            combo.addItem(session_id, session_id)
            combo.setCurrentIndex(combo.count() - 1)

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
        self.dlg.samWorkflowStatusValue.setText(inference.we_workflow_status or "-")

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
