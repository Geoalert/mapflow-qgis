"""Start: pick a scenario (or set up a run by hand), see what ran recently."""
from __future__ import annotations

from typing import List, Optional

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QLineEdit, QProgressBar, QScrollArea, QVBoxLayout,
                                 QWidget)

from .. import config
from ..core import formatting
from ..core.models import Processing
from ..core.scenarios import Catalogue, Scenario
from . import icons
from .theme import tokens
from .widgets import Card, ElidedLabel, ImageTile, Pill, button, clear_layout, label, link, placeholder, vbox


def scenario_pixmap(catalogue: Catalogue, scenario: Scenario, width: int = 170, height: int = 88) -> QPixmap:
    path = catalogue.image_path(scenario)
    if path and path.exists():
        return QPixmap(str(path))
    return placeholder(scenario.icon or ("search" if scenario.imagery_hint == "search" else "image"), width, height)


def plain(text: str) -> str:
    """A label without the leading emoji the API puts on model names."""
    text = (text or "").strip()
    while text and not text[0].isalnum() and text[0] not in "[(":
        text = text[1:].lstrip()
    return text


def status_pill(processing: Processing, in_map: bool) -> tuple:
    if processing.needs_review:
        return "Review required", "warn"
    if processing.is_running:
        return f"Running · {processing.percent}%", "run"
    if processing.is_done:
        return ("✓ In map", "ok") if in_map else ("Done", "ok")
    return {"FAILED": ("Failed", "err"), "REFUNDED": ("Refunded", "gray"),
            "CANCELLED": ("Cancelled", "gray")}.get(processing.status.value, (processing.status.value.title(), "gray"))


def model_icon(model_name: str) -> Optional[str]:
    name = (model_name or "").lower()
    if "building" in name and ("road" in name or "forest" in name):
        return "cityscape"
    for key, icon_name in (("building", "buildings"), ("forest", "forest"), ("tree", "forest"), ("road", "road"),
                           ("construction", "crane"), ("field", "tractor"), ("segment", "segment-anything"),
                           ("housing", "cityscape")):
        if key in name:
            return icon_name
    return None


class StartPage(QWidget):
    scenarioChosen = pyqtSignal(str)
    galleryRequested = pyqtSignal(str)        # search text to start with
    customRequested = pyqtSignal()
    processingsRequested = pyqtSignal()

    def __init__(self, catalogue: Catalogue, parent=None):
        super().__init__(parent)
        self.catalogue = catalogue
        self.setObjectName("mfPage")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("mfScrollBody")
        scroll.setWidget(body)
        outer.addWidget(scroll)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        layout.addLayout(vbox(label("What do you want to map?", "h1", wrap=True),
                              label("Pick a scenario. The model, options and zoom are set for you.", "lead", wrap=True),
                              spacing=4))
        self.search = QLineEdit(body)
        self.search.setPlaceholderText("Search: trees, roads, solar panels…")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(icons.icon("search", tokens()["text2"], 16), QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(self._filter)
        self.search.returnPressed.connect(lambda: self.galleryRequested.emit(self.search.text()))
        layout.addWidget(self.search)

        self.grid = QGridLayout()
        self.grid.setSpacing(12)
        layout.addLayout(self.grid)
        self.no_match = label("", "meta", wrap=True)
        layout.addWidget(self.no_match)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.all_button = button(f"All {len(catalogue.scenarios)} scenarios", "outline", "grid")
        self.all_button.clicked.connect(lambda: self.galleryRequested.emit(self.search.text()))
        custom = button("Custom setup", "ghost", "sliders")
        custom.clicked.connect(self.customRequested.emit)
        actions.addWidget(self.all_button, 1)
        actions.addWidget(custom)
        layout.addLayout(actions)
        agent = link("Describe your task to the Mapflow AI Agent", config.WEB_URL)
        agent.setIcon(icons.icon("message", tokens()["link"], 14))
        layout.addWidget(agent)

        header = QHBoxLayout()
        self.recent_title = label("Recent", "label")
        see_all = link("See all", external=False)
        see_all.clicked.connect(self.processingsRequested.emit)
        header.addWidget(self.recent_title, 1)
        header.addWidget(see_all)
        self.recent_box = QVBoxLayout()
        self.recent_box.setSpacing(8)
        self.recent = QWidget(body)
        self.recent.setObjectName("mfScrollBody")
        recent_layout = vbox(header, self.recent_box, spacing=8)
        self.recent.setLayout(recent_layout)
        layout.addWidget(self.recent)
        layout.addStretch(1)
        self._tiles: List[ImageTile] = []
        self._filter("")

    def _filter(self, text: str) -> None:
        for tile in self._tiles:
            self.grid.removeWidget(tile)
            tile.hide()
            tile.deleteLater()
        self._tiles = []
        found = [s for s in self.catalogue.search(text) if not s.custom] if text.strip() else self.catalogue.popular(4)
        for index, scenario in enumerate(found[:4]):
            tile = ImageTile(scenario.title, f"{plain(scenario.model_label)} · {scenario.price_short.split(' +')[0]}",
                             scenario_pixmap(self.catalogue, scenario), scenario.icon)
            tile.setToolTip(scenario.short)
            tile.clicked.connect(lambda _=False, sid=scenario.id: self.scenarioChosen.emit(sid))
            self.grid.addWidget(tile, index // 2, index % 2)
            self._tiles.append(tile)
        more = len(found) - 4
        if not found:
            self.no_match.setText("No scenario matches that. Open all scenarios, or set up a run by hand.")
        elif more > 0:
            self.no_match.setText(f"{more} more in All scenarios.")
        else:
            self.no_match.setText("")
        self.no_match.setVisible(bool(self.no_match.text()))

    def set_recent(self, project_name: str, processings: List[Processing], in_map: set) -> None:
        self.recent_title.setText(f"Recent in {project_name}" if project_name else "Recent")
        clear_layout(self.recent_box)
        for processing in processings[:2]:
            self.recent_box.addWidget(_MiniCard(processing, processing.id in in_map))
        self.recent.setVisible(bool(processings))


class _MiniCard(Card):
    def __init__(self, processing: Processing, in_map: bool):
        super().__init__(margins=(12, 10, 12, 10), spacing=6)
        row = QHBoxLayout()
        row.setSpacing(10)
        badge = QLabel(self)
        badge.setFixedSize(34, 34)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"background: {tokens()['icon_button']}; border-radius: 8px;")
        badge.setPixmap(icons.pixmap(model_icon(processing.model_name) or "layers", tokens()["ink"], 18))
        row.addWidget(badge)
        texts = QVBoxLayout()
        texts.setSpacing(4)
        top = QHBoxLayout()
        top.setSpacing(6)
        top.addWidget(ElidedLabel(processing.name, "title"), 1)
        text, kind = status_pill(processing, in_map)
        top.addWidget(Pill(text, kind))
        texts.addLayout(top)
        if processing.is_running:
            bar = QProgressBar(self)
            bar.setTextVisible(False)
            bar.setValue(processing.percent)
            texts.addWidget(bar)
        else:
            meta = [formatting.km2(processing.area_km2)]
            if processing.cost:
                meta.append(f"{processing.cost:,} credits")
            meta.append(formatting.when(processing.created))
            texts.addWidget(label(" · ".join(m for m in meta if m), "meta"))
        row.addLayout(texts, 1)
        self.add(row)
