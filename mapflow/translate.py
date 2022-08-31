from .config import PLUGIN_NAME
from PyQt5.QtCore import QCoreApplication


def tr(message: str) -> str:
    """Localize a UI element text.

    :param message: A text to translate
    """
    # Don't use self.plugin_name as context since it'll be overriden in supermodules
    return QCoreApplication.translate(PLUGIN_NAME, message)