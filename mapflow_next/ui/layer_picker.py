"""Choose the project's GeoTIFF layers to upload to My imagery: one or several at once."""
from __future__ import annotations

from typing import List, Tuple

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAbstractItemView, QDialog, QHBoxLayout, QListWidget, QListWidgetItem, QVBoxLayout

from .theme import stylesheet
from .widgets import button, label


class LayerPicker(QDialog):
    def __init__(self, layers: List[Tuple[str, str]], parent=None):
        """`layers`: (layer id, name) of the GeoTIFF layers to choose from."""
        super().__init__(parent)
        self.setObjectName("mfRoot")
        self.setWindowTitle("Upload raster layers")
        self.setStyleSheet(stylesheet())
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(8)
        layout.addWidget(label("Upload raster layers", "h2"))
        layout.addWidget(label("Only GeoTIFF file layers can be uploaded. Ctrl or Shift selects several."
                               if layers else "No GeoTIFF layers in the project", "meta", wrap=True))
        self.list = QListWidget(self)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        for layer_id, name in layers:
            item = QListWidgetItem(name, self.list)
            item.setData(Qt.ItemDataRole.UserRole, layer_id)
        self.list.setVisible(bool(layers))
        layout.addWidget(self.list)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = button("Cancel", "ghost")
        cancel.clicked.connect(lambda *_: self.reject())
        self.upload = button("Upload", "primary")
        self.upload.clicked.connect(lambda *_: self.accept())
        self.upload.setDefault(True)
        self.upload.setEnabled(False)
        self.list.itemSelectionChanged.connect(lambda: self.upload.setEnabled(bool(self.list.selectedItems())))
        if layers:
            self.list.setCurrentRow(0)
        buttons.addWidget(cancel)
        buttons.addWidget(self.upload)
        layout.addSpacing(6)
        layout.addLayout(buttons)

    def chosen(self) -> List[str]:
        """The selected layers' ids, in the list's order."""
        return [self.list.item(row).data(Qt.ItemDataRole.UserRole) for row in range(self.list.count())
                if self.list.item(row).isSelected()]


def pick_layers(layers: List[Tuple[str, str]], parent=None) -> List[str]:
    dialog = LayerPicker(layers, parent)
    return dialog.chosen() if dialog.exec() else []
