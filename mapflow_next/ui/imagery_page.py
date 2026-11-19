"""Imagery: search the catalog over your area, or use your own collections (My imagery)."""
from __future__ import annotations

from datetime import date
from typing import Callable, Dict, List, Optional, Tuple

from qgis.PyQt.QtCore import QDate, QSize, Qt, QTimer, pyqtSignal
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import (QComboBox, QDateEdit, QGridLayout, QHBoxLayout, QLabel, QProgressBar,
                                 QPushButton, QScrollArea, QSlider, QToolButton, QVBoxLayout, QWidget)

from .. import config
from ..core import formatting
from ..core.models import CatalogImage, Mosaic
from . import icons
from .layer_picker import pick_layers
from .theme import set_prop, tokens
from .widgets import (Callout, Card, Combo, DropCard, DropTarget, ElidedLabel, Pill, Segmented, button,
                      clear_layout, hbox, label, link, placeholder, release_focus, rounded, same_width, tool,
                      vbox)
from ..core.guard import guarded


MINE, SEARCH = 0, 1                             # the tabs: My imagery, Search the catalog


class ImageryPage(QWidget):
    searchRequested = pyqtSignal(dict)
    useImage = pyqtSignal(str)
    showImage = pyqtSignal(str)               # the eye: the image's preview on or off the map
    moreResults = pyqtSignal()
    useMosaic = pyqtSignal(str)
    showMosaic = pyqtSignal(str)
    moreMosaics = pyqtSignal()                # "Show more" under the collections: their next page
    uploadRequested = pyqtSignal()
    layerUploadRequested = pyqtSignal(list)   # GeoTIFF layers of the project, by layer id
    areaAction = pyqtSignal(str)              # draw | extent: the same actions as the run form's
    layerChosen = pyqtSignal(str)
    clearRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mfPage")
        self._thumbs: Dict[str, QLabel] = {}
        self._pixmaps: Dict[str, QPixmap] = {}      # loaded thumbnails, kept while the results are
        self._eyes: Dict[str, QToolButton] = {}
        self._uses: List[QPushButton] = []        # the results' Use buttons
        self.more_button: Optional[QPushButton] = None
        self._mosaic_keys: List[tuple] = []           # what each drawn collection card shows, in order
        self._mosaic_uses: List[QPushButton] = []     # their Use / Chosen / Choose… buttons
        self._use_width = 0                           # the width those buttons share
        # (layer id, name) of the project's GeoTIFF layers, asked for when the menu opens; the controller sets it
        self.geotiff_layers: Callable[[], List[Tuple[str, str]]] = lambda: []
        # (file, name) of the GeoTIFFs a drag carries; the controller sets it
        self.parse_drop: Callable[[object], List[Tuple[str, str]]] = lambda mime: []
        self.my_data_url = config.WEB_URL + config.MY_DATA_PATH     # the controller sets the environment's
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
        self.tabs = Segmented(["My imagery", "Search the catalog"])
        layout.addWidget(self.tabs)
        # Two panes shown one at a time (MINE, SEARCH). Not a stacked widget: that is as tall as its tallest
        # page, which left a long empty space under a short list
        self.panes = [self._build_mine(), self._build_search()]
        for pane in self.panes:
            layout.addWidget(pane)
        self.tabs.changed.connect(self.show_tab)
        layout.addStretch(1)
        self.scroll = scroll
        self.show_tab(MINE)                         # your own imagery first

    @guarded
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
        self.draw_button = button("Draw", "ghost", "pen")
        self.draw_button.setToolTip("Draw a polygon on the map: click corners, double-click to finish")
        self.draw_button.clicked.connect(guarded(lambda *_: self.areaAction.emit("draw")))
        self.extent_button = button("Use map view", "ghost", "maximize")
        self.extent_button.clicked.connect(guarded(lambda *_: self.areaAction.emit("extent")))
        for item in (self.draw_button, self.extent_button):
            item.setProperty("compact", True)
            item.setIconSize(QSize(13, 13))
            area_row.addWidget(item)
        form.add(area_row)
        # The same area as the run form: choosing a layer here sets it there too
        self.layer_combo = Combo(form)
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
        self.date_from.dateChanged.connect(guarded(lambda d: self.date_to.setMinimumDate(d)))
        self.date_to.dateChanged.connect(guarded(lambda d: self.date_from.setMaximumDate(d)))
        for column, (text, widget) in enumerate((("From", self.date_from), ("To", self.date_to))):
            grid.addWidget(label(text, "label"), 0, column)
            grid.addWidget(widget, 1, column)
        form.add(grid)
        self.cloud, self.cloud_value = self._slider(form, "Max cloud cover", 0, 100, 20, 5, "{} %")
        self.nadir, self.nadir_value = self._slider(form, "Max off-nadir angle", 0, 50, 30, 5, "{}°")
        self.coverage, self.coverage_value = self._slider(form, "Min area coverage", 0, 100, 20, 10, "{} %")
        self.coverage.setToolTip("Only images that cover at least this share of the area. 0: any overlap")

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
        self.search_button.clicked.connect(guarded(lambda *_: self._emit_search()))
        form.add(self.search_button)
        layout.addWidget(form)

        self.search_message = Callout("info", "")
        layout.addWidget(self.search_message)
        results_head = QHBoxLayout()
        self.results_title = label("", "title")
        results_head.addWidget(self.results_title, 1)
        self.clear_button = button("Clear", "ghost", "x", size="sm")
        self.clear_button.setToolTip("Clear the search results and their footprints on the map")
        self.clear_button.clicked.connect(guarded(lambda *_: self.clearRequested.emit()))
        self.clear_button.setVisible(False)
        results_head.addWidget(self.clear_button)
        layout.addLayout(results_head)
        self.results = QVBoxLayout()
        self.results.setSpacing(8)
        layout.addLayout(self.results)
        layout.addWidget(link("Get advanced imagery search tools in Mapflow Web", config.WEB_URL))
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
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(low, high)
        slider.setSingleStep(1)
        slider.setPageStep(step)
        slider.setValue(value)
        slider.setAccessibleName(title)
        slider.valueChanged.connect(guarded(lambda v: shown.setText(unit.format(v))))
        form.add(vbox(head, slider, spacing=0))     # the title sits right on its slider
        return slider, shown

    def _emit_search(self) -> None:
        # The API's product types are MOSAIC and IMAGE (a "Scene" in the results is an IMAGE)
        types = [t for t, chip in (("MOSAIC", self.type_mosaic), ("IMAGE", self.type_image)) if chip.isChecked()]
        self.searchRequested.emit({
            "date_from": self.date_from.date().toPyDate(), "date_to": self.date_to.date().toPyDate(),
            "max_cloud": float(self.cloud.value()), "max_off_nadir": float(self.nadir.value()),
            "min_coverage": float(self.coverage.value()) or None,
            "product_types": types if len(types) == 1 else None,
        })

    def set_drawing(self, active: bool) -> None:
        self.draw_button.setText("Drawing…" if active else "Draw")

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

    @guarded
    def _layer_activated(self, index: int) -> None:
        if 0 <= index < len(self._layer_ids) and self._layer_ids[index]:
            self.layerChosen.emit(self._layer_ids[index])

    def set_searching(self, busy: bool) -> None:
        self.search_button.setEnabled(not busy)
        self.search_button.setText("Searching…" if busy else "Search imagery")

    def show_search_message(self, text: str, kind: str = "info") -> None:
        self.search_message.set(kind, text)

    def set_results(self, images: List[CatalogImage], total: int, chosen: Optional[str],
                    previewing: Optional[set] = None, loading_more: bool = False) -> None:
        self._clear(self.results)
        self._thumbs, self._eyes = {}, {}
        if not images:
            self._pixmaps = {}
        self.results_title.setText(f"{total:,} images over your area" if total else "")
        self.results_title.setVisible(bool(total))
        self.clear_button.setVisible(bool(images))
        self._uses = []                             # Use and Chosen: one width
        for image in images:
            self.results.addWidget(self._result_card(image, image.key == chosen))
        same_width(self._uses)
        self.set_previewing(previewing or set())
        if images and len(images) < total:
            more = button("Loading…" if loading_more else f"Show more · {len(images):,} of {total:,}", "outline",
                          size="sm")
            more.setEnabled(not loading_more)
            more.clicked.connect(guarded(lambda *_: self.moreResults.emit()))
            self.results.addWidget(more)
            self.more_button = more
        else:
            self.more_button = None

    def set_previewing(self, image_ids: set) -> None:
        """Which results have their preview on the map: their eye shows it as on."""
        for image_id, eye in self._eyes.items():
            on = image_id in image_ids
            eye.setIcon(icons.icon("eye", tokens()["primary_ink" if on else "ink"], 16))
            eye.setToolTip("Hide the preview" if on else "Show the preview and the footprint on the map")
            set_prop(eye, "on", on)

    def _result_card(self, image: CatalogImage, chosen: bool) -> Card:
        card = Card(margins=(10, 10, 10, 10))
        row = QHBoxLayout()
        row.setSpacing(10)
        thumb = QLabel(card)
        thumb.setFixedSize(56, 56)
        cached = self._pixmaps.get(image.key)
        thumb.setPixmap(rounded(cached, 56, 56, 8) if cached is not None else placeholder("image", 56, 56, 8))
        self._thumbs[image.key] = thumb
        row.addWidget(thumb)
        texts = QVBoxLayout()
        texts.setSpacing(3)
        texts.addWidget(ElidedLabel(_provider_label(image.provider), "title"))
        first = [f"{image.acquired.day} {image.acquired:%b %Y}" if image.acquired else "Date varies"]
        if image.cloud is not None:
            first.append(f"cloud {image.cloud:.0f}%")
        if image.off_nadir is not None:
            first.append(f"off-nadir {image.off_nadir:.0f}°")
        second = []
        if image.resolution:
            second.append(f"{image.resolution:.2f} m/px" + (f" (z{image.zoom})" if image.zoom else ""))
        elif image.zoom:
            second.append(f"z{image.zoom}")
        if image.coverage is not None:
            second.append(f"covers {image.coverage:.0f}%")
        texts.addWidget(label(" · ".join(first), "meta"))
        if second:
            texts.addWidget(label(" · ".join(second), "meta"))
        row.addLayout(texts, 1)
        show = tool("eye", "Show the preview and the footprint on the map", "plain")
        show.clicked.connect(guarded(lambda *_: self.showImage.emit(image.key)))
        self._eyes[image.key] = show
        use = button("Chosen" if chosen else "Use", "outline" if chosen else "primary", size="sm")
        use.setEnabled(not chosen)
        self._uses.append(use)
        use.clicked.connect(guarded(lambda *_: self.useImage.emit(image.key)))
        # The kind, the eye and Use on one line, centred in the card
        pill = Pill("Mosaic" if image.is_mosaic else "Scene", "gray")
        actions = hbox(pill, show, use, spacing=8)
        for widget in (pill, show, use):
            actions.setAlignment(widget, Qt.AlignmentFlag.AlignVCenter)
        row.addLayout(actions)
        row.setAlignment(actions, Qt.AlignmentFlag.AlignVCenter)
        card.add(row)
        return card

    def set_thumbnail(self, image_id: str, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            return
        self._pixmaps[image_id] = pixmap
        thumb = self._thumbs.get(image_id)
        if thumb is not None:
            thumb.setPixmap(rounded(pixmap, 56, 56, 8))

    def has_thumbnail(self, image_id: str) -> bool:
        return image_id in self._pixmaps

    def forget_thumbnails(self) -> None:
        self._pixmaps = {}

    # ---------- My imagery ----------

    def _build_mine(self) -> QWidget:
        page = QWidget()
        page.setObjectName("mfScrollBody")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        upload = DropCard(margins=(20, 17, 20, 17), spacing=8)     # room inside the dashed line
        upload.add(hbox(label("Your own imagery", "h2"), None, label("Drag GeoTIFF layers or files here", "meta")))
        upload.add(vbox(4, label("Upload RGB GeoTIFFs, up to 2 GB each, as a new collection.", "meta", wrap=True),
                        label("It costs no imagery credits to process.", "meta", wrap=True), 4, spacing=0))
        self.drop = DropTarget(upload, lambda mime: self.parse_drop(mime))
        self.upload_button = button("Upload a GeoTIFF", "outline", "upload")
        self.upload_button.clicked.connect(guarded(lambda *_: self.uploadRequested.emit()))
        self.layer_button = button("Choose from raster layers", "outline", "layers")
        self.layer_button.clicked.connect(guarded(lambda *_: self._choose_layers()))
        # The two ways in, side by side and sharing the width
        buttons = hbox(self.upload_button, self.layer_button, spacing=8)
        buttons.setStretch(0, 1)
        buttons.setStretch(1, 1)
        for item in (self.upload_button, self.layer_button):
            item.setMinimumWidth(1)                 # a narrow dock squeezes them instead of widening the page
        upload.add(buttons)
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
        # One "Show more", kept under the list and only changed: the cards above are added to, not redrawn
        self.more_mosaics = button("Show more", "outline", size="sm")
        self.more_mosaics.clicked.connect(guarded(lambda *_: self.moreMosaics.emit()))
        self.more_mosaics.setVisible(False)
        layout.addWidget(self.more_mosaics)
        layout.addWidget(link("Manage collections in Mapflow Web", lambda: self.my_data_url))
        layout.addStretch(1)
        return page

    def set_mosaics(self, mosaics: List[Mosaic], chosen: Optional[str], total: Optional[int] = None,
                    loading: bool = False) -> None:
        """The collections loaded so far, of `total` in the account: "Show more" brings the next page.
        Cards already drawn stay: a new page only adds its own, and nothing is redrawn while it loads.
        Redrawing hundreds of cards on every page (and on every refresh) made the list stutter."""
        total = len(mosaics) if total is None else max(total, len(mosaics))
        self.mosaics_title.setText(f"Collections · {total:,}" if mosaics else "No collections yet")
        keys = [_mosaic_key(m, chosen) for m in mosaics]
        drawn = self._mosaic_keys
        if [k[0] for k in keys[:len(drawn)]] != [k[0] for k in drawn]:
            self._clear(self.mosaic_list)           # removed or reordered: draw them again
            self._mosaic_uses, drawn = [], []
        new_uses = []
        for index, (old, new) in enumerate(zip(drawn, keys)):
            if old != new:                          # the same collection, showing something else: that card only
                card, use = self._mosaic_card(mosaics[index], chosen)
                stale = self.mosaic_list.itemAt(index).widget()
                self.mosaic_list.insertWidget(index, card)
                self.mosaic_list.removeWidget(stale)
                stale.hide()
                stale.deleteLater()
                self._mosaic_uses[index] = use
                new_uses.append(use)
        for mosaic in mosaics[len(drawn):]:
            card, use = self._mosaic_card(mosaic, chosen)
            new_uses.append(use)
            self._mosaic_uses.append(use)
            self.mosaic_list.addWidget(card)
        self._mosaic_keys = keys
        if new_uses:
            self._match_use_widths(new_uses)
        more = self.more_mosaics
        more.setVisible(bool(mosaics) and len(mosaics) < total)
        more.setText("Loading…" if loading else f"Show more · {len(mosaics):,} of {total:,}")
        more.setEnabled(not loading)

    def _mosaic_card(self, mosaic: Mosaic, chosen: Optional[str]):
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
        show.clicked.connect(guarded(lambda *_, mid=mosaic.id: self.showMosaic.emit(mid)))
        several = (mosaic.image_count or 0) > 1
        use = button("Chosen" if mosaic.id == chosen else ("Choose…" if several else "Use"),
                     "outline" if mosaic.id == chosen else "primary", size="sm")
        use.setToolTip("Pick the whole collection or one of its images" if several else "Process this collection")
        use.clicked.connect(guarded(lambda *_, mid=mosaic.id: self.useMosaic.emit(mid)))
        row.addWidget(show)
        row.addWidget(use)
        card.add(row)
        return card, use

    def _match_use_widths(self, new_uses: List[QPushButton]) -> None:
        """Use, Chosen and Choose… are one width. New buttons take the width already found at once, so they
        don't show narrow and then widen; the width is measured again once they are styled."""
        if self._use_width:
            for use in new_uses:
                use.setMinimumWidth(self._use_width)

        @guarded
        def measure() -> None:
            try:
                width = max((u.sizeHint().width() for u in self._mosaic_uses), default=0)
            except RuntimeError:                    # redrawn meanwhile
                return
            if width > self._use_width:
                self._use_width = width
                for use in self._mosaic_uses:
                    use.setMinimumWidth(width)
            else:
                for use in new_uses:
                    use.setMinimumWidth(self._use_width)
        QTimer.singleShot(0, measure)

    def _choose_layers(self) -> None:
        """Only GeoTIFF files: tile layers (XYZ, TMS, WMS) have no file to upload."""
        chosen = pick_layers(self.geotiff_layers(), self)
        if chosen:
            self.layerUploadRequested.emit(chosen)

    def set_upload(self, percent: Optional[int], message: str = "", kind: str = "info") -> None:
        uploading = percent is not None
        self.upload_bar.setVisible(uploading)
        self.upload_bar.setValue(percent or 0)
        for widget in (self.upload_button, self.layer_button):
            if uploading:
                release_focus(widget)   # or Qt moves the focus to a Use button below, and the page scrolls there
            widget.setEnabled(not uploading)
        self.upload_button.setText(f"Uploading… {percent}%" if uploading else "Upload a GeoTIFF")
        self.upload_message.set(kind, message)

    @staticmethod
    def _clear(layout) -> None:
        clear_layout(layout)


def _mosaic_key(mosaic: Mosaic, chosen: Optional[str]) -> tuple:
    """What a collection card shows: when it changes, the card is drawn again."""
    return (mosaic.id, mosaic.name, mosaic.image_count, mosaic.size_bytes, str(mosaic.created), mosaic.id == chosen)


def _provider_label(name: str) -> str:
    known = {"my_imagery_images": "My image", "my_imagery_mosaics": "My collection"}
    readable = (name or "Image").replace("_", " ").title() if (name or "").islower() else name or "Image"
    return known.get(name) or readable
