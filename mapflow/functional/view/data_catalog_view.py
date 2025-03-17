from typing import List, Optional
import sys

from ...dialogs.main_dialog import MainDialog
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QAbstractItemView, QToolButton,
                             QMessageBox, QApplication, QMenu, QAction)
from PyQt5.QtGui import QPixmap, QFontMetrics

from ...schema.data_catalog import MosaicReturnSchema, ImageReturnSchema
from ...dialogs import icons
from ...functional.helpers import get_readable_size


class DataCatalogView(QObject):
    def __init__(self, dlg: MainDialog):
        super().__init__()
        self.dlg = dlg

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
        self.dlg.catalogInfo.setWordWrap(True)

        # Setup layouts
        self.mosaic_cell_layout = QHBoxLayout()
        self.image_cell_layout = QHBoxLayout()
        self.create_mosaic_cell_buttons_layout()
        self.create_image_cell_buttons_layout()

        # Add sorting options for catalog tables
        self.dlg.sortCatalogCombo.addItems([self.tr("A-Z"), self.tr("Z-A"),
                                     self.tr("Biggest first"), self.tr("Smallest first"),
                                     self.tr("Newest first"), self.tr("Oldest first")])
        # Default sorting column is 1 (name)
        self.sort_mosaics_column = 1
        self.sort_images_column = 1
        # Default sortCatalogCombo index is 0 (A-Z)
        self.sort_mosaics_index = 0
        self.sort_images_index = 0

        # Mosaic images instant preview
        self.dlg.nextImageButton.setVisible(False)
        self.dlg.previousImageButton.setVisible(False)
        self.dlg.nextImageButton.setIcon(icons.arrow_right_icon)
        self.dlg.previousImageButton.setIcon(icons.arrow_left_icon)
        
        # Other icons
        self.dlg.refreshCatalogButton.setIcon(icons.refresh_icon)
        self.dlg.myImageryDocsButton.setIcon(icons.info_icon)
        
        # Other text
        self.dlg.myImageryDocsButton.setToolTip(self.tr("More about My imagery"))
        self.dlg.filterCatalog.setPlaceholderText(self.tr("Filter mosaics by name or id"))

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
        self.sort_catalog()
        self.filter_catalog_table(self.dlg.filterCatalog.text())

    def sort_catalog(self):
        index = self.dlg.sortCatalogCombo.currentIndex()
        # Define sorting order based on sortCatalogCombo index
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
                elided_tag = self.dlg.catalogInfo.fontMetrics().elidedText(tag, Qt.ElideRight, self.dlg.catalogInfo.width() - 40)
                elided_tags.append(elided_tag)
            tags_str = ', '.join(elided_tags)
        else:
            tags_str = ''
        text = self.tr("Number of images: {count} \n").format(count=len(images))
        if images:
            # Find spatial resolution as the arithmetic mean between resolutions along X and Y axes
            pixel_size = sum(images[0].meta_data.pixel_size)/2
            # If it is less then 1 cm, we assume that CRS is geographic
            if pixel_size < 0.01:
                pixel_size = round(pixel_size, 6) # decimal degrees
            # Otherwise - CRS is most likely projected
            else:
                pixel_size = round(pixel_size, 2) # meters or other units
            text += self.tr("Size: {mosaic_size} \n"
                            "Pixel size: {pixel_size} \n"
                            "CRS: {crs} \n"
                            "Number of bands: {count} \n"
                           ).format(mosaic_size=get_readable_size(mosaic.sizeInBytes),
                                    pixel_size=pixel_size,
                                    crs=images[0].meta_data.crs,
                                    count=images[0].meta_data.count)
        text += self.tr("Created: {date} at {time} \nTags: {tags}"
                       ).format(date=mosaic.created_at.date(), time=mosaic.created_at.strftime('%H:%M'),
                                tags=tags_str)
        self.dlg.catalogInfo.setText(text)
        self.display_image_number(0, len(images))
    
    def display_image_number(self, number: int, count: int):
        if count > 0:
            self.dlg.imageNumberLabel.setText(f"{number+1}/{count}")
        else:
            self.dlg.imageNumberLabel.setVisible(False)

    def enable_mosaic_images_preview(self, images_count: int = 0, preview_idx: int = 0):
        # Hide '<','>' and image number in images table
        if not self.mosaic_table_visible:
            self.dlg.previousImageButton.setVisible(False)
            self.dlg.nextImageButton.setVisible(False)
            self.dlg.imageNumberLabel.setVisible(False)
            return
        # Hide '<' and '>' for empty mosaics
        if images_count == 0:
            self.dlg.previousImageButton.setVisible(False)
            self.dlg.nextImageButton.setVisible(False)
            self.dlg.imageNumberLabel.setVisible(False)
            self.dlg.imagePreview.clear()
            return
        # Show '<','>' and image number
        self.dlg.previousImageButton.setVisible(True)
        self.dlg.nextImageButton.setVisible(True)
        self.dlg.imageNumberLabel.setVisible(True)
        # Disable '>' if it's the last image
        if preview_idx + 1 >= images_count:
            self.dlg.nextImageButton.setEnabled(False)
        else:
            self.dlg.nextImageButton.setEnabled(True)
        # Disable '<' if it's the first image
        if preview_idx <= 0:
            self.dlg.previousImageButton.setEnabled(False)
        else:
            self.dlg.previousImageButton.setEnabled(True)

    def full_image_info(self, image: ImageReturnSchema):
        try:
            # Find spatial resolution as the arithmetic mean between resolutions along X and Y axes
            pixel_size = sum(image.meta_data.pixel_size)/2
            # If it is less then 1 cm, we assume that CRS is geographic
            if pixel_size < 0.01:
                pixel_size = round(pixel_size, 6) # decimal degrees
            # Otherwise - CRS is most likely projected
            else:
                pixel_size = round(pixel_size, 2) # meters or other units
            message = self.tr('<b>Name</b>: {filename}\
                              <br><b>Uploaded</b></br>: {date} at {time}\
                              <br><b>Size</b></br>: {file_size}\
                              <br><b>CRS</b></br>: {crs}\
                              <br><b>Number of bands</br></b>: {bands}\
                              <br><b>Width</br></b>: {width} pixels\
                              <br><b>Height</br></b>: {height} pixels\
                              <br><b>Pixel size</br></b>: {pixel_size}'\
                             ).format(filename=image.filename, 
                                     date=image.uploaded_at.date(),
                                     time=image.uploaded_at.strftime('%H:%M'),
                                     file_size=get_readable_size(image.file_size), 
                                     crs=image.meta_data.crs,
                                     bands=image.meta_data.count,
                                     width=image.meta_data.width,
                                     height=image.meta_data.height,
                                     pixel_size=pixel_size)
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
        self.sort_catalog()
        self.filter_catalog_table(self.dlg.filterCatalog.text())

    def show_preview_s(self, preview_image):
        self.dlg.imagePreview.setPixmap(QPixmap.fromImage(preview_image))
        self.dlg.imagePreview.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

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
        bold_font = self.dlg.catalogSelectionLabel.font()
        bold_font.setBold(True)
        self.dlg.catalogSelectionLabel.setText(self.tr("Selected mosaic: <b>{mosaic_name}").format(
            mosaic_name=QFontMetrics(bold_font).elidedText(mosaic_name,
                                                           Qt.ElideRight,
                                                           self.dlg.catalogSelectionLabel.width() - 10)))
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
        # Find spatial resolution as the arithmetic mean between resolutions along X and Y axes
        pixel_size = sum(image.meta_data.pixel_size)/2
        # If it is less then 1 cm, we assume that CRS is geographic
        if pixel_size < 0.01:
            pixel_size = round(pixel_size, 6) # decimal degrees
        # Otherwise - CRS is most likely projected
        else:
            pixel_size = round(pixel_size, 2) # meters or other units
        self.dlg.catalogInfo.setText(self.tr("Uploaded: {date} at {time} \n"
                                             "File size: {size} \n"
                                             "Pixel size: {pixel_size} \n"
                                             "CRS: {crs} \n"
                                             "Bands: {count}"
                                            ).format(date=image.uploaded_at.date(),
                                                     time=image.uploaded_at.strftime('%H:%M'),
                                                     size=get_readable_size(image.file_size),
                                                     pixel_size=pixel_size,
                                                     crs=image.meta_data.crs,
                                                     count=image.meta_data.count))
        bold_font = self.dlg.catalogSelectionLabel.font()
        bold_font.setBold(True)
        self.dlg.catalogSelectionLabel.setText(self.tr("Selected image: <b>{image_name}").format(
            image_name=QFontMetrics(bold_font).elidedText(image.filename,
                                                          Qt.ElideRight,
                                                          self.dlg.catalogSelectionLabel.width() - 10)))
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
        self.dlg.deleteCatalogButton.setText(self.tr("Delete image"))
        self.dlg.addCatalogButton.setText(self.tr("Add image"))
        self.dlg.addCatalogButton.setMenu(self.upload_image_menu)
        # Allow selection back
        self.dlg.mosaicTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dlg.mosaicTable.setCurrentCell(row, column)
        # Because we open images table always with empty selection
        self.clear_image_info()
        # Set sorting combo text
<<<<<<< HEAD
        self.dlg.sortCombo.setCurrentIndex(self.sort_images_index)
        # Disable '<' and '>' for images table
        self.enable_mosaic_images_preview(0, 0)
        # Set filter and its placeholder text
        self.filter_catalog_table(self.dlg.filterCatalog.text())
        self.dlg.filterCatalog.setPlaceholderText(self.tr("Filter images by name or id"))
=======
        self.dlg.sortCatalogCombo.setCurrentIndex(self.sort_images_index)
>>>>>>> 0979741 (Projects: Refactor, move controls, add sorting)

    def show_mosaics_table(self, selected_mosaic_name: Optional[str]):
        # Save buttons before deleting cells and therefore widgets
        # En(dis)able buttons and change labels
        self.dlg.seeMosaicsButton.setEnabled(False)
        self.dlg.seeImagesButton.setEnabled(True)
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
<<<<<<< HEAD
        self.dlg.sortCombo.setCurrentIndex(self.sort_mosaics_index)
        # Set filter and its placeholder text
        self.filter_catalog_table(self.dlg.filterCatalog.text())
        self.dlg.filterCatalog.setPlaceholderText(self.tr("Filter mosaics by name or id"))
=======
        self.dlg.sortCatalogCombo.setCurrentIndex(self.sort_mosaics_index)
>>>>>>> 0979741 (Projects: Refactor, move controls, add sorting)

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

    def filter_catalog_table(self, name_filter: str = None):
        if self.mosaic_table_visible:
            table = self.dlg.mosaicTable
        else:
            table = self.dlg.imageTable
        for row in range(table.rowCount()):
            item_id = table.item(row, 0).data(Qt.DisplayRole)
            item_name = table.item(row, 1).data(Qt.DisplayRole)
            hide = bool(name_filter) and ((name_filter.lower() not in item_id.lower() and name_filter.lower() not in item_name.lower()))
            table.setRowHidden(row, hide)
        
    def alert(self, message: str, icon: QMessageBox.Icon = QMessageBox.Critical, blocking=True) -> None:
        """A duplicate of alert function from mapflow.py to avoid circular import.
        """
        box = QMessageBox(icon, "Mapflow", message, parent=QApplication.activeWindow())
        box.setTextFormat(Qt.RichText)
        if icon == QMessageBox.Question:  # by default, only OK is added
            box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        return box.exec() == QMessageBox.Ok if blocking else box.open()
