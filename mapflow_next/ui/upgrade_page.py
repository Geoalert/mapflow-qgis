"""The page that replaces the dock while the backend expects a higher major version of the plugin."""
from __future__ import annotations

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QVBoxLayout, QWidget

from . import icons
from .theme import is_dark
from .widgets import button, label, vbox


class UpgradePage(QWidget):
    upgradeRequested = pyqtSignal()
    signOutRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mfPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 28, 24, 20)
        layout.setSpacing(20)
        layout.addWidget(icons.logo_widget(is_dark(), 44, self), 0, Qt.AlignmentFlag.AlignLeft)
        self.message = label("", "lead", wrap=True)
        layout.addLayout(vbox(label("Upgrade Mapflow Next", "h1", wrap=True), self.message, spacing=6))
        self.upgrade = button("Open the plugin manager", "primary", size="lg")
        self.upgrade.clicked.connect(self.upgradeRequested.emit)
        self.sign_out = button("Sign out", "ghost", "logout", size="sm")
        self.sign_out.clicked.connect(self.signOutRequested.emit)
        layout.addWidget(self.upgrade)
        layout.addWidget(self.sign_out, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)

    def show_versions(self, expected: str, installed: str) -> None:
        self.message.setText(f"Mapflow now expects version {expected} of this plugin, and you have {installed}. "
                             "Upgrade the plugin to go on.")
