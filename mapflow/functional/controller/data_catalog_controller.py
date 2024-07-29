from PyQt5.QtCore import QObject
from ..service.data_catalog import DataCatalogService
from ...dialogs.main_dialog import MainDialog


class DataCatalogController(QObject):
    def __init__(self, dlg: MainDialog, data_catalog_service: DataCatalogService):
        self.dlg = dlg
        self.service = data_catalog_service

        self.dlg.mosaicTable.cellClicked.connect(self.service.mosaic_clicked)
        self.dlg.imageTable.cellClicked.connect(self.service.image_clicked)
        self.dlg.previewMosaicButton.clicked.connect(self.service.mosaic_preview)
        self.dlg.imageInfoButton.clicked.connect(self.service.image_info)