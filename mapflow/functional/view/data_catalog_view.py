from typing import List

from ...dialogs.main_dialog import MainDialog
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QAbstractItemView, QToolButton,
                             QMessageBox, QApplication, QMenu, QAction)
from PyQt5.QtGui import QPixmap

from ...schema.data_catalog import MosaicReturnSchema, ImageReturnSchema
from ...dialogs import icons


class DataCatalogView(QObject):
    def __init__(self, dlg: MainDialog):
        super().__init__()
        self.dlg = dlg
        self.dlg.mosaicTable.setSelectionMode(QAbstractItemView.SingleSelection)

        # Setup menu for uploading images to mosaic
        self.upload_image_menu = QMenu()
        self.upload_from_file = QAction(self.tr("Upload from file"))
        self.choose_raster_layer = QAction(self.tr("Choose raster layer"))
        self.setup_upload_image_menu()

        # Add icons to '<' and '>' catalog buttons
        self.dlg.seeMosaicsButton.setIcon(icons.arrow_left_icon)
        self.dlg.seeImagesButton.setIcon(icons.arrow_right_icon)

        # Create containers for image cells widget (so widgets don't get deleted by Qt)
        self.containerWidget = QWidget()
        self.containerLayout = QHBoxLayout()
        # Add icons to mosaic and image cell widgets
        self.dlg.addImageButton.setIcon(icons.plus_icon)
        self.dlg.showImagesButton.setIcon(icons.images_icon)
        self.dlg.previewMosaicButton.setIcon(icons.lens_icon)
        self.dlg.editMosaicButton.setIcon(icons.edit_icon)
        self.dlg.previewImageButton.setIcon(icons.lens_icon)
        self.dlg.imageInfoButton.setIcon(icons.info_icon)        
        # Add tooltips to mosaic and image cell widgets
        self.dlg.addImageButton.setToolTip(self.tr("Add images"))
        self.dlg.showImagesButton.setToolTip(self.tr("Show images"))
        self.dlg.previewMosaicButton.setToolTip(self.tr("Preview"))
        self.dlg.editMosaicButton.setToolTip(self.tr("Edit"))
        self.dlg.previewImageButton.setToolTip(self.tr("Preview"))
        self.dlg.imageInfoButton.setToolTip(self.tr("Info"))
        # Set size for mosaic and image cell widgets
        buttons_width = 30
        self.dlg.addImageButton.setFixedWidth(buttons_width)
        self.dlg.showImagesButton.setFixedWidth(buttons_width)
        self.dlg.previewMosaicButton.setFixedWidth(buttons_width)
        self.dlg.editMosaicButton.setFixedWidth(buttons_width)
        self.dlg.previewImageButton.setFixedWidth(buttons_width)
        self.dlg.imageInfoButton.setFixedWidth(buttons_width)
        
        # Transfer labels' long text to a new line
        self.dlg.catalogSelectionLabel.setWordWrap(True)
        self.dlg.imagePreview.setWordWrap(True)

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
            self.dlg.mosaicTable.setHorizontalHeaderLabels(["ID", self.tr("Mosaics")])
            self.dlg.mosaicTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.dlg.mosaicTable.sortItems(1, Qt.AscendingOrder)
        
    def display_mosaic_info(self, mosaic: MosaicReturnSchema, images: list[ImageReturnSchema]):
        if not mosaic:
            return
        if mosaic.tags:
            elided_tags = []
            for tag in mosaic.tags:
                elided_tag = self.dlg.imagePreview.fontMetrics().elidedText(tag, Qt.ElideRight, self.dlg.imagePreview.width() - 10)
                elided_tags.append(elided_tag)
            tags_str = ', '.join(elided_tags)
        else:
            tags_str = ''
        text = self.tr("Mosaic: {name} \n"
                       "Number of images: {count} \n".format(name=self.dlg.imagePreview.fontMetrics().elidedText(
                                                                  mosaic.name, 
                                                                  Qt.ElideRight, 
                                                                  self.dlg.imagePreview.width() - 10), 
                                                             count=len(images)))
        if images:
            text += self.tr("Size: {mosaic_size} MB \nPixel size: {pixel_size} m \n"
                            .format(mosaic_size=round(sum(i.file_size for i in images)/1000000, 1),
                                    pixel_size=round(sum(list(images[0].meta_data.values())[6])/len(list(images[0].meta_data.values())[6]), 2)))
        text += self.tr("Created: {date} at {time} \nTags: {tags}"
                        .format(date=mosaic.created_at.date(), time=mosaic.created_at.strftime('%H:%M'),
                                tags=tags_str))
        self.dlg.imagePreview.setText(text)
        self.dlg.imagePreview.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

    def display_image_info(self, image: ImageReturnSchema):
        if not image:
            return
        self.dlg.catalogInfo.setText(self.tr("uploaded: {date} at {time} \n"
                                             "file size: {size} MB \n"
                                             "pixel size: {pixel_size} m \n"
                                             "bands: {count}"
                                             .format(date=image.uploaded_at.date(),
                                                     time=image.uploaded_at.strftime('%H:%M'),
                                                     size=round(image.file_size/1048576, 1),
                                                     pixel_size=round(sum(list(image.meta_data.values())[6])/len(list(image.meta_data.values())[6]), 2),
                                                     count=list(image.meta_data.values())[1])))

    def full_image_info(self, image: ImageReturnSchema):
        try:
            message = self.tr('<b>Name</b>: {filename}\
                              <br><b>Uploaded</b></br>: {date} at {time}\
                              <br><b>Size</b></br>: {file_size} MB\
                              <br><b>CRS</b></br>: {crs}\
                              <br><b>Number of bands</br></b>: {bands}\
                              <br><b>Width</br></b>: {width} pixels\
                              <br><b>Height</br></b>: {height} pixels\
                              <br><b>Pixel size</br></b>: {pixel_size} m'\
                             .format(filename=image.filename, 
                                     date=image.uploaded_at.date(),
                                     time=image.uploaded_at.strftime('%H:%M'),
                                     file_size=round(image.file_size/1048576, 1), 
                                     crs=list(image.meta_data.values())[0],
                                     bands=list(image.meta_data.values())[1],
                                     width=list(image.meta_data.values())[2],
                                     height=list(image.meta_data.values())[4],
                                     pixel_size=round(sum(list(image.meta_data.values())[6])/len(list(image.meta_data.values())[6]), 2)))
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
        self.dlg.imageTable.setHorizontalHeaderLabels(["ID", self.tr("Images")])
        if len(images) == 0:
            self.dlg.previewMosaicButton.setEnabled(False)
            self.dlg.showImagesButton.setEnabled(False)
        else:
            self.dlg.previewMosaicButton.setEnabled(True)
            self.dlg.showImagesButton.setEnabled(True)
        self.dlg.imageTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.dlg.imageTable.sortItems(1, Qt.AscendingOrder)

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
    
    def select_mosaic_cell(self, mosaic_id):
        # Store widgets before deleting a row
        self.contain_mosaic_cell_buttons()
        item = self.dlg.mosaicTable.findItems(mosaic_id, Qt.MatchExactly)[0]
        self.dlg.mosaicTable.setCurrentCell(item.row(), 1)

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
        self.dlg.addImageButton.setPopupMode(QToolButton.InstantPopup)
        self.dlg.addImageButton.setMenu(self.upload_image_menu)

    def check_mosaic_or_image_selection(self, mosaic_name, image_name):
        """ Called when selection in any catalog table is changed.

        :param mosaic_name: str (to display if mosaics table is used) or None (no current sellection).
        :param image_name: str (to display if image table is used) or None (so mosaic_name is displayed).
        """
        if not mosaic_name and not image_name:
            self.dlg.catalogSelectionLabel.setText(self.tr("No current selection"))

        # Mosaics:
        if self.dlg.mosaicTable.selectionModel().hasSelection() is False:
            # Clear info
            self.dlg.catalogInfo.setText("")
            self.dlg.imagePreview.setText("")
            # Disable buttons
            self.dlg.deleteCatalogButton.setEnabled(False)
            self.dlg.seeImagesButton.setEnabled(False)
            # Clear images table
            self.dlg.imageTable.clearSelection()
            self.dlg.imageTable.setColumnCount(0)
            self.dlg.imageTable.setRowCount(0)
            # Hide widgets
            self.show_cell_widgets(mosaic=True, on=False)
        else:
            # Add buttons on selection change only for mosaics, because images have multiselect
            self.add_mosaic_cell_buttons()
            # Show mosaic info
            self.dlg.catalogSelectionLabel.setText(self.tr("Selected mosaic: <b>{mosaic_name}".format(
                                                            mosaic_name=self.dlg.imagePreview.fontMetrics().elidedText(
                                                                        mosaic_name, 
                                                                        Qt.ElideRight, 
                                                                        self.dlg.imagePreview.width() - 10))))
            # Enable buttons
            self.dlg.deleteCatalogButton.setEnabled(True)
            if self.dlg.stackedLayout.currentIndex() == 0:
                self.dlg.seeImagesButton.setEnabled(True)
            # Show widgets
            self.show_cell_widgets(mosaic=True, on=True)

        # Images:
        if self.dlg.imageTable.selectionModel().hasSelection() is False:
            # Change text to mosaic-related
            self.dlg.infoPreviewLabel.setText(self.tr("Mosaic info"))
            self.dlg.deleteCatalogButton.setText(self.tr("Delete mosaic"))
            # Clear bottom info label
            self.dlg.catalogInfo.setText("")
            # Hide widgets
            self.show_cell_widgets(mosaic=False, on=False)
        else:
            # Change text to image-related
            self.dlg.infoPreviewLabel.setText(self.tr("Image preview"))
            self.dlg.deleteCatalogButton.setText(self.tr("Delete image"))
            # Show image info in a bottom label
            self.dlg.catalogSelectionLabel.setText(self.tr("Selected image: <b>{image_name}".format(
                                                            image_name=self.dlg.imagePreview.fontMetrics().elidedText(
                                                                       image_name, 
                                                                       Qt.ElideRight, 
                                                                       self.dlg.imagePreview.width() - 10))))
            # Show widgets
            self.show_cell_widgets(mosaic=False, on=True)
        
        # Set mosaic or image cell deselection tooltip
        if self.dlg.stackedLayout.currentIndex() == 0:
            self.add_cell_tooltip(mosaic=True)
        else:
            self.add_cell_tooltip(mosaic=False)

    def show_cell_widgets(self, mosaic: bool, on: bool):
        """ Called upon selection/deselection in tables to show/hide buttons.

        :param mosaic: whether mosaic (True) or image (False) tables is used.
        :param on: show (True) or hide (False) mosaic or image.
        """
        # Specify table and position
        if mosaic: # mosaic table is opened
            if not self.dlg.selected_mosaic_cell:
                return
            row = self.dlg.selected_mosaic_cell.row()
            column = self.dlg.selected_mosaic_cell.column()
            table = self.dlg.mosaicTable
        else: # image table is opened
            if not self.dlg.selected_image_cell:
                return
            row = self.dlg.selected_image_cell.row()
            column = self.dlg.selected_image_cell.column()
            table = self.dlg.imageTable
        # Show or hide widgets
        if table.cellWidget(row, column):
            for widget in table.cellWidget(row, column).children():
                if isinstance(widget, QWidget):
                    widget.setVisible(on)
        else:
            if mosaic:
                self.add_mosaic_cell_buttons()
            else:
                self.add_image_cell_buttons()
    
    def add_cell_tooltip(self, mosaic: bool):
        """ Called upon selection/deselection in tables to show/hide deselection tooltip.

        :param mosaic: whether mosaic (True) or image (False) table needs deselection tooltip.
        """
        if mosaic:
            table = self.dlg.mosaicTable
        else:
            table = self.dlg.imageTable
        for row in range(table.rowCount()): 
            item = table.item(row, 1)
            if item.isSelected():
                item.setToolTip(self.tr("'Ctrl' + click to deselect"))
            else:
                item.setToolTip("")

    def switch_catalog_table(self):
        row = self.dlg.selected_mosaic_cell.row()
        column = self.dlg.selected_mosaic_cell.column()
        # If mosaics are opened before the click
        if self.dlg.stackedLayout.currentIndex() == 0:
            self.dlg.stackedLayout.setCurrentIndex(1)
            self.dlg.mosaicTable.setCurrentCell(row, column)
            self.dlg.seeMosaicsButton.setEnabled(True)
            self.dlg.seeImagesButton.setEnabled(False)      
            # Setup add image menu
            self.dlg.addCatalogButton.setText(self.tr("Add image"))
            self.dlg.addCatalogButton.setMenu(self.upload_image_menu)
        else: # if images are opened before the click
            # Save buttons before deleting cells and therefore widgets
            self.contain_image_cell_buttons()
            # Remove menu for add mosaic
            self.dlg.addCatalogButton.setText(self.tr("Add mosaic"))
            self.dlg.addCatalogButton.setMenu(None)
            # Clear image table
            self.dlg.imageTable.clearSelection()
            self.dlg.seeMosaicsButton.setEnabled(False)
            self.dlg.seeImagesButton.setEnabled(True)
            # Show mosaics
            self.dlg.stackedLayout.setCurrentIndex(0)

    def add_mosaic_cell_buttons(self):
        # Create layout of mosaic cell buttons
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,3,0)
        layout.setSpacing(0)
        layout.addWidget(self.dlg.addImageButton)
        layout.addWidget(self.dlg.mosaicSpacers[0])
        layout.addWidget(self.dlg.showImagesButton)
        layout.addWidget(self.dlg.mosaicSpacers[1])
        layout.addWidget(self.dlg.previewMosaicButton)
        layout.addWidget(self.dlg.mosaicSpacers[2])
        layout.addWidget(self.dlg.editMosaicButton)
        layout.setAlignment(Qt.AlignRight)
        # Create mosaic cell widget with this layout        
        cellWidget = QWidget()
        cellWidget.setLayout(layout)
        self.dlg.mosaicTable.setCellWidget(self.dlg.selected_mosaic_cell.row(), 
                                           self.dlg.selected_mosaic_cell.column(),
                                           cellWidget)
    
    def add_image_cell_buttons(self):
        if self.dlg.imageTable.selectionModel().hasSelection():
            self.dlg.selected_image_cell = self.dlg.imageTable.selectedIndexes()[0]
        # Create layout of image cell buttons
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,3,0)
        layout.setSpacing(0)
        layout.addWidget(self.dlg.previewImageButton)
        layout.addWidget(self.dlg.imageSpacer)
        layout.addWidget(self.dlg.imageInfoButton)
        layout.setAlignment(Qt.AlignRight)
        # Create image cell widget with this layout 
        cellWidget = QWidget()
        cellWidget.setLayout(layout)
        self.dlg.imageTable.setCellWidget(self.dlg.selected_image_cell.row(),
                                          self.dlg.selected_image_cell.column(),
                                          cellWidget)
        
    def contain_mosaic_cell_buttons(self):
        self.containerLayout.addWidget(self.dlg.editMosaicButton)
        self.containerLayout.addWidget(self.dlg.previewMosaicButton)
        self.containerLayout.addWidget(self.dlg.showImagesButton)
        self.containerLayout.addWidget(self.dlg.addImageButton)
        for spacer in self.dlg.mosaicSpacers:
            self.containerLayout.addWidget(spacer)
        self.containerWidget.setLayout(self.containerLayout)

    def contain_image_cell_buttons(self):
        self.containerLayout.addWidget(self.dlg.previewImageButton)
        self.containerLayout.addWidget(self.dlg.imageSpacer)
        self.containerLayout.addWidget(self.dlg.imageInfoButton)
        self.containerWidget.setLayout(self.containerLayout)
        
    def alert(self, message: str, icon: QMessageBox.Icon = QMessageBox.Critical, blocking=True) -> None:
        """A duplicate of alert function from mapflow.py to avoid circular import.
        """
        box = QMessageBox(icon, "Mapflow", message, parent=QApplication.activeWindow())
        box.setTextFormat(Qt.RichText)
        if icon == QMessageBox.Question:  # by default, only OK is added
            box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        return box.exec() == QMessageBox.Ok if blocking else box.open()
