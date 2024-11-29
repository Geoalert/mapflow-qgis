from typing import List

from ...dialogs.main_dialog import MainDialog
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QWidget, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QApplication, QMenu, QAction, QHeaderView, QHBoxLayout
from PyQt5.QtGui import QPixmap

from ...schema.data_catalog import MosaicReturnSchema, ImageReturnSchema
from ...dialogs import icons


class DataCatalogView(QObject):
    def __init__(self, dlg: MainDialog):
        super().__init__()
        self.dlg = dlg
        # Setup menu for uploadinf images to mosaic
        self.upload_image_menu = QMenu()
        self.upload_from_file = QAction(self.tr("Upload from file"))
        self.choose_raster_layer = QAction(self.tr("Choose raster layer"))
        self.setup_upload_image_menu()
        # Create containers for image cells widget (so widgets don't get deleted by Qt)
        self.containerWidget = QWidget()
        self.containerLayout = QHBoxLayout()

    def display_mosaics(self, mosaics: list[MosaicReturnSchema]):
        if not mosaics:
            return
        # First column is ID, hidden; second is name
        self.dlg.mosaicTable.setColumnCount(2)
        self.dlg.mosaicTable.setColumnHidden(0, True)
        self.dlg.mosaicTable.setRowCount(len(mosaics))
        self.dlg.mosaicTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, mosaic in enumerate(mosaics):
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, mosaic.id)
            self.dlg.mosaicTable.setItem(row, 0, id_item)
            name_item = QTableWidgetItem()
            name_item.setData(Qt.DisplayRole, mosaic.name)
            self.dlg.mosaicTable.setItem(row, 1, name_item)
            self.dlg.mosaicTable.setHorizontalHeaderLabels(["ID", "Mosaics"])
            self.dlg.mosaicTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
    def display_mosaic_info(self, mosaic: MosaicReturnSchema, images: list[ImageReturnSchema]):
        if not mosaic:
            return
        if mosaic.tags:
            tags_str = ', '.join(mosaic.tags)
        else:
            tags_str = ''
        if images:
            self.dlg.imagePreview.setText(self.tr("Number of images: {count} \n"
                                                  "Size: {mosaic_size} MB \n"
                                                  "Pixel size: {pixel_size} m \n"
                                                  "Created {date} at {h}:{m} \n"
                                                  "Tags: {tags}".format(count=len(images),
                                                                        mosaic_size=round(sum(i.file_size for i in images)/1000000, 1),
                                                                        pixel_size=round(sum(list(images[0].meta_data.values())[6])/len(list(images[0].meta_data.values())[6]), 2),
                                                                        date=mosaic.created_at.date(),
                                                                        h=mosaic.created_at.hour,
                                                                        m=mosaic.created_at.minute,
                                                                        tags=tags_str)))
        else:
            self.dlg.imagePreview.setText(self.tr("Number of images: None \n"
                                                  "Created {date} at {h}:{m} \n"
                                                  "Tags: {tags}".format(date=mosaic.created_at.date(),
                                                                        h=mosaic.created_at.hour,
                                                                        m=mosaic.created_at.minute,
                                                                        tags=tags_str)))
        self.dlg.imagePreview.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

    def display_image_info(self, image: ImageReturnSchema):
        if not image:
            return
        self.dlg.catalogInfo.setText(self.tr("created {date} at {h}:{m} \n"
                                             "bands: {count} \n"
                                             "pixel size: {pixel_size}"
                                             .format(date=image.uploaded_at.date(),
                                                     h=image.uploaded_at.hour,
                                                     m=image.uploaded_at.minute,
                                                     count=list(image.meta_data.values())[1],
                                                     pixel_size=round(sum(list(image.meta_data.values())[6])/len(list(image.meta_data.values())[6]), 2))))

    def full_image_info(self, image: ImageReturnSchema):
        try:
            message = '<b>Name</b>: {filename}\
                        <br><b>Uploaded</b></br>: {date} at {h}:{m}\
                        <br><b>Size</b></br>: {file_size} MB\
                        <br><b>CRS</b></br>: {crs}\
                        <br><b>Number of bands</br></b>: {bands}\
                        <br><b>Width</br></b>: {width} pixels\
                        <br><b>Height</br></b>: {height} pixels\
                        <br><b>Pixel size</br></b>: {pixel_size} m'\
                        .format(filename=image.filename, 
                                date=image.uploaded_at.date(),
                                h=image.uploaded_at.hour,
                                m=image.uploaded_at.minute,
                                file_size=round(image.file_size/1000000, 1), 
                                crs=list(image.meta_data.values())[0],
                                bands=list(image.meta_data.values())[1],
                                width=list(image.meta_data.values())[2],
                                height=list(image.meta_data.values())[4],
                                pixel_size=round(sum(list(image.meta_data.values())[6])/len(list(image.meta_data.values())[6]), 2))
            info_box = QMessageBox(QMessageBox.Information, "Mapflow", message, parent=QApplication.activeWindow())
            return info_box.exec()
        except IndexError:
            return

    def display_images(self, images: list[ImageReturnSchema]):
        self.dlg.imageTable.setRowCount(len(images))
        self.dlg.imageTable.setColumnCount(2)
        self.dlg.imageTable.setColumnHidden(0, True)
        self.dlg.imageTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, image in enumerate(images):
            table_item = QTableWidgetItem()
            table_item.setData(Qt.DisplayRole, image.id)
            self.dlg.imageTable.setItem(row, 0, table_item)
            name_item = QTableWidgetItem()
            name_item.setData(Qt.DisplayRole, image.filename)
            self.dlg.imageTable.setItem(row, 1, name_item)
        self.dlg.imageTable.setHorizontalHeaderLabels(["ID", "Images"])
        if len(images) == 0:
            self.dlg.previewMosaicButton.setEnabled(False)
            self.dlg.showImagesButton.setEnabled(False)
        else:
            self.dlg.previewMosaicButton.setEnabled(True)
            self.dlg.showImagesButton.setEnabled(True)
        self.dlg.imageTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def show_preview_s(self, preview_image):
        self.dlg.imagePreview.setPixmap(QPixmap.fromImage(preview_image))
        self.dlg.imagePreview.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

    def selected_mosaic_ids(self, limit=None):
        # add unique selected rows
        selected_rows = list(set(index.row() for index in self.dlg.mosaicTable.selectionModel().selectedIndexes()))
        if not selected_rows:
            return []
        pids = [self.dlg.mosaicTable.item(row, 0).text()
                for row in selected_rows[:limit]]
        return pids

    def selected_images_indecies(self, limit=None):
        selected_rows = list(set(index.row() for index in self.dlg.imageTable.selectionModel().selectedIndexes()))
        if not selected_rows:
            return []
        return selected_rows
    
    def show_storage(self, taken_storage, free_storage):
        if free_storage:
            self.dlg.dataLimit.setText(self.tr("Your data: {taken} MB. Free space: {free} MB".format(taken=round(taken_storage/1048576, 1), 
                                                                                                     free=round(free_storage/1048576, 1))))
        else:
            self.dlg.dataLimit.setText("")

    def setup_upload_image_menu(self):
        self.upload_image_menu.addAction(self.upload_from_file)
        self.upload_image_menu.addAction(self.choose_raster_layer)

    def check_mosaic_or_image_selection(self, mosaic_name, image_name):
        if not mosaic_name and not image_name:
            self.dlg.catalogSelectionLabel.setText(self.tr("No current selection"))

        # Mosaics
        if self.dlg.mosaicTable.selectionModel().hasSelection() is False:
            # Disable buttons and update widgets upon table selection change
            self.dlg.catalogInfo.setText("")
            self.dlg.imagePreview.setText("")
            self.dlg.deleteCatalogButton.setEnabled(False)
            self.dlg.imageTable.clearSelection()
            self.dlg.imageTable.setColumnCount(0)
            self.dlg.imageTable.setRowCount(0)
            # Hide all cell widgets
            for row in range(self.dlg.mosaicTable.rowCount()):
                if self.dlg.mosaicTable.cellWidget(row,1):
                    for widget in self.dlg.mosaicTable.cellWidget(row,1).children():
                        if isinstance(widget, QWidget):
                            widget.setVisible(False)
        else:
            # Enable buttons and update widgets upon table selection change
            self.dlg.deleteCatalogButton.setEnabled(True)
            self.dlg.catalogSelectionLabel.setText(self.tr("Selected mosaic: <b>{mosaic_name}".format(mosaic_name=mosaic_name)))
            # Show cell widgets
            for row in range(self.dlg.mosaicTable.rowCount()):
                if self.dlg.mosaicTable.cellWidget(row,1):
                    for widget in self.dlg.mosaicTable.cellWidget(row,1).children():
                        if isinstance(widget, QWidget):
                            widget.setVisible(True)
        # Set mosaic cell deselection tooltip
        for row in range(self.dlg.mosaicTable.rowCount()): 
            item = self.dlg.mosaicTable.item(row, 1)
            if item.isSelected():
                item.setToolTip(self.tr("'Ctrl' + click to deselect"))
            else:
                item.setToolTip("")

        # Images
        if self.dlg.imageTable.selectionModel().hasSelection() is False:
            # Disable buttons and update widgets upon table selection change
            self.dlg.infoPreviewLabel.setText(self.tr("Mosaic info"))
            self.dlg.deleteCatalogButton.setText("Delete mosaic")
            self.dlg.catalogInfo.setText("")
            # Hide all cell widgets
            for row in range(self.dlg.imageTable.rowCount()):
                if self.dlg.imageTable.cellWidget(row,1):
                    for widget in self.dlg.imageTable.cellWidget(row,1).children():
                        if isinstance(widget, QWidget):
                            widget.setVisible(False)
        else:
            # Enable buttons and update widgets upon table selection change
            self.dlg.infoPreviewLabel.setText(self.tr("Image preview"))
            self.dlg.deleteCatalogButton.setText("Delete image")
            self.dlg.catalogSelectionLabel.setText(self.tr("Selected image: <b>{image_name}".format(image_name=image_name)))
            # Show cell widgets
            for row in range(self.dlg.imageTable.rowCount()):
                if self.dlg.imageTable.cellWidget(row,1):
                    for widget in self.dlg.imageTable.cellWidget(row,1).children():
                        if isinstance(widget, QWidget):
                            widget.setVisible(True)
        # Set image cell deselection tooltip
        for row in range(self.dlg.imageTable.rowCount()): 
            item = self.dlg.imageTable.item(row, 1)
            if item.isSelected():
                item.setToolTip(self.tr("'Ctrl' + click to deselect"))
            else:
                item.setToolTip("")

    def switch_catalog_table(self):
        row = self.dlg.mosaicTable.selectedIndexes()[0].row()
        if self.dlg.stackedLayout.currentIndex() == 0:
            self.dlg.stackedLayout.setCurrentIndex(1)
            self.dlg.showMosaicsButton.setVisible(True)
        else:
            # Save buttons before deleting cells and therefore widgets
            self.containerLayout.addWidget(self.dlg.previewImageButton)
            self.containerLayout.addWidget(self.dlg.imageInfoButton)
            self.containerWidget.setLayout(self.containerLayout)
            # Show mosaics
            self.dlg.imageTable.clearSelection()
            self.dlg.stackedLayout.setCurrentIndex(0)
            self.dlg.showMosaicsButton.setVisible(False)
        self.dlg.mosaicTable.selectRow(row)

    def add_mosaic_cell_buttons(self):
        # Create layout of mosaic cell buttons
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,3,0)
        layout.setSpacing(3)
        layout.addWidget(self.dlg.addImageButton)
        layout.addWidget(self.dlg.showImagesButton)
        layout.addWidget(self.dlg.previewMosaicButton)
        layout.addWidget(self.dlg.editMosaicButton)
        layout.setAlignment(Qt.AlignRight)
        # Add icons
        self.dlg.addImageButton.setIcon(icons.plus_icon)
        self.dlg.showImagesButton.setIcon(icons.images_icon)
        self.dlg.previewMosaicButton.setIcon(icons.lens_icon)
        self.dlg.editMosaicButton.setIcon(icons.edit_icon)
        # Add tooltips
        self.dlg.addImageButton.setToolTip("Add images")
        self.dlg.showImagesButton.setToolTip("Show images")
        self.dlg.previewMosaicButton.setToolTip("Preview")
        self.dlg.editMosaicButton.setToolTip("Edit")
        # Set size
        buttons_width = 30
        self.dlg.addImageButton.setFixedWidth(buttons_width)
        self.dlg.showImagesButton.setFixedWidth(buttons_width)
        self.dlg.previewMosaicButton.setFixedWidth(buttons_width)
        self.dlg.editMosaicButton.setFixedWidth(buttons_width)
        # Create mosaic cell widget with this layout        
        cellWidget = QWidget()
        cellWidget.setLayout(layout)
        self.dlg.mosaicTable.setCellWidget(self.dlg.mosaicTable.selectedIndexes()[0].row(), 
                                           self.dlg.mosaicTable.selectedIndexes()[0].column(), 
                                           cellWidget)
    
    def add_image_cell_buttons(self):
        # Create layout of image cell buttons
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,3,0)
        layout.setSpacing(3)
        layout.addWidget(self.dlg.previewImageButton)
        layout.addWidget(self.dlg.imageInfoButton)
        layout.setAlignment(Qt.AlignRight)
        # Add icons
        self.dlg.previewImageButton.setIcon(icons.lens_icon)
        self.dlg.imageInfoButton.setIcon(icons.info_icon)
        # Add tooltips
        self.dlg.previewImageButton.setToolTip("Preview")
        self.dlg.imageInfoButton.setToolTip("Info")
        # Set size
        buttons_width = 30
        self.dlg.previewImageButton.setFixedWidth(buttons_width)
        self.dlg.imageInfoButton.setFixedWidth(buttons_width)
        # Create image cell widget with this layout 
        cellWidget = QWidget()
        cellWidget.setLayout(layout)
        self.dlg.imageTable.setCellWidget(self.dlg.imageTable.selectedIndexes()[0].row(), 
                                           self.dlg.imageTable.selectedIndexes()[0].column(), 
                                           cellWidget)
        
    def alert(self, message: str, icon: QMessageBox.Icon = QMessageBox.Critical, blocking=True) -> None:
        """A duplicate of alert function from mapflow.py to avoid circular import.
        """
        box = QMessageBox(icon, "Mapflow", message, parent=QApplication.activeWindow())
        box.setTextFormat(Qt.RichText)
        if icon == QMessageBox.Question:  # by default, only OK is added
            box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        return box.exec() == QMessageBox.Ok if blocking else box.open()
