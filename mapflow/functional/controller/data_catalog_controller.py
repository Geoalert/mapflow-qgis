from PyQt5.QtCore import QObject, QTimer
from ..service.data_catalog import DataCatalogService
from ...dialogs.main_dialog import MainDialog


class DataCatalogController(QObject):
    def __init__(self, dlg: MainDialog, data_catalog_service: DataCatalogService):
        self.dlg = dlg
        self.service = data_catalog_service
        self.view = self.service.view

        # At first, when mosaic and image are not selected, make buttons unavailable or hidden
        self.dlg.deleteCatalogButton.setEnabled(False)
        self.dlg.seeMosaicsButton.setEnabled(False)
        self.dlg.seeImagesButton.setEnabled(False)

        # Mosaic
        self.dlg.editMosaicButton.clicked.connect(self.service.update_mosaic)
        self.dlg.previewMosaicButton.clicked.connect(self.service.mosaic_preview)
        self.dlg.mosaicTable.selectionModel().selectionChanged.connect(self.service.check_mosaic_selection)
        self.dlg.showImagesButton.clicked.connect(self.view.show_images_table)
        self.dlg.seeImagesButton.clicked.connect(self.view.show_images_table)
        self.dlg.mosaicTable.cellDoubleClicked.connect(self.view.show_images_table)
        self.dlg.nextImageButton.clicked.connect(self.service.get_next_preview)
        self.dlg.previousImageButton.clicked.connect(self.service.get_previous_preview)

        # Image
        self.dlg.addImageButton.setMenu(self.view.upload_image_menu)
        self.view.upload_from_file.triggered.connect(self.service.upload_images_to_mosaic)
        self.view.choose_raster_layer.triggered.connect(self.service.choose_raster_layers)
        self.dlg.imageInfoButton.clicked.connect(self.service.image_info)
        self.dlg.previewImageButton.clicked.connect(self.service.get_image_preview_l)
        self.dlg.imageTable.selectionModel().selectionChanged.connect(self.service.check_image_selection)
        self.dlg.seeMosaicsButton.clicked.connect(self.service.switch_to_mosaics_table)

        # Mosaic or image (depending on selection)
        self.dlg.addCatalogButton.clicked.connect(self.service.add_mosaic_or_image)
        self.dlg.deleteCatalogButton.clicked.connect(self.service.delete_mosaic_or_image)
        self.dlg.sortCatalogCombo.activated.connect(self.view.sort_catalog)
        self.dlg.refreshCatalogButton.clicked.connect(self.service.refresh_catalog)
        self.dlg.filterCatalog.textChanged.connect(self.view.filter_catalog_table)

        # Show free and taken space if limit is not None
        self.service.mosaicsUpdated.connect(self.service.get_user_limit)

        self.dlg.myImageryDocsButton.clicked.connect(self.service.open_imagery_docs)
