"""Processings of the current project as cards: status at a glance, actions on the selected one."""
from __future__ import annotations

import time
from typing import Dict, List, Optional

from qgis.PyQt.QtCore import Qt, QTimer, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QTransform
from qgis.PyQt.QtWidgets import (QButtonGroup, QHBoxLayout, QLineEdit, QMenu, QProgressBar, QPushButton, QScrollArea,
                                 QSizePolicy, QToolButton, QVBoxLayout, QWidget)

from .. import config
from ..core import formatting
from ..core.failures import empty_list_text
from ..core.messages import describe
from ..core.models import Processing, Status
from . import icons
from .start_page import model_icon, status_pill
from .theme import set_prop, tokens
from .widgets import (Card, ElidedLabel, Pill, Stars, button, clear_layout, event_pos, label, link, menu_action,
                      rule, tool)
from ..core.guard import guarded

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
                add.clicked.connect(guarded(lambda *_: page.zoomTo.emit(pid)))
            else:
                add = button("Add to map", "primary", "layers", size="sm")
                add.clicked.connect(guarded(lambda *_: page.addToMap.emit(pid)))
            row.addWidget(add, 1)
            save = button("GeoJSON", "outline", "download", size="sm")
            save.setToolTip("Save the results as a GeoJSON file")
            save.setEnabled(not busy)
            save.clicked.connect(guarded(lambda *_: page.saveGeojson.emit(pid)))
            row.addWidget(save)
        elif processing.status.can_restart and page.can_run:
            restart = button("Restart", "outline", "refresh", size="sm")
            restart.clicked.connect(guarded(lambda *_: page.restart.emit(pid)))
            row.addWidget(restart)
            row.addStretch(1)
        else:
            row.addStretch(1)
        more = tool("more", "More: run again, rename, download the area, delete")
        menu = QMenu(more)
        menu_action(menu, "copy", "Run again with these settings", lambda: page.duplicate.emit(pid))
        if page.can_manage:
            menu_action(menu, "edit", "Rename…", lambda: page.rename.emit(pid))
        menu_action(menu, "download", "Download the area (AOI)…", lambda: page.downloadAoi.emit(pid))
        menu_action(menu, "globe", "Open in Mapflow Web", lambda: page.openWeb.emit(pid))
        if page.can_manage:
            menu.addSeparator()
            menu_action(menu, "trash", "Delete…", lambda: page.delete.emit(pid), tokens()["err_fg"])
        more.setMenu(menu)
        more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        row.addWidget(more)
        self.add(row)

        if processing.needs_review:
            self.add(link("Review this result in Mapflow Web", on_click=lambda: page.openWeb.emit(pid)))
        if processing.is_done:
            self.add(rule())
            rating = QHBoxLayout()
            rating.setSpacing(6)
            rated = page.ratings.get(pid, 0)
            rating.addWidget(label("Your rating" if rated else "Rate the result", "label"))
            stars = Stars(self)
            stars.set_value(rated)
            stars.rated.connect(guarded(lambda value: page.rate.emit(pid, value)))   # opens the feedback form
            rating.addWidget(stars)
            rating.addStretch(1)
            self.add(rating)

    @guarded
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
    rate = pyqtSignal(str, int)             # a star was clicked: the feedback form opens, nothing is sent yet
    downloadAoi = pyqtSignal(str)
    startRequested = pyqtSignal()
    refreshRequested = pyqtSignal()
    moreRequested = pyqtSignal()
    searchChanged = pyqtSignal(str)         # the trimmed text, once typing pauses (at once when it is empty)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mfPage")
        self.items: List[Processing] = []
        self.expanded: Optional[str] = None
        self.filter = "all"
        self.in_map: set = set()
        self.busy: set = set()
        self.can_manage = True
        self.can_run = True
        self.loading = False
        self.loaded, self.failed = True, False
        self.loading_more = False
        self.total = 0
        self.terms = ""                             # the terms the list shown answers (the field may be ahead)
        self._scroll_pending: Optional[str] = None
        self.provider_names: Dict[str, str] = {}
        self.mosaic_names: Dict[str, str] = {}
        self.ratings: Dict[str, int] = {}           # processing id → the rating sent from here
        self._spin = QTimer(self)
        self._spin.setInterval(40)
        self._spin.timeout.connect(self._turn)
        self._angle = 0
        self._spin_until = 0.0

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
            chip.clicked.connect(guarded(lambda _=False, k=key: self._set_filter(k)))
            self.chips.addButton(chip)
            self.chip_buttons[key] = chip
            toolbar.addWidget(chip)
        self.chip_buttons["all"].setChecked(True)
        toolbar.addStretch(1)
        outer.addLayout(toolbar)
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Find by name")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(icons.icon("search", tokens()["text2"], 16), QLineEdit.ActionPosition.LeadingPosition)
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(config.PROCESSINGS_SEARCH_DEBOUNCE_MS)
        self._debounce.timeout.connect(guarded(lambda: self.searchChanged.emit(self.search.text().strip())))
        self.search.textChanged.connect(guarded(lambda _: self._typed()))
        search_row = QHBoxLayout()
        search_row.setContentsMargins(16, 4, 16, 4)
        search_row.addWidget(self.search, 1)
        refresh = tool("refresh", "Refresh")       # here, so the filter chips keep the full width
        refresh.clicked.connect(guarded(lambda *_: (self.set_refreshing(True), self.refreshRequested.emit())))
        search_row.addWidget(refresh)
        self.refresh_button = refresh
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
        self.empty_text = label("Loading processings…", "lead", wrap=True)
        self.empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start = button("Start mapping", "primary", "play")
        start.clicked.connect(guarded(lambda *_: self.startRequested.emit()))
        self.start_button = start
        empty_layout.addWidget(self.empty_text)
        empty_layout.addWidget(start, 0, Qt.AlignmentFlag.AlignHCenter)
        footer = QHBoxLayout()
        footer.setContentsMargins(16, 0, 16, 10)
        footer.addWidget(link("Statistics and sharing in Mapflow Web", config.WEB_URL))
        footer.addStretch(1)
        outer.addLayout(footer)

    # ---------- refreshing ----------

    def set_refreshing(self, on: bool) -> None:
        """The Refresh button turns while the list is on its way (at least half a second, so a fast
        answer still shows that something happened)."""
        if on:
            self._spin_until = time.monotonic() + 0.5
            self.refresh_button.setEnabled(False)
            self._spin.start()
        elif self._spin.isActive():
            if time.monotonic() < self._spin_until:
                QTimer.singleShot(int((self._spin_until - time.monotonic()) * 1000) + 10,
                                  guarded(lambda: self.set_refreshing(False)))
                return
            self._spin.stop()
            self._angle = 0
            self.refresh_button.setIcon(icons.icon("refresh", tokens()["ink"], 16))
            self.refresh_button.setEnabled(True)

    @property
    def refreshing(self) -> bool:
        return self._spin.isActive()

    @guarded
    def _turn(self) -> None:
        self._angle = (self._angle + 30) % 360
        pixmap = icons.pixmap("refresh", tokens()["primary_ink"], 16)
        turned = pixmap.transformed(QTransform().rotate(self._angle), Qt.TransformationMode.SmoothTransformation)
        side = pixmap.width()
        x, y = (turned.width() - side) // 2, (turned.height() - side) // 2
        frame = turned.copy(x, y, side, side)
        frame.setDevicePixelRatio(pixmap.devicePixelRatio())
        self.refresh_button.setIcon(QIcon(frame))

    def _typed(self) -> None:
        """The text of the field changed: the search goes to Mapflow once typing pauses. Nothing is filtered here."""
        if self.search.text().strip():
            self._debounce.start()
        else:
            self._debounce.stop()               # nothing to wait for: the full list is asked for at once
            self.searchChanged.emit("")

    def clear_search(self) -> None:
        """Empty the field without a search (a new project starts with the full list)."""
        self._debounce.stop()
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)

    def _set_filter(self, key: str) -> None:
        self.filter = key
        self._render()

    def counts(self) -> Dict[str, int]:
        """All: every processing in the project. The others count the loaded pages, the only ones
        whose status is known."""
        return {"all": self.total,
                "running": sum(1 for p in self.items if p.is_running),
                "done": sum(1 for p in self.items if p.is_done and not p.needs_review),
                "attention": sum(1 for p in self.items if p.status is Status.failed or p.needs_review)}

    def set_items(self, items: List[Processing], in_map: set, busy: set, can_manage: bool, loading: bool = False,
                  total: int = 0, loading_more: bool = False, loaded: bool = True, failed: bool = False,
                  can_run: bool = True, terms: str = "") -> None:
        """`loaded`: a list of this project came back. `failed`: the last answer was a failure. The "no
        processings" text needs a successful answer with no items. `terms`: the search the list answers."""
        self.items, self.in_map, self.busy, self.can_manage = items, in_map, busy, can_manage
        self.loading, self.total, self.loading_more = loading, max(total, len(items)), loading_more
        self.loaded, self.failed, self.can_run, self.terms = loaded, failed, can_run, terms
        if self.expanded is None and items:
            self.expanded = items[0].id
        self._render()

    def expand(self, processing_id: str) -> None:
        """Open one processing: shown, expanded and scrolled to."""
        self.expanded = processing_id
        self.filter = "all"
        self.chip_buttons["all"].setChecked(True)
        self._scroll_pending = processing_id
        if self.search.text():
            self.search.clear()                 # or the search may hide it: the full list is asked for at once
        self._render()

    def _scroll_to(self, processing_id: str) -> None:
        cards = (self.list.itemAt(i).widget() for i in range(self.list.count()))
        card = next((w for w in cards if isinstance(w, ProcessingCard) and w.processing.id == processing_id), None)
        if card is not None:
            self.scroll.ensureWidgetVisible(card, 0, 40)

    def _visible(self) -> List[Processing]:
        result = []
        for p in self.items:
            if self.filter == "running" and not p.is_running:
                continue
            if self.filter == "done" and not (p.is_done and not p.needs_review):
                continue
            if self.filter == "attention" and not (p.status is Status.failed or p.needs_review):
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
        partial = len(self.items) < self.total
        if not self.items:
            if self.terms and self.loaded and not self.loading and not self.failed:
                self.empty_text.setText(f"No processings match “{self.terms}”.")
            else:
                self.empty_text.setText(empty_list_text("processings", "No processings in this project yet.",
                                                        self.loaded, self.loading, self.failed))
        elif partial:
            self.empty_text.setText(f"Nothing matches this filter among the latest {len(self.items):,} of "
                                    f"{self.total:,} processings.")
        else:
            self.empty_text.setText("Nothing matches this filter.")
        self.start_button.setVisible(self.loaded and not self.failed and not self.loading and not self.items
                                     and not self.terms)
        self.list.addWidget(self.empty)
        self.empty.setVisible(not visible)
        if visible and partial:
            # Older processings, one page at a time. The status filters apply to the loaded ones; with
            # nothing shown, a button whose pages may show nothing either would read as broken.
            more = button("Loading…" if self.loading_more else
                          f"Show more · {len(self.items):,} of {self.total:,}", "outline")
            more.setEnabled(not self.loading_more)
            more.clicked.connect(guarded(lambda *_: self.moreRequested.emit()))
            self.more_button = more
            self.list.addWidget(more, 0, Qt.AlignmentFlag.AlignHCenter)
        else:
            self.more_button = None
        self.list.addStretch(1)
        bar.setValue(position)
        QTimer.singleShot(0, guarded(lambda: bar.setValue(position)))   # polling re-renders: keep the reader's place
        if self._scroll_pending and not self.loading:
            target, self._scroll_pending = self._scroll_pending, None
            QTimer.singleShot(0, guarded(lambda: self._scroll_to(target)))     # after the scroll above is restored

    @guarded
    def _toggle(self, processing_id: str) -> None:
        self.expanded = None if self.expanded == processing_id else processing_id
        self._render()
