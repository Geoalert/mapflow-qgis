from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget

from .icons import plugin_icon

ui_path = Path(__file__).parent/'static'/'ui'

class ConfirmProcessingStartDialog(*uic.loadUiType(ui_path / 'processing_start_confirmation.ui')):
    def __init__(self, parent: QWidget) -> None:
        """A confirmation dialog for processing start with 'don't show again' checkbox, connected to Settings tab."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.setWindowTitle(self.tr("Confirm processing start"))
    
    def setup(self, name, price, provider, zoom, area, model, blocks) -> None:
        elided_name = self.modelLabel.fontMetrics().elidedText(name, Qt.ElideRight, self.nameLabel.width() + 100)
        self.nameLabel.setText(elided_name)
        if price is not None:
            self.priceHeader.setVisible(True)
            self.priceLabel.setVisible(True)
            self.priceLabel.setText(price)
        else:
            self.priceHeader.setVisible(False)
            self.priceLabel.setVisible(False)
        elided_provider = self.dataSourceLabel.fontMetrics().elidedText(provider, Qt.ElideRight, self.modelLabel.width() + 150)
        self.dataSourceLabel.setText(elided_provider)
        if not zoom:
            zoom = self.tr("No zoom selected")
        self.zoomLabel.setText(zoom)
        self.areaLabel.setText(area)
        elided_model = self.modelLabel.fontMetrics().elidedText(model, Qt.ElideRight, self.modelLabel.width() + 100)
        self.modelLabel.setText(elided_model)
        if len(blocks) == 0:
            blocks = [self.tr("No options selected")]
        else:
            blocks = [block.text() for block in blocks if block.isChecked()]
        self.modelOptionsLabel.setText(', \n'.join(blocks))
        self.exec()
