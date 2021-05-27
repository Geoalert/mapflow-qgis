from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
from qgis.core import QgsMapLayerProxyModel
from qgis.utils import iface


mainWindow = iface.mainWindow()
MainDialogForm = uic.loadUiType(Path(__file__).parent/'main_dialog.ui')[0]
LoginDialogForm = uic.loadUiType(Path(__file__).parent/'login_dialog.ui')[0]


class MainDialog(QDialog, MainDialogForm):
    def __init__(self, parent=mainWindow):
        """Constructor."""
        super(MainDialog, self).__init__(parent)
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


class LoginDialog(QDialog, LoginDialogForm):
    def __init__(self, parent=mainWindow):
        """Constructor."""
        super(LoginDialog, self).__init__(parent)
        self.setupUi(self)
        self.cancelButton.clicked.connect(self.reject)
        self.loginButton.clicked.connect(self.accept)
