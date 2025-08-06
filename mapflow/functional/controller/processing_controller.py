from PyQt5.QtCore import QObject, QTimer
from ..service.processing_service import ProcessingService
from ...dialogs.main_dialog import MainDialog


class ProcessingController(QObject):
    def __init__(self, dlg: MainDialog, processing_service: ProcessingService):
        self.dlg = dlg
        self.service = processing_service
        self.view = self.service.view

        self.dlg.startProcessing.clicked.connect(self.service.start_processing)
