from typing import Optional

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QDialogButtonBox

from .dialogs import ui_path, plugin_icon
from ..entity.provider import (CRS,
                               BasicAuth,
                               Provider,
                               XYZProvider,
                               TMSProvider,
                               QuadkeyProvider,
                               MaxarProvider)
from ..functional.helpers import QUAD_KEY_REGEX, XYZ_REGEX, MAXAR_PROVIDER_REGEX


class ProviderDialog(*uic.loadUiType(ui_path/'provider_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """A dialog for adding or editing an imagery provider."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        ok = self.buttonBox.button(QDialogButtonBox.Ok)
        ok.setEnabled(False)

        self.type.currentTextChanged.connect(self.on_type_change)
        self.name.textChanged.connect(lambda: ok.setEnabled(self.validate_and_create_provider()))
        self.url.textChanged.connect(lambda: ok.setEnabled(self.validate_and_create_provider()))
        self.login.textChanged.connect(lambda: ok.setEnabled(self.validate_and_create_provider()))
        self.password.textChanged.connect(lambda: ok.setEnabled(self.validate_and_create_provider()))
        self.crs.currentTextChanged.connect(lambda: ok.setEnabled(self.validate_and_create_provider()))
        self.save_credentials.toggled.connect(lambda: ok.setEnabled(self.validate_and_create_provider()))

        # we store here the provider that we are editing right now
        self.current_provider = None
        self.result = None

    def setup(self, provider: Optional[Provider] = None, title: str = ''):
        self.current_provider = provider
        self.result = None

        if provider:
            name = provider.name
            url = provider.url
            source_type = provider.option_name
            crs = provider.crs
            title = name
            login = provider.credentials.login
            password = provider.credentials.password
            save_credentials = provider.save_credentials
        else:
            name = ""
            url = ""
            source_type = "xyz"
            crs = CRS.web_mercator
            title = title
            login = ""
            password = ""
            save_credentials = False


        # Fill out the edit dialog with the current data
        self.setWindowTitle(title)
        self.type.setCurrentText(source_type)
        self.name.setText(name)
        self.url.setText(url)
        self.crs.setCurrentText(crs.value)
        self.login.setText(login)
        self.password.setText(password)
        self.save_credentials.setChecked(save_credentials)

        self.show()

    def on_type_change(self):
        if self.type.currentText == MaxarProvider.option_name:
            self.crs.setCurrentText('EPSG:3857')
            self.crs.setDisabled(True)
        else:  # ['xyz', 'tms', 'quadkey']
            self.url.setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(self.validate_and_create_provider())

    def validate_and_create_provider(self):
        name = self.name.text()
        url = self.url.text()
        source_type = self.type.currentText()
        crs = self.crs.currentText()
        login = self.login.text()
        password = self.password.text()
        save_credentials = self.save_credentials.isChecked()

        res = False
        if name and url:  # non-empty
            if source_type in (TMSProvider.option_name, XYZProvider.option_name):
                res = bool(XYZ_REGEX.match(url))
            elif source_type == QuadkeyProvider.option_name:
                res = bool(QUAD_KEY_REGEX.match(url))
            elif source_type == MaxarProvider.option_name:
                res = bool(MAXAR_PROVIDER_REGEX.match(url)) and bool(login) and bool(password)
            else:
                raise AssertionError("Unexpected source type")
        if res:
            self.result = dict(option_name=source_type,
                               name=name,
                               url=url,
                               crs=crs,
                               credentials=BasicAuth(login, password),
                               save_credentials=save_credentials)

        else:
            self.result = None
        return res
