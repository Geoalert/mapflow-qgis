from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QHeaderView
from qgis.core import QgsMapLayerProxyModel


ui_path = Path(__file__).parent/'static'/'ui'


class MainDialog(*uic.loadUiType(ui_path/'main_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Constructor."""
        super().__init__(parent)
        self.setupUi(self)
        # Restrict combos to relevant layer types; QGIS 3.10-3.20 (at least) bugs up if set in .ui
        self.maxarAOICombo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.polygonCombo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.rasterCombo.setFilters(QgsMapLayerProxyModel.RasterLayer)


class LoginDialog(*uic.loadUiType(ui_path/'login_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Constructor."""
        super().__init__(parent)
        self.setupUi(self)


class CustomProviderDialog(*uic.loadUiType(ui_path/'custom_provider_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Constructor."""
        super().__init__(parent)
        self.setupUi(self)


class ConnectIdDialog(*uic.loadUiType(ui_path/'connect_id_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Constructor."""
        super().__init__(parent)
        self.setupUi(self)
