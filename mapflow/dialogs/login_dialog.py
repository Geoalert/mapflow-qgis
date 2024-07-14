from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget

from .icons import plugin_icon

ui_path = Path(__file__).parent/'static'/'ui'


class MapflowLoginDialog(*uic.loadUiType(ui_path / 'login_dialog.ui')):
    def __init__(self, parent: QWidget, use_oauth: bool = False, token: str = "") -> None:
        """Auth dialog."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.use_oauth = use_oauth
        self.set_auth_type(self.use_oauth, token)
        self.invalidToken.setVisible(False)
        self.useOauth.setChecked(use_oauth)

    def token_value(self):
        if not self.use_oauth:
            return self.token.text().strip()
        else:
            return None

    def set_auth_type(self, use_oauth: bool = False, token: str = ""):
        self.use_oauth = use_oauth
        self.invalidToken.setVisible(False)
        if use_oauth:
            self.needAnAccount.setText(self.tr('<html><head/><body><p>You will be redirecrted to web browser <br/>to enter your Mapflow login and password</p></body></html>'))
            self.invalidToken.setText(self.tr('<html><head/><body><p><span style=" color:#ff0000;">Authorization is not completed! </span></p><p>'
                                              '<br/>1. Complete authorization in browser. <br/>'
                                              '<br/>2. If it does not help, restart QGIS. '
                                              '<br/><a href="https://docs.mapflow.ai/api/qgis_mapflow.html#oauth2_setup"><span style=" text-decoration: underline; color:#094fd1;">See documentation for help </span></a></p></body></html>'))
        else:  # basic
            self.needAnAccount.setText(self.tr('<html><head/><body><p><a href="https://app.mapflow.ai/account/api"><span style=" text-decoration: underline; color:#0057ae;">Get token</span></a></p><p><a href="https://mapflow.ai/terms-of-use-en.pdf"><span style=" text-decoration: underline; color:#0057ae;">Terms of use</span></a></p><p>Register at <a href="https://mapflow.ai"><span style=" text-decoration: underline; color:#0057ae;">mapflow.ai</span></a> to use the plugin</p><p><br/></p></body></html>'))
            self.invalidToken.setText(self.tr('Invalid credentials'))
            self.invalidToken.setStyleSheet('color: rgb(239, 41, 41);')
        self.token.setText(token)
        self.token.setVisible(not use_oauth)
        self.labelPassword.setVisible(not use_oauth)


