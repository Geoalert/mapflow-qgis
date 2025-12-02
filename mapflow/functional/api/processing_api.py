from typing import Callable, Union
from uuid import UUID

from PyQt5.QtCore import QObject, pyqtSignal, QFile, QIODevice
from ...http import Http
from ...dialogs.main_dialog import MainDialog
from ...schema.processing import PostProcessingSchema, UpdateProcessingSchema

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

    def update_processing(self, processing_id: Union[UUID, str], processing: UpdateProcessingSchema, callback: Callable, error_handler: Callable):
        self.http.put(path=f"processings/{processing_id}",
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
        self.http.delete(path="processings/{processing_id}",
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

    def get_processings(self, project_id: Union[UUID, str], callback: Callable):
        self.http.get(path=f"projects/{project_id}/processings/v2",
                         callback=callback,
                         use_default_error_handler=False,
                         timeout=5)


    def get_cost(self, data: PostProcessingSchema, callback: Callable, error_handler: Callable):
        self.http.post(
            path="processing/cost/v2",
            callback=callback,
            body=data.as_json().encode(),
            use_default_error_handler=False,
            error_handler=callback
        )
