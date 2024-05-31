from typing import List

from ...dialogs.main_dialog import MainDialog
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QWidget, QPushButton, QComboBox, QTableWidgetItem
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
        for row, mosaic in enumerate(mosaics):
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, mosaic.id)
            self.dlg.mosaicTable.setItem(row, 0, id_item)
            name_item = QTableWidgetItem()
            name_item.setData(Qt.DisplayRole, mosaic.name)
            self.dlg.mosaicTable.setItem(row, 1, name_item)

    def display_mosaic_info(self, mosaic: MosaicReturnSchema):
        if not mosaic:
            return
        self.dlg.mosaicInfo.setText("ID: {id} \n"
                                    "created at {created} \n"
                                    "tags: {tags}".format(id=mosaic.id,
                                                          created=mosaic.created_at,
                                                          tags=", ".join(mosaic.tags)))

    def display_images(self, images: list[ImageReturnSchema]):
        self.dlg.imageTable.setRowCount(len(images))
        self.dlg.imageTable.setColumnCount(1)
        for row, image in enumerate(images):
            table_item = QTableWidgetItem()
            table_item.setData(Qt.DisplayRole, image.id)
            self.dlg.imageTable.setItem(row, 0, table_item)

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

