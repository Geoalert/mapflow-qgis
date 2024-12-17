from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QDialogButtonBox

from ..schema.data_catalog import MosaicCreateSchema, MosaicUpdateSchema, MosaicReturnSchema
from .dialogs import ui_path, plugin_icon

class MosaicDialog(*uic.loadUiType(ui_path/'mosaic_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """A dialog for adding or editing mosaics"""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.ok = self.buttonBox.button(QDialogButtonBox.Ok)

        self.mosaicName.textChanged.connect(self.on_name_change)

    def on_name_change(self):
        if not self.mosaicName.text():
            self.ok.setEnabled(False)
            self.ok.setToolTip(self.tr("Mosaic name must not be empty!"))
        else:
            self.ok.setEnabled(True)
            self.ok.setToolTip("")

class CreateMosaicDialog(MosaicDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.ok.setEnabled(False)

    def setup(self):
        self.setWindowTitle("")
        self.mosaicName.setText("")
        self.mosaicTags.setText("")
        self.exec()

    def mosaic(self):
        if not self.mosaicName:
            raise AssertionError(self.tr("Mosaic name must not be empty!"))
        tags_list = self.mosaicTags.text().split(", ") if self.mosaicTags.text() else None
        return MosaicUpdateSchema(name = self.mosaicName.text(),
                                  tags = tags_list if self.mosaicTags.text() else [])

class UpdateMosaicDialog(MosaicDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.ok.setEnabled(True)

    def setup(self, mosaic: MosaicReturnSchema):
        if not mosaic:
            raise TypeError(self.tr("UpdateMosaicDialog requires a mosaic to update"))
        self.setWindowTitle(self.tr("Edit mosaic {}").format(mosaic.name))
        self.mosaicName.setText(mosaic.name)
        if mosaic.tags:
            self.mosaicTags.setText(", ".join(mosaic.tags))
        else:
            self.mosaicTags.setText("")
        self.exec()

    def mosaic(self):
        if not self.mosaicName:
            raise AssertionError(self.tr("Mosaic name must not be empty!"))
        tags_list = self.mosaicTags.text().split(", ") if self.mosaicTags.text() else None
        return MosaicUpdateSchema(name = self.mosaicName.text(),
                                  tags = tags_list if self.mosaicTags.text() else [])
