"""The alert before a processing on a QGIS tile layer that has a login (spec/002_B § The alert before the start)."""
from __future__ import annotations

from typing import Optional, Tuple

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QCheckBox, QMessageBox, QWidget

TEXT = ('Mapflow needs the login and the password of the layer "{layer}" to read its tiles. The plugin sends them '
        'to Mapflow with the processing. Members of the project can read them.')


class TileLoginAlert(QMessageBox):
    """"Send and run" or "Cancel", and a box to not ask again. "Cancel" is the default button and Escape."""

    def __init__(self, layer_name: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setIcon(QMessageBox.Icon.Warning)
        self.setWindowTitle("Send the login to Mapflow?")
        self.setTextFormat(Qt.TextFormat.PlainText)         # a layer's name is the user's text, not markup
        self.setText(TEXT.replace("{layer}", layer_name))
        self.send_button = self.addButton("Send and run", QMessageBox.ButtonRole.AcceptRole)
        self.cancel_button = self.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        self.setDefaultButton(self.cancel_button)
        self.setEscapeButton(self.cancel_button)
        self.checkbox = QCheckBox("Don't show this again", self)
        self.setCheckBox(self.checkbox)

    def outcome(self) -> Tuple[bool, bool]:
        """(send, skip): whether to send the login and run, and whether to stop asking. The box counts only
        with "Send and run": "Cancel" never stores the choice."""
        send = self.clickedButton() is self.send_button
        return send, send and self.checkbox.isChecked()


def ask_tile_login(layer_name: str, parent: Optional[QWidget] = None) -> Tuple[bool, bool]:
    """Show the alert and wait for the answer: (send, skip)."""
    box = TileLoginAlert(layer_name, parent)
    box.exec()
    return box.outcome()
