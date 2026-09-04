from typing import Callable, Optional, Tuple
from PyQt5.QtWidgets import QApplication, QInputDialog, QMessageBox
from PyQt5.QtCore import Qt, QObject


class AlertService(QObject):
    """Singleton service for displaying alerts and notifications."""
    
    _instance: Optional['AlertService'] = None
    _initialized: bool = False
    
    def __new__(cls, plugin_name: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, plugin_name: str = None):
        if AlertService._initialized:
            return
        super().__init__()
        self._plugin_name = plugin_name or "Mapflow"
        AlertService._initialized = True
    
    @classmethod
    def instance(cls) -> 'AlertService':
        """Get the singleton instance. Must be initialized first."""
        if cls._instance is None:
            raise RuntimeError("AlertService not initialized. Call AlertService(plugin_name) first.")
        return cls._instance
    
    @property
    def plugin_name(self) -> str:
        return self._plugin_name

    def alert(self, message: str, icon: QMessageBox.Icon = QMessageBox.Critical, blocking: bool = True) -> bool:
        """Display a minimalistic modal dialog with some info or a question.

        :param message: A text to display
        :param icon: Info/Warning/Critical/Question
        :param blocking: Opened as modal - code below will only be executed when the alert is closed
        :return: True if user clicked OK (for Question dialogs), False otherwise
        """
        box = QMessageBox(icon, self._plugin_name, message, parent=QApplication.activeWindow())
        box.setTextFormat(Qt.RichText)
        if icon == QMessageBox.Question:
            box.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        return box.exec() == QMessageBox.Ok if blocking else box.open()

    def info(self, message: str, blocking: bool = True) -> bool:
        """Display an info message."""
        return self.alert(message, QMessageBox.Information, blocking)

    def warning(self, message: str, blocking: bool = True) -> bool:
        """Display a warning message."""
        return self.alert(message, QMessageBox.Warning, blocking)

    def error(self, message: str, blocking: bool = True) -> bool:
        """Display an error message."""
        return self.alert(message, QMessageBox.Critical, blocking)

    def confirm(self, message: str) -> bool:
        """Display a confirmation dialog. Returns True if user confirms."""
        return self.alert(message, QMessageBox.Question, blocking=True)

    def report_http_error(self,
                          response,
                          plugin_version: str,
                          title: str = None,
                          error_message_parser: Optional[Callable] = None) -> None:
        """The *report* tier of `spec/006_error_reporting.md`: the dialog that offers to mail us
        the failure. Here for the same reason `alert` and `ask_text` are — a service that hits an
        HTTP error should not have to import a dialog to say so.

        `plugin_version` is passed in rather than read: this tier knows how to present a failure,
        not where the session state lives.
        """
        # Imported here, not at module scope, for the reason `error_guard.report_unexpected_error`
        # gives for the same import: the dialog pulls in the Qt widget tree, and keeping it lazy
        # lets a headless context construct this service without one. Showing dialogs is this
        # tier's job, so the dependency itself is not the thing being avoided.
        from ..dialogs.error_message_widget import ErrorMessageWidget
        from ..http import get_error_report_body
        response_body = response.readAll().data().decode()
        error_summary, email_body = get_error_report_body(
            response=response,
            response_body=response_body,
            plugin_version=plugin_version,
            error_message_parser=error_message_parser)
        ErrorMessageWidget(parent=QApplication.activeWindow(),
                           text=error_summary,
                           title=title,
                           email_body=email_body).show()

    def ask_text(self, title: str, label: str, default: str = "") -> Tuple[str, bool]:
        """Ask the user for a line of text. Returns (text, accepted).

        Here for the same reason `confirm` is: a caller that needs a synchronous answer from
        the user should not have to import Qt to get one. `confirm` already establishes that a
        service may drive a modal through this tier — this is the same capability with a string
        instead of a bool, and it is what keeps `QInputDialog` out of the services that ask.
        """
        return QInputDialog.getText(QApplication.activeWindow(), title, label, text=default)


# Convenience functions for direct import
def alert(message: str, icon: QMessageBox.Icon = QMessageBox.Critical, blocking: bool = True) -> bool:
    """Display an alert using the singleton AlertService."""
    return AlertService.instance().alert(message, icon, blocking)

def alert_info(message: str, blocking: bool = True) -> bool:
    return AlertService.instance().info(message, blocking)

def alert_warning(message: str, blocking: bool = True) -> bool:
    return AlertService.instance().warning(message, blocking)

def alert_error(message: str, blocking: bool = True) -> bool:
    return AlertService.instance().error(message, blocking)

def alert_confirm(message: str) -> bool:
    return AlertService.instance().confirm(message)

def ask_text(title: str, label: str, default: str = "") -> Tuple[str, bool]:
    return AlertService.instance().ask_text(title, label, default)

def report_http_error(response, plugin_version: str, title: str = None,
                      error_message_parser: Optional[Callable] = None) -> None:
    return AlertService.instance().report_http_error(
        response, plugin_version, title, error_message_parser)
