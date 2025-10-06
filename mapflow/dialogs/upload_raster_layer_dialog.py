from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QAbstractItemView, QListWidgetItem

from .icons import plugin_icon

ui_path = Path(__file__).parent/'static'/'ui'

class UploadRasterLayersDialog(*uic.loadUiType(ui_path / 'raster_layers_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Dialog for choosing raster layer(s) when uploading image to mosaic."""
        super().__init__(parent)
        self.setupUi(self)
        
    def setup(self, layers):
        self.setWindowTitle(self.tr("Choose raster layers to upload to imagery collection"))
        for layer in layers:
            item_to_add = QListWidgetItem()
            item_to_add.setText(layer.name())
            item_to_add.setData(Qt.UserRole, layer.source()) 
            self.listWidget.addItem(item_to_add)
        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)    
        self.exec() 

    def get_selected_rasters_list(self, callback):
        # Get selected layers' paths
        layers_paths = []
        for item in self.listWidget.selectedItems():
            layers_paths.append(item.data(Qt.UserRole))
        # Run service.upload_raster_layers_to_mosaic
        callback(layers_paths)
        