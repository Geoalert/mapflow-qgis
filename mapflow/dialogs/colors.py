"""Named UI colors, shared so the same palette can be reused across widgets.

Import the names rather than hard-coding ``QColor(...)`` literals at call sites, e.g.::

    from ...dialogs.colors import LightBlue
    item.setBackground(LightBlue)
"""
from PyQt5.QtGui import QColor

# Base palette (by appearance).
LightBlue = QColor(207, 242, 249)
BlueTint = QColor(207, 226, 243)
GreenTint = QColor(223, 240, 223)
Grey = QColor(230, 230, 230)
Peach = QColor(255, 220, 200)

# Semantic aliases for the processings/templates table rows.
TemplateRow = LightBlue
AoiRow = BlueTint
AoiProcessingRow = GreenTint
SeparatorRow = Grey
ReviewExpiringRow = Peach
