from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QDialogButtonBox

from ..entity.processing import Processing
from ..schema.processing import UpdateProcessingSchema
from .dialogs import ui_path, plugin_icon

class UpdateProcessingDialog(*uic.loadUiType(ui_path/'processing_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """A dialog for adding or editing an imagery provider."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.ok = self.buttonBox.button(QDialogButtonBox.Ok)

        self.processingName.textChanged.connect(self.on_name_change)

    def on_name_change(self):
        if not self.processingName.text():
            self.ok.setEnabled(False)
            self.ok.setToolTip(self.tr("Processing name must not be empty!"))
        else:
            self.ok.setEnabled(True)
            self.ok.setToolTip("")

    def setup(self, processing: Processing):
        if not processing:
            raise TypeError("Can edit only existing processing!")
        self.setWindowTitle(self.tr("Edit processing {}").format(processing.name))
        self.processingName.setText(processing.name)
        self.processingDescription.setText(processing.description or "")
        self.exec()

    def processing(self):
        if not self.processingName.text():
            raise AssertionError("Processing name must not be empty!")
        return UpdateProcessingSchema(name = self.processingName.text(),
                                      description = self.processingDescription.text() or None)
