"""SAM Interactive backend API client.

Follows existing ProjectApi pattern: QObject subclass, thin Http wrappers,
callback-based async via Qt signals.
"""
from typing import Callable, Optional

from PyQt5.QtCore import QObject

from ...http import Http
from ...schema.sam import (
    ProcessingCreateRequest,
    PromptCreateRequest,
    PromptCopyRequest,
    PromptUpdateRequest,
    PointPromptRequest,
    BboxPromptRequest,
    SessionNameUpdateRequest,
    InferenceCreateRequest,
    SessionInferenceCreateRequest,
)


class SamApi(QObject):

    def __init__(self, http: Http, server: str):
        super().__init__()
        self.server = f"{server}/sam-interactive"
        self.http = http


    # ------------------------------------------------------------------
    # Configuration endpoints
    # ------------------------------------------------------------------

    def get_wdid(self, callback: Callable):
        self.http.get(
            url=f"{self.server}/wdid",
            headers={},
            callback=callback,
            use_default_error_handler=False,
            timeout=5,
        )

    # ------------------------------------------------------------------
    # Processing endpoints
    # ------------------------------------------------------------------

    def create_processing(self, request: ProcessingCreateRequest, callback: Callable):
        self.http.post(
            url=f"{self.server}/processings",
            body=request.as_json().encode(),
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=10,
        )

    def list_processings(self, callback: Callable,
                         filter_: Optional[str] = None,
                         limit: int = 20, offset: int = 0,
                         project_id: Optional[str] = None):
        params = f"limit={limit}&offset={offset}"
        if filter_:
            params += f"&filter={filter_}"
        if project_id:
            params += f"&projectId={project_id}"
        self.http.get(
            url=f"{self.server}/processings/page?{params}",
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=10,
        )

    def get_processing(self, processing_id: str, callback: Callable):
        self.http.get(
            url=f"{self.server}/processings/{processing_id}",
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def get_processing_workflows(self, processing_id: str, callback: Callable):
        self.http.get(
            url=f"{self.server}/processings/{processing_id}/workflows",
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def get_processing_sessions(self, processing_id: str, callback: Callable):
        self.http.get(
            url=f"{self.server}/processings/{processing_id}/sessions",
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def get_processing_results(self, processing_id: str, callback: Callable):
        self.http.get(
            url=f"{self.server}/processings/{processing_id}/results",
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def delete_processing(self, processing_id: str, callback: Callable):
        self.http.delete(
            url=f"{self.server}/processings/{processing_id}",
            callback=callback,
            timeout=5,
        )

    def get_workflow(self, workflow_id: str, callback: Callable):
        self.http.get(
            url=f"{self.server}/workflows/{workflow_id}",
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    # ------------------------------------------------------------------
    # Prompt endpoints
    # ------------------------------------------------------------------

    def create_prompt(self, request: PromptCreateRequest, callback: Callable):
        self.http.post(
            url=f"{self.server}/prompts",
            body=request.as_json().encode(),
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def copy_prompt(self, prompt_id: str, request: PromptCopyRequest,
                    callback: Callable):
        self.http.post(
            url=f"{self.server}/prompts/{prompt_id}/copy",
            body=request.as_json().encode(),
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def list_prompts(self, callback: Callable,
                     filter_: Optional[str] = None,
                     limit: int = 20, offset: int = 0):
        params = f"limit={limit}&offset={offset}"
        if filter_:
            params += f"&filter={filter_}"
        self.http.get(
            url=f"{self.server}/prompts/page?{params}",
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=10,
        )

    def get_prompt(self, prompt_id: str, callback: Callable):
        self.http.get(
            url=f"{self.server}/prompts/{prompt_id}",
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def add_point_prompt(self, prompt_id: str, request: PointPromptRequest,
                         callback: Callable):
        self.http.post(
            url=f"{self.server}/prompts/{prompt_id}/point_prompts",
            body=request.as_json().encode(),
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=15,
        )

    def add_bbox_prompt(self, prompt_id: str, request: BboxPromptRequest,
                        callback: Callable):
        self.http.post(
            url=f"{self.server}/prompts/{prompt_id}/bbox_prompts",
            body=request.as_json().encode(),
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=15,
        )

    def unlink_point_prompt(self, prompt_id: str, point_prompt_id: str, callback: Callable):
        self.http.delete(
            url=f"{self.server}/prompts/{prompt_id}/point_prompts/{point_prompt_id}",
            callback=callback,
            timeout=5,
        )

    def unlink_bbox_prompt(self, prompt_id: str, bbox_prompt_id: str, callback: Callable):
        self.http.delete(
            url=f"{self.server}/prompts/{prompt_id}/bbox_prompts/{bbox_prompt_id}",
            callback=callback,
            timeout=5,
        )

    def delete_prompt(self, prompt_id, callback: Callable):
        self.http.delete(
            url=f"{self.server}/prompts/{prompt_id}",
            callback=callback,
            timeout=5
        )

    def update_prompt(self, prompt_id: str, request: PromptUpdateRequest,
                      callback: Callable, callback_kwargs: Optional[dict] = None):
        self.http.patch(
            url=f"{self.server}/prompts/{prompt_id}",
            body=request.as_json().encode(),
            headers={},
            callback=callback,
            callback_kwargs=callback_kwargs,
            use_default_error_handler=True,
            timeout=5,
        )

    # ------------------------------------------------------------------
    # Session endpoints
    # ------------------------------------------------------------------
    #
    # Sessions are not created via a dedicated POST /sessions endpoint;
    # they are created implicitly by POST /inference. POST /sessions/{id}/copy
    # was removed from the backend along with the workflow-visibility refactor.
    # GET /sessions/{id}/prompts was retired — the frozen prompt snapshot is
    # embedded in SessionResponse.

    def get_session(self, session_id: str, callback: Callable):
        self.http.get(
            url=f"{self.server}/sessions/{session_id}",
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def create_session_inference(self, session_id: str, request, callback: Callable):
        self.http.post(
            url=f"{self.server}/sessions/{session_id}/inferences",
            body=request.as_json().encode(),
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=10,
        )

    def delete_session(self, session_id, callback: Callable):
        self.http.delete(
            url=f"{self.server}/sessions/{session_id}",
            callback=callback,
            timeout=5
        )

    def update_session_name(self, session_id: str,
                            request: SessionNameUpdateRequest,
                            callback: Callable,
                            callback_kwargs: Optional[dict] = None):
        body=request.as_json().encode()
        self.http.patch(
            url=f"{self.server}/sessions/{session_id}",
            body=body,
            headers={},
            callback=callback,
            callback_kwargs=callback_kwargs,
            use_default_error_handler=True,
            timeout=5,
        )

    # ------------------------------------------------------------------
    # Inference endpoints
    # ------------------------------------------------------------------

    def create_inference(self, request: InferenceCreateRequest, callback: Callable):
        self.http.post(
            url=f"{self.server}/inference",
            body=request.as_json().encode(),
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=10,
        )

    def get_inference(self, inference_id: str, callback: Callable):
        self.http.get(
            url=f"{self.server}/inference/{inference_id}",
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    # ------------------------------------------------------------------
    # Spatial prompt raster previews
    # ------------------------------------------------------------------

    def download_spatial_prompt_raster(self, raster_url: str, callback: Callable,
                                       callback_kwargs: Optional[dict] = None):
        """Download a spatial-prompt GeoTIFF preview.

        `raster_url` is the value of `SpatialPromptResponse.raster_url`. The
        backend returns it relative to the `/sam-interactive` base — e.g.
        `/sessions/{sid}/spatial_prompts/{spid}/raster` when the response
        came from a session, or the prompt-rooted equivalent — so we
        concatenate it with `self.server` here. The URL prefix encodes the
        access path the backend uses to authorize the call (session-rights
        vs prompt-ownership), so we must not rewrite it client-side.

        Auth header is added by `Http` automatically (same OAuth/Basic
        scheme as every other SAM endpoint). The reply body is binary
        GeoTIFF bytes; the caller writes them to a temp file before
        loading as a raster layer.
        """
        self.http.get(
            url=f"{self.server}{raster_url}",
            headers={},
            callback=callback,
            callback_kwargs=callback_kwargs,
            use_default_error_handler=True,
            timeout=15,
        )

    # ------------------------------------------------------------------
    # Result endpoints
    # ------------------------------------------------------------------

    def get_result(self, session_id: str, callback: Callable,
                   callback_kwargs: Optional[dict] = None):
        self.http.get(
            url=f"{self.server}/result/{session_id}",
            headers={},
            callback=callback,
            callback_kwargs=callback_kwargs,
            use_default_error_handler=True,
            timeout=10,
        )
