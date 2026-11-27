"""Rate a processing's results: the stars, a comment, then Send feedback."""
from __future__ import annotations

from typing import Tuple

from qgis.PyQt.QtWidgets import QDialog, QHBoxLayout, QPlainTextEdit, QVBoxLayout

from .theme import stylesheet
from .widgets import Stars, button, label
from ..core.guard import guarded


class FeedbackDialog(QDialog):
    def __init__(self, processing_name: str, rating: int, parent=None):
        super().__init__(parent)
        self.setObjectName("mfRoot")
        self.setWindowTitle("Rate the results")
        self.setStyleSheet(stylesheet())
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(8)
        layout.addWidget(label("Rate the results", "h2"))
        layout.addWidget(label(processing_name, "meta", wrap=True))
        self.stars = Stars(self)
        self.stars.set_value(rating)
        layout.addWidget(self.stars)
        layout.addWidget(label("Comment", "label"))
        self.comment = QPlainTextEdit(self)
        self.comment.setPlaceholderText("What was good, what was missed or wrong (optional)")
        self.comment.setFixedHeight(100)
        layout.addWidget(self.comment)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = button("Cancel", "ghost")
        cancel.clicked.connect(guarded(lambda *_: self.reject()))
        self.send = button("Send feedback", "primary")
        self.send.clicked.connect(guarded(lambda *_: self.accept()))
        self.send.setDefault(True)
        self.send.setEnabled(rating > 0)
        self.stars.rated.connect(guarded(lambda value: self.send.setEnabled(value > 0)))
        buttons.addWidget(cancel)
        buttons.addWidget(self.send)
        layout.addSpacing(6)
        layout.addLayout(buttons)
        self.comment.setFocus()

    def values(self) -> Tuple[int, str]:
        return self.stars.value, self.comment.toPlainText().strip()
