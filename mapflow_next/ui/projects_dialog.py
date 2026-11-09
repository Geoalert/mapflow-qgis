"""Projects: a window to find, pin and switch projects, with what's in each one and who it's shared with."""
from __future__ import annotations

from typing import Dict, List, Optional

from qgis.PyQt.QtCore import QSize, Qt, QTimer, QUrl, pyqtSignal
from qgis.PyQt.QtGui import QDesktopServices, QKeySequence
from qgis.PyQt.QtWidgets import (QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QShortcut,
                                 QSizePolicy, QVBoxLayout, QWidget)

from .. import config
from ..core import formatting
from ..core.models import Project, Role
from . import icons
from .theme import stylesheet, tokens
from .widgets import Callout, ElidedLabel, Pill, button, clear_layout, event_pos, label, link, tool

GAP = 14
MIN_TILE = 250
ROLE_NAMES = {Role.readonly: "Read only", Role.contributor: "Contributor", Role.maintainer: "Maintainer",
              Role.owner: "Owner"}


def _stat(icon_name: str, text: str, ink: str) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(4)
    picture = QLabel()
    picture.setPixmap(icons.pixmap(icon_name, ink, 13))
    row.addWidget(picture)
    row.addWidget(label(text, "meta"))
    return row


class ProjectTile(QFrame):
    """One project: name, description, numbers, sharing; pin and share buttons. Click to open."""
    clicked = pyqtSignal(str)
    pinToggled = pyqtSignal(str, bool)
    shareRequested = pyqtSignal(str)

    def __init__(self, project: Project, current: bool, pinned: bool, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project = project
        self.setProperty("card", "tile")
        self.setProperty("current", current)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(f"Project {project.name}")
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)   # tiles in a row share its height
        t = tokens()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 10, 12)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(8)
        badge = QLabel(self)
        badge.setPixmap(icons.pixmap("users" if project.shared else "folder", t["ink"], 16))
        top.addWidget(badge)
        top.addWidget(ElidedLabel(project.name or "Untitled project", "title"), 1)
        pin = tool("pin-filled" if pinned else "pin", "Unpin" if pinned else "Pin to the top", "plain", 16)
        if pinned:
            pin.setIcon(icons.icon("pin-filled", t["primary"], 16))
        pin.clicked.connect(lambda *_: self.pinToggled.emit(project.id, not pinned))
        self.pin_button = pin
        top.addWidget(pin)
        layout.addLayout(top)

        fallback = "Default project" if project.is_default else "No description"
        description = ElidedLabel(project.description or fallback, "meta")
        layout.addWidget(description)

        pills_row = QWidget(self)
        pills_row.setFixedHeight(22)                    # kept even when empty, so details line up across tiles
        pills = QHBoxLayout(pills_row)
        pills.setContentsMargins(0, 0, 0, 0)
        pills.setSpacing(6)
        if current:
            pills.addWidget(Pill("Open now", "run"))
        if project.shared:
            people = f" · {project.members + 1} people" if project.members else ""
            pills.addWidget(Pill(f"Shared{people}", "gray"))
        if project.role is not Role.owner:
            pills.addWidget(Pill(ROLE_NAMES.get(project.role, "Member"), "warn" if project.role is Role.readonly
                                 else "gray"))
        pills.addStretch(1)
        layout.addWidget(pills_row)

        stats = QHBoxLayout()
        stats.setSpacing(12)
        stats.addLayout(_stat("check-circle", f"{project.succeeded:,} done", t["ok_fg"]))
        if project.failed:
            stats.addLayout(_stat("x-circle", f"{project.failed:,} failed", t["err_fg"]))
        if project.in_progress:
            stats.addLayout(_stat("refresh", f"{project.in_progress:,} running", t["primary_ink"]))
        stats.addStretch(1)
        layout.addLayout(stats)
        layout.addStretch(1)

        bottom = QHBoxLayout()
        bottom.setSpacing(6)
        updated = formatting.when(project.updated) if project.updated else ""
        bottom.addWidget(label(f"Updated {updated}" if updated else "", "meta"), 1)
        share = tool("share", "Share this project in Mapflow Web", "plain", 15)
        share.clicked.connect(lambda *_: self.shareRequested.emit(project.id))
        self.share_button = share
        bottom.addWidget(share)
        layout.addLayout(bottom)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event_pos(event)):
            self.clicked.emit(self.project.id)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit(self.project.id)
            return
        super().keyPressEvent(event)


class ProjectsDialog(QDialog):
    """Pinned projects first, then all projects (most recently updated first), searched on the server."""
    queryChanged = pyqtSignal(str)
    moreRequested = pyqtSignal()
    projectChosen = pyqtSignal(str)
    pinToggled = pyqtSignal(str, bool)
    shareRequested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mfRoot")
        self.setWindowTitle("Mapflow projects")
        self.setStyleSheet(stylesheet())
        self.resize(900, 640)
        self.current_id: Optional[str] = None
        self.pinned_ids: List[str] = []
        self.pinned: Dict[str, Project] = {}
        self.results: List[Project] = []
        self.total = 0
        self.loading = False
        self.query = ""
        self.tiles: List[ProjectTile] = []
        self._columns = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 16)
        outer.setSpacing(12)
        head = QHBoxLayout()
        head.setSpacing(16)
        head.addWidget(label("Projects", "h1"))
        self.count = label("", "meta")
        head.addWidget(self.count, 0, Qt.AlignmentFlag.AlignBottom)
        head.addStretch(1)
        team = link("Team in Mapflow Web", config.TEAM_URL)
        team.setIcon(icons.icon("users", tokens()["link"], 14))
        head.addWidget(team)
        head.addWidget(link("New project in Mapflow Web", config.PROJECTS_URL))
        outer.addLayout(head)

        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Find a project by name")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(icons.icon("search", tokens()["text2"], 16), QLineEdit.ActionPosition.LeadingPosition)
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)
        self._debounce.timeout.connect(lambda: self.queryChanged.emit(self.search.text().strip()))
        self.search.textChanged.connect(lambda *_: self._debounce.start())
        outer.addWidget(self.search)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        body.setObjectName("mfScrollBody")
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(0, 4, 8, 8)
        self.body.setSpacing(10)
        self.scroll.setWidget(body)
        outer.addWidget(self.scroll, 1)

        foot = QHBoxLayout()
        foot.addWidget(label("Pinned projects stay on top, on this computer. Sharing and roles are managed in "
                             "Mapflow Web.", "meta", wrap=True), 1)
        close = button("Close", "ghost")
        close.clicked.connect(lambda *_: self.reject())
        foot.addWidget(close)
        outer.addLayout(foot)
        QShortcut(QKeySequence.StandardKey.Find, self, activated=self.search.setFocus)

    # ---------- data in ----------

    def set_state(self, current_id: Optional[str], pinned_ids: List[str]) -> None:
        self.current_id, self.pinned_ids = current_id, list(pinned_ids)
        self._render()

    def set_loading(self, loading: bool) -> None:
        self.loading = loading
        self._render()

    def set_results(self, projects: List[Project], total: int, append: bool = False) -> None:
        self.loading = False
        if append:
            known = {p.id for p in self.results}
            self.results += [p for p in projects if p.id not in known]
        else:
            self.results = list(projects)
        self.total = max(total, len(self.results))
        for project in projects:
            if project.id in self.pinned_ids:
                self.pinned[project.id] = project
        self._render()

    def set_pinned_project(self, project: Project) -> None:
        self.pinned[project.id] = project
        self._render()

    # ---------- rendering ----------

    def _section(self, title: str, projects: List[Project]) -> None:
        self.body.addWidget(label(title, "label"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(GAP)
        grid.setVerticalSpacing(GAP)
        columns = self._column_count()
        for column in range(columns):
            grid.setColumnStretch(column, 1)
        for index, project in enumerate(projects):
            tile = ProjectTile(project, project.id == self.current_id, project.id in self.pinned_ids)
            tile.clicked.connect(self.projectChosen.emit)
            tile.pinToggled.connect(self.pinToggled.emit)
            tile.shareRequested.connect(self.shareRequested.emit)
            grid.addWidget(tile, index // columns, index % columns)
            self.tiles.append(tile)
        self.body.addLayout(grid)

    def _column_count(self) -> int:
        width = max(MIN_TILE, self.scroll.viewport().width() - 12)
        return max(1, min(3, (width + GAP) // (MIN_TILE + GAP)))

    def _render(self) -> None:
        bar = self.scroll.verticalScrollBar()
        position = bar.value()
        clear_layout(self.body)
        self.tiles = []
        self._columns = self._column_count()
        needle = self.search.text().strip().lower()
        pinned = [self.pinned[i] for i in self.pinned_ids if i in self.pinned
                  and (not needle or needle in self.pinned[i].name.lower())]
        rest = [p for p in self.results if p.id not in self.pinned_ids]
        if pinned:
            self._section("Pinned", pinned)
        if rest:
            self._section(f"Matching “{self.search.text().strip()}”" if needle else "All projects", rest)
        if self.loading and not self.results:
            self.body.addWidget(label("Loading projects…", "lead"))
        elif not pinned and not rest:
            self.body.addWidget(Callout("info", "No projects match this name." if needle else "No projects yet."))
        if len(self.results) < self.total:
            more = button("Loading…" if self.loading else
                          f"Show more · {len(self.results):,} of {self.total:,}", "outline")
            more.setEnabled(not self.loading)
            more.clicked.connect(lambda *_: self.moreRequested.emit())
            self.more_button = more
            self.body.addWidget(more, 0, Qt.AlignmentFlag.AlignHCenter)
        self.body.addStretch(1)
        shown = len(self.results) + len([p for p in pinned if p.id not in {r.id for r in self.results}])
        self.count.setText(f"{self.total:,} projects" if self.total else (f"{shown}" if shown else ""))
        QTimer.singleShot(0, lambda: bar.setValue(position))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._columns and self._column_count() != self._columns:
            self._render()

    def sizeHint(self) -> QSize:
        return QSize(900, 640)


def open_in_web(url: str = config.PROJECTS_URL) -> None:
    QDesktopServices.openUrl(QUrl(url))
