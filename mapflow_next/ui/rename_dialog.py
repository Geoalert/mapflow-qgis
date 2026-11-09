"""Rename a processing: its name and description."""
from __future__ import annotations

from typing import Tuple

from qgis.PyQt.QtWidgets import QDialog, QHBoxLayout, QLineEdit, QPlainTextEdit, QVBoxLayout

from .theme import stylesheet
from .widgets import button, label


class RenameDialog(QDialog):
    def __init__(self, name: str, description: str, parent=None, title: str = "Rename processing"):
        super().__init__(parent)
        self.setObjectName("mfRoot")
        self.setWindowTitle(title)
        self.setStyleSheet(stylesheet())
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(8)
        layout.addWidget(label(title, "h2"))
        layout.addWidget(label("Name", "label"))
        self.name = QLineEdit(name, self)
        self.name.setPlaceholderText("Processing name")
        self.name.selectAll()
        layout.addWidget(self.name)
        layout.addWidget(label("Description", "label"))
        self.description = QPlainTextEdit(description, self)
        self.description.setPlaceholderText("What this processing is for (optional)")
        self.description.setFixedHeight(90)
        layout.addWidget(self.description)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = button("Cancel", "ghost")
        cancel.clicked.connect(lambda *_: self.reject())
        self.save = button("Save", "primary")
        self.save.clicked.connect(lambda *_: self.accept())
        self.save.setDefault(True)
        buttons.addWidget(cancel)
        buttons.addWidget(self.save)
        layout.addSpacing(6)
        layout.addLayout(buttons)
        self.name.textChanged.connect(lambda text: self.save.setEnabled(bool(text.strip())))
        self.name.setFocus()

    def values(self) -> Tuple[str, str]:
        return self.name.text().strip(), self.description.toPlainText().strip()
