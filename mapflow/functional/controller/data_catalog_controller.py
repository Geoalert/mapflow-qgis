from PyQt5.QtCore import QObject
from ..service.data_catalog import DataCatalogService
from ...dialogs.main_dialog import MainDialog

from PyQt5.QtWidgets import QApplication, QMessageBox


class DataCatalogController(QObject):
    def __init__(self, dlg: MainDialog, data_catalog_service: DataCatalogService):
        self.dlg = dlg
        self.service = data_catalog_service
        self.dlg.addImageButton.setEnabled(False)

        self.dlg.mosaicTable.cellClicked.connect(self.service.mosaic_clicked)
        self.dlg.imageTable.cellClicked.connect(self.service.image_clicked)
        self.dlg.addImageButton.clicked.connect(self.service.upload_image_to_mosaic)
        self.dlg.mosaicTable.selectionModel().selectionChanged.connect(self.service.check_mosaic_selection)
        
