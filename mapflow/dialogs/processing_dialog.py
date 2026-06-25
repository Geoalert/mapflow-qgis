from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QDialogButtonBox

# Re-exported for other dialogs (image_dialog, processing_details_dialog) that do
# `from .processing_dialog import plugin_icon`. The redundant alias marks it as an
# intentional re-export so ruff won't strip it as unused.
from .icons import plugin_icon as plugin_icon
from ..schema.processing import UpdateProcessingSchema, ProcessingDTO

ui_path = Path(__file__).parent/'static'/'ui'

class UpdateProcessingDialog(*uic.loadUiType(ui_path/'processing_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """A dialog for adding or editing an imagery provider."""
        super().__init__(parent)
        self.setupUi(self)
        self.ok = self.buttonBox.button(QDialogButtonBox.Ok)

        self.processingName.textChanged.connect(self.on_name_change)

    def on_name_change(self):
        if not self.processingName.text():
            self.ok.setEnabled(False)
            self.ok.setToolTip(self.tr("Processing name must not be empty!"))
        else:
            self.ok.setEnabled(True)
            self.ok.setToolTip("")

    def setup(self, processing: ProcessingDTO):
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
