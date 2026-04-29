"""Modal dialog for creating a SAM Interactive prompt.

Two inputs: a free-form name and an optional text prompt. The text-prompt
field's placeholder reads "visual" so the user is reminded that an empty
text prompt yields a purely visual (point/bbox-only) prompt.

The confidence threshold is intentionally NOT here — it's a session-level
concept selected at the moment of launching an inference, not a property
of the prompt.
"""
from typing import Optional

from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from .icons import plugin_icon


class SamPromptCreateDialog(QDialog):
    """Collects (name, text_prompt) for a new SAM prompt."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowIcon(plugin_icon)
        self.setWindowTitle(self.tr("New SAM prompt"))
        self.setModal(True)

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText(self.tr("Prompt name"))

        self.text_prompt_input = QLineEdit(self)
        # Placeholder communicates that an empty text prompt is fine — the
        # resulting prompt then relies on visual (point/bbox) sub-prompts only.
        self.text_prompt_input.setPlaceholderText(self.tr("visual"))

        form = QFormLayout()
        form.addRow(self.tr("Name:"), self.name_input)
        form.addRow(self.tr("Text prompt:"), self.text_prompt_input)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self,
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.button_box)

        self.name_input.setFocus()

    @property
    def name(self) -> Optional[str]:
        value = self.name_input.text().strip()
        return value or None

    @property
    def text_prompt(self) -> Optional[str]:
        value = self.text_prompt_input.text().strip()
        return value or None
