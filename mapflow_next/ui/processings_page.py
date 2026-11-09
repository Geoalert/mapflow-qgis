"""Processings of the current project as cards: status at a glance, actions on the selected one."""
from __future__ import annotations

from typing import Dict, List, Optional

from qgis.PyQt.QtCore import Qt, QTimer, pyqtSignal
from qgis.PyQt.QtWidgets import (QButtonGroup, QHBoxLayout, QLineEdit, QMenu, QProgressBar, QPushButton, QScrollArea,
                                 QSizePolicy, QToolButton, QVBoxLayout, QWidget)

from .. import config
from ..core import formatting
from ..core.messages import describe
from ..core.models import Processing, Status
from . import icons
from .start_page import model_icon, status_pill
from .theme import set_prop, tokens
from .widgets import (Card, ElidedLabel, Pill, Stars, button, clear_layout, event_pos, label, link, menu_action,
                      rule, tool)

FILTERS = (("all", "All"), ("running", "Running"), ("done", "Done"), ("attention", "Needs action"))


def source_text(processing: Processing, provider_names: Dict[str, str], mosaic_names: Dict[str, str]) -> str:
    source = processing.source
    if source.kind == "provider":
        name = provider_names.get(source.provider, source.provider or "Basemap")
        return f"{name} z{source.zoom}" if source.zoom else name
    if source.kind == "my_imagery":
        return mosaic_names.get(source.mosaic_id or "", "My imagery")
    if source.kind == "catalog":
        return f"{source.provider or 'Catalog'} image"
    if source.kind == "custom":
        return "Custom imagery"
    return ""


class ProcessingCard(Card):
    clicked = pyqtSignal(str)

    def __init__(self, processing: Processing, source: str, in_map: bool, busy: bool, expanded: bool,
                 page: "ProcessingsPage"):
        super().__init__(margins=(14, 12, 14, 12), spacing=8)
        self.processing = processing
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        set_prop(self, "active", expanded)
        if processing.status is Status.failed:
            set_prop(self, "tone", "error" if expanded else None)

        top = QHBoxLayout()
        top.setSpacing(8)
        icon = label("")
        icon.setPixmap(icons.pixmap(model_icon(processing.model_name) or "layers", tokens()["text"], 18))
        top.addWidget(icon)
        top.addWidget(ElidedLabel(processing.name, "title"), 1)
        text, kind = status_pill(processing, in_map)
        top.addWidget(Pill(text, kind))
        self.add(top)

        if processing.is_running:
            bar = QProgressBar(self)
            bar.setTextVisible(False)
            bar.setValue(processing.percent)
            self.add(bar)
        meta = [processing.model_name.lstrip(" "), source, formatting.km2(processing.area_km2)]
        if processing.cost:
            meta.append(f"{processing.cost:,} credits")
        meta.append(formatting.when(processing.created))
        meta_label = label(" · ".join(m for m in meta if m), "meta", wrap=True)
        meta_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.add(meta_label)

        if processing.status is Status.failed and processing.messages:
            errors = "\n".join(describe(m.code, m.params, m.text) for m in processing.messages[:2])
            error = label(errors, "error", wrap=True)
            error.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.add(error)

        if expanded:
            self._actions(processing, in_map, busy, page)

    def _actions(self, processing: Processing, in_map: bool, busy: bool, page: "ProcessingsPage") -> None:
        pid = processing.id
        row = QHBoxLayout()
        row.setSpacing(6)
        if processing.is_done:
            if busy:
                add = button("Loading…", "primary", size="sm")
                add.setEnabled(False)
            elif in_map:
                add = button("Show on map", "outline", "layers", size="sm")
                add.clicked.connect(lambda *_: page.zoomTo.emit(pid))
            else:
                add = button("Add to map", "primary", "layers", size="sm")
                add.clicked.connect(lambda *_: page.addToMap.emit(pid))
            row.addWidget(add, 1)
            save = button("GeoJSON", "outline", "download", size="sm")
            save.setToolTip("Save the results as a GeoJSON file")
            save.setEnabled(not busy)
            save.clicked.connect(lambda *_: page.saveGeojson.emit(pid))
            row.addWidget(save)
        elif processing.status is Status.failed and page.can_manage:
            restart = button("Restart", "outline", "refresh", size="sm")
            restart.clicked.connect(lambda *_: page.restart.emit(pid))
            row.addWidget(restart)
            row.addStretch(1)
        else:
            row.addStretch(1)
        more = tool("more", "More: run again, rename, delete")
        menu = QMenu(more)
        menu_action(menu, "copy", "Run again with these settings", lambda: page.duplicate.emit(pid))
        if page.can_manage:
            menu_action(menu, "edit", "Rename…", lambda: page.rename.emit(pid))
        menu_action(menu, "globe", "Open in Mapflow Web", lambda: page.openWeb.emit(pid))
        if page.can_manage:
            menu.addSeparator()
            menu_action(menu, "trash", "Delete…", lambda: page.delete.emit(pid), tokens()["err_fg"])
        more.setMenu(menu)
        more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        row.addWidget(more)
        self.add(row)

        if processing.needs_review:
            self.add(link("Review this result in Mapflow Web", config.WEB_URL))
        if processing.is_done:
            self.add(rule())
            rating = QHBoxLayout()
            rating.setSpacing(6)
            rating.addWidget(label("Rate the result", "label"))
            stars = Stars(self)
            stars.rated.connect(lambda value: page.rate.emit(pid, value))
            rating.addWidget(stars)
            rating.addStretch(1)
            self.add(rating)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event_pos(event)):
            self.clicked.emit(self.processing.id)
        super().mouseReleaseEvent(event)


class ProcessingsPage(QWidget):
    addToMap = pyqtSignal(str)
    zoomTo = pyqtSignal(str)
    saveGeojson = pyqtSignal(str)
    restart = pyqtSignal(str)
    rename = pyqtSignal(str)
    duplicate = pyqtSignal(str)
    delete = pyqtSignal(str)
    openWeb = pyqtSignal(str)
    rate = pyqtSignal(str, int)
    startRequested = pyqtSignal()
    refreshRequested = pyqtSignal()
    moreRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mfPage")
        self.items: List[Processing] = []
        self.expanded: Optional[str] = None
        self.filter = "all"
        self.in_map: set = set()
        self.busy: set = set()
        self.can_manage = True
        self.loading = False
        self.loading_more = False
        self.total = 0
        self.provider_names: Dict[str, str] = {}
        self.mosaic_names: Dict[str, str] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(16, 12, 16, 4)
        toolbar.setSpacing(6)
        self.chips = QButtonGroup(self)
        self.chip_buttons = {}
        for key, text in FILTERS:
            chip = QPushButton(text, self)
            chip.setProperty("chip", True)
            chip.setCheckable(True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.clicked.connect(lambda _=False, k=key: self._set_filter(k))
            self.chips.addButton(chip)
            self.chip_buttons[key] = chip
            toolbar.addWidget(chip)
        self.chip_buttons["all"].setChecked(True)
        toolbar.addStretch(1)
        outer.addLayout(toolbar)
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Find by name or model")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(icons.icon("search", tokens()["text2"], 16), QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(lambda _: self._render())
        search_row = QHBoxLayout()
        search_row.setContentsMargins(16, 4, 16, 4)
        search_row.addWidget(self.search, 1)
        refresh = tool("refresh", "Refresh")       # here, so the filter chips keep the full width
        refresh.clicked.connect(lambda *_: self.refreshRequested.emit())
        search_row.addWidget(refresh)
        outer.addLayout(search_row)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll = scroll
        body = QWidget()
        body.setObjectName("mfScrollBody")
        self.list = QVBoxLayout(body)
        self.list.setContentsMargins(16, 8, 16, 16)
        self.list.setSpacing(10)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        self.empty = QWidget(body)
        self.empty.setObjectName("mfScrollBody")
        empty_layout = QVBoxLayout(self.empty)
        empty_layout.setContentsMargins(0, 24, 0, 0)
        empty_layout.setSpacing(10)
        self.empty_text = label("No processings in this project yet.", "lead", wrap=True)
        self.empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start = button("Start mapping", "primary", "play")
        start.clicked.connect(lambda *_: self.startRequested.emit())
        self.start_button = start
        empty_layout.addWidget(self.empty_text)
        empty_layout.addWidget(start, 0, Qt.AlignmentFlag.AlignHCenter)
        footer = QHBoxLayout()
        footer.setContentsMargins(16, 0, 16, 10)
        footer.addWidget(link("Statistics and sharing in Mapflow Web", config.WEB_URL))
        footer.addStretch(1)
        outer.addLayout(footer)

    def _set_filter(self, key: str) -> None:
        self.filter = key
        self._render()

    def counts(self) -> Dict[str, int]:
        return {"all": len(self.items),
                "running": sum(1 for p in self.items if p.is_running),
                "done": sum(1 for p in self.items if p.is_done and not p.needs_review),
                "attention": sum(1 for p in self.items if p.status is Status.failed or p.needs_review)}

    def set_items(self, items: List[Processing], in_map: set, busy: set, can_manage: bool, loading: bool = False,
                  total: int = 0, loading_more: bool = False) -> None:
        self.items, self.in_map, self.busy, self.can_manage = items, in_map, busy, can_manage
        self.loading, self.total, self.loading_more = loading, max(total, len(items)), loading_more
        if self.expanded is None and items:
            self.expanded = items[0].id
        self._render()

    def expand(self, processing_id: str) -> None:
        self.expanded = processing_id
        self.filter = "all"
        self.chip_buttons["all"].setChecked(True)
        self._render()

    def _visible(self) -> List[Processing]:
        needle = self.search.text().strip().lower()
        result = []
        for p in self.items:
            if self.filter == "running" and not p.is_running:
                continue
            if self.filter == "done" and not (p.is_done and not p.needs_review):
                continue
            if self.filter == "attention" and not (p.status is Status.failed or p.needs_review):
                continue
            if needle and needle not in f"{p.name} {p.model_name}".lower():
                continue
            result.append(p)
        return result

    def _render(self) -> None:
        self.list.removeWidget(self.empty)
        bar = self.scroll.verticalScrollBar()
        position = bar.value()
        clear_layout(self.list)
        counts = self.counts()
        for key, text in FILTERS:
            self.chip_buttons[key].setText(f"{text} {counts[key]}" if counts[key] else text)
        visible = self._visible()
        for processing in visible:
            card = ProcessingCard(processing, source_text(processing, self.provider_names, self.mosaic_names),
                                  processing.id in self.in_map, processing.id in self.busy,
                                  processing.id == self.expanded, self)
            card.clicked.connect(self._toggle)
            self.list.addWidget(card)
        if self.loading:
            self.empty_text.setText("Loading processings…")
        else:
            self.empty_text.setText("No processings in this project yet." if not self.items
                                    else "Nothing matches this filter.")
        self.start_button.setVisible(not self.loading and not self.items)
        self.list.addWidget(self.empty)
        self.empty.setVisible(not visible)
        if self.items and len(self.items) < self.total:
            # Older processings: one page at a time (filters and search apply to the loaded ones)
            more = button("Loading…" if self.loading_more else
                          f"Show more · {len(self.items):,} of {self.total:,}", "outline")
            more.setEnabled(not self.loading_more)
            more.clicked.connect(lambda *_: self.moreRequested.emit())
            self.more_button = more
            self.list.addWidget(more, 0, Qt.AlignmentFlag.AlignHCenter)
        else:
            self.more_button = None
        self.list.addStretch(1)
        bar.setValue(position)
        QTimer.singleShot(0, lambda: bar.setValue(position))   # polling re-renders: keep the reader's place

    def _toggle(self, processing_id: str) -> None:
        self.expanded = None if self.expanded == processing_id else processing_id
        self._render()
