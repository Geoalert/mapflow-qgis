import json
from typing import Callable, List, Optional, Union
from uuid import UUID

from PyQt5.QtCore import QObject
from ...http import Http, RequestMode
from ...schema.processing import (
    PostProcessingSchema,
    UpdateProcessingSchema,
    ProcessingsRequest,
)
from ...schema.template import (
    CreateProcessingTemplateSchema,
    UpdateProcessingTemplateSchema,
    RunTemplateProcessingSchema,
    UpdateAoiSchema,
    AddAoisSchema,
    DeleteAoisSchema,
    TemplateImagesRequestSchema,
)

class ProcessingApi(QObject):
    """
    API for processing requests:
    - get processings of a project
    - get single processing
    - request processing cost
    - create new processing
    - update existing processing
    - delete processing

    A read takes the request `mode` from its caller, which knows what triggered it; a request that
    changes server state is always `INTERACTIVE`, because it must never be sent twice
    (spec/005 § Request modes).
    """

    def __init__(self,
                 http: Http,
                 iface,
                 result_loader):
        super().__init__()
        self.http = http
        self.iface = iface
        self.result_loader = result_loader

    # project CRUD
    def create_processing(self, data: PostProcessingSchema, callback: Callable, error_handler: Callable) -> None:
        self.http.post(
            path="processings/v2",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
            body=data.as_json().encode(),
            timeout=30,
            mode=RequestMode.INTERACTIVE,
        )

    def update_processing(self, processing_id: Union[UUID, str],
                          processing: UpdateProcessingSchema,
                          callback: Callable,
                          error_handler: Optional[Callable] = None):
        self.http.put(path=f"processings/{processing_id}/v2",
                       body=processing.as_json().encode(),
                       headers={},
                       callback=callback,
                       use_default_error_handler=True,
                       timeout=5,
                       mode=RequestMode.INTERACTIVE)

    def delete_processing(self, processing_id: Union[UUID, str],
                          callback: Callable,
                          error_handler: Callable,
                          callback_kwargs: dict,
                          error_handler_kwargs: dict) -> None:
        self.http.delete(path=f"processings/{processing_id}",
                         callback = callback,
                         callback_kwargs = callback_kwargs,
                         use_default_error_handler=False,
                         error_handler = error_handler,
                         error_handler_kwargs = error_handler_kwargs,
                         timeout=5,
                         mode=RequestMode.INTERACTIVE)

    def get_processing(self, processing_id: Union[UUID, str], callback: Callable, *,
                       mode: RequestMode) -> None:
        self.http.get(path=f"processings/{processing_id}/v2",
                         callback=callback,
                         use_default_error_handler=True,
                         timeout=5,
                         mode=mode)

    def get_processing_aois(self,
                            processing_id: Union[UUID, str],
                            callback: Callable,
                            error_handler: Callable,
                            callback_kwargs: Optional[dict] = None,
                            error_handler_kwargs: Optional[dict] = None,
                            *,
                            mode: RequestMode) -> None:
        """A processing's own AOI geometries (a JSON list of AOI objects). Used to draw a
        'No AOI' template processing lazily on click — its geometry is absent from the
        template's aoiDetails, so it is fetched per processing."""
        self.http.get(path=f"processings/{processing_id}/aois",
                      callback=callback,
                      callback_kwargs=callback_kwargs or {},
                      error_handler=error_handler,
                      error_handler_kwargs=error_handler_kwargs or {},
                      use_default_error_handler=False,
                      timeout=30,
                      mode=mode)

    # ---- review and rating ----
    #
    # These three were the only processing endpoints called with a hand-built URL straight off
    # `Http`, which is why the code around them could not leave `mapflow.py`.

    def rate_processing(self,
                        processing_id: Union[UUID, str],
                        rating: int,
                        feedback: str,
                        callback: Callable,
                        callback_kwargs: Optional[dict] = None) -> None:
        self.http.put(path=f"processings/{processing_id}/rate",
                      body=json.dumps({"rating": rating, "feedback": feedback}).encode(),
                      callback=callback,
                      callback_kwargs=callback_kwargs or {},
                      mode=RequestMode.INTERACTIVE)

    def accept_processing(self, processing_id: Union[UUID, str], callback: Callable) -> None:
        """Approve a processing awaiting review."""
        self.http.put(path=f"processings/{processing_id}/acceptation", callback=callback,
                      mode=RequestMode.INTERACTIVE)

    def reject_processing(self,
                          processing_id: Union[UUID, str],
                          comment: str,
                          features,
                          callback: Callable) -> None:
        """Send a review back with a comment and the reviewer's corrections."""
        self.http.put(path=f"processings/{processing_id}/rejection",
                      body=json.dumps({"comment": comment, "features": features}).encode(),
                      callback=callback,
                      mode=RequestMode.INTERACTIVE)

    def get_processings(self, project_id: Union[UUID, str], request_body: ProcessingsRequest,
                        callback: Callable, *, mode: RequestMode, callback_kwargs: Optional[dict] = None):
        self.http.post(path=f"projects/{project_id}/processings/v2/page",
                       body=request_body.as_json().encode(),
                       callback=callback,
                       callback_kwargs=callback_kwargs or {},
                       use_default_error_handler=True,
                       timeout=5,
                       mode=mode)


    def get_cost(self, data: PostProcessingSchema, callback: Callable, error_handler: Callable, *,
                 mode: RequestMode):
        self.http.post(
            path="processing/cost/v2",
            callback=callback,
            body=data.as_json().encode(),
            use_default_error_handler=False,
            error_handler=error_handler,
            mode=mode,
        )

    def restart_processing(self,
                           processing_id: UUID,
                           callback: Callable,
                           error_handler: Callable):
        self.http.post(
            path=f"processings/{processing_id}/restart/v2",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
            mode=RequestMode.INTERACTIVE,
        )

    def create_template(self, data: CreateProcessingTemplateSchema, callback: Callable, error_handler: Callable):
        self.http.post(
            path="processings/template",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
            body=data.as_json().encode(),
            mode=RequestMode.INTERACTIVE,
        )

    def get_template(self, template_id: Union[UUID, str], callback: Callable, *, mode: RequestMode):
        self.http.get(
            path=f"processings/template/{template_id}",
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
            mode=mode,
        )

    def get_template_images(
        self,
        template_id: Union[UUID, str],
        callback: Callable,
        limit: int = 100,
        offset: int = 0,
        aoi_ids: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        *,
        mode: RequestMode,
    ):
        """The template's search results, paginated, optionally scoped to specific AOIs, and
        sorted server-side (``sort_by`` TemplateImagesSortBy token / ``sort_order`` ASC|DESC).

        Read-only: it does not modify the template. Date/cloud/intersection filtering is applied
        on the client (``Mapflow.apply_local_filter``), so no filter fields are sent."""
        data = TemplateImagesRequestSchema(limit=limit, offset=offset, aoiIds=aoi_ids,
                                           sortBy=sort_by, sortOrder=sort_order)
        self.http.post(
            path=f"processings/template/{template_id}/images",
            body=data.as_json().encode(),
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=20,
            mode=mode,
        )

    def update_template(self,
                        template_id: Union[UUID, str],
                        data: UpdateProcessingTemplateSchema,
                        callback: Callable,
                        error_handler: Optional[Callable] = None):
        self.http.put(
            path=f"processings/template/{template_id}",
            body=data.as_json().encode(),
            headers={},
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=error_handler is None,
            timeout=5,
            mode=RequestMode.INTERACTIVE,
        )

    def delete_template(self, template_id: Union[UUID, str], callback: Callable, error_handler: Callable):
        self.http.delete(
            path=f"processings/template/{template_id}",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
            timeout=5,
            mode=RequestMode.INTERACTIVE,
        )

    def run_template_processing(self,
                                template_id: Union[UUID, str],
                                data: RunTemplateProcessingSchema,
                                callback: Callable,
                                error_handler: Callable):
        self.http.post(
            path=f"processings/template/{template_id}/v2",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
            body=data.as_json().encode(),
            mode=RequestMode.INTERACTIVE,
        )

    def stop_template(self, template_id: Union[UUID, str], callback: Callable, error_handler: Callable):
        self.http.post(
            path=f"processings/template/{template_id}/pause",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
            mode=RequestMode.INTERACTIVE,
        )

    def resume_template(self, template_id: Union[UUID, str], callback: Callable, error_handler: Callable):
        self.http.post(
            path=f"processings/template/{template_id}/resume",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
            mode=RequestMode.INTERACTIVE,
        )

    def restart_template(self, template_id: Union[UUID, str], callback: Callable, error_handler: Callable):
        self.http.post(
            path=f"processings/template/{template_id}/restart",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
            mode=RequestMode.INTERACTIVE,
        )

    def get_template_processings(self, template_id: Union[UUID, str], callback: Callable, *,
                                 mode: RequestMode):
        self.http.get(
            path=f"processings/template/{template_id}/processings",
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
            mode=mode,
        )

    # ---- Template AOI management ----
    def update_aoi(self,
                   template_id: Union[UUID, str],
                   aoi_id: Union[UUID, str],
                   data: UpdateAoiSchema,
                   callback: Callable,
                   error_handler: Optional[Callable] = None):
        # NB: the backend serves AOI update over POST (not PUT) — see
        # ProcessingResource.updateAoiEndpoint (`.post`). PUT returns 404.
        self.http.post(
            path=f"processings/template/{template_id}/aoi/{aoi_id}",
            body=data.as_json().encode(),
            headers={},
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=error_handler is None,
            timeout=5,
            mode=RequestMode.INTERACTIVE,
        )

    def add_aois(self,
                 template_id: Union[UUID, str],
                 data: AddAoisSchema,
                 callback: Callable,
                 error_handler: Optional[Callable] = None):
        self.http.post(
            path=f"processings/template/{template_id}/aoi",
            body=data.as_json().encode(),
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=error_handler is None,
            timeout=5,
            mode=RequestMode.INTERACTIVE,
        )

    def delete_aois(self,
                    template_id: Union[UUID, str],
                    data: DeleteAoisSchema,
                    callback: Callable,
                    error_handler: Optional[Callable] = None):
        self.http.delete(
            path=f"processings/template/{template_id}/aoi",
            body=data.as_json().encode(),
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=error_handler is None,
            timeout=5,
            mode=RequestMode.INTERACTIVE,
        )

    def mark_template_image_seen(self,
                                 template_id: Union[UUID, str],
                                 image_id: str,
                                 callback: Callable,
                                 error_handler: Callable):
        self.http.post(
            path=f"processings/template/{template_id}/image/{image_id}/seen",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
            mode=RequestMode.INTERACTIVE,
        )

    def mark_all_template_images_seen(self,
                                      template_id: Union[UUID, str],
                                      callback: Callable,
                                      error_handler: Callable):
        """Mark every image of the template as seen in a single request."""
        self.http.put(
            path=f"processings/template/{template_id}/image/seenAll",
            body=b"",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
            mode=RequestMode.INTERACTIVE,
        )

    def get_templates_by_project(self, project_id: Union[UUID, str], callback: Callable, *,
                                 mode: RequestMode):
        self.http.get(
            path=f"processings/template/project/{project_id}",
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
            mode=mode,
        )
