"""The dock: header (project, balance, settings), three tabs, the pages and a status footer."""
from __future__ import annotations

from typing import Optional

from qgis.PyQt.QtCore import QRectF, QSize, Qt, QUrl, pyqtSignal
from qgis.PyQt.QtGui import QDesktopServices, QFont, QFontMetrics, QPainter, QPixmap
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtWidgets import (QAbstractButton, QButtonGroup, QFrame, QHBoxLayout, QLabel, QMenu, QProgressBar,
                                 QSizePolicy, QStackedWidget, QToolButton, QVBoxLayout, QWidget)
from qgis.gui import QgsDockWidget

from .. import config
from ..core.models import Project
from ..core.scenarios import Catalogue
from . import icons
from .imagery_page import ImageryPage
from .processings_page import ProcessingsPage
from .run_page import RunPage
from .sign_in import SignInPage
from .start_page import StartPage
from .theme import color, is_dark, load_fonts, stylesheet, tokens
from .widgets import link, menu_action, tool

START, PROCESSINGS, IMAGERY = 0, 1, 2
PAGE_SIGN_IN, PAGE_START, PAGE_RUN, PAGE_PROCESSINGS, PAGE_IMAGERY = range(5)


class TabButton(QAbstractButton):
    def __init__(self, text: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.icon_name = icon_name
        self.badge = 0
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(42)
        self.setAccessibleName(text)

    def set_badge(self, value: int) -> None:
        self.badge = value
        self.setAccessibleName(f"{self.text()}, {value} running" if value else self.text())
        self.update()

    def _font(self) -> QFont:
        font = QFont(self.font())
        font.setPixelSize(13)
        font.setBold(True)
        return font

    def sizeHint(self) -> QSize:
        """As wide as the icon, label and badge need: tabs with longer labels get more room."""
        metrics = QFontMetrics(self._font())
        badge = (metrics.horizontalAdvance(str(self.badge)) + 16) if self.badge else 0
        return QSize(22 + metrics.horizontalAdvance(self.text()) + badge + 20, 42)

    def minimumSizeHint(self) -> QSize:
        return QSize(QFontMetrics(self._font()).horizontalAdvance(self.text()) // 2, 42)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        on = self.isChecked()
        ink = color("link") if on else (color("ink") if self.underMouse() else color("text2"))
        font = self._font()
        painter.setFont(font)
        metrics = QFontMetrics(font)
        badge_w = (metrics.horizontalAdvance(str(self.badge)) + 10) if self.badge else 0
        extra = 6 + badge_w if badge_w else 0
        text = self.text()
        text_w = metrics.horizontalAdvance(text)
        icon_w = 22
        if icon_w + text_w + extra > self.width() - 8:      # narrow: drop the icon, then shorten the label
            icon_w = 0
            text = metrics.elidedText(text, Qt.TextElideMode.ElideRight, max(10, self.width() - 8 - extra))
            text_w = metrics.horizontalAdvance(text)
        total = icon_w + text_w + extra
        x = (self.width() - total) / 2
        if icon_w:
            painter.drawPixmap(int(x), (self.height() - 16) // 2, icons.pixmap(self.icon_name, ink.name(), 16))
        painter.setPen(ink)
        painter.drawText(QRectF(x + icon_w, 0, text_w + 2, self.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
        if badge_w:
            rect = QRectF(x + icon_w + text_w + 6, (self.height() - 18) / 2, badge_w, 18)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color("primary_hover"))
            painter.drawRoundedRect(rect, 9, 9)
            painter.setPen(Qt.GlobalColor.white)
            font.setPixelSize(11)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self.badge))
        if on:
            painter.fillRect(QRectF(4, self.height() - 2, self.width() - 8, 2), color("primary"))
        if self.hasFocus():
            painter.setPen(color("focus"))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(2, 4, -2, -4), 4, 4)
        painter.end()


class DockContent(QWidget):
    projectsRequested = pyqtSignal()
    settingsRequested = pyqtSignal()
    signOutRequested = pyqtSignal()
    tabChanged = pyqtSignal(int)

    def __init__(self, catalogue: Catalogue, parent=None):
        super().__init__(parent)
        load_fonts()
        self.setObjectName("mfRoot")
        self.setStyleSheet(stylesheet())
        font = QFont(self.font())
        font.setFamily(load_fonts() or font.family())
        self.setFont(font)
        self.setMinimumWidth(360)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._header())
        layout.addWidget(self._tabs())
        self.stack = QStackedWidget(self)
        self.sign_in = SignInPage()
        self.start = StartPage(catalogue)
        self.run = RunPage()
        self.processings = ProcessingsPage()
        self.imagery = ImageryPage()
        for page in (self.sign_in, self.start, self.run, self.processings, self.imagery):
            self.stack.addWidget(page)
        layout.addWidget(self.stack, 1)
        layout.addWidget(self._footer())
        self._start_page = PAGE_START
        self.show_signed_out()

    # ---------- header ----------

    def _header(self) -> QWidget:
        header = QFrame(self)
        header.setObjectName("mfHeader")
        header.setFixedHeight(52)
        row = QHBoxLayout(header)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(8)
        mark = icons.mark_widget(is_dark(), 26, header)
        mark.setToolTip("Mapflow")
        row.addWidget(mark)
        self.project_button = QToolButton(header)
        self.project_button.setProperty("variant", "project")
        self.project_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.project_button.setIcon(icons.icon("folder", tokens()["ink"], 15))
        self.project_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.project_button.setToolTip("Projects: find, pin and switch projects")
        self.project_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.project_button.clicked.connect(lambda *_: self.projectsRequested.emit())
        row.addWidget(self.project_button, 1)
        self.credits = QToolButton(header)
        self.credits.setProperty("variant", "credits")
        self.credits.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.credits.setIcon(icons.icon("coins", tokens()["primary_ink"], 14))
        self.credits.setCursor(Qt.CursorShape.PointingHandCursor)
        self.credits.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(config.TOP_UP_URL)))
        row.addWidget(self.credits)
        settings = tool("settings", "Settings")
        settings.clicked.connect(lambda *_: self.settingsRequested.emit())
        row.addWidget(settings)
        self.avatar = QToolButton(header)
        self.avatar.setProperty("variant", "avatar")
        self.avatar.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.avatar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.account_menu = QMenu(self.avatar)
        self.avatar.setMenu(self.account_menu)
        row.addWidget(self.avatar)
        self.header = header
        return header

    def _menu_action(self, menu: QMenu, icon_name: str, text: str, handler) -> QAction:
        return menu_action(menu, icon_name, text, handler)

    def set_account(self, email: str) -> None:
        self.avatar.setText((email[:1] or "M").upper())
        self.avatar.setToolTip(email or "Account")
        self.account_menu.clear()
        title = self.account_menu.addAction(email or "Signed in")
        title.setEnabled(False)
        self.account_menu.addSeparator()
        self._menu_action(self.account_menu, "coins", "Balance and billing  ↗",
                          lambda: QDesktopServices.openUrl(QUrl(config.TOP_UP_URL)))
        self._menu_action(self.account_menu, "users", "Team in Mapflow Web  ↗",
                          lambda: QDesktopServices.openUrl(QUrl(config.TEAM_URL)))
        self._menu_action(self.account_menu, "settings", "Settings…", self.settingsRequested.emit)
        self._menu_action(self.account_menu, "logout", "Sign out", self.signOutRequested.emit)

    def set_credits(self, text: str, tooltip: str) -> None:
        self.credits.setText(text)
        self.credits.setToolTip(tooltip)
        self.credits.setVisible(bool(text))

    def set_project(self, current: Optional[Project]) -> None:
        name = current.name if current else "Loading…"
        metrics = QFontMetrics(self.project_button.font())
        self.project_button.setText(metrics.elidedText(name, Qt.TextElideMode.ElideRight, 150))
        shared = bool(current and current.shared)
        self.project_button.setIcon(icons.icon("users" if shared else "folder", tokens()["ink"], 15))
        self.project_button.setToolTip(f"Project: {name}{' (shared)' if shared else ''}. Click to switch, "
                                       "find or pin projects")

    # ---------- tabs ----------

    def _tabs(self) -> QWidget:
        bar = QFrame(self)
        bar.setObjectName("mfTabs")
        row = QHBoxLayout(bar)
        row.setContentsMargins(8, 0, 8, 0)
        row.setSpacing(0)
        self.tab_group = QButtonGroup(self)
        self.tab_buttons = []
        for index, (text, icon_name) in enumerate((("Start", "home"), ("Processings", "list"),
                                                   ("Imagery sources", "image"))):
            item = TabButton(text, icon_name, bar)
            item.clicked.connect(lambda *_, i=index: self.go(i))
            self.tab_group.addButton(item, index)
            self.tab_buttons.append(item)
            row.addWidget(item)
        self.tabs = bar
        return bar

    def go(self, tab: int) -> None:
        self.tab_buttons[tab].setChecked(True)
        page = {START: self._start_page, PROCESSINGS: PAGE_PROCESSINGS, IMAGERY: PAGE_IMAGERY}[tab]
        self.stack.setCurrentIndex(page)
        self.tabChanged.emit(tab)

    def open_start(self) -> None:
        self._start_page = PAGE_START
        self.go(START)

    def open_run(self) -> None:
        self._start_page = PAGE_RUN
        self.go(START)

    def current_tab(self) -> int:
        return self.tab_group.checkedId()

    # ---------- footer ----------

    def _footer(self) -> QWidget:
        footer = QFrame(self)
        footer.setObjectName("mfFooter")
        footer.setFixedHeight(38)
        row = QHBoxLayout(footer)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(8)
        self.live_dot = QLabel(footer)
        dot = QPixmap(20, 20)
        dot.fill(Qt.GlobalColor.transparent)
        painter = QPainter(dot)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color("primary_soft2"))
        painter.drawEllipse(QRectF(0, 0, 20, 20))
        painter.setBrush(color("primary"))
        painter.drawEllipse(QRectF(5, 5, 10, 10))
        painter.end()
        dot.setDevicePixelRatio(2)
        self.live_dot.setPixmap(dot)
        self.running_link = link("", external=False)
        self.running_link.clicked.connect(lambda *_: self.go(PROCESSINGS))
        self.running_bar = QProgressBar(footer)
        self.running_bar.setTextVisible(False)
        self.running_bar.setFixedWidth(56)
        row.addWidget(self.live_dot)
        row.addWidget(self.running_link)
        row.addWidget(self.running_bar)
        row.addStretch(1)
        row.addWidget(link("Mapflow Web", config.WEB_URL))
        self.footer = footer
        self.set_running(0, 0)
        return footer

    def set_running(self, count: int, percent: int) -> None:
        self.tab_buttons[PROCESSINGS].set_badge(count)
        for widget in (self.live_dot, self.running_link, self.running_bar):
            widget.setVisible(count > 0)
        self.running_link.setText(f"{count} running · {percent}%")
        self.running_bar.setValue(percent)

    # ---------- states ----------

    def show_signed_out(self) -> None:
        for widget in (self.header, self.tabs, self.footer):
            widget.setVisible(False)
        self.stack.setCurrentIndex(PAGE_SIGN_IN)

    def show_signed_in(self) -> None:
        for widget in (self.header, self.tabs, self.footer):
            widget.setVisible(True)
        self.open_start()


class MapflowDock(QgsDockWidget):
    def __init__(self, catalogue: Catalogue, parent=None):
        super().__init__("Mapflow", parent)
        self.setObjectName("MapflowNextDock")
        self.content = DockContent(catalogue, self)
        self.setWidget(self.content)
        self.setMinimumWidth(360)
