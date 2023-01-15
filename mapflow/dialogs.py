from . import helpers
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
        self.maxarAoiCombo.setFilters(QgsMapLayerProxyModel.PolygonLayer)
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
        ok = self.buttonBox.button(QDialogButtonBox.Ok)
        ok.setEnabled(False)
        self.name.textChanged.connect(lambda: ok.setEnabled(helpers.validate_provider_form(self)))
        self.url.textChanged.connect(lambda: ok.setEnabled(helpers.validate_provider_form(self)))
        self.type.currentTextChanged.connect(lambda: ok.setEnabled(helpers.validate_provider_form(self)))
        self.finished.connect(self.name.clear)
        self.finished.connect(self.url.clear)


class ConnectIdDialog(*uic.loadUiType(ui_path/'connect_id_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Constructor."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        ok = self.buttonBox.button(QDialogButtonBox.Ok)
        self.connectId.textChanged.connect(
            lambda text: ok.setEnabled(bool(helpers.UUID_REGEX.match(text)) or not(text))
        )


class SentinelAuthDialog(*uic.loadUiType(ui_path/'sentinel_auth_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Constructor."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)


class ErrorMessage(*uic.loadUiType(ui_path/'error_message.ui')):
    def __init__(self,  parent: QWidget, text: str, title: str = None, email_body: str = '') -> None:
        """An message box notifying user about a plugin error, with a 'Send a report' button."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.text.setText(text)
        if title:
            self.title.setText(title)
        self.mailTo.setText(
            '<html><head/><body><p><a href="mailto:help@geoalert.io?subject=Mapflow-QGIS&body=' +
            email_body +
            '"><span style=" text-decoration: underline; color:#0057ae;">Let us know</span></a></p></body></html>'
        )


class CreateCatalogDialog(*uic.loadUiType(ui_path/'create_new_catalog_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)


class UpdateCatalogDialog(*uic.loadUiType(ui_path/'update_catalog_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)


class CreateCatalogAndFileUpload(*uic.loadUiType(ui_path/'create_catalog_upload_file_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)


class UploadImageToExistingMosaic(*uic.loadUiType(ui_path/'upload_image_to_existing_mosaic_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
