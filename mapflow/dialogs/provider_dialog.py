from typing import Optional

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QDialogButtonBox

from .dialogs import ui_path, plugin_icon
from ..entity.provider.provider import SourceType, CRS, Provider
from ..helpers import QUAD_KEY_REGEX, XYZ_REGEX, MAXAR_PROVIDER_REGEX

MAXAR_PROVIDER_NAME = "Maxar WMTS"


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

    def on_type_change(self):
        if self.type.currentText == MAXAR_PROVIDER_NAME:
            self.crs.setCurrentText('EPSG:3857')
            self.crs.setDisabled()
        else:  # ['xyz', 'tms', 'quadkey']
            self.url.setEnabled()
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(self.validate_provider_form())

    def validate_provider_form(self):
        name = self.name.text()
        url = self.url.text()
        source_type = self.type.currentText()
        crs = self.crs.currentText()
        login = self.login.text()
        password = self.password.text()

        res = False
        if name and url:  # non-empty
            if SourceType(source_type) in (SourceType.xyz, SourceType.tms):
                res = bool(XYZ_REGEX.match(url))
            elif SourceType(source_type) == SourceType.quadkey:
                res = bool(QUAD_KEY_REGEX.match(url))
            elif source_type == MAXAR_PROVIDER_NAME:
                res = bool(MAXAR_PROVIDER_REGEX.match(url)) and bool(login) and bool(password)
            else:
                raise AssertionError("Unexpected source type")
        if res:
            self.result_provider = Provider(name=name, url=url, source_type=source_type, crs=crs)
        else:
            self.result_provider = None
        return res
