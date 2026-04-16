"""SAM Interactive controller — signal/slot wiring for SAM tab.

Thin wiring layer: connects UI signals to SamService methods.
No business logic here.
"""
import json
from typing import Callable, Optional

from PyQt5.QtCore import QObject, Qt

from qgis.core import QgsGeometry
from qgis.gui import QgsMapCanvas

from ..map_tools import SamPointMapTool, SamBboxMapTool
from ..service.sam import SamService
from ...dialogs.main_dialog import MainDialog
from ...schema.sam import parse_confidence_threshold


class SamController(QObject):
    """Controller for SAM Interactive tab.

    Args:
        aoi_provider: callable returning the current plugin AOI as QgsGeometry
            (WGS84) or None if no AOI is selected.
    """

    def __init__(
        self,
        dlg: MainDialog,
        sam_service: SamService,
        canvas: QgsMapCanvas,
        aoi_provider: Callable[[], Optional[QgsGeometry]],
    ):
        super().__init__()
        self.dlg = dlg
        self.service = sam_service
        self.view = self.service.view
        self._canvas = canvas
        self._aoi_provider = aoi_provider
        self._prev_map_tool = None
        self._updating_selection = False

        # Map tools
        self._point_tool = SamPointMapTool(canvas)
        self._bbox_tool = SamBboxMapTool(canvas)
        self._point_tool.point_captured.connect(self._on_point_captured)
        self._bbox_tool.bbox_captured.connect(self._on_bbox_captured)

        # Processings
        self.dlg.samRefreshProcessings.clicked.connect(self._refresh_processings)
        self.dlg.samProcessingsTable.selectionModel().selectionChanged.connect(
            self._on_processing_selected)
        self.dlg.samProcessingsTable.doubleClicked.connect(self._on_processing_double_clicked)
        self.dlg.samPreviewImage.clicked.connect(self._on_processing_double_clicked)
        self.dlg.deleteProcessingButton.clicked.connect(self._delete_processing)

        # Prompts
        self.dlg.samCreatePrompt.clicked.connect(self._create_prompt)
        self.dlg.samRefreshPrompts.clicked.connect(self._refresh_prompts)
        self.dlg.deletePromptButton.clicked.connect(self._delete_prompt)
        self.dlg.samAddPointPrompt.clicked.connect(self._activate_point_tool)
        self.dlg.samAddBboxPrompt.clicked.connect(self._activate_bbox_tool)
        self.dlg.samPromptsTable.selectionModel().selectionChanged.connect(
            self._on_prompt_selected)
        self.dlg.samPromptsTable.doubleClicked.connect(self._on_prompt_double_clicked)
        self.dlg.samPromptsTable.itemChanged.connect(self._on_prompt_item_changed)
        self.dlg.deleteSpatialPrompt.clicked.connect(self._unlink_spatial_prompt)

        # Sessions
        self.dlg.samRefreshSessions.clicked.connect(self._refresh_sessions)
        self.dlg.deleteSessionButton.clicked.connect(self._delete_session)
        self.dlg.samSessionsTable.selectionModel().selectionChanged.connect(
            self._on_session_selected)
        self.dlg.samSessionsTable.doubleClicked.connect(self._on_session_double_clicked)
        self.dlg.samSessionsTable.itemChanged.connect(self._on_session_item_changed)

        # Inference
        self.dlg.samRunInference.clicked.connect(self._run_inference)
        self.dlg.samRunSessionInference.clicked.connect(self._run_session_inference)
        self.dlg.samRefreshInferenceStatus.clicked.connect(self._refresh_inference_status)

        # Workflow debug
        self.dlg.samInferenceWorkflowCombo.currentIndexChanged.connect(
            self._on_workflow_combo_changed)

        # Results
        self.dlg.samLoadResult.clicked.connect(self._load_result)

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self):
        """Load initial data for all SAM tables."""
        self._refresh_processings()
        self._refresh_prompts()

    # ------------------------------------------------------------------
    # Processings
    # ------------------------------------------------------------------

    def _refresh_processings(self):
        self.service.list_processings()

    def _on_processing_selected(self):
        processing_id = self.view.selected_processing_id()
        has_selection = bool(processing_id)
        self.dlg.samRefreshSessions.setEnabled(has_selection)
        self.dlg.deleteProcessingButton.setEnabled(has_selection)
        if processing_id:
            self.service.get_processing(processing_id)
            self.service.list_workflows(processing_id)
            self.service.list_sessions(processing_id)

    def _on_processing_double_clicked(self):
        processing_id = self.view.selected_processing_id()
        if processing_id:
            self.service.show_processing_layers(processing_id)

    def _delete_processing(self):
        self.service.delete_processing()

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    def _on_prompt_selected(self):
        if self._updating_selection:
            return
        prompt_id = self.view.selected_prompt_id()
        self.view.set_prompt_buttons_enabled(bool(prompt_id))
        if prompt_id:
            self._updating_selection = True
            self.dlg.samSessionsTable.clearSelection()
            self._updating_selection = False
            self.service.get_prompt_detail(prompt_id)

    def _on_prompt_double_clicked(self):
        self.service.show_prompt_layers()

    def _create_prompt(self):
        text = self.dlg.samPromptText.text().strip() or None
        self.service.create_prompt(text_prompt=text)

    def _refresh_prompts(self):
        self.service.list_prompts()

    def _delete_prompt(self):
        self.service.delete_prompt()

    def _unlink_spatial_prompt(self):
        spatial_prompt_id, prompt_type = self.view.selected_spatial_prompt()
        print(spatial_prompt_id, prompt_type)
        if spatial_prompt_id:
            self.service.unlink_spatial_prompt(spatial_prompt_id, prompt_type)

    def _on_prompt_item_changed(self, item):
        if item.column() not in (1, 2):
            return
        previous_value = item.data(Qt.UserRole) or ""
        current_value = item.data(Qt.DisplayRole) or ""
        if previous_value == current_value:
            return

        row = item.row()
        prompt_id_item = self.dlg.samPromptsTable.item(row, 0)
        if prompt_id_item is None:
            return
        prompt_id = prompt_id_item.data(Qt.DisplayRole)
        name_value = self.dlg.samPromptsTable.item(row, 1).data(Qt.DisplayRole) or ""
        text_prompt_value = self.dlg.samPromptsTable.item(row, 2).data(Qt.DisplayRole) or ""
        self.service.update_prompt(
            prompt_id=prompt_id,
            name=name_value.strip() or None,
            text_prompt=text_prompt_value.strip() or None,
        )
        item.setData(Qt.UserRole, current_value)

    def _activate_point_tool(self):
        prompt_id = self.view.selected_prompt_id()
        processing_id = self.view.selected_processing_id()
        if not prompt_id or not processing_id:
            self.view.append_debug(
                "Add Point Prompt",
                {"error": "Select a prompt and a processing first"},
            )
            return
        self._prev_map_tool = self._canvas.mapTool()
        self._canvas.setMapTool(self._point_tool)
        self.dlg.hide()

    def _activate_bbox_tool(self):
        prompt_id = self.view.selected_prompt_id()
        processing_id = self.view.selected_processing_id()
        if not prompt_id or not processing_id:
            self.view.append_debug(
                "Add Bbox Prompt",
                {"error": "Select a prompt and a processing first"},
            )
            return
        self._prev_map_tool = self._canvas.mapTool()
        self._canvas.setMapTool(self._bbox_tool)
        self.dlg.hide()

    def _on_point_captured(self, geojson: dict, positive: bool):
        prompt_id = self.view.selected_prompt_id()
        processing_id = self.view.selected_processing_id()
        if prompt_id and processing_id:
            self.service.add_point_prompt(
                prompt_id=prompt_id,
                processing_id=processing_id,
                geometry=geojson,
                positive=positive,
            )
        self._restore_map_tool()
        self.dlg.show()

    def _on_bbox_captured(self, geojson: dict, positive: bool):
        prompt_id = self.view.selected_prompt_id()
        processing_id = self.view.selected_processing_id()
        if prompt_id and processing_id:
            self.service.add_bbox_prompt(
                prompt_id=prompt_id,
                processing_id=processing_id,
                geometry=geojson,
                positive=positive,
            )
        self._restore_map_tool()
        self.dlg.show()

    def _restore_map_tool(self):
        if self._prev_map_tool is not None:
            self._canvas.setMapTool(self._prev_map_tool)
            self._prev_map_tool = None

    def _confidence_threshold(self):
        return parse_confidence_threshold(
            self.dlg.samConfidenceThresholdInput.text()
        )

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def _on_session_selected(self):
        if self._updating_selection:
            return
        session_id = self.view.selected_session_id()
        self.view.set_session_buttons_enabled(bool(session_id))
        if session_id:
            self._updating_selection = True
            self.dlg.samPromptsTable.clearSelection()
            self._updating_selection = False
            self.service.get_session_detail(session_id)

    def _on_session_double_clicked(self):
        self.service.show_session_layers()

    def _refresh_sessions(self):
        processing_id = self.view.selected_processing_id()
        if processing_id:
            self.service.list_sessions(processing_id)

    def _copy_session(self):
        session_id = self.view.selected_session_id()
        if session_id:
            self.service.copy_session(session_id)

    def _delete_session(self):
        self.service.delete_session()

    def _on_session_item_changed(self, item):
        if item.column() != 1:
            return
        previous_value = item.data(Qt.UserRole) or ""
        current_value = item.data(Qt.DisplayRole) or ""
        if previous_value == current_value:
            return

        row = item.row()
        session_id_item = self.dlg.samSessionsTable.item(row, 0)
        if session_id_item is None:
            return
        session_id = session_id_item.data(Qt.DisplayRole)
        new_name = (current_value or "").strip()
        if not new_name:
            item.setData(Qt.DisplayRole, previous_value)
            self.view.append_debug("Rename Session", {"error": "Name must not be empty"})
            return
        self.service.update_session_name(session_id=session_id, name=new_name)
        item.setData(Qt.UserRole, new_name)
    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def _run_inference(self):
        """Run inference — creates a new session + first inference."""
        processing_id = self.view.selected_processing_id()
        prompt_id = self.view.selected_prompt_id()
        aoi = self._aoi_provider()
        if not processing_id or not prompt_id or not aoi:
            self.view.append_debug(
                "Run Inference",
                {"error": "Select processing, prompt, and AOI first"},
            )
            return
        confidence_threshold, threshold_error = self._confidence_threshold()
        if threshold_error:
            self.view.append_debug("Run Inference", {"error": threshold_error})
            return
        geometry = json.loads(aoi.asJson())
        self.service.create_inference(
            processing_id,
            prompt_id,
            geometry,
            confidence_threshold=confidence_threshold,
        )

    def _run_session_inference(self):
        """Add inference to an existing session."""
        session_id = self.view.selected_session_id()
        aoi = self._aoi_provider()
        if not session_id or not aoi:
            self.view.append_debug(
                "Session Inference",
                {"error": "Select session and AOI first"},
            )
            return
        geometry = json.loads(aoi.asJson())
        self.service.create_session_inference(
            session_id,
            geometry,
        )

    def _on_workflow_combo_changed(self):
        """Debug: fetch and display workflow detail when combo selection changes."""
        workflow_id = self.view.selected_workflow_id()
        if workflow_id:
            self.service.get_workflow(workflow_id)

    def _refresh_inference_status(self):
        inference_id = getattr(self.service, '_current_inference_id', None)
        if inference_id:
            self.service.get_inference_status(inference_id)

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def _load_result(self):
        session_id = self.view.selected_session_id()
        if session_id:
            self.service.get_result(session_id)
