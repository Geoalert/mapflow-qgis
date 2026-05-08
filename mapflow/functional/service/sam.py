"""SAM Interactive service — business logic for the SAM tab.

Coordinates SamApi (HTTP calls) and SamView (UI state).
Manages pagination state and response parsing.
"""
import json
import tempfile
from typing import Callable, Iterable, List, Optional

from PyQt5.QtCore import QObject
from PyQt5.QtNetwork import QNetworkReply

from ..api.sam_api import SamApi
from ..layer_utils import ResultsLoader, generate_vector_layer
from ..view.sam_view import SamView
from ...dialogs.main_dialog import MainDialog
from ...config import config
from ...schema.project import UserRole
from ...schema.sam import (
    ProcessingListResponse,
    ProcessingDetailResponse,
    PromptListResponse,
    PromptDetailResponse,
    PromptCreateRequest,
    PromptCopyRequest,
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

        # Pagination state for processings list. Backend dropped `total` to
        # skip the COUNT(*) on large tables; we paginate by offset+limit and
        # use `has_more` from each response to drive the "next page"
        # affordance. Note: a page may legitimately come back with fewer
        # than `limit` items even when has_more=True.
        self._offset = 0
        self._limit = config.SAM_PROCESSINGS_PAGE_LIMIT
        self._has_more = False

        # Project + role context. The SAM tab follows the main-tab project
        # selection: with no project, the processings table stays empty and
        # no HTTP request is made. The role drives which action buttons are
        # enabled in the view (mirrors backend ACL: contributor+ for create,
        # maintainer+ for delete/rename).
        self._project_id: Optional[str] = None
        self._user_role: UserRole = UserRole.owner

        # Cached data for double-click layer display
        self._last_prompt_detail = None
        self._last_session = None
        self._last_session_prompts = []
        # Tracks whichever set of spatial prompts is currently rendered on
        # the map (from prompt or session double-click). Used by the
        # "Show rasters" toggle handler to know what to re-fetch when the
        # user flips the checkbox back on.
        self._last_displayed_prompts: List[SpatialPromptResponse] = []

    # ------------------------------------------------------------------
    # Project context
    # ------------------------------------------------------------------

    def set_project_context(self, project_id: Optional[str], user_role: UserRole):
        """Update the project the SAM tab is bound to and the caller's role.

        Resets pagination so the new project starts on page 0. When the
        project is unset (main table is on the projects view), clears the
        processings table without firing an HTTP request — matches the rule
        that processings are only meaningful within a project context.
        """
        self._project_id = project_id
        self._user_role = user_role or UserRole.readonly
        self._offset = 0
        self._has_more = False
        self.view.set_user_role(self._user_role)
        if project_id:
            self.list_processings()
        else:
            self.view.clear_processings_table()

    # ------------------------------------------------------------------
    # Processings
    # ------------------------------------------------------------------

    def list_processings(self, filter_: Optional[str] = None):
        if not self._project_id:
            self.view.clear_processings_table()
            return
        self.api.list_processings(
            callback=self.list_processings_callback,
            filter_=filter_,
            limit=self._limit,
            offset=self._offset,
            project_id=self._project_id,
        )

    def refresh_processings(self, filter_: Optional[str] = None):
        """Refresh the processings list, jumping back to page 0.

        Pagination state survives between fetches so prev/next pages keep
        their offset; the Refresh button explicitly opts out of that — the
        user expects to see the newest data.
        """
        self._offset = 0
        self.list_processings(filter_=filter_)

    def list_processings_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        result = ProcessingListResponse.from_dict(data)
        self._has_more = result.has_more
        self.view.display_processings(result.items)
        self.view.append_debug("List Processings", data)
        self.view.update_pagination_buttons(self.has_prev_page, self.has_next_page)

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

    def copy_prompt(self, prompt_id: str,
                    name: Optional[str] = None,
                    text_prompt: Optional[str] = None):
        request = PromptCopyRequest(name=name, text_prompt=text_prompt)
        self.api.copy_prompt(
            prompt_id=prompt_id,
            request=request,
            callback=self.copy_prompt_callback,
        )

    def copy_prompt_callback(self, response: QNetworkReply):
        data = json.loads(response.readAll().data().decode())
        self.view.append_debug("Copy Prompt", data)
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
        """Double-click action: show spatial prompt layers on map.

        Renders vector geometry synchronously, then kicks off async raster
        downloads — the GeoTIFF crops drop into the previews subgroup as
        each one finishes. View clears the previous batch before painting.
        """
        if self._last_prompt_detail:
            spatial_prompts = list(self._last_prompt_detail.spatial_prompts or [])
            self._last_displayed_prompts = spatial_prompts
            self.view.show_spatial_prompt_layers(spatial_prompts)
            self._fetch_spatial_prompt_previews(spatial_prompts)

    # ------------------------------------------------------------------
    # Spatial prompt raster previews
    # ------------------------------------------------------------------

    def _fetch_spatial_prompt_previews(self,
                                       spatial_prompts: Iterable[SpatialPromptResponse]):
        """Start an async download for every spatial prompt with a raster_url.

        `raster_url` is a backend-rooted path (e.g.
        `/sessions/{sid}/spatial_prompts/{spid}/raster`); the API client
        joins it with the SAM base. Skipped silently when the field is
        empty — older prompts created before the preview pipeline existed
        don't have one.

        Short-circuits when the user has the "Show rasters" toggle off —
        no HTTP requests, no temp files, no layers. Toggling the checkbox
        back on re-enters this method via on_show_rasters_toggled.
        """
        if not self.view.is_show_rasters_enabled():
            return
        for sp in spatial_prompts:
            if not sp.raster_url:
                continue
            self.api.download_spatial_prompt_raster(
                raster_url=sp.raster_url,
                callback=self._on_spatial_prompt_raster_downloaded,
                callback_kwargs={
                    "sp_id": sp.id,
                    "geometry_type": sp.geometry_type,
                },
            )

    def on_show_rasters_toggled(self, enabled: bool):
        """User flipped the "Show rasters" checkbox.

        On: re-download previews for whatever spatial prompts are
        currently rendered (so the user sees rasters appear without
        having to double-click again).
        Off: drop existing preview layers; further downloads are
        suppressed by `_fetch_spatial_prompt_previews`.
        """
        if enabled:
            self._fetch_spatial_prompt_previews(self._last_displayed_prompts)
        else:
            self.view.clear_spatial_prompt_previews()

    def _on_spatial_prompt_raster_downloaded(self, response: QNetworkReply,
                                             sp_id: str, geometry_type: str):
        # Match the convention used by other binary-body callbacks in this
        # module (see get_result_callback): readAll().data() returns the
        # raw bytes regardless of QByteArray vs bytes mocking conventions.
        data = response.readAll().data()
        if not data:
            self.view.append_debug(
                "Spatial Prompt Preview",
                {"sp_id": sp_id, "error": "empty body"},
            )
            return
        # delete=False so the file outlives the context manager — QGIS
        # holds the path; the view tracks it for cleanup on next clear.
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as f:
            f.write(data)
            local_path = f.name
        self.view.add_spatial_prompt_preview(
            local_path=local_path,
            sp_id=sp_id,
            geometry_type=geometry_type,
        )

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
            spatial_prompts = list(self._last_session_prompts)
            self._last_displayed_prompts = spatial_prompts
            self.view.show_spatial_prompt_layers(spatial_prompts)
            # The frozen prompt snapshot also carries raster_url per spatial
            # prompt — show those previews so the session's source crops
            # are visible alongside the result.
            self._fetch_spatial_prompt_previews(spatial_prompts)

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
        # Server tells us directly whether more rows exist beyond this page.
        # We do not infer it from items count vs limit because a page can
        # be partially trimmed server-side while still having more rows
        # available (rows archived during a per-page sync).
        return self._has_more

    @property
    def has_prev_page(self) -> bool:
        return self._offset > 0

    def next_page(self):
        if self.has_next_page:
            # Always advance by the full limit, even if the current page
            # came back partial — that's what `offset` semantics require.
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
