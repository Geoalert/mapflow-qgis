"""SAM Interactive controller — signal/slot wiring for SAM tab.

Thin wiring layer: connects UI signals to SamService methods.
No business logic here.
"""
from PyQt5.QtCore import QObject

from qgis.gui import QgsMapCanvas

from ..map_tools import SamPointMapTool, SamBboxMapTool
from ..service.sam import SamService
from ...dialogs.main_dialog import MainDialog


class SamController(QObject):
    def __init__(self, dlg: MainDialog, sam_service: SamService, canvas: QgsMapCanvas):
        super().__init__()
        self.dlg = dlg
        self.service = sam_service
        self.view = self.service.view
        self._canvas = canvas
        self._prev_map_tool = None

        # Map tools
        self._point_tool = SamPointMapTool(canvas)
        self._bbox_tool = SamBboxMapTool(canvas)
        self._point_tool.point_captured.connect(self._on_point_captured)
        self._bbox_tool.bbox_captured.connect(self._on_bbox_captured)

        # Processings
        self.dlg.samRefreshProcessings.clicked.connect(self._refresh_processings)
        self.dlg.samProcessingsTable.selectionModel().selectionChanged.connect(
            self._on_processing_selected)
        self.dlg.samViewWorkflows.clicked.connect(self._view_workflows)
        self.dlg.samViewSessions.clicked.connect(self._refresh_sessions)

        # Prompts
        self.dlg.samCreatePrompt.clicked.connect(self._create_prompt)
        self.dlg.samRefreshPrompts.clicked.connect(self._refresh_prompts)
        self.dlg.samViewPromptDetail.clicked.connect(self._view_prompt_detail)
        self.dlg.samAddPointPrompt.clicked.connect(self._activate_point_tool)
        self.dlg.samAddBboxPrompt.clicked.connect(self._activate_bbox_tool)

        # Prompts table selection
        self.dlg.samPromptsTable.selectionModel().selectionChanged.connect(
            self._on_prompt_selected)

        # Sessions
        self.dlg.samCreateSession.clicked.connect(self._create_session)
        self.dlg.samRefreshSessions.clicked.connect(self._refresh_sessions)
        self.dlg.samViewSessionDetail.clicked.connect(self._view_session_detail)
        self.dlg.samCopySession.clicked.connect(self._copy_session)
        self.dlg.samSessionsTable.selectionModel().selectionChanged.connect(
            self._on_session_selected)

        # Inference
        self.dlg.samDrawAoi.clicked.connect(self._activate_aoi_tool)
        self.dlg.samRunInference.clicked.connect(self._run_inference)
        self.dlg.samRefreshInferenceStatus.clicked.connect(self._refresh_inference_status)

        # Results
        self.dlg.samLoadResult.clicked.connect(self._load_result)

        # AOI tool (reuse bbox tool for drawing inference AOI)
        self._aoi_tool = SamBboxMapTool(canvas)
        self._aoi_tool.bbox_captured.connect(self._on_aoi_captured)
        self._inference_aoi = None

    # ------------------------------------------------------------------
    # Processings
    # ------------------------------------------------------------------

    def _refresh_processings(self):
        self.service.list_processings()

    def _on_processing_selected(self):
        processing_id = self.view.selected_processing_id()
        self.view.set_processing_buttons_enabled(bool(processing_id))
        self.dlg.samRefreshSessions.setEnabled(bool(processing_id))
        if processing_id:
            self.service.get_processing(processing_id)

    def _view_workflows(self):
        processing_id = self.view.selected_processing_id()
        if processing_id:
            self.service.list_workflows(processing_id)

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    def _on_prompt_selected(self):
        prompt_id = self.view.selected_prompt_id()
        self.view.set_prompt_buttons_enabled(bool(prompt_id))

    def _create_prompt(self):
        text = self.dlg.samPromptText.text().strip() or None
        self.service.create_prompt(text_prompt=text)

    def _refresh_prompts(self):
        self.service.list_prompts()

    def _view_prompt_detail(self):
        prompt_id = self.view.selected_prompt_id()
        if prompt_id:
            self.service.get_prompt_detail(prompt_id)

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
        self.view.append_debug(
            "Add Point Prompt",
            {"status": "Click on map to add point prompt"},
        )

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
        self.view.append_debug(
            "Add Bbox Prompt",
            {"status": "Draw rectangle on map to add bbox prompt"},
        )

    def _on_point_captured(self, geojson: dict):
        prompt_id = self.view.selected_prompt_id()
        processing_id = self.view.selected_processing_id()
        positive = self.dlg.samPositivePrompt.isChecked()
        if prompt_id and processing_id:
            self.service.add_point_prompt(
                prompt_id=prompt_id,
                processing_id=processing_id,
                geometry=geojson,
                positive=positive,
            )
        self._restore_map_tool()

    def _on_bbox_captured(self, geojson: dict):
        prompt_id = self.view.selected_prompt_id()
        processing_id = self.view.selected_processing_id()
        positive = self.dlg.samPositivePrompt.isChecked()
        if prompt_id and processing_id:
            self.service.add_bbox_prompt(
                prompt_id=prompt_id,
                processing_id=processing_id,
                geometry=geojson,
                positive=positive,
            )
        self._restore_map_tool()

    def _restore_map_tool(self):
        if self._prev_map_tool is not None:
            self._canvas.setMapTool(self._prev_map_tool)
            self._prev_map_tool = None

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def _on_session_selected(self):
        session_id = self.view.selected_session_id()
        self.view.set_session_buttons_enabled(bool(session_id))

    def _create_session(self):
        processing_id = self.dlg.samSessionProcessingCombo.currentData()
        prompt_id = self.dlg.samSessionPromptCombo.currentData()
        if not processing_id or not prompt_id:
            self.view.append_debug(
                "Create Session",
                {"error": "Select a processing and a prompt in the combo boxes"},
            )
            return
        self.service.create_session(processing_id, prompt_id)

    def _refresh_sessions(self):
        processing_id = self.view.selected_processing_id()
        if processing_id:
            self.service.list_sessions(processing_id)

    def _view_session_detail(self):
        session_id = self.view.selected_session_id()
        if session_id:
            self.service.get_session_detail(session_id)

    def _copy_session(self):
        session_id = self.view.selected_session_id()
        if session_id:
            self.service.copy_session(session_id)

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def _activate_aoi_tool(self):
        self._prev_map_tool = self._canvas.mapTool()
        self._canvas.setMapTool(self._aoi_tool)
        self.view.append_debug(
            "Draw AOI",
            {"status": "Draw rectangle on map for inference AOI"},
        )

    def _on_aoi_captured(self, geojson: dict):
        self._inference_aoi = geojson
        self.view.append_debug("AOI Captured", geojson)
        self._restore_map_tool()

    def _run_inference(self):
        session_id = self.dlg.samInferenceSessionCombo.currentData()
        workflow_id = self.dlg.samInferenceWorkflowCombo.currentData()
        if not session_id or not workflow_id or not self._inference_aoi:
            self.view.append_debug(
                "Run Inference",
                {"error": "Select session, workflow, and draw AOI first"},
            )
            return
        self.service.create_inference(session_id, workflow_id, self._inference_aoi)
        self._inference_aoi = None

    def _refresh_inference_status(self):
        inference_id = getattr(self.service, '_current_inference_id', None)
        if inference_id:
            self.service.get_inference_status(inference_id)

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def _load_result(self):
        session_id = self.dlg.samResultSessionCombo.currentData()
        if session_id:
            self.service.get_result(session_id)
