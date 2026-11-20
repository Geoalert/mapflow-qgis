"""Small building blocks shared by the dock pages. Styling comes from theme.QSS via properties."""
from __future__ import annotations

from typing import Callable, List, Optional

from qgis.PyQt.QtCore import QEvent, QObject, QPointF, QRectF, QSize, Qt, QTimer, QUrl, pyqtSignal
from qgis.PyQt.QtGui import QCursor, QDesktopServices, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QPixmap
from qgis.PyQt.QtWidgets import (QAbstractButton, QAction, QApplication, QButtonGroup, QComboBox, QFrame, QHBoxLayout,
                                 QLabel, QLineEdit, QPushButton, QSizePolicy, QToolButton, QToolTip, QVBoxLayout,
                                 QWidget)

from . import icons
from .theme import color, set_prop, tokens
from ..core.guard import guarded


def menu_action(menu, icon_name: str, text: str, handler, ink: Optional[str] = None) -> QAction:
    """A menu item built as a QAction (QMenu.addAction(icon, text, slot) differs between Qt 5 and Qt 6).
    Its handler ignores the `checked` argument some PyQt builds pass with `triggered`, and macOS must
    not move it to the application menu (it does that to "Settings…")."""
    action = QAction(icons.icon(icon_name, ink or tokens()["ink"]), text, menu)
    action.setMenuRole(QAction.MenuRole.NoRole)
    action.triggered.connect(guarded(lambda *_: handler()))
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
        widget.clicked.connect(guarded(lambda *_: QDesktopServices.openUrl(QUrl(url() if callable(url) else url))))
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


def same_width(buttons: List[QWidget]) -> None:
    """Buttons stacked in a list (Use, Chosen, Choose…), made one width: the widest's. Measured once they are
    shown and styled, so the theme's font and padding count."""
    @guarded
    def apply() -> None:
        try:
            width = max((b.sizeHint().width() for b in buttons), default=0)
            for b in buttons:
                b.setMinimumWidth(width)
        except RuntimeError:                    # the list was redrawn meanwhile: these are gone
            pass
    if buttons:
        QTimer.singleShot(0, apply)


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


class DropTarget(QObject):
    """Drops onto `widget`: `parse(mime data)` says what a drag carries, and a drag that carries nothing is
    refused. While something it takes is over it, the widget has dropping=true, which the theme outlines."""
    dropped = pyqtSignal(list)

    def __init__(self, widget: QWidget, parse: Callable[[object], list]):
        super().__init__(widget)
        self.widget, self.parse = widget, parse
        widget.setAcceptDrops(True)
        widget.installEventFilter(self)

    @guarded(default=False)
    def eventFilter(self, obj, event) -> bool:
        kind = event.type()
        if kind in (QEvent.Type.DragEnter, QEvent.Type.DragMove, QEvent.Type.Drop):
            items = self.parse(event.mimeData())
            set_prop(self.widget, "dropping", bool(items) and kind != QEvent.Type.Drop)
            if not items:
                event.ignore()
                return True
            event.acceptProposedAction()
            if kind == QEvent.Type.Drop:
                self.dropped.emit(items)
            return True
        if kind == QEvent.Type.DragLeave:
            set_prop(self.widget, "dropping", False)
        return False


class HoverTip(QObject):
    """One tooltip for a whole area: shown after a pause, every time, and kept while the mouse is anywhere
    in the area. Qt's own reopens over each child widget and shows the next ones at once."""

    def __init__(self, widget: QWidget, text: str, delay: int = 800):
        super().__init__(widget)
        self.widget, self.text = widget, text
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(delay)
        self.timer.timeout.connect(self._show)
        widget.installEventFilter(self)

    @guarded(default=False)
    def eventFilter(self, obj, event) -> bool:
        kind = event.type()
        if kind == QEvent.Type.ToolTip:             # the children's come up here too: ours instead
            return True
        if kind == QEvent.Type.Enter:
            self.timer.start()
        elif kind == QEvent.Type.Leave:
            self.timer.stop()
            QToolTip.hideText()
        return False

    @guarded
    def _show(self) -> None:
        if self.widget.underMouse():
            QToolTip.showText(QCursor.pos(), self.text, self.widget, self.widget.rect())


class Combo(QComboBox):
    """A drop-down for scrolling pages: the mouse wheel over it scrolls the page instead of changing the
    value. Its list, once opened, takes the wheel as usual (the list gets those events, not the combo)."""

    @guarded
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


class DropCard(Card):
    """A card things can be dropped on (with a DropTarget), styled as Mapflow Web's drop zones: a grey dashed
    outline always says so; on hover, and while something droppable is over it, the outline turns blue and
    the background a quiet grey. Drawn here: QSS dashes are long and break on rounded corners."""
    WIDTH, DASH, GAP, RADIUS = 1.5, 5.0, 4.0, 15.0

    def __init__(self, parent: Optional[QWidget] = None, **kwargs):
        super().__init__(parent, kind="drop", **kwargs)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    @guarded(default=False)
    def event(self, event) -> bool:
        if event.type() in (QEvent.Type.HoverEnter, QEvent.Type.HoverLeave):
            set_prop(self, "hover", event.type() == QEvent.Type.HoverEnter)
        return super().event(event)

    @guarded
    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        half = self.WIDTH / 2
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()).adjusted(half, half, -half, -half), self.RADIUS, self.RADIUS)
        # A whole number of dashes around the outline: no short dash or double gap where it closes
        period = self.DASH + self.GAP
        stretch = path.length() / max(1, round(path.length() / period)) / period
        active = self.property("dropping") is True or self.property("hover") is True
        pen = QPen(color("primary" if active else "dash"), self.WIDTH)
        pen.setDashPattern([self.DASH * stretch / self.WIDTH, self.GAP * stretch / self.WIDTH])
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        painter.end()


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
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text = label(text, f"callout-{kind}", wrap=True, parent=self)
        self.text.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.text.setOpenExternalLinks(True)
        layout.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignVCenter)     # centred on the text, any length
        layout.addWidget(self.text, 1)
        # A way out (Top up), as a button on the right; set_action shows it
        self.action = button("", "outline", size="sm", parent=self)
        self.action.setProperty("callout_action", True)     # small, in the callout's own colours (theme)
        self.action.setVisible(False)
        self._action_url = ""
        self.action.clicked.connect(
            guarded(lambda *_: self._action_url and QDesktopServices.openUrl(QUrl(self._action_url))))
        layout.addWidget(self.action, 0, Qt.AlignmentFlag.AlignVCenter)
        self.set(kind, text)

    def set_action(self, text: str = "", url: str = "") -> None:
        """A button on the right that opens `url` in the browser; no text hides it."""
        self.action.setText(f"{text}  ↗" if text else "")
        self._action_url = url
        self.action.setVisible(bool(text and url))

    def set(self, kind: str, text: str) -> None:
        set_prop(self, "callout", kind)
        set_prop(self.text, "role", f"callout-{kind}")
        name = {"info": "info", "warn": "alert", "error": "alert"}[kind]
        tone = {"info": "primary_ink", "warn": "warn_fg", "error": "err_fg"}[kind]
        self.icon.setPixmap(icons.pixmap(name, tokens()[tone], 16))
        self.text.setText(text)
        # Shown only once it has a parent: a parentless widget shown is a window of its own, and one flashed up
        # empty, titled "QGIS3", before the projects window took it in. With text, it shows when it is added.
        if self.parentWidget() is not None or not text:
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


KEYBOARD_FOCUS = (Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason,
                  Qt.FocusReason.ShortcutFocusReason)


class FocusRing:
    """For widgets that draw a focus ring: shown only when the focus came from the keyboard, as a browser's
    :focus-visible. A click focuses them too (so it takes the focus from a field being edited), but leaves no
    ring around what was just clicked. Mixed in before the Qt class; the property `focusring` is for QSS."""
    _keyboard_focus = False

    @guarded
    def focusInEvent(self, event) -> None:
        self._keyboard_focus = event.reason() in KEYBOARD_FOCUS
        set_prop(self, "focusring", self._keyboard_focus)
        super().focusInEvent(event)

    @guarded
    def focusOutEvent(self, event) -> None:
        self._keyboard_focus = False
        set_prop(self, "focusring", False)
        super().focusOutEvent(event)

    def focus_ring(self) -> bool:
        return self.hasFocus() and self._keyboard_focus


class Toggle(FocusRing, QAbstractButton):
    """A switch. Painted, so it looks the same on every platform."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def sizeHint(self) -> QSize:
        return QSize(36, 20)

    @guarded
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
        if self.focus_ring():
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
            star.clicked.connect(guarded(lambda _=False, i=index: self._rate(i)))
            layout.addWidget(star)
            self.buttons.append(star)
        self._paint()

    def _rate(self, value: int) -> None:
        self.set_value(value)
        self.rated.emit(value)

    def set_value(self, value: int) -> None:
        self.value = value
        self._paint()

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


class ImageTile(FocusRing, QAbstractButton):
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

    @guarded
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        hover = self.underMouse() or self.focus_ring()
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
        if self.focus_ring():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(color("focus"), 2))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 13, 13)
        painter.end()


class OptionRow(QFrame):
    """A selectable row (radio-like) with a title, a meta line and free space on the right."""
    clicked = pyqtSignal()

    def __init__(self, title: str, meta: str = "", parent: Optional[QWidget] = None,
                 *, title_detail: str = ""):
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
        if title_detail:
            texts.addLayout(hbox(self.title, label(title_detail, "meta"), None))
        else:
            texts.addWidget(self.title)
        texts.addWidget(self.meta)
        self.texts = texts
        layout.addWidget(self.dot)
        layout.addLayout(texts, 1)
        self.right = QHBoxLayout()
        self.right.setSpacing(6)
        layout.addLayout(self.right)
        self._paint_dot(False)

    def add_note(self, text: str, icon_name: str = "alert", tone: str = "muted") -> None:
        """A warning after the meta: "≈ 0.15 m per pixel · ⚠ z19 recommended", or on the next line, whole."""
        picture = QLabel()
        picture.setPixmap(icons.pixmap(icon_name, tokens()[tone], NOTE_ICON))
        picture.setAlignment(Qt.AlignmentFlag.AlignTop)
        words = label(text, "meta")
        block = QWidget()
        block.picture, block.words = picture, words     # MetaWithNote lines the icon up with the letters
        line = hbox(picture, words, spacing=4)
        line.setAlignment(picture, Qt.AlignmentFlag.AlignTop)
        line.setAlignment(words, Qt.AlignmentFlag.AlignTop)
        block.setLayout(line)
        at = self.texts.indexOf(self.meta)
        self.texts.removeWidget(self.meta)
        self.meta.setVisible(True)
        self.texts.insertWidget(at, MetaWithNote(self.meta, block, self))

    def set_selected(self, selected: bool) -> None:
        set_prop(self, "selected", selected)
        self._paint_dot(selected)

    def _paint_dot(self, selected: bool) -> None:
        scale = icons.screen_scale()                # drawn at the screen's own scale, so it is never resampled
        pixmap = QPixmap(round(16 * scale), round(16 * scale))
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(scale, scale)
        if selected:
            painter.setPen(QPen(color("primary"), 5))
            painter.setBrush(color("bg"))
            painter.drawEllipse(QRectF(2.5, 2.5, 11, 11))
        else:
            painter.setPen(QPen(color("disabled"), 2))
            painter.setBrush(color("bg"))
            painter.drawEllipse(QRectF(1.5, 1.5, 13, 13))
        painter.end()
        pixmap.setDevicePixelRatio(scale)
        self.dot.setPixmap(pixmap)

    @guarded
    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event_pos(event)):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    @guarded
    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.clicked.emit()
            return
        super().keyPressEvent(event)


NOTE_ICON = 13                                  # the warning icon's size in an option row's meta line


class MetaWithNote(QWidget):
    """A wrapping meta label and a block after it (the warning) that never splits: on the meta's line, after a
    "·", when it fits there, else on a line of its own. Qt's rich text can't keep an inline icon with the words
    after it, so the block is a widget, placed here by hand."""
    GAP = 4

    def __init__(self, meta: QLabel, block: QWidget, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.meta, self.block = meta, block
        self.text = meta.text()
        meta.setParent(self)
        block.setParent(self)
        size = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        size.setHeightForWidth(True)
        self.setSizePolicy(size)

    def _joined(self) -> str:
        return f"{self.text} · " if self.text else ""

    def _one_line(self, width: int) -> bool:
        return self.meta.fontMetrics().horizontalAdvance(self._joined()) + self.block.sizeHint().width() <= width

    def hasHeightForWidth(self) -> bool:
        return True

    def _line_height(self) -> int:
        """One line of the meta label as it lays itself out (theme margins included): what a plain meta line
        takes, so a row with a warning spaces its texts as one without."""
        return self.meta.heightForWidth(10_000) if self.text else self.meta.fontMetrics().height()

    @guarded(default=-1)               # -1: Qt's own "no height for width"
    def heightForWidth(self, width: int) -> int:
        block = self.block.sizeHint().height()
        if self._one_line(width):
            return max(self._line_height(), block)
        return (self.meta.heightForWidth(width) + self.GAP if self.text else 0) + block

    def sizeHint(self) -> QSize:
        width = self.meta.fontMetrics().horizontalAdvance(self._joined()) + self.block.sizeHint().width()
        return QSize(width, self.heightForWidth(width))

    def minimumSizeHint(self) -> QSize:
        width = self.block.sizeHint().width()
        return QSize(width, self.heightForWidth(width))

    def _line_up_icon(self) -> None:
        """The icon centred on the letters (between the baseline and the cap height), not on the label's box:
        the box keeps room for descenders under the text, so a box-centred icon sits visibly higher. Measured
        here, once shown, when the theme's font is on the label."""
        picture, words = getattr(self.block, "picture", None), getattr(self.block, "words", None)
        if picture is None or words is None:
            return
        metrics = words.fontMetrics()
        top = max(0, round(metrics.ascent() - metrics.capHeight() / 2 - NOTE_ICON / 2))
        if picture.contentsMargins().top() != top:
            picture.setContentsMargins(0, top, 0, 0)
            self.updateGeometry()                   # the block may be a pixel taller now

    @guarded
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._line_up_icon()
        width, block, text_height = self.width(), self.block.sizeHint(), self._line_height()
        # Centred in the height it is given, as a plain meta label centres its text: a row with a zoom box and a
        # price is taller than its texts, and the layout shares the extra height out between them
        offset = max(0, (self.height() - self.heightForWidth(width)) // 2)
        if self._one_line(width):
            self.meta.setText(self._joined())
            text_width = self.meta.fontMetrics().horizontalAdvance(self._joined())
            # Both from the same top: the warning's words are a label like the meta, so their lines line up
            self.meta.setGeometry(0, offset, text_width, text_height)
            self.block.setGeometry(text_width, offset, block.width(), block.height())
        else:
            self.meta.setText(self.text)         # no "·": the warning is on its own line
            meta_height = self.meta.heightForWidth(width) if self.text else 0
            self.meta.setGeometry(0, offset, width, meta_height)
            top = offset + (meta_height + self.GAP if self.text else 0)
            self.block.setGeometry(0, top, block.width(), block.height())


class FitLineEdit(QLineEdit):
    """A one-line field as wide as its text (as narrow as the space it has, when the text is longer), so what
    follows it, a pencil, sits right after the text instead of at the far end of the row. While it is being
    edited it takes the whole row instead, and says so (`editing`): nothing next to it moves as you type."""
    editing = pyqtSignal(bool)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._editing = False
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.textChanged.connect(guarded(lambda *_: self._editing or self.updateGeometry()))

    @guarded
    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        self._set_editing(True)

    @guarded
    def focusOutEvent(self, event) -> None:
        super().focusOutEvent(event)
        self.setCursorPosition(0)                   # a long name shows from its start again
        self._set_editing(False)

    def _set_editing(self, on: bool) -> None:
        if on != self._editing:
            self._editing = on
            self.updateGeometry()
            self.editing.emit(on)

    def sizeHint(self) -> QSize:
        if self._editing:                           # wider than any row: it gets all the space there is
            return QSize(10_000, super().sizeHint().height())
        text = self.text() or self.placeholderText()
        # + the field's own 2 px margins on each side and the cursor
        return QSize(self.fontMetrics().horizontalAdvance(text) + 8, super().sizeHint().height())

    def minimumSizeHint(self) -> QSize:
        return QSize(40, super().minimumSizeHint().height())


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

    @guarded
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._elide()

    @guarded
    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self._elide()

    def _elide(self) -> None:
        width = max(10, self.width())
        QLabel.setText(self, self.fontMetrics().elidedText(self._full, Qt.TextElideMode.ElideRight, width))
