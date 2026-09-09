from pathlib import Path

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QMessageBox, QApplication, QFileDialog

from ..service.data_catalog import DataCatalogService
from ..service.preview_service import PreviewService
from ...error_guard import guarded_connect
from ...infra.alert_service import alert
from ..view.data_catalog_view import DataCatalogView
from ...dialogs.main_dialog import MainDialog
from ...dialogs.mosaic_dialog import CreateMosaicDialog, UpdateMosaicDialog
from ...dialogs.image_dialog import RenameImageDialog
from ...dialogs.upload_raster_layer_dialog import UploadRasterLayersDialog
from ...dialogs.error_message_widget import ErrorMessageWidget
from ...functional.app_context import AppContext
from ...model.provider import MyImageryProvider


class DataCatalogController(QObject):
    """The My Imagery panel. `DataCatalogService` does the requests and holds the mosaics/images;
    this controller owns every dialog, reads the table selections and pushes them to the service,
    and renders what the service announces. A service touches no widget
    (`spec/007_architecture.md` § Services)."""

    def __init__(self,
                 dlg: MainDialog,
                 data_catalog_service: DataCatalogService,
                 preview_service: PreviewService,
                 view: DataCatalogView,
                 app_context: AppContext):
        super().__init__()
        self.dlg = dlg
        self.service = data_catalog_service
        # Which mosaic/image is selected is the catalog's; putting the raster on the map is
        # PreviewService's, so the two preview buttons wire across.
        self.preview_service = preview_service
        self.view = view
        self.app_context = app_context

        # At first, when mosaic and image are not selected, make buttons unavailable or hidden
        self.dlg.deleteCatalogButton.setEnabled(False)
        self.dlg.seeMosaicsButton.setEnabled(False)
        self.dlg.seeImagesButton.setEnabled(False)

        self._connect_buttons()
        self._connect_service_signals()

    # ---------- wiring ----------

    def _connect_buttons(self):
        # Mosaic
        guarded_connect(self.dlg.editMosaicButton.clicked, self.update_mosaic,
                        "editing a mosaic", self.app_context)
        guarded_connect(self.dlg.previewMosaicButton.clicked,
                        self.preview_service.preview_my_imagery_mosaic,
                        "previewing a mosaic", self.app_context)
        # itemSelectionChanged (not selectionModel().selectionChanged), so this runs in the same
        # signal whose first slot — connected in mapflow.py above every reader — pushes the
        # selected ids to the service. The dedup/resolve below then reads fresh pushed state.
        guarded_connect(self.dlg.mosaicTable.itemSelectionChanged, self.check_mosaic_selection,
                        "selecting a mosaic", self.app_context)
        guarded_connect(self.dlg.showImagesButton.clicked, self.show_images_table,
                        "showing the images table", self.app_context)
        guarded_connect(self.dlg.seeImagesButton.clicked, self.show_images_table,
                        "showing the images table", self.app_context)
        guarded_connect(self.dlg.mosaicTable.cellDoubleClicked, self.show_images_table,
                        "opening a mosaic", self.app_context)
        guarded_connect(self.dlg.nextImageButton.clicked, self.service.get_next_preview,
                        "the next image preview", self.app_context)
        guarded_connect(self.dlg.previousImageButton.clicked, self.service.get_previous_preview,
                        "the previous image preview", self.app_context)

        # Image
        self.dlg.addImageButton.setMenu(self.view.upload_image_menu)
        guarded_connect(self.view.upload_from_file.triggered, self.upload_images_to_mosaic,
                        "uploading images", self.app_context)
        guarded_connect(self.view.choose_raster_layer.triggered, self.choose_raster_layers,
                        "choosing raster layers", self.app_context)
        guarded_connect(self.dlg.imageInfoButton.clicked, self.image_info,
                        "showing image info", self.app_context)
        guarded_connect(self.dlg.renameImageButton.clicked, self.show_rename_image_dialog,
                        "renaming an image", self.app_context)
        guarded_connect(self.dlg.previewImageButton.clicked,
                        self.preview_service.preview_my_imagery_image,
                        "previewing an image", self.app_context)
        guarded_connect(self.dlg.downloadImageButton.clicked, self.service.download_image,
                        "downloading an image", self.app_context)
        guarded_connect(self.dlg.imageTable.itemSelectionChanged, self.check_image_selection,
                        "selecting an image", self.app_context)
        guarded_connect(self.dlg.seeMosaicsButton.clicked, self.switch_to_mosaics_table,
                        "showing the mosaics table", self.app_context)

        # Mosaic or image (depending on selection)
        guarded_connect(self.dlg.addCatalogButton.clicked, self.add_mosaic_or_image,
                        "adding to the catalog", self.app_context)
        guarded_connect(self.dlg.deleteCatalogButton.clicked, self.delete_mosaic_or_image,
                        "deleting from the catalog", self.app_context)
        guarded_connect(self.dlg.sortCatalogCombo.activated, self.view.sort_catalog,
                        "sorting the catalog", self.app_context)
        guarded_connect(self.dlg.refreshCatalogButton.clicked, self.service.refresh_catalog,
                        "refreshing the catalog", self.app_context)
        guarded_connect(self.dlg.filterCatalog.textChanged, self.view.filter_catalog_table,
                        "filtering the catalog", self.app_context)

        # Show free and taken space if limit is not None
        self.service.mosaicsUpdated.connect(self.service.get_user_limit)

        guarded_connect(self.dlg.myImageryDocsButton.clicked, self.service.open_imagery_docs,
                        "opening the imagery docs", self.app_context)

    def _connect_service_signals(self):
        """What the service announces, rendered here."""
        s = self.service
        s.mosaicsChanged.connect(self._render_mosaics)
        s.mosaicReselected.connect(self.view.display_mosaics_and_reselect)
        s.imagesChanged.connect(self.view.display_images)
        s.mosaicInfoChanged.connect(self.view.display_mosaic_info)
        s.previewChanged.connect(self.view.show_preview_s)
        s.previewNavChanged.connect(self.view.enable_mosaic_images_preview)
        s.imageNumberChanged.connect(self.view.display_image_number)
        s.imageRenamedInTable.connect(self.view.rename_image_in_table)
        s.storageChanged.connect(self.view.show_storage)
        s.mosaicSelectionCleared.connect(self.view.clear_mosaic_selection)
        s.imageSelectionCleared.connect(self.view.clear_image_selection)
        s.sourceMosaicSelected.connect(self.view.select_mosaic_cell)
        s.sourceImageReady.connect(self._render_source_image)
        s.mySourceShown.connect(self.view.show_my_imagery_source)
        s.catalogResetToMosaics.connect(self.view.reset_to_mosaics_table)
        s.imageSourceError.connect(self._show_source_error)
        s.downloadUrlReady.connect(self._prompt_save_download)
        s.dialogShouldRaise.connect(self.view.raise_dialog)
        s.switchToMyImageryRequested.connect(self._switch_to_my_imagery)

    def _render_mosaics(self, mosaics):
        self.view.display_mosaics(mosaics)
        self.view.clear_mosaic_selection()

    def _render_source_image(self, image):
        self.view.select_mosaic_cell(image.mosaic_id)
        self.view.bind_source_image(image.id)

    def _show_source_error(self, summary: str):
        ErrorMessageWidget(parent=QApplication.activeWindow(), text=summary).show()

    def _switch_to_my_imagery(self, providers):
        """Point the data-source combo at My Imagery if it is not there already."""
        current = providers[self.dlg.providerIndex()]
        if isinstance(current, MyImageryProvider):
            return
        for index, provider in enumerate(providers):
            if isinstance(provider, MyImageryProvider):
                self.dlg.sourceCombo.setCurrentIndex(index)
                return

    # ---------- which catalog table is showing ----------

    def show_images_table(self, *args):
        self.view.show_images_table()
        self.service.set_mosaic_table_visible(False)

    def switch_to_mosaics_table(self, *args):
        mosaic = self.service.selected_mosaic()
        self.service.set_mosaic_table_visible(True)
        self.view.show_mosaics_table(mosaic.name if mosaic else None)
        if mosaic:
            self.view.display_mosaic_info(mosaic, self.service.images)
            self.service.get_mosaic_images(mosaic.id)

    # ---------- selection ----------

    def check_mosaic_selection(self, *args):
        mosaic = self.service.selected_mosaic()
        if mosaic:
            self.on_mosaic_selection(mosaic)
        else:
            self.view.clear_mosaic_info()

    def on_mosaic_selection(self, mosaic):
        # Clear previous images details
        self.view.clear_image_table()
        # Selecting a mosaic clears the image selection, so drop the cached image too — otherwise
        # a stale selected_image would still feed imageIds into the next processing (a mosaic run
        # would wrongly reuse the previously processed image).
        self.app_context.selected_image = None
        # Don't send GET requests if the first selected mosaic didn't change
        selected = self.dlg.mosaicTable.selectedIndexes()
        if len(selected) > 1 and self.dlg.selected_mosaic_cell == selected[0]:
            pass
        else:
            self.dlg.selected_mosaic_cell = self.dlg.mosaicTable.selectedIndexes()[0]
            self.service.get_mosaic_images(mosaic.id)
        self.view.add_mosaic_cell_buttons()
        self.view.show_mosaic_info(mosaic.name)

    def check_image_selection(self, *args):
        image = self.service.selected_image()
        if image:
            self.on_image_selection(image)
        else:
            # Keep the cached image in sync with the table: deselecting must not leave a stale
            # selected_image that would be picked up when building processing params.
            self.app_context.selected_image = None
            self.view.clear_image_info()

    def on_image_selection(self, image):
        selected_images = self.dlg.imageTable.selectedIndexes()
        selected_mosaics = self.dlg.mosaicTable.selectedIndexes()
        if not selected_mosaics or (len(selected_images) > 1 and self.dlg.selected_image_cell == selected_images[0]):
            pass
        else:
            self.dlg.selected_mosaic_cell = self.dlg.mosaicTable.selectedIndexes()[0]
            self.service.get_image_preview_s(image)
        self.view.show_image_info(image)
        self.view.add_image_cell_buttons()
        self.app_context.selected_image = image

    # ---------- add / delete dispatch ----------

    def add_mosaic_or_image(self, *args):
        if self.view.mosaic_table_visible:
            self.create_mosaic()
        else:
            self.upload_images_to_mosaic()

    def delete_mosaic_or_image(self, *args):
        if self.service.selected_image():
            self.confirm_image_deletion()
        elif self.service.selected_mosaic():
            self.confirm_mosaic_deletion()

    # ---------- mosaic dialogs ----------

    def create_mosaic(self, *args):
        dialog = CreateMosaicDialog(self.dlg)
        guarded_connect(dialog.accepted, lambda: self._create_mosaic_from_options(dialog),
                        "creating a mosaic", self.app_context)
        dialog.setup()
        dialog.deleteLater()

    def _create_mosaic_from_options(self, mosaic_dialog: CreateMosaicDialog):
        mosaic = mosaic_dialog.mosaic()
        if mosaic_dialog.createMosaicCombo.currentIndex() == 0:  # empty mosaic
            self.service.create_mosaic(mosaic)
            return
        if mosaic_dialog.createMosaicCombo.currentIndex() == 1:  # mosaic from files
            image_paths = QFileDialog.getOpenFileNames(QApplication.activeWindow(),
                                                       self.tr("Choose image to upload"),
                                                       filter='TIF files (*.tif *.tiff)')[0]
        else:  # mosaic from layers
            image_paths = self._choose_raster_layer_paths()
        if image_paths:
            self.service.create_mosaic_from_images(mosaic, image_paths)

    def update_mosaic(self, *args):
        mosaic = self.service.selected_mosaic()
        if not mosaic:
            return
        dialog = UpdateMosaicDialog(self.dlg)
        guarded_connect(dialog.accepted,
                        lambda: self.service.update_mosaic(mosaic.id, dialog.mosaic()),
                        "saving a mosaic edit", self.app_context)
        dialog.setup(mosaic)
        dialog.deleteLater()

    def confirm_mosaic_deletion(self):
        mosaics = self.service.selected_mosaics()
        if not mosaics:
            return
        names = [mosaic.name for mosaic in mosaics]
        if len(names) == 1:
            message = self.tr("<center>Delete imagery collection <b>'{name}'</b>?").format(name=names[0])
        elif len(names) <= 3:
            message = self.tr("<center>Delete following imagery collections:<br><b>'{names}'</b>?"
                              ).format(names="', <br>'".join(names))
        else:
            message = self.tr("<center>Delete <b>{len}</b> imagery collections?").format(len=len(names))
        if self._confirm(message):
            self.service.delete_mosaics(response=None, mosaics=mosaics, deleted=[], failed=[])

    # ---------- image dialogs ----------

    def upload_images_to_mosaic(self, *args):
        if not self.service.selected_mosaic():
            alert(self.tr("Please, select existing imagery collection"))
            return
        image_paths = QFileDialog.getOpenFileNames(QApplication.activeWindow(),
                                                   self.tr("Choose images to upload"),
                                                   filter='TIF files (*.tif *.tiff)')[0]
        if image_paths:
            self.service.upload_images_to_mosaic(image_paths)

    def choose_raster_layers(self, *args):
        paths = self._choose_raster_layer_paths()
        if paths:
            self.service.upload_raster_layers_to_mosaic(paths)

    def _choose_raster_layer_paths(self):
        """Open the raster-layer picker and return the chosen files' paths (empty if cancelled)."""
        dialog = UploadRasterLayersDialog(self.dlg)
        paths = []

        def collect():
            for item in dialog.listWidget.selectedItems():
                paths.append(item.data(Qt.UserRole))

        guarded_connect(dialog.accepted, collect,
                        "choosing raster layers to upload", self.app_context)
        layers = [layer for layer in self.app_context.project.mapLayers().values()
                  if Path(layer.source()).suffix.lower() in ['.tif', '.tiff']]
        dialog.setup(layers)
        dialog.deleteLater()
        return paths

    def show_rename_image_dialog(self, *args):
        image = self.service.selected_image()
        if not image:
            return
        dialog = RenameImageDialog(self.dlg)
        guarded_connect(dialog.accepted,
                        lambda: self.service.rename_image(image.id, dialog.image()),
                        "renaming an image", self.app_context)
        dialog.setup(image)
        dialog.deleteLater()

    def confirm_image_deletion(self):
        mosaic = self.service.selected_mosaic()
        images = self.service.selected_images()
        if not images:
            return
        names = [image.filename for image in images]
        if len(names) == 1:
            message = self.tr("<center>Delete image <b>'{name}'</b> from '{mosaic}' imagery collection?"
                              ).format(name=names[0], mosaic=mosaic.name)
        elif len(names) <= 3:
            message = self.tr("<center>Delete following images from '{mosaic}' imagery collection:<br><b>'{names}'</b>?"
                              ).format(names="', <br>'".join(names), mosaic=mosaic.name)
        else:
            message = self.tr("<center>Delete <b>{len}</b> images from '{mosaic}' imagery collection?"
                              ).format(len=len(names), mosaic=mosaic.name)
        if self._confirm(message):
            self.service.delete_selected_images()

    def image_info(self, *args):
        image = self.service.selected_image()
        if image:
            self.view.full_image_info(image=image)

    # ---------- download save prompt ----------

    def _prompt_save_download(self, url: str, suggested_filename: str):
        save_path, _ = QFileDialog.getSaveFileName(
            QApplication.activeWindow(),
            self.tr("Save image as"),
            suggested_filename,
            "TIF files (*.tif *.tiff);;All files (*)")
        if save_path:
            self.service.save_downloaded(url, save_path)

    def _confirm(self, message: str) -> bool:
        box = QMessageBox(QMessageBox.Question, "Mapflow", message, parent=QApplication.activeWindow())
        box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        return box.exec() == QMessageBox.Ok
