from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QApplication

from .icons import plugin_icon

ui_path = Path(__file__).parent/'static'/'ui'

class ErrorMessageWidget(*uic.loadUiType(ui_path / 'error_message.ui')):
    def __init__(self, parent: QWidget, text: str, title: str = None, email_body: str = '') -> None:
        """A message box notifying user about a plugin error, with a 'Send a report' button."""
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(QApplication.activeWindow().windowIcon())
        self.setWindowTitle(QApplication.activeWindow().windowTitle())
        self.text.setText(text)
        if title:
            self.title.setText(title)
        self.mailTo.setText(
            '<html><head/><body><p><a href="mailto:help@geoalert.io?subject=Mapflow-QGIS&body=' +
            email_body +
            self.tr('"><span style=" text-decoration: underline; color:#0057ae;">Let us know</span></a></p></body></html>')
        )
