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
        self.dlg.previewCatalogButton.setEnabled(False)
        self.dlg.editCatalogButton.setEnabled(False)
        self.dlg.deleteCatalogButton.setEnabled(False)
        self.dlg.addImageButton.setEnabled(False)

        # Mosaic
        self.dlg.mosaicTable.cellClicked.connect(self.service.mosaic_clicked)
        self.dlg.addMosaicButton.clicked.connect(self.service.create_mosaic)
        self.dlg.mosaicTable.selectionModel().selectionChanged.connect(self.service.check_catalog_selection)

        # Image
        self.dlg.imageTable.cellClicked.connect(self.service.image_clicked)
        self.dlg.addImageButton.setMenu(self.view.upload_image_menu)
        self.view.upload_from_file.triggered.connect(self.service.upload_images_to_mosaic)
        self.view.choose_raster_layer.triggered.connect(self.service.choose_raster_layers)
        self.dlg.imageTable.selectionModel().selectionChanged.connect(self.service.check_catalog_selection)

        # Mosaic or image (depending on selection)
        self.dlg.previewCatalogButton.clicked.connect(self.service.preview_mosaic_or_image)
        self.dlg.editCatalogButton.clicked.connect(self.service.update_or_show_info)
        self.dlg.deleteCatalogButton.clicked.connect(self.service.delete_mosaic_or_image)


        self.service.mosaicsUpdated.connect(self.service.get_user_limit)
