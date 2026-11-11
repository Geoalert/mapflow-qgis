"""Small building blocks shared by the dock pages. Styling comes from theme.QSS via properties."""
from __future__ import annotations

from typing import List, Optional

from qgis.PyQt.QtCore import QEvent, QPointF, QRectF, QSize, Qt, QUrl, pyqtSignal
from qgis.PyQt.QtGui import QDesktopServices, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QPixmap
from qgis.PyQt.QtWidgets import (QAbstractButton, QAction, QApplication, QButtonGroup, QComboBox, QFrame, QHBoxLayout,
                                 QLabel, QPushButton, QSizePolicy, QToolButton, QVBoxLayout, QWidget)

from . import icons
from .theme import color, set_prop, tokens


def menu_action(menu, icon_name: str, text: str, handler, ink: Optional[str] = None) -> QAction:
    """A menu item built as a QAction (QMenu.addAction(icon, text, slot) differs between Qt 5 and Qt 6).
    Its handler ignores the `checked` argument some PyQt builds pass with `triggered`, and macOS must
    not move it to the application menu (it does that to "Settings…")."""
    action = QAction(icons.icon(icon_name, ink or tokens()["ink"]), text, menu)
    action.setMenuRole(QAction.MenuRole.NoRole)
    action.triggered.connect(lambda *_: handler())
    menu.addAction(action)
    return action


def event_pos(event):
    """Where a mouse event happened, in widget coordinates: position() on Qt 6, pos() on Qt 5."""
    position = getattr(event, "position", None)
    return position().toPoint() if position is not None else event.pos()


def label(text: str = "", role: str = "body", wrap: bool = False, parent: Optional[QWidget] = None) -> QLabel:
    widget = QLabel(text, parent)
    widget.setProperty("role", role)
    widget.setWordWrap(wrap)
    widget.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
    return widget


def button(text: str, variant: str = "outline", icon: Optional[str] = None, size: Optional[str] = None,
           icon_color: Optional[str] = None, external: bool = False, parent: Optional[QWidget] = None) -> QPushButton:
    if external:
        text = f"{text}  ↗"
    widget = QPushButton(text, parent)
    widget.setProperty("variant", variant)
    if size:
        widget.setProperty("size", size)
    if icon:
        default = {"primary": tokens()["primary_text"], "ghost": tokens()["link"], "link": tokens()["link"]}
        widget.setIcon(icons.icon(icon, icon_color or default.get(variant, tokens()["ink"]), 14))
        widget.setIconSize(QSize(14, 14))
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    return widget


def link(text: str, url=None, external: bool = True, parent: Optional[QWidget] = None) -> QPushButton:
    """A link button. `url` is an address, or a function that returns one when clicked (for an address
    that depends on the environment, known only once the plugin has its configuration)."""
    widget = button(text, "link", external=external and bool(url), parent=parent)
    widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    if url:
        if isinstance(url, str):
            widget.setToolTip(url)
        widget.clicked.connect(lambda *_: QDesktopServices.openUrl(QUrl(url() if callable(url) else url)))
    return widget


def tool(icon_name: str, tooltip: str, variant: str = "icon", size: int = 16,
         parent: Optional[QWidget] = None) -> QToolButton:
    widget = QToolButton(parent)
    widget.setProperty("variant", variant)
    widget.setIcon(icons.icon(icon_name, tokens()["ink"], size))
    widget.setIconSize(QSize(size, size))
    widget.setToolTip(tooltip)
    widget.setAccessibleName(tooltip)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    widget.setAutoRaise(True)
    return widget


def release_focus(widget: QWidget) -> None:
    """If the keyboard focus is on `widget` or inside it, drop it. Hiding a focused widget makes Qt move
    the focus to the next one, and a scroll area then scrolls to show it: the page jumps."""
    focused = QApplication.focusWidget()
    if focused is not None and (focused is widget or widget.isAncestorOf(focused)):
        focused.clearFocus()


def clear_layout(layout) -> None:
    """Empty a layout: widgets are hidden at once (so nothing stale shows until Qt deletes them)."""
    focused = QApplication.focusWidget()
    if focused is not None and _in_layout(focused, layout):
        focused.clearFocus()
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()
        elif item.layout() is not None:
            clear_layout(item.layout())
            item.layout().deleteLater()


def _in_layout(widget: QWidget, layout) -> bool:
    """Is `widget` placed (at any depth) in `layout`?"""
    for index in range(layout.count()):
        item = layout.itemAt(index)
        child = item.widget()
        if child is not None and (child is widget or child.isAncestorOf(widget)):
            return True
        if item.layout() is not None and _in_layout(widget, item.layout()):
            return True
    return False


def rule(parent: Optional[QWidget] = None) -> QFrame:
    line = QFrame(parent)
    line.setProperty("rule", True)
    line.setFixedHeight(1)
    return line


def hbox(*items, spacing: int = 8, margins=(0, 0, 0, 0)) -> QHBoxLayout:
    layout = QHBoxLayout()
    layout.setSpacing(spacing)
    layout.setContentsMargins(*margins)
    for item in items:
        if item is None:
            layout.addStretch(1)
        elif isinstance(item, int):
            layout.addSpacing(item)
        elif isinstance(item, QWidget):
            layout.addWidget(item)
        else:
            layout.addLayout(item)
    return layout


def vbox(*items, spacing: int = 8, margins=(0, 0, 0, 0)) -> QVBoxLayout:
    layout = QVBoxLayout()
    layout.setSpacing(spacing)
    layout.setContentsMargins(*margins)
    for item in items:
        if item is None:
            layout.addStretch(1)
        elif isinstance(item, int):
            layout.addSpacing(item)
        elif isinstance(item, QWidget):
            layout.addWidget(item)
        else:
            layout.addLayout(item)
    return layout


class Combo(QComboBox):
    """A drop-down for scrolling pages: the mouse wheel over it scrolls the page instead of changing the
    value. Its list, once opened, takes the wheel as usual (the list gets those events, not the combo)."""

    def wheelEvent(self, event) -> None:
        event.ignore()                          # left to the parent: the scroll area scrolls


class Card(QFrame):
    def __init__(self, parent: Optional[QWidget] = None, margins=(14, 12, 14, 12), spacing: int = 8, kind="true"):
        super().__init__(parent)
        self.setProperty("card", kind)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(*margins)
        self.body.setSpacing(spacing)

    def add(self, item) -> None:
        if isinstance(item, QWidget):
            self.body.addWidget(item)
        else:
            self.body.addLayout(item)


class Pill(QLabel):
    KINDS = {"ok", "run", "warn", "err", "gray"}

    def __init__(self, text: str = "", kind: str = "gray", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setProperty("pill", kind)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

    def set(self, text: str, kind: str) -> None:
        self.setText(text)
        set_prop(self, "pill", kind)
        self.setVisible(bool(text))


class Callout(QFrame):
    def __init__(self, kind: str = "info", text: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("callout", kind)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        self.icon = QLabel(self)
        self.icon.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.text = label(text, f"callout-{kind}", wrap=True, parent=self)
        self.text.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.text.setOpenExternalLinks(True)
        layout.addWidget(self.icon)
        layout.addWidget(self.text, 1)
        self.set(kind, text)

    def set(self, kind: str, text: str) -> None:
        set_prop(self, "callout", kind)
        set_prop(self.text, "role", f"callout-{kind}")
        name = {"info": "info", "warn": "alert", "error": "alert"}[kind]
        tone = {"info": "primary_ink", "warn": "warn_fg", "error": "err_fg"}[kind]
        self.icon.setPixmap(icons.pixmap(name, tokens()[tone], 16))
        self.text.setText(text)
        self.setVisible(bool(text))


class StepHeader(QWidget):
    """Numbered step: ① Title ............ value/actions"""

    def __init__(self, number: int, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.number = number
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.badge = QLabel(str(number), self)
        self.badge.setProperty("step", "todo")
        self.title = label(title, "h2", parent=self)
        self.right = QHBoxLayout()
        self.right.setSpacing(6)
        layout.addWidget(self.badge)
        layout.addWidget(self.title, 1)
        layout.addLayout(self.right)

    def set_state(self, state: str) -> None:
        """todo | active | done"""
        set_prop(self.badge, "step", state)
        if state == "done":
            self.badge.setText("")
            self.badge.setPixmap(icons.pixmap("check", tokens()["ok_fg"], 13))
        else:
            self.badge.setPixmap(QPixmap())
            self.badge.setText(str(self.number))


class Toggle(QAbstractButton):
    """A switch. Painted, so it looks the same on every platform."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def sizeHint(self) -> QSize:
        return QSize(36, 20)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0, (self.height() - 20) / 2, 36, 20)
        painter.setPen(Qt.PenStyle.NoPen)
        on = self.isChecked()
        track = color("primary") if on else color("stroke")
        if not self.isEnabled():
            track = color("tile")
        painter.setBrush(track)
        painter.drawRoundedRect(rect, 10, 10)
        painter.setBrush(color("bg") if self.isEnabled() else color("border"))
        knob_x = rect.x() + (18 if on else 2)
        painter.drawEllipse(QRectF(knob_x, rect.y() + 2, 16, 16))
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(color("focus"), 1.5))
            painter.drawRoundedRect(rect.adjusted(-1.5, -1.5, 1.5, 1.5), 11, 11)
        painter.end()


class Stars(QWidget):
    rated = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.buttons: List[QToolButton] = []
        self.value = 0
        for index in range(1, 6):
            star = QToolButton(self)
            star.setProperty("variant", "plain")
            star.setAutoRaise(True)
            star.setCursor(Qt.CursorShape.PointingHandCursor)
            star.setToolTip(f"Rate {index} of 5")
            star.setAccessibleName(f"Rate {index} of 5")
            star.clicked.connect(lambda _=False, i=index: self._rate(i))
            layout.addWidget(star)
            self.buttons.append(star)
        self._paint()

    def _rate(self, value: int) -> None:
        self.value = value
        self._paint()
        self.rated.emit(value)

    def _paint(self) -> None:
        for index, star in enumerate(self.buttons, start=1):
            filled = index <= self.value
            star.setIcon(icons.icon("star", tokens()["warn_fg"] if filled else tokens()["disabled"], 16))


class Segmented(QFrame):
    changed = pyqtSignal(int)

    def __init__(self, labels: List[str], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("seg", True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)
        self.group = QButtonGroup(self)
        for index, text in enumerate(labels):
            item = QPushButton(text, self)
            item.setProperty("segbtn", True)
            item.setCheckable(True)
            item.setCursor(Qt.CursorShape.PointingHandCursor)
            self.group.addButton(item, index)
            layout.addWidget(item, 1)
        self.group.button(0).setChecked(True)
        self.group.idClicked.connect(self.changed.emit) if hasattr(self.group, "idClicked") \
            else self.group.buttonClicked[int].connect(self.changed.emit)

    def set_index(self, index: int) -> None:
        self.group.button(index).setChecked(True)

    def index(self) -> int:
        return self.group.checkedId()


def rounded(pixmap: QPixmap, width: int, height: int, radius: float = 8) -> QPixmap:
    """Cover-crop a picture into a rounded rectangle."""
    result = QPixmap(width * 2, height * 2)
    result.fill(Qt.GlobalColor.transparent)
    if pixmap is None or pixmap.isNull():
        return result
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, width * 2, height * 2), radius * 2, radius * 2)
    painter.setClipPath(path)
    scale = max(width * 2 / pixmap.width(), height * 2 / pixmap.height())
    src_w, src_h = width * 2 / scale, height * 2 / scale
    painter.drawPixmap(QRectF(0, 0, width * 2, height * 2), pixmap,
                       QRectF((pixmap.width() - src_w) / 2, (pixmap.height() - src_h) / 2, src_w, src_h))
    painter.end()
    result.setDevicePixelRatio(2)
    return result


def placeholder(icon_name: str, width: int, height: int, radius: float = 8) -> QPixmap:
    """A dotted brand tile with an icon, for scenarios without a result picture."""
    result = QPixmap(width * 2, height * 2)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, width * 2, height * 2), radius * 2, radius * 2)
    painter.setClipPath(path)
    painter.fillRect(result.rect(), color("primary_soft"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color("primary_soft2"))
    step = 28
    for y in range(step // 2, height * 2, step):
        for x in range(step // 2, width * 2, step):
            painter.drawEllipse(QPointF(x, y), 2.4, 2.4)
    side = int(min(width, height) * 0.45)
    glyph = icons.pixmap(icon_name, tokens()["primary_hover"], side)
    painter.drawPixmap(QRectF(width - side, height - side, side * 2, side * 2), glyph, QRectF(glyph.rect()))
    painter.end()
    result.setDevicePixelRatio(2)
    return result


class ImageTile(QAbstractButton):
    """Start-page scenario tile: picture on top, title and one meta line under it."""

    def __init__(self, title: str, meta: str, pixmap: QPixmap, model_icon: Optional[str] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.title, self.meta, self.source, self.model_icon = title, meta, pixmap, model_icon
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(title)
        self.setMinimumHeight(156)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def sizeHint(self) -> QSize:
        return QSize(170, 156)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        hover = self.underMouse() or self.hasFocus()
        painter.setPen(QPen(color("stroke" if hover else "border"), 1))
        painter.setBrush(color("bg"))
        painter.drawRoundedRect(rect, 14, 14)
        image_h = 88
        cover = rounded(self.source, int(rect.width()) - 2, image_h + 14, 13)
        clip = QPainterPath()
        clip.addRect(QRectF(1, 1, rect.width() - 1, image_h))
        painter.save()
        painter.setClipPath(clip)
        painter.drawPixmap(QPointF(1, 1), cover)
        painter.restore()
        font = QFont(self.font())
        font.setPixelSize(13)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(color("ink"))
        text_rect = QRectF(12, image_h + 9, rect.width() - 24, 38)
        metrics = QFontMetrics(font)
        painter.drawText(text_rect, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                         metrics.elidedText(self.title, Qt.TextElideMode.ElideRight, int(text_rect.width() * 2)))
        font.setPixelSize(11)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(color("text2"))
        x = 12
        if self.model_icon:
            painter.drawPixmap(QPointF(x, rect.height() - 22), icons.pixmap(self.model_icon, tokens()["text2"], 13))
            x += 18
        meta_rect = QRectF(x, rect.height() - 25, rect.width() - x - 10, 18)
        painter.drawText(meta_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         QFontMetrics(font).elidedText(self.meta, Qt.TextElideMode.ElideRight, int(meta_rect.width())))
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(color("focus"), 2))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 13, 13)
        painter.end()


class OptionRow(QFrame):
    """A selectable row (radio-like) with a title, a meta line and free space on the right."""
    clicked = pyqtSignal()

    def __init__(self, title: str, meta: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("option", True)
        self.setProperty("selected", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(title)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(10)
        self.dot = QLabel(self)
        self.dot.setFixedSize(16, 16)
        texts = QVBoxLayout()
        texts.setSpacing(1)
        self.title = label(title, "title", wrap=True, parent=self)
        self.meta = label(meta, "meta", wrap=True, parent=self)
        self.meta.setVisible(bool(meta))
        texts.addWidget(self.title)
        texts.addWidget(self.meta)
        layout.addWidget(self.dot)
        layout.addLayout(texts, 1)
        self.right = QHBoxLayout()
        self.right.setSpacing(6)
        layout.addLayout(self.right)
        self._paint_dot(False)

    def set_selected(self, selected: bool) -> None:
        set_prop(self, "selected", selected)
        self._paint_dot(selected)

    def _paint_dot(self, selected: bool) -> None:
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if selected:
            painter.setPen(QPen(color("primary"), 10))
            painter.setBrush(color("bg"))
            painter.drawEllipse(QRectF(5, 5, 22, 22))
        else:
            painter.setPen(QPen(color("disabled"), 4))
            painter.setBrush(color("bg"))
            painter.drawEllipse(QRectF(3, 3, 26, 26))
        painter.end()
        pixmap.setDevicePixelRatio(2)
        self.dot.setPixmap(pixmap)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event_pos(event)):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.clicked.emit()
            return
        super().keyPressEvent(event)


class ElidedLabel(QLabel):
    def __init__(self, text: str = "", role: str = "body", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setProperty("role", role)
        self._full = text
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setText(text)

    def setText(self, text: str) -> None:
        self._full = text
        self.setToolTip(text)
        self._elide()

    def full_text(self) -> str:
        return self._full

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._elide()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self._elide()

    def _elide(self) -> None:
        width = max(10, self.width())
        QLabel.setText(self, self.fontMetrics().elidedText(self._full, Qt.TextElideMode.ElideRight, width))
