from typing import Optional
from PyQt5.QtWidgets import QApplication, QMessageBox
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
