"""Scenario gallery: a non-modal window to browse every scenario, with categories, search and details."""
from __future__ import annotations

from typing import Dict, List, Optional

from qgis.PyQt.QtCore import QEvent, QRectF, QSize, Qt, QUrl, pyqtSignal
from qgis.PyQt.QtGui import QDesktopServices, QFont, QFontMetrics, QKeySequence, QPainter, QPainterPath, QPen, QPixmap
from qgis.PyQt.QtWidgets import (QAbstractButton, QButtonGroup, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
                                 QLineEdit, QScrollArea, QShortcut, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget)

from .. import config
from ..core.scenarios import Catalogue, Scenario
from . import icons
from .start_page import plain, scenario_pixmap
from .theme import color, stylesheet, tokens
from .widgets import Callout, Card, button, label, link, rounded, vbox

IMAGE_RATIO = 10 / 16
LEFT_MIDDLE = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
RIGHT_MIDDLE = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
GAP = 18
MIN_CARD = 240


def _elide_lines(text: str, metrics: QFontMetrics, width: int, lines: int) -> str:
    words, out, current, index = text.split(), [], "", 0
    while index < len(words):
        trial = f"{current} {words[index]}".strip()
        if not current or metrics.horizontalAdvance(trial) <= width:
            current, index = trial, index + 1
        else:
            out.append(current)
            current = ""
            if len(out) == lines - 1:
                break
    rest = " ".join(([current] if current else []) + words[index:])
    if rest:
        out.append(metrics.elidedText(rest, Qt.TextElideMode.ElideRight, width))
    return "\n".join(out)


class CategoryButton(QAbstractButton):
    def __init__(self, text: str, count: int, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.count = count
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(f"{text}, {count} scenarios")

    def sizeHint(self) -> QSize:
        return QSize(200, 36)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())
        if self.isChecked():
            background, foreground = color("primary_soft"), color("primary_ink")
        elif self.underMouse():
            background, foreground = color("tile"), color("text")
        else:
            background, foreground = None, color("text")
        if background is not None:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(background)
            painter.drawRoundedRect(rect, 8, 8)
        if self.hasFocus():
            painter.setPen(QPen(color("focus"), 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 7, 7)
        font = QFont(self.font())
        font.setPixelSize(13)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(foreground)
        painter.drawText(rect.adjusted(12, 0, -36, 0), LEFT_MIDDLE, self.text())
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(foreground if self.isChecked() else color("text2"))
        painter.drawText(rect.adjusted(0, 0, -12, 0), RIGHT_MIDDLE, str(self.count))
        painter.end()


class ScenarioCard(QAbstractButton):
    """Picture with model chips, title, two-line description, price and zoom."""

    def __init__(self, scenario: Scenario, picture: QPixmap, parent=None):
        super().__init__(parent)
        self.scenario, self.picture = scenario, picture
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(scenario.title)
        self.setAccessibleDescription(scenario.short)
        self.setToolTip(scenario.short)
        self.setFixedSize(280, self._height(280))

    @staticmethod
    def _height(width: int) -> int:
        return int(width * IMAGE_RATIO) + 112

    def set_width(self, width: int) -> None:
        self.setFixedSize(width, self._height(width))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        hover = self.underMouse() or self.hasFocus()
        painter.setPen(QPen(color("focus" if self.hasFocus() else ("stroke" if hover else "border")),
                            2 if self.hasFocus() else 1))
        painter.setBrush(color("bg"))
        painter.drawRoundedRect(rect, 15, 15)
        image_h = int(self.width() * IMAGE_RATIO)
        cover = rounded(self.picture, self.width() - 2, image_h + 16, 14)
        clip = QPainterPath()
        clip.addRect(QRectF(1, 1, self.width() - 2, image_h))
        painter.save()
        painter.setClipPath(clip)
        painter.drawPixmap(1, 1, cover)
        painter.restore()
        # chips over the picture
        font = QFont(self.font())
        font.setPixelSize(11)
        font.setBold(True)
        painter.setFont(font)
        x = 10.0
        chips = [(plain(self.scenario.model_label), "plain")]
        if self.scenario.custom:
            chips.append(("On request", "warn"))
        for text, kind in chips:
            icon_w = 16 if (kind == "plain" and self.scenario.icon) else 0
            width = QFontMetrics(font).horizontalAdvance(text) + 18 + icon_w
            chip = QRectF(x, 10, width, 24)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color("warn_bg") if kind == "warn" else color("bg"))
            painter.drawRoundedRect(chip, 12, 12)
            if icon_w:
                painter.drawPixmap(int(x + 8), 14, icons.pixmap(self.scenario.icon, tokens()["ink"], 14))
            painter.setPen(color("warn_fg") if kind == "warn" else color("ink"))
            painter.drawText(chip.adjusted(icon_w + 8, 0, -8, 0), LEFT_MIDDLE, text)
            x += width + 6
        # text
        left, inner = 16, self.width() - 32
        font.setPixelSize(15)
        painter.setFont(font)
        painter.setPen(color("ink"))
        title_metrics = QFontMetrics(font)
        painter.drawText(QRectF(left, image_h + 12, inner, 22), LEFT_MIDDLE,
                         title_metrics.elidedText(self.scenario.title, Qt.TextElideMode.ElideRight, inner))
        font.setPixelSize(13)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(color("text2"))
        painter.drawText(QRectF(left, image_h + 38, inner, 40), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                         _elide_lines(self.scenario.short, QFontMetrics(font), inner, 2))
        font.setPixelSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(color("text"))
        meta = "  ·  ".join(t for t in (self.scenario.price_short, self.scenario.best_short) if t)
        painter.drawText(QRectF(left, self.height() - 30, inner, 18), LEFT_MIDDLE,
                         QFontMetrics(font).elidedText(meta, Qt.TextElideMode.ElideRight, inner))
        painter.end()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.click()
            return
        super().keyPressEvent(event)


class GalleryDialog(QDialog):
    scenarioChosen = pyqtSignal(str)

    def __init__(self, catalogue: Catalogue, parent=None):
        super().__init__(parent)
        self.catalogue = catalogue
        self.setObjectName("mfRoot")
        self.setWindowTitle("Mapflow — Scenarios")
        self.setWindowIcon(icons.app_icon())
        self.setModal(False)
        self.resize(1120, 780)
        self.setMinimumSize(840, 560)
        self.setStyleSheet(stylesheet() + f"""
            QFrame#galSide {{ background: {tokens()['subtle']}; border: 0;
                              border-right: 1px solid {tokens()['border']}; }}
            QWidget#galMain, QWidget#galGrid, QWidget#galDetail {{ background: {tokens()['bg']}; }}
        """)
        self.pictures: Dict[str, QPixmap] = {s.id: scenario_pixmap(catalogue, s, 320, 200) for s in catalogue.scenarios}
        self.current: Optional[Scenario] = None
        self.category = "popular"
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._sidebar())
        self.stack = QStackedWidget(self)
        self.stack.addWidget(self._grid_page())
        self.stack.addWidget(self._detail_page())
        root.addWidget(self.stack, 1)
        QShortcut(QKeySequence.StandardKey.Find, self, activated=self.search.setFocus)
        self.show_category("popular")

    # ---------- sidebar ----------

    def _sidebar(self) -> QWidget:
        side = QFrame(self)
        side.setObjectName("galSide")
        side.setFixedWidth(250)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(12, 18, 12, 16)
        layout.setSpacing(2)
        title = label("Scenarios", "h2")
        title.setContentsMargins(12, 0, 0, 10)
        layout.addWidget(title)
        caption = label("Categories", "label")
        caption.setContentsMargins(12, 0, 0, 6)
        layout.addWidget(caption)
        self.group = QButtonGroup(self)
        self.category_buttons: Dict[str, CategoryButton] = {}
        for category in self.catalogue.categories:
            item = CategoryButton(category["label"], len(self.catalogue.in_category(category["id"])), side)
            item.clicked.connect(lambda _=False, cid=category["id"]: self.show_category(cid))
            self.group.addButton(item)
            self.category_buttons[category["id"]] = item
            layout.addWidget(item)
        layout.addStretch(1)
        help_card = Card(margins=(14, 14, 14, 14), spacing=6)
        help_card.add(label("Need a different object?", "title"))
        help_card.add(label("We train custom models on your imagery and classes.", "meta", wrap=True))
        help_card.add(link("Request a custom model", config.CUSTOM_MODELS_URL))
        help_card.add(link("Models and benchmarks", config.MODELS_DOCS_URL))
        layout.addWidget(help_card)
        return side

    # ---------- grid ----------

    def _grid_page(self) -> QWidget:
        page = QWidget(self)
        page.setObjectName("galMain")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 24, 10, 0)
        layout.setSpacing(16)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 20, 0)
        header.addLayout(vbox(label("Scenarios", "h1"),
                              label("Each scenario sets the model, options and zoom for one task. Choose one, "
                                    "set your area and run.", "lead", wrap=True), spacing=4), 1)
        self.search = QLineEdit(page)
        self.search.setPlaceholderText("Search scenarios")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(icons.icon("search", tokens()["text2"], 16), QLineEdit.ActionPosition.LeadingPosition)
        self.search.setFixedWidth(280)
        self.search.textChanged.connect(self._on_search)
        header.addWidget(self.search, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(header)
        section = QHBoxLayout()
        section.setSpacing(10)
        self.section_title = label("", "h2")
        self.section_count = label("", "meta")
        section.addWidget(self.section_title)
        section.addWidget(self.section_count, 0, Qt.AlignmentFlag.AlignBottom)
        section.addStretch(1)
        layout.addLayout(section)
        self.scroll = QScrollArea(page)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        host = QWidget()
        host.setObjectName("galGrid")
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 20, 24)
        self.empty = Callout("info", "")
        host_layout.addWidget(self.empty)
        self.grid = QGridLayout()
        self.grid.setSpacing(GAP)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        host_layout.addLayout(self.grid)
        host_layout.addStretch(1)
        self.scroll.setWidget(host)
        self.scroll.viewport().installEventFilter(self)
        layout.addWidget(self.scroll, 1)
        self.cards = {}
        for scenario in self.catalogue.scenarios:
            card = ScenarioCard(scenario, self.pictures[scenario.id], host)
            card.clicked.connect(lambda _=False, sid=scenario.id: self.open_scenario(sid))
            card.hide()
            self.cards[scenario.id] = card
        self.visible: List[ScenarioCard] = []
        self._layout_key = None
        return page

    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.Type.Resize:
            if watched is self.scroll.viewport():
                self._reflow()
            elif watched is getattr(self, "detail_image", None):
                self._fit_detail_image()
        return super().eventFilter(watched, event)

    def show_category(self, category_id: str) -> None:
        self.category = category_id
        self.category_buttons[category_id].setChecked(True)
        if self.search.text():
            self.search.blockSignals(True)
            self.search.clear()
            self.search.blockSignals(False)
        name = next(c["label"] for c in self.catalogue.categories if c["id"] == category_id)
        self._show(name, self.catalogue.in_category(category_id))

    def set_query(self, text: str) -> None:
        self.search.setText(text)
        if not text:
            self.show_category(self.category)

    def _on_search(self, text: str) -> None:
        if not text.strip():
            self.show_category(self.category)
            return
        self.group.setExclusive(False)
        for item in self.category_buttons.values():
            item.setChecked(False)
        self.group.setExclusive(True)
        self._show(f"Results for “{text.strip()}”", self.catalogue.search(text))

    def _show(self, title: str, scenarios: List[Scenario]) -> None:
        self.stack.setCurrentIndex(0)
        self.section_title.setText(title)
        self.section_count.setText(f"{len(scenarios)} scenario" + ("" if len(scenarios) == 1 else "s"))
        for card in self.visible:
            card.hide()
        self.visible = [self.cards[s.id] for s in scenarios]
        self.empty.set("info", "" if scenarios else
                       "No scenario matches that search. Try another word, browse the categories, or "
                       f"<a href='{config.CUSTOM_MODELS_URL}'>ask us to train a model</a> for your objects.")
        self._reflow(force=True)
        self.scroll.verticalScrollBar().setValue(0)

    def _reflow(self, force: bool = False) -> None:
        width = self.scroll.viewport().width() - 20
        columns = max(1, min(3, (width + GAP) // (MIN_CARD + GAP)))
        card_width = max(200, (width - GAP * (columns - 1)) // columns)
        key = (columns, card_width, tuple(c.scenario.id for c in self.visible))
        if not force and key == self._layout_key:
            return
        self._layout_key = key
        for card in self.cards.values():
            self.grid.removeWidget(card)
        for index, card in enumerate(self.visible):
            card.set_width(card_width)
            self.grid.addWidget(card, index // columns, index % columns)
            card.show()

    # ---------- detail ----------

    def _detail_page(self) -> QWidget:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        host = QWidget()
        host.setObjectName("galDetail")
        layout = QVBoxLayout(host)
        layout.setContentsMargins(24, 18, 30, 30)
        layout.setSpacing(18)
        crumbs = QHBoxLayout()
        back = button("All scenarios", "ghost", "chevron-left", size="sm")
        back.clicked.connect(self.back)
        self.crumb = label("", "meta")
        crumbs.addWidget(back)
        crumbs.addWidget(self.crumb)
        crumbs.addStretch(1)
        layout.addLayout(crumbs)
        columns = QHBoxLayout()
        columns.setSpacing(30)
        left = QVBoxLayout()
        left.setSpacing(10)
        self.detail_image = QLabel(host)
        self.detail_image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.detail_image.setMinimumWidth(260)
        self.detail_image.installEventFilter(self)
        left.addWidget(self.detail_image)
        left.addWidget(label("Example result from the Mapflow model docs.", "meta"))
        cost = Card(margins=(16, 14, 16, 16), spacing=4)
        cost.add(label("Cost", "label"))
        self.cost_main = label("", "big", wrap=True)
        self.cost_note = label("", "body", wrap=True)
        cost.add(self.cost_main)
        cost.add(self.cost_note)
        left.addWidget(cost)
        left.addStretch(1)
        right = QVBoxLayout()
        right.setSpacing(12)
        self.chips = label("", "meta", wrap=True)
        right.addWidget(self.chips)
        self.detail_title = label("", "h1", wrap=True)
        self.detail_long = label("", "body", wrap=True)
        right.addWidget(self.detail_title)
        right.addWidget(self.detail_long)
        facts = QGridLayout()
        facts.setHorizontalSpacing(16)
        facts.setVerticalSpacing(4)
        self.output = label("", "body", wrap=True)
        self.best = label("", "body", wrap=True)
        for column, (caption, value) in enumerate((("What you get", self.output), ("Works best with", self.best))):
            facts.addWidget(label(caption, "label"), 0, column)
            facts.addWidget(value, 1, column, Qt.AlignmentFlag.AlignTop)
        facts.setColumnStretch(0, 1)
        facts.setColumnStretch(1, 1)
        right.addLayout(facts)
        right.addWidget(label("Usage examples", "label"))
        self.uses = label("", "body", wrap=True)
        self.uses.setTextFormat(Qt.TextFormat.RichText)
        right.addWidget(self.uses)
        self.tip = Callout("info", "")
        right.addWidget(self.tip)
        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.primary = button("Use this scenario", "primary", "play", size="lg")
        self.primary.clicked.connect(self._use)
        docs = button("Model docs", "outline", "book", size="lg", external=True)
        docs.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(config.MODELS_DOCS_URL)))
        actions.addWidget(self.primary)
        actions.addWidget(docs)
        actions.addStretch(1)
        right.addLayout(actions)
        right.addWidget(link("Try it in Mapflow Web", config.WEB_URL))
        right.addStretch(1)
        columns.addLayout(left, 11)
        columns.addLayout(right, 10)
        layout.addLayout(columns)
        layout.addStretch(1)
        scroll.setWidget(host)
        return scroll

    def open_scenario(self, scenario_id: str) -> None:
        scenario = self.catalogue.get(scenario_id)
        if scenario is None:
            return
        self.current = scenario
        category = next((c["label"] for c in self.catalogue.categories
                         if c["id"] not in ("all", "popular") and c["id"] in scenario.categories), "")
        self.crumb.setText(f"/  {category}")
        chips = [plain(scenario.model_label)]
        if scenario.option:
            chips.append(f"+ {scenario.option}")
        if scenario.custom:
            chips.append("On request")
        self.chips.setText("   ·   ".join(chips))
        self.detail_title.setText(scenario.title)
        self.detail_long.setText(scenario.long)
        self.output.setText(scenario.output)
        self.best.setText(scenario.best)
        check = tokens()["check"]
        self.uses.setText("<br>".join(f"<span style='color:{check}; font-weight:700'>✓</span>&nbsp;&nbsp;{u}"
                                      for u in scenario.uses))
        self.tip.set("info", f"<b>Tip.</b> {scenario.tip}" if scenario.tip else "")
        self.cost_main.setText(scenario.cost_main)
        self.cost_note.setText(scenario.cost_note)
        if scenario.custom:
            self.primary.setText("Request access  ↗")
            self.primary.setIcon(icons.icon("external", tokens()["primary_text"], 14))
        else:
            self.primary.setText("Use this scenario")
            self.primary.setIcon(icons.icon("play", tokens()["primary_text"], 14))
        self.stack.setCurrentIndex(1)
        self._fit_detail_image()
        self.primary.setFocus()

    def _fit_detail_image(self) -> None:
        if not self.current:
            return
        width = max(260, self.detail_image.width())
        height = int(width * IMAGE_RATIO)
        self.detail_image.setFixedHeight(height)
        self.detail_image.setPixmap(rounded(self.pictures[self.current.id], width, height, 14))

    def back(self) -> None:
        self.stack.setCurrentIndex(0)
        if self.current and self.current.id in self.cards:
            self.cards[self.current.id].setFocus()

    def _use(self) -> None:
        if not self.current:
            return
        if self.current.custom:
            QDesktopServices.openUrl(QUrl(config.CUSTOM_MODELS_URL))
            return
        self.scenarioChosen.emit(self.current.id)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape and self.stack.currentIndex() == 1:
            self.back()
            return
        super().keyPressEvent(event)
