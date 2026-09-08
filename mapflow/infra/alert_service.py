from typing import Optional, Tuple
from PyQt5.QtWidgets import QApplication, QInputDialog, QMessageBox
from PyQt5.QtCore import Qt, QObject

from ..report_throttle import ReportThrottle

#: Message-tier suppression budget (spec/006 § Volume limit). A separate instance from the report
#: tier's: a dialog storm is same-tier repetition, which each budget bounds on its own. Tests
#: substitute a fresh one; configure_throttle() rebuilds it from config at startup.
_throttle = ReportThrottle()

#: Appended to a message the throttle lets through after hiding repeats of it, so a recurring
#: failure reads as systematic rather than a one-off.
REPEATED_MESSAGE_SUFFIX = "\n\n(Repeated {count} more time(s) since this was last shown.)"


def configure_throttle(first_window: float, max_window: float,
                       global_floor: float, backoff: float) -> None:
    """Rebuild the message-tier budget from config values; called once at startup."""
    global _throttle
    _throttle = ReportThrottle(first_window=first_window, max_window=max_window,
                               global_floor=global_floor, backoff=backoff)


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
        # Volume limit (spec/006 § Volume limit): an informational modal on a polled path stacks
        # exactly like a report dialog — exec() runs a nested event loop, so QTimer keeps firing and
        # dialogs pile up. Suppress a repeat of the same message within the throttle window and carry
        # the hidden count into the next one that gets through. Question is exempt: an interactive
        # prompt must return a real answer, never a suppressed default. The signature is icon+message
        # text — the only stable key a message alert has; a fixed poll message keys stably, while an
        # id-bearing one-off never suppresses, which is fine because it does not storm.
        if icon != QMessageBox.Question:
            suppressed = _throttle.should_report(f"{int(icon)}:{message}")
            if suppressed is None:
                return False
            if suppressed:
                message += REPEATED_MESSAGE_SUFFIX.format(count=suppressed)
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

    def show_error_report(self, text: str, title: str = None, email_body: str = "") -> None:
        """The *report* tier, for a caller that has already composed the failure text itself (an
        expected error with a bespoke message, or one it parsed its own way). `report_http_error`
        is the variant that parses a raw response; this one just shows what it is given, so a
        service or api never has to import the report widget to raise it.
        """
        from ..dialogs.error_message_widget import ErrorMessageWidget
        ErrorMessageWidget(parent=QApplication.activeWindow(),
                           text=text,
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

def show_error_report(text: str, title: str = None, email_body: str = "") -> None:
    return AlertService.instance().show_error_report(text, title, email_body)
