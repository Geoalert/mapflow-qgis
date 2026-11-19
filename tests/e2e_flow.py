"""End to end in real QGIS (offscreen) against the mock API: sign in → scenario → area → imagery → run →
results on the map, plus imagery search, the gallery and sign-out. Saves screenshots when given a folder.

    python3 -m tests.e2e_flow [screenshot-folder]
"""
import json
import os
import sys
import tempfile
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .qgis_env import FakeIface, start_qgis, wait_until

APP = start_qgis()

from qgis.PyQt.QtCore import QObject, QSize, Qt, QTimer, QUrl, pyqtSlot  # noqa: E402
from qgis.PyQt.QtGui import QDesktopServices  # noqa: E402
from qgis.PyQt.QtTest import QTest  # noqa: E402
from qgis.PyQt.QtWidgets import QAction, QSlider, QToolBar, QToolButton  # noqa: E402
from qgis.PyQt.QtGui import QColor, QPalette  # noqa: E402
from qgis.PyQt.QtWidgets import QApplication, QComboBox, QLabel, QPushButton, QWidget  # noqa: E402
from qgis.core import (Qgis, QgsFeature, QgsGeometry, QgsPointXY, QgsProject, QgsRectangle, QgsSettings,  # noqa: E402
                       QgsVectorLayer, QgsVectorTileLayer)

from . import fixtures, mock_server  # noqa: E402
from mapflow_next import config  # noqa: E402
from mapflow_next.core.failures import LOAD  # noqa: E402
from mapflow_next.ui.imagery_page import MINE  # noqa: E402

SHOTS = Path(sys.argv[1]) if len(sys.argv) > 1 else None
CHECKS = []
RUN_STARTED = time.time()


def check(condition, text):
    CHECKS.append((bool(condition), text))
    print(("PASS " if condition else "FAIL ") + text, flush=True)
    return condition


def expect_critical(iface, fragment, text, count=None):
    """Declare that the check before this call caused Critical messages containing `fragment`: `count` of them,
    or any number but at least one. A declaration that matches too few messages fails, so it can't go stale."""
    marked = iface.bar.ledger.expect(fragment)
    return check(marked == count if count is not None else marked > 0, f"{text} ({marked} messages)")


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


def make_geotiff(name, bands=3, epsg=4326, data_type=None, folder=None):
    """A tiny georeferenced GeoTIFF."""
    from osgeo import gdal, osr
    folder = folder or tempfile.mkdtemp()
    path = str(Path(folder) / name)
    raster = gdal.GetDriverByName("GTiff").Create(path, 4, 4, bands, data_type or gdal.GDT_Byte)
    raster.SetGeoTransform((37.6, 0.0001, 0, 55.75, 0, -0.0001))
    if epsg:
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(epsg)
        raster.SetProjection(srs.ExportToWkt())
    raster.FlushCache()
    raster = None
    return path


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


def check_credentials_origin(iface, plugin, state, api_url):
    """spec/002_api.md § Authentication: credentials go only to the API's own scheme, host and port, on a first
    request and on every redirect hop. A second mock server (same host, another port) plays another origin."""
    from mapflow_next.api.client import MapflowApi
    http = plugin.services[0]
    other_server, other, other_url = mock_server.start()
    unauthorized = []

    def on_unauthorized():
        unauthorized.append(True)
    http.unauthorized.connect(on_unauthorized)
    seen = len(iface.bar.ledger.unexpected())

    def header(requests, path):
        """The Authorization header of the last request for `path` ("" when it had none), or None if none came."""
        matching = [r for r in requests if r[1] == path]
        if not matching:
            return None
        return next((v for k, v in matching[-1][3].items() if k.lower() == "authorization"), "")

    def fetch(path, parse="bytes", **kwargs):
        got = {}
        http.get(path, parse=parse, on_success=lambda value: got.setdefault("ok", value),
                 on_error=lambda error: got.setdefault("error", error), **kwargs)
        wait_until(lambda: got, 10)
        return got

    def run(label, expect_prefix):
        before_api, before_other = len(state.requests), len(other.requests)
        got = fetch("user/status", parse="json")
        sent = header(state.requests[before_api:], "/user/status")
        check("ok" in got and (sent or "").startswith(expect_prefix),
              f"{label}: a request to the API origin carries the {expect_prefix.strip()} credentials")
        got = fetch(f"{other_url}/open/preview.png")
        check(got.get("ok") == mock_server.PNG and header(other.requests[before_other:], "/open/preview.png") == "",
              f"{label}: a picture of another port loads and its request has no Authorization header")
        previews = {}
        MapflowApi(http).preview(f"{other_url}/open/preview.png", lambda data: previews.setdefault("ok", data),
                                 lambda error: previews.setdefault("error", error))
        wait_until(lambda: previews, 10)
        check(previews.get("ok") == mock_server.PNG, f"{label}: MapflowApi.preview of another origin loads")
        before_api, before_other = len(state.requests), len(other.requests)
        target = f"{other_url}/open/preview.png"
        got = fetch(f"redirect?to={target}")
        check(got.get("ok") == mock_server.PNG and header(state.requests[before_api:], "/redirect") != ""
              and header(other.requests[before_other:], "/open/preview.png") == "",
              f"{label}: a redirect from the API to another origin loads the picture without the credentials "
              f"({got.get('error')})")
        got = fetch("redirect?to=/rest/user/status", parse="json")
        check("ok" in got and header(state.requests, "/user/status").startswith(expect_prefix),
              f"{label}: a redirect to a path of the API origin keeps the credentials ({got.get('error')})")

    saved = (http.bearer, http.auth_config_id)
    try:
        run("API token", "Basic")
        token = "access-origin-check"
        state.access_tokens.add(token)
        http.bearer = token
        run("browser sign-in", "Bearer")
        http.bearer = None

        # the sink survives a redirect, and the redirect's own body does not reach the file
        target_file = str(Path(tempfile.mkdtemp()) / "picture.png")
        done = {}
        http.download(f"redirect?to={other_url}/open/preview.png", target_file,
                      on_success=lambda path: done.setdefault("ok", path),
                      on_error=lambda error: done.setdefault("error", error))
        wait_until(lambda: done, 10)
        check("ok" in done and Path(target_file).read_bytes() == mock_server.PNG,
              f"a download that is redirected to another origin writes the picture ({done.get('error')})")

        # a redirect loop ends in one error
        errors, answers = [], []
        http.get("redirect", parse="bytes", on_success=answers.append, on_error=errors.append)
        wait_until(lambda: errors or answers, 10)
        wait_until(lambda: False, 0.3)
        check(not answers and len(errors) == 1 and errors[0].kind == "server",
              f"a redirect loop ends in one error of kind server ({[e.kind for e in errors]})")

        # a write is never redirected
        before_other = len(other.requests)
        errors, answers = [], []
        http.post(f"redirect?to={other_url}/open/preview.png", {"a": 1}, on_success=answers.append,
                  on_error=errors.append)
        wait_until(lambda: errors or answers, 10)
        wait_until(lambda: False, 0.3)
        check(not answers and len(errors) == 1 and errors[0].kind == "server"
              and len(other.requests) == before_other,
              f"a redirect of a POST is an error and nothing is sent to the target ({[e.kind for e in errors]})")
    finally:
        http.bearer, http.auth_config_id = saved
        http.unauthorized.disconnect(on_unauthorized)
        other_server.shutdown()
    check(not unauthorized, "no request of these checks ended the sign-in")
    check(len(iface.bar.ledger.unexpected()) == seen, "…and none of them raised a Critical message")


def check_the_guard(iface, plugin, api_url, settings):
    """spec/006 § The guard: `Http` tells a body that is not JSON from a callback that raises, a request ends
    in one outcome, a result that cannot be placed leaves no "loading" flag, and a timer reaches the reporter."""
    from mapflow_next.core.guard import guarded
    from mapflow_next.core.models import Processing
    from mapflow_next.services.results import FILES, TILES
    http, results = plugin.services[0], plugin.services[4]
    ledger = iface.bar.ledger
    unhandled = []                                  # what `Http` reports when no caller took the error
    http.failed.connect(unhandled.append)

    def raiser(_result=None):
        raise ValueError("boom")

    # an on_success that raises: logged with its traceback, reported, then on_error runs once
    errors, seen = [], len(ledger.unexpected())
    http.get("user/status", on_success=raiser, on_error=errors.append)
    check(wait_until(lambda: errors, 5), "a request whose on_success raises ends in on_error")
    wait_until(lambda: False, 0.3)
    lines = ledger.unexpected()[seen:]
    check(len(errors) == 1 and errors[0].kind == "plugin"
          and "Unexpected response from Mapflow" not in errors[0].message,
          f"…once, and a ValueError of the callback is not shown as a bad answer ({[e.message for e in errors]})")
    check(len(lines) == 2 and lines[0].startswith("log: ") and "Traceback" in lines[0]
          and all(part in lines[0] for part in ("ValueError: boom", "raiser", "user/status"))
          and lines[1].startswith("bar: Something went wrong: boom"),
          f"…the log has the traceback and the request, then the bar has the Critical line ({len(lines)} lines)")
    expect_critical(iface, "boom", "the guard's lines of an on_success that raises", count=2)
    check(not unhandled, "…and Http.failed stays silent: the caller's on_error took it")

    # no on_error: the guard has told the user once, and nothing says it again
    http.get("user/status", on_success=raiser)
    wait_until(lambda: len(ledger.unexpected()) > 0, 5)
    wait_until(lambda: False, 0.3)
    check(not unhandled, "an on_success that raises, with no on_error, is reported once and Http.failed stays silent")
    expect_critical(iface, "boom", "the guard's lines of an on_success that raises without on_error", count=2)

    # an on_error that raises: reported, and nothing runs again
    calls = []

    def bad_error(error):
        calls.append(error.kind)
        raise ValueError("on_error boom")
    http.get("projects/missing", on_success=raiser, on_error=bad_error)
    check(wait_until(lambda: calls, 5), "a failed request reaches on_error")
    wait_until(lambda: False, 0.3)
    check(calls == ["not_found"] and not unhandled, f"an on_error that raises runs once ({calls})")
    expect_critical(iface, "on_error boom", "the guard's lines of an on_error that raises", count=2)

    # a body that is not the promised JSON is the expected failure
    answered, errors, seen = [], [], len(ledger.unexpected())
    http.get("not-json", on_success=answered.append, on_error=errors.append)
    check(wait_until(lambda: errors, 5), "a body that is not JSON ends in on_error")
    wait_until(lambda: False, 0.3)
    check(not answered and len(errors) == 1 and errors[0].kind == "server"
          and errors[0].message.startswith("Unexpected response from Mapflow"),
          f"…once, as “Unexpected response from Mapflow” ({[e.message for e in errors]})")
    check(len(ledger.unexpected()) == seen, "…and it is no failure of the plugin: nothing Critical")
    texts = []
    http.get("not-json", parse="text", on_success=texts.append)
    check(wait_until(lambda: texts, 5) and texts == ["<html>maintenance</html>"],
          "the same body is fine when the caller asked for text")

    # a result whose bounds cannot be transformed leaves no "loading" flag
    def done_processing(name):
        body = fixtures.processing_json(name, "OK", 100, name="Forest · odd")
        body["vectorLayer"]["tileJsonUrl"] = f"{api_url}/tiles/{name}.json"
        return Processing.from_api(body)

    failures = []
    results.failed.connect(lambda pid, text: failures.append((pid, text)))
    odd = done_processing(mock_server.ODD_BOUNDS_ID)
    seen = len(ledger.unexpected())
    settings.setValue("mapflow_next/results_mode", TILES)
    try:
        results.add_to_map(odd)
        check(wait_until(lambda: odd.id in results.in_map() and not results.is_busy(odd.id), 5)
              and not failures and len(ledger.unexpected()) == seen,
              "bounds that cannot be transformed: the results still load, the processing is not left loading")
    finally:
        settings.setValue("mapflow_next/results_mode", FILES)
    for layer in results.layers.layers_for(odd.id):
        QgsProject.instance().removeMapLayer(layer.id())

    # a timer reaches the reporter that the plugin installed
    QTimer.singleShot(0, guarded(lambda: raiser()))
    wait_until(lambda: False, 0.1)
    expect_critical(iface, "boom", "the guard's lines of a timer callback that raises", count=2)


def files_under(folder):
    """Every file below `folder`, `.downloads/` included, as paths relative to it."""
    return sorted(str(path.relative_to(folder)) for path in Path(folder).rglob("*") if path.is_file())


def processing_done(name):
    from mapflow_next.core.models import Processing
    return Processing.from_api(fixtures.processing_json(name, "OK", 100, name=f"Forest · {name}"))


def waiting_conversion(started, stopped):
    """A stand-in for `conversion.convert_geojson` that writes some bytes to the work file and then waits for the
    cancel, as a long write does. `started` gets the job the moment the worker is inside, `stopped` when it leaves."""
    def waiting(job, is_canceled, feedback, *rest):
        job.work.parent.mkdir(parents=True, exist_ok=True)
        job.work.write_bytes(b"partial")
        started.append(job)
        while not is_canceled():
            time.sleep(0.02)
        stopped.append(job)
    return waiting


def check_result_conversion(iface, plugin):
    """spec/005 § QGIS Application and spec/006: a result is converted in a `QgsTask`. The GUI thread keeps turning
    meanwhile; a failed, cancelled or interrupted conversion shows a message (or, on sign-out and unload, none), clears
    the processing's "loading" flag and leaves no file in the output folder. `convert_geojson` is replaced for the
    duration of a scenario and put back in a `finally`."""
    import errno
    import mapflow_next.qgis_bridge.conversion as conversion
    results = plugin.services[4]
    ledger = iface.bar.ledger
    out_dir = results.output_dir
    original = conversion.convert_geojson
    failures, loaded = [], []

    def on_failed(processing_id, text):
        failures.append((processing_id, text, threading.current_thread() is threading.main_thread()))
    results.failed.connect(on_failed)
    results.loaded.connect(lambda processing_id, _ids: loaded.append(processing_id))

    def scenario(name, seam):
        """Start the results of a new processing with `seam` in place of the conversion."""
        processing = processing_done(name)
        failures.clear()
        conversion.convert_geojson = seam
        results.add_to_map(processing)
        return processing

    # an exception in the worker: reported once, on the GUI thread, through the guard
    before = files_under(out_dir)

    def disk_error(job, is_canceled, feedback, *rest):
        job.work.parent.mkdir(parents=True, exist_ok=True)
        job.work.write_bytes(b"partial")
        raise RuntimeError("disk")
    try:
        broken = scenario("conv-broken", disk_error)
        check(wait_until(lambda: len(failures) >= 1, 5), "an exception while converting the results reaches the user")
        wait_until(lambda: False, 0.3)
    finally:
        conversion.convert_geojson = original
    check(conversion.convert_geojson is original and not results.is_busy(broken.id) and len(failures) == 1
          and failures[0][1] == "The results could not be added to the map. Details are in the Log Messages panel."
          and failures[0][2],
          f"…the processing is not left loading, and it fails once, on the GUI thread ({failures})")
    check(not results.layers.layers_for(broken.id) and files_under(out_dir) == before,
          f"…no layer, and no file stays in the output folder ({sorted(set(files_under(out_dir)) - set(before))})")
    expect_critical(iface, "disk", "the guard's lines of an exception while converting", count=2)

    # an error of the disk is expected: a message that names the folder, and no report
    def disk_full(job, is_canceled, feedback, *rest):
        job.work.parent.mkdir(parents=True, exist_ok=True)
        job.work.write_bytes(b"partial")
        raise OSError(errno.ENOSPC, "No space left on device")
    seen = len(ledger.unexpected())
    try:
        full = scenario("conv-full", disk_full)
        check(wait_until(lambda: len(failures) >= 1, 5), "a disk error while converting reaches the user")
        wait_until(lambda: False, 0.3)
    finally:
        conversion.convert_geojson = original
    check(len(failures) == 1 and str(out_dir) in failures[0][1] and "No space left on device" in failures[0][1]
          and "Settings" in failures[0][1] and not results.is_busy(full.id),
          f"…the message names the folder and the cause, and the flag is cleared ({failures})")
    check(len(ledger.unexpected()) == seen and files_under(out_dir) == before,
          "…nothing is reported as a failure of the plugin, and no file stays")

    # a result without a feature
    def empty(job, is_canceled, feedback, *rest):
        return conversion.Converted(job.target, [], "gpkg")
    try:
        nothing = scenario("conv-empty", empty)
        check(wait_until(lambda: len(failures) >= 1, 5), "a result without features reaches the user")
    finally:
        conversion.convert_geojson = original
    check(failures[0][1] == "The processing returned no features." and not results.is_busy(nothing.id)
          and files_under(out_dir) == before, f"…as “no features”, the flag cleared, no file left ({failures})")

    # the user cancels in the Tasks panel: QGIS keeps answering, and the work file goes
    started, stopped = [], []
    try:
        slow = scenario("conv-cancel", waiting_conversion(started, stopped))
        check(wait_until(lambda: started, 5), "the conversion runs in a worker")
        task = results._tasks.get(slow.id)
        ticks = []
        timer = QTimer()
        timer.timeout.connect(lambda: ticks.append(1))
        timer.start(20)
        check(task is not None, "…and the task is the processing's")
        wait_until(lambda: False, 0.3)
        timer.stop()
        check(results.is_busy(slow.id) and len(ticks) >= 3 and Path(started[0].work).exists(),
              f"…while it runs the processing is loading and the GUI loop turns ({len(ticks)} ticks)")
        task.cancel()
        check(wait_until(lambda: len(failures) >= 1, 5), "cancelling the task reaches the user")
    finally:
        conversion.convert_geojson = original
    check(failures[0][1] == "Converting “Forest · conv-cancel” was cancelled." and not results.is_busy(slow.id)
          and slow.id not in results._tasks and stopped, f"…as “was cancelled”, the flag cleared ({failures})")
    check(files_under(out_dir) == before and not results.layers.layers_for(slow.id),
          "…and neither the work file nor the download stays, and no layer appears")

    # sign-out: the flag is cleared at once, the task stops, nothing is said, no file stays
    started.clear()
    stopped.clear()
    try:
        slow = scenario("conv-signout", waiting_conversion(started, stopped))
        check(wait_until(lambda: started, 5), "a conversion runs when the user signs out")
        results.reset()                    # what the controller calls when the session ends
        check(not results.is_busy(slow.id) and not results._tasks, "sign-out clears the flag and forgets the task")
        check(wait_until(lambda: stopped, 5) and wait_until(lambda: files_under(out_dir) == before, 5),
              f"…the worker stops and no file stays ({sorted(set(files_under(out_dir)) - set(before))})")
        wait_until(lambda: False, 0.3)
        check(not failures and not results.is_busy(slow.id), "…and the stopped task says nothing")
    finally:
        conversion.convert_geojson = original

    # the same processing converts again after that: the work file of the old task is not in the way
    again = processing_done("conv-signout")
    loaded.clear()
    results.add_to_map(again)
    check(wait_until(lambda: again.id in loaded, 10) and not results.is_busy(again.id),
          "the results of the same processing load after the sign-out")
    check(sum(f.endswith(".gpkg") for f in files_under(out_dir)) == sum(f.endswith(".gpkg") for f in before) + 1
          and not [f for f in files_under(out_dir) if f.startswith(".downloads")],
          "…as one GeoPackage, and nothing stays in .downloads")
    for layer in results.layers.layers_for(again.id):
        QgsProject.instance().removeMapLayer(layer.id())
    results.failed.disconnect(on_failed)


def check_failed_requests(iface, plugin, state):
    """spec/005 § Failed requests: the rule follows what triggered the request. A user's request shows its failure
    at once; a one-off load tells once and clears what it marked as pending; a timer's request drops a transient
    failure (logged) until POLL_FAILURES_BEFORE_ALERT in a row, and stops on a permanent one; a list that failed
    never reads as empty; a project that answers 403 or 404 is gone; nothing that changes state is sent again.
    Everything the function changes is restored, so the rest of the flow runs as before."""
    import re
    import mapflow_next.api.http as http_module
    from datetime import date
    from mapflow_next.core.draft import ImageryChoice
    from mapflow_next.core.failures import POLL, USER, is_transient
    from mapflow_next.ui.projects_dialog import ProjectsDialog
    from qgis.core import QgsApplication
    session, processings, imagery = plugin.services[1], plugin.services[2], plugin.services[3]
    controller, content = plugin.controller, plugin.dock.content
    threshold = config.POLL_FAILURES_BEFORE_ALERT
    warn = Qgis.MessageLevel.Warning
    page = r"/projects/project-2/processings/v2/page"
    saved_project = session.project.id

    def lines(since):
        return [text for level, text in iface.bar.messages[since:] if level == warn]

    def requests(method, pattern):
        return len([r for r in state.requests if r[0] == method and re.search(pattern, r[1])])

    def settle(seconds=0.4):
        wait_until(lambda: False, seconds)

    logged = []
    log = QgsApplication.messageLog()
    if hasattr(log, "messageReceivedWithFormat"):
        log.messageReceivedWithFormat.connect(lambda message, tag, level, _format: logged.append(message))
    else:
        log.messageReceived.connect(lambda message, tag, level: logged.append(message))

    def ready():
        """The project's list answered, nothing in flight, no failure left over."""
        state.heal()
        processings.refresh(USER)
        return wait_until(lambda: processings.loaded and not processings.load_failed and not processings._loading, 5)

    check(ready() and processings._poll_failures.count == 0, "the failure checks start from a loaded project list")
    processings._poll.setInterval(50)
    session._timer.setInterval(50)
    session._timer.stop()                               # started again by the checks that need it

    # ---------- USER: shown at once ----------
    for what in (503, 400):
        state.heal()
        state.fail("POST", "/catalog/meta", what)
        before, asked = len(iface.bar.messages), requests("POST", "/catalog/meta")
        imagery.search({"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
                       date(2026, 1, 1), date(2026, 2, 1), None, None)
        check(wait_until(lambda: content.imagery.search_message.text.text() != "", 5),
              f"USER: a failed catalog search ({what}) shows its error next to the search")
        settle(0.5)
        check(requests("POST", "/catalog/meta") == asked + 1, f"…and the search is not sent again ({what})")
        content.imagery.show_search_message("")
    state.heal()
    for what in (503, 400):
        state.fail("POST", page, what, times=1)
        before, asked = len(iface.bar.messages), requests("POST", page)
        content.processings.refresh_button.click()
        check(wait_until(lambda: len(lines(before)) == 1, 5) and processings.load_failed,
              f"USER: Refresh on a list that fails ({what}) says so at once, once ({lines(before)})")
        check(wait_until(lambda: not content.processings.refreshing, 3), "…and the Refresh button comes back")
        settle(0.5)
        check(requests("POST", page) == asked + (2 if what == 503 else 1) and len(lines(before)) == 1,
              f"…a transient failure is asked again by the poll, a permanent one is not ({what})")
        ready()
    state.many_mosaics = 60
    imagery.forget_mosaics()
    imagery.load_mosaics()
    check(wait_until(lambda: imagery.mosaics_loaded and imagery.has_more_mosaics, 5), "a long listing has “Show more”")
    state.fail("GET", r"/rasters/mosaic/page", 503, times=1)
    before = len(iface.bar.messages)
    imagery.load_more_mosaics()
    check(wait_until(lambda: lines(before) and not imagery.loading_mosaics, 5)
          and "More collections didn't load" in lines(before)[0] and len(lines(before)) == 1
          and content.imagery.more_mosaics.isEnabled(),
          "USER: “Show more” of collections that fails says so and comes back")
    state.heal()
    state.many_mosaics = 0
    imagery.forget_mosaics()
    imagery.load_mosaics()
    wait_until(lambda: imagery.mosaics_loaded, 5)

    # ---------- LOAD: once, and nothing is left pending ----------
    for what in (503, 403):
        state.heal()
        state.fail("GET", r"/rasters/mosaic/page", what)
        imagery.forget_mosaics()
        controller._choose_uploaded, controller._select_in_picker = "an upload", "a new collection"
        before = len(iface.bar.messages)
        imagery.load_mosaics()
        check(wait_until(lambda: imagery.mosaics_failed and not imagery.loading_mosaics, 5),
              f"LOAD: the listing fails ({what})")
        settle()
        check(len(lines(before)) == 1 and "Collections didn't load" in lines(before)[0],
              f"…and the message bar says so once ({lines(before)})")
        check(controller._choose_uploaded is None and controller._select_in_picker is None,
              "…and what waited for the listing is cleared")
        title = content.imagery.mosaics_title.text()
        check("No collections yet" not in title and "didn't load" in title,
              f"…and the page does not look empty ({title!r})")
    state.heal()
    imagery.load_mosaics()
    check(wait_until(lambda: imagery.mosaics_loaded and not imagery.mosaics_failed and imagery.mosaics, 5)
          and content.imagery.mosaics_title.text().startswith("Collections ·"),
          "…and the next good answer brings it back")

    mosaic = imagery.mosaics[0]
    mosaic.image_count = None
    imagery.images.pop(mosaic.id, None)
    state.fail("GET", rf"/rasters/mosaic/{mosaic.id}/image", 503)
    before, asked = len(iface.bar.messages), requests("GET", rf"/rasters/mosaic/{mosaic.id}/image")
    controller.use_mosaic(mosaic.id)
    check(controller._use_pending == mosaic.id, "a click that needs an image list waits for it")
    check(wait_until(lambda: controller._use_pending is None and not imagery._images_loading, 5)
          and len(lines(before)) == 1 and "images didn't load" in lines(before)[0],
          f"LOAD: …the list fails: nothing waits for it any more, and one line says so ({lines(before)})")
    choice_before = controller.draft.imagery
    controller.draft.imagery = ImageryChoice.from_mosaic(mosaic.id, mosaic.name)
    before = len(iface.bar.messages)
    sent, footprint = requests("GET", rf"/rasters/mosaic/{mosaic.id}/image"), mosaic.footprint_wkt
    mosaic.footprint_wkt = None                                 # its outline comes with the image list
    controller.use_imagery_extent()
    wait_until(lambda: not controller._extent_pending and not imagery._images_loading, 5)
    settle()
    check(requests("GET", rf"/rasters/mosaic/{mosaic.id}/image") > sent and not controller._extent_pending
          and not imagery._images_loading,
          "…and a click that waited for the footprints (use the extent) is not left waiting either "
          f"({requests('GET', rf'/rasters/mosaic/{mosaic.id}/image') - sent} requests)")
    controller.draft.imagery, mosaic.footprint_wkt = choice_before, footprint
    state.heal()
    imagery.load_images(mosaic.id, force=True)                  # a list that loads ends the outage's one line
    wait_until(lambda: mosaic.id in imagery.images, 5)
    # the counts of a listing: many lists fail together, and one line says so
    state.extra_mosaics = [{"id": f"m-nc-{n}", "name": f"No count {n}", "created_at": f"2025-02-01T00:00:0{n}Z",
                            "sizeInBytes": 1, "footprint": None, "tags": [],
                            "rasterLayer": {"tileUrl": "", "tileJsonUrl": ""}} for n in range(5)]
    state.fail("GET", r"/rasters/mosaic/m-nc-\d/image", 503)
    before = len(iface.bar.messages)
    imagery.load_mosaics()
    check(wait_until(lambda: requests("GET", r"/rasters/mosaic/m-nc-\d/image") >= 5 and not imagery._images_loading, 5),
          "background image lists for the counts are asked")
    settle()
    check(len(lines(before)) == 1, f"LOAD: five failing image lists for a listing give one line ({lines(before)})")
    state.heal()
    state.extra_mosaics = []
    imagery.load_mosaics()
    wait_until(lambda: imagery.mosaics_loaded and not imagery._mosaics_loading, 5)

    state.fail("POST", "/projects/page", 503)
    before = len(iface.bar.messages)
    session.load_projects()
    check(wait_until(lambda: len(lines(before)) == 1, 5) and "Projects didn't load" in lines(before)[0],
          "LOAD: the project list after sign-in that fails says so once")
    state.heal()
    state.fail("POST", "/projects/page", 503)
    controller.open_projects()
    window = controller.projects_dialog
    check(wait_until(lambda: window.failed_text != "", 5),
          "USER: the projects window keeps the list it had and records that the new one did not load")
    check(not any(w.text() == "No projects yet." for w in window.findChildren(QLabel)),
          "…and does not call it “No projects yet.”")
    window.hide()
    state.heal()

    # ---------- POLL, transient: dropped and logged, then said once ----------
    def poll_requests():
        return requests("POST", page)

    state.heal()
    state.fail("POST", page, 503)
    before, asked, log_start = len(iface.bar.messages), poll_requests(), len(logged)
    processings.refresh(POLL)
    check(wait_until(lambda: poll_requests() >= asked + threshold - 1, 5), "POLL: the processings poll keeps asking")
    check(not lines(before), f"POLL: {threshold - 1} failures in a row are dropped without a word")
    check(wait_until(lambda: len(lines(before)) == 1, 5), f"POLL: failure number {threshold} is said, once")
    check(any("server 503" in line and "processings/v2/page" in line for line in logged[log_start:]),
          "…and the dropped failures are logged (Http writes every failure to the log at Warning)")
    check("Mapflow is not answering" in lines(before)[0] and "processings list" in lines(before)[0],
          f"…in plain words ({lines(before)[0]!r})")
    seen = poll_requests()
    wait_until(lambda: poll_requests() >= seen + 3, 5)
    check(len(lines(before)) == 1, "POLL: further failures of the same outage say nothing more")
    state.heal()
    check(wait_until(lambda: processings._poll_failures.count == 0 and not processings.load_failed, 5),
          "POLL: the poll recovers by itself and the count starts again")
    before = len(iface.bar.messages)
    for _ in range(2):                                      # fail, fail, success, fail, fail: never in a row
        asked = poll_requests()
        state.fail("POST", page, 503, times=threshold - 1)
        processings.refresh(POLL)
        check(wait_until(lambda: poll_requests() >= asked + threshold and not processings.load_failed
                         and not processings._loading, 5), "POLL: failures, then a success")
    settle()
    check(not lines(before), f"POLL: a success between failures resets the count: no line ({lines(before)})")
    # a request that times out is transient too
    saved_timeout = http_module.TIMEOUT_S
    http_module.TIMEOUT_S, state.hang_seconds = 1, 3
    kinds, original = [], processings._poll_failures.failed

    def record(kind, status=None):
        kinds.append(kind)
        return original(kind, status)
    processings._poll_failures.failed = record
    try:
        state.fail("POST", page, "hang", times=1)
        state.fail("POST", page, 503, times=threshold - 2)
        processings.refresh(POLL)
        check(wait_until(lambda: len(kinds) == threshold - 1 and not processings._loading, 8)
              and kinds[0] == "timeout" and not lines(before),
              f"POLL: a request that timed out is a transient failure, dropped without a line ({kinds})")
        check(wait_until(lambda: processings._poll_failures.count == 0 and processings.loaded
                         and not processings.load_failed, 6), "…and the next good answer resets the count")
    finally:
        http_module.TIMEOUT_S = saved_timeout
        del processings._poll_failures.failed
    # the account status
    state.heal()
    state.fail("GET", "/user/status", 503)
    before, asked = len(iface.bar.messages), requests("GET", "/user/status")
    session._timer.start()
    check(wait_until(lambda: requests("GET", "/user/status") >= asked + threshold, 5)
          and wait_until(lambda: len(lines(before)) == 1, 3),
          "POLL: the account status says it once, after the same count")
    check("account status" in lines(before)[0], f"…naming what failed ({lines(before)[0]!r})")
    seen = requests("GET", "/user/status")
    wait_until(lambda: requests("GET", "/user/status") >= seen + 3, 5)
    check(len(lines(before)) == 1, "…and does not say it again")
    state.heal()
    check(wait_until(lambda: session._status_poll.count == 0, 5), "…and a success resets its count")
    before = len(iface.bar.messages)
    for _ in range(2):
        asked = requests("GET", "/user/status")
        state.fail("GET", "/user/status", 503, times=threshold - 1)
        wait_until(lambda: requests("GET", "/user/status") >= asked + threshold, 5)
        settle(0.2)
    check(not lines(before), "…a success between failures: no line")
    session._timer.stop()
    # the collections refresh, by the controller's timer
    state.heal()
    state.fail("GET", r"/rasters/mosaic/page", 503)
    before, asked = len(iface.bar.messages), requests("GET", r"/rasters/mosaic/page")

    def mosaic_tick():
        imagery._mosaics_at = 0.0
        controller._mosaic_refresh.timeout.emit()
        return wait_until(lambda: not imagery.loading_mosaics, 5)

    check(content.isVisible() and session.state == "signed_in", "the panel is open, so the collections refresh runs")
    for _ in range(threshold - 1):
        mosaic_tick()
    check(requests("GET", r"/rasters/mosaic/page") == asked + threshold - 1 and not lines(before),
          "POLL: the collections refresh drops its first failures")
    mosaic_tick()
    check(len(lines(before)) == 1 and "collections list" in lines(before)[0], "…and says so once at the count")
    mosaic_tick()
    mosaic_tick()
    check(len(lines(before)) == 1, "…and not again")
    state.heal()
    mosaic_tick()
    check(imagery._mosaics_poll.count == 0 and imagery.mosaics_loaded and not imagery.mosaics_failed,
          "…and a success resets it")

    # ---------- POLL, permanent: stops, and says why ----------
    state.heal()
    state.fail("GET", "/user/status", 403)
    before, asked = len(iface.bar.messages), requests("GET", "/user/status")
    session._timer.start()
    check(wait_until(lambda: not session._timer.isActive() and len(lines(before)) == 1, 5),
          "POLL: a permanent failure of the account status stops its timer and says so once")
    check("account status" in lines(before)[0], f"…naming it ({lines(before)[0]!r})")
    settle(0.5)
    session.refresh_status()
    settle(0.3)
    check(requests("GET", "/user/status") == asked + 1, "…and nothing asks again, not even a panel opening")
    state.heal()
    session.api.default_project(session._signed_in, None)           # what a sign-in runs
    check(wait_until(lambda: session._timer.isActive() and not session._status_poll.stopped, 5)
          and wait_until(lambda: requests("GET", "/user/status") > asked + 1, 5),
          "…until the next sign-in, which starts it again")
    session._timer.stop()
    wait_until(lambda: session.project is not None and session.project.id == saved_project, 5)
    # the collections refresh
    state.fail("GET", r"/rasters/mosaic/page", 403)
    before, asked = len(iface.bar.messages), requests("GET", r"/rasters/mosaic/page")
    mosaic_tick()
    check(len(lines(before)) == 1 and imagery._mosaics_poll.stopped and "no longer refreshed" in lines(before)[0],
          f"POLL: a permanent failure of the collections refresh stops it and says why ({lines(before)})")
    mosaic_tick()
    mosaic_tick()
    check(requests("GET", r"/rasters/mosaic/page") == asked + 1, "…and the timer's next ticks send nothing")
    state.heal()
    imagery.load_mosaics()
    check(wait_until(lambda: imagery.mosaics_loaded and not imagery._mosaics_poll.stopped, 5),
          "…until a load succeeds, which clears the stop")
    mosaic_tick()
    check(requests("GET", r"/rasters/mosaic/page") > asked + 1, "…and then the refresh asks again")
    # the processings poll
    with state.lock:
        state.processings.append(dict(fixtures.processing_json("poll-run", "IN_PROGRESS", 0, name="Poll run"),
                                      projectId="project-2"))
    state.fail("POST", page, 400)
    before, asked = len(iface.bar.messages), poll_requests()
    processings.refresh(POLL)
    check(wait_until(lambda: len(lines(before)) == 1 and processings._poll_failures.stopped, 5)
          and "no longer refreshed" in lines(before)[0],
          f"POLL: a permanent failure of the processings poll stops it and says why ({lines(before)})")
    settle(0.5)
    check(poll_requests() == asked + 1 and not processings._poll.isActive(), "…and no more list requests go out")
    state.heal()
    processings.refresh(USER)
    check(wait_until(lambda: not processings._poll_failures.stopped and processings.loaded, 5)
          and wait_until(lambda: poll_requests() >= asked + 3, 5),
          "…until a list loads: the poll then starts again by itself")
    ready()
    with state.lock:
        state.processings[:] = [p for p in state.processings if p["id"] != "poll-run"]

    # ---------- the open project is gone ----------
    default_id = session.default_project.id
    for what in (404, 403):
        state.heal()
        state.fail("POST", page, what)
        before, asked, projects_asked = len(iface.bar.messages), poll_requests(), requests("POST", "/projects/page")
        processings.refresh(POLL)
        check(wait_until(lambda: session.project.id == default_id and processings.loaded, 5)
              and len(lines(before)) == 1 and "Harbor" in lines(before)[0],
              f"the open project answers {what}: the default project opens and one line names the gone one "
              f"({lines(before)})")
        settle(0.5)
        check(poll_requests() == asked + 1 and requests("POST", "/projects/page") > projects_asked,
              "…the gone project's list is not asked again, and the project list is loaded again")
        state.heal()
        session.select_project("project-2")
        check(wait_until(lambda: session.project.id == "project-2" and processings.loaded, 5), "…(the project is back)")
    default_page = r"/projects/project-1/processings/v2/page"
    state.fail("POST", default_page, 404)
    before, asked = len(iface.bar.messages), requests("POST", default_page)
    session.select_project(default_id)
    wait_until(lambda: session.project.id == default_id, 5)
    settle(0.6)
    check(session.project.id == default_id and len(lines(before)) == 1 and "no other project" in lines(before)[0],
          f"the default project itself is gone: the user is told and nothing else opens ({lines(before)})")
    check(requests("POST", default_page) == asked + 1 and not processings._poll.isActive(),
          "…with no loop of requests")
    state.heal()
    session.select_project("project-2")
    check(wait_until(lambda: session.project.id == "project-2" and processings.loaded, 5), "…(the project is back)")
    ready()

    # ---------- a failed list does not look empty ----------
    state.fail("POST", page, 503)
    processings.set_project(None)
    processings.set_project(session.project)
    check(wait_until(lambda: processings.load_failed, 5), "a project whose list fails")
    text = content.processings.empty_text.text()
    check(text == "Processings didn't load." and not content.processings.start_button.isVisibleTo(content.processings),
          f"…says that the list did not load, not “No processings in this project yet” ({text!r})")
    state.heal()
    session.select_project("project-new-1")                 # a project with no processings
    check(wait_until(lambda: session.project.id == "project-new-1" and processings.loaded
                     and not processings.load_failed, 5), "a project with no processings answers")
    check(content.processings.empty_text.text() == "No processings in this project yet."
          and content.processings.start_button.isVisibleTo(content.processings),
          "…and only then the page says “No processings in this project yet.”")
    session.select_project("project-2")
    wait_until(lambda: session.project.id == "project-2" and processings.loaded, 5)
    state.no_mosaics = True
    imagery.forget_mosaics()
    imagery.load_mosaics()
    check(wait_until(lambda: imagery.mosaics_loaded, 5)
          and content.imagery.mosaics_title.text() == "No collections yet",
          "an account without collections says so after a successful answer")
    state.no_mosaics = False
    state.fail("GET", r"/rasters/mosaic/page", 503)
    imagery.forget_mosaics()
    imagery.load_mosaics()
    wait_until(lambda: imagery.mosaics_failed, 5)
    controller.open_mosaic_picker()
    picker = controller.mosaic_picker
    check(picker.list_empty.text() == "Collections didn't load.",
          f"the picker says so too ({picker.list_empty.text()!r})")
    picker.hide()
    state.heal()
    imagery.load_mosaics()
    wait_until(lambda: imagery.mosaics_loaded and not imagery.mosaics_failed, 5)
    fresh = ProjectsDialog()
    fresh.set_state(None, [])
    texts = lambda: [w.text() for w in fresh.findChildren(QLabel)]  # noqa: E731
    check("Loading projects…" in texts() and "No projects yet." not in texts(),
          "the projects window says “Loading projects…” before any answer")
    fresh.set_failed("Mapflow is not responding.")
    check(any("didn't load" in t for t in texts()) and "No projects yet." not in texts(),
          "…“Projects didn't load” after a failure")
    fresh.set_results([], 0)
    check("No projects yet." in texts(), "…and “No projects yet.” only after a successful empty answer")
    fresh.deleteLater()

    # ---------- nothing that changes state is sent again ----------
    state.heal()
    session._timer.stop()
    target, other = processings.items[0], processings.items[1]
    http = session.http
    sent, real_send = [], http._send

    def counting_send(method, path, *args, **kwargs):
        sent.append((method, "/" + path.lstrip("/")))
        return real_send(method, path, *args, **kwargs)
    http._send = counting_send
    # What the plugin sends is counted at Http. A dropped connection is also counted at the server for reads
    # only: Qt itself reconnects and sends a request again when the server closes the connection with no answer
    # (up to three more times, on QGIS 3.28's Qt 5.15), and the plugin cannot tell it not to.
    for what in (503, "drop"):
        errors = []
        cases = (
            ("POST", r"/processings/v2$",
             lambda: processings.api.start({"name": "no resend"}, lambda _p: None, errors.append)),
            ("PUT", rf"/processings/{target.id}/v2$", lambda: processings.rename(target, "Renamed", "")),
            ("DELETE", rf"/processings/{other.id}$", lambda: processings.delete(other)),
            ("POST", r"/rasters/mosaic$",
             lambda: imagery.create_collection("No resend", [], lambda _i: None, errors.append)),
        )
        for method, pattern, send in cases:
            state.heal()
            state.fail(method, pattern, what)
            before, asked = len(iface.bar.messages), requests(method, pattern)
            sent.clear()
            send()
            check(wait_until(lambda: requests(method, pattern) >= asked + 1, 5), f"{method} {pattern}: sent ({what})")
            settle(0.5)
            mine = [m for m, p in sent if m == method and re.search(pattern, p)]
            check(len(mine) == 1, f"{method} {pattern} that failed ({what}) is not sent again by the plugin ({mine})")
            if what != "drop":
                check(requests(method, pattern) == asked + 1, "…and exactly one request reached the server")
            check(errors or lines(before), f"…and the failure reaches the user or the caller ({what})")
            errors.clear()
    del http._send
    state.heal()
    state.fail("DELETE", r"/rasters/mosaic/probe$", "drop")
    answers = []
    session.http.delete("rasters/mosaic/probe", on_error=answers.append)
    check(wait_until(lambda: answers, 5) and is_transient(answers[0].kind, answers[0].status),
          f"a connection the server drops is a transient failure ({answers[0].kind} {answers[0].status})")
    state.heal()
    state.fail("GET", "/user/status", 503, times=1)
    asked = requests("GET", "/user/status")
    session._timer.start()
    check(wait_until(lambda: requests("GET", "/user/status") >= asked + 2, 5),
          "a read that failed is asked again by its timer")
    session._timer.stop()

    # ---------- restore ----------
    state.heal()
    state.no_mosaics, state.many_mosaics, state.extra_mosaics = False, 0, []
    processings._poll.setInterval(150)
    session._timer.setInterval(config.STATUS_INTERVAL_MS)
    session._timer.start()
    session.select_project(saved_project)
    ready()
    check(session.project.id == saved_project and not processings._poll_failures.stopped,
          "the failure checks leave the session as they found it")


def check_upload_timeout(iface, plugin, state):
    """spec/005 § Mapflow Backend API, spec/002_C (upload): every request has a timer, and an upload that stalls
    ends through `on_error` as a timeout, with the upload flags cleared so the next upload can start.
    A short value stands for the hour. Everything the function changes is restored."""
    import mapflow_next.api.http as http_module
    session, imagery = plugin.services[1], plugin.services[3]
    http, controller = session.http, plugin.controller
    page = plugin.dock.content.imagery
    path = make_geotiff("stalled.tif")
    saved, saved_hang = http_module.UPLOAD_TIMEOUT_S, state.hang_seconds
    check(isinstance(config.UPLOAD_TIMEOUT_S, int) and config.UPLOAD_TIMEOUT_S == 3600
          and config.UPLOAD_TIMEOUT_S > config.RESULT_TIMEOUT_S, "TIMEOUT: an upload has a timeout of one hour")
    check(http_module.UPLOAD_TIMEOUT_S == config.UPLOAD_TIMEOUT_S, "…and Http uses that constant")
    state.heal()
    state.hang_seconds = 3
    failed = []
    imagery.uploadFailed.connect(failed.append)
    try:
        # every request has a timeout
        before = dict(http._pending)
        for bad in (0, -1):
            try:
                http.get("projects", timeout=bad)
                raised = False
            except ValueError:
                raised = True
            check(raised and http._pending == before, f"TIMEOUT: timeout={bad} is refused and nothing is created")
        state.fail("GET", r"/user/status", "hang", times=1)
        stopped = []
        key = http.get("user/status", on_error=stopped.append)
        pending = http._pending[key]
        check(pending.timer is not None and pending.timer.isActive() and pending.timeout == config.TIMEOUT_S,
              "TIMEOUT: a request with no timeout gets the default one, and its timer runs")
        # the inactivity timer of an upload restarts while bytes move, and only then (the timer runs 1 s here)
        pending.timer.start(1000)
        wait_until(lambda: False, 0.6)
        http._alive(key, 10, 100)
        wait_until(lambda: False, 0.7)
        check(key in http._pending and not stopped, "TIMEOUT: an upload whose bytes move is not cut")
        http._alive(key, 10, 100)
        check(wait_until(lambda: stopped, 1.5) and stopped[0].kind == "timeout",
              "…and one whose count stands still ends as a timeout")
        check(wait_until(lambda: key not in http._pending, 5), "…and leaves nothing pending")
        state.heal()
        state.uploads.clear()
        key = http.upload("rasters/mosaic/image?name=quick&tags=", path, on_error=lambda _e: None)
        check(http._pending[key].timeout == config.UPLOAD_TIMEOUT_S and http._pending[key].timer.isActive(),
              "TIMEOUT: an upload's request carries the upload timeout and a running timer")
        check(wait_until(lambda: not http._pending and state.uploads, 5), "…and an upload that answers ends normally")

        # a short value, the direct request
        http_module.UPLOAD_TIMEOUT_S = 1
        errors, done = [], []
        state.fail("POST", r"/rasters/mosaic/image", "hang", times=1)
        started = time.time()
        http.upload("rasters/mosaic/image?name=timeout&tags=", path, on_success=done.append, on_error=errors.append)
        check(wait_until(lambda: errors, 5), "TIMEOUT: an upload that gets no answer ends through on_error")
        elapsed = time.time() - started
        check(len(errors) == 1 and errors[0].kind == "timeout" and not done, f"…once, as a timeout ({errors})")
        check(elapsed < state.hang_seconds, f"…and the client gives up before the server does ({elapsed:.1f} s)")
        check(not http._pending, "…and nothing is left pending")

        # through the service: the flags are cleared
        state.heal()
        state.uploads.clear()
        state.fail("POST", r"/rasters/mosaic/image", "hang", times=1)
        imagery.upload(path, "Stalled")
        check(imagery.uploading, "TIMEOUT: an upload is under way")
        check(wait_until(lambda: failed, 5) and "did not answer in time" in failed[0],
              f"…and a stalled one says so ({failed})")
        check(not imagery.uploading and controller.uploading is None and page.upload_button.isEnabled()
              and not page.upload_bar.isVisible(), "…and the upload flags and the page are cleared")
        state.heal()
        imagery.upload(path, "Again")
        check(wait_until(lambda: not imagery.uploading and [u[:2] for u in state.uploads] == [("new", "Again")], 8),
              f"…and the next upload starts and finishes ({state.uploads})")

        # a file into an existing collection
        failed.clear()
        state.fail("POST", r"/rasters/mosaic/m-1/image", "hang", times=1)
        imagery.upload_into("m-1", [path])
        check(wait_until(lambda: failed, 5) and "stalled.tif" in failed[0] and "did not answer in time" in failed[0],
              f"TIMEOUT: a file into a collection that stalls names the file ({failed})")
        check(not imagery.uploading and controller.uploading is None, "…and clears the flags")

        # a new collection with several files
        failed.clear()
        state.fail("POST", r"/rasters/mosaic/m-new-\d+/image", "hang", times=1)
        imagery.upload_many([path, make_geotiff("second.tif")], "Two files")
        check(wait_until(lambda: failed, 8) and not imagery.uploading and controller.uploading is None,
              f"TIMEOUT: a stalled file of several clears the flags ({failed})")
    finally:
        imagery.uploadFailed.disconnect(failed.append)
        http_module.UPLOAD_TIMEOUT_S = saved
        state.hang_seconds = saved_hang
        state.heal()
        http.abort_all()
        wait_until(lambda: not http._pending, 5)


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
    toolbars = iface.window.findChildren(QToolBar, "MapflowToolbar")
    check(len(toolbars) == 1 and toolbars[0].windowTitle() == "Mapflow" and plugin.action in toolbars[0].actions()
          and not iface.toolbar_actions,
          "the Mapflow button sits in a toolbar of its own, not in the Plugins toolbar")
    menu = [action.text() for action in iface.menu_actions.get("&Mapflow Next", [])]
    check(menu == ["Mapflow", "Scenarios…", "Check for updates…"], f"the plugin's menu: {menu}")

    # Check for updates, with QGIS's plugin installer standing in for the plugin repositories
    from mapflow_next.qgis_bridge import updates
    import types
    calls = []

    class OldInstaller:                  # QGIS 3.x: showPluginManagerWhenReady(*params)
        def showPluginManagerWhenReady(self, *params):
            calls.append(("old",) + params)

    class NewInstaller:                  # newer QGIS: (tab_index, search_term)
        def showPluginManagerWhenReady(self, tab_index=-1, search_term=""):
            calls.append(("new", tab_index, search_term))
    saved = sys.modules.get("pyplugin_installer")
    sys.modules["pyplugin_installer"] = fake = types.ModuleType("pyplugin_installer")
    for installer in (OldInstaller, NewInstaller):
        fake.instance = installer
        updates.open_upgrades()
    if saved is None:
        del sys.modules["pyplugin_installer"]
    else:
        sys.modules["pyplugin_installer"] = saved
    check(calls == [("old", 3), ("new", 3, "Mapflow Next")],
          f"Update… opens the Upgradeable tab, filtered to the plugin where QGIS can ({calls})")
    upgrades_opened, record = [], {}
    updates.fetch_record = lambda key: record.get(key)
    updates.open_upgrades = lambda: upgrades_opened.append(True)
    updates.allow_experimental = lambda: allow[0]
    allow = [True]

    def check_updates():
        before = len(iface.bar.messages)
        plugin.updates_action.trigger()
        return iface.bar.messages[before][1] if len(iface.bar.messages) > before else ""

    record["mapflow_next"] = {"version_available_stable": "4.1.0", "version_available_experimental": ""}
    text = check_updates()
    buttons = iface.bar.widgets[-1].findChildren(QPushButton) if iface.bar.widgets else []
    check("4.1.0 is available" in text and "You have 4.0.0" in text and [b.text() for b in buttons] == ["Update…"],
          f"a newer version in the repositories is announced with an Update button ({text})")
    buttons[0].click()
    check(upgrades_opened == [True], "Update… opens the Plugin Manager on the Upgradeable tab")
    record["mapflow_next"] = {"version_available_stable": "4.0.0"}
    check("is up to date (4.0.0)" in check_updates(), "the installed version is the newest: up to date")
    record.clear()
    allow[0] = False
    check("experimental" in check_updates(),
          "not listed while QGIS hides experimental plugins: says how to show them")
    allow[0] = True
    text = check_updates()
    iface.bar.widgets[-1].findChildren(QPushButton)[0].click()
    check("isn't in your plugin repositories" in text and links.opened[-1:] == [config.RELEASES_URL],
          "not in any repository (a ZIP install): points to the releases page")

    def unreachable(key):
        raise OSError("repository unreachable")
    updates.fetch_record = unreachable
    check("Couldn't check for updates: repository unreachable" in check_updates(), "a failed check says why")
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
    # several requests out when the token ran out (a laptop waking up): one renewal, and no sign-out
    session._forced_refresh_at = 0.0                     # a minute later
    with state.lock:
        state.access_tokens.discard("access-3")
    answers = []
    for _ in range(4):
        session.http.get("user/status", on_success=lambda _d: answers.append("ok"),
                         on_error=lambda e: answers.append(e.status))
    check(wait_until(lambda: len(answers) == 4 and session.http.bearer == "access-4", 5)
          and session.state == "signed_in" and answers.count(401) == 4,
          f"four requests rejected together renew the token once and keep the sign-in ({answers}, "
          f"{session.http.bearer}, {session.state})")

    # QGIS restart: the saved sign-in comes back without opening the browser
    opened = len(browser.opened)
    # unload while a result is converting: it returns at once, the task stops, and no file or message follows
    import mapflow_next.qgis_bridge.conversion as conversion
    results_now = plugin.services[4]
    entered, left, told = [], [], []
    results_now.failed.connect(lambda *args: told.append(args))
    files_before = files_under(out_dir)
    saved_convert, shown = conversion.convert_geojson, len(iface.bar.messages)
    conversion.convert_geojson = waiting_conversion(entered, left)
    try:
        converting = processing_done("conv-unload")
        results_now.add_to_map(converting)
        check(wait_until(lambda: entered, 5), "a conversion runs when the plugin is unloaded")
        stopping = time.time()
        plugin.unload()
        took = time.time() - stopping
        check(took < 6 and left, f"unload cancels the conversion and waits for its worker ({took:.1f} s)")
        check(files_under(out_dir) == files_before, "…and no file stays in the output folder "
              f"({sorted(set(files_under(out_dir)) - set(files_before))})")
        wait_until(lambda: False, 0.3)
        check(not told and len(iface.bar.messages) == shown, "…and nothing is told about it afterwards")
    finally:
        conversion.convert_geojson = saved_convert
    plugin = classFactory(iface)
    plugin.initGui()
    check(wait_until(lambda: len(iface.window.findChildren(QToolBar, "MapflowToolbar")) == 1, 3),
          "after a reload there is still one Mapflow toolbar")
    plugin.toggle(True)
    content = plugin.dock.content
    session, processings, controller = plugin.services[1], plugin.services[2], plugin.controller
    processings._poll.setInterval(150)
    check(wait_until(lambda: session.state == "signed_in") and len(browser.opened) == opened
          and session.http.bearer == "access-5", "after a restart the browser sign-in is restored silently")
    imagery_now = plugin.services[3]
    controller.starting, imagery_now.uploading = True, True        # a start and an upload in flight
    imagery_now._images_loading.add("m-1")
    session.sign_out()
    check(wait_until(lambda: session.state == "signed_out") and not auth.load_refresh_token(session.config),
          "signing out forgets the browser sign-in")
    check(not controller.starting and not imagery_now.uploading and not imagery_now._images_loading,
          "…and what was in flight isn't left busy for the next sign-in (Run, uploads, image lists)")

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
    check(mapbox.note == "" and "★" not in mapbox.meta, "at the recommended zoom there is no warning line")
    # A source not chosen shows the zoom it would run at: set to another one, its row names the recommended zoom
    controller.provider_zoom["arcgis"] = 18
    other = next(r for r in controller._imagery_rows(session.status, True)[0] if r.key == "provider:arcgis")
    check(other.zoom == 18 and other.note == "z19 recommended" and "★" not in other.meta,
          f"at another zoom a warning line names the recommended one ({other.zoom}, {other.note!r})")
    controller.provider_zoom.pop("arcgis")
    zoom_combo = next(w for w in run._rows[[r.key for r in rows].index("provider:mapbox")].findChildren(QComboBox))
    zooms = [zoom_combo.itemText(i) for i in range(zoom_combo.count())]
    marks = [zoom_combo.itemIcon(i).pixmap(12, 12).toImage() for i in range(zoom_combo.count())]
    check("z19" in zooms and len(zooms) > 1
          and all(mark != marks[zooms.index("z19")] for z, mark in zip(zooms, marks) if z != "z19"),
          f"the recommended zoom is marked with a star icon, the others aren't ({zooms})")
    eyes = [b for row in run._rows for b in row.findChildren(QToolButton) if b.toolTip() == "Preview on the map"]
    check(len(eyes) == 1 and eyes[0].parentWidget() is run._rows[[r.key for r in rows].index(selected)],
          "the preview is an eye on the selected source only")
    wait_until(lambda: False, 0.1)
    picker_control = next(w for w in eyes[0].parentWidget().findChildren(QComboBox))
    check(abs(eyes[0].geometry().center().y() - picker_control.geometry().center().y()) <= 2,
          f"the eye is level with the source's control ({eyes[0].geometry().center().y()} vs "
          f"{picker_control.geometry().center().y()})")
    eyes[0].click()
    check(wait_until(lambda: QgsProject.instance().mapLayersByName("Mapbox Satellite · preview")),
          "the eye adds the source's preview to the map")

    def eye():
        return next((b for row in run._rows for b in row.findChildren(QToolButton)
                     if b.toolTip() in ("Preview on the map", "Hide the preview") and b.isVisible()), None)

    check(wait_until(lambda: eye() is not None and eye().toolTip() == "Hide the preview"
                     and eye().property("on") is True, 3),
          "while the preview is on the map, the eye shows it as on")
    eye().click()
    check(wait_until(lambda: not QgsProject.instance().mapLayersByName("Mapbox Satellite · preview"), 3)
          and wait_until(lambda: eye() is not None and eye().toolTip() == "Preview on the map", 3),
          "a second click takes the preview off the map, and the eye shows it as off")
    arcgis = next(r for r in rows if r.key == "provider:arcgis")
    check(arcgis.price == "+8.5 cr/km²", f"imagery prices per km² are rounded (8.523731677829918 → {arcgis.price})")
    check(run.model_price.text() == "10 cr/km²",
          f"What to map shows the model's price, from pricePerSqKm ({run.model_price.text()!r})")
    texts = {w.text() for w in run.findChildren(QLabel)} | {b.text() for b in run.findChildren(QToolButton)}
    check("Name:" in texts and "Saves as" not in texts, "the processing name is labelled “Name:”")
    check("Select features" in texts and "Selected features" not in texts,
          "the area tool reads “Select features” (a tool, not an option)")
    agent = [b for b in content.start.findChildren(QPushButton) if "AI Agent" in b.text()]
    links.opened.clear()
    agent and agent[0].click()
    check(links.opened == ["https://app.mapflow.ai/#home-top"],
          f"the AI Agent link opens Mapflow's home ({links.opened})")
    check(session._timer.interval() == 5000 and session._timer.isActive(),
          "while the panel is open, the balance and plan are checked every 5 seconds")

    # the mouse wheel over a zoom list scrolls the form; only the opened list changes the zoom
    from qgis.PyQt.QtCore import QPoint, QPointF
    from qgis.PyQt.QtGui import QWheelEvent
    index = zoom_combo.currentIndex()
    centre = QPointF(zoom_combo.rect().center())
    wheel = QWheelEvent(centre, QPointF(zoom_combo.mapToGlobal(centre.toPoint())), QPoint(0, 0), QPoint(0, -120),
                        Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
    zoom_combo.wheelEvent(wheel)          # the combo's own handler: Qt then passes an ignored event to the form
    check(zoom_combo.currentIndex() == index and not wheel.isAccepted(),
          "the wheel over the zoom list leaves the zoom alone and goes on to the form")
    check(all(type(c).__name__ == "Combo" for c in (run.model_combo, run.layer_combo, content.imagery.layer_combo)),
          "the model and area lists ignore the wheel too")
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
    from mapflow_next.ui.widgets import Callout
    loose = Callout("info", "No projects yet.")
    check(not loose.isVisible(), "a callout made before it is put in a window doesn't flash up as a window of its own")
    loose.deleteLater()
    from mapflow_next.core.draft import Issue
    run.set_issues([Issue("account", "This run needs 9 credits; you have 1.", (("Top up", "top_up"),))])
    check(not run.issues.action.isHidden() and run.issues.action.text().startswith("Top up")
          and "Top up" not in run.issues.text.text(), "not enough credits: Top up is a button on the right")
    run.set_issues([])
    check(run.issues.isHidden() and run.issues.action.isHidden(), "…gone once the run can go")
    controller.refresh_run()                        # the form's own issues back
    from qgis.PyQt.QtCore import QEvent as _QEvent
    from qgis.PyQt.QtGui import QFocusEvent as _QFocusEvent
    tab_button = content.tab_buttons[1]
    QApplication.sendEvent(tab_button, _QFocusEvent(_QEvent.Type.FocusIn, Qt.FocusReason.MouseFocusReason))
    clicked = tab_button.property("focusring")
    QApplication.sendEvent(tab_button, _QFocusEvent(_QEvent.Type.FocusIn, Qt.FocusReason.TabFocusReason))
    tabbed = tab_button.property("focusring")
    QApplication.sendEvent(tab_button, _QFocusEvent(_QEvent.Type.FocusOut, Qt.FocusReason.TabFocusReason))
    check(clicked is False and tabbed is True and tab_button.property("focusring") is False,
          "a focus ring shows when the focus comes from the keyboard, not after a click")
    gone = controller._cost_error_text('DataCatalog error mosaicId not found: DC returned status 404: {"detail": '
                                       '{"code": "ItemNotFound"}}')
    check(not gone.startswith("Cost check") and "no longer" in gone
          and controller._cost_error_text("Area too large").startswith("Cost check"),
          f"imagery gone since is said in words, other cost errors as Mapflow sends them ({gone!r})")
    tips = {name: getattr(getattr(s.parentWidget(), "tip", None), "text", "") for name, s in run._switches.items()}
    check("Sorts buildings into classes by use" in tips.get("classification", "")
          and "Estimates the height of each building" in tips.get("heights", "") and tips.get("simplification") == ""
          and not any(s.toolTip() for s in run._switches.values()),
          f"an option's hover text, from /user/status, covers the whole option; one without a description has "
          f"none ({tips})")

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
    check(not plugin.services[4].is_busy(started["id"]) and not plugin.services[4]._tasks,
          "…and the processing is not loading, with no conversion task left")
    saved_files = files_under(out_dir)
    check(sum(f.endswith(".gpkg") for f in saved_files) >= 1 and not [f for f in saved_files
                                                                      if f.startswith(".downloads")],
          f"…one GeoPackage is in the output folder and nothing stays in .downloads ({saved_files})")

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

    # Start's Recent: a long project name is cut with "…", and a processing there opens in Processings
    from mapflow_next.ui.start_page import _MiniCard
    content.start.set_recent("A" * 300, processings.items[:2], set())
    title = content.start.recent_title
    content.go(0)
    wait_until(lambda: False, 0.1)
    see_all = next(b for b in content.start.findChildren(QPushButton) if b.text() == "See all")
    gap = see_all.geometry().left() - title.geometry().right()
    check(title.full_text() == "Recent in " + "A" * 300 and title.text().endswith("…") and gap >= 12,
          f"a long project name is cut short of “See all” ({gap} px between them)")
    mini = next(w for w in content.start.findChildren(_MiniCard) if w.isVisibleTo(content.start))
    content.go(0)
    content.processings.expanded = None
    QTest.mouseClick(mini, Qt.MouseButton.LeftButton)
    check(wait_until(lambda: content.current_tab() == 1, 3) and content.processings.expanded == mini.processing_id,
          "a recent processing opens in Processings, expanded")

    # rate: a star opens the feedback form; only "Send feedback" sends, and the rating stays shown
    seen = []

    def comment(dialog):
        dialog.stars.set_value(4)
        dialog.comment.setPlainText("Missed two small sheds")
    close_modal_later(seen, comment)
    content.processings.rate.emit(started["id"], 3)

    def ratings():
        return [r for r in state.requests if r[0] == "PUT" and r[1] == f"/processings/{started['id']}/rate"]
    check(seen == ["FeedbackDialog"] and wait_until(lambda: ratings(), 5)
          and ratings()[-1][2] == {"rating": 4, "feedback": "Missed two small sheds"},
          "a star opens the feedback form, and Send feedback sends the rating with the comment")
    check(wait_until(lambda: content.processings.ratings.get(started["id"]) == 4, 3),
          "the rating stays shown when the processing is opened again")
    seen = []
    close_modal_later(seen)                      # Cancel
    content.processings.rate.emit(started["id"], 1)
    wait_until(lambda: False, 0.6)
    check(seen == ["FeedbackDialog"] and len(ratings()) == 1, "cancelling the form sends nothing")

    # Open in Mapflow Web: that processing, in its project
    links.opened.clear()
    content.processings.openWeb.emit(started["id"])
    check(links.opened == [f"https://app.mapflow.ai/projects/project-1?processing={started['id']}"],
          f"Open in Mapflow Web opens that processing ({links.opened})")

    # Download the area (AOI)
    import mapflow_next.controller as controller_module
    aoi_file = Path(tempfile.mkdtemp()) / "area.geojson"
    saved_dialog = controller_module.QFileDialog.getSaveFileName
    controller_module.QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: (str(aoi_file), ""))
    try:
        content.processings.downloadAoi.emit(started["id"])
        check(wait_until(lambda: aoi_file.exists(), 5)
              and QgsProject.instance().mapLayersByName("Area · Old town heights"),
              "Download the area saves the processing's AOI as GeoJSON and adds it to the map")
    finally:
        controller_module.QFileDialog.getSaveFileName = saved_dialog

    # Refresh turns while the list is on its way
    content.processings.refresh_button.click()
    check(content.processings.refreshing, "Refresh turns while the list loads")
    check(wait_until(lambda: not content.processings.refreshing, 5), "…and stops once it's back")

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
    check_the_guard(iface, plugin, url, settings)
    check_result_conversion(iface, plugin)
    check_credentials_origin(iface, plugin, state, url)

    # imagery search: the Area drop-down is the run's area
    run.searchImageryRequested.emit()
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
    check(meta.get("minAoiIntersectionPercent") == 20, f"min area coverage is 20 % by default ({meta})")
    gap = imagery_page.cloud.geometry().top() - imagery_page.cloud_value.geometry().bottom()
    check(0 <= gap <= 4, f"a slider's title sits right on its slider ({gap} px)")
    check(QgsProject.instance().mapLayersByName("Mapflow · search results"), "footprints are drawn on the map")
    check(imagery_page.date_from.calendarPopup() and "calendar" in content.styleSheet(),
          "dates have a calendar picker with a visible calendar icon")
    check(isinstance(imagery_page.cloud, QSlider) and isinstance(imagery_page.nadir, QSlider),
          "cloud cover and off-nadir are sliders")
    check(wait_until(lambda: imagery_page.has_thumbnail("img-1"), 5), "search results load their picture previews")
    eye = imagery_page._eyes["img-1"]
    eye.click()
    check(wait_until(lambda: any(x.customProperty("mapflow_next/preview") == "catalog:img-1"
                                 for x in QgsProject.instance().mapLayers().values()), 5)
          and wait_until(lambda: imagery_page._eyes["img-1"].property("on") is True, 3),
          "the eye on a search result puts its preview on the map, and shows it as on")
    imagery_page._eyes["img-1"].click()
    check(wait_until(lambda: not any(x.customProperty("mapflow_next/preview") == "catalog:img-1"
                                     for x in QgsProject.instance().mapLayers().values()), 3)
          and wait_until(lambda: imagery_page._eyes["img-1"].property("on") is not True, 3),
          "…and a second click takes it off")
    content.open_start()
    content.go(2)
    controller.render_search_results()
    from mapflow_next.ui.widgets import rounded

    def centre(pixmap):  # QLabel.pixmap() differs in size and pixel ratio between Qt 5 and Qt 6
        image = pixmap.toImage()
        return image.pixelColor(image.width() // 2, image.height() // 2).getRgb()  # (r, g, b, a)

    shown = imagery_page._thumbs["img-1"].pixmap()
    expected = centre(rounded(imagery_page._pixmaps["img-1"], 56, 56, 8))
    check(shown is not None and not shown.isNull() and expected[3] == 255 and centre(shown) == expected,
          "back from Start, the results keep their picture previews")
    links_texts = [b.text() for b in imagery_page.findChildren(QPushButton)]
    check(any("Get advanced imagery search tools in Mapflow Web" in t for t in links_texts),
          "the search links to Mapflow Web's advanced imagery search")
    state.catalog_many = True
    imagery_page.search_button.click()
    check(wait_until(lambda: len(plugin.services[3].results) == 50, 5) and imagery_page.more_button is not None
          and "50 of 60" in imagery_page.more_button.text(), "search results come in pages, with “Show more”")
    imagery_page.more_button.click()
    check(wait_until(lambda: len(plugin.services[3].results) == 60, 5) and imagery_page.more_button is None
          and [r for r in state.requests if r[1] == "/catalog/meta"][-1][2]["offset"] == 50,
          "“Show more” loads the next page (offset 50), and then there is no more")
    state.catalog_many = False
    imagery_page.search_button.click()
    wait_until(lambda: len(plugin.services[3].results) == 2, 5)
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
    imagery_page.coverage.setValue(60)
    wait_until(lambda: imagery_page.search_button.isEnabled(), 5)     # the search before is done
    imagery_page.search_button.click()
    check(wait_until(lambda: [r for r in state.requests if r[1] == "/catalog/meta"][-1][2]
                     .get("minAoiIntersectionPercent") == 60 and imagery_page.search_button.isEnabled(), 5),
          "the min area coverage slider sends minAoiIntersectionPercent")
    imagery_page.coverage.setValue(0)
    imagery_page.search_button.click()
    check(wait_until(lambda: imagery_page.search_button.isEnabled(), 5)
          and "minAoiIntersectionPercent" not in [r for r in state.requests if r[1] == "/catalog/meta"][-1][2],
          "…and at 0 it is no filter: it isn't sent")
    imagery_page.coverage.setValue(20)

    # a multi-part preview (Roscosmos): every part is fetched, and they make one preview layer
    from mapflow_next.core.models import CatalogImage
    base = plugin.services[3].results[0].preview_url.rsplit("/", 1)[0]

    def box(west):
        return {"type": "Polygon", "coordinates": [[[west, 55.74], [west + 0.01, 55.74], [west + 0.01, 55.75],
                                                    [west, 55.75], [west, 55.74]]]}
    roscosmos = CatalogImage.from_api({
        "id": "ros-1", "providerName": "roscosmos", "productType": "Image", "previewType": "png",
        "previewUrl": f"{base}/ros-1-a", "footprint": box(37.60),
        "previews": [{"url": f"{base}/ros-1-a", "geometry": box(37.60)},
                     json.dumps({"url": f"{base}/ros-1-b", "geometry": box(37.61)})]})
    check(len(roscosmos.parts) == 2, f"both parts of the preview are read, dicts or JSON strings ({roscosmos.parts})")
    plugin.services[3].results.append(roscosmos)
    controller.show_image("ros-1")

    def ros_previews():
        return [x for x in QgsProject.instance().mapLayers().values()
                if x.customProperty("mapflow_next/preview") == "catalog:ros-1"]
    check(wait_until(lambda: len(ros_previews()) == 1, 5)
          and {r[1] for r in state.requests} >= {"/catalog/preview/ros-1-a", "/catalog/preview/ros-1-b"}
          and abs(ros_previews()[0].extent().width() - 0.02) < 0.001,
          "a preview in two parts loads both, as one layer over both footprints")
    controller.show_image("ros-1")
    check(wait_until(lambda: not ros_previews(), 3), "…and the eye takes it off again")
    plugin.services[3].results.remove(roscosmos)

    # a turned scene (Orbview): the picture is laid on the footprint's corners, not on its bounding box
    from mapflow_next.qgis_bridge.layers import footprint_corners
    nw, ne, se, sw = (37.600, 55.752), (37.612, 55.750), (37.610, 55.740), (37.598, 55.742)
    turned = {"type": "Polygon", "coordinates": [[list(se), list(sw), list(nw), list(ne), list(se)]]}
    pentagon = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0.5, 1.5], [0, 1], [0, 0]]]}
    check(footprint_corners(turned) == [nw, ne, se, sw] and footprint_corners(box(37.60)) is not None
          and footprint_corners(pentagon) is None,
          "a quadrilateral footprint's corners are read as NW, NE, SE, SW, whatever order they come in")
    orbview = CatalogImage.from_api({"id": "orb-1", "providerName": "orbview", "productType": "Image",
                                     "previewType": "png", "previewUrl": f"{base}/orb-1", "footprint": turned})
    plugin.services[3].results.append(orbview)
    controller.show_image("orb-1")

    def orb_previews():
        return [x for x in QgsProject.instance().mapLayers().values()
                if x.customProperty("mapflow_next/preview") == "catalog:orb-1"]
    check(wait_until(lambda: len(orb_previews()) == 1, 5)
          and orb_previews()[0].extent().toRectF().adjusted(-1e-4, -1e-4, 1e-4, 1e-4).contains(
              QgsRectangle(37.5985, 55.7405, 37.6115, 55.7515).toRectF())
          and orb_previews()[0].bandCount() == 4,
          f"a turned scene's preview is warped onto its footprint, clear outside it "
          f"({orb_previews()[0].extent().toString(4) if orb_previews() else 'no layer'})")
    controller.show_image("orb-1")
    wait_until(lambda: not orb_previews(), 3)
    plugin.services[3].results.remove(orbview)

    # ids as a server could send them: no file name carries them, and every file lands in the session folder
    from mapflow_next.qgis_bridge.layers import MapLayers
    session_folder = plugin.layers.temp_folder()
    legacy = Path(tempfile.gettempdir()) / "mapflow_next"
    before = set(os.listdir(session_folder.parent))
    hostile = [
        CatalogImage.from_api({"id": "../escape-1", "providerName": "orbview", "productType": "Image",
                               "previewType": "png", "previewUrl": f"{base}/hostile-1", "footprint": box(37.60)}),
        CatalogImage.from_api({"id": "x/y/escape-2", "providerName": "orbview", "productType": "Image",
                               "previewType": "png", "previewUrl": f"{base}/hostile-2", "footprint": turned}),
        CatalogImage.from_api({
            "id": "../ros-escape", "providerName": "roscosmos", "productType": "Image", "previewType": "png",
            "previewUrl": f"{base}/hostile-3a", "footprint": box(37.60),
            "previews": [{"url": f"{base}/hostile-3a", "geometry": box(37.60)},
                         {"url": f"{base}/hostile-3b", "geometry": box(37.61)}]})]
    plugin.services[3].results.extend(hostile)
    hostile_layers = []
    for image in hostile:
        controller.show_image(image.key)

        def hostile_previews(key=image.key):
            return [x for x in QgsProject.instance().mapLayers().values()
                    if x.customProperty("mapflow_next/preview") == f"catalog:{key}"]
        check(wait_until(lambda: len(hostile_previews()) == 1, 5), f"the preview of {image.id!r} is on the map")
        hostile_layers.extend(hostile_previews())
    in_folder = [Path(x.source()).resolve().parent == session_folder.resolve() for x in hostile_layers]
    check(len(hostile_layers) == 3 and all(in_folder),
          f"a preview of an id with ../ or / is a file in the session folder ({[x.source() for x in hostile_layers]})")
    names = os.listdir(session_folder)
    check(not any(re.search(r"escape|ros|\.\.", Path(x.source()).name) for x in hostile_layers)
          and all(re.fullmatch(r"preview_[0-9a-f]{16}(\.\w+)+", name) for name in names),
          f"no file name carries an id as it was sent ({sorted(names)})")
    created = set(os.listdir(session_folder.parent)) - before
    check(not any("escape" in name or name in ("y", "etc") for name in created)
          and not any(legacy.glob("*escape*")) and not any(p.stat().st_mtime >= RUN_STARTED for p in legacy.glob("*")),
          f"no file landed beside the session folder or in the old shared one ({sorted(created)})")
    check(session_folder.is_dir() and session_folder.name.startswith("mapflow_next_")
          and (os.name == "nt" or session_folder.stat().st_mode & 0o777 == 0o700),
          f"the session folder is made by mkdtemp: private, and named mapflow_next_… ({session_folder})")
    for image in hostile:
        controller.show_image(image.key)                    # the eye off again
    for image in hostile:
        plugin.services[3].results.remove(image)

    # a tiled preview (ArcGIS): the card shows its whole-world tile
    arcgis = CatalogImage.from_api({"id": "arc-1", "providerName": "arcgis", "productType": "Mosaic",
                                    "previewType": "xyz", "previewUrl": f"{base}/tile-{{z}}-{{x}}-{{y}}"})
    controller._load_thumbnails([arcgis])
    check(wait_until(lambda: imagery_page.has_thumbnail("arc-1"), 5)
          and ("GET", "/catalog/preview/tile-0-0-0") in {r[:2] for r in state.requests},
          "a tiled preview's card shows its tile 0/0/0")

    # one tiled mosaic at two zooms, under one id (as the catalog lists ArcGIS): two results, told apart by zoom
    twins = [CatalogImage.from_api({"id": "arc-2", "providerName": "arcgis", "productType": "Mosaic",
                                    "previewType": "xyz", "previewUrl": f"{base}/tile-{{z}}-{{x}}-{{y}}",
                                    "zoom": zoom, "pixelResolution": resolution, "footprint": box(37.60)})
             for zoom, resolution in ((17, 1.19), (18, 0.6))]
    check(len({t.key for t in twins}) == 2 and {t.id for t in twins} == {"arc-2"},
          f"the same mosaic at two zooms is two results ({[t.key for t in twins]})")
    plugin.services[3].results.extend(twins)
    controller.render_search_results()
    controller._world_tiles.clear()                 # both cards ask while the tile is still on its way

    def tile_requests():
        return sum(1 for r in state.requests if r[:2] == ("GET", "/catalog/preview/tile-0-0-0"))
    asked = tile_requests()
    controller._load_thumbnails(twins)
    check(wait_until(lambda: all(imagery_page.has_thumbnail(t.key) for t in twins)
                     and all(imagery_page._thumbs[t.key].pixmap() is not None for t in twins), 5)
          and tile_requests() == asked + 1,
          f"…each with its own thumbnail, from one request for their shared tile ({tile_requests() - asked})")
    controller._load_thumbnails([arcgis, *twins])
    check(tile_requests() == asked + 1, "…and a tile once loaded isn't asked for again")
    check(any(w.text().startswith("0.60 m/px (z18)") for w in imagery_page.findChildren(QLabel)),
          "a result shows its zoom next to its resolution")
    controller.show_image(twins[1].key)
    check(wait_until(lambda: controller._search_previewing() == {twins[1].key}
                     and imagery_page._eyes[twins[1].key].property("on") is True
                     and imagery_page._eyes[twins[0].key].property("on") is not True, 3),
          "the eye that lights up is the one of the zoom whose preview is on")
    controller.show_image(twins[1].key)
    wait_until(lambda: not controller._search_previewing(), 3)
    controller.use_image(twins[0].key)
    check(controller.draft.payload("project-1")["params"]["sourceParams"]["imagerySearch"]["imageIds"] == ["arc-2"]
          and controller.draft.imagery.zoom == 17, "Use on one of them runs on the image id, at its zoom")
    content.go(2)
    controller.render_search_results()
    check(wait_until(lambda: len({b.width() for b in imagery_page._uses}) == 1, 3)
          and {b.text() for b in imagery_page._uses} == {"Use", "Chosen"},
          f"Use and Chosen are one width ({[(b.text(), b.width()) for b in imagery_page._uses]})")
    for twin in twins:
        plugin.services[3].results.remove(twin)
    controller.render_search_results()

    # Draw, as on Start: the drawn polygon is the area here and there
    imagery_page.draw_button.click()
    check(iface.canvas.mapTool() is controller.draw_tool and imagery_page.draw_button.text() == "Drawing…"
          and run.area_buttons["draw"].isChecked(), "Draw in Search starts drawing on the map")
    controller.on_drawn(QgsGeometry.fromRect(QgsRectangle(37.60, 55.74, 37.61, 55.75)))
    check(imagery_page.draw_button.text() == "Draw" and controller.draft.aoi.name.startswith("Mapflow area")
          and combo.currentText() == controller.draft.aoi.name and "1 polygon" in imagery_page.area_text.text(),
          f"…and the drawn polygon becomes the area, in Search too ({combo.currentText()})")
    run.layerChosen.emit(layer.id())
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

    # No collections yet: My imagery still shows in the run form, and offers the upload
    imagery_service = plugin.services[3]
    import mapflow_next.controller as controller_module
    state.no_mosaics = True
    imagery_service.load_mosaics()
    check(wait_until(lambda: not imagery_service.mosaics, 5), "an account without collections")
    controller.refresh_run()
    rows, _selected = controller._imagery_rows(session.status, True)
    mine = next((r for r in rows if r.key == "mosaic"), None)
    check(mine is not None and mine.pick == "Add imagery…"
          and mine.meta == "Upload a GeoTIFF to process your own imagery",
          "without collections, My imagery is still listed, with Add imagery…")
    content.go(0)
    content.open_run()
    wait_until(lambda: False, 0.3)
    add = [b for row in content.run._rows for b in row.findChildren(QPushButton) if b.text() == "Add imagery…"]
    add and add[0].click()
    check(content.current_tab() == 2 and content.imagery.current_tab() == MINE
          and not (controller.mosaic_picker and controller.mosaic_picker.isVisible()),
          "…and with nothing to pick, the button goes to the My imagery tab, where uploads are")
    content.open_run()
    before = controller.draft.imagery
    QTest.mouseClick(content.run._rows[0], Qt.MouseButton.LeftButton)
    check(content.current_tab() == 2 and content.imagery.current_tab() == MINE
          and controller.draft.imagery is before,
          "choosing the row goes there too, and changes nothing else")
    state.no_mosaics = False
    imagery_service.load_mosaics()

    # several GeoTIFFs at once, into one collection; each checked here and by Mapflow first
    from osgeo import gdal
    survey = Path(tempfile.mkdtemp()) / "Harbour survey"
    survey.mkdir()
    tiles = [make_geotiff(f"tile_{n}.tif", folder=survey) for n in (1, 2)]
    picked = {}
    saved_open = controller_module.QFileDialog.getOpenFileNames
    controller_module.QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: (picked["files"], ""))
    try:
        state.uploads.clear()
        picked["files"] = tiles
        controller.upload()
        check(wait_until(lambda: [u[0] for u in state.uploads] == ["create", "image", "image"], 5)
              and state.uploads[0][2] == "Harbour survey"
              and len([r for r in state.requests if r[1] == "/rasters/validate-image-metadata"]) >= 2,
              f"several GeoTIFFs go into one new collection, named after their folder ({state.uploads})")
        check(wait_until(lambda: controller.uploading is None and not imagery_service.uploading, 5),
              "…and the upload finishes")
        validated = [r[2] for r in state.requests if r[1] == "/rasters/validate-image-metadata"][-1]
        ring = (validated.get("footprint") or {}).get("coordinates", [[]])[0]
        check(set(validated) == {"width", "height", "channels", "dtype", "crs", "pixel_size_meters", "footprint",
                                 "file_size_bytes"}
              and validated["crs"] == "EPSG:4326" and validated["channels"] == 3 and validated["dtype"] == "uint8"
              and len(ring) == 5 and ring[0] == ring[-1]
              # 0.0001° at 55.75° N: 6.3 m across, 11.1 m down
              and 6 < validated["pixel_size_meters"][0] < 6.6 and 10.9 < validated["pixel_size_meters"][1] < 11.4,
              f"Mapflow is asked about each image in the shape its check takes ({validated})")

        def refused(files, says):
            state.uploads.clear()
            iface.bar.messages.clear()
            picked["files"] = files
            controller.upload()
            wait_until(lambda: any(says in (m or "") for _l, m in iface.bar.messages), 3)
            return not state.uploads and any(says in (m or "") for _l, m in iface.bar.messages)

        check(refused([make_geotiff("two_bands.tif", bands=2)], "1, 3 or 4"),
              "a GeoTIFF with 2 bands is refused before uploading")
        check(refused([make_geotiff("plain.tif", epsg=None)], "isn't georeferenced"),
              "…and one without a coordinate system")
        check(refused([tiles[0], make_geotiff("utm.tif", epsg=32637)], "another coordinate system"),
              "images in different coordinate systems can't share a collection")
        check(refused([make_geotiff("deep.tif", data_type=gdal.GDT_UInt16)], "must be 8-bit"),
              "an image Mapflow's check refuses isn't uploaded, and its reason is shown")
        check(refused([make_geotiff("depth.tif", bands=3, data_type=gdal.GDT_Float64)], "Mapflow takes uint8"),
              "…and one whose data type the check doesn't take is refused here")
        state.uploads.clear()
        iface.bar.messages.clear()
        picked["files"] = [make_geotiff("grey.tif", bands=1)]
        controller.upload()
        check(wait_until(lambda: [u[0] for u in state.uploads] == ["new"] and controller.uploading is None, 5)
              and any("processed as grayscale" in (m or "") for _l, m in iface.bar.messages),
              f"the check's warnings are shown, and the upload goes on ({state.uploads})")
    finally:
        controller_module.QFileDialog.getOpenFileNames = saved_open

    # the project's GeoTIFF layers: My imagery's "Choose from raster layer", and the Layers panel's menu
    from qgis.core import QgsRasterLayer
    from mapflow_next.qgis_bridge import aoi as aoi_module
    project = QgsProject.instance()
    pier = QgsRasterLayer(make_geotiff("pier.tif"), "Pier 7")
    dock = QgsRasterLayer(make_geotiff("dock.tif"), "Dock 2")
    xyz = QgsRasterLayer("type=xyz&url=https://tile.example.com/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0",
                         "Street tiles", "wms")
    wells = QgsVectorLayer("Point?crs=EPSG:4326", "Wells", "memory")
    harbour = QgsVectorLayer("Polygon?crs=EPSG:4326", "Harbour area", "memory")
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromRect(QgsRectangle(37.60, 55.74, 37.62, 55.75)))
    harbour.dataProvider().addFeatures([feature])
    project.addMapLayers([pier, dock, xyz, wells, harbour])
    page = content.imagery
    listed = []

    def pick(names):
        def fill(dialog):
            items = [dialog.list.item(row) for row in range(dialog.list.count())]
            listed.append([item.text() for item in items])
            for item in items:
                item.setSelected(item.text() in names)
        return fill
    seen = []
    close_modal_later(seen, pick({"Pier 7"}))
    state.uploads.clear()
    page.layer_button.click()
    check(seen == ["LayerPicker"] and sorted(listed[-1]) == ["Dock 2", "Pier 7"],
          f"Choose from raster layers lists only GeoTIFF file layers ({listed})")
    check(wait_until(lambda: [u[:2] for u in state.uploads] == [("new", "Pier 7")] and controller.uploading is None
                     and not imagery_service.uploading, 5),
          f"…and picking one uploads its file as a collection named after the layer ({state.uploads})")
    close_modal_later(seen, pick({"Pier 7", "Dock 2"}))
    state.uploads.clear()
    page.layer_button.click()
    check(wait_until(lambda: [u[0] for u in state.uploads] == ["create", "image", "image"]
                     and controller.uploading is None and not imagery_service.uploading, 5),
          f"…and picking several uploads them all into one new collection ({state.uploads})")

    # drag and drop: layers from the Layers panel (several at once) or .tif files onto My imagery
    from qgis.core import QgsMimeDataUtils
    from qgis.PyQt.QtCore import QMimeData, QPoint, QPointF
    from qgis.PyQt.QtGui import QDragEnterEvent, QDropEvent
    from mapflow_next.qgis_bridge import rasters as rasters_module

    def drag(layers=(), files=()):
        mime = QgsMimeDataUtils.encodeUriList([QgsMimeDataUtils.Uri(x) for x in layers]) if layers else QMimeData()
        if files:
            mime.setUrls([QUrl.fromLocalFile(f) for f in files])
        return mime

    def dropped(mime):          # (file, name), the file as the OS writes it
        return [(os.path.normcase(os.path.normpath(p)), n) for p, n in rasters_module.dropped_geotiffs(mime)]
    pier_file, dock_file, loose = (os.path.normcase(os.path.normpath(p)) for p in (
        rasters_module.geotiff_path(pier), rasters_module.geotiff_path(dock), make_geotiff("loose.tif")))
    found = [dropped(drag([pier, dock, xyz, wells])), dropped(drag(files=[loose, pier_file])),
             dropped(drag([xyz, wells]))]
    check(found == [[(pier_file, "Pier 7"), (dock_file, "Dock 2")], [(loose, "loose"), (pier_file, "pier")], []],
          f"a drag carries the GeoTIFF layers and files in it, and nothing else ({found})")
    card = page.drop.widget
    tiles, two = drag([xyz]), drag([pier, dock])        # kept: an event doesn't own its mime data
    refused = QDragEnterEvent(QPoint(10, 10), Qt.DropAction.CopyAction, tiles, Qt.MouseButton.LeftButton,
                              Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(card, refused)
    taken = QDragEnterEvent(QPoint(10, 10), Qt.DropAction.CopyAction, two, Qt.MouseButton.LeftButton,
                            Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(card, taken)
    check(not refused.isAccepted() and taken.isAccepted() and card.property("dropping") is True,
          "My imagery takes a drag of GeoTIFF layers, outlined, and refuses tile layers")
    state.uploads.clear()
    drop = QDropEvent(QPointF(10, 10), Qt.DropAction.CopyAction, two, Qt.MouseButton.LeftButton,
                      Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(card, drop)
    check(wait_until(lambda: [u[0] for u in state.uploads] == ["create", "image", "image"]
                     and controller.uploading is None and not imagery_service.uploading, 5)
          and card.property("dropping") is False,
          f"…and dropping two layers uploads both into one new collection ({state.uploads})")
    content.go(2)
    page.show_tab(MINE)
    QApplication.setActiveWindow(iface.window)
    page.upload_button.setFocus()
    wait_until(lambda: False, 0.1)
    top = page.scroll.verticalScrollBar().value()
    page.set_upload(0, "Checking…")
    wait_until(lambda: False, 0.2)
    check(page.scroll.verticalScrollBar().value() == top and QApplication.focusWidget() is not page.upload_button,
          f"starting an upload doesn't scroll My imagery down to the collections "
          f"({top} → {page.scroll.verticalScrollBar().value()})")
    page.set_upload(None)
    menus = {layer.name(): iface.layer_menu(layer) for layer in (pier, xyz, wells, harbour)}
    check(menus == {"Pier 7": ["Use as imagery in Mapflow"], "Street tiles": [], "Wells": [],
                    "Harbour area": ["Use as AOI in Mapflow"]},
          f"the Layers panel offers Mapflow's actions on GeoTIFF and polygon layers only ({menus})")
    check(not plugin.aoi_action.icon().isNull() and not plugin.imagery_action.icon().isNull(),
          "…with the Mapflow mark")
    area_before, imagery_before = controller.aoi_layer, controller.draft.imagery
    content.go(2)
    iface.setActiveLayer(harbour)
    plugin.aoi_action.trigger()
    check(controller.draft.aoi is not None and controller.draft.aoi.layer_id == harbour.id()
          and content.stack.currentWidget() is content.run,
          "Use as AOI in Mapflow: the layer becomes the area, and the run form opens")
    state.uploads.clear()
    state.list_uploads = True
    iface.setActiveLayer(pier)
    plugin.imagery_action.trigger()

    def chosen_name():
        choice = controller.draft.imagery
        mosaic = imagery_service.get_mosaic(choice.mosaic_id) if choice and choice.kind == "my_imagery" else None
        return mosaic.name if mosaic else ""

    check(wait_until(lambda: chosen_name() == "Pier 7", 8),
          f"Use as imagery in Mapflow: the layer is uploaded and becomes the imagery ({state.uploads})")
    state.list_uploads = False
    state.extra_mosaics, state.extra_images = [], {}
    controller.draft.imagery = imagery_before
    if area_before is not None:
        controller.set_aoi_layer(area_before)
    project.removeMapLayers([pier.id(), dock.id(), xyz.id(), wells.id(), harbour.id()])
    check(aoi_module.is_polygon_layer(controller.aoi_layer) or area_before is None, "…and the area is put back")
    imagery_service.load_mosaics()
    wait_until(lambda: not imagery_service._mosaics_loading, 5)    # or the check below would ride on this load
    controller.refresh_run()

    # a collection made in Mapflow Web shows up without restarting
    state.extra_mosaics = [{"id": "m-web", "name": "Made in Web", "created_at": "2026-11-13T20:00:00Z",
                            "sizeInBytes": 10, "footprint": None, "rasterLayer": {"tileUrl": "", "tileJsonUrl": ""},
                            "tags": []}]
    imagery_service._mosaics_at = 0
    content.go(2)
    content.imagery.show_tab(MINE)
    content.imagery.tabs.changed.emit(MINE)
    check(wait_until(lambda: imagery_service.get_mosaic("m-web") is not None, 5),
          "opening My imagery asks Mapflow again, so a collection made in Mapflow Web appears")
    check(controller._mosaic_refresh.isActive() and controller._mosaic_refresh.interval() == 30_000,
          "…and the list is asked for every 30 s while the panel is open")
    state.extra_mosaics = []
    imagery_service.load_mosaics()
    wait_until(lambda: not imagery_service.loading_mosaics, 5)

    # many collections: listed 50 at a time, newest first, and searched on the server
    def pages():
        return getattr(state, "mosaic_pages", [])
    state.many_mosaics = 120
    imagery_service.load_mosaics()
    check(wait_until(lambda: len(imagery_service.mosaics) == 50 and imagery_service.mosaics_total > 120, 5)
          and pages()[-1].get("offset") == "0" and pages()[-1].get("limit") == "50"
          and pages()[-1].get("sort") == "created_at" and pages()[-1].get("order") == "desc"
          and "name_contains" not in pages()[-1],
          f"collections come 50 at a time, newest first, of all there are ({len(imagery_service.mosaics)} of "
          f"{imagery_service.mosaics_total}; {pages()[-1] if pages() else None})")
    check("Survey tile 119" in [m.name for m in imagery_service.mosaics]
          and "Survey tile 000" not in [m.name for m in imagery_service.mosaics],
          "…the newest first: the oldest isn't on the first page")
    content.go(2)
    content.imagery.show_tab(MINE)
    wait_until(lambda: False, 0.2)
    more = content.imagery.more_mosaics
    check(more is not None and f"50 of {imagery_service.mosaics_total}" in more.text()
          and content.imagery.mosaics_title.text() == f"Collections · {imagery_service.mosaics_total}",
          f"My imagery says how many there are, and has “Show more” ({more.text() if more else None})")
    first_card = content.imagery.mosaic_list.itemAt(0).widget()
    more.click()
    check(wait_until(lambda: len(imagery_service.mosaics) == 100, 5) and pages()[-1].get("offset") == "50",
          "“Show more” brings the next 50")
    wait_until(lambda: False, 0.2)
    check(content.imagery.mosaic_list.count() == 100 and content.imagery.mosaic_list.itemAt(0).widget() is first_card,
          "…added under the cards already drawn, which stay as they are (no redraw of the whole list)")
    imagery_service.load_mosaics()
    check(wait_until(lambda: not imagery_service.loading_mosaics, 5) and len(imagery_service.mosaics) == 100
          and pages()[-1].get("limit") == "100", "a refresh keeps what “Show more” brought")
    controller.open_mosaic_picker()
    picker = controller.mosaic_picker
    picker.search.setText("tile 007")
    check(wait_until(lambda: [m.name for m in picker.found] == ["Survey tile 007"] and not picker.found_loading, 5)
          and pages()[-1].get("name_contains") == "tile 007",
          f"the collection search asks Mapflow, so it finds a collection on no loaded page ({picker.found})")
    image_name = fixtures.MOSAIC_IMAGES["m-1"][0]
    picker.search.setText(image_name)
    check(wait_until(lambda: "m-1" in [m.id for m in picker.found], 5),
          f"…and finds a collection by the name of an image in it ({image_name})")
    asked = len(pages())
    picker.search.clear()
    check(wait_until(lambda: picker._shown() is picker.mosaics and len(picker.mosaics) == 100, 3)
          and all(p.get("name_contains") for p in pages()[asked:]),
          "clearing the search shows the listing again, and no empty search is sent (Mapflow refuses it)")
    picker.close()
    got = []
    imagery_service._known.pop("m-many-000", None)
    imagery_service.fetch_mosaic("m-many-000", lambda m: got.append(m.name), lambda: got.append("missing"))
    imagery_service.fetch_mosaic("m-gone", lambda m: got.append(m.name), lambda: got.append("missing"))
    check(wait_until(lambda: len(got) == 2, 5) and sorted(got) == ["Survey tile 000", "missing"],
          f"a collection on no loaded page is asked for by id, and a 404 says it is gone ({got})")
    state.many_mosaics = 0
    imagery_service.load_mosaics()
    check(wait_until(lambda: not imagery_service.loading_mosaics and imagery_service.mosaics_total < 50, 5)
          and len(imagery_service.mosaics) == imagery_service.mosaics_total, "…and back to a few collections")

    # icons: the single-stripe mark, white on a dark theme; every icon has an exact 1× drawing
    from mapflow_next.ui import icons as icon_module
    from qgis.PyQt.QtCore import QSize as Size
    light, dark = icon_module.app_icon(False), icon_module.app_icon(True)
    check(not light.isNull() and not dark.isNull() and plugin.action.icon().cacheKey() != 0,
          "the toolbar icon is the SVG mark with one stripe")
    dark_file = Path(tempfile.gettempdir()) / "mapflow_next_icons" / "mark-simple-dark.svg"
    check(dark_file.exists() and "#FFFFFF" in dark_file.read_text() and "#1A234B" not in dark_file.read_text(),
          "on a dark QGIS theme the mark is white")
    eye_icon = icon_module.icon("eye", "#000000", 16)
    check(Size(16, 16) in eye_icon.availableSizes() and Size(32, 32) in eye_icon.availableSizes(),
          f"icons are drawn at 1× and 2× from their SVG ({eye_icon.availableSizes()})")

    # My imagery: image counts, no empty space, the collection picker
    content.go(2)
    content.imagery.show_tab(MINE)
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
    manage = next(b for b in picker.findChildren(QPushButton) if b.text().startswith("Manage collections"))
    manage.click()
    check(links.opened[-1:] == ["https://app.mapflow.ai/my-data"], f"“Manage collections” opens My data in Mapflow "
                                                                   f"Web ({links.opened[-1:]})")

    # adding imagery from My imagery: into the selected collection, or into a new one
    check(picker.current == "m-1" and "added to “Drone survey March”" in picker.target.text(),
          "the collection opened is selected, and uploads go into it")
    picked = {"files": [make_geotiff("extra.tif")]}
    saved_open = controller_module.QFileDialog.getOpenFileNames
    controller_module.QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: (picked["files"], ""))
    try:
        state.uploads.clear()
        images_asked = getattr(state, "image_requests", 0)
        picker.upload_button.click()
        check(wait_until(lambda: [u[:2] for u in state.uploads] == [("image", "m-1")]
                         and controller.uploading is None and not imagery_service.uploading, 5),
              f"Upload a GeoTIFF adds the file to the selected collection, without a new one ({state.uploads})")
        asked = [r[2] for r in state.requests if r[1] == "/rasters/validate-image-metadata"][-1]
        check(asked.get("mosaic_id") == "m-1", "…and Mapflow checks the file fits that collection (mosaic_id)")
        check(wait_until(lambda: getattr(state, "image_requests", 0) > images_asked, 3)
              and "Uploaded to “Drone survey March”" in picker.upload_note.text.text(),
              "…its image list is asked for again, and the window says where the file went")

        # a file the collection already has: the user decides, before anything is sent
        asked_dup, answer = [], {"value": "skip"}
        saved_ask = controller._ask_duplicate
        controller._ask_duplicate = lambda files, where: (asked_dup.append((files, where)), answer["value"])[1]
        try:
            wait_until(lambda: "m-1" not in imagery_service._images_loading and "m-1" in imagery_service.images, 5)
            state.uploads.clear()
            picked["files"] = [make_geotiff("north.tif")]
            picker.upload_button.click()
            check(asked_dup == [(["north.tif"], "Drone survey March")]
                  and "nothing new" in picker.upload_note.text.text() and not state.uploads,
                  f"a file the collection already has is asked about first; Skip sends nothing ({asked_dup})")
            answer["value"] = "upload"
            picker.upload_button.click()
            check(wait_until(lambda: [u[:2] for u in state.uploads] == [("image", "m-1")]
                             and not imagery_service.uploading, 5),
                  f"…Upload again adds it anyway (allow_duplicate) ({state.uploads})")
            # Mapflow finds one the plugin's list didn't know about: the same question, then a retry
            wait_until(lambda: "m-1" not in imagery_service._images_loading, 5)
            imagery_service.images.pop("m-1", None)
            state.uploads.clear()
            asked_dup.clear()
            picked["files"] = [make_geotiff("south.tif")]
            picker.upload_button.click()
            check(wait_until(lambda: [u[0] for u in state.uploads] == ["duplicate", "image"]
                             and not imagery_service.uploading, 5)
                  and asked_dup == [(["south.tif"], "Drone survey March")],
                  f"when Mapflow refuses a repeated file, the user is asked, and Upload again retries it "
                  f"({state.uploads})")
            wait_until(lambda: "m-1" not in imagery_service._images_loading, 5)
            imagery_service.images.pop("m-1", None)
            state.uploads.clear()
            answer["value"] = "cancel"
            picked["files"] = [make_geotiff("centre.tif")]
            picker.upload_button.click()
            check(wait_until(lambda: not imagery_service.uploading and controller.uploading is None, 5)
                  and [u[0] for u in state.uploads] == ["duplicate"]
                  and "“centre.tif” is already in this collection" in picker.upload_note.text.text()
                  and "existing_image_id" not in picker.upload_note.text.text(),
                  f"…Cancel stops, with a readable reason ({picker.upload_note.text.text()})")
        finally:
            controller._ask_duplicate = saved_ask
        wait_until(lambda: "m-1" not in imagery_service._images_loading, 5)
        picker._row_clicked("m-1")
        check(picker.current is None and "new collection" in picker.target.text()
              and not picker.use_all.isVisible(),
              "clicking the selected collection again clears the selection: uploads make a new collection")
        state.uploads.clear()
        state.list_uploads = True
        picked["files"] = [make_geotiff("Jetty.tif")]
        picker.upload_button.click()
        check(wait_until(lambda: [u[:2] for u in state.uploads] == [("new", "Jetty")]
                         and picker.current is not None and imagery_service.get_mosaic(picker.current).name == "Jetty",
                         8),
              f"…and once the new collection is listed, it's selected in the window ({state.uploads})")
    finally:
        controller_module.QFileDialog.getOpenFileNames = saved_open

    # Create collection: a name and tags, then it's selected, ready for uploads
    from mapflow_next.ui.collection_dialog import CollectionDialog
    dialog = CollectionDialog()
    check(not dialog.create.isEnabled(), "a new collection needs a name: Create waits for it")
    dialog.name.setText("Coastline 2026")
    for tag in ("coast", "Coast", "2026"):
        dialog.tag.setText(tag)
        QTest.keyClick(dialog.tag, Qt.Key.Key_Return)
    check(dialog.create.isEnabled() and dialog.values() == ("Coastline 2026", ["coast", "2026"])
          and dialog.result() == 0,
          f"tags are added with Enter or +, once each, and Enter doesn't create yet ({dialog.values()})")
    shot(dialog, "19-new-collection", QSize(460, 300))
    dialog.close()

    class FakeCollectionDialog:
        def __init__(self, *_a, **_k):
            pass

        def exec(self):
            return 1

        def values(self):
            return "Coastline 2026", ["coast", "2026"]

    saved_dialog = controller_module.CollectionDialog
    controller_module.CollectionDialog = FakeCollectionDialog
    try:
        state.uploads.clear()
        picker.create_button.click()
        check(wait_until(lambda: picker.current is not None
                         and imagery_service.get_mosaic(picker.current).name == "Coastline 2026", 5)
              and state.created_tags.get(picker.current) == ["coast", "2026"],
              "Create collection makes it in Mapflow with its tags, and selects it in the window")
    finally:
        controller_module.CollectionDialog = saved_dialog

    # ⋯ menus: delete an image (the collection stays, even empty), delete a collection; both asked first
    confirms, answer_del = [], {"value": False}
    saved_confirm, imagery_kept = controller._confirm_delete, controller.draft.imagery
    controller._confirm_delete = lambda title, text, detail: (confirms.append((title, text, detail)),
                                                              answer_del["value"])[1]
    try:
        jetty = next(m for m in imagery_service.mosaics if m.name == "Jetty")
        image_id = f"{jetty.id}-i0"
        picker.open_collection(jetty.id)
        check(wait_until(lambda: len(picker._thumbs) == 1, 5), "the new collection shows its uploaded image")
        menu = picker.image_menu(jetty.id, image_id)
        check(picker.findChild(QToolButton, f"more:{image_id}") is not None
              and [a.text() for a in menu.actions()] == ["Delete from the collection…"],
              "each image has a ⋯ menu with Delete (no extra large buttons)")
        menu.actions()[0].trigger()
        check(not state.deleted_images and confirms[-1][1] == "Delete “centre.tif” from “Jetty”?",
              f"deleting an image asks first; Cancel deletes nothing ({confirms[-1:]})")
        answer_del["value"] = True
        controller.draft.imagery = controller_module.ImageryChoice.from_mosaic(jetty.id, "Jetty", image_id,
                                                                               "centre.tif")
        picker.image_menu(jetty.id, image_id).actions()[0].trigger()
        check(wait_until(lambda: image_id in state.deleted_images and not picker._thumbs
                         and any("no images yet" in w.text() for w in picker.findChildren(QLabel) if w.isVisible()), 5)
              and "stays, empty" in confirms[-1][2]
              and imagery_service.get_mosaic(jetty.id) is not None and jetty.id not in state.deleted_mosaics,
              "deleting the last image leaves the collection in place, empty, and says so")
        check(controller.draft.imagery is None, "…and the run form no longer uses the deleted image")
        menu = picker.collection_menu()
        check(picker.more_button.isVisible() and [a.text() for a in menu.actions()] == ["Delete collection…"],
              "the selected collection has a ⋯ menu with Delete collection")
        controller.draft.imagery = controller_module.ImageryChoice.from_mosaic(jetty.id, "Jetty")
        menu.actions()[0].trigger()
        check(wait_until(lambda: jetty.id in state.deleted_mosaics and imagery_service.get_mosaic(jetty.id) is None
                         and picker.current is None and jetty.id not in picker._rows, 5)
              and confirms[-1][1] == "Delete “Jetty”?" and controller.draft.imagery is None,
              "Delete collection removes it from Mapflow and from the list, and the run form drops it")
    finally:
        controller._confirm_delete = saved_confirm
        controller.draft.imagery = imagery_kept
    state.list_uploads = False
    state.extra_mosaics, state.extra_images = [], {}
    imagery_service.load_mosaics()
    wait_until(lambda: not imagery_service._mosaics_loading, 5)
    picker.set_upload(None)
    picker.open_collection(None)
    shot(picker, "13b-my-imagery-none-selected", QSize(820, 600))
    picker.open_collection("m-1")
    wait_until(lambda: len(picker.previews) == 3, 5)
    shot(picker, "13-my-imagery-picker", QSize(820, 600))
    picker.chosen.emit("m-1", "m-1-i1")

    def previews(name):
        return [x for x in QgsProject.instance().mapLayersByName(f"My imagery · {name}")
                if x.customProperty("mapflow_next/preview") == "mosaic:m-1"]

    check(wait_until(lambda: len(previews("Drone survey March")) == 1, 5),
          "choosing My imagery puts the collection on the map")
    check(wait_until(lambda: next((b for row in content.run._rows for b in row.findChildren(QToolButton)
                                   if b.toolTip() == "Hide the preview"), None) is not None, 3),
          "…and the eye shows its preview as on")
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
    gap = run.rename_button.geometry().left() - run.name.geometry().right()
    check(0 <= gap <= 12, f"the pencil sits right after the name, not at the row's end ({gap} px)")
    from qgis.PyQt.QtCore import QEvent
    from qgis.PyQt.QtGui import QFocusEvent
    # What the field asks the layout for (the pixels depend on whether the page is laid out at this point)
    resting = run.name.sizeHint().width()
    QApplication.sendEvent(run.name, QFocusEvent(QEvent.Type.FocusIn))
    wait_until(lambda: False, 0.1)
    check(run.rename_button.isHidden() and run.name.sizeHint().width() > 1000
          and run.rename_button.sizePolicy().retainSizeWhenHidden(),
          f"while the name is edited the field asks for the whole row and the pencil steps aside, keeping its "
          f"place so the form below doesn't move ({resting} → {run.name.sizeHint().width()} px asked)")
    QApplication.sendEvent(run.name, QFocusEvent(QEvent.Type.FocusOut))
    wait_until(lambda: False, 0.1)
    check(not run.rename_button.isHidden() and run.name.sizeHint().width() == resting,
          "…and comes back right after it")
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
    content.imagery.show_tab(MINE)
    check(not picker.isVisible() and "centre.tif" in content.run._rows[0].meta.text(),
          "the run form shows the chosen image")
    pick_button = next(b for b in content.run._rows[0].findChildren(QPushButton) if b.text() == "Choose…")
    pick_button.click()
    check(picker.isVisible() and picker.current == "m-1", "“Choose…” on My imagery opens the picker at the chosen "
                                                          "collection")
    picker.chosen.emit("m-1", "")
    check(controller.draft.imagery.image_ids == [] and controller.draft.imagery.mosaic_id == "m-1",
          "“Use the whole collection” processes the whole collection")
    wait_until(lambda: False, 0.3)
    check(len(previews("Drone survey March")) == 1, "choosing the same collection again doesn't add it twice")
    mine = next(b for b in content.imagery.findChildren(QPushButton) if b.text().startswith("Manage collections"))
    mine.click()
    check(links.opened[-1:] == ["https://app.mapflow.ai/my-data"], "…as does the link under My imagery")

    # an empty collection can't be chosen, and asking for its images doesn't go round in circles
    state.extra_mosaics = [{"id": "m-empty", "name": "Empty upload", "created_at": "2026-11-12T10:00:00Z",
                            "sizeInBytes": 0, "footprint": None,
                            "rasterLayer": {"tileUrl": "", "tileJsonUrl": ""}, "tags": []}]   # no image count
    imagery_service.load_mosaics()
    check(wait_until(lambda: imagery_service.get_mosaic("m-empty") is not None, 5), "a new empty collection is listed")
    before = controller.draft.imagery
    asked = getattr(state, "image_requests", 0)
    content.imagery.useMosaic.emit("m-empty")
    wait_until(lambda: False, 1.5)
    asked = getattr(state, "image_requests", 0) - asked
    check(controller.draft.imagery is before and asked <= 2,
          f"using an empty collection is refused, and its image list is asked for once ({asked} requests)")
    check(any("has no images" in (m or "") for _l, m in iface.bar.messages[-3:]), "…with a message that says why")
    picker.chosen.emit("m-empty", "")
    check(controller.draft.imagery is before, "the picker can't choose it either")
    refused = [m for level, m in iface.bar.messages if "has no images" in (m or "")]
    check(any(level == Qgis.MessageLevel.Critical for level, m in iface.bar.messages if "has no images" in (m or ""))
          and iface.bar.widgets and iface.bar.widgets[-1].findChildren(QPushButton)[-1].text() == "Mapflow Web",
          "…the message bar shows it as an error, with a button to Mapflow Web")
    expect_critical(iface, "has no images", "…the test expects these error messages (an empty collection is refused)",
                    count=len(refused))
    # chosen another way (a scenario's default, Run again): the run form says it, and so does the message bar, once
    controller.draft.imagery = controller_module.ImageryChoice.from_mosaic("m-empty", "Empty upload")
    controller.refresh_run()
    controller.refresh_run()
    again = [m for _l, m in iface.bar.messages if "has no images" in (m or "")]
    check(len(again) == len(refused) + 1, f"an empty collection in the run form is named in the message bar once "
                                          f"({len(again) - len(refused)} messages)")
    expect_critical(iface, "has no images", "…the test expects that error message too (the run form's collection)",
                    count=1)
    controller.draft.imagery = before
    controller.refresh_run()
    state.extra_mosaics = []
    imagery_service.load_mosaics()
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
    cached = plugin.services[3].images.get("m-1")
    check(cached is None or len(cached) == len(fixtures.MOSAIC_IMAGES["m-1"]),
          f"…without caching that one image as the collection's whole image list ({cached})")

    # Run again on catalog imagery restores the image; imagery it can't restore is left for the user to choose
    from mapflow_next.core.models import Processing as ProcessingModel
    for pid, source in (("cat-1", {"imagerySearch": {"dataProvider": "Maxar", "zoom": "18",
                                                     "imageIds": ["10300100ABCDEF01"]}}),
                        ("custom-1", {"userDefined": {"sourceType": "XYZ", "url": "https://x/{z}/{x}/{y}"}})):
        item = fixtures.processing_json(pid, "OK", 100, name=f"Run {pid}")
        item["params"] = {"sourceParams": source}
        processings.items.insert(0, ProcessingModel.from_api(item))
    controller.draft.imagery = controller_module.ImageryChoice.from_mosaic("m-1", "Drone survey March")
    iface.bar.messages.clear()
    content.processings.duplicate.emit("cat-1")
    check(controller.draft.imagery is not None and controller.draft.imagery.kind == "catalog"
          and controller.draft.imagery.image_ids == ["10300100ABCDEF01"],
          "“Run again” on a catalog image chooses the same image, not the imagery chosen before")
    content.processings.duplicate.emit("custom-1")
    controller.on_status(session.status)
    check(controller.draft.imagery is None
          and any("Choose the imagery" in (m or "") for _l, m in iface.bar.messages),
          "…imagery it can't restore stays empty, with a message, and no default fills it in")
    # …and a change of the account status in that state is not an error
    before = len(iface.bar.messages)
    with state.lock:
        state.status = dict(fixtures.STATUS, remainingCredits=900)
    check(wait_until(lambda: (session.refresh_status(), session.status.remaining_credits == 900)[1], 5),
          "a changed balance is polled while the form has no imagery")
    check(controller.draft.imagery is None and controller._imagery_to_choose
          and not any(level == Qgis.MessageLevel.Critical for level, _m in iface.bar.messages[before:]),
          "…and it raises nothing, shows no Critical message, and no default imagery fills the form")
    with state.lock:
        state.status = None
    check(wait_until(lambda: (session.refresh_status(), session.status.remaining_credits == 1240)[1], 5),
          "…the original balance is restored for the next checks")
    processings.items = [p for p in processings.items if p.id not in ("cat-1", "custom-1")]

    # duplicate → run again: the area comes from Mapflow (GET /processings/{id}/aois answers a list)
    content.processings.duplicate.emit("old-1")
    check(controller.draft.aoi is None, "until Mapflow sends the processing's area, the form has none (not the "
                                        "previous one)")
    check(wait_until(lambda: controller.draft.aoi is not None and controller.draft.aoi.name.startswith("Area ·"), 5),
          "Run again restores the processing's area as a layer")
    check(any(r[1] == "/processings/old-1/aois" for r in state.requests)
          and controller.aoi_layer.featureCount() == 1 and controller.draft.aoi.area_km2 > 0,
          "…downloaded from Mapflow, so it works when the original layer is gone")

    # an empty area layer, removed: the form forgets it (its object is gone), and another area can be chosen
    empty = QgsVectorLayer("Polygon?crs=EPSG:4326", "Empty area", "memory")
    QgsProject.instance().addMapLayer(empty)
    restored = controller.aoi_layer
    controller.set_aoi_layer(empty)
    QgsProject.instance().removeMapLayer(empty.id())
    check(controller.aoi_layer is None, "removing an empty area layer clears it from the form")
    controller.set_aoi_layer(restored)
    check(controller.aoi_layer is restored and controller.draft.aoi is not None, "…and another area can be chosen")

    # area plans: the usage shown is the area that is processed (inside My imagery), not the whole area
    import dataclasses
    from mapflow_next.core.models import BillingType
    area_plan = dataclasses.replace(session.status, billing=BillingType.area, remaining_area_km2=100.0)
    whole = controller.draft.aoi
    clipped = dataclasses.replace(whole, area_km2=whole.area_km2 / 4)
    saved_coverage = controller.draft.coverage
    controller.draft.coverage = type("Coverage", (), {"overlaps": True, "clipped": clipped})()
    view = controller._cost_view(area_plan)
    check(view.value == controller_module.formatting.km2(clipped.area_km2)
          and controller_module.formatting.km2(100.0 - clipped.area_km2) in view.balance,
          f"an area plan shows the processed (clipped) area and what's left after it ({view.value}, {view.balance})")
    controller.draft.coverage = saved_coverage

    # the processings list follows the server: a page smaller than asked for is the whole list
    from mapflow_next.services.processings import _merge
    one, two, three = (ProcessingModel.from_api(fixtures.processing_json(f"m{n}", "OK", 100)) for n in (1, 2, 3))
    check(_merge([], [one, two], complete=True) == [] and _merge([one], [one, two, three], complete=True) == [one]
          and _merge([one], [one, two, three], complete=False) == [one, two, three],
          "a refresh drops processings deleted elsewhere, down to the last one; a full page keeps the older ones")

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
    check(wait_until(lambda: controller.pinned_projects() == ["project-3"], 3),
          f"a project starred in Mapflow Web is pinned here ({controller.pinned_projects()})")
    pin_target = next(t for t in projects_window.tiles if t.project.id == "project-30")
    pin_target.pin_button.click()
    check(projects_window.tiles[0].project.id == "project-30"
          and controller.pinned_projects() == ["project-30", "project-3"],
          "a pinned project moves to the top and stays pinned")
    check(wait_until(lambda: "project-30" in state.starred, 3)
          and any(r[0] == "POST" and r[1] == "/projects/project-30/starred" for r in state.requests),
          "pinning stars the project in Mapflow (POST /projects/{id}/starred), so Mapflow Web shows it too")
    unpin = next(t for t in projects_window.tiles if t.project.id == "project-3")
    unpin.pin_button.click()
    check(wait_until(lambda: "project-3" not in state.starred, 3) and controller.pinned_projects() == ["project-30"],
          "unpinning unstars it (DELETE /projects/{id}/starred)")
    projects_window.search.setText("harb")
    check(wait_until(lambda: [p.id for p in projects_window.results] == ["project-2"], 5)
          and [r for r in state.requests if r[1] == "/projects/page"][-1][2].get("filter") == "harb",
          "searching filters projects by name on the server")
    links.opened.clear()
    projects_window.tiles[0].share_button.click()
    check(links.opened == ["https://app.mapflow.ai/projects/project-2"],
          f"the share icon opens that project in Mapflow Web ({links.opened})")
    share = [b for b in projects_window.findChildren(QPushButton) if b.text().startswith("Share project in Mapflow")]
    links.opened.clear()
    share and share[0].click()
    check(links.opened == [f"https://app.mapflow.ai/projects/{session.project.id}"],
          f"“Share project in Mapflow Web” opens the current project there ({links.opened})")
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
    chips = content.processings.chip_buttons
    check(chips["all"].text() == "All 70", f"All counts every processing in the project ({chips['all'].text()!r})")
    empty = next((k for k in ("running", "attention", "done") if not content.processings.counts()[k]), None)
    if empty:
        chips[empty].click()
    else:
        content.processings.search.setText("no processing has this name")
    check(content.processings.more_button is None and content.processings.empty.isVisibleTo(content.processings)
          and "latest 30 of 70" in content.processings.empty_text.text(),
          f"a filter that matches nothing offers no “Show more” and says what it looked through "
          f"({content.processings.empty_text.text()!r})")
    content.processings.search.setText("")
    chips["all"].click()
    check(content.processings.more_button is not None, "…and All brings “Show more” back")
    content.processings.more_button.click()
    check(wait_until(lambda: len(processings.items) == 60, 5), "the next page appends 30 more")
    check(chips["all"].text() == "All 70", "loading more pages leaves the All count alone")
    content.processings.more_button.click()
    check(wait_until(lambda: len(processings.items) == 70 and content.processings.more_button is None, 5),
          "the last page loads and “Show more” goes away")

    # delete: gone from the list as soon as Mapflow confirms, even with a refresh already on its way
    import mapflow_next.controller as controller_module
    from qgis.PyQt.QtWidgets import QMessageBox
    saved_question = controller_module.QMessageBox.question
    controller_module.QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
    try:
        processings.refresh(LOAD)                     # a list request in flight, sent before the deletion
        content.processings.delete.emit("h-05")
        check(wait_until(lambda: processings.get("h-05") is None and processings.total == 69, 5)
              and not any(card.processing.id == "h-05"
                          for card in content.processings.findChildren(QWidget) if hasattr(card, "processing")
                          and card.isVisibleTo(content.processings)),
              "a deleted processing leaves the list at once")
        processings.refresh(LOAD)
        wait_until(lambda: False, 0.8)
        check(processings.get("h-05") is None and chips["all"].text() == "All 69",
              "…and doesn't come back with the next refresh")
    finally:
        controller_module.QMessageBox.question = saved_question
    check(len({p.id for p in processings.items}) == len(processings.items) == 69, "no processing is listed twice")
    shot(content, "15-processings-paged", QSize(400, 880))
    processings.refresh(LOAD)
    check(wait_until(lambda: not processings._loading, 5) and len(processings.items) == 69,
          "polling keeps the older pages in the list")

    # ---------- a new project, from the projects window ----------
    controller.open_projects()
    projects_window = controller.projects_dialog
    new = [b for b in projects_window.findChildren(QPushButton) if b.text() == "New project"]
    check(new and new[0].isVisible(), "the projects window has New project")
    seen = []

    def name_it(dialog):
        check(not dialog.save.isEnabled() and dialog.save.text() == "Create",
              "Create stays disabled until the project has a name")
        dialog.name.setText("Coastal survey 2026")
        dialog.description.setPlainText("Buildings along the coast")
    close_modal_later(seen, name_it)
    new[0].click()
    check(seen == ["RenameDialog"] and wait_until(lambda: session.project.name == "Coastal survey 2026", 5),
          "New project asks for a name and opens the created project")
    created = [r for r in state.requests if r[0] == "POST" and r[1] == "/projects"]
    check(created and created[-1][2] == {"name": "Coastal survey 2026", "description": "Buildings along the coast"},
          "…created with POST /projects {name, description}")
    check(not projects_window.isVisible() and session.project.id.startswith("project-new"),
          "the projects window closes on the new project")
    session.select_project("project-2")
    wait_until(lambda: session.project.id == "project-2", 5)

    check_failed_requests(iface, plugin, state)
    check_upload_timeout(iface, plugin, state)

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

    late = plugin.layers.picture_on_footprint(mock_server.PNG, box(37.60), "Preview · before unload", "../escape-3")
    plugin.layers.add(late, position=0, preview="catalog:escape-3")
    check(any(str(session_folder) in x.source() for x in QgsProject.instance().mapLayers().values())
          and session_folder.exists(), "a preview is still on the map and its folder is there before the unload")
    plugin.unload()
    check(not session_folder.exists() and plugin.layers is None
          and not any(x.source().startswith(str(session_folder)) for x in QgsProject.instance().mapLayers().values()),
          "unload removes the session folder and the preview layers that point into it")
    closed = MapLayers(iface)
    first = closed.temp_folder()
    closed.close()
    closed.close()
    check(first is not None and not first.exists() and closed.temp_folder() is None
          and closed.preview_path("img-1", ".png") is None
          and closed.picture_on_footprint(mock_server.PNG, box(37.60), "late", "img-1") is None,
          "closing the layers twice is harmless, and a preview that comes after it is not written")
    check(wait_until(lambda: not iface.window.findChildren(QToolBar, "MapflowToolbar"), 3)
          and not any(iface.menu_actions.values()), "unload removes the Mapflow toolbar and the menu")
    from mapflow_next.core import guard
    shown = len(iface.bar.messages)
    guard.report(ValueError("late"), "after unload")
    check(len(iface.bar.messages) == shown, "after unload the guard has no reporter: nothing reaches the bar")
    server.shutdown()
    APP.processEvents()                                   # log lines can arrive from another thread
    unexpected = iface.bar.ledger.unexpected()
    check(not unexpected, f"no Critical message the test did not expect ({len(unexpected)})")
    for line in unexpected:
        print("FAIL unexpected Critical message " + line.replace("\n", " | "), flush=True)
    failed = [text for ok, text in CHECKS if not ok]
    print(f"\n{len(CHECKS) - len(failed)}/{len(CHECKS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    code = main()
    os._exit(code)
