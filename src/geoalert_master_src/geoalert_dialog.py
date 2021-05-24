from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from qgis.core import QgsMapLayerProxyModel
from qgis.utils import iface


FORM_CLASS = uic.loadUiType(Path(__file__).parent/'geoalert_dialog_base.ui')[0]


class GeoalertDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=iface.mainWindow()):
        """Constructor."""
        super(GeoalertDialog, self).__init__(parent)
        self.setupUi(self)
        # Adjust column width in processings table
        for index, width in enumerate((95, 145, 75, 140, 100, 120)):
            self.processingsTable.setColumnWidth(index, width)
        # Or else let the widget resize the columns automatically
        # self.dlg.processingsTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # комбобокс с выбором слоев
        # self.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.PolygonLayer) #фильтр полигональных слоев
        self.VMapLayerComboBox.setFilters(QgsMapLayerProxyModel.HasGeometry)  # фильтр векторных слоев
        # self.vectorComboBox.setFilters(QgsMapLayerProxyModel.PointLayer) #фильтр точечных слоев
