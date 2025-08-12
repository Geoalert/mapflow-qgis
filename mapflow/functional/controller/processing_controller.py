from PyQt5.QtCore import QObject, QTimer
from ..service.processing_service import ProcessingService
from ..service.project_service import ProjectService
from ...dialogs.main_dialog import MainDialog


class ProcessingController(QObject):
    def __init__(self, dlg: MainDialog, processing_service: ProcessingService, project_service: ProjectService):
        super().__init__()
        self.dlg = dlg
        self.processing_service = processing_service
        self.project_service = project_service
        self.view = self.processing_service.view

        # Connect UI actions
        self.dlg.startProcessing.clicked.connect(self.processing_service.start_processing)
        self.processing_service.processing_fetch_timer.timeout.connect(self.processing_service.get_processings)
        
        # Connect project service signals to processing service slots
        self.project_service.projectChanged.connect(self.processing_service.set_current_project)
