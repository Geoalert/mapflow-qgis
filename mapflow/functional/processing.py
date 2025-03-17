from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QNetworkReply

from ..schema.processing import UpdateProcessingSchema


class ProcessingService(QObject):
    processingUpdated = pyqtSignal()

    def __init__(self, http, server):
        super().__init__()
        self.http = http
        self.server = server
        self.projects = []

    def get_processings(self, project_id, callback):
        self.http.get(
                url=f'{self.server}/projects/{project_id}/processings',
                callback=callback,
                use_default_error_handler=False # ignore errors to prevent repetitive alerts
                )

    def update_processing(self, processing_id, processing: UpdateProcessingSchema):
        self.http.put(url=f"{self.server}/processings/{processing_id}",
                       body=processing.as_json().encode(),
                       headers={},
                       callback=self.update_processing_callback,
                       use_default_error_handler=True,
                       timeout=5)

    def update_processing_callback(self, response: QNetworkReply):
        self.processingUpdated.emit()
