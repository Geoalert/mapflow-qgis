from typing import List

from ...dialogs.main_dialog import MainDialog
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QWidget, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QMessageBox, QApplication
from PyQt5.QtGui import QPixmap

from ...schema.data_catalog import MosaicReturnSchema, ImageReturnSchema


class DataCatalogView(QObject):
    def __init__(self, dlg: MainDialog):
        super().__init__()
        self.dlg = dlg
        # First column is ID, hidden; second is name
        self.dlg.mosaicTable.setColumnCount(2)
        self.dlg.mosaicTable.setColumnHidden(0, True)

    def display_mosaics(self, mosaics: list[MosaicReturnSchema]):
        self.dlg.mosaicTable.setRowCount(len(mosaics))
        self.dlg.mosaicTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, mosaic in enumerate(mosaics):
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, mosaic.id)
            self.dlg.mosaicTable.setItem(row, 0, id_item)
            name_item = QTableWidgetItem()
            name_item.setData(Qt.DisplayRole, mosaic.name)
            self.dlg.mosaicTable.setItem(row, 1, name_item)
            self.dlg.mosaicTable.setHorizontalHeaderLabels(["ID", "Mosaic"])
        
    def display_mosaic_info(self, mosaic: MosaicReturnSchema):
        if not mosaic:
            return
        if mosaic.tags:
            tags_str = ', '.join(mosaic.tags)
        else:
            tags_str = ''
        self.dlg.mosaicInfo.setText("ID: {id} \n"
                                    "created {date} at {h}:{m} \n"
                                    "tags: {tags}".format(id=mosaic.id,
                                                          date=mosaic.created_at.date(),
                                                          h=mosaic.created_at.hour,
                                                          m=mosaic.created_at.minute,
                                                          tags=tags_str))

    def display_image_info(self, image: ImageReturnSchema):
        if not image:
            return
        self.dlg.imageDetails.setText("created {date} at {h}:{m} \n"
                                      "bands: {count} \n"
                                      "pixel size: {pixel_size}"
                                      .format(date=image.uploaded_at.date(),
                                              h=image.uploaded_at.hour,
                                              m=image.uploaded_at.minute,
                                              count=list(image.meta_data.values())[1],
                                              pixel_size=round(sum(list(image.meta_data.values())[6])/len(list(image.meta_data.values())[6]), 2)))

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
        self.dlg.imageTable.setHorizontalHeaderLabels(["Image"])
        if len(images) == 0:
            self.dlg.previewMosaicButton.setEnabled(False)
        else:
            self.dlg.previewMosaicButton.setEnabled(True)

    def show_preview_s(self, preview_image):
        self.dlg.imagePreview.setPixmap(QPixmap.fromImage(preview_image))

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
        self.dlg.dataLimit.setText("Your data: {taken} MB. Free space: {free} MB".format(taken=round(taken_storage/1048576, 1), 
                                                                                         free=round(free_storage/1048576, 1)))
