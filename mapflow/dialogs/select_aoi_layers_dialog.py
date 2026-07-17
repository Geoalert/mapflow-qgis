from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QAbstractItemView, QListWidgetItem


ui_path = Path(__file__).parent / 'static' / 'ui'


class SelectAoiLayersDialog(*uic.loadUiType(ui_path / 'raster_layers_dialog.ui')):
    """Pick one or more polygon vector layers to add as template AOIs.

    Reuses the raster-upload dialog's list UI (a multi-select list + OK/Cancel), but lists
    vector layers and returns their ids (so the caller can read each layer's features)."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupUi(self)

    def setup(self, layers):
        self.setWindowTitle(self.tr("Choose polygon layers to add as AOIs"))
        self.listWidget.clear()
        for layer in layers:
            item = QListWidgetItem(layer.name())
            item.setData(Qt.UserRole, layer.id())
            self.listWidget.addItem(item)
        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def selected_layer_ids(self):
        return [item.data(Qt.UserRole) for item in self.listWidget.selectedItems()]
