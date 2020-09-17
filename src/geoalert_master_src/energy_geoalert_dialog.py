# -*- coding: utf-8 -*-

import os
from PyQt5 import uic
from PyQt5 import QtWidgets
from qgis.core import QgsMapLayerProxyModel

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'energy_geoalert_dialog_base.ui'))

class EnergyGeoalertDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(EnergyGeoalertDialog, self).__init__(parent)
        self.setupUi(self)

        # комбобокс с выбором слоев
        self.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.PolygonLayer) #фильтр полигональных полей
        #self.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.HasGeometry) #фильтр векторных слоев
        self.vectorComboBox.setFilters(QgsMapLayerProxyModel.PointLayer) #фильтр точечных слоев
        self.vectorComboBox_2.setFilters(QgsMapLayerProxyModel.PointLayer)  # фильтр точечных слоев
        self.MapLay_CB_2.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.MapLay_CB_3.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.MapLay_CB.setFilters(QgsMapLayerProxyModel.PolygonLayer)