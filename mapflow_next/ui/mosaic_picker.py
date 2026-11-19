"""My imagery: choose a collection, or one image of it, to process; upload GeoTIFFs and create collections."""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from qgis.PyQt.QtCore import Qt, QTimer, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtWidgets import (QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu, QProgressBar, QScrollArea,
                                 QVBoxLayout, QWidget)

from .. import config
from ..core import formatting
from ..core.models import Mosaic, MosaicImage
from . import icons
from .layer_picker import pick_layers
from .theme import stylesheet, tokens
from .widgets import (Callout, Card, DropTarget, ElidedLabel, OptionRow, button, clear_layout, label, link,
                      menu_action, placeholder, rounded, tool)
from ..core.guard import guarded

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
    layerUploadRequested = pyqtSignal(list, str)  # GeoTIFF layers' ids, into this collection ("" = a new one)
    filesDropped = pyqtSignal(list, str)        # [(file, name)] dragged in, into this collection ("" = a new one)
    createRequested = pyqtSignal()              # "Create collection"
    deleteCollectionRequested = pyqtSignal(str)   # mosaic id
    deleteImageRequested = pyqtSignal(str, str)   # mosaic id, image id
    queryChanged = pyqtSignal(str)              # the search box, once typing pauses ("" = the listing again)
    moreRequested = pyqtSignal(str)             # "Show more": the next page of the search (or of the listing, "")

    def __init__(self, parent=None, my_data_url: str = config.WEB_URL + config.MY_DATA_PATH):
        super().__init__(parent)
        self.setObjectName("mfRoot")
        self.setWindowTitle("My imagery")
        self.setStyleSheet(stylesheet())
        self.resize(820, 560)
        self.mosaics: List[Mosaic] = []              # the listing, loaded so far
        self.total = 0                               # collections in the account
        self.loading = False
        self.found: List[Mosaic] = []                # the server's answer to the search box, so far
        self.found_total = 0
        self.found_loading = False
        self.more_collections = None                 # "Show more", under the rows
        self.list_empty = None                       # "No collections yet." and the like, when there are no rows
        self._drawn: List[tuple] = []                # (id, name) of the rows drawn, in order
        self._drawn_mode = False                     # whether they are the search's
        self._list_tail = False                      # the note, "Show more" and the stretch are in the list
        # A collection by id that is neither listed nor found (the chosen one); the controller sets it
        self.lookup: Callable[[str], Optional[Mosaic]] = lambda mosaic_id: None
        self.current: Optional[str] = None           # collection shown on the right
        self.chosen_mosaic: Optional[str] = None
        self.chosen_image: Optional[str] = None
        self._thumbs: Dict[str, QLabel] = {}
        self.previews: set = set()            # images whose preview is shown
        self._rows: Dict[str, OptionRow] = {}
        # (layer id, name) of the project's GeoTIFF layers, asked for when the menu opens; the controller sets it
        self.geotiff_layers: Callable[[], List[Tuple[str, str]]] = lambda: []
        # (file, name) of the GeoTIFFs a drag carries; the controller sets it. Dropped, they go where uploads go
        self.parse_drop: Callable[[object], List[Tuple[str, str]]] = lambda mime: []
        self.drop = DropTarget(self, lambda mime: self.parse_drop(mime))
        self.drop.dropped.connect(guarded(lambda items: self.filesDropped.emit(items, self.current or "")))

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
        self.upload_button.clicked.connect(guarded(lambda *_: self.uploadRequested.emit(self.current or "")))
        actions.addWidget(self.upload_button)
        self.layer_button = button("Choose from raster layers", "outline", "layers")
        self.layer_button.clicked.connect(guarded(lambda *_: self._choose_layers()))
        actions.addWidget(self.layer_button)
        actions.addStretch(1)
        self.create_button = button("Create collection", "ghost", "plus")
        self.create_button.clicked.connect(guarded(lambda *_: self.createRequested.emit()))
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
        # Searched on the server (names of collections and of their images), once typing pauses
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)
        self._debounce.timeout.connect(guarded(lambda: self.queryChanged.emit(self.search.text().strip())))
        self.search.textChanged.connect(guarded(lambda *_: self._query_typed()))
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
        self.show_button.clicked.connect(guarded(lambda *_: self.current and self.showRequested.emit(self.current)))
        title_row.addWidget(self.show_button)
        self.more_button = tool("more", "More actions", "plain", 18)
        self.more_button.clicked.connect(guarded(lambda *_: self._popup(self.collection_menu(), self.more_button)))
        title_row.addWidget(self.more_button)
        right.addLayout(title_row)
        self.meta = label("", "meta", wrap=True)
        right.addWidget(self.meta)
        self.use_all = button("Use the whole collection", "primary", "layers")
        self._use_all_icon = self.use_all.icon()
        self.use_all.clicked.connect(guarded(lambda *_: self.current and self.chosen.emit(self.current, "")))
        right.addWidget(self.use_all, 0, Qt.AlignmentFlag.AlignLeft)
        self.images_scroll, self.images_box = self._scroll_box(8)
        right.addWidget(self.images_scroll, 1)
        columns.addLayout(right, 1)
        outer.addLayout(columns, 1)

        foot = QHBoxLayout()
        foot.addWidget(label("A collection is processed as one mosaic. Pick an image to process only that one.",
                             "meta", wrap=True), 1)
        close = button("Cancel", "ghost")
        close.clicked.connect(guarded(lambda *_: self.reject()))
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

    def set_collections(self, mosaics: List[Mosaic], chosen_mosaic: Optional[str], chosen_image: Optional[str],
                        total: Optional[int] = None, loading: bool = False) -> None:
        """The listing: the collections loaded so far, of `total` in the account."""
        self.mosaics = list(mosaics)
        self.total = len(self.mosaics) if total is None else max(total, len(self.mosaics))
        self.loading = loading
        self.chosen_mosaic, self.chosen_image = chosen_mosaic, chosen_image
        self._render_collections()

    def set_found(self, query: str, found: List[Mosaic], total: int, loading: bool = False) -> None:
        """The server's answer to the search: shown while the search box still says `query`."""
        if query != self.search.text().strip():
            return                                  # typed on since: a newer search is on its way
        self.found, self.found_total, self.found_loading = list(found), max(total, len(found)), loading
        self._render_collections()

    def _searching(self) -> bool:
        return bool(self.search.text().strip())

    def _shown(self) -> List[Mosaic]:
        return self.found if self._searching() else self.mosaics

    def _lookup(self, mosaic_id: Optional[str]) -> Optional[Mosaic]:
        """A collection by id: listed, found, or known to the controller (chosen but on no loaded page)."""
        if not mosaic_id:
            return None
        return next((m for m in self.mosaics + self.found if m.id == mosaic_id), None) or self.lookup(mosaic_id)

    def _query_typed(self) -> None:
        """A search goes to the server once typing pauses; meanwhile the list says it's searching."""
        query = self.search.text().strip()
        self.found, self.found_total, self.found_loading = [], 0, bool(query)
        self._render_collections()
        self._debounce.start()

    def _render_collections(self) -> None:
        """The rows drawn stay while the list only grows (a new page): its rows are added after them. Drawn
        again only when the list changes otherwise (a search, a deletion), as redrawing hundreds of rows on
        every page made the window stutter."""
        shown, searching = self._shown(), self._searching()
        ids = [(m.id, m.name) for m in shown]
        drawn = self._drawn
        if self._drawn_mode != searching or ids[:len(drawn)] != drawn or not self._list_tail:
            clear_layout(self.list_box)
            self._rows, drawn = {}, []
            self.list_empty = label("", "meta")
            self.more_collections = button("Show more", "outline", size="sm")
            self.more_collections.clicked.connect(
                guarded(lambda *_: self.moreRequested.emit(self.search.text().strip())))
            self.list_box.addWidget(self.list_empty)
            self.list_box.addWidget(self.more_collections)
            self.list_box.addStretch(1)
            self._list_tail = True
        for mosaic in shown[len(drawn):]:
            meta = " · ".join(t for t in (image_count_text(mosaic), formatting.size(mosaic.size_bytes)
                                          if mosaic.size_bytes else "") if t)
            row = OptionRow(mosaic.name, meta)
            row.set_selected(mosaic.id == self.current)
            row.clicked.connect(guarded(lambda *_, mid=mosaic.id: self._row_clicked(mid)))
            self.list_box.insertWidget(len(self._rows), row)      # before the note, "Show more" and the stretch
            self._rows[mosaic.id] = row
        self._drawn, self._drawn_mode = ids, searching
        total = self.found_total if searching else self.total
        loading = self.found_loading if searching else self.loading
        self.list_empty.setText(("Searching…" if searching else "Loading collections…") if loading else
                                ("No collections match." if searching else "No collections yet."))
        self.list_empty.setVisible(not self._rows)
        self.more_collections.setVisible(bool(shown) and len(shown) < total)
        self.more_collections.setText("Loading…" if loading else f"Show more · {len(shown):,} of {total:,}")
        self.more_collections.setEnabled(not loading)

    def update_counts(self) -> None:
        for mosaic in self._shown():
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
        mosaic = self._lookup(mosaic_id)
        self.current = mosaic.id if mosaic else None
        for mid, row in self._rows.items():
            row.set_selected(mid == self.current)
        self._show_target()
        for widget in (self.title, self.show_button, self.more_button, self.meta, self.use_all):
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
        self.use_all.setIcon(QIcon() if whole else self._use_all_icon)
        self.use_all.setEnabled(not whole)
        clear_layout(self.images_box)
        self._thumbs = {}
        self.images_box.addWidget(label("Loading images…", "meta"))
        self.images_box.addStretch(1)
        self.collectionOpened.emit(mosaic_id)

    # ---------- "⋯" menus ----------

    @staticmethod
    def _popup(menu: QMenu, anchor: QWidget) -> None:
        menu.exec(anchor.mapToGlobal(anchor.rect().bottomLeft()))

    def collection_menu(self) -> QMenu:
        """The selected collection's actions."""
        menu = QMenu(self)
        mosaic_id = self.current or ""
        menu_action(menu, "trash", "Delete collection…", lambda: self.deleteCollectionRequested.emit(mosaic_id),
                    ink=tokens()["err_fg"])
        return menu

    def image_menu(self, mosaic_id: str, image_id: str) -> QMenu:
        menu = QMenu(self)
        menu_action(menu, "trash", "Delete from the collection…",
                    lambda: self.deleteImageRequested.emit(mosaic_id, image_id), ink=tokens()["err_fg"])
        return menu

    # ---------- adding imagery ----------

    def _show_target(self) -> None:
        mosaic = self._lookup(self.current)
        if mosaic is not None:
            self.target.setText(f"GeoTIFFs are added to “{mosaic.name}”. Click it again to upload into a new "
                                f"collection instead. You can drag GeoTIFF layers or files onto this window.")
        else:
            self.target.setText("GeoTIFFs go into a new collection. Select a collection to add them to it. You can "
                                "drag GeoTIFF layers or files onto this window.")

    def _choose_layers(self) -> None:
        """Only GeoTIFF files: tile layers (XYZ, TMS, WMS) have no file to upload."""
        chosen = pick_layers(self.geotiff_layers(), self)
        if chosen:
            self.layerUploadRequested.emit(chosen, self.current or "")

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
        use.clicked.connect(guarded(lambda *_, iid=image.id: self.chosen.emit(mosaic_id, iid)))
        row.addWidget(use, 0, Qt.AlignmentFlag.AlignVCenter)
        more = tool("more", "More actions", "plain", 16)
        more.setObjectName(f"more:{image.id}")
        more.clicked.connect(
            guarded(lambda *_, iid=image.id, anchor=more: self._popup(self.image_menu(mosaic_id, iid), anchor)))
        row.addWidget(more, 0, Qt.AlignmentFlag.AlignVCenter)
        card.add(row)
        return card

    def set_thumbnail(self, image_id: str, pixmap: QPixmap) -> None:
        thumb = self._thumbs.get(image_id)
        if thumb is not None and not pixmap.isNull():
            thumb.setPixmap(rounded(pixmap, THUMB, THUMB, 8))
            self.previews.add(image_id)
