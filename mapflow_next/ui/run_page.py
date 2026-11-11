"""The run form: ① model → ② area → ③ imagery, with the cost and the Run button always in view."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import astuple, dataclass, field
from typing import Dict, List, Optional, Tuple

from qgis.PyQt.QtCore import QSignalBlocker, Qt, QTimer, pyqtSignal
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import (QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                                 QScrollArea, QSizePolicy, QToolButton, QVBoxLayout, QWidget)

from .. import config
from ..core import formatting
from ..core.draft import Issue
from ..core.models import Block, Model
from . import icons
from .theme import set_prop, tokens
from .widgets import (Callout, Card, Combo, ElidedLabel, OptionRow, Pill, StepHeader, Toggle, button, clear_layout,
                      label, link, rounded, tool, vbox)


@dataclass
class ImageryRow:
    key: str                          # provider:<name> | mosaic | catalog
    title: str
    meta: str = ""
    price: str = ""
    zooms: List[int] = field(default_factory=list)
    zoom: Optional[int] = None
    recommended_zoom: Optional[int] = None    # marked ★ in the zoom list
    pick: str = ""                    # My imagery: text of the button that opens the collection picker
    recommended: bool = False
    removable: bool = False
    previewable: bool = False         # an eye shows it on the map (on the selected row)
    previewing: Optional[bool] = None  # its preview is on the map; None: the eye only zooms to it


@dataclass
class CostView:
    value: str = "—"                  # "46 credits"
    formula: str = ""
    balance: str = ""                 # "Balance after run: 1,194 credits"
    show_top_up: bool = False
    pending: bool = False


class RunPage(QWidget):
    backRequested = pyqtSignal()
    changeScenarioRequested = pyqtSignal()
    nameEdited = pyqtSignal(str)
    renameRequested = pyqtSignal()
    modelChosen = pyqtSignal(str)
    optionToggled = pyqtSignal(str, bool)
    layerChosen = pyqtSignal(str)
    areaAction = pyqtSignal(str)               # draw | selected | extent | file
    imageryChosen = pyqtSignal(str)            # row key
    zoomChosen = pyqtSignal(str, int)          # row key, zoom
    mosaicPickRequested = pyqtSignal()
    catalogRemoved = pyqtSignal()
    previewRequested = pyqtSignal()
    searchImageryRequested = pyqtSignal()
    runRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mfPage")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll = scroll
        body = QWidget()
        body.setObjectName("mfScrollBody")
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(self._build_summary())
        layout.addWidget(self._build_model_step())
        layout.addWidget(self._build_area_step())
        layout.addWidget(self._build_imagery_step())
        layout.addStretch(1)
        outer.addWidget(self._build_cost_bar())
        self._model_ids: List[str] = []
        self._layer_ids: List[str] = []
        self._rows: List[OptionRow] = []
        self._rows_key = None
        self._switches: Dict[str, Toggle] = {}
        self._options_key = None

    # ---------- building ----------

    def _build_summary(self) -> QWidget:
        card = Card(margins=(8, 8, 12, 8))
        row = QHBoxLayout()
        row.setSpacing(10)
        back = tool("chevron-left", "Back to scenarios", "plain", 18)
        back.clicked.connect(self.backRequested.emit)
        self.thumb = QLabel(card)
        self.thumb.setFixedSize(52, 34)
        texts = QVBoxLayout()
        texts.setSpacing(1)
        self.scenario_title = ElidedLabel("Custom setup", "h2")
        name_row = QHBoxLayout()
        name_row.setSpacing(4)
        name_row.addWidget(label("Saves as", "meta"))
        self.name = QLineEdit(card)
        self.name.setProperty("flat", True)
        self.name.setToolTip("Processing name: edit to rename")
        self.name.textEdited.connect(self.nameEdited.emit)
        edit = tool("edit", "Name and description of this processing", "plain", 14)
        edit.clicked.connect(lambda *_: self.renameRequested.emit())
        self.rename_button = edit
        name_row.addWidget(self.name, 1)
        name_row.addWidget(edit)
        texts.addWidget(self.scenario_title)
        texts.addLayout(name_row)
        change = tool("grid", "Change the scenario: open the scenario gallery", "icon", 18)
        change.clicked.connect(lambda *_: self.changeScenarioRequested.emit())
        self.change_button = change
        row.addWidget(back)
        row.addWidget(self.thumb)
        row.addLayout(texts, 1)
        row.addWidget(change)
        card.add(row)
        return card

    def _build_model_step(self) -> QWidget:
        self.model_card = Card(spacing=10)
        self.model_header = StepHeader(1, "What to map")
        self.model_price = label("", "value")
        self.model_header.right.addWidget(self.model_price)
        self.model_card.add(self.model_header)
        self.model_combo = Combo(self.model_card)
        self.model_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.model_combo.setMinimumContentsLength(12)
        self.model_combo.activated.connect(self._model_activated)
        self.model_card.add(self.model_combo)
        self.model_note = label("", "meta", wrap=True)
        self.model_card.add(self.model_note)
        self.options_box = QVBoxLayout()
        self.options_box.setSpacing(10)
        self.model_card.add(self.options_box)
        info = link("How the models work", config.MODELS_DOCS_URL)
        self.model_card.add(info)
        return self.model_card

    def _build_area_step(self) -> QWidget:
        self.area_card = Card(spacing=8)
        self.area_header = StepHeader(2, "Area")
        self.area_value = label("", "value")
        self.area_header.right.addWidget(self.area_value)
        self.area_card.add(self.area_header)
        self.layer_combo = Combo(self.area_card)
        self.layer_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.layer_combo.setMinimumContentsLength(12)
        self.layer_combo.activated.connect(self._layer_activated)
        self.area_card.add(self.layer_combo)
        grid = QGridLayout()
        grid.setSpacing(6)
        self.area_buttons = {}
        for index, (key, icon_name, text, tip) in enumerate((
                ("draw", "pen", "Draw", "Draw a polygon on the map: click corners, double-click to finish"),
                ("selected", "pointer", "Selected features", "Use the selected features of the active layer"),
                ("extent", "maximize", "Map view", "Use what the map shows now"),
                ("file", "upload", "From file", "Open a vector file (GeoJSON, GeoPackage, Shapefile, KML)"))):
            item = QToolButton(self.area_card)
            item.setProperty("variant", "aoi")
            item.setText(text)
            item.setIcon(icons.icon(icon_name, tokens()["ink"], 14))
            item.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            item.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            item.setMinimumWidth(90)
            item.setToolTip(tip)
            item.setCursor(Qt.CursorShape.PointingHandCursor)
            item.clicked.connect(lambda _=False, k=key: self.areaAction.emit(k))
            if key == "draw":
                item.setCheckable(True)
            grid.addWidget(item, index // 2, index % 2)
            self.area_buttons[key] = item
        self.area_card.add(grid)
        self.area_meta = label("Pick a polygon layer, or draw the area on the map.", "meta", wrap=True)
        self.area_card.add(self.area_meta)
        self.area_error = label("", "error", wrap=True)
        self.area_error.setVisible(False)
        self.area_card.add(self.area_error)
        # A suggestion about the area (My imagery: its extent, or an area outside it), with actions
        self.area_hint = QWidget(self.area_card)
        hint_layout = QVBoxLayout(self.area_hint)
        hint_layout.setContentsMargins(0, 2, 0, 0)
        hint_layout.setSpacing(6)
        self.area_hint_text = Callout("info", "", self.area_hint)
        hint_layout.addWidget(self.area_hint_text)
        self.area_hint_actions = QGridLayout()        # two columns that shrink with the dock
        self.area_hint_actions.setHorizontalSpacing(6)
        self.area_hint_actions.setVerticalSpacing(6)
        hint_layout.addLayout(self.area_hint_actions)
        self.area_hint.setVisible(False)
        self.area_hint_buttons: Dict[str, QPushButton] = {}
        self._area_hint_key = None
        self.area_card.add(self.area_hint)
        return self.area_card

    def _build_imagery_step(self) -> QWidget:
        self.imagery_card = Card(spacing=8)
        self.imagery_header = StepHeader(3, "Imagery sources")
        self.imagery_card.add(self.imagery_header)
        self.imagery_hint = label("", "meta", wrap=True)
        self.imagery_card.add(self.imagery_hint)
        self.rows_box = QVBoxLayout()
        self.rows_box.setSpacing(6)
        self.imagery_card.add(self.rows_box)
        self.imagery_error = label("", "error", wrap=True)
        self.imagery_error.setVisible(False)
        self.imagery_card.add(self.imagery_error)
        find = link("Find a newer satellite image", external=False)
        find.setIcon(icons.icon("search", tokens()["link"], 14))
        find.clicked.connect(self.searchImageryRequested.emit)
        self.imagery_card.add(find)
        return self.imagery_card

    def _build_cost_bar(self) -> QWidget:
        bar = QFrame(self)
        bar.setObjectName("mfBottomBar")
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(16, 10, 16, 12)
        layout.setSpacing(6)
        self.issues = Callout("warn", "", bar)
        layout.addWidget(self.issues)
        top = QHBoxLayout()
        self.cost_label = label("Estimated cost", "title")
        self.cost_value = label("—", "big")
        top.addWidget(self.cost_label, 1)
        top.addWidget(self.cost_value)
        layout.addLayout(top)
        self.cost_formula = label("", "meta", wrap=True)
        layout.addWidget(self.cost_formula)
        self.run_button = button("Run processing", "primary", "play", size="lg")
        self.run_button.clicked.connect(self.runRequested.emit)
        layout.addWidget(self.run_button)
        bottom = QHBoxLayout()
        self.balance = label("", "meta")
        self.top_up = link("Top up", config.TOP_UP_URL)
        bottom.addWidget(self.balance, 1)
        bottom.addWidget(self.top_up)
        layout.addLayout(bottom)
        return bar

    # ---------- events ----------

    def _model_activated(self, index: int) -> None:
        if 0 <= index < len(self._model_ids):
            self.modelChosen.emit(self._model_ids[index])

    def _layer_activated(self, index: int) -> None:
        if 0 <= index < len(self._layer_ids):
            self.layerChosen.emit(self._layer_ids[index])

    # ---------- rendering ----------

    def set_scenario(self, title: str, pixmap: Optional[QPixmap]) -> None:
        self.scenario_title.setText(title)
        if pixmap is not None and not pixmap.isNull():
            self.thumb.setPixmap(rounded(pixmap, 52, 34, 6))
            self.thumb.show()
        else:
            self.thumb.hide()

    def set_name(self, text: str, description: str = "", force: bool = False) -> None:
        """`force` sets the text even while the field has focus (after the name dialog)."""
        if self.name.text() != text and (force or not self.name.hasFocus()):
            self.name.setText(text)
            self.name.setCursorPosition(0)
        self.name.setToolTip(f"{text}\n\n{description}" if description else "Processing name: edit to rename")

    def set_models(self, models: List[Model], selected: Optional[str]) -> None:
        blocker = QSignalBlocker(self.model_combo)
        self.model_combo.clear()
        self._model_ids = []
        if not selected:
            self.model_combo.addItem("Choose a model…")
            self._model_ids.append("")
        for model in models:
            self.model_combo.addItem(model.name)
            self._model_ids.append(model.id)
        self.model_combo.setCurrentIndex(self._model_ids.index(selected) if selected in self._model_ids else 0)
        del blocker

    @contextmanager
    def keep_scroll(self):
        """Hold the scroll position while the form re-renders (restored again once layouts settle)."""
        bar = self.scroll.verticalScrollBar()
        value = bar.value()
        try:
            yield
        finally:
            bar.setValue(value)
            QTimer.singleShot(0, lambda: bar.setValue(value))

    def set_options(self, model: Optional[Model], enabled: set, base_price: str, note: str = "") -> None:
        self.model_price.setText(base_price)
        self.model_note.setText(note or (model.description if model else ""))
        self.model_note.setVisible(bool(self.model_note.text()))
        blocks = model.options if model else []
        key = (model.id if model else None, tuple(b.name for b in blocks))
        if key == self._options_key:
            # Same model and options: only the switches change. Rebuilding them would move the focus
            for name, switch in self._switches.items():
                if switch.isChecked() != (name in enabled):
                    switch.blockSignals(True)
                    switch.setChecked(name in enabled)
                    switch.blockSignals(False)
            return
        self._options_key = key
        clear_layout(self.options_box)
        self._switches = {}
        for block in blocks:
            self.options_box.addLayout(self._option_row(block, block.name in enabled))

    def _option_row(self, block: Block, checked: bool) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        price = "no extra cost" if not block.price else f"+{formatting.per_km2(block.price)}"
        texts = vbox(label(block.display_name, "title", wrap=True), label(price, "meta"), spacing=1)
        switch = Toggle()
        switch.setChecked(checked)
        switch.setAccessibleName(block.display_name)
        switch.toggled.connect(lambda on, name=block.name: self.optionToggled.emit(name, bool(on)))
        self._switches[block.name] = switch
        row.addLayout(texts, 1)
        row.addWidget(switch)
        return row

    def set_layers(self, layers: List[Tuple[str, str]], selected: Optional[str]) -> None:
        blocker = QSignalBlocker(self.layer_combo)
        self.layer_combo.clear()
        self._layer_ids = []
        if not selected:
            self.layer_combo.addItem("Choose a polygon layer…" if layers else "No polygon layers yet: draw the area")
            self._layer_ids.append("")
        for layer_id, name in layers:
            self.layer_combo.addItem(icons.icon("map", tokens()["text2"], 14), name)
            self._layer_ids.append(layer_id)
        self.layer_combo.setCurrentIndex(self._layer_ids.index(selected) if selected in self._layer_ids else 0)
        del blocker

    def set_drawing(self, active: bool) -> None:
        self.area_buttons["draw"].setChecked(active)
        self.area_buttons["draw"].setText("Drawing…" if active else "Draw")

    def set_area(self, value: str, meta: str, error: str = "") -> None:
        self.area_value.setText(value)
        self.area_meta.setText(meta)
        self.area_error.setText(error)
        self.area_error.setVisible(bool(error))

    def set_area_hint(self, kind: str = "info", text: str = "", actions: Tuple[Tuple[str, str], ...] = ()) -> None:
        """A suggestion under the area, with buttons that emit areaAction(key). Empty text hides it."""
        key = (kind, text, tuple(actions))
        if key == self._area_hint_key:
            return
        self._area_hint_key = key
        self.area_hint_text.set(kind, text)
        clear_layout(self.area_hint_actions)
        self.area_hint_buttons = {}
        for index, (caption, action) in enumerate(actions):
            item = button(caption, "outline", size="sm")
            item.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            item.setMinimumWidth(90)
            item.setToolTip(caption)
            item.clicked.connect(lambda *_, a=action: self.areaAction.emit(a))
            self.area_hint_actions.addWidget(item, index // 2, index % 2)
            self.area_hint_buttons[action] = item
        self.area_hint.setVisible(bool(text))

    def set_imagery(self, rows: List[ImageryRow], selected: Optional[str], hint: str = "", error: str = "") -> None:
        self.imagery_hint.setText(hint)
        self.imagery_hint.setVisible(bool(hint))
        self.imagery_error.setText(error)
        self.imagery_error.setVisible(bool(error))
        key = (tuple(astuple(r) for r in rows), selected)
        if key == self._rows_key:
            return                      # nothing changed: keep the widgets (and the focus) as they are
        self._rows_key = key
        clear_layout(self.rows_box)
        self._rows = []
        for spec in rows:
            row = OptionRow(spec.title, spec.meta)
            chosen = spec.key == selected
            row.set_selected(chosen)
            row.clicked.connect(lambda *_, key=spec.key: self.imageryChosen.emit(key))
            if spec.recommended:
                row.right.addWidget(Pill("Recommended", "ok"))
            # The control (zoom or picker) with the price under it: one narrow column
            column = QVBoxLayout()
            column.setSpacing(2)
            if spec.zooms:
                zoom = Combo(row)
                for value in spec.zooms:
                    zoom.addItem(f"z{value} ★" if value == spec.recommended_zoom else f"z{value}", value)
                zoom.setCurrentIndex(spec.zooms.index(spec.zoom) if spec.zoom in spec.zooms else len(spec.zooms) - 1)
                zoom.setToolTip("Zoom level: higher is sharper and costs more. ★ recommended for this scenario")
                zoom.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
                zoom.setMinimumContentsLength(4)
                zoom.activated.connect(lambda i, key=spec.key, combo=zoom: self.zoomChosen.emit(key, combo.itemData(i)))
                column.addWidget(zoom)
            if spec.pick:
                pick = button(spec.pick, "outline", size="sm")
                pick.setToolTip("Choose a collection, or one image of it")
                pick.clicked.connect(lambda *_: self.mosaicPickRequested.emit())
                column.addWidget(pick)
            if spec.price:
                price = label(spec.price, "meta")
                price.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                column.addWidget(price)
            if column.count():
                row.right.addLayout(column)
            if chosen and spec.previewable:
                on = bool(spec.previewing)
                eye = tool("eye", "Hide the preview" if on else "Preview on the map", "plain", 16)
                if on:      # the preview is on the map: the eye shows it, and a click takes it off
                    eye.setIcon(icons.icon("eye", tokens()["primary_ink"], 16))
                    eye.setProperty("on", True)
                eye.clicked.connect(lambda *_: self.previewRequested.emit())
                row.right.addWidget(eye)
            if spec.removable:
                remove = tool("x", "Remove this image", "plain", 14)
                remove.clicked.connect(lambda *_: self.catalogRemoved.emit())
                row.right.addWidget(remove)
            self.rows_box.addWidget(row)
            self._rows.append(row)

    def set_steps(self, model_done: bool, area_done: bool, imagery_done: bool) -> None:
        states = []
        active_given = False
        for done in (model_done, area_done, imagery_done):
            if done:
                states.append("done")
            elif not active_given:
                states.append("active")
                active_given = True
            else:
                states.append("todo")
        for header, card, state in ((self.model_header, self.model_card, states[0]),
                                    (self.area_header, self.area_card, states[1]),
                                    (self.imagery_header, self.imagery_card, states[2])):
            header.set_state(state)
            set_prop(card, "active", state == "active")

    def set_cost(self, view: CostView, credits_billing: bool) -> None:
        self.cost_label.setText("Estimated cost" if credits_billing else "Uses")
        self.cost_value.setText(view.value)
        self.cost_formula.setText(view.formula)
        self.cost_formula.setVisible(bool(view.formula))
        self.balance.setText(view.balance)
        self.top_up.setVisible(view.show_top_up)

    def set_issues(self, issues: List[Issue], busy: bool = False) -> None:
        blocking = [i for i in issues if i.field in ("account",)]
        # Steps show their own hints; the bar only repeats what no step can show
        self.issues.set("warn", blocking[0].text if blocking else "")
        self.run_button.setEnabled(not issues and not busy)
        self.run_button.setText("Starting…" if busy else "Run processing")
