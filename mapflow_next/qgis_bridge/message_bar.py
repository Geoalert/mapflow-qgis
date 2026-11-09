"""Messages in the QGIS message bar, optionally with one action button."""
from __future__ import annotations

from typing import Callable, Optional, Tuple

from qgis.PyQt.QtWidgets import QPushButton
from qgis.core import Qgis

from .. import config


def push(iface, text: str, level=Qgis.MessageLevel.Info, action: Optional[Tuple[str, Callable]] = None,
         duration: int = 6) -> None:
    """`action` is (button text, handler). `duration` 0 keeps the message until it is closed."""
    bar = iface.messageBar()
    if action:
        widget = bar.createMessage(config.PLUGIN_SHORT_NAME, text)
        button = QPushButton(action[0], widget)
        button.clicked.connect(lambda *_: action[1]())
        widget.layout().addWidget(button)
        bar.pushWidget(widget, level, duration)
    else:
        bar.pushMessage(config.PLUGIN_SHORT_NAME, text, level, duration)
