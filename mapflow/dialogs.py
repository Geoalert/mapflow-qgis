from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget
from qgis.core import QgsMapLayerProxyModel, QgsProviderRegistry


class MainDialog(*uic.loadUiType(Path(__file__).parent/'main_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Constructor."""
        super().__init__(parent)
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


class LoginDialog(*uic.loadUiType(Path(__file__).parent/'login_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Constructor."""
        super().__init__(parent)
        self.setupUi(self)
        self.cancelButton.clicked.connect(self.reject)
        self.loginButton.clicked.connect(self.accept)


class CustomProviderDialog(*uic.loadUiType(Path(__file__).parent/'custom_provider_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Constructor."""
        super().__init__(parent)
        self.setupUi(self)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.rejected.connect(lambda: self.name.setStyleSheet(''))
        self.buttonBox.rejected.connect(lambda: self.url.setStyleSheet(''))
        self.buttonBox.rejected.connect(lambda: self.name.setText(''))
        self.buttonBox.rejected.connect(lambda: self.url.setText(''))
