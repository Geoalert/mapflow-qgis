from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QDialogButtonBox

from .icons import plugin_icon

ui_path = Path(__file__).parent/'static'/'ui'


class LoginDialog(*uic.loadUiType(ui_path/'login_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Auth dialog."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)

    @property
    def auth_data(self):
        return self.token.text().strip()

class OauthLoginDialog(*uic.loadUiType(ui_path/'oauth_login_dialog.ui')):
    def __init__(self, parent: QWidget) -> None:
        """Auth dialog."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(plugin_icon)
        self.wrong_token_label.setVisible(False)

    @property
    def auth_data(self):
        return None
