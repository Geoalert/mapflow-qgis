"""New My imagery collection: a name and tags, as in Mapflow Web's "New collection"."""
from __future__ import annotations

from typing import List, Tuple

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog, QHBoxLayout, QLineEdit, QVBoxLayout, QWidget

from .theme import stylesheet, tokens
from .widgets import Pill, button, clear_layout, label, tool
from ..core.guard import guarded

MAX_TAG = 40


class CollectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mfRoot")
        self.setWindowTitle("New collection")
        self.setStyleSheet(stylesheet())
        self.setMinimumWidth(440)
        self.tags: List[str] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(8)
        layout.addWidget(label("New collection", "h1"))
        layout.addSpacing(6)
        name_label = label(f"Name <span style='color:{tokens()['err_fg']}'>*</span>", "label")
        name_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(name_label)
        self.name = QLineEdit(self)
        self.name.setPlaceholderText("Untitled mosaic")
        self.name.setMaxLength(120)
        layout.addWidget(self.name)
        layout.addSpacing(6)
        layout.addWidget(label("Tags", "label"))
        entry = QHBoxLayout()
        entry.setSpacing(8)
        self.tag = QLineEdit(self)
        self.tag.setPlaceholderText("new tag")
        self.tag.setMaxLength(MAX_TAG)
        self.tag.setFixedWidth(200)
        self.tag.returnPressed.connect(self.add_tag)
        entry.addWidget(self.tag)
        self.add_button = tool("plus", "Add the tag", "plain", 16)
        self.add_button.clicked.connect(guarded(lambda *_: self.add_tag()))
        entry.addWidget(self.add_button)
        entry.addStretch(1)
        layout.addLayout(entry)
        self.chips_holder = QWidget(self)
        self.chips = QHBoxLayout(self.chips_holder)
        self.chips.setContentsMargins(0, 2, 0, 0)
        self.chips.setSpacing(6)
        self.chips_holder.setVisible(False)
        layout.addWidget(self.chips_holder)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = button("Cancel", "ghost")
        cancel.clicked.connect(guarded(lambda *_: self.reject()))
        self.create = button("Create", "primary")
        self.create.clicked.connect(guarded(lambda *_: self.accept()))
        buttons.addWidget(cancel)
        buttons.addWidget(self.create)
        layout.addSpacing(10)
        layout.addLayout(buttons)
        self.name.textChanged.connect(guarded(lambda text: self.create.setEnabled(bool(text.strip()))))
        self.create.setEnabled(False)
        self.name.setFocus()

    def keyPressEvent(self, event) -> None:
        # Enter in the tag field adds the tag; it must not press Create as well
        if self.tag.hasFocus() and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.add_tag()
            return
        super().keyPressEvent(event)

    @guarded
    def add_tag(self) -> None:
        tag = self.tag.text().strip()
        if tag and tag.lower() not in {t.lower() for t in self.tags}:
            self.tags.append(tag)
            self._render_tags()
        self.tag.clear()
        self.tag.setFocus()

    def remove_tag(self, tag: str) -> None:
        self.tags = [t for t in self.tags if t != tag]
        self._render_tags()

    def _render_tags(self) -> None:
        clear_layout(self.chips)
        for tag in self.tags:
            chip = QWidget(self.chips_holder)
            row = QHBoxLayout(chip)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(2)
            row.addWidget(Pill(tag, "gray"))
            remove = tool("x", f"Remove “{tag}”", "plain", 12)
            remove.clicked.connect(guarded(lambda *_, t=tag: self.remove_tag(t)))
            row.addWidget(remove)
            self.chips.addWidget(chip)
        self.chips.addStretch(1)
        self.chips_holder.setVisible(bool(self.tags))

    def values(self) -> Tuple[str, List[str]]:
        """The name, and the tags, including one typed but not yet added."""
        pending = self.tag.text().strip()
        tags = self.tags + ([pending] if pending and pending.lower() not in {t.lower() for t in self.tags} else [])
        return self.name.text().strip(), tags
