"""SAM Interactive service — business logic for the SAM tab.

Coordinates SamApi (HTTP calls) and SamView (UI state).
Manages pagination state and response parsing.
"""
import json
from typing import Callable, Optional

from PyQt5.QtCore import QObject
from PyQt5.QtNetwork import QNetworkReply

from ..api.sam_api import SamApi
from ..layer_utils import ResultsLoader, generate_vector_layer
from ..view.sam_view import SamView
from ...dialogs.main_dialog import MainDialog
from ...config import config
from ...schema.sam import (
    ProcessingListResponse,
    ProcessingDetailResponse,
    PromptListResponse,
    PromptDetailResponse,
    PromptCreateRequest,
    PromptUpdateRequest,
    PointPromptRequest,
    BboxPromptRequest,
    SpatialPromptResponse,
    SessionNameUpdateRequest,
    SessionResponse,
    InferenceCreateRequest,
    SessionInferenceCreateRequest,
)


class SamService(QObject):
    def __init__(self, dlg: MainDialog,
                 sam_api: SamApi,
                 results_loader: ResultsLoader,
                 load_processing_results_callback: Optional[Callable] = None):
        super().__init__()
        self.dlg = dlg
        self.api = sam_api
        self.view = SamView(dlg)
        self.results_loader = results_loader
        self._load_processing_results_callback = load_processing_results_callback

        # Pagination state for processings list
        self._offset = 0
        self._limit = config.SAM_PROCESSINGS_PAGE_LIMIT
        self._total = 0

        # Cached data for double-click layer display
        self._last_prompt_detail = None
        self._last_session = None
        self._last_session_prompts = []

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

    def delete_processing(self):
        processing_id = self.view.selected_processing_id()
        if not processing_id:
            return
        self.api.delete_processing(
            processing_id=processing_id,
            callback=self._delete_processing_callback,
        )

    def _delete_processing_callback(self, response: QNetworkReply):
        self.list_processings()

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

    # ------------------------------------------------------------------
    # Workflows
    # ------------------------------------------------------------------
    #
    # Workflows are no longer user-facing — the backend auto-selects them
    # from AOI intersection. The processing-level workflows endpoint
    # (GET /processings/{id}/workflows) and GET /workflows/{id} remain on
    # SamApi for future debug needs but are not driven from the UI.

    def show_processing_layers(self, processing_id: str):
        """Double-click action: use the main-tab "see results" flow only."""
        if self._load_processing_results_callback:
            self._load_processing_results_callback(processing_id=processing_id)

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    def create_prompt(self, name: Optional[str] = None, text_prompt: Optional[str] = None):
        request = PromptCreateRequest(name=name, text_prompt=text_prompt)
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
            limit=100
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
        self._last_prompt_detail = detail
        self.view.populate_spatial_prompts_table(detail.spatial_prompts)
        self.view.append_debug("Prompt Detail", data)

    def show_prompt_layers(self):
        """Double-click action: show spatial prompt layers on map."""
        if self._last_prompt_detail:
            self.view.show_spatial_prompt_layers(self._last_prompt_detail.spatial_prompts)

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

    def update_prompt(self,
                      prompt_id: str,
                      name: Optional[str],
                      text_prompt: Optional[str]):
        request = PromptUpdateRequest(name=name, text_prompt=text_prompt)
        self.api.update_prompt(
            prompt_id=prompt_id,
            request=request,
            callback=self.update_prompt_callback,
            callback_kwargs={"prompt_id": prompt_id},
        )

    def update_prompt_callback(self, response: QNetworkReply, prompt_id: str):
        data = json.loads(response.readAll().data().decode())
        self.view.append_debug("Update Prompt", data)
        self.list_prompts()
        if prompt_id:
            self.get_prompt_detail(prompt_id)

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------
    #
    # Sessions are not created standalone — POST /inference creates the
    # session implicitly. POST /sessions/{id}/copy was removed from the
    # backend along with the workflow-visibility refactor.

    def delete_session(self):
        session_id = self.view.selected_session_id()
        self.api.delete_session(session_id,
                               callback=self.delete_session_callback)

    def delete_session_callback(self, response: QNetworkReply):
        self.list_sessions(self.view.selected_processing_id())

    def update_session_name(self, session_id: str, name: str):
        request = SessionNameUpdateRequest(name=name)
        self.api.update_session_name(
            session_id=session_id,
            request=request,
            callback=self.update_session_name_callback,
            callback_kwargs={"session_id": session_id},
        )

    def update_session_name_callback(self, response: QNetworkReply, session_id: str):
        data = json.loads(response.readAll().data().decode())
        self.view.append_debug("Update Session Name", data)
        processing_id = self.view.selected_processing_id()
        if processing_id:
            self.list_sessions(processing_id)
        if session_id:
            self.get_session_detail(session_id)

    def get_session_detail(self, session_id: str):
        self.api.get_session(
            session_id=session_id,
            callback=self.get_session_detail_callback,
        )

    def get_session_detail_callback(self, response: QNetworkReply):
        """Render the entire session at once.

        `GET /sessions/{id}` is the freshest view in the system: backend
        bulk-refreshes WE statuses for non-terminal inferences before
        responding, and embeds the frozen prompt snapshot directly. So one
        call drives every panel in the session view.

        Important UX rule: this path must not mutate map layers. Result
        loading is explicit (Result button) or deliberate (double-click),
        never a side effect of row selection.
        """
        data = json.loads(response.readAll().data().decode())
        session = SessionResponse.from_dict(data)
        self._last_session = session
        self._last_session_prompts = session.spatial_prompts or []

        self.view.display_session(session)
        self.view.append_debug("Session Detail", data)

    def refresh_session_status(self, session_id: str):
        """Manual session-level status poll triggered by the Refresh button.

        Repaints the whole session view in one shot: status table, prompt
        snapshot, and text prompt. No map/layer side effects.
        """
        self.get_session_detail(session_id)

    def show_session_layers(self):
        """Double-click action: show result layer + spatial prompt layers on map."""
        session = getattr(self, '_last_session', None)
        if session and session.vector_layer:
            self.add_tile_vector_layer(
                name=f"Results {session.id}",
                tile_url=session.vector_layer.tile_url,
            )
        if self._last_session_prompts:
            self.view.show_spatial_prompt_layers(self._last_session_prompts)

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
        session_id = self.view.selected_session_id()
        if session_id:
            self.get_session_detail(session_id)
        else:
            self.view.clear_session_display()

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def create_inference(
        self,
        processing_id: str,
        prompt_id: str,
        geometry: dict,
        confidence_threshold: Optional[float] = None,
    ):
        """POST /inference — creates a new session and dispatches the first
        batch of inferences (one per workflow intersecting the AOI)."""
        request = InferenceCreateRequest(
            processing_id=processing_id,
            prompt_id=prompt_id,
            geometry=geometry,
            confidence_threshold=confidence_threshold,
        )
        self.api.create_inference(
            request=request,
            callback=self.create_inference_callback,
        )

    def create_inference_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        session = SessionResponse.from_dict(data)
        self._last_session = session
        self._last_session_prompts = session.spatial_prompts or []
        self.view.append_debug("Create Inference", data)
        self.view.add_session_to_table(session)
        self.view.display_session(session)
        self.view.set_inference_refresh_enabled(True)

    def create_session_inference(
        self,
        session_id: str,
        geometry: dict,
    ):
        """POST /sessions/{id}/inferences — add a new inference batch (one per
        intersecting workflow) to an existing session."""
        request = SessionInferenceCreateRequest(
            geometry=geometry,
        )
        self.api.create_session_inference(
            session_id=session_id,
            request=request,
            callback=self.create_session_inference_callback,
        )

    def create_session_inference_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        session = SessionResponse.from_dict(data)
        self._last_session = session
        self._last_session_prompts = session.spatial_prompts or []
        self.view.append_debug("Session Inference", data)
        self.view.display_session(session)
        self.view.set_inference_refresh_enabled(True)

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def get_result(self, session_id: str):
        self.api.get_result(
            session_id=session_id,
            callback=self.get_result_callback,
            callback_kwargs={"session_id": session_id},
        )

    def get_result_callback(self, response: QNetworkReply, session_id: str):
        # GET /result/{session_id} returns the merged session GeoJSON
        # FeatureCollection directly, or HTTP 204 when no result exists yet.
        # We treat empty body as "no partial result available" silently —
        # this is expected during the in-progress phase.
        raw = response.readAll().data()
        if not raw:
            return
        try:
            data = json.loads(raw.decode())
        except ValueError:
            self.view.append_debug("Session Result", {"error": "non-JSON response"})
            return
        self.view.load_result_layer(data, session_id=session_id)

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
