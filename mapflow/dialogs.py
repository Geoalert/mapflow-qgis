from typing import Optional
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialogButtonBox, QWidget
from qgis.core import QgsMapLayerProxyModel

from .entity.provider import SourceType, CRS, Provider
from .helpers import QUAD_KEY_REGEX, XYZ_REGEX, UUID_REGEX

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
        self.name.textChanged.connect(lambda: ok.setEnabled(self.validate_provider_form()))
        self.url.textChanged.connect(lambda: ok.setEnabled(self.validate_provider_form()))
        self.type.currentTextChanged.connect(lambda: ok.setEnabled(self.validate_provider_form()))
        self.finished.connect(self.name.clear)
        self.finished.connect(self.url.clear)
        # we store here the provider that we are editing right now
        self.current_provider = None
        self.result_provider = None

    def setup(self, provider: Optional[Provider] = None):
        self.current_provider = provider
        self.result_provider = None
        if provider:
            name = provider.name
            url = provider.url
            source_type = provider.source_type
            crs = provider.crs
            self.setWindowTitle(name)
        else:
            name = ""
            url = ""
            source_type = SourceType.xyz
            crs = CRS.web_mercator
            self.setWindowTitle("Add new provider")

        # Fill out the edit dialog with the current data
        self.name.setText(name)
        self.url.setText(url)
        self.type.setCurrentText(source_type.value)
        self.crs.setCurrentText(crs.value)
        self.show()

    def validate_provider_form(self):
        name = self.name.text()
        url = self.url.text()
        source_type = self.type.currentText()
        crs = self.crs.currentText()
        res = False
        if name and url:  # non-empty
            if SourceType(source_type) in (SourceType.xyz, SourceType.tms):
                res = bool(XYZ_REGEX.match(url))
            elif SourceType(source_type) == SourceType.quadkey:
                res = bool(QUAD_KEY_REGEX.match(url))
            else:
                raise AssertionError("Unexpected source type")
        if res:
            self.result_provider = Provider(name=name, url=url, source_type=source_type, crs=crs)
        else:
            self.result_provider = None
        return res


class ConnectIdDialog(*uic.loadUiType(ui_path/'connect_id_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Constructor."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        ok = self.buttonBox.button(QDialogButtonBox.Ok)
        self.connectId.textChanged.connect(
            lambda text: ok.setEnabled(bool(UUID_REGEX.match(text)) or not(text))
        )

    def setup(self, product, current_connect_id):
        self.connectId.setEnabled(current_connect_id is not None)
        if current_connect_id is None:
            self.setWindowTitle(self.tr('Current provider does not support ConnectID'))
        else:
            self.setWindowTitle(f'Connect ID - {product}')
        self.connectId.setText(current_connect_id)
        self.connectId.setCursorPosition(0)
        self.show()


class SentinelAuthDialog(*uic.loadUiType(ui_path/'sentinel_auth_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Constructor."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)

    def setup(self, api_key):
        self.apiKey.setText(api_key)
        self.show()


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
