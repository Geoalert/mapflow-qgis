from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QWidget
from qgis.core import QgsMapLayerProxyModel, QgsProviderRegistry
from qgis.utils import iface


MAIN_WINDOW = iface.mainWindow()
MAIN_DIALOG_FORM = uic.loadUiType(Path(__file__).parent/'main_dialog.ui')[0]
LOGIN_DIALOG_FORM = uic.loadUiType(Path(__file__).parent/'login_dialog.ui')[0]


class MainDialog(QDialog, MAIN_DIALOG_FORM):
    def __init__(self, parent: QWidget = MAIN_WINDOW):
        """Constructor."""
        super(MainDialog, self).__init__(parent)
        self.setupUi(self)
        # Adjust column width in processings table
        for index, width in enumerate((95, 145, 75, 140, 100, 120)):
            self.processingsTable.setColumnWidth(index, width)
        # Restrict the combo boxes to their relevant layer types
        self.maxarAOICombo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.polygonCombo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.rasterCombo.setFilters(QgsMapLayerProxyModel.RasterLayer)
        # Restrict the raster combo to GDAL. This won't itself narrow it down to GeoTIFF alone
        # But it'll filter out other admittedly irrelevant providers
        excluded_providers = QgsProviderRegistry.instance().providerList()
        excluded_providers.remove('gdal')
        self.rasterCombo.setExcludedProviders(excluded_providers)
        # Add the 'virtual' raster layers
        self.rasterCombo.setAdditionalItems(('Mapbox Satellite', 'Custom URL (in Settings)'))


class LoginDialog(QDialog, LOGIN_DIALOG_FORM):
    def __init__(self, parent: QWidget = MAIN_WINDOW):
        """Constructor."""
        super(LoginDialog, self).__init__(parent)
        self.setupUi(self)
        self.cancelButton.clicked.connect(self.reject)
        self.loginButton.clicked.connect(self.accept)
