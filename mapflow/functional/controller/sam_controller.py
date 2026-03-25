"""SAM Interactive controller — signal/slot wiring for SAM tab.

Thin wiring layer: connects UI signals to SamService methods.
No business logic here.
"""
from PyQt5.QtCore import QObject

from ..service.sam import SamService
from ...dialogs.main_dialog import MainDialog


class SamController(QObject):
    def __init__(self, dlg: MainDialog, sam_service: SamService):
        super().__init__()
        self.dlg = dlg
        self.service = sam_service
        self.view = self.service.view

        # Processings
        self.dlg.samRefreshProcessings.clicked.connect(self._refresh_processings)
        self.dlg.samProcessingsTable.selectionModel().selectionChanged.connect(
            self._on_processing_selected)
        self.dlg.samViewWorkflows.clicked.connect(self._view_workflows)

    def _refresh_processings(self):
        self.service.list_processings()

    def _on_processing_selected(self):
        processing_id = self.view.selected_processing_id()
        if processing_id:
            self.service.get_processing(processing_id)

    def _view_workflows(self):
        processing_id = self.view.selected_processing_id()
        if processing_id:
            self.service.list_workflows(processing_id)
