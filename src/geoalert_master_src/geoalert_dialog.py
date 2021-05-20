# -*- coding: utf-8 -*-

import os
from PyQt5 import uic
from PyQt5 import QtWidgets
from qgis.core import QgsMapLayerProxyModel

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'geoalert_dialog_base.ui'))


class GeoalertDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(GeoalertDialog, self).__init__(parent)
        self.setupUi(self)

        # комбобокс с выбором слоев
        # self.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.PolygonLayer) #фильтр полигональных слоев
        self.VMapLayerComboBox.setFilters(QgsMapLayerProxyModel.HasGeometry)  # фильтр векторных слоев
        # self.vectorComboBox.setFilters(QgsMapLayerProxyModel.PointLayer) #фильтр точечных слоев
