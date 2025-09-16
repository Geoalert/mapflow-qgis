from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QDialogButtonBox

from ..schema.data_catalog import ImageReturnSchema
from .processing_dialog import ui_path, plugin_icon

class RenameImageDialog(*uic.loadUiType(ui_path/'image_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """A dialog for adding or editing mosaics"""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.ok = self.buttonBox.button(QDialogButtonBox.Ok)
        self.imageName.textChanged.connect(self.on_name_change)

    def setup(self, image: ImageReturnSchema):
        if not image:
            raise TypeError(self.tr("Dialog requires current image"))
        self.setWindowTitle(self.tr("Rename image {}").format(image.filename))
        self.imageName.setText(image.filename)
        self.setFixedHeight(self.sizeHint().height())
        self.exec()

    def on_name_change(self):
        if not self.imageName.text():
            self.ok.setEnabled(False)
            self.ok.setToolTip(self.tr("Image name must not be empty!"))
        else:
            self.ok.setEnabled(True)
            self.ok.setToolTip("")

    def image(self):
        if not self.imageName.text():
            raise AssertionError(self.tr("Image name must not be empty!"))
        return self.imageName.text()
