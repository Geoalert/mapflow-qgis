from PyQt5.QtCore import QObject, pyqtSignal, Qt
from ...dialogs.main_dialog import MainDialog
from ...http import Http
from ..view.project_view import ProcessingView
from ..api.processing_api import ProcessingApi

class ProcessingService(QObject):
    """
    A service to store & query the mapflow processings.
    """

    def __init__(self,
                 http: Http,
                 server: str,
                 dlg: MainDialog,
                 iface,
                 result_loader,
                 plugin_version,
                 temp_dir):
        super().__init__()
        self.http = http
        self.server = server
        self.iface = iface
        self.result_loader = result_loader
        self.plugin_version = plugin_version
        self.temp_dir = temp_dir
        self.view = ProcessingView(dlg=dlg)
        self.api = ProcessingApi(http=http, server=server, dlg=dlg, iface=iface, result_loader=self.result_loader, plugin_version=self.plugin_version)

    def validate_params(self, ui_start_params):
        pass

    def start_processing(self):
        ui_start_params = self.view.read_processing_start_params()
        # maybe some logic behind validation?
        self.validate_params(ui_start_params)
        provider = self.get_data_provider(ui_start_params)
        source_params = provider.source_params()
        # gather all the other logic
        self.http.post()

    def refresh_processings(self):
        pass
