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

        # Prompts
        self.dlg.samCreatePrompt.clicked.connect(self._create_prompt)
        self.dlg.samRefreshPrompts.clicked.connect(self._refresh_prompts)
        self.dlg.samViewPromptDetail.clicked.connect(self._view_prompt_detail)
        self.dlg.samAddPointPrompt.clicked.connect(self._activate_point_tool)
        self.dlg.samAddBboxPrompt.clicked.connect(self._activate_bbox_tool)

    # ------------------------------------------------------------------
    # Processings
    # ------------------------------------------------------------------

    def _refresh_processings(self):
        self.service.list_processings()

    def _on_processing_selected(self):
        processing_id = self.view.selected_processing_id()
        if processing_id:
            self.service.get_processing(processing_id)

    def _view_workflows(self):
        processing_id = self.view.selected_processing_id()
        if processing_id:
            self.service.list_workflows(processing_id)

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

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
