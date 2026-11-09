"""Imagery: search the catalog over your area, or use your own collections (My imagery)."""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Tuple

from qgis.PyQt.QtCore import QDate, Qt, pyqtSignal
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import (QComboBox, QDateEdit, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton,
                                 QScrollArea, QSlider, QVBoxLayout, QWidget)

from .. import config
from ..core import formatting
from ..core.models import CatalogImage, Mosaic
from . import icons
from .theme import tokens
from .widgets import (Callout, Card, ElidedLabel, Pill, Segmented, button, clear_layout, label, link, placeholder,
                      rounded, tool, vbox)


class ImageryPage(QWidget):
    searchRequested = pyqtSignal(dict)
    useImage = pyqtSignal(str)
    showImage = pyqtSignal(str)
    useMosaic = pyqtSignal(str)
    showMosaic = pyqtSignal(str)
    uploadRequested = pyqtSignal()
    useMapExtent = pyqtSignal()
    layerChosen = pyqtSignal(str)
    clearRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mfPage")
        self._thumbs: Dict[str, QLabel] = {}
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
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(12)
        self.tabs = Segmented(["Search the catalog", "My imagery"])
        layout.addWidget(self.tabs)
        # Two panes shown one at a time. Not a stacked widget: that is as tall as its tallest page, which
        # left a long empty space under a short list
        self.panes = [self._build_search(), self._build_mine()]
        for pane in self.panes:
            layout.addWidget(pane)
        self.tabs.changed.connect(self.show_tab)
        layout.addStretch(1)
        self.scroll = scroll
        self.show_tab(0)

    def show_tab(self, index: int) -> None:
        if self.tabs.index() != index:
            self.tabs.set_index(index)
        for position, pane in enumerate(self.panes):
            pane.setVisible(position == index)
        self.scroll.verticalScrollBar().setValue(0)

    def current_tab(self) -> int:
        return next((i for i, pane in enumerate(self.panes) if not pane.isHidden()), 0)

    # ---------- search ----------

    def _build_search(self) -> QWidget:
        page = QWidget()
        page.setObjectName("mfScrollBody")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        form = Card(spacing=10)
        area_row = QHBoxLayout()
        area_row.addWidget(label("Area", "label"))
        area_row.addStretch(1)
        self.extent_button = button("Use map view", "ghost", "maximize", size="sm")
        self.extent_button.clicked.connect(lambda *_: self.useMapExtent.emit())
        area_row.addWidget(self.extent_button)
        form.add(area_row)
        # The same area as the run form: choosing a layer here sets it there too
        self.layer_combo = QComboBox(form)
        self.layer_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.layer_combo.setMinimumContentsLength(12)
        self.layer_combo.setToolTip("The area to search over: a polygon layer (the same area as on Start)")
        self.layer_combo.activated.connect(self._layer_activated)
        self._layer_ids: List[str] = []
        form.add(self.layer_combo)
        self.area_text = label("Set an area on Start, or use the map view.", "meta")
        form.add(self.area_text)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)
        today = date.today()
        self.date_from = QDateEdit(QDate(today.year - 1, today.month, today.day))
        self.date_to = QDateEdit(QDate(today.year, today.month, today.day))
        for edit in (self.date_from, self.date_to):
            edit.setCalendarPopup(True)              # the calendar icon opens a month view
            edit.setDisplayFormat("d MMM yyyy")
            edit.setMaximumDate(QDate.currentDate())
            edit.setToolTip("Click the calendar icon to pick a date")
        self.date_from.dateChanged.connect(lambda d: self.date_to.setMinimumDate(d))
        self.date_to.dateChanged.connect(lambda d: self.date_from.setMaximumDate(d))
        for column, (text, widget) in enumerate((("From", self.date_from), ("To", self.date_to))):
            grid.addWidget(label(text, "label"), 0, column)
            grid.addWidget(widget, 1, column)
        form.add(grid)
        self.cloud, self.cloud_value = self._slider(form, "Max cloud cover", 0, 100, 20, 5, "{} %")
        self.nadir, self.nadir_value = self._slider(form, "Max off-nadir angle", 0, 50, 30, 5, "{}°")

        types = QHBoxLayout()
        types.setSpacing(6)
        types.addWidget(label("Type", "label"))
        self.type_mosaic = self._chip("Mosaics", True)
        self.type_image = self._chip("Scenes", True)
        types.addWidget(self.type_mosaic)
        types.addWidget(self.type_image)
        types.addStretch(1)
        form.add(types)
        self.search_button = button("Search imagery", "primary", "search")
        self.search_button.clicked.connect(lambda *_: self._emit_search())
        form.add(self.search_button)
        layout.addWidget(form)

        self.search_message = Callout("info", "")
        layout.addWidget(self.search_message)
        results_head = QHBoxLayout()
        self.results_title = label("", "title")
        results_head.addWidget(self.results_title, 1)
        self.clear_button = button("Clear", "ghost", "x", size="sm")
        self.clear_button.setToolTip("Clear the search results and their footprints on the map")
        self.clear_button.clicked.connect(lambda *_: self.clearRequested.emit())
        self.clear_button.setVisible(False)
        results_head.addWidget(self.clear_button)
        layout.addLayout(results_head)
        self.results = QVBoxLayout()
        self.results.setSpacing(8)
        layout.addLayout(self.results)
        layout.addWidget(link("Order scenes and connect providers in Mapflow Web", config.WEB_URL))
        layout.addStretch(1)
        return page

    def _chip(self, text: str, checked: bool) -> QPushButton:
        chip = QPushButton(text)
        chip.setProperty("chip", True)
        chip.setCheckable(True)
        chip.setChecked(checked)
        chip.setCursor(Qt.CursorShape.PointingHandCursor)
        return chip

    def _slider(self, form: Card, title: str, low: int, high: int, value: int, step: int, unit: str):
        head = QHBoxLayout()
        head.addWidget(label(title, "label"))
        head.addStretch(1)
        shown = label(unit.format(value), "value")
        head.addWidget(shown)
        form.add(head)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(low, high)
        slider.setSingleStep(1)
        slider.setPageStep(step)
        slider.setValue(value)
        slider.setAccessibleName(title)
        slider.valueChanged.connect(lambda v: shown.setText(unit.format(v)))
        form.add(slider)
        return slider, shown

    def _emit_search(self) -> None:
        # The API's product types are MOSAIC and IMAGE (a "Scene" in the results is an IMAGE)
        types = [t for t, chip in (("MOSAIC", self.type_mosaic), ("IMAGE", self.type_image)) if chip.isChecked()]
        self.searchRequested.emit({
            "date_from": self.date_from.date().toPyDate(), "date_to": self.date_to.date().toPyDate(),
            "max_cloud": float(self.cloud.value()), "max_off_nadir": float(self.nadir.value()),
            "product_types": types if len(types) == 1 else None,
        })

    def set_area(self, text: str, has_area: bool) -> None:
        self.area_text.setText(text)
        self.search_button.setEnabled(has_area)

    def set_layers(self, layers: List[Tuple[str, str]], selected: Optional[str]) -> None:
        self.layer_combo.blockSignals(True)
        self.layer_combo.clear()
        self._layer_ids = []
        if not selected:
            self.layer_combo.addItem("Choose a polygon layer…" if layers else "No polygon layers yet")
            self._layer_ids.append("")
        for layer_id, name in layers:
            self.layer_combo.addItem(icons.icon("map", tokens()["text2"], 14), name)
            self._layer_ids.append(layer_id)
        self.layer_combo.setCurrentIndex(self._layer_ids.index(selected) if selected in self._layer_ids else 0)
        self.layer_combo.blockSignals(False)

    def _layer_activated(self, index: int) -> None:
        if 0 <= index < len(self._layer_ids) and self._layer_ids[index]:
            self.layerChosen.emit(self._layer_ids[index])

    def set_searching(self, busy: bool) -> None:
        self.search_button.setEnabled(not busy)
        self.search_button.setText("Searching…" if busy else "Search imagery")

    def show_search_message(self, text: str, kind: str = "info") -> None:
        self.search_message.set(kind, text)

    def set_results(self, images: List[CatalogImage], total: int, chosen: Optional[str]) -> None:
        self._clear(self.results)
        self._thumbs = {}
        self.results_title.setText(f"{total:,} images over your area" if total else "")
        self.results_title.setVisible(bool(total))
        self.clear_button.setVisible(bool(images))
        for image in images:
            self.results.addWidget(self._result_card(image, image.id == chosen))

    def _result_card(self, image: CatalogImage, chosen: bool) -> Card:
        card = Card(margins=(10, 10, 10, 10))
        row = QHBoxLayout()
        row.setSpacing(10)
        thumb = QLabel(card)
        thumb.setFixedSize(56, 56)
        thumb.setPixmap(placeholder("image", 56, 56, 8))
        self._thumbs[image.id] = thumb
        row.addWidget(thumb)
        texts = QVBoxLayout()
        texts.setSpacing(3)
        top = QHBoxLayout()
        top.setSpacing(6)
        top.addWidget(ElidedLabel(_provider_label(image.provider), "title"), 1)
        top.addWidget(Pill("Mosaic" if image.is_mosaic else "Scene", "gray"))
        texts.addLayout(top)
        first = [f"{image.acquired.day} {image.acquired:%b %Y}" if image.acquired else "Date varies"]
        if image.cloud is not None:
            first.append(f"cloud {image.cloud:.0f}%")
        if image.off_nadir is not None:
            first.append(f"off-nadir {image.off_nadir:.0f}°")
        second = []
        if image.resolution:
            second.append(f"{image.resolution:.2f} m/px")
        if image.coverage is not None:
            second.append(f"covers {image.coverage:.0f}%")
        texts.addWidget(label(" · ".join(first), "meta"))
        if second:
            texts.addWidget(label(" · ".join(second), "meta"))
        row.addLayout(texts, 1)
        actions = QVBoxLayout()
        actions.setSpacing(4)
        show = tool("eye", "Show the footprint on the map", "plain")
        show.clicked.connect(lambda *_: self.showImage.emit(image.id))
        use = button("Chosen" if chosen else "Use", "outline" if chosen else "primary", size="sm")
        use.setEnabled(not chosen)
        use.clicked.connect(lambda *_: self.useImage.emit(image.id))
        actions.addWidget(show, 0, Qt.AlignmentFlag.AlignRight)
        actions.addWidget(use)
        row.addLayout(actions)
        card.add(row)
        return card

    def set_thumbnail(self, image_id: str, pixmap: QPixmap) -> None:
        thumb = self._thumbs.get(image_id)
        if thumb is not None and not pixmap.isNull():
            thumb.setPixmap(rounded(pixmap, 56, 56, 8))

    # ---------- My imagery ----------

    def _build_mine(self) -> QWidget:
        page = QWidget()
        page.setObjectName("mfScrollBody")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        upload = Card(spacing=8)
        upload.add(label("Your own imagery", "h2"))
        upload.add(label("Upload an RGB GeoTIFF (up to 1 GB) as a new collection. It costs no imagery credits "
                         "to process.", "meta", wrap=True))
        self.upload_button = button("Upload a GeoTIFF", "outline", "upload")
        self.upload_button.clicked.connect(lambda *_: self.uploadRequested.emit())
        upload.add(self.upload_button)
        self.upload_bar = QProgressBar()
        self.upload_bar.setTextVisible(False)
        self.upload_bar.setVisible(False)
        upload.add(self.upload_bar)
        self.upload_message = Callout("info", "")
        upload.add(self.upload_message)
        layout.addWidget(upload)
        self.mosaics_title = label("", "label")
        layout.addWidget(self.mosaics_title)
        self.mosaic_list = QVBoxLayout()
        self.mosaic_list.setSpacing(8)
        layout.addLayout(self.mosaic_list)
        layout.addWidget(link("Manage collections in Mapflow Web", config.WEB_URL))
        layout.addStretch(1)
        return page

    def set_mosaics(self, mosaics: List[Mosaic], chosen: Optional[str]) -> None:
        self._clear(self.mosaic_list)
        self.mosaics_title.setText(f"Collections · {len(mosaics)}" if mosaics else "No collections yet")
        for mosaic in mosaics:
            card = Card(margins=(12, 10, 10, 10))
            row = QHBoxLayout()
            row.setSpacing(10)
            badge = QLabel(card)
            badge.setPixmap(icons.pixmap("image", tokens()["text"], 18))
            row.addWidget(badge)
            count = "" if mosaic.image_count is None else \
                f"{mosaic.image_count} image" + ("" if mosaic.image_count == 1 else "s")
            meta = " · ".join(t for t in (count, formatting.size(mosaic.size_bytes) if mosaic.size_bytes else "",
                                          formatting.when(mosaic.created)) if t)
            row.addLayout(vbox(ElidedLabel(mosaic.name, "title"), label(meta, "meta"), spacing=2), 1)
            show = tool("eye", "Show on the map", "plain")
            show.clicked.connect(lambda *_, mid=mosaic.id: self.showMosaic.emit(mid))
            several = (mosaic.image_count or 0) > 1
            use = button("Chosen" if mosaic.id == chosen else ("Choose…" if several else "Use"),
                         "outline" if mosaic.id == chosen else "primary", size="sm")
            use.setToolTip("Pick the whole collection or one of its images" if several else "Process this collection")
            use.clicked.connect(lambda *_, mid=mosaic.id: self.useMosaic.emit(mid))
            row.addWidget(show)
            row.addWidget(use)
            card.add(row)
            self.mosaic_list.addWidget(card)

    def set_upload(self, percent: Optional[int], message: str = "", kind: str = "info") -> None:
        uploading = percent is not None
        self.upload_bar.setVisible(uploading)
        self.upload_bar.setValue(percent or 0)
        self.upload_button.setEnabled(not uploading)
        self.upload_button.setText(f"Uploading… {percent}%" if uploading else "Upload a GeoTIFF")
        self.upload_message.set(kind, message)

    @staticmethod
    def _clear(layout) -> None:
        clear_layout(layout)


def _provider_label(name: str) -> str:
    known = {"my_imagery_images": "My image", "my_imagery_mosaics": "My collection"}
    readable = (name or "Image").replace("_", " ").title() if (name or "").islower() else name or "Image"
    return known.get(name) or readable
