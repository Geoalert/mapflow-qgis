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
from mapflow_next.core.models import (CatalogImage, Mosaic, MosaicImage, Processing, Project,  # noqa: E402
                                      UserStatus)
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
    run.set_issues([Issue("area", "Choose an area")], False)
    check(not run.run_button.isEnabled(), "an issue disables Run")


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


@step("imagery search and My imagery")
def _imagery():
    content = state["content"]
    content.go(2)
    page = content.imagery
    page.set_layers([("layer-1", "Old town"), ("layer-2", "Blocks")], "layer-1")
    page.set_area("1 polygon · 1.40 km²", True)
    searched = recorder(page.searchRequested)
    page.cloud.setValue(35)
    page.search_button.click()
    check(searched and searched[-1][0]["max_cloud"] == 35.0, "Search sends the slider's cloud cover")
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
    page.show_tab(1)
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
    content.set_account("me@example.com")
    content.set_project(project)
    content.show_signed_in()
    content.show()
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
