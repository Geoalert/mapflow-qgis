from typing import List, Optional
import sys

from ...dialogs.main_dialog import MainDialog
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QAbstractItemView, QToolButton,
                             QMessageBox, QApplication, QMenu, QAction)
from PyQt5.QtGui import QPixmap

from ...schema.data_catalog import MosaicReturnSchema, ImageReturnSchema
from ...dialogs import icons
from ...functional.helpers import get_readable_size


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
        self.imageContainerWidget = QWidget()
        self.mosaicContainerWidget = QWidget()
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

        # Setup layouts
        self.mosaic_cell_layout = QHBoxLayout()
        self.image_cell_layout = QHBoxLayout()
        self.create_mosaic_cell_buttons_layout()
        self.create_image_cell_buttons_layout()

        # Add sorting options for catalog tables
        self.dlg.sortCombo.addItems([self.tr("A-Z"), self.tr("Z-A"),
                                     self.tr("Biggest first"), self.tr("Smallest first"),
                                     self.tr("Newest first"), self.tr("Oldest first")])
        # Default sorting column is 1 (name)
        self.sort_mosaics_column = 1
        self.sort_images_column = 1
        # Default sortCombo index is 0 (A-Z)
        self.sort_mosaics_index = 0
        self.sort_images_index = 0

    @property
    def mosaic_table_visible(self):
        return self.dlg.stackedLayout.currentIndex() == 0

    def display_mosaics(self, mosaics: list[MosaicReturnSchema]):
        self.contain_mosaic_cell_buttons()
        if not mosaics:
            return
        # First column is ID, hidden; second is name
        self.dlg.mosaicTable.setColumnCount(4)
        self.dlg.mosaicTable.setColumnHidden(0, True)
        self.dlg.mosaicTable.setColumnHidden(2, True)
        self.dlg.mosaicTable.setColumnHidden(3, True)
        self.dlg.mosaicTable.setRowCount(len(mosaics))
        self.dlg.mosaicTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, mosaic in enumerate(mosaics):
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, mosaic.id)
            self.dlg.mosaicTable.setItem(row, 0, id_item)
            name_item = QTableWidgetItem()
            name_item.setData(Qt.DisplayRole, mosaic.name)
            self.dlg.mosaicTable.setItem(row, 1, name_item)
            size_item = QTableWidgetItem()
            size_item.setData(Qt.DisplayRole, mosaic.sizeInBytes)
            self.dlg.mosaicTable.setItem(row, 2, size_item)
            date_item = QTableWidgetItem()
            date_item.setData(Qt.DisplayRole, mosaic.created_at.timestamp())
            self.dlg.mosaicTable.setItem(row, 3, date_item)
            self.dlg.mosaicTable.setHorizontalHeaderLabels(["ID", self.tr("Mosaics"), self.tr("Size"), self.tr("Created")])
        self.dlg.mosaicTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.dlg.mosaicTable.sortItems(self.sort_mosaics_column, Qt.AscendingOrder)
        # Set show-images tooltip for mosaics' cells
        for row in range(self.dlg.mosaicTable.rowCount()):
            item = self.dlg.mosaicTable.item(row, 1)
            item.setToolTip(self.tr("Double-click to show images"))

    def sort_catalog(self):
        index = self.dlg.sortCombo.currentIndex()
        # Define sorting order based on sortCombo index
        if index in (0, 3, 5): # A-Z, Smallest first, Oldest first
            order = Qt.AscendingOrder
        else: # Z-A, Biggest first, Newest first
            order = Qt.DescendingOrder
        # Sort mosaics
        if self.mosaic_table_visible:
            self.sort_mosaics_index = index
            if index in (0, 1): # sort by name
                self.sort_mosaics_column = 1
            elif index in (2, 3): # sort by size
                self.sort_mosaics_column = 2
            else: # sort by date
                self.sort_mosaics_column = 3
            self.dlg.mosaicTable.sortItems(self.sort_mosaics_column, order)
        # Sort images
        else:
            if index in (0, 1): # sort by name
                self.sort_images_column = 1
            elif index in (2, 3): # sort by size
                self.sort_images_column = 2
            else: # sort by date
                self.sort_images_column = 3
            self.dlg.imageTable.sortItems(self.sort_images_column, order)
        
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
                       "Number of images: {count} \n").format(name=self.dlg.imagePreview.fontMetrics().elidedText(
                                                                  mosaic.name, 
                                                                  Qt.ElideRight, 
                                                                  self.dlg.imagePreview.width() - 10), 
                                                             count=len(images))
        if images:
            text += self.tr("Size: {mosaic_size} \nPixel size: {pixel_size} m \n"
                           ).format(mosaic_size=get_readable_size(mosaic.sizeInBytes),
                                    pixel_size=round(sum(list(images[0].meta_data.values())[6])/len(list(images[0].meta_data.values())[6]), 2))
        text += self.tr("Created: {date} at {time} \nTags: {tags}"
                       ).format(date=mosaic.created_at.date(), time=mosaic.created_at.strftime('%H:%M'),
                                tags=tags_str)
        self.dlg.imagePreview.setText(text)
        self.dlg.imagePreview.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

    def full_image_info(self, image: ImageReturnSchema):
        try:
            message = self.tr('<b>Name</b>: {filename}\
                              <br><b>Uploaded</b></br>: {date} at {time}\
                              <br><b>Size</b></br>: {file_size}\
                              <br><b>CRS</b></br>: {crs}\
                              <br><b>Number of bands</br></b>: {bands}\
                              <br><b>Width</br></b>: {width} pixels\
                              <br><b>Height</br></b>: {height} pixels\
                              <br><b>Pixel size</br></b>: {pixel_size} m'\
                             ).format(filename=image.filename, 
                                     date=image.uploaded_at.date(),
                                     time=image.uploaded_at.strftime('%H:%M'),
                                     file_size=get_readable_size(image.file_size), 
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
        self.contain_image_cell_buttons()
        self.dlg.imageTable.setRowCount(len(images))
        self.dlg.imageTable.setColumnCount(4)
        self.dlg.imageTable.setColumnHidden(0, True)
        self.dlg.imageTable.setColumnHidden(2, True)
        self.dlg.imageTable.setColumnHidden(3, True)
        self.dlg.imageTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, image in enumerate(images):
            table_item = QTableWidgetItem()
            table_item.setData(Qt.DisplayRole, image.id)
            self.dlg.imageTable.setItem(row, 0, table_item)
            name_item = QTableWidgetItem()
            name_item.setData(Qt.DisplayRole, image.filename)
            self.dlg.imageTable.setItem(row, 1, name_item)
            size_item = QTableWidgetItem()
            size_item.setData(Qt.DisplayRole, image.file_size)
            self.dlg.imageTable.setItem(row, 2, size_item)
            date_item = QTableWidgetItem()
            date_item.setData(Qt.DisplayRole, image.uploaded_at.timestamp())
            self.dlg.imageTable.setItem(row, 3, date_item)
        self.dlg.imageTable.setHorizontalHeaderLabels(["ID", self.tr("Images"), self.tr("Size"), self.tr("Uploaded")])
        self.dlg.imageTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.dlg.imageTable.sortItems(self.sort_images_column, Qt.AscendingOrder)
        if len(images) == 0:
            self.dlg.previewMosaicButton.setEnabled(False)
            self.dlg.showImagesButton.setEnabled(False)
        else:
            self.dlg.previewMosaicButton.setEnabled(True)
            self.dlg.showImagesButton.setEnabled(True)

    def show_preview_s(self, preview_image):
        self.dlg.imagePreview.setPixmap(QPixmap.fromImage(preview_image))
        self.dlg.imagePreview.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

    def selected_mosaic_ids(self, limit=None):
        # Add unique selected rows
        selected_rows = list(set(index.row() for index in self.dlg.mosaicTable.selectionModel().selectedIndexes()))
        if not selected_rows:
            return []
        pids = [self.dlg.mosaicTable.item(row, 0).text()
                for row in selected_rows[:limit]]
        return pids
    
    def select_mosaic_cell(self, mosaic_id):
        # Store widgets before deleting a row
        item = self.dlg.mosaicTable.findItems(mosaic_id, Qt.MatchExactly)[0]
        self.dlg.mosaicTable.setCurrentCell(item.row(), 1)

    def selected_images_indecies(self, limit=None):
        selected_rows = list(set(index.row() for index in self.dlg.imageTable.selectionModel().selectedIndexes()))
        if not selected_rows:
            return []
        pids = [self.dlg.imageTable.item(row, 0).text()
                for row in selected_rows[:limit]]
        return pids
    
    def show_storage(self, taken_storage, free_storage):
        if free_storage:
            self.dlg.dataLimit.setText(self.tr("Your data: {taken}. Free space: {free}").format(taken=get_readable_size(taken_storage), 
                                                                                                free=get_readable_size(free_storage)))
        else:
            self.dlg.dataLimit.setText("")

    def setup_upload_image_menu(self):
        self.upload_image_menu.addAction(self.upload_from_file)
        self.upload_image_menu.addAction(self.choose_raster_layer)
        self.dlg.addImageButton.setPopupMode(QToolButton.InstantPopup)
        self.dlg.addImageButton.setMenu(self.upload_image_menu)

    def show_mosaic_info(self, mosaic_name):
        self.add_mosaic_cell_buttons()
        # Show mosaic info
        self.dlg.catalogSelectionLabel.setText(self.tr("Selected mosaic: <b>{mosaic_name}").format(
            mosaic_name=self.dlg.imagePreview.fontMetrics().elidedText(
                mosaic_name,
                Qt.ElideRight,
                self.dlg.imagePreview.width() - 10)))
        # Enable buttons
        self.dlg.deleteCatalogButton.setEnabled(True)
        self.dlg.seeImagesButton.setEnabled(True)
        # Show widgets
        self.set_table_tooltip(self.dlg.mosaicTable)

    def clear_mosaic_info(self):
        self.contain_mosaic_cell_buttons()
        self.dlg.catalogInfo.clear()
        self.dlg.imagePreview.clear()
        self.dlg.catalogSelectionLabel.setText(self.tr("No mosaic selected"))
        # Disable buttons
        self.dlg.deleteCatalogButton.setEnabled(False)
        self.dlg.seeImagesButton.setEnabled(False)
        # Hide widgets
        self.set_table_tooltip(self.dlg.mosaicTable)

    def show_image_info(self, image: ImageReturnSchema):
        if not image:
            return
        self.dlg.catalogInfo.setText(self.tr("uploaded: {date} at {time} \n"
                                             "file size: {size} \n"
                                             "pixel size: {pixel_size} m \n"
                                             "bands: {count}"
                                            ).format(date=image.uploaded_at.date(),
                                                     time=image.uploaded_at.strftime('%H:%M'),
                                                     size=get_readable_size(image.file_size),
                                                     pixel_size=round(sum(list(image.meta_data.values())[6])/len(list(image.meta_data.values())[6]), 2),
                                                     count=list(image.meta_data.values())[1]))
        self.dlg.catalogSelectionLabel.setText(self.tr("Selected image: <b>{image_name}").format(
            image_name=self.dlg.imagePreview.fontMetrics().elidedText(
                image.filename,
                Qt.ElideRight,
                self.dlg.imagePreview.width() - 10)))
        # Show widgets
        self.dlg.deleteCatalogButton.setEnabled(True)
        self.set_table_tooltip(self.dlg.imageTable)

    def clear_image_info(self):
        self.contain_image_cell_buttons()
        self.dlg.catalogSelectionLabel.setText(self.tr("No image selected"))
        self.dlg.deleteCatalogButton.setEnabled(False)
        self.dlg.imagePreview.clear()
        self.dlg.catalogInfo.clear()
        self.set_table_tooltip(self.dlg.imageTable)

    def set_table_tooltip(self, table):
        for row in range(table.rowCount()):
            item = table.item(row, 1)
            if item.isSelected(): # set deselection tooltip for both tables' selected items
                text = self.tr("'Cmd' + click to deselect") if sys.platform == 'darwin' else self.tr("'Ctrl' + click to deselect")
                item.setToolTip(text)
            else: # when not selected, set show-images tooltip for mosaics and none for images
                text = self.tr("Double-click to show images") if table == self.dlg.mosaicTable else ""
                item.setToolTip(text)

    def show_images_table(self):
        row = self.dlg.selected_mosaic_cell.row()
        column = self.dlg.selected_mosaic_cell.column()
        # Temporary forbit selection to prevent weird bug
        self.dlg.mosaicTable.setSelectionMode(QAbstractItemView.NoSelection)
        # Show images
        self.dlg.stackedLayout.setCurrentIndex(1)
        # En(dis)able buttons and change labels
        self.dlg.seeMosaicsButton.setEnabled(True)
        self.dlg.seeImagesButton.setEnabled(False)
        self.dlg.infoPreviewLabel.setText(self.tr("Image preview"))
        self.dlg.deleteCatalogButton.setText(self.tr("Delete image"))
        self.dlg.addCatalogButton.setText(self.tr("Add image"))
        self.dlg.addCatalogButton.setMenu(self.upload_image_menu)
        # Allow selection back
        self.dlg.mosaicTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dlg.mosaicTable.setCurrentCell(row, column)
        # Because we open images table always with empty selection
        self.clear_image_info()
        # Set sorting combo text
        self.dlg.sortCombo.setCurrentIndex(self.sort_images_index)

    def show_mosaics_table(self, selected_mosaic_name: Optional[str]):
        # Save buttons before deleting cells and therefore widgets
        # En(dis)able buttons and change labels
        self.dlg.seeMosaicsButton.setEnabled(False)
        self.dlg.seeImagesButton.setEnabled(True)
        self.dlg.infoPreviewLabel.setText(self.tr("Mosaic data"))
        self.dlg.deleteCatalogButton.setText(self.tr("Delete mosaic"))
        self.dlg.addCatalogButton.setText(self.tr("Add mosaic"))
        self.dlg.addCatalogButton.setMenu(None)
        # Clear image table
        self.dlg.imageTable.clearSelection()
        # Show mosaics
        self.dlg.stackedLayout.setCurrentIndex(0)
        if selected_mosaic_name:
            self.show_mosaic_info(selected_mosaic_name)
        else:
            self.clear_mosaic_info()
        # Set sorting combo text
        self.dlg.sortCombo.setCurrentIndex(self.sort_mosaics_index)

    def create_mosaic_cell_buttons_layout(self):
        self.mosaic_cell_layout.setContentsMargins(0,0,3,0)
        self.mosaic_cell_layout.setSpacing(0)
        self.mosaic_cell_layout.addWidget(self.dlg.addImageButton)
        self.mosaic_cell_layout.addWidget(self.dlg.mosaicSpacers[0])
        self.mosaic_cell_layout.addWidget(self.dlg.showImagesButton)
        self.mosaic_cell_layout.addWidget(self.dlg.mosaicSpacers[1])
        self.mosaic_cell_layout.addWidget(self.dlg.previewMosaicButton)
        self.mosaic_cell_layout.addWidget(self.dlg.mosaicSpacers[2])
        self.mosaic_cell_layout.addWidget(self.dlg.editMosaicButton)
        self.mosaic_cell_layout.setAlignment(Qt.AlignRight)

    def create_image_cell_buttons_layout(self):
        self.image_cell_layout.setContentsMargins(0,0,3,0)
        self.image_cell_layout.setSpacing(0)
        self.image_cell_layout.addWidget(self.dlg.previewImageButton)
        self.image_cell_layout.addWidget(self.dlg.imageSpacer)
        self.image_cell_layout.addWidget(self.dlg.imageInfoButton)
        self.image_cell_layout.setAlignment(Qt.AlignRight)

    def add_mosaic_cell_buttons(self):
        # Create layout of mosaic cell buttons
        # Create mosaic cell widget with this layout
        cellWidget = QWidget()
        cellWidget.setLayout(self.mosaic_cell_layout)
        self.dlg.mosaicTable.setCellWidget(self.dlg.selected_mosaic_cell.row(), 
                                           self.dlg.selected_mosaic_cell.column(),
                                           cellWidget)
    
    def add_image_cell_buttons(self):
        if self.dlg.imageTable.selectionModel().hasSelection():
            self.dlg.selected_image_cell = self.dlg.imageTable.selectedIndexes()[0]
        # Create layout of image cell buttons
        # Create image cell widget with this layout
        cellWidget = QWidget()
        cellWidget.setLayout(self.image_cell_layout)
        self.dlg.imageTable.setCellWidget(self.dlg.selected_image_cell.row(),
                                          self.dlg.selected_image_cell.column(),
                                          cellWidget)
        
    def contain_mosaic_cell_buttons(self):
        self.mosaicContainerWidget.setLayout(self.mosaic_cell_layout)

    def contain_image_cell_buttons(self):
        self.imageContainerWidget.setLayout(self.image_cell_layout)
        
    def alert(self, message: str, icon: QMessageBox.Icon = QMessageBox.Critical, blocking=True) -> None:
        """A duplicate of alert function from mapflow.py to avoid circular import.
        """
        box = QMessageBox(icon, "Mapflow", message, parent=QApplication.activeWindow())
        box.setTextFormat(Qt.RichText)
        if icon == QMessageBox.Question:  # by default, only OK is added
            box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        return box.exec() == QMessageBox.Ok if blocking else box.open()
