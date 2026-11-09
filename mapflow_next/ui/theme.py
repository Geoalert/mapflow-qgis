"""Mapflow design tokens (Chakra palette + Mapflow tokens) and the dock's stylesheet.

Light and dark token sets: the dock follows the QGIS UI theme, so it reads as part of QGIS in
both the default and the Night Mapping themes.
"""
from __future__ import annotations

from string import Template
from typing import Dict

from qgis.PyQt.QtGui import QColor, QFontDatabase, QPalette
from qgis.PyQt.QtWidgets import QApplication, QWidget

from ..config import RESOURCES

LIGHT: Dict[str, str] = {
    "bg": "#ffffff", "subtle": "#f7fafc", "tile": "#edf2f7", "icon_button": "#f2f6fb",
    "border": "#e2e8f0", "stroke": "#cdd8e6", "ink": "#1b202b", "text": "#1a202c",
    "text2": "#4a5568", "muted": "#718096", "placeholder": "#858c94", "disabled": "#a0aec0",
    "primary": "#3182ce", "primary_hover": "#2b6cb0", "primary_text": "#ffffff",
    "primary_soft": "#ebf8ff", "primary_soft2": "#bee3f8", "primary_ink": "#2c5282", "link": "#2b6cb0",
    "focus": "#4299e1",
    "ok_bg": "#e0f4e8", "ok_fg": "#276749", "warn_bg": "#fffaf0", "warn_fg": "#9c4221", "warn_line": "#feebc8",
    "err_bg": "#fff5f5", "err_fg": "#c53030", "err_line": "#fed7d7", "progress": "#27b263",
    "track": "#e2e6ec", "navy": "#292946", "check": "#2f855a",
}

DARK: Dict[str, str] = {
    "bg": "#1f2633", "subtle": "#171c26", "tile": "#2d3748", "icon_button": "#2a3342",
    "border": "#323c4d", "stroke": "#4a5568", "ink": "#f7fafc", "text": "#e9edf2",
    "text2": "#a0aec0", "muted": "#8a96a8", "placeholder": "#718096", "disabled": "#5b6678",
    "primary": "#63b3ed", "primary_hover": "#90cdf4", "primary_text": "#1a202c",
    "primary_soft": "#1e3a54", "primary_soft2": "#2a4f72", "primary_ink": "#90cdf4", "link": "#90cdf4",
    "focus": "#63b3ed",
    "ok_bg": "#1c4532", "ok_fg": "#9ae6b4", "warn_bg": "#3b2a17", "warn_fg": "#fbd38d", "warn_line": "#5c3d1a",
    "err_bg": "#3f1d1d", "err_fg": "#feb2b2", "err_line": "#63171b", "progress": "#48bb78",
    "track": "#3a4556", "navy": "#e9edf2", "check": "#68d391",
}

_FONT_FAMILY = None


def load_fonts() -> str:
    """Register the bundled Nunito (the design system's only face); falls back to the system font."""
    global _FONT_FAMILY
    if _FONT_FAMILY is None:
        family = ""
        for name in ("Nunito-Regular.ttf", "Nunito-Bold.ttf"):
            font_id = QFontDatabase.addApplicationFont(str(RESOURCES / "fonts" / name))
            families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
            family = family or (families[0] if families else "")
        _FONT_FAMILY = family
    return _FONT_FAMILY


def is_dark() -> bool:
    app = QApplication.instance()
    if app is None:
        return False
    return app.palette().color(QPalette.ColorRole.Window).lightness() < 110


def tokens() -> Dict[str, str]:
    return DARK if is_dark() else LIGHT


def color(name: str) -> QColor:
    return QColor(tokens()[name])


QSS = Template("""
QWidget { font-family: "$font"; font-size: 13px; color: $text; }
QWidget#mfRoot { background: $subtle; }
QWidget#mfPage, QWidget#mfScrollBody { background: $subtle; }
QScrollArea { border: 0; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QFrame#mfHeader, QFrame#mfTabs, QFrame#mfFooter, QFrame#mfBottomBar { background: $bg; border: 0; }
QFrame#mfHeader { border-bottom: 1px solid $border; }
QFrame#mfTabs { border-bottom: 1px solid $border; }
QFrame#mfFooter { border-top: 1px solid $border; }
QFrame#mfBottomBar { border-top: 1px solid $border; }

QFrame[card="true"] { background: $bg; border: 1px solid $border; border-radius: 15px; }
QFrame[card="true"][active="true"] { border: 1px solid $primary_soft2; }
QFrame[card="true"][tone="error"] { border: 1px solid $err_line; }
QFrame[card="flat"] { background: $subtle; border: 1px solid $border; border-radius: 12px; }
QFrame[card="tile"] { background: $bg; border: 1px solid $border; border-radius: 12px; }
QFrame[card="tile"]:hover { border-color: $primary_soft2; }
QFrame[card="tile"]:focus { border-color: $focus; }
QFrame[card="tile"][current="true"] { border: 2px solid $primary; }
QFrame[callout="info"] { background: $primary_soft; border: 0; border-radius: 8px; }
QFrame[callout="warn"] { background: $warn_bg; border: 1px solid $warn_line; border-radius: 8px; }
QFrame[callout="error"] { background: $err_bg; border: 1px solid $err_line; border-radius: 8px; }
QFrame[rule="true"] { background: $border; border: 0; max-height: 1px; min-height: 1px; }

QLabel { background: transparent; }
QLabel[role="h1"] { font-size: 20px; font-weight: 700; color: $ink; }
QLabel[role="h2"] { font-size: 15px; font-weight: 700; color: $ink; }
QLabel[role="title"] { font-size: 14px; font-weight: 700; color: $ink; }
QLabel[role="body"] { font-size: 13px; color: $text; }
QLabel[role="lead"] { font-size: 14px; color: $text2; }
QLabel[role="meta"] { font-size: 12px; color: $text2; }
QLabel[role="label"] { font-size: 12px; font-weight: 700; color: $text2; }
QLabel[role="value"] { font-size: 14px; font-weight: 700; color: $ink; }
QLabel[role="big"] { font-size: 20px; font-weight: 700; color: $ink; }
QLabel[role="error"] { font-size: 12px; color: $err_fg; }
QLabel[role="callout-info"] { font-size: 13px; color: $primary_ink; }
QLabel[role="callout-warn"] { font-size: 13px; color: $warn_fg; }
QLabel[role="callout-error"] { font-size: 13px; color: $err_fg; }
QLabel[role="link"] { font-size: 13px; font-weight: 700; color: $link; }

QLabel[pill] { border-radius: 10px; padding: 2px 8px; font-size: 11px; font-weight: 700; min-height: 16px; }
QLabel[pill="ok"] { background: $ok_bg; color: $ok_fg; }
QLabel[pill="run"] { background: $primary_soft; color: $primary_ink; }
QLabel[pill="warn"] { background: $warn_bg; color: $warn_fg; border: 1px solid $warn_line; }
QLabel[pill="err"] { background: $err_bg; color: $err_fg; border: 1px solid $err_line; }
QLabel[pill="gray"] { background: $tile; color: $text2; }

QLabel[step] { border-radius: 11px; min-width: 22px; max-width: 22px; min-height: 22px; max-height: 22px;
               font-size: 12px; font-weight: 700; qproperty-alignment: AlignCenter; }
QLabel[step="todo"] { background: $tile; color: $text; }
QLabel[step="active"] { background: $primary_hover; color: #ffffff; }
QLabel[step="done"] { background: $ok_bg; color: $ok_fg; }

QPushButton { border-radius: 6px; font-size: 13px; font-weight: 700; padding: 0 14px; min-height: 34px; }
QPushButton[variant="primary"] { background: $primary; color: $primary_text; border: 0; }
QPushButton[variant="primary"]:hover { background: $primary_hover; }
QPushButton[variant="primary"]:disabled { background: $tile; color: $disabled; }
QPushButton[variant="outline"] { background: $bg; color: $ink; border: 1px solid $stroke; }
QPushButton[variant="outline"]:hover { background: $subtle; }
QPushButton[variant="outline"]:disabled { color: $disabled; }
QPushButton[variant="ghost"] { background: transparent; color: $link; border: 0; }
QPushButton[variant="ghost"]:hover { background: $primary_soft; }
QPushButton[variant="ghost"]:disabled { color: $disabled; }
QPushButton[variant="link"] { background: transparent; color: $link; border: 0; padding: 0; min-height: 18px;
                              text-align: left; }
QPushButton[variant="link"]:hover { text-decoration: underline; }
QPushButton[size="sm"] { min-height: 28px; padding: 0 10px; font-size: 12px; }
QPushButton[size="lg"] { min-height: 40px; font-size: 14px; }
QPushButton:focus { outline: none; }

QToolButton[variant="icon"] { background: $icon_button; border: 0; border-radius: 6px; min-width: 30px;
                              min-height: 30px; max-width: 30px; max-height: 30px; }
QToolButton[variant="icon"]:hover { background: $border; }
QToolButton[variant="plain"] { background: transparent; border: 0; border-radius: 6px; min-width: 28px;
                               min-height: 28px; }
QToolButton[variant="plain"]:hover { background: $tile; }
QToolButton[variant="avatar"] { background: $navy; color: $bg; border: 0; border-radius: 15px; min-width: 30px;
                                min-height: 30px; max-width: 30px; max-height: 30px; font-weight: 700; }
QToolButton[variant="credits"] { background: $primary_soft; color: $primary_ink; border: 0; border-radius: 14px;
                                 padding: 0 10px; min-height: 28px; font-size: 12px; font-weight: 700; }
QToolButton[variant="credits"]:hover { background: $primary_soft2; }
QToolButton[variant="project"] { background: $bg; color: $ink; border: 1px solid $border; border-radius: 6px;
                                 padding: 0 8px; min-height: 32px; font-size: 13px; font-weight: 700;
                                 text-align: left; }
QToolButton[variant="project"]:hover { background: $subtle; }
QToolButton[variant="project"]::menu-indicator { image: none; width: 0; }
QToolButton::menu-indicator { image: none; width: 0; }
QToolButton[variant="aoi"] { background: $bg; color: $ink; border: 1px solid $stroke; border-radius: 6px;
                             min-height: 30px; font-size: 12px; font-weight: 700; padding: 0 6px; }
QToolButton[variant="aoi"]:hover { background: $subtle; }
QToolButton[variant="aoi"]:checked { background: $primary_soft; border-color: $primary; color: $primary_ink; }

QPushButton[tab="true"] { background: transparent; border: 0; border-bottom: 2px solid transparent; border-radius: 0;
                          color: $text2; font-size: 13px; font-weight: 700; min-height: 40px; padding: 0 6px; }
QPushButton[tab="true"]:hover { color: $ink; }
QPushButton[tab="true"]:checked { color: $link; border-bottom: 2px solid $primary; }

QFrame[seg="true"] { background: $tile; border-radius: 8px; }
QPushButton[segbtn="true"] { background: transparent; color: $text2; border: 0; border-radius: 6px; min-height: 28px;
                             font-size: 12px; }
QPushButton[segbtn="true"]:checked { background: $bg; color: $ink; }

QPushButton[chip="true"] { background: $bg; color: $text; border: 1px solid $border; border-radius: 13px;
                           min-height: 24px; padding: 0 10px; font-size: 12px; }
QPushButton[chip="true"]:checked { background: $primary_soft; border-color: $primary_soft2; color: $primary_ink; }

QFrame[option="true"] { background: $bg; border: 1px solid $border; border-radius: 8px; }
QFrame[option="true"]:hover { border-color: $stroke; }
QFrame[option="true"][selected="true"] { background: $primary_soft; border: 1px solid $primary; }
QRadioButton { spacing: 8px; font-size: 13px; font-weight: 700; color: $ink; background: transparent; }

QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit {
    background: $bg; color: $text; border: 1px solid $stroke; border-radius: 6px; padding: 0 8px; min-height: 30px;
    selection-background-color: $primary_soft2; selection-color: $ink; }
QPlainTextEdit { padding: 6px 8px; }
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QPlainTextEdit:focus { border: 1px solid $focus; }
QLineEdit[flat="true"] { border: 0; background: transparent; padding: 0; min-height: 18px; font-size: 12px;
                         color: $text2; }
QLineEdit[flat="true"]:focus { border-bottom: 1px solid $focus; }
QComboBox::drop-down, QDateEdit::drop-down { border: 0; width: 24px; subcontrol-origin: padding;
                                             subcontrol-position: center right; }
QComboBox::down-arrow { image: url("$arrow_icon"); width: 14px; height: 14px; }
QComboBox::down-arrow:disabled { image: url("$arrow_icon_off"); }
QDateEdit::down-arrow { image: url("$calendar_icon"); width: 15px; height: 15px; }
QComboBox { padding-right: 4px; }
QCalendarWidget QWidget { color: $text; background: $bg; }
QCalendarWidget QToolButton { color: $ink; font-weight: 700; background: transparent; border: 0; padding: 4px; }
QCalendarWidget QAbstractItemView:enabled { selection-background-color: $primary; selection-color: #ffffff; }
QCalendarWidget QAbstractItemView:disabled { color: $disabled; }
QSlider:horizontal { min-height: 22px; }
QSlider::groove:horizontal { height: 4px; background: $track; border-radius: 2px; }
QSlider::sub-page:horizontal { background: $primary; border-radius: 2px; }
QSlider::handle:horizontal { background: $bg; border: 2px solid $primary; width: 10px; height: 10px;
                             margin: -5px 0; border-radius: 7px; }
QSlider:focus { outline: none; }
QComboBox QAbstractItemView { background: $bg; color: $text; border: 1px solid $border;
                              selection-background-color: $primary_soft; selection-color: $ink; }

QProgressBar { background: $track; border: 0; border-radius: 3px; max-height: 6px; min-height: 6px; }
QProgressBar::chunk { background: $progress; border-radius: 3px; }

QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: $stroke; border-radius: 3px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QToolTip { background: #171923; color: #ffffff; border: 0; padding: 3px 6px; font-size: 12px; }
QMenu { background: $bg; color: $text; border: 1px solid $border; padding: 4px; }
QMenu::item { padding: 6px 18px 6px 10px; border-radius: 4px; }
QMenu::item:selected { background: $primary_soft; color: $ink; }
QMenu::item:disabled { color: $text2; }
QMenu::separator { height: 1px; background: $border; margin: 4px 6px; }
""")


def stylesheet() -> str:
    from .icons import icon_file
    t = tokens()
    return QSS.substitute(font=load_fonts() or "sans-serif", arrow_icon=icon_file("chevron-down", t["text2"]),
                          arrow_icon_off=icon_file("chevron-down", t["disabled"]),
                          calendar_icon=icon_file("calendar", t["text2"]), **t)


def set_prop(widget: QWidget, name: str, value) -> None:
    """Change a QSS-relevant property and restyle the widget."""
    if widget.property(name) == value:
        return
    widget.setProperty(name, value)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()
