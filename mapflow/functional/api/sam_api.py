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
    PointPromptRequest,
    BboxPromptRequest,
    SessionCreateRequest,
    InferenceCreateRequest,
)


class SamApi(QObject):

    def __init__(self, http: Http, server: str):
        super().__init__()
        self.server = f"{server}/sam-interactive"
        self.http = http


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
                         limit: int = 20, offset: int = 0):
        params = f"limit={limit}&offset={offset}"
        if filter_:
            params += f"&filter={filter_}"
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
            timeout=5,
        )

    def add_bbox_prompt(self, prompt_id: str, request: BboxPromptRequest,
                        callback: Callable):
        self.http.post(
            url=f"{self.server}/prompts/{prompt_id}/bbox_prompts",
            body=request.as_json().encode(),
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def delete_prompt(self, prompt_id, callback: Callable):
        self.http.delete(
            url=f"{self.server}/prompts/{prompt_id}",
            callback=callback,
            timeout=5
        )
    # ------------------------------------------------------------------
    # Session endpoints
    # ------------------------------------------------------------------

    def create_session(self, request: SessionCreateRequest, callback: Callable):
        self.http.post(
            url=f"{self.server}/sessions",
            body=request.as_json().encode(),
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def get_session(self, session_id: str, callback: Callable):
        self.http.get(
            url=f"{self.server}/sessions/{session_id}",
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def copy_session(self, session_id: str, callback: Callable):
        self.http.post(
            url=f"{self.server}/sessions/{session_id}/copy",
            body=b"",
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def delete_session(self, session_id, callback: Callable):
        self.http.delete(
            url=f"{self.server}/prompts/{session_id}",
            callback=callback,
            timeout=5
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
    # Result endpoints
    # ------------------------------------------------------------------

    def get_result(self, session_id: str, callback: Callable):
        self.http.get(
            url=f"{self.server}/result/{session_id}",
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=10,
        )
