"""The plugin's pages on Qt 6 (PyQt6), the toolkit of QGIS 4, without QGIS itself.

`tests/qt6_shim` stands in for QGIS 4's `qgis.PyQt`, so this catches what Qt 6 changed: unscoped enums,
exec_(), classes that moved between modules, mouse events, overloaded signals. The map, the API and the
services are covered by the end-to-end flow, which runs in a real QGIS (3 or 4).

    QT_QPA_PLATFORM=offscreen python -m tests.qt6_ui [screenshots dir]      (needs: pip install PyQt6)
"""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests" / "qt6_shim"))
sys.path.insert(1, str(ROOT))

from PyQt6.QtCore import QPoint, QSize, Qt, QTimer  # noqa: E402
from PyQt6.QtTest import QTest  # noqa: E402
from PyQt6.QtWidgets import QApplication, QLabel, QMenu, QPushButton, QSlider, QToolButton, QWidget  # noqa: E402

APP = QApplication.instance() or QApplication(sys.argv[:1])
SHOTS = Path(sys.argv[1]) if len(sys.argv) > 1 else None
results = []


def check(condition, text):
    results.append(bool(condition))
    print(("PASS " if condition else "FAIL ") + text)


def step(name):
    """Run a block of checks; an exception fails it with its traceback instead of stopping the run."""
    def wrap(fn):
        try:
            fn()
        except Exception:                                   # noqa: BLE001
            results.append(False)
            print(f"FAIL {name}: exception")
            traceback.print_exc()
        return fn
    return wrap


def shot(widget, name, size=None):
    if size:
        widget.resize(size)
    for _ in range(5):
        APP.processEvents()
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        widget.grab().save(str(SHOTS / f"{name}.png"))


class Opened:
    """Takes `https` links instead of the system browser, so a check reads the address a link opens."""

    def __init__(self):
        from PyQt6.QtCore import QObject, QUrl, pyqtSlot
        from PyQt6.QtGui import QDesktopServices
        self.urls = []
        outer = self

        class Handler(QObject):
            @pyqtSlot(QUrl)
            def handle(self, url):
                outer.urls.append(url.toString())

        self._handler = Handler()
        QDesktopServices.setUrlHandler("https", self._handler, "handle")

    def close(self):
        from PyQt6.QtGui import QDesktopServices
        QDesktopServices.unsetUrlHandler("https")


TERMS = "https://mapflow.ai/terms-of-use-en.pdf"


def check_terms_link(sign_in, label):
    """The sign-in page's "Terms of use" link shows, fits the page, and opens the terms address on a click."""
    terms = getattr(sign_in, "terms", None)
    check(terms is not None and terms.isVisible() and terms.text().startswith("Terms of use"),
          f"{label}: the sign-in page shows the \"Terms of use\" link")
    if terms is None:
        return
    right = terms.mapTo(sign_in, QPoint(terms.width(), 0)).x()
    check(0 <= terms.mapTo(sign_in, QPoint(0, 0)).x() and right <= sign_in.width(),
          f"{label}: the link is not cut off ({right} of {sign_in.width()} px)")
    opened = Opened()
    try:
        terms.click()
        check(opened.urls == [TERMS], f"{label}: the link opens the terms of use ({opened.urls})")
    finally:
        opened.close()


def spin(ms=50):
    QTest.qWait(ms)


def recorder(signal):
    seen = []
    signal.connect(lambda *args: seen.append(args))
    return seen


import PyQt6.QtCore  # noqa: E402

print(f"Qt {PyQt6.QtCore.QT_VERSION_STR}, PyQt {PyQt6.QtCore.PYQT_VERSION_STR}")

from mapflow_next import config  # noqa: E402
from mapflow_next.core.draft import Issue  # noqa: E402
from mapflow_next.core.models import (CatalogImage, Mosaic, MosaicImage, PlannedProcessing, Processing,  # noqa: E402
                                      Project, UserStatus)
from mapflow_next.core.scenarios import Catalogue  # noqa: E402

from . import fixtures  # noqa: E402

catalogue = Catalogue.load(config.RESOURCES / "scenarios")
project = Project.from_api(fixtures.PROJECT, "me@example.com")
status = UserStatus.from_api(fixtures.STATUS)
state = {}


@step("every module imports on Qt 6")
def _imports():
    import importlib
    names = ["mapflow_next.ui." + p.stem for p in sorted((ROOT / "mapflow_next" / "ui").glob("*.py"))
             if p.stem != "__init__"]
    failed = []
    for name in names:
        try:
            importlib.import_module(name)
        except Exception as error:                         # noqa: BLE001
            failed.append(f"{name}: {error!r}")
    check(not failed, f"all {len(names)} UI modules import on Qt 6 {failed or ''}")
    from mapflow_next.ui import icons
    check(icons.QSvgWidget.__module__.startswith("PyQt6.QtSvgWidgets"),
          "QSvgWidget comes from QtSvgWidgets on Qt 6")


@step("dock: header, tabs, sign-in")
def _dock():
    from mapflow_next.ui.dock import DockContent
    content = DockContent(catalogue)
    content.resize(400, 880)
    content.show()
    state["content"] = content
    sign_in = content.sign_in
    asked = recorder(sign_in.browserRequested)
    browser = sign_in.browser
    check(browser is not None, "sign-in page has the browser button")
    if browser:
        browser.click()
    check(asked, "the browser button asks for a browser sign-in")
    others = next((b for b in sign_in.findChildren(QPushButton) if "other ways" in b.text().lower()), None)
    if others:
        others.click()
        spin()
    shot(content, "q6-01-sign-in")
    check_terms_link(sign_in, "light theme")
    content.set_account("me@example.com")
    content.set_credits("1,240", "Credits left")
    content.set_project(project)
    content.show_signed_in()
    content.go(0)
    content.start.set_recent(project.name, [Processing.from_api(fixtures.processing_json("p-1", "OK", 100))], set())
    spin()
    shot(content, "q6-02-start")
    check(content.isVisible() and content.current_tab() == 0, "signed in, the Start tab shows")
    chosen = recorder(content.start.scenarioChosen)
    tiles = list(content.start._tiles)
    if tiles:
        QTest.mouseClick(tiles[0], Qt.MouseButton.LeftButton)
    check(tiles and chosen, f"clicking a scenario tile chooses it ({len(tiles)} tiles)")


@step("account menu")
def _menu():
    content = state["content"]
    settings = recorder(content.settingsRequested)
    sign_out = recorder(content.signOutRequested)
    menu = content.account_menu
    actions = {a.text(): a for a in menu.actions()}
    check("Settings…" in actions and "Sign out" in actions, f"the account menu has its actions {list(actions)}")
    actions["Settings…"].trigger()
    actions["Sign out"].trigger()
    check(settings and sign_out, "Settings… and Sign out work on Qt 6 (QAction.triggered passes checked)")


@step("dock: upgrade page")
def _upgrade():
    from mapflow_next.ui.dock import PAGE_UPGRADE, DockContent
    content = DockContent(catalogue)
    content.resize(400, 880)
    content.show()
    content.show_upgrade("5.0.0", "4.0.0")
    page = content.upgrade
    check(content.stack.currentWidget() is page and content.stack.currentIndex() == PAGE_UPGRADE,
          "the upgrade page is the current page")
    check(not content.header.isVisible() and not content.tabs.isVisible() and not content.footer.isVisible(),
          "header, tabs and footer are hidden on it")
    text = page.message.text()
    check("5.0.0" in text and "4.0.0" in text and "Upgrade" in text,
          f"it names both versions and says to upgrade ({text})")
    upgrade, sign_out = recorder(page.upgradeRequested), recorder(page.signOutRequested)
    page.upgrade.click()
    page.sign_out.click()
    check(len(upgrade) == 1 and len(sign_out) == 1, "its two buttons emit upgradeRequested and signOutRequested")
    shot(content, "q6-01c-upgrade")
    content.show_signed_out()
    check(content.stack.currentWidget() is content.sign_in, "show_signed_out leaves the upgrade page")


@step("run form")
def _run():
    from mapflow_next.ui.run_page import CostView, ImageryRow
    content = state["content"]
    content.open_run()
    run = content.run
    scenario = catalogue.scenarios[0]
    from mapflow_next.ui.start_page import scenario_pixmap
    run.set_scenario(scenario.title, scenario_pixmap(catalogue, scenario, 52, 34))
    run.set_name("Buildings · Old town", "")
    models = project.models
    run.set_models(models, models[0].id)
    run.set_options(models[0], set(), "10 cr/km²")
    run.set_layers([("layer-1", "Old town"), ("layer-2", "Blocks")], "layer-1")
    run.set_area("1.40 km²", "Old town · 1 polygon · within your 100 km² limit")
    run.set_area_hint("info", "The area is the whole extent of “centre.tif”. Draw a smaller one?",
                      (("draw", "Draw an area"), ("previous", "Back to Old town")))
    rows = [ImageryRow(key="mosaic", title="My imagery", meta="Drone survey March · 3 images", pick="Choose…",
                       price="Free", previewable=True),
            ImageryRow(key="provider:mapbox", title="Mapbox Satellite", meta="z18 · 0.6 m/px · recommended",
                       price="Free", zooms=[17, 18, 19], zoom=18, recommended_zoom=18, previewable=True)]
    run.set_imagery(rows, "provider:mapbox", "Recommended for this scenario: 0.5 m/px or better")
    run.set_steps(True, True, True)
    run.set_cost(CostView(value="70 credits", formula="1.40 km² × 50 cr/km²", balance="Balance after run: 1,170",
                          show_top_up=True), True)
    run.set_issues([], False)
    spin()
    shot(content, "q6-03-run")
    run_asked = recorder(run.runRequested)
    rename = recorder(run.renameRequested)
    model = recorder(run.modelChosen)
    layer = recorder(run.layerChosen)
    zoom = recorder(run.zoomChosen)
    option = recorder(run.optionToggled)
    action = recorder(run.areaAction)
    run.run_button.click()
    run.rename_button.click()
    check(run_asked and rename, "Run and the pencil by the name emit their signals")
    run.model_combo.setCurrentIndex(1)
    run.model_combo.activated.emit(1)
    run.layer_combo.activated.emit(1)
    check(model and layer, "choosing a model and a layer works")
    switch = next(iter(run._switches.values()), None)
    if switch is not None:
        QTest.mouseClick(switch, Qt.MouseButton.LeftButton)
    check(option or switch is None, f"an option switch toggles ({len(run._switches)} options)")
    next(iter(run.area_hint_buttons.values())).click()
    check(action, "the area suggestion's buttons work")
    combos = [c for c in run.findChildren(type(run.model_combo)) if c is not run.model_combo
              and c is not run.layer_combo and c.isVisible()]
    for combo in combos:
        combo.activated.emit(0)
    check(zoom or not combos, f"the zoom list chooses a zoom {zoom[-1:]}")
    from PyQt6.QtCore import QPointF
    from PyQt6.QtGui import QWheelEvent
    if combos:
        before = combos[0].currentIndex()
        wheel = QWheelEvent(QPointF(5, 5), QPointF(5, 5), QPoint(0, 0), QPoint(0, -120), Qt.MouseButton.NoButton,
                            Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
        combos[0].wheelEvent(wheel)
        check(combos[0].currentIndex() == before and not wheel.isAccepted(),
              "the wheel over a closed zoom list is left to the form")
    rows[1].previewing = True
    run.set_imagery(rows, "provider:mapbox")
    spin()
    eyes = [b for b in run.findChildren(QToolButton) if b.toolTip() == "Hide the preview" and b.isVisible()]
    check(len(eyes) == 1 and eyes[0].property("on") is True, "the eye shows a preview on the map as on")
    tiles = rows + [ImageryRow(key="tile:l1", title="Tiles XYZ", meta="zoom 2–17", price="In estimate",
                               zooms=list(range(2, 18)), zoom=17, group="QGIS tile layers"),
                    ImageryRow(key="tile:l2", title="Tiles local", meta="Its host is this computer or a private "
                               "network address. Mapflow cannot reach it.", group="QGIS tile layers",
                               disabled=True)]
    run.set_imagery(tiles, "tile:l1")
    spin()
    heading = [label.text() for label in run.group_labels]
    disabled = run._rows[-1]
    chosen = recorder(run.imageryChosen)
    disabled.clicked.emit()
    check(heading == ["QGIS tile layers"] and len(run._rows) == 4 and not disabled.isEnabled()
          and disabled.toolTip() == disabled.meta.text() and not chosen
          and not [t for t in run._rows[-2].findChildren(QToolButton) if t.toolTip().startswith("Preview")],
          "a tile layer is a row under its heading, a disabled one shows its reason and chooses nothing")
    shot(content, "q6-03b-run-tiles")
    run.set_issues([Issue("area", "Choose an area")], False)
    check(not run.run_button.isEnabled(), "an issue disables Run")


@step("tile login alert")
def _tile_alert():
    from mapflow_next.ui.tile_login_alert import TEXT, TileLoginAlert
    box = TileLoginAlert("Tiles XYZ")
    box.show()
    check(box.text() == TEXT.replace("{layer}", "Tiles XYZ") and box.send_button.text() == "Send and run"
          and box.cancel_button.text() == "Cancel" and box.checkbox.text() == "Don't show this again"
          and box.defaultButton() is box.cancel_button, "the tile login alert shows the text, the buttons and the box")
    box.checkbox.setChecked(True)
    box.send_button.click()
    sent = box.outcome()
    box = TileLoginAlert("Tiles XYZ")
    box.show()
    box.checkbox.setChecked(True)
    box.cancel_button.click()
    check(sent == (True, True) and box.outcome() == (False, False),
          "Send and run keeps the box, Cancel never does")


@step("rename dialog")
def _rename():
    from mapflow_next.ui.rename_dialog import RenameDialog
    seen = []

    def fill():
        dialog = QApplication.activeModalWidget()
        seen.append(type(dialog).__name__ if dialog else None)
        if dialog:
            dialog.name.setText("Centre roofs")
            dialog.description.setPlainText("Roofs inside the survey")
            dialog.accept()
    QTimer.singleShot(200, fill)
    dialog = RenameDialog("Buildings · Old town", "", None, title="Name this processing")
    accepted = dialog.exec()
    check(accepted and seen == ["RenameDialog"] and dialog.values() == ("Centre roofs", "Roofs inside the survey"),
          "the name dialog runs modally with exec() and returns the name and description")


@step("report dialog")
def _report_dialog():
    from urllib.parse import parse_qs, urlsplit
    from PyQt6.QtCore import QObject, QUrl, pyqtSlot
    from mapflow_next.core.report import Environment, RequestInfo, technical_text
    from mapflow_next.ui.report_dialog import ReportDialog
    from PyQt6.QtGui import QDesktopServices

    class Mail(QObject):
        def __init__(self):
            super().__init__()
            self.opened = []

        @pyqtSlot(QUrl)
        def handle(self, url):
            self.opened.append(url.toString(QUrl.ComponentFormattingOption.FullyEncoded))

    mail = Mail()
    QDesktopServices.setUrlHandler("mailto", mail, "handle")
    request = RequestInfo("GET", "https://api.example.com/rest/user/status?token=SECRET", 200,
                          '{"access_token": "AAA", "name": "kept"}')
    environment = Environment("4.0.0", "4.2.0", "6.8.0", "Linux", "production")
    technical = technical_text("ValueError: boom", "Traceback (most recent call last):\nValueError: boom",
                               request, environment)
    dialog = ReportDialog("ValueError: boom", technical, config.SUPPORT_EMAIL, "4.0.0")
    dialog.show()
    shot(dialog, "q6-report-dialog", QSize(600, 560))
    check(dialog.summary_label.text() == "ValueError: boom", "the report dialog shows the one-line summary")
    check(dialog.report_view.isReadOnly() and dialog.report_view.toPlainText() == technical
          and "Request: GET https://api.example.com/rest/user/status\n" in technical
          and "SECRET" not in technical and "AAA" not in technical,
          "the technical text is read-only, and has the request without its query and without secrets")
    check(dialog.report_text() == technical, "without a comment the report is the technical text")
    dialog.comment.setPlainText("I pressed Run")
    check(dialog.report_text() == "I pressed Run\n\n" + technical, "the comment goes above the technical text")
    dialog.send()
    check(len(mail.opened) == 1 and mail.opened[0].startswith(f"mailto:{config.SUPPORT_EMAIL}?subject=")
          and parse_qs(urlsplit(mail.opened[0]).query)["body"] == [dialog.report_text().replace("\n", "\r\n")],
          "Send opens a mailto: link to Mapflow support with the report")
    dialog.copy()
    check(QApplication.clipboard().text() == dialog.report_text(), "Copy puts the same text on the clipboard")
    dialog.close()


def _available_for_me(page, searched) -> None:
    from mapflow_next.ui.widgets import Toggle
    switch = getattr(page, "available", None)
    check(isinstance(switch, Toggle) and not switch.isChecked() and switch.accessibleName() == "Available for me",
          "Search has an \"Available for me\" switch, off by default")
    check(searched[-1][0].get("hide_unavailable") is False, "Search sends hide_unavailable False by default")
    sent = len(searched)
    switch.setChecked(True)
    check(len(searched) == sent, "moving the switch asks for no search")
    page.search_button.click()
    check(len(searched) == sent + 1 and searched[-1][0].get("hide_unavailable") is True,
          "Search sends hide_unavailable True when the switch is on")
    switch.setChecked(False)
    page.search_button.click()
    check(searched[-1][0].get("hide_unavailable") is False, "…and False again when it is turned off")


def _off_nadir(page, searched):
    from mapflow_next.ui.widgets import RangeSlider
    nadir = page.nadir
    check(isinstance(nadir, RangeSlider) and (nadir.low(), nadir.high()) == (0, 30)
          and (nadir.minimum(), nadir.maximum()) == (0, 30) and page.nadir_value.text() == "0°–30°",
          "the off-nadir control is a range slider, 0-30 by default, and its label shows both ends")
    check(nadir.height() >= 20, f"the range slider is tall enough for its handle ({nadir.height()} px)")
    changes, sent = recorder(nadir.valuesChanged), len(searched)
    nadir.setValues(10, 25)
    check(changes == [(10, 25)] and page.nadir_value.text() == "10°–25°" and len(searched) == sent,
          f"setValues moves both handles, shows both ends, and asks for no search ({changes})")
    nadir.setValues(10, 25)
    check(len(changes) == 1, "a value that does not change emits nothing")
    nadir.setValues(28, 3)
    check(0 <= nadir.low() <= nadir.high() <= 30, f"values are clamped, low <= high ({nadir.low()}, {nadir.high()})")
    nadir.setValues(-5, 99)
    check((nadir.low(), nadir.high()) == (0, 30), "values out of range are clamped to 0-30")
    nadir.setValues(10, 25)
    page.search_button.click()
    check(searched[-1][0]["min_off_nadir"] == 10.0 and searched[-1][0]["max_off_nadir"] == 25.0
          and len(searched) == sent + 1, "Search sends the range that was set")
    middle, none = nadir.height() // 2, Qt.KeyboardModifier.NoModifier

    def drag(start, end):
        QTest.mousePress(nadir, Qt.MouseButton.LeftButton, none, QPoint(start, middle))
        QTest.mouseMove(nadir, QPoint(end, middle))
        QTest.mouseRelease(nadir, Qt.MouseButton.LeftButton, none, QPoint(end, middle))
    drag(nadir.width() - 8, nadir.width() // 2)
    check(nadir.low() == 10 and 10 <= nadir.high() < 25, f"dragging the high handle lowers it ({nadir.high()})")
    drag(nadir.width() // 2, 2)
    check(nadir.low() <= nadir.high() and nadir.low() <= 10,
          f"a handle never crosses the other ({nadir.low()}, {nadir.high()})")
    nadir.setValues(10, 25)
    nadir.setFocus()
    before = (nadir.low(), nadir.high())
    QTest.keyClick(nadir, Qt.Key.Key_Left)
    moved = (nadir.low(), nadir.high())
    check(sum(abs(a - b) for a, b in zip(before, moved)) == 1,
          f"the Left key moves a handle by 1 ({before} -> {moved})")
    QTest.keyClick(nadir, Qt.Key.Key_Home)
    QTest.keyClick(nadir, Qt.Key.Key_End)
    check(nadir.low() <= nadir.high() and 0 <= nadir.low() and nadir.high() <= 30,
          f"Home and End keep the handles in range ({nadir.low()}, {nadir.high()})")
    check(len(searched) == sent + 1, "no search was asked for while the control moved")
    nadir.setValues(0, 30)


@step("imagery search and My imagery")
def _imagery():
    from mapflow_next.ui.imagery_page import MINE, SEARCH

    content = state["content"]
    content.go(2)
    page = content.imagery
    check(page.current_tab() == MINE, "My imagery is the default tab")
    page.show_tab(SEARCH)
    page.set_layers([("layer-1", "Old town"), ("layer-2", "Blocks")], "layer-1")
    page.set_area("1 polygon · 1.40 km²", True)
    searched = recorder(page.searchRequested)
    page.cloud.setValue(35)
    page.search_button.click()
    check(searched and searched[-1][0]["max_cloud"] == 35.0, "Search sends the slider's cloud cover")
    check(searched[-1][0]["min_off_nadir"] == 0.0 and searched[-1][0]["max_off_nadir"] == 30.0,
          "Search sends both ends of the off-nadir range, the full 0-30 by default")
    _available_for_me(page, searched)
    _off_nadir(page, searched)
    images = [CatalogImage.from_api(item) for item in fixtures.CATALOG["images"]]
    page.set_results(images, len(images), None)
    spin()
    shot(content, "q6-06-imagery")
    check(isinstance(page.cloud, QSlider) and page.cloud.height() >= 20,
          f"sliders are tall enough for their handle ({page.cloud.height()} px)")
    cleared = recorder(page.clearRequested)
    page.clear_button.click()
    use = recorder(page.useImage)
    for b in page.findChildren(QPushButton):
        if b.text() == "Use" and b.isVisible():
            b.click()
            break
    check(cleared and use, "Clear and Use work")
    chosen = recorder(page.layerChosen)
    page.layer_combo.activated.emit(2 if page.layer_combo.count() > 2 else 1)
    check(chosen, "the Area drop-down chooses a layer")
    page.date_from.setDate(page.date_from.date().addDays(-10))
    check(page.date_from.calendarPopup(), "dates have a calendar")
    page.show_tab(MINE)
    mosaics = [Mosaic.from_api(item) for item in fixtures.MOSAICS]
    page.set_mosaics(mosaics, None)
    spin()
    shot(content, "q6-08-my-imagery")
    texts = [w.text() for w in page.findChildren(QLabel) if w.isVisible()]
    check(any("Drone survey March" in t for t in texts), "My imagery lists the collections")


@step("processings")
def _processings():
    content = state["content"]
    content.go(1)
    page = content.processings
    items = [Processing.from_api(fixtures.processing_json(f"p-{n}", status, percent, name=f"Buildings · site {n}"))
             for n, (status, percent) in enumerate([("IN_PROGRESS", 40), ("OK", 100), ("FAILED", 0)] * 4)]
    page.set_items(items, {"p-1"}, set(), True, total=30)
    spin()
    shot(content, "q6-04-processings")
    more = recorder(page.moreRequested)
    page.more_button.click()
    check(more, "“Show more” asks for the next page")
    cards = [w for w in page.findChildren(QWidget) if type(w).__name__ == "ProcessingCard"]
    expanded = recorder(cards[1].clicked) if cards else []
    if cards:
        QTest.mouseClick(cards[1], Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(20, 12))
    check(expanded, f"clicking a processing card works (mouse position on Qt 6) ({len(cards)} cards)")
    menus = [m for m in page.findChildren(QMenu)]
    rename = recorder(page.rename)
    for menu in menus:
        for action in menu.actions():
            if action.text().startswith("Rename"):
                action.trigger()
                break
    check(rename or not menus, f"the processing menu's Rename works ({len(menus)} menus)")

    page.set_items(items, set(), set(), True, total=30,
                   planned=[PlannedProcessing.from_api(fixtures.planned_json("tpl-1", "Harbor watch", "Searching"))])
    spin()
    layout = [page.list.itemAt(i).widget() for i in range(page.list.count())]
    kinds = [type(w).__name__ for w in layout if type(w).__name__ in ("PlannedCard", "ProcessingCard")]
    planned = next((w for w in layout if type(w).__name__ == "PlannedCard"), None)
    check(kinds[:2] == ["PlannedCard", "ProcessingCard"] and planned is not None
          and not planned.findChildren(QToolButton), f"a planned processing shows first, with no menu ({kinds[:2]})")
    opened = recorder(page.plannedOpened)
    if planned is not None:
        QTest.mouseClick(planned, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(20, 12))
    check(opened == [("tpl-1",)], f"clicking a planned processing emits its id (mouse position on Qt 6) ({opened})")


@step("projects window")
def _projects():
    from mapflow_next.ui.projects_dialog import ProjectsDialog
    dialog = ProjectsDialog()
    projects = [Project.from_api(fixtures.PROJECT, "me@example.com"),
                Project.from_api(fixtures.PROJECT_2, "me@example.com")]
    projects += [Project.from_api(item, "me@example.com") for item in fixtures.MORE_PROJECTS[:6]]
    dialog.show()
    dialog.set_state("project-1", ["project-2"])
    dialog.set_results(projects, 45)
    spin(100)
    shot(dialog, "q6-14-projects", QSize(900, 640))
    check(len(dialog.tiles) == len(projects), f"projects show as tiles ({len(dialog.tiles)})")
    chosen = recorder(dialog.projectChosen)
    pinned = recorder(dialog.pinToggled)
    tile = dialog.tiles[1]
    QTest.mouseClick(tile, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(60, 60))
    QTest.keyClick(tile, Qt.Key.Key_Return)
    tile.pin_button.click()
    check(len(chosen) == 2 and pinned, "a tile opens by click and by Enter; the pin works")
    renamed = recorder(dialog.renameRequested)
    by_id = {t.project.id: t for t in dialog.tiles}
    check(by_id["project-1"].more_button is None and by_id["project-2"].more_button is not None
          and [a.text() for a in by_id["project-2"].menu().actions()] == ["Rename…", "Delete…"],
          "the default project has no ⋯ menu; an own project's offers Rename… and Delete…")
    by_id["project-2"].menu().actions()[0].trigger()
    check(renamed == [("project-2",)], f"Rename… asks to rename the project ({renamed})")
    dialog.project_renamed("project-2", "Harbor east", "New yards")
    check(any(t.project.id == "project-2" and t.project.name == "Harbor east" for t in dialog.tiles),
          "a renamed project shows its new name")
    deleted = recorder(dialog.deleteRequested)
    by_id["project-2"].menu().actions()[1].trigger()
    check(deleted == [("project-2",)], f"Delete… asks to delete the project ({deleted})")
    dialog.project_deleted("project-2")
    check(all(t.project.id != "project-2" for t in dialog.tiles) and "project-2" not in dialog.pinned_ids
          and dialog.total == 44 and next(t for t in dialog.tiles if t.project.id == "project-1").more_button is None,
          "a deleted project leaves the tiles, the pins and the count")
    dialog.set_note("warn", "Couldn't rename")
    check(dialog.note.isVisibleTo(dialog), "a note shows in the window")
    dialog.close()


@step("My imagery picker")
def _picker():
    from mapflow_next.ui.mosaic_picker import MosaicPicker
    picker = MosaicPicker()
    picker.show()
    mosaics = [Mosaic.from_api(item) for item in fixtures.MOSAICS]
    picker.set_collections(mosaics, None, None)
    picker.open_collection("m-1")
    picker.set_images("m-1", [MosaicImage.from_api(fixtures.mosaic_image(f"m-1-i{n}", "m-1", name))
                              for n, name in enumerate(fixtures.MOSAIC_IMAGES["m-1"], 1)])
    spin()
    shot(picker, "q6-13-picker", QSize(820, 560))
    chosen = recorder(picker.chosen)
    picker.use_all.click()
    check(chosen == [("m-1", "")], "“Use the whole collection” works")
    picker.close()


@step("scenario gallery")
def _gallery():
    from mapflow_next.ui.gallery import GalleryDialog
    gallery = GalleryDialog(catalogue)
    gallery.show()
    spin(100)
    shot(gallery, "q6-09-gallery")
    check(gallery.isVisible(), "the gallery opens")
    gallery.close()


@step("settings")
def _settings():
    from mapflow_next.ui.settings_dialog import SettingsDialog

    class Settings(dict):                                       # the plugin's Settings, in memory
        def value(self, key, default=None):
            return self.get(key, default)

        def flag(self, key, default=False):
            return bool(self.get(key, default))

        def setValue(self, key, value):
            self[key] = value

        def remove(self, key):
            self.pop(key, None)
    seen = []

    def close():
        dialog = QApplication.activeModalWidget()
        seen.append(type(dialog).__name__ if dialog else None)
        if dialog:
            dialog.reject()
    QTimer.singleShot(200, close)
    dialog = SettingsDialog(Settings(), "me@example.com", "https://whitemaps-production.mapflow.ai/rest")
    dialog.exec()
    check(seen == ["SettingsDialog"], "the settings dialog opens")


@step("dark theme")
def _dark():
    from PyQt6.QtGui import QColor, QPalette
    from mapflow_next.ui import theme
    from mapflow_next.ui.dock import DockContent
    palette = QPalette(APP.palette())
    palette.setColor(QPalette.ColorRole.Window, QColor("#2b2b2b"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#eeeeee"))
    APP.setPalette(palette)
    for name in ("_tokens_cache", "_dark"):
        if hasattr(theme, name):
            setattr(theme, name, None)
    content = DockContent(catalogue)
    content.show()
    shot(content, "q6-12-dark-sign-in", QSize(400, 880))
    check(theme.is_dark() and theme.tokens()["link"] == "#90cdf4"
          and theme.tokens()["link"] != theme.tokens()["subtle"],
          "dark theme: the link colour differs from the page background")
    check_terms_link(content.sign_in, "dark theme")
    content.set_account("me@example.com")
    content.set_project(project)
    content.show_signed_in()
    shot(content, "q6-12-dark", QSize(400, 880))
    check(True, "the dock renders with a dark palette")


@step("network: browser sign-in and API calls on Qt 6")
def _network():
    import tempfile
    import threading
    import urllib.error
    import urllib.request
    from urllib.parse import parse_qs, urlsplit

    from mapflow_next.api import oauth as oauth_api
    from mapflow_next.api.client import MapflowApi
    from mapflow_next.api.http import Http
    from mapflow_next.config import Config

    from . import mock_server

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(NoRedirect)

    def browse(url):
        """One browser request in a thread (the plugin answers on this event loop): (status, Location)."""
        result = {}

        def run():
            try:
                with opener.open(url, timeout=10) as reply:
                    result["value"] = (reply.status, reply.headers.get("Location", ""))
            except urllib.error.HTTPError as exc:
                result["value"] = (exc.code, exc.headers.get("Location", ""))
            except (urllib.error.URLError, OSError):
                result["value"] = (0, "")
        threading.Thread(target=run, daemon=True).start()
        for _ in range(300):
            if "value" in result:
                break
            spin(50)
        return result.get("value", (0, ""))

    def wait(condition, seconds=10):
        for _ in range(int(seconds * 20)):
            if condition():
                return True
            spin(50)
        return condition()

    server, mock, api_url = mock_server.start()
    try:
        http = Http(api_url, "4.0.0")
        settings = Config(env="production", server=api_url, auth_url=mock_server.auth_url(api_url))
        opened = []
        oauth_api.open_in_browser = lambda url: opened.append(url) or True
        sign_in = oauth_api.BrowserSignIn(settings, http)
        tokens, failures = [], []
        sign_in.succeeded.connect(tokens.append)
        sign_in.failed.connect(failures.append)
        sign_in.start()
        check(opened and parse_qs(urlsplit(opened[-1]).query).get("client_id") == ["qgis"],
              f"browser sign-in opens the sign-in page {failures}")
        status, back = browse(opened[-1])
        status, landing = browse(back) if status == 302 else (status, "")
        check(status == 302 and landing == config.SIGNED_IN_URL,
              f"the loopback listener (QTcpServer) takes the code and sends the browser on ({status} {landing})")
        check(wait(lambda: tokens), "the code is exchanged for tokens (form POST)")
        if not tokens:
            return
        http.bearer = tokens[-1].access
        api = MapflowApi(http)
        got = {}
        api.user_status(lambda value: got.setdefault("status", value), lambda e: got.setdefault("error", e))
        api.processings("project-1", lambda items, total: got.setdefault("processings", (items, total)),
                        lambda e: got.setdefault("error", e))
        check(wait(lambda: "status" in got and "processings" in got) and "error" not in got,
              f"GET and POST with JSON work, with the bearer token ({got.get('error')})")
        items = got.get("processings", ([], 0))[0]
        check(items and got["status"].remaining_credits == 1240, "responses parse into the plugin's models")
        api.rename(items[0], "Renamed", "On Qt 6", lambda *_: got.setdefault("renamed", True),
                   lambda e: got.setdefault("rename_error", e))
        check(wait(lambda: "renamed" in got or "rename_error" in got) and "renamed" in got, "PUT works")
        target = str(Path(tempfile.mkdtemp()) / "result.geojson")
        api.download_result("old-1", target, lambda path: got.setdefault("downloaded", path),
                            lambda e: got.setdefault("download_error", e))
        check(wait(lambda: "downloaded" in got or "download_error" in got) and Path(target).exists()
              and Path(target).stat().st_size > 100,
              f"results stream to a file (QSaveFile) ({got.get('download_error')})")
        api.processing("does-not-exist", lambda *_: got.setdefault("found", True),
                       lambda e: got.setdefault("missing", e))
        check(wait(lambda: "missing" in got or "found" in got)
              and getattr(got.get("missing"), "kind", "") == "not_found",
              f"a 404 becomes a readable “not found” error (QNetworkReply error enums) ({got.get('missing')!r})")
        # credentials stay with the API's origin: another port gets none, directly or through a redirect
        other_server, other, other_url = mock_server.start()
        try:
            def sent_headers(path):
                return [{k.lower(): v for k, v in r[3].items()} for r in other.requests if r[1] == path]
            picture = "/open/preview.png"
            api.preview(f"{other_url}/open/preview.png", lambda data: got.setdefault("picture", data),
                        lambda e: got.setdefault("picture_error", e))
            check(wait(lambda: "picture" in got or "picture_error" in got) and got.get("picture") == mock_server.PNG
                  and sent_headers(picture) and "authorization" not in sent_headers(picture)[-1],
                  f"a Bearer request to another port loads the picture with no Authorization header "
                  f"({got.get('picture_error')})")
            api.preview(f"redirect?to={other_url}/open/preview.png", lambda data: got.setdefault("hop", data),
                        lambda e: got.setdefault("hop_error", e))
            check(wait(lambda: "hop" in got or "hop_error" in got) and got.get("hop") == mock_server.PNG
                  and len(sent_headers(picture)) == 2 and "authorization" not in sent_headers(picture)[-1],
                  f"a redirect from the API to another port arrives without Authorization (manual redirect policy "
                  f"on Qt 6) ({got.get('hop_error')})")
        finally:
            other_server.shutdown()
        http.bearer = "expired"
        api.user_status(lambda *_: got.setdefault("ok_with_bad_token", True), lambda e: got.setdefault("denied", e))
        check(wait(lambda: "denied" in got or "ok_with_bad_token" in got)
              and getattr(got.get("denied"), "kind", "") == "auth",
              "a rejected token is reported as a sign-in problem")
    finally:
        server.shutdown()


passed = sum(results)
print(f"\n{passed}/{len(results)} checks passed on Qt 6")
sys.exit(0 if passed == len(results) else 1)
