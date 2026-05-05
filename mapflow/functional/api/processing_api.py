import json
from typing import Callable, List, Optional, Union
from uuid import UUID

from PyQt5.QtCore import QObject, pyqtSignal, QFile, QIODevice
from ...http import Http
from ...dialogs.main_dialog import MainDialog
from ...schema.processing import (
    PostProcessingSchema,
    UpdateProcessingSchema,
    ProcessingsRequest,
    CreateProcessingTemplateSchema,
    UpdateProcessingTemplateSchema,
    RunTemplateProcessingSchema,
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
    """

    def __init__(self,
                 http: Http,
                 dlg: MainDialog,
                 iface,
                 result_loader):
        super().__init__()
        self.http = http
        self.iface = iface
        self.dlg = dlg
        self.result_loader = result_loader

    # project CRUD
    def create_processing(self, data: PostProcessingSchema, callback: Callable, error_handler: Callable) -> None:
        self.http.post(
            path="processings/v2",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
            body=data.as_json().encode()
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
                       timeout=5)

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
                         timeout=5)

    def get_processing(self, processing_id: Union[UUID, str], callback: Callable) -> None:
        self.http.get(path=f"processings/{processing_id}/v2",
                         callback=callback,
                         use_default_error_handler=True,
                         timeout=5)

    def get_processings(self, project_id: Union[UUID, str], request_body: ProcessingsRequest, callback: Callable):
        self.http.post(path=f"projects/{project_id}/processings/v2/page",
                       body=request_body.as_json().encode(),
                       callback=callback,
                       use_default_error_handler=False,
                       timeout=5)


    def get_cost(self, data: PostProcessingSchema, callback: Callable, error_handler: Callable):
        self.http.post(
            path="processing/cost/v2",
            callback=callback,
            body=data.as_json().encode(),
            use_default_error_handler=False,
            error_handler=error_handler
        )
    
    def restart_processing(self,
                           processing_id: UUID,
                           callback: Callable,
                           error_handler: Callable):
        self.http.post(
            path=f"processings/{processing_id}/restart/v2",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False
        )

    def create_template(self, data: CreateProcessingTemplateSchema, callback: Callable, error_handler: Callable):
        self.http.post(
            path="processings/template",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
            body=data.as_json().encode(),
        )

    def get_templates(self, callback: Callable):
        self.http.get(
            path="processings/template",
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def get_template(self, template_id: Union[UUID, str], callback: Callable):
        self.http.get(
            path=f"processings/template/{template_id}",
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def post_template(
        self,
        template_id: Union[UUID, str],
        callback: Callable,
        limit: int = 100,
        offset: int = 0,
        aoi_ids: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ):
        body: dict = {"limit": limit, "offset": offset}
        if aoi_ids is not None:
            body["aoiIds"] = aoi_ids
        if sort_by is not None:
            body["sortBy"] = sort_by
        if sort_order is not None:
            body["sortOrder"] = sort_order
        self.http.post(
            path=f"processings/template/{template_id}/run",
            body=json.dumps(body).encode(),
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
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
    ):
        body: dict = {"limit": limit, "offset": offset}
        if aoi_ids is not None:
            body["aoiIds"] = aoi_ids
        if sort_by is not None:
            body["sortBy"] = sort_by
        if sort_order is not None:
            body["sortOrder"] = sort_order
        self.http.post(
            path=f"processings/template/{template_id}/images",
            body=json.dumps(body).encode(),
            headers={},
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
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
        )

    def delete_template(self, template_id: Union[UUID, str], callback: Callable, error_handler: Callable):
        self.http.delete(
            path=f"processings/template/{template_id}",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
            timeout=5,
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
        )

    def stop_template(self, template_id: Union[UUID, str], callback: Callable, error_handler: Callable):
        self.http.post(
            path=f"processings/template/{template_id}/stop",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
        )

    def resume_template(self, template_id: Union[UUID, str], callback: Callable, error_handler: Callable):
        self.http.post(
            path=f"processings/template/{template_id}/resume",
            callback=callback,
            error_handler=error_handler,
            use_default_error_handler=False,
        )

    def get_template_processings(self, template_id: Union[UUID, str], callback: Callable):
        self.http.get(
            path=f"processings/template/{template_id}/processings",
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
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
        )

    def get_templates_by_user(self, user_id: Union[UUID, str], callback: Callable):
        self.http.get(
            path=f"processings/template/user/{user_id}",
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )

    def get_templates_by_project(self, project_id: Union[UUID, str], callback: Callable):
        self.http.get(
            path=f"processings/template/project/{project_id}",
            callback=callback,
            use_default_error_handler=True,
            timeout=5,
        )
