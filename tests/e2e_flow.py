"""End to end in real QGIS (offscreen) against the mock API: sign in → scenario → area → imagery → run →
results on the map, plus imagery search, the gallery and sign-out. Saves screenshots when given a folder.

    python3 -m tests.e2e_flow [screenshot-folder]
"""
import os
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .qgis_env import FakeIface, start_qgis, wait_until

APP = start_qgis()

from qgis.PyQt.QtCore import QObject, QSize, Qt, QTimer, QUrl, pyqtSlot  # noqa: E402
from qgis.PyQt.QtGui import QDesktopServices  # noqa: E402
from qgis.PyQt.QtTest import QTest  # noqa: E402
from qgis.PyQt.QtWidgets import QAction, QSlider, QToolButton  # noqa: E402
from qgis.PyQt.QtGui import QColor, QPalette  # noqa: E402
from qgis.PyQt.QtWidgets import QApplication, QComboBox, QLabel, QPushButton  # noqa: E402
from qgis.core import (QgsFeature, QgsGeometry, QgsPointXY, QgsProject, QgsRectangle, QgsSettings,  # noqa: E402
                       QgsVectorLayer, QgsVectorTileLayer)

from . import fixtures, mock_server  # noqa: E402
from mapflow_next import config  # noqa: E402

SHOTS = Path(sys.argv[1]) if len(sys.argv) > 1 else None
CHECKS = []


def check(condition, text):
    CHECKS.append((bool(condition), text))
    print(("PASS " if condition else "FAIL ") + text, flush=True)
    return condition


def shot(widget, name, size=None):
    if not SHOTS:
        return
    SHOTS.mkdir(parents=True, exist_ok=True)
    if size:
        widget.resize(size)
    for _ in range(5):
        APP.processEvents()
    widget.grab().save(str(SHOTS / f"{name}.png"))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)


def browse(url):
    """One browser request, without following redirects: (status, Location). Runs in a thread
    because the plugin answers on the main thread's event loop. Status 0: nothing listening."""
    result = {}

    def run():
        try:
            with _OPENER.open(url, timeout=10) as reply:
                result["value"] = (reply.status, reply.headers.get("Location", ""))
        except urllib.error.HTTPError as exc:
            result["value"] = (exc.code, exc.headers.get("Location", ""))
        except (urllib.error.URLError, OSError):
            result["value"] = (0, "")
    threading.Thread(target=run, daemon=True).start()
    wait_until(lambda: "value" in result, 15)
    return result.get("value", (0, ""))


class FakeBrowser:
    """Stands in for the system browser: records the pages the plugin opens."""

    def __init__(self):
        self.opened = []

    def open(self, url):
        self.opened.append(url)
        return True


class UrlRecorder(QObject):
    """Takes https links instead of the system browser, so tests can see what would open."""

    def __init__(self):
        super().__init__()
        self.opened = []

    @pyqtSlot(QUrl)
    def handle(self, url):
        self.opened.append(url.toString())


def close_modal_later(record, fill=None, delay=300):
    """A modal dialog blocks in exec(): look at it shortly after it opens, then close it."""
    def close():
        dialog = QApplication.activeModalWidget()
        record.append(type(dialog).__name__ if dialog else None)
        if dialog is not None:
            if fill is not None:
                fill(dialog)
                dialog.accept()
            else:
                dialog.reject()
    QTimer.singleShot(delay, close)


def blocks_layer():
    layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "Blocks", "memory")
    features = []
    for wkt in ("POLYGON((37.60 55.746, 37.605 55.746, 37.605 55.749, 37.60 55.749, 37.60 55.746))",
                "POLYGON((37.607 55.746, 37.612 55.746, 37.612 55.749, 37.607 55.749, 37.607 55.746))"):
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromWkt(wkt))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    layer.updateExtents()
    return layer


def old_town_layer():
    layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "Old town", "memory")
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromWkt(
        "POLYGON((37.595 55.745, 37.615 55.745, 37.615 55.755, 37.595 55.755, 37.595 55.745))"))
    layer.dataProvider().addFeatures([feature])
    layer.updateExtents()
    return layer


def main():
    server, state, url = mock_server.start()
    links = UrlRecorder()
    QDesktopServices.setUrlHandler("https", links, "handle")       # no real browser opens during the test
    QDesktopServices.setUrlHandler("http", links, "handle")
    out_dir = tempfile.mkdtemp(prefix="mapflow-results-")
    settings = QgsSettings()
    check("mapflow-next-data-" in settings.fileName(), "the test runs with its own QGIS settings")
    settings.setValue("mapflow_next/server", url)
    settings.setValue("mapflow_next/auth_url", mock_server.auth_url(url))
    settings.setValue("mapflow_next/output_dir", out_dir)
    settings.setValue("mapflow_next/auto_load", True)

    from mapflow_next import classFactory
    iface = FakeIface()
    iface.window.show()
    plugin = classFactory(iface)
    plugin.initGui()
    check(len(iface.toolbar_actions) == 1, "toolbar button added")
    plugin.toggle(True)
    content = plugin.dock.content
    session, processings, controller = plugin.services[1], plugin.services[2], plugin.controller
    processings._poll.setInterval(150)
    check(wait_until(lambda: session.state == "signed_out", 3), "starts signed out without a saved sign-in")
    content.sign_in.more.click()
    check(content.sign_in.token_box.isVisible(), "clicking “Other ways to sign in” shows the API token field")
    content.sign_in.more.click()
    check(not content.sign_in.token_box.isVisible(), "clicking it again folds the token field away")
    shot(content, "01-sign-in", QSize(400, 880))

    # ---------- browser sign-in ----------
    from mapflow_next.api import auth
    from mapflow_next.api import oauth as oauth_api
    browser = FakeBrowser()
    oauth_api.open_in_browser = browser.open
    content.sign_in.browserRequested.emit()
    query = parse_qs(urlsplit(browser.opened[-1]).query) if browser.opened else {}
    check(query.get("client_id") == ["qgis"] and query.get("redirect_uri") == [mock_server.REDIRECT_URI]
          and query.get("code_challenge_method") == ["S256"] and query.get("state"),
          "browser sign-in opens Mapflow's sign-in page for the QGIS client, with PKCE")
    check(session.state == "signing_in" and content.sign_in.cancel.isVisible()
          and "browser" in content.sign_in.browser.text(), "while it waits, the sign-in page says so and offers Cancel")
    shot(content, "01b-sign-in-waiting", QSize(400, 880))
    check(browse(f"{mock_server.REDIRECT_URI}?code=forged&state=wrong")[0] == 400 and session.state == "signing_in",
          "an answer with the wrong state is refused and the sign-in keeps waiting")
    check(browse("http://127.0.0.1:7070/favicon.ico")[0] == 404, "other requests to the listener get 404")
    status, back = browse(browser.opened[-1])
    check(status == 302 and back.startswith(mock_server.REDIRECT_URI + "?"),
          "Mapflow sends the browser back to http://127.0.0.1:7070/qgis with the code")
    status, landing = browse(back)
    check(status == 302 and landing == "https://app.mapflow.ai",
          f"QGIS takes the code and sends the browser on to app.mapflow.ai ({status} → {landing})")
    check(wait_until(lambda: session.state == "signed_in" and session.project is not None), "signs in through the "
                                                                                            "browser")
    check(session.method == "browser" and session.email == "me@example.com", "knows who signed in through the browser")
    check(state.pkce_checked == 1, "the code is exchanged with its PKCE verifier")
    bearer = [r[3].get("Authorization") for r in state.requests if r[1] == "/projects/default"][-1]
    check(bearer == "Bearer access-1", "API requests carry the access token")
    check(browse(back)[0] == 0, "the listener closes once the sign-in is done")
    check(auth.load_refresh_token(session.config) == "refresh-1" and not settings.value("mapflow_next/refresh_token")
          and settings.value("mapflow_next/auth_method") == "browser",
          "the sign-in is kept encrypted in the QGIS auth database, not in settings")
    check(session._refresh_timer.isActive() and session._refresh_timer.interval() == 240_000,
          "the access token is renewed a minute before it expires")
    session.refresh_sign_in()
    check(wait_until(lambda: session.http.bearer == "access-2")
          and auth.load_refresh_token(session.config) == "refresh-2",
          "renewal swaps in new tokens and keeps the new refresh token")
    with state.lock:
        state.access_tokens.discard("access-2")          # e.g. the laptop slept past the expiry
    session.refresh_status()
    check(wait_until(lambda: session.http.bearer == "access-3") and session.state == "signed_in",
          "a rejected access token is renewed once instead of signing out")

    # QGIS restart: the saved sign-in comes back without opening the browser
    opened = len(browser.opened)
    plugin.unload()
    plugin = classFactory(iface)
    plugin.initGui()
    plugin.toggle(True)
    content = plugin.dock.content
    session, processings, controller = plugin.services[1], plugin.services[2], plugin.controller
    processings._poll.setInterval(150)
    check(wait_until(lambda: session.state == "signed_in") and len(browser.opened) == opened
          and session.http.bearer == "access-4", "after a restart the browser sign-in is restored silently")
    session.sign_out()
    check(wait_until(lambda: session.state == "signed_out") and not auth.load_refresh_token(session.config),
          "signing out forgets the browser sign-in")

    # a saved sign-in that has run out: back to the sign-in page, no browser popping up
    auth.store_refresh_token(session.config, "refresh-expired")
    settings.setValue("mapflow_next/auth_method", "browser")
    session.restore()
    check(wait_until(lambda: session.state == "signed_out" and not auth.load_refresh_token(session.config))
          and len(browser.opened) == opened and not content.sign_in.error.isVisible(),
          "an expired saved sign-in quietly shows the sign-in page")

    # cancel while waiting for the browser frees the port
    content.sign_in.browserRequested.emit()
    content.sign_in.cancelRequested.emit()
    check(session.state == "signed_out" and not content.sign_in.cancel.isVisible()
          and browse(mock_server.REDIRECT_URI)[0] == 0, "Cancel stops waiting and closes the listener")

    # ---------- API token ----------
    # wrong token first: a friendly error, still signed out
    content.sign_in.tokenSubmitted.emit("not a token")
    check("doesn't look like" in content.sign_in.error.text.text(), "rejects a malformed token with a readable error")

    content.sign_in.tokenSubmitted.emit(mock_server.TOKEN)
    check(wait_until(lambda: session.state == "signed_in" and session.status is not None
                     and session.project is not None and len(session.projects) >= 2), "signs in with the API token")
    check(session.email == "me@example.com", "knows who is signed in")
    check(session.settings.value("auth_config_id"), "keeps only an auth config id in settings")
    check(not settings.value("mapflow_next/token"), "never stores the token in settings")
    auth_header = [r[3].get("Authorization") for r in state.requests if r[1] == "/projects/default"][-1]
    check(auth_header and auth_header.startswith("Basic "), "token goes through the QGIS auth database as Basic")
    check(wait_until(lambda: len(processings.items) == 2), "lists the project's processings")
    check(content.credits.text() == "1,240", "header shows the credit balance")
    shot(content, "02-start", QSize(400, 880))

    layer = old_town_layer()
    QgsProject.instance().addMapLayer(layer)
    iface.setActiveLayer(layer)
    iface.canvas.setDestinationCrs(layer.crs())
    iface.canvas.setExtent(QgsRectangle(37.58, 55.735, 37.63, 55.765))

    # model: a scenario sets model, options and zoom
    content.start.scenarioChosen.emit("heights")
    draft = controller.draft
    check(draft.model and draft.model.id == "wd-buildings", "scenario picks the Buildings model")
    check(draft.options == {"heights"}, "scenario switches on the heights option")
    # area: adopted from the active polygon layer
    check(draft.aoi and draft.aoi.name == "Old town" and 1.0 < draft.aoi.area_km2 < 1.5,
          f"area comes from the active polygon layer ({draft.aoi.area_km2 if draft.aoi else 0:.3f} km²)")
    # imagery: default provider at the scenario's zoom
    check(draft.imagery and draft.imagery.provider.name == "mapbox" and draft.imagery.zoom == 19,
          "imagery defaults to Mapbox at the scenario's zoom 19")
    check(wait_until(lambda: controller.server_cost == 70, 5), "asks Mapflow for the cost and shows it")
    cost_requests = [r for r in state.requests if r[1] == "/processing/cost/v2"]
    body = cost_requests[-1][2]
    check(body["params"] == {"sourceParams": {"dataProvider": {"providerName": "mapbox", "zoom": "19"}}}
          and body["wdId"] == "wd-buildings" and {"name": "heights", "enabled": True} in body["blocks"],
          "cost request carries the v2 processing payload")
    check(content.run.cost_value.text() == "70 credits", "cost bar shows the server's figure")
    check(content.run.run_button.isEnabled(), "Run is enabled once model, area and imagery are set")
    shot(content, "03-run", QSize(400, 980))
    content.resize(360, 980)
    wait_until(lambda: False, 0.2)
    shot(content, "03b-run-narrow", QSize(360, 980))
    from qgis.PyQt.QtWidgets import QScrollArea
    area = content.run.findChild(QScrollArea)
    area.verticalScrollBar().setValue(area.verticalScrollBar().maximum())
    shot(content, "03c-run-imagery", QSize(360, 980))
    area.verticalScrollBar().setValue(0)
    iface.window.resizeDocks([plugin.dock], [360], Qt.Orientation.Horizontal)
    wait_until(lambda: False, 0.2)
    scroll_body = content.run.model_card.parentWidget()
    check(scroll_body.width() <= area.viewport().width(),
          f"run form fits a narrow dock without sideways scrolling "
          f"({scroll_body.width()} ≤ {area.viewport().width()} px)")
    content.resize(400, 980)

    # ---------- review round: the run form ----------
    run = content.run
    check(content.tab_buttons[2].text() == "Imagery sources" and run.imagery_header.title.text() == "Imagery sources",
          "the imagery step and tab are called “Imagery sources”")
    rows, selected = controller._imagery_rows(session.status, True)
    check(rows[0].key == "mosaic" or not plugin.services[3].mosaics, "My imagery is listed first among the sources")
    check(all(17 <= z <= 21 for r in rows for z in r.zooms) and any(r.zooms for r in rows),
          "basemap zoom levels are limited to z17–z21")
    mapbox = next(r for r in rows if r.key == "provider:mapbox")
    check(mapbox.recommended_zoom == 19 and mapbox.zoom == 19, "the scenario's zoom (z19 for heights) is recommended "
                                                               "and preselected")
    zoom_combo = next(w for w in run._rows[[r.key for r in rows].index("provider:mapbox")].findChildren(QComboBox))
    check("z19 ★" in [zoom_combo.itemText(i) for i in range(zoom_combo.count())], "the recommended zoom is marked ★")
    eyes = [b for row in run._rows for b in row.findChildren(QToolButton) if b.toolTip() == "Preview on the map"]
    check(len(eyes) == 1 and eyes[0].parentWidget() is run._rows[[r.key for r in rows].index(selected)],
          "the preview is an eye on the selected source only")
    eyes[0].click()
    check(wait_until(lambda: QgsProject.instance().mapLayersByName("Mapbox Satellite · preview")),
          "the eye adds the source's preview to the map")
    check(isinstance(run.change_button, QToolButton) and not run.change_button.text(),
          "the scenario gallery opens from an icon, not a “Change” link")
    run.change_button.click()
    check(controller.gallery is not None and controller.gallery.isVisible(), "the icon opens the scenario gallery")
    controller.gallery.hide()

    # toggling an option leaves the form where it is
    iface.window.activateWindow()
    QApplication.setActiveWindow(iface.window)
    bar = run.scroll.verticalScrollBar()
    wait_until(lambda: False, 0.2)
    bar.setValue(max(1, bar.maximum() // 3))
    position = bar.value()
    switch = run._switches["classification"]
    switch.setFocus()
    QTest.mouseClick(switch, Qt.MouseButton.LeftButton)
    wait_until(lambda: False, 0.4)
    check("classification" in controller.draft.options and switch.isChecked(), "the option switch works")
    check(bar.value() == position and run._switches.get("classification") is switch,
          f"toggling an option doesn't scroll the form ({position} → {bar.value()})")
    QTest.mouseClick(switch, Qt.MouseButton.LeftButton)
    wait_until(lambda: "classification" not in controller.draft.options, 2)
    bar.setValue(0)

    # a selection in the area's layer: "2 polygons · 1 polygon selected"
    blocks = blocks_layer()
    QgsProject.instance().addMapLayer(blocks)
    run.layerChosen.emit(blocks.id())
    check("Blocks · 2 polygons" in run.area_meta.text() and "selected" not in run.area_meta.text(),
          f"the area names the layer and counts its polygons ({run.area_meta.text()})")
    blocks.selectByIds([next(blocks.getFeatures()).id()])
    check(wait_until(lambda: "2 polygons · 1 polygon selected" in run.area_meta.text(), 3)
          and controller.draft.aoi.area_km2 < 0.2,
          f"with one polygon selected the area is that polygon ({run.area_meta.text()})")
    shot(content, "03d-run-selection", QSize(400, 980))
    blocks.removeSelection()
    run.layerChosen.emit(layer.id())
    check(controller.draft.aoi.name == "Old town", "switching the area back to Old town")

    # change zoom: local estimate first, then the server's
    content.run.zoomChosen.emit("provider:mapbox", 18)
    check(controller.draft.imagery.zoom == 18, "zoom change applies to the draft")
    check(wait_until(lambda: controller.server_cost == 70, 5), "cost is re-checked after a change")

    # run
    before = len(state.processings)
    content.run.runRequested.emit()
    check(wait_until(lambda: len(state.processings) == before + 1, 5), "Run creates a processing")
    started = state.processings[-1]
    check(started["name"] == "Buildings · Old town", f"default name is model · area ({started['name']})")
    check(wait_until(lambda: content.current_tab() == 1, 3), "after Run the Processings tab opens")
    shot(content, "04-processings-running", QSize(400, 880))
    check(wait_until(lambda: plugin.services[4].in_map() and started["id"] in plugin.services[4].in_map(), 20),
          "finished results are added to the map automatically")
    result_layers = [layer_ for layer_ in QgsProject.instance().mapLayers().values()
                     if layer_.customProperty("mapflow_next/processing_id") == started["id"]]
    check(result_layers and result_layers[0].featureCount() == 5, "result layer has the 5 features")
    check(result_layers and result_layers[0].source().endswith(".gpkg|layername=Buildings · Old town"),
          "results are saved as a GeoPackage")
    group = QgsProject.instance().layerTreeRoot().findGroup("Mapflow")
    check(group is not None and group.findLayer(result_layers[0].id()) is not None, "results sit in the Mapflow group")
    check(any("ready" in (m[1] or "") for m in iface.bar.messages), "message bar announces the finished run")

    # rename: name and description
    seen = []

    def fill(dialog):
        dialog.name.setText("Old town heights")
        dialog.description.setPlainText("For the 3D city model")
    close_modal_later(seen, fill)
    content.processings.rename.emit(started["id"])

    def renames():
        return [r for r in state.requests if r[0] == "PUT" and r[1] == f"/processings/{started['id']}/v2"]
    check(seen == ["RenameDialog"] and wait_until(lambda: renames(), 5)
          and renames()[-1][2] == {"name": "Old town heights", "description": "For the 3D city model"},
          "Rename asks for a name and a description and saves both")
    check(wait_until(lambda: processings.get(started["id"]).name == "Old town heights", 5),
          "the renamed processing shows its new name")

    # results as vector tiles: the map goes to the results, not to the whole world
    from mapflow_next.services.results import FILES, TILES
    results = plugin.services[4]
    settings.setValue("mapflow_next/results_mode", TILES)      # as the Settings dialog does
    for item in results.layers.layers_for(started["id"]):
        QgsProject.instance().removeMapLayer(item.id())
    elsewhere = QgsRectangle(10, 10, 11, 11)
    iface.canvas.setExtent(elsewhere)
    results.add_to_map(processings.get(started["id"]))
    check(wait_until(lambda: started["id"] in results.in_map() and not results.is_busy(started["id"]), 5),
          "results load as vector tiles")
    tiles = [item for item in results.layers.layers_for(started["id"]) if isinstance(item, QgsVectorTileLayer)]
    view = iface.canvas.extent()
    check(tiles and view.width() < 0.1 and view.contains(QgsPointXY(37.605, 55.75)),
          f"vector tiles: the map shows the results' extent from their tilejson ({view.toString(3)})")
    iface.canvas.setExtent(elsewhere)
    results.add_to_map(processings.get("old-1"))         # its tilejson has no bounds
    check(wait_until(lambda: "old-1" in results.in_map() and not results.is_busy("old-1"), 5)
          and iface.canvas.extent().width() < 0.1 and iface.canvas.extent().contains(QgsPointXY(37.60025, 55.7502)),
          f"without tilejson bounds, the map shows the processing's area ({iface.canvas.extent().toString(3)})")
    iface.canvas.setExtent(elsewhere)
    content.processings.zoomTo.emit(started["id"])
    check(iface.canvas.extent().width() < 0.1 and iface.canvas.extent().contains(QgsPointXY(37.605, 55.75)),
          "“Show on map” goes back to the tile results")
    settings.setValue("mapflow_next/results_mode", FILES)
    wait_until(lambda: False, 0.4)
    shot(content, "05-processings-done", QSize(400, 880))

    # imagery search: the Area drop-down is the run's area
    content.go(2)
    imagery_page = content.imagery
    combo = imagery_page.layer_combo
    check(combo.isVisible() and combo.currentText() == "Old town" and combo.findText("Blocks") >= 0,
          f"Search has the Area drop-down, set to the run's area ({combo.currentText()})")
    index = combo.findText("Blocks")
    combo.setCurrentIndex(index)
    combo.activated.emit(index)
    check(controller.draft.aoi.name == "Blocks" and run.layer_combo.currentText() == "Blocks"
          and "2 polygons" in imagery_page.area_text.text(),
          f"choosing a layer in Search sets the area on Start too ({imagery_page.area_text.text()})")
    run.layerChosen.emit(layer.id())
    check(combo.currentText() == "Old town" and "1 polygon" in imagery_page.area_text.text(),
          "a change of area on Start shows in Search")
    check(imagery_page.cloud.height() >= 20 and imagery_page.cloud.sizeHint().height() >= 20,
          f"sliders are tall enough for their handle ({imagery_page.cloud.height()} px)")
    content.imagery._emit_search()
    check(wait_until(lambda: len(plugin.services[3].results) == 2, 5), "catalog search returns images")
    meta = [r for r in state.requests if r[1] == "/catalog/meta"][-1][2]
    check(meta["aoi"]["type"] in ("Polygon", "MultiPolygon") and meta["maxCloudCover"] == 20,
          "search sends the area and the filters")
    check(QgsProject.instance().mapLayersByName("Mapflow · search results"), "footprints are drawn on the map")
    check(imagery_page.date_from.calendarPopup() and "calendar" in content.styleSheet(),
          "dates have a calendar picker with a visible calendar icon")
    check(isinstance(imagery_page.cloud, QSlider) and isinstance(imagery_page.nadir, QSlider),
          "cloud cover and off-nadir are sliders")
    imagery_page.type_image.setChecked(False)
    imagery_page.cloud.setValue(35)
    imagery_page.search_button.click()
    check(wait_until(lambda: [r for r in state.requests
                              if r[1] == "/catalog/meta"][-1][2].get("productTypes") == ["MOSAIC"]
                     and not imagery_page.search_message.isVisible() and len(plugin.services[3].results) == 2, 5),
          "a mosaics-only search sends productTypes MOSAIC and succeeds")
    check([r for r in state.requests if r[1] == "/catalog/meta"][-1][2]["maxCloudCover"] == 35,
          "the cloud cover slider sets the filter")
    imagery_page.type_image.setChecked(True)
    shot(content, "06-imagery", QSize(400, 880))
    content.imagery.useImage.emit("img-1")
    check(controller.draft.imagery.kind == "catalog", "Use sets the search image as the imagery")
    check(controller.draft.payload("project-1")["params"]["sourceParams"]["imagerySearch"]["imageIds"] == ["img-1"],
          "the processing would run on that image")
    check(not imagery_page.clear_button.isHidden(), "search results have a Clear button")
    imagery_page.clear_button.click()
    check(not plugin.services[3].results and not QgsProject.instance().mapLayersByName("Mapflow · search results")
          and imagery_page.clear_button.isHidden() and imagery_page.results_title.isHidden()
          and imagery_page.results.count() == 0,
          "Clear empties the results and takes their footprints off the map")
    check(controller.draft.payload("project-1")["params"]["sourceParams"]["imagerySearch"]["imageIds"] == ["img-1"],
          "the image chosen before Clear stays chosen")
    wait_until(lambda: controller.server_cost == 70, 3)
    shot(content, "07-run-catalog", QSize(400, 980))

    # My imagery: image counts, no empty space, the collection picker
    content.go(2)
    content.imagery.show_tab(1)
    imagery_service = plugin.services[3]
    check(wait_until(lambda: imagery_service.get_mosaic("m-1").image_count == 3
                     and imagery_service.get_mosaic("m-2").image_count == 1, 5),
          "collections know how many images they have")
    wait_until(lambda: False, 0.3)
    texts = [w.text() for w in content.imagery.findChildren(QLabel) if w.isVisible()]
    check(any("3 images" in t for t in texts) and any("1 image ·" in t for t in texts),
          "My imagery shows the image count of each collection")
    check(content.imagery.scroll.verticalScrollBar().maximum() == 0,
          "My imagery is as tall as its list: no empty space below it")
    shot(content, "08-my-imagery", QSize(400, 880))
    content.imagery.useMosaic.emit("m-1")
    picker = controller.mosaic_picker
    check(picker is not None and wait_until(lambda: picker.isVisible() and len(picker._thumbs) == 3, 5),
          "using a collection of several images opens the picker with its images")
    ok = wait_until(lambda: len(picker.previews) == 3, 5)
    check(ok, "the picker shows each image's preview")
    shot(picker, "13-my-imagery-picker", QSize(820, 560))
    picker.chosen.emit("m-1", "m-1-i1")
    choice = controller.draft.imagery
    check(choice.kind == "my_imagery" and choice.image_ids == ["m-1-i1"]
          and controller.draft.payload("project-1")["params"]["sourceParams"]
          == {"myImagery": {"imageIds": ["m-1-i1"]}},
          "picking one image processes only that image (imageIds alone, as the API requires)")
    # the image's extent becomes the area, with a suggestion to change it
    run = content.run
    extent = controller.aoi_layer
    check(extent is not None and extent.name() == "Extent of centre.tif" and controller.draft.aoi.name == "centre.tif",
          "choosing an image makes its extent the area")
    check(run.area_hint.isVisible() and "whole extent of “centre.tif”" in run.area_hint_text.text.text()
          and set(run.area_hint_buttons) == {"draw", "edit_outline", "previous"}
          and "Old town" in run.area_hint_buttons["previous"].text(),
          "the form suggests drawing a smaller area, editing the outline, or going back to the previous area")
    wait_until(lambda: False, 0.1)
    run.scroll.ensureWidgetVisible(run.area_hint, 0, 40)
    shot(content, "16-my-imagery-extent", QSize(400, 980))
    iface.window.resizeDocks([plugin.dock], [360], Qt.Orientation.Horizontal)
    wait_until(lambda: False, 0.2)
    body = run.model_card.parentWidget()
    check(body.width() <= run.scroll.viewport().width(),
          f"with the suggestion showing, the form still fits a narrow dock "
          f"({body.width()} ≤ {run.scroll.viewport().width()} px)")
    run.area_hint_buttons["edit_outline"].click()
    check(extent.isEditable() and iface.activeLayer() is extent, "“Edit the outline” starts editing the extent")
    extent.rollBack()
    run.area_hint_buttons["previous"].click()
    draft = controller.draft
    check(draft.aoi.name == "Old town" and draft.coverage and draft.coverage.overlaps
          and draft.processed_area.area_km2 < draft.aoi.area_km2 * 0.5,
          f"an area partly over the image is clipped to it "
          f"({draft.processed_area.area_km2:.3f} of {draft.aoi.area_km2:.3f} km²)")
    check("inside the imagery" in run.area_meta.text(),
          f"the form says how much of the area is inside the imagery ({run.area_meta.text()})")
    check(draft.payload("project-1")["geometry"] == draft.processed_area.geometry,
          "only the part inside the image is sent")
    run.layerChosen.emit(blocks.id())
    check(controller.draft.coverage is not None and not controller.draft.coverage.overlaps
          and not run.run_button.isEnabled() and run.area_hint.isVisible()
          and "doesn't overlap “centre.tif”" in run.area_hint_text.text.text(),
          "an area outside the image shows a warning and Run is disabled")
    check(any("doesn't overlap" in i.text for i in controller.draft.issues(session.project, session.status)),
          "the run is blocked until the area overlaps the imagery")
    wait_until(lambda: False, 0.1)
    run.scroll.ensureWidgetVisible(run.area_hint, 0, 40)
    shot(content, "17-my-imagery-outside", QSize(400, 980))
    run.area_hint_buttons["imagery_extent"].click()
    check(controller.aoi_layer is extent and controller.draft.coverage.overlaps,
          "“Use the imagery extent” brings the extent back as the area")
    check(len(QgsProject.instance().mapLayersByName("Extent of centre.tif")) == 1,
          "the extent layer is reused, not duplicated")
    check(wait_until(lambda: controller.server_cost == 70, 5), "Mapflow accepts the cost request for one image")

    # the pencil by the name: name and describe the processing before it runs
    generated = run.name.text()
    named = []

    def name_it(dialog):
        named.append((dialog.windowTitle(), dialog.name.text()))
        dialog.name.setText("Centre roofs")
        dialog.description.setPlainText("Roofs inside the drone survey")
    close_modal_later(named, name_it)
    check(run.rename_button.isEnabled() and run.rename_button.isVisible(), "the pencil by the name is a button")
    run.rename_button.click()
    check(named == ["RenameDialog", ("Name this processing", generated)],
          f"the pencil opens the rename dialog with the generated name ({named})")
    check(run.name.text() == "Centre roofs" and controller.draft.description == "Roofs inside the drone survey"
          and "Roofs inside" in run.name.toolTip(),
          "the dialog's name and description go to the form")
    shot(content, "18-run-named", QSize(400, 520))
    before = len(state.processings)
    content.run.runRequested.emit()
    check(wait_until(lambda: len(state.processings) == before + 1, 5)
          and state.processings[-1]["params"]["sourceParams"] == {"myImagery": {"imageIds": ["m-1-i1"]}},
          "a processing on one image of a collection starts")
    posted = [r for r in state.requests if r[1] == "/processings/v2" and r[0] == "POST"][-1][2]
    check(posted["name"] == "Centre roofs" and posted["description"] == "Roofs inside the drone survey",
          "it runs with that name and description")
    check(wait_until(lambda: run.name.text() == generated and not controller.draft.description, 3),
          f"the next run gets a generated name again ({run.name.text()})")
    one_image_run = state.processings[-1]["id"]
    extent_area = controller.draft.aoi.area_km2
    starts = [r for r in state.requests if r[1] == "/processings/v2" and r[0] == "POST"]
    check(starts[-1][2]["meta"] == {"source-app": "qgis", "source": "my imagery", "version": "4.0.0"},
          "processings carry the plugin's meta, as the current plugin sends it")
    content.go(2)
    content.imagery.show_tab(1)
    check(not picker.isVisible() and "centre.tif" in content.run._rows[0].meta.text(),
          "the run form shows the chosen image")
    pick_button = next(b for b in content.run._rows[0].findChildren(QPushButton) if b.text() == "Choose…")
    pick_button.click()
    check(picker.isVisible() and picker.current == "m-1", "“Choose…” on My imagery opens the picker at the chosen "
                                                          "collection")
    picker.chosen.emit("m-1", "")
    check(controller.draft.imagery.image_ids == [] and controller.draft.imagery.mosaic_id == "m-1",
          "“Use the whole collection” processes the whole collection")
    check(controller.aoi_layer.name() == "Extent of Drone survey March"
          and abs(controller.draft.aoi.area_km2 - 3 * extent_area) < 0.02 * 3 * extent_area,
          "the whole collection's extent (all its images) becomes the area")
    content.imagery.useMosaic.emit("m-2")
    check(controller.draft.imagery.mosaic_id == "m-2" and not picker.isVisible(),
          "a single-image collection is used directly, without the picker")
    check(wait_until(lambda: controller.aoi_layer is not None and controller.aoi_layer.name() == "Extent of Beirut", 5),
          "a collection chosen in My imagery sets the area to its extent")

    # gallery
    controller.open_gallery("")
    gallery = controller.gallery
    shot(gallery, "09-gallery", QSize(1180, 800))
    gallery.open_scenario("veg-height")
    shot(gallery, "10-gallery-detail", QSize(1180, 800))
    gallery.scenarioChosen.emit("roads")
    check(controller.draft.model.id == "wd-roads", "choosing in the gallery sets the run form")

    # whole window
    shot(iface.window, "11-qgis-window", QSize(1500, 950))

    # run again on one image: the API keeps only the image id; its collection is looked up
    check(wait_until(lambda: processings.get(one_image_run) is not None, 5), "the one-image processing is listed")
    plugin.services[3].images.clear()
    controller.draft.imagery = None
    content.processings.duplicate.emit(one_image_run)
    check(wait_until(lambda: controller.draft.imagery is not None and controller.draft.imagery.kind == "my_imagery"
                     and controller.draft.imagery.mosaic_id == "m-1"
                     and controller.draft.imagery.image_ids == ["m-1-i1"], 5),
          "“Run again” on one image finds its collection and picks the same image")

    # duplicate → run again
    content.processings.duplicate.emit("old-1")
    check(wait_until(lambda: controller.draft.aoi is not None and controller.draft.aoi.name.startswith("Area ·"), 5),
          "Run again restores the processing's area as a layer")

    # ---------- projects window ----------
    with state.lock:
        for n in range(70):
            item = fixtures.processing_json(f"h-{n:02d}", "OK", 100, name=f"Harbor run {n:02d}")
            state.processings.insert(0, dict(item, projectId="project-2"))
    content.project_button.click()
    projects_window = controller.projects_dialog
    check(projects_window is not None and wait_until(lambda: projects_window.isVisible()
                                                     and len(projects_window.results) == 24, 5),
          "the project button opens the projects window with the first page")
    check(len(projects_window.tiles) == 24 and wait_until(lambda: projects_window.more_button.isVisible(), 2),
          "projects show as tiles, with “Show more”")
    harbor = next(t for t in projects_window.tiles if t.project.id == "project-2")
    pills = [w.text() for w in harbor.findChildren(QLabel)]
    check(any(t.startswith("Shared · 3 people") for t in pills) and any("12 done" in t for t in pills)
          and any("1 failed" in t for t in pills) and any("Port and storage" in t for t in pills),
          "a tile shows the description, the numbers and that the project is shared")
    shot(projects_window, "14-projects", QSize(900, 640))
    projects_window.more_button.click()
    check(wait_until(lambda: len(projects_window.results) == 45, 5), "“Show more” loads the next page")
    pin_target = next(t for t in projects_window.tiles if t.project.id == "project-30")
    pin_target.pin_button.click()
    check(projects_window.tiles[0].project.id == "project-30" and controller.pinned_projects() == ["project-30"],
          "a pinned project moves to the top and stays pinned")
    projects_window.search.setText("harb")
    check(wait_until(lambda: [p.id for p in projects_window.results] == ["project-2"], 5)
          and [r for r in state.requests if r[1] == "/projects/page"][-1][2].get("filter") == "harb",
          "searching filters projects by name on the server")
    links.opened.clear()
    projects_window.tiles[0].share_button.click()
    check(links.opened == [config.PROJECTS_URL], "the share icon opens sharing in Mapflow Web")
    team = [b for b in projects_window.findChildren(QPushButton) if b.text().startswith("Team")]
    check(team, "the projects window links to the team page in Mapflow Web")
    shot(projects_window, "14b-projects-search", QSize(900, 640))
    projects_window.tiles[0].clicked.emit("project-2")
    check(not projects_window.isVisible() and wait_until(lambda: session.project.id == "project-2", 5),
          "clicking a tile opens that project")
    check(content.processings.empty_text.text() == "Loading processings…" or processings.items,
          "while the list loads it says so (not “Start mapping”)")
    check("(shared)" in content.project_button.toolTip(), "the header marks a shared project")
    content.go(1)
    check(wait_until(lambda: len(processings.items) == 30 and processings.total == 70, 5),
          "the first page of 30 processings loads")
    check(content.processings.more_button is not None and "30 of 70" in content.processings.more_button.text(),
          "“Show more” says how many are left")
    content.processings.more_button.click()
    check(wait_until(lambda: len(processings.items) == 60, 5), "the next page appends 30 more")
    content.processings.more_button.click()
    check(wait_until(lambda: len(processings.items) == 70 and content.processings.more_button is None, 5),
          "the last page loads and “Show more” goes away")
    check(len({p.id for p in processings.items}) == 70, "no processing is listed twice")
    shot(content, "15-processings-paged", QSize(400, 880))
    processings.refresh()
    check(wait_until(lambda: not processings._loading, 5) and len(processings.items) == 70,
          "polling keeps the older pages in the list")

    # ---------- account menu: Settings and Sign out ----------
    menu_actions = {a.text(): a for a in content.account_menu.actions()}
    seen = []
    close_modal_later(seen)
    menu_actions["Settings…"].triggered.emit(False)        # some PyQt builds pass `checked` along
    check(seen == ["SettingsDialog"], "Settings… in the account menu opens the settings")
    check(menu_actions["Settings…"].menuRole() == QAction.MenuRole.NoRole, "macOS keeps Settings… in the account menu")

    # sign out
    menu_actions["Sign out"].triggered.emit(False)
    check(wait_until(lambda: content.stack.currentIndex() == 0, 3), "sign-out returns to the sign-in page")
    check(not session.settings.value("auth_config_id"), "sign-out forgets the sign-in")

    # dark theme renders too
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#2b2b2b"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#eeeeee"))
    QApplication.setPalette(palette)
    from mapflow_next.ui.dock import DockContent
    from mapflow_next.core.scenarios import Catalogue
    from mapflow_next.config import RESOURCES
    dark = DockContent(Catalogue.load(RESOURCES / "scenarios"))
    dark.show_signed_in()
    dark.set_project(session.project)
    dark.set_credits("1,240", "")
    shot(dark, "12-dark-start", QSize(400, 880))

    plugin.unload()
    check(not iface.toolbar_actions, "unload removes the toolbar button")
    server.shutdown()
    failed = [text for ok, text in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    code = main()
    os._exit(code)
