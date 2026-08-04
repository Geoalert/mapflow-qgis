from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QApplication


ui_path = Path(__file__).parent/'static'/'ui'

class ErrorMessageWidget(*uic.loadUiType(ui_path / 'error_message.ui')):
    def __init__(self, parent: QWidget, text: str, title: str = None, email_body: str = '') -> None:
        """A message box notifying user about a plugin error, with a 'Send a report' button."""
        super().__init__(parent)
        self.setupUi(self)
        try:
            self.setWindowIcon(QApplication.activeWindow().windowIcon())
            self.setWindowTitle(QApplication.activeWindow().windowTitle())
        except Exception as e:
            # Lazy import: this module is imported early in the chain, before the service package.
            from ..functional.service.alert_service import log
            log(f"Could not copy active-window icon/title for the error dialog: {e}", "info")
        self.text.setText(text)
        if title:
            self.title.setText(title)
        self.mailTo.setText(
            '<html><head/><body><p><a href="mailto:help@geoalert.io?subject=Mapflow-QGIS&body=' +
            email_body +
            self.tr('"><span style=" text-decoration: underline; color:#0057ae;">Let us know</span></a></p></body></html>')
        )
