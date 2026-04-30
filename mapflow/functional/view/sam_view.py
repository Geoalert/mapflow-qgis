"""SAM Interactive tab view — UI state management.

Handles display of processings table, prompts table, workflows,
prompt map visualization, and debug output.
No business logic or API calls.
"""
import json
from typing import List, Optional, Tuple

import sip
from PyQt5.QtCore import QObject, QPointF, Qt
from PyQt5.QtGui import QColor, QBrush, QPainter, QPen, QPixmap, QPolygonF
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
)

from ...dialogs.main_dialog import MainDialog
from ...dialogs import icons

from ...schema.sam import (
    GeometryType,
    ProcessingSummaryResponse,
    ProcessingDetailResponse,
    PromptResponse,
    PromptDetailResponse,
    SpatialPromptResponse,
    SessionResponse,
    InferenceStatusSummary,
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
        self._setup_inferences_table()
        self._setup_initial_button_states()
        self.clear_processing_detail()
        self._point_prompts_layer = None
        self._bbox_prompts_layer = None
        # One result vector layer per session, keyed by session_id, so we
        # can refresh partial results in place rather than spawn duplicates.
        self._result_layers = {}

    def _setup_processings_table(self):
        # SAM tab only ever shows OK (interactive-ready) processings — non-OK
        # rows are filtered out at populate time. The Status column is gone
        # because every visible row carries the same value.
        table = self.dlg.samProcessingsTable
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["ID", "Name", "Created"])
        table.setColumnHidden(0, True)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().resizeSection(1, 260)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

    def _setup_prompts_table(self):
        table = self.dlg.samPromptsTable
        table.setEditTriggers(QTableWidget.EditTrigger.SelectedClicked)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["ID", "Name", "Text Prompt"])
        table.setColumnHidden(0, True)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

    def _setup_sessions_table(self):
        # Progress + Confidence are sourced from SessionListItem aggregates
        # (inferences_total / inferences_done / confidence_threshold). The
        # Confidence value is immutable — fixed when the session was first
        # created — so the column is read-only.
        table = self.dlg.samSessionsTable
        table.setEditTriggers(QTableWidget.EditTrigger.SelectedClicked)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Name", "Progress", "Confidence"])
        table.setColumnHidden(0, True)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

    def _setup_spatial_prompts_table(self):
        table = self.dlg.spatialPromptsTable
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["ID", "Icon", "Geometry"])
        table.setColumnHidden(0, True)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

    def _setup_inferences_table(self):
        # One row per Inference belonging to the currently selected session.
        # Backend creates N inferences per user request (one per workflow
        # whose AOI intersects the request). A short ID prefix is shown for
        # human-readable identification; the row carries no click action —
        # session-level refresh is the only interaction.
        table = self.dlg.samInferencesTable
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["ID", "Status", "Created"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

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
        # Refresh-status now polls the selected session, so it tracks
        # session selection rather than the existence of a single inference.
        self.dlg.samRunSessionInference.setEnabled(enabled)
        self.dlg.deleteSessionButton.setEnabled(enabled)
        self.dlg.samRefreshInferenceStatus.setEnabled(enabled)

    def set_inference_refresh_enabled(self, enabled: bool):
        # Kept for service callers that flip the button after creating an
        # inference (the new session row gets selected immediately, so the
        # button would normally already be enabled by set_session_buttons_enabled).
        self.dlg.samRefreshInferenceStatus.setEnabled(enabled)

    # ------------------------------------------------------------------
    # Processings
    # ------------------------------------------------------------------

    def display_processings(self, items: List[ProcessingSummaryResponse]):
        # Only OK-status processings are interactive. Non-OK rows would just
        # error out on session creation, so they're filtered here at the
        # display boundary (cheap and the whole list fits in memory).
        visible = [p for p in items if (p.status or "").upper() == "OK"]
        table = self.dlg.samProcessingsTable
        table.setRowCount(len(visible))
        for row, proc in enumerate(visible):
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, proc.id)
            table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem()
            name_item.setData(Qt.DisplayRole, proc.name)
            table.setItem(row, 1, name_item)

            created_item = QTableWidgetItem()
            created_item.setData(Qt.DisplayRole, proc.created_at or "")
            table.setItem(row, 2, created_item)

    def selected_processing_id(self) -> Optional[str]:
        table = self.dlg.samProcessingsTable
        selected = table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        item = table.item(row, 0)
        return item.data(Qt.DisplayRole) if item else None

    def display_processing_detail(self, detail: ProcessingDetailResponse):
        params = detail.params or {}
        text_prompt = detail.text_prompt or self._extract_param_value(
            params, ("text_prompt", "textPrompt", "prompt")
        )
        confidence = detail.confidence_threshold
        if confidence is None:
            confidence = self._extract_param_value(
                params, ("confidence_threshold", "confidenceThreshold")
            )
        confidence_text = "-"
        if confidence not in (None, ""):
            try:
                confidence_text = f"{float(confidence):.2f}"
            except (TypeError, ValueError):
                confidence_text = str(confidence)
        prompt_text = text_prompt if text_prompt not in (None, "") else "-"
        self.dlg.samProcessingDetailsLabel.setText(
            f"Prompt: {prompt_text}    Confidence: {confidence_text}"
        )

    def clear_processing_detail(self):
        self.dlg.samProcessingDetailsLabel.setText("")

    @staticmethod
    def _extract_param_value(params: dict, keys: tuple):
        if not isinstance(params, dict):
            return None
        for key in keys:
            value = params.get(key)
            if value not in (None, ""):
                return value
        for nested_key in ("inferenceParams", "sourceParams", "meta"):
            nested = params.get(nested_key)
            if not isinstance(nested, dict):
                continue
            for key in keys:
                value = nested.get(key)
                if value not in (None, ""):
                    return value
        return None

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    def display_prompts(self, items: List[PromptResponse]):
        table = self.dlg.samPromptsTable
        table.blockSignals(True)
        table.setRowCount(len(items))
        for row, prompt in enumerate(items):
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, prompt.id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem()
            name_item.setData(Qt.DisplayRole, prompt.name or "")
            name_item.setData(Qt.UserRole, prompt.name or "")
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            table.setItem(row, 1, name_item)

            text_item = QTableWidgetItem()
            text_item.setData(Qt.DisplayRole, prompt.text_prompt or "")
            text_item.setData(Qt.UserRole, prompt.text_prompt or "")
            text_item.setFlags(text_item.flags() | Qt.ItemIsEditable)
            table.setItem(row, 2, text_item)
        table.blockSignals(False)


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
            self._set_spatial_prompt_row(table, row, sp)
        self.dlg.deleteSpatialPrompt.setEnabled(len(spatial_prompts) > 0)

    def show_spatial_prompt_layers(self, spatial_prompts: List[SpatialPromptResponse]):
        """Add spatial prompt features to map layers."""
        self._clear_prompts_layers()
        for sp in spatial_prompts:
            geom_type = "Point" if sp.geometry_type == GeometryType.POINT.value else "Polygon"
            self._add_spatial_prompt_feature(sp, geom_type)
        self._refresh_prompt_layer_extents()

    @staticmethod
    def _set_spatial_prompt_row(table, row: int, prompt: SpatialPromptResponse):
        id_item = QTableWidgetItem()
        id_item.setData(Qt.DisplayRole, prompt.id)
        table.setItem(row, 0, id_item)

        icon_item = QTableWidgetItem()
        icon_item.setData(
            Qt.DecorationRole,
            _build_prompt_pictogram(prompt.geometry_type, prompt.positive),
        )
        icon_item.setData(Qt.UserRole, prompt.geometry_type)
        icon_item.setToolTip(
            f"{'Positive' if prompt.positive else 'Negative'} {prompt.geometry_type}"
        )
        icon_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, 1, icon_item)

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
        table.setItem(row, 2, geom_item)

    def selected_spatial_prompt(self) -> Tuple[Optional[str], Optional[str]]:
        table = self.dlg.spatialPromptsTable
        selected = table.selectionModel().selectedRows()
        if not selected:
            return None, None
        row = selected[0].row()
        prompt_type = str(table.item(row, 1).data(Qt.UserRole)).lower()
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
            layer.updateExtents()
            layer.triggerRepaint()

    def _clear_prompts_layers(self):
        for layer in (self._point_prompts_layer, self._bbox_prompts_layer):
            if self._layer_alive(layer):
                layer.dataProvider().truncate()
                layer.updateExtents()
                layer.triggerRepaint()

    def _refresh_prompt_layer_extents(self):
        for layer in (self._point_prompts_layer, self._bbox_prompts_layer):
            if self._layer_alive(layer):
                layer.updateExtents()
                layer.triggerRepaint()

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def display_sessions(self, sessions: List[SessionResponse]):
        table = self.dlg.samSessionsTable
        selected_session_id = self.selected_session_id()
        table.blockSignals(True)
        try:
            table.clearSelection()
            table.setRowCount(len(sessions))
            selected_row = 0 if sessions else None
            for row, sess in enumerate(sessions):
                self._set_session_row(table, row, sess)
                if sess.id == selected_session_id:
                    selected_row = row
            if selected_row is not None:
                table.selectRow(selected_row)
        finally:
            table.blockSignals(False)

    def add_session_to_table(self, session: SessionResponse):
        table = self.dlg.samSessionsTable
        table.blockSignals(True)
        row = table.rowCount()
        table.insertRow(row)
        self._set_session_row(table, row, session)
        table.selectRow(row)
        table.blockSignals(False)

    @staticmethod
    def _set_session_row(table, row: int, sess: SessionResponse):
        id_item = QTableWidgetItem()
        id_item.setData(Qt.DisplayRole, sess.id)
        id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
        table.setItem(row, 0, id_item)

        name_item = QTableWidgetItem()
        name_item.setData(Qt.DisplayRole, sess.name or sess.id[:12])
        name_item.setData(Qt.UserRole, sess.name or sess.id[:12])
        name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
        table.setItem(row, 1, name_item)

        # Progress aggregates land on the LIST endpoint as inferences_total /
        # inferences_done; on the DETAIL endpoint they're absent and we fall
        # back to counting the embedded inferences[] list. Either way, blank
        # if neither is available.
        progress_item = QTableWidgetItem()
        progress_text = ""
        total = sess.inferences_total
        done = sess.inferences_done
        if total is None and sess.inferences is not None:
            total = len(sess.inferences)
            done = sum(1 for inf in sess.inferences
                       if (inf.status or "").lower() == "done")
        if total:
            progress_text = f"{done or 0}/{total}"
        progress_item.setData(Qt.DisplayRole, progress_text)
        progress_item.setFlags(progress_item.flags() & ~Qt.ItemIsEditable)
        table.setItem(row, 2, progress_item)

        # Confidence threshold — immutable per session. Backend ships it on
        # SessionListItem (post-B-1); blank if the response shape is older.
        conf_item = QTableWidgetItem()
        conf_text = ""
        if sess.confidence_threshold is not None:
            conf_text = f"{sess.confidence_threshold:.2f}"
        conf_item.setData(Qt.DisplayRole, conf_text)
        conf_item.setFlags(conf_item.flags() & ~Qt.ItemIsEditable)
        table.setItem(row, 3, conf_item)

    def selected_session_id(self) -> Optional[str]:
        table = self.dlg.samSessionsTable
        selected = table.selectionModel().selectedRows()
        if not selected:
            return None
        row = selected[0].row()
        item = table.item(row, 0)
        return item.data(Qt.DisplayRole) if item else None

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def display_session(self, session: SessionResponse):
        """Repaint the entire session view from a single SessionResponse.

        Drives three panels at once: the text-prompt label, the spatial
        prompts table, and the per-inference status table. Backed by the
        post-A4 SessionResponse shape that embeds the frozen prompt
        snapshot directly. SkipDataClass tolerance keeps the call safe
        against an older backend that doesn't yet ship those fields.
        """
        # Text prompt label — embedded TextPromptSummary.
        if session.text_prompt is not None:
            text = getattr(session.text_prompt, "text", "") or ""
            self.dlg.samSessionTextPromptLabel.setText(f"Prompt: {text}" if text else "")
        else:
            self.dlg.samSessionTextPromptLabel.setText("")

        # Frozen spatial prompts.
        self.populate_spatial_prompts_table(session.spatial_prompts or [])

        # Inferences table.
        table = self.dlg.samInferencesTable
        table.blockSignals(True)
        try:
            table.setRowCount(0)
            inferences = session.inferences or []
            table.setRowCount(len(inferences))
            for row, inf in enumerate(inferences):
                self._set_inference_row(table, row, inf)
        finally:
            table.blockSignals(False)

        self.update_session_row(session)

    def update_session_row(self, session: SessionResponse):
        table = self.dlg.samSessionsTable
        for row in range(table.rowCount()):
            id_item = table.item(row, 0)
            if id_item is None or id_item.data(Qt.DisplayRole) != session.id:
                continue
            self._set_session_row(table, row, session)
            return

    def clear_session_display(self):
        self.dlg.samSessionTextPromptLabel.setText("")
        self.populate_spatial_prompts_table([])

        table = self.dlg.samInferencesTable
        table.blockSignals(True)
        try:
            table.setRowCount(0)
        finally:
            table.blockSignals(False)

    @staticmethod
    def _set_inference_row(table, row: int, inf: InferenceStatusSummary):
        # Hide the full UUID in UserRole / tooltip; show a short prefix
        # in the cell so the table stays readable.
        id_item = QTableWidgetItem(inf.id[:8] if inf.id else "")
        id_item.setData(Qt.UserRole, inf.id)
        id_item.setToolTip(inf.id or "")
        table.setItem(row, 0, id_item)

        status_item = QTableWidgetItem(inf.status or "")
        table.setItem(row, 1, status_item)

        created_item = QTableWidgetItem(inf.created_at or "")
        table.setItem(row, 2, created_item)

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def load_result_layer(self, data: dict, session_id: Optional[str] = None):
        """Load (or refresh) the merged GeoJSON result for a session.

        Re-uses one layer per session id so partial-result refreshes update
        the existing layer in place instead of stacking duplicates.
        """
        geojson_str = json.dumps(data)
        existing = self._result_layers.get(session_id) if session_id else None
        if self._layer_alive(existing):
            QgsProject.instance().removeMapLayer(existing.id())
        layer_name = f"SAM Result {session_id[:8]}" if session_id else "SAM Result"
        layer = QgsVectorLayer(geojson_str, layer_name, "ogr")
        if layer.isValid():
            layer.updateExtents()
            QgsProject.instance().addMapLayer(layer)
            if session_id:
                self._result_layers[session_id] = layer

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


def _build_prompt_pictogram(geometry_type: str, positive: bool) -> QPixmap:
    """Render the SAM prompt marker used by the spatial prompts table."""
    color = QColor(0, 170, 0) if positive else QColor(200, 0, 0)
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(color, 1.5))
    painter.setBrush(QBrush(color))
    if geometry_type == GeometryType.POINT.value:
        painter.drawEllipse(3, 3, 10, 10)
    else:
        painter.drawPolygon(
            QPolygonF([
                QPointF(8.0, 2.5),
                QPointF(13.5, 13.0),
                QPointF(2.5, 13.0),
            ])
        )
    painter.end()
    return pixmap
