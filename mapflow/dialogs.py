from pathlib import Path

from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialogButtonBox, QWidget
from qgis.core import QgsMapLayerProxyModel


ui_path = Path(__file__).parent/'static'/'ui'
icon_path = Path(__file__).parent/'static'/'icons'
plugin_icon = QIcon(str(icon_path/'mapflow.png'))


class MainDialog(*uic.loadUiType(ui_path/'main_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Plugin's main dialog."""
        super().__init__(parent)
        self.setupUi(self)
        # Restrict combos to relevant layer types; QGIS 3.10-3.20 (at least) bugs up if set in .ui
        self.maxarAOICombo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.polygonCombo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.rasterCombo.setFilters(QgsMapLayerProxyModel.RasterLayer)
        # Set icons (can be done in .ui but brings about the resources_rc import bug)
        self.setWindowIcon(plugin_icon)
        self.addProvider.setIcon(QIcon(str(icon_path/'add_provider.svg')))
        self.removeProvider.setIcon(QIcon(str(icon_path/'remove_provider.svg')))
        self.editProvider.setIcon(QIcon(str(icon_path/'edit_provider.svg')))


class LoginDialog(*uic.loadUiType(ui_path/'login_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Auth dialog."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)


class ProviderDialog(*uic.loadUiType(ui_path/'provider_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """A dialog for adding or editing an imagery provider."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        ok_button.setEnabled(False)
        self.name.textChanged.connect(lambda text: ok_button.setEnabled(bool(text and self.url.text())))
        self.url.textChanged.connect(lambda text: ok_button.setEnabled(bool(text and self.name.text())))
        self.finished.connect(self.name.clear)
        self.finished.connect(self.url.clear)


class ConnectIdDialog(*uic.loadUiType(ui_path/'connect_id_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Constructor."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.connectId.textChanged.connect(
            lambda: self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(self.connectId.hasAcceptableInput())
        )


class ErrorMessage(*uic.loadUiType(ui_path/'error_message.ui')):
    def __init__(self, text: str, parent: QWidget) -> None:
        """An message box notifying user about a plugin error, with a 'Send a report' button."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.text.setText(text)
