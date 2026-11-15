"""My imagery: choose a collection, or one image of it, to process; upload GeoTIFFs and create collections."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import (QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QProgressBar, QScrollArea,
                                 QVBoxLayout, QWidget)

from .. import config
from ..core import formatting
from ..core.models import Mosaic, MosaicImage
from . import icons
from .theme import stylesheet, tokens
from .widgets import (Callout, Card, ElidedLabel, OptionRow, button, clear_layout, label, link, menu_action,
                      placeholder, rounded, tool)

THUMB = 72


def image_count_text(mosaic: Mosaic) -> str:
    if mosaic.image_count is None:
        return ""
    return f"{mosaic.image_count} image" + ("" if mosaic.image_count == 1 else "s")


class MosaicPicker(QDialog):
    collectionOpened = pyqtSignal(str)          # mosaic id: show its images (the controller loads them)
    chosen = pyqtSignal(str, str)               # mosaic id, image id ("" = the whole collection)
    showRequested = pyqtSignal(str)             # mosaic id: show it on the map
    uploadRequested = pyqtSignal(str)           # into this collection ("" = a new one)
    layerUploadRequested = pyqtSignal(str, str)  # a GeoTIFF layer's id, into this collection ("" = a new one)
    createRequested = pyqtSignal()              # "Create collection"

    def __init__(self, parent=None, my_data_url: str = config.WEB_URL + config.MY_DATA_PATH):
        super().__init__(parent)
        self.setObjectName("mfRoot")
        self.setWindowTitle("My imagery")
        self.setStyleSheet(stylesheet())
        self.resize(820, 560)
        self.mosaics: List[Mosaic] = []
        self.current: Optional[str] = None           # collection shown on the right
        self.chosen_mosaic: Optional[str] = None
        self.chosen_image: Optional[str] = None
        self._thumbs: Dict[str, QLabel] = {}
        self.previews: set = set()            # images whose preview is shown
        self._rows: Dict[str, OptionRow] = {}
        # (layer id, name) of the project's GeoTIFF layers, asked for when the menu opens; the controller sets it
        self.geotiff_layers: Callable[[], List[Tuple[str, str]]] = lambda: []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 18, 20, 14)
        outer.setSpacing(12)
        head = QHBoxLayout()
        head.addWidget(label("My imagery", "h1"))
        head.addStretch(1)
        head.addWidget(link("Manage collections in Mapflow Web", my_data_url))
        outer.addLayout(head)

        # Adding imagery: into the collection selected on the left, or into a new one when none is
        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.upload_button = button("Upload a GeoTIFF", "outline", "upload")
        self.upload_button.clicked.connect(lambda *_: self.uploadRequested.emit(self.current or ""))
        actions.addWidget(self.upload_button)
        self.layer_button = button("Choose from raster layer", "outline", "layers")
        self.layer_menu = QMenu(self.layer_button)
        self.layer_menu.aboutToShow.connect(self._fill_layer_menu)
        self.layer_button.clicked.connect(
            lambda *_: self.layer_menu.exec(self.layer_button.mapToGlobal(self.layer_button.rect().bottomLeft())))
        actions.addWidget(self.layer_button)
        actions.addStretch(1)
        self.create_button = button("Create collection", "ghost", "plus")
        self.create_button.clicked.connect(lambda *_: self.createRequested.emit())
        actions.addWidget(self.create_button)
        outer.addLayout(actions)
        self.target = label("", "meta", wrap=True)
        outer.addWidget(self.target)
        self.upload_bar = QProgressBar(self)
        self.upload_bar.setTextVisible(False)
        self.upload_bar.setFixedHeight(6)
        self.upload_bar.setVisible(False)
        outer.addWidget(self.upload_bar)
        self.upload_note = Callout("info", "")
        self.upload_note.setVisible(False)
        outer.addWidget(self.upload_note)

        columns = QHBoxLayout()
        columns.setSpacing(16)
        left = QVBoxLayout()
        left.setSpacing(8)
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Find a collection")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(icons.icon("search", tokens()["text2"], 16), QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(lambda *_: self._render_collections())
        left.addWidget(self.search)
        self.list_scroll, self.list_box = self._scroll_box(6)
        left.addWidget(self.list_scroll, 1)
        holder = QWidget(self)
        holder.setLayout(left)
        holder.setFixedWidth(280)
        columns.addWidget(holder)

        right = QVBoxLayout()
        right.setSpacing(8)
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        self.title = ElidedLabel("", "h2")
        title_row.addWidget(self.title, 1)
        self.show_button = tool("eye", "Show the collection on the map", "plain", 18)
        self.show_button.clicked.connect(lambda *_: self.current and self.showRequested.emit(self.current))
        title_row.addWidget(self.show_button)
        right.addLayout(title_row)
        self.meta = label("", "meta", wrap=True)
        right.addWidget(self.meta)
        self.use_all = button("Use the whole collection", "primary", "layers")
        self.use_all.clicked.connect(lambda *_: self.current and self.chosen.emit(self.current, ""))
        right.addWidget(self.use_all, 0, Qt.AlignmentFlag.AlignLeft)
        self.images_scroll, self.images_box = self._scroll_box(8)
        right.addWidget(self.images_scroll, 1)
        columns.addLayout(right, 1)
        outer.addLayout(columns, 1)

        foot = QHBoxLayout()
        foot.addWidget(label("A collection is processed as one mosaic. Pick an image to process only that one.",
                             "meta", wrap=True), 1)
        close = button("Cancel", "ghost")
        close.clicked.connect(lambda *_: self.reject())
        foot.addWidget(close)
        outer.addLayout(foot)

    def _scroll_box(self, spacing: int):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        body.setObjectName("mfScrollBody")
        box = QVBoxLayout(body)
        box.setContentsMargins(0, 0, 6, 0)
        box.setSpacing(spacing)
        scroll.setWidget(body)
        return scroll, box

    # ---------- collections ----------

    def set_collections(self, mosaics: List[Mosaic], chosen_mosaic: Optional[str], chosen_image: Optional[str]) -> None:
        self.mosaics = list(mosaics)
        self.chosen_mosaic, self.chosen_image = chosen_mosaic, chosen_image
        self._render_collections()

    def _render_collections(self) -> None:
        clear_layout(self.list_box)
        self._rows = {}
        needle = self.search.text().strip().lower()
        for mosaic in self.mosaics:
            if needle and needle not in mosaic.name.lower():
                continue
            meta = " · ".join(t for t in (image_count_text(mosaic), formatting.size(mosaic.size_bytes)
                                          if mosaic.size_bytes else "") if t)
            row = OptionRow(mosaic.name, meta)
            row.set_selected(mosaic.id == self.current)
            row.clicked.connect(lambda *_, mid=mosaic.id: self._row_clicked(mid))
            self.list_box.addWidget(row)
            self._rows[mosaic.id] = row
        if not self._rows:
            self.list_box.addWidget(label("No collections match." if needle else "No collections yet.", "meta"))
        self.list_box.addStretch(1)

    def update_counts(self) -> None:
        for mosaic in self.mosaics:
            row = self._rows.get(mosaic.id)
            if row is not None:
                meta = " · ".join(t for t in (image_count_text(mosaic), formatting.size(mosaic.size_bytes)
                                              if mosaic.size_bytes else "") if t)
                row.meta.setText(meta)
                row.meta.setVisible(bool(meta))

    def _row_clicked(self, mosaic_id: str) -> None:
        """One collection at a time; clicking the selected one again clears the selection (uploads then make
        a new collection)."""
        if mosaic_id == self.current:
            self.open_collection(None)
        else:
            self.open_collection(mosaic_id)

    def open_collection(self, mosaic_id: Optional[str]) -> None:
        mosaic = next((m for m in self.mosaics if m.id == mosaic_id), None)
        self.current = mosaic.id if mosaic else None
        for mid, row in self._rows.items():
            row.set_selected(mid == self.current)
        self._show_target()
        for widget in (self.title, self.show_button, self.meta, self.use_all):
            widget.setVisible(mosaic is not None)
        if mosaic is None:
            clear_layout(self.images_box)
            self._thumbs = {}
            self.images_box.addWidget(label("Select a collection to see its images and use it, or to upload "
                                            "GeoTIFFs into it.", "meta", wrap=True))
            self.images_box.addStretch(1)
            return
        self.title.setText(mosaic.name)
        self.meta.setText(" · ".join(t for t in (image_count_text(mosaic), formatting.size(mosaic.size_bytes)
                                                 if mosaic.size_bytes else "", formatting.when(mosaic.created)) if t))
        whole = mosaic_id == self.chosen_mosaic and not self.chosen_image
        self.use_all.setText("Chosen: the whole collection" if whole else "Use the whole collection")
        self.use_all.setEnabled(not whole)
        clear_layout(self.images_box)
        self._thumbs = {}
        self.images_box.addWidget(label("Loading images…", "meta"))
        self.images_box.addStretch(1)
        self.collectionOpened.emit(mosaic_id)

    # ---------- adding imagery ----------

    def _show_target(self) -> None:
        mosaic = next((m for m in self.mosaics if m.id == self.current), None)
        if mosaic is not None:
            self.target.setText(f"GeoTIFFs are added to “{mosaic.name}”. Click it again to upload into a new "
                                f"collection instead.")
        else:
            self.target.setText("GeoTIFFs go into a new collection. Select a collection to add them to it.")

    def _fill_layer_menu(self) -> None:
        """Only GeoTIFF files: tile layers (XYZ, TMS, WMS) have no file to upload."""
        self.layer_menu.clear()
        layers = self.geotiff_layers()
        for layer_id, name in layers:
            menu_action(self.layer_menu, "image", name,
                        lambda lid=layer_id: self.layerUploadRequested.emit(lid, self.current or ""))
        if not layers:
            self.layer_menu.addAction("No GeoTIFF layers in the project").setEnabled(False)

    def set_upload(self, percent: Optional[int], message: str = "", kind: str = "info") -> None:
        uploading = percent is not None
        self.upload_bar.setVisible(uploading)
        self.upload_bar.setValue(percent or 0)
        for widget in (self.upload_button, self.layer_button, self.create_button):
            widget.setEnabled(not uploading)
        if uploading and not message:
            message = f"Uploading… {percent}%"
        self.upload_note.set(kind, message)
        self.upload_note.setVisible(bool(message))

    # ---------- images ----------

    def set_images(self, mosaic_id: str, images: List[MosaicImage]) -> None:
        if mosaic_id != self.current:
            return
        clear_layout(self.images_box)
        self._thumbs = {}
        if not images:      # nothing to process: the collection can't be chosen
            self.use_all.setEnabled(False)
            self.images_box.addWidget(Callout("warn", "This collection has no images yet, so it can't be "
                                                      "processed. Upload a GeoTIFF into it above."))
        for image in images:
            self.images_box.addWidget(self._image_card(mosaic_id, image))
        self.images_box.addStretch(1)

    def _image_card(self, mosaic_id: str, image: MosaicImage) -> Card:
        card = Card(margins=(10, 8, 10, 8))
        row = QHBoxLayout()
        row.setSpacing(12)
        thumb = QLabel(card)
        thumb.setFixedSize(THUMB, THUMB)
        thumb.setPixmap(placeholder("image", THUMB, THUMB, 8))
        self._thumbs[image.id] = thumb
        row.addWidget(thumb)
        texts = QVBoxLayout()
        texts.setSpacing(3)
        texts.addWidget(ElidedLabel(image.filename or image.id, "title"))
        details = [f"{image.pixel_size:.2f} m/px" if image.pixel_size else "",
                   formatting.size(image.size_bytes) if image.size_bytes else "",
                   f"uploaded {formatting.when(image.uploaded)}" if image.uploaded else ""]
        texts.addWidget(label(" · ".join(t for t in details if t), "meta"))
        texts.addStretch(1)
        row.addLayout(texts, 1)
        chosen = mosaic_id == self.chosen_mosaic and image.id == self.chosen_image
        use = button("Chosen" if chosen else "Use this image", "outline" if chosen else "primary", size="sm")
        use.setEnabled(not chosen)
        use.clicked.connect(lambda *_, iid=image.id: self.chosen.emit(mosaic_id, iid))
        row.addWidget(use, 0, Qt.AlignmentFlag.AlignVCenter)
        card.add(row)
        return card

    def set_thumbnail(self, image_id: str, pixmap: QPixmap) -> None:
        thumb = self._thumbs.get(image_id)
        if thumb is not None and not pixmap.isNull():
            thumb.setPixmap(rounded(pixmap, THUMB, THUMB, 8))
            self.previews.add(image_id)
