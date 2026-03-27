"""SAM Interactive service — business logic for the SAM tab.

Coordinates SamApi (HTTP calls) and SamView (UI state).
Manages pagination state and response parsing.
"""
import json
from typing import Optional

from PyQt5.QtCore import QObject
from PyQt5.QtNetwork import QNetworkReply
from qgis.core import QgsProject

from ..api.sam_api import SamApi
from ..layer_utils import generate_raster_layer, get_bounding_box_from_tile_json, ResultsLoader, generate_vector_layer
from ..view.sam_view import SamView
from ...dialogs.main_dialog import MainDialog
from ...http import Http
from ...schema.sam import (
    ProcessingListResponse,
    ProcessingDetailResponse,
    WorkflowSummaryResponse,
    PromptListResponse,
    PromptDetailResponse,
    PromptCreateRequest,
    PointPromptRequest,
    BboxPromptRequest,
    SpatialPromptResponse,
    SessionCreateRequest,
    SessionResponse,
    SessionPromptsResponse,
    InferenceCreateRequest,
    SessionInferenceCreateRequest,
    InferenceResponse,
    ResultResponse,
)


class SamService(QObject):
    def __init__(self, dlg: MainDialog,
                 sam_api: SamApi,
                 mapflow_http: Http,
                 mapflow_server: str,
                 results_loader: ResultsLoader):
        super().__init__()
        self.dlg = dlg
        self.api = sam_api
        self._mapflow_http = mapflow_http
        self._mapflow_server = mapflow_server
        self.view = SamView(dlg)
        self.results_loader = results_loader

        # Pagination state for processings list
        self._offset = 0
        self._limit = 20
        self._total = 0

    # ------------------------------------------------------------------
    # Processings
    # ------------------------------------------------------------------

    def list_processings(self, filter_: Optional[str] = None):
        self.api.list_processings(
            callback=self.list_processings_callback,
            filter_=filter_,
            limit=self._limit,
            offset=self._offset,
        )

    def list_processings_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        result = ProcessingListResponse.from_dict(data)
        self._total = result.total
        self.view.display_processings(result.items)
        self.view.append_debug("List Processings", data)
        self.view.update_pagination_buttons(
            self.has_prev_page, self.has_next_page,
            self._offset, self._limit, self._total,
        )

    def get_processing(self, processing_id: str):
        self.api.get_processing(
            processing_id=processing_id,
            callback=self.get_processing_callback,
        )

    def get_processing_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        detail = ProcessingDetailResponse.from_dict(data)
        self.view.display_processing_detail(detail)
        self.view.append_debug("Processing Detail", data)

    def preview_image(self, processing_id: str):
        """Fetch Mapflow processing detail to load its raster preview layer."""
        self._mapflow_http.get(
            url=f"{self._mapflow_server}/processings/{processing_id}",
            callback=self._preview_image_callback,
        )

    def _preview_image_callback(self, response: QNetworkReply):
        # TODO: rewrite to use the same processing preview function as in mapflow.py
        # Probably via moving all the preview functions to a separate service
        data = json.loads(response.readAll().data().decode())
        raster_info = data.get("rasterLayer", {})
        tile_url = raster_info.get("tileUrl")
        tilejson_url = raster_info.get("tileJsonUrl")
        name = data.get("name", "SAM Preview")

        if not tile_url:
            self.view.append_debug("Preview Image", {"error": "No raster layer available"})
            return

        layer = generate_raster_layer(tile_url, f"{name} preview")
        if not layer or not layer.isValid():
            self.view.append_debug("Preview Image", {"error": "Failed to create raster layer"})
            return

        if tilejson_url:
            self._mapflow_http.get(
                url=tilejson_url,
                callback=self._preview_extent_callback,
                callback_kwargs={"layer": layer},
                use_default_error_handler=False,
            )
        else:
            QgsProject.instance().addMapLayer(layer)

    def _preview_extent_callback(self, response: QNetworkReply, layer):
        if response.error() == QNetworkReply.NoError:
            try:
                bbox = get_bounding_box_from_tile_json(response)
                layer.setExtent(bbox)
            except Exception:
                pass
        QgsProject.instance().addMapLayer(layer)

    # ------------------------------------------------------------------
    # Workflows
    # ------------------------------------------------------------------

    def list_workflows(self, processing_id: str):
        self.api.get_processing_workflows(
            processing_id=processing_id,
            callback=self.list_workflows_callback,
        )

    def list_workflows_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        workflows = [WorkflowSummaryResponse.from_dict(w) for w in data.get('items', [])]
        self.view.display_workflows(workflows)
        self.view.append_debug("Workflows", data)

    def get_workflow(self, workflow_id: str):
        self.api.get_workflow(
            workflow_id=workflow_id,
            callback=self.get_workflow_callback,
        )

    def get_workflow_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        self.view.append_debug("Workflow Detail", data)

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    def create_prompt(self, text_prompt: Optional[str] = None):
        request = PromptCreateRequest(text_prompt=text_prompt)
        self.api.create_prompt(
            request=request,
            callback=self.create_prompt_callback,
        )

    def create_prompt_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        self.view.append_debug("Create Prompt", data)
        self.list_prompts()

    def list_prompts(self):
        self.api.list_prompts(
            callback=self.list_prompts_callback,
        )

    def list_prompts_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        result = PromptListResponse.from_dict(data)
        self.view.display_prompts(result.items)
        self.view.append_debug("List Prompts", data)

    def get_prompt_detail(self, prompt_id: str):
        self.api.get_prompt(
            prompt_id=prompt_id,
            callback=self.get_prompt_detail_callback,
        )

    def get_prompt_detail_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        detail = PromptDetailResponse.from_dict(data)
        self.view.display_prompt_detail(detail)
        self.view.display_spatial_prompts(detail.point_prompts, detail.bbox_prompts)
        self.view.append_debug("Prompt Detail", data)

    def add_point_prompt(self, prompt_id: str, processing_id: str,
                         geometry: dict, positive: bool = True):
        request = PointPromptRequest(
            processing_id=processing_id,
            geometry=geometry,
            positive=positive,
        )
        self.api.add_point_prompt(
            prompt_id=prompt_id,
            request=request,
            callback=self.add_point_prompt_callback,
        )

    def add_point_prompt_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        prompt = SpatialPromptResponse.from_dict(data)
        self.view.add_prompt_to_map(prompt)
        self.view.append_debug("Point Prompt", data)
        self._refresh_prompt_detail()

    def add_bbox_prompt(self, prompt_id: str, processing_id: str,
                        geometry: dict, positive: bool = True):
        request = BboxPromptRequest(
            processing_id=processing_id,
            geometry=geometry,
            positive=positive,
        )
        self.api.add_bbox_prompt(
            prompt_id=prompt_id,
            request=request,
            callback=self.add_bbox_prompt_callback,
        )

    def add_bbox_prompt_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        prompt = SpatialPromptResponse.from_dict(data)
        self.view.add_prompt_to_map(prompt)
        self.view.append_debug("Bbox Prompt", data)
        self._refresh_prompt_detail()

    def _refresh_prompt_detail(self):
        """Re-fetch prompt detail to refresh the spatial prompts table."""
        prompt_id = self.view.selected_prompt_id()
        if prompt_id:
            self.get_prompt_detail(prompt_id)

    def unlink_spatial_prompt(self, spatial_prompt_id: str, prompt_type: str):
        """Unlink a point or bbox prompt from the currently selected prompt."""
        prompt_id = self.view.selected_prompt_id()
        if not prompt_id:
            return
        if prompt_type.lower() == "point":
            self.api.unlink_point_prompt(
                prompt_id=prompt_id,
                point_prompt_id=spatial_prompt_id,
                callback=self._unlink_spatial_prompt_callback,
            )
        else:
            self.api.unlink_bbox_prompt(
                prompt_id=prompt_id,
                bbox_prompt_id=spatial_prompt_id,
                callback=self._unlink_spatial_prompt_callback,
            )

    def _unlink_spatial_prompt_callback(self, response: QNetworkReply):
        self.view.append_debug("Unlink Prompt", {"status": response.attribute(0)})
        self._refresh_prompt_detail()

    def delete_prompt(self):
        prompt_id = self.view.selected_prompt_id()
        self.api.delete_prompt(prompt_id,
                               callback = self.delete_prompt_callback)

    def delete_prompt_callback(self, response: QNetworkReply):
        self.list_prompts()

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def create_session(self, processing_id: str, prompt_id: str):
        request = SessionCreateRequest(
            processing_id=processing_id,
            prompt_id=prompt_id,
        )
        self.api.create_session(
            request=request,
            callback=self.create_session_callback,
        )

    def create_session_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        session = SessionResponse.from_dict(data)
        self.view.append_debug("Create Session", data)
        self.view.add_session_to_table(session)

    def delete_session(self):
        session_id = self.view.selected_session_id()
        self.api.delete_session(session_id,
                               callback=self.delete_session_callback)

    def delete_session_callback(self, response: QNetworkReply):
        self.list_sessions(self.view.selected_processing_id())

    def get_session_detail(self, session_id: str):
        self.api.get_session(
            session_id=session_id,
            callback=self.get_session_detail_callback,
        )

    def get_session_detail_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        session = SessionResponse.from_dict(data)
        self.view.display_session_detail(session)
        self.view.append_debug("Session Detail", data)
        # Also fetch and display session's frozen prompt snapshot
        self.get_session_prompts(session.id)
        # Also add vector layer with results
        self.add_tile_vector_layer(name = f"Results {session.id}",
                                   tile_url = session.vector_layer.tile_url)

    def get_session_prompts(self, session_id: str):
        self.api.get_session_prompts(
            session_id=session_id,
            callback=self.get_session_prompts_callback,
        )

    def get_session_prompts_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        prompts = SessionPromptsResponse.from_dict(data)
        self.view.display_spatial_prompts(prompts.point_prompts, prompts.bbox_prompts)
        self.view.append_debug("Session Prompts", data)

    def copy_session(self, session_id: str):
        self.api.copy_session(
            session_id=session_id,
            callback=self.copy_session_callback,
        )

    def copy_session_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        session = SessionResponse.from_dict(data)
        self.view.append_debug("Copy Session", data)
        self.view.add_session_to_table(session)

    def list_sessions(self, processing_id: str):
        self.api.get_processing_sessions(
            processing_id=processing_id,
            callback=self.list_sessions_callback,
        )

    def list_sessions_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        sessions = [SessionResponse.from_dict(s) for s in data.get('items', [])]
        self.view.display_sessions(sessions)
        self.view.append_debug("List Sessions", data)

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def create_inference(self, prompt_id: str, workflow_id: str, geometry: dict):
        """POST /inference — creates new session + first inference."""
        request = InferenceCreateRequest(
            prompt_id=prompt_id,
            workflow_id=workflow_id,
            geometry=geometry,
        )
        self.api.create_inference(
            request=request,
            callback=self.create_inference_callback,
        )

    def create_inference_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        # Response contains session info — update sessions table
        session_data = data.get("session")
        if session_data:
            session = SessionResponse.from_dict(session_data)
            self.view.add_session_to_table(session)
        inference = InferenceResponse.from_dict(data)
        self.view.display_inference_status(inference)
        self.view.append_debug("Create Inference", data)
        self._current_inference_id = inference.id
        self.view.set_inference_refresh_enabled(True)

    def create_session_inference(self, session_id: str, workflow_id: str, geometry: dict):
        """POST /sessions/{id}/inferences — add inference to existing session."""
        request = SessionInferenceCreateRequest(
            workflow_id=workflow_id,
            geometry=geometry,
        )
        self.api.create_session_inference(
            session_id=session_id,
            request=request,
            callback=self.create_session_inference_callback,
        )

    def create_session_inference_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        inference = InferenceResponse.from_dict(data)
        self.view.display_inference_status(inference)
        self.view.append_debug("Session Inference", data)
        self._current_inference_id = inference.id
        self.view.set_inference_refresh_enabled(True)

    def get_inference_status(self, inference_id: str):
        self.api.get_inference(
            inference_id=inference_id,
            callback=self.get_inference_status_callback,
        )

    def get_inference_status_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        inference = InferenceResponse.from_dict(data)
        self.view.display_inference_status(inference)
        self.view.append_debug("Inference Status", data)

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def get_result(self, session_id: str):
        self.api.get_result(
            session_id=session_id,
            callback=self.get_result_callback,
        )

    def get_result_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        self.view.load_result_layer(data)
        # self.view.append_debug("Session Result", data)

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    @property
    def has_next_page(self) -> bool:
        return self._offset + self._limit < self._total

    @property
    def has_prev_page(self) -> bool:
        return self._offset > 0

    def next_page(self):
        if self.has_next_page:
            self._offset += self._limit
            self.list_processings()

    def prev_page(self):
        if self.has_prev_page:
            self._offset = max(0, self._offset - self._limit)
            self.list_processings()

    # ---
    # result layer
    # ---
    def add_tile_vector_layer(self, name: str, tile_url: str):
        vector_layer = generate_vector_layer(tile_url,
                                             name=name)
        self.results_loader.add_layer(vector_layer)