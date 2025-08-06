from typing import Callable
from PyQt5.QtCore import QObject, pyqtSignal, QFile, QIODevice
from ...http import Http
from ...dialogs.main_dialog import MainDialog
from ...schema.processing import PostProcessingSchema

class ProcessingApi(QObject):
    """

    """

    def __init__(self,
                 http: Http,
                 server: str,
                 dlg: MainDialog,
                 iface,
                 result_loader,
                 plugin_version):
        super().__init__()
        self.server = server
        self.http = http
        self.iface = iface
        self.dlg = dlg
        self.result_loader = result_loader
        self.plugin_version = plugin_version

    # project CRUD
    def create_processing(self, data: PostProcessingSchema, callback: Callable, error_handler: Callable):
        self.http.post(url=f"{self.server}/processing",
                       body=data.as_json().encode(),
                       callback=callback,
                       error_handler=error_handler)
