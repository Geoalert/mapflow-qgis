from PyQt5.QtWidgets import QLabel, QWidget

from ..config import config
from ..domain import text_with_domain


def labels_on_domain(widget: QWidget) -> None:
    """Show the Mapflow domain in use in the links of every label of `widget`.

    The label texts come from the `.ui` files and the translations, where the links are written with the
    default domain. The texts themselves stay as they are in those files: the domain is changed in the
    text that the label shows, after the translation (spec/002_api.md, section "The `mapflow.ru` domain").
    """
    for label in widget.findChildren(QLabel):
        text = label.text()
        changed = text_with_domain(text, config.DOMAIN)
        if changed != text:
            label.setText(changed)
