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
        self.dlg.imagePreviewButton.clicked.connect(self.service.get_image_preview_l)
        self.dlg.imageInfoButton.clicked.connect(self.service.image_info)
        self.dlg.tabWidget.tabBarClicked.connect(self.service.get_user_limit)
        self.dlg.imageTable.selectionModel().selectionChanged.connect(self.service.check_image_selection)
        self.dlg.addImageButton.clicked.connect(self.service.upload_images_to_mosaic)
        self.dlg.deleteImageButton.clicked.connect(self.service.delete_image)
