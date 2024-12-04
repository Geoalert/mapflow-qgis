from PyQt5.QtCore import QObject, QTimer
from ..service.data_catalog import DataCatalogService
from ..view.data_catalog_view import DataCatalogView
from ...dialogs.main_dialog import MainDialog


class DataCatalogController(QObject):
    def __init__(self, dlg: MainDialog, data_catalog_service: DataCatalogService):
        self.dlg = dlg
        self.service = data_catalog_service
        self.view = DataCatalogView(self.dlg)

        # At first, when mosaic and image are not selected, make buttons unavailable
        self.dlg.previewMosaicButton.setEnabled(False)
        self.dlg.editMosaicButton.setEnabled(False)
        self.dlg.deleteMosaicButton.setEnabled(False)
        self.dlg.addImageButton.setEnabled(False)
        self.dlg.deleteImageButton.setEnabled(False)
        self.dlg.imagePreviewButton.setEnabled(False)
        self.dlg.imageInfoButton.setEnabled(False)

        # Mosaic
        self.dlg.mosaicTable.cellClicked.connect(self.service.mosaic_clicked)
        self.dlg.previewMosaicButton.clicked.connect(self.service.mosaic_preview)
        self.dlg.addMosaicButton.clicked.connect(self.service.create_mosaic)
        self.dlg.editMosaicButton.clicked.connect(self.service.update_mosaic)
        self.dlg.deleteMosaicButton.clicked.connect(self.service.delete_mosaic)
        self.dlg.mosaicTable.selectionModel().selectionChanged.connect(self.view.check_mosaic_selection)

        # Image
        self.dlg.imageTable.cellClicked.connect(self.service.image_clicked)
        self.dlg.imagePreviewButton.clicked.connect(self.service.get_image_preview_l)
        self.dlg.addImageButton.setMenu(self.view.upload_image_menu)
        self.view.upload_from_file.triggered.connect(self.service.upload_images_to_mosaic)
        self.view.choose_raster_layer.triggered.connect(self.service.choose_raster_layers)
        self.dlg.deleteImageButton.clicked.connect(self.service.delete_image)
        self.dlg.imageInfoButton.clicked.connect(self.service.image_info)
        self.dlg.imageTable.selectionModel().selectionChanged.connect(self.view.check_image_selection)

        self.service.mosaicsUpdated.connect(self.service.get_user_limit)
