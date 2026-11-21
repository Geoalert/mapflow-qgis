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
import weakref
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .qgis_env import FakeIface, start_qgis, wait_until

APP = start_qgis()

from qgis.PyQt.QtCore import QCoreApplication, QEvent, QObject, QSize, Qt, QTimer, QUrl, pyqtSlot  # noqa: E402
from qgis.PyQt.QtGui import QDesktopServices, QPainter  # noqa: E402
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
from mapflow_next.ui.widgets import RangeSlider  # noqa: E402

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


class MailRecorder(UrlRecorder):
    """Takes `mailto:` links instead of the mail program. Keeps each link as it would be sent (encoded)."""

    @pyqtSlot(QUrl)
    def handle(self, url):
        self.opened.append(url.toString(QUrl.ComponentFormattingOption.FullyEncoded))


MAIL = MailRecorder()


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


def make_geotiff(name, bands=3, epsg=4326, data_type=None, folder=None, size=4):
    """A tiny georeferenced GeoTIFF, `size` pixels wide and 4 high."""
    from osgeo import gdal, osr
    folder = folder or tempfile.mkdtemp()
    path = str(Path(folder) / name)
    raster = gdal.GetDriverByName("GTiff").Create(path, size, 4, bands, data_type or gdal.GDT_Byte)
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


def report_buttons(iface):
    """The texts of the buttons on the newest message-bar widget."""
    return [b.text() for b in iface.bar.widgets[-1].findChildren(QPushButton)] if iface.bar.widgets else []


def press_report(iface, comment):
    """Press "Send a report" on the newest Critical line, type `comment`, press Send and Copy. Returns what the
    dialog showed, what Send opened, what Copy put on the clipboard, and the type of the modal that was open."""
    from urllib.parse import parse_qs
    button = next(b for b in iface.bar.widgets[-1].findChildren(QPushButton) if b.text() == "Send a report")
    seen, got = [], {}
    QApplication.clipboard().clear()
    sent = len(MAIL.opened)

    def fill(dialog):
        got["summary"] = dialog.summary_label.text()
        got["view"], got["read_only"] = dialog.report_view.toPlainText(), dialog.report_view.isReadOnly()
        dialog.comment.setPlainText(comment)
        dialog.send()
        dialog.copy()
        got["text"] = dialog.report_text()
        got["clipboard"] = QApplication.clipboard().text()
        got["dialog"] = dialog
    close_modal_later(seen, fill)
    button.click()
    mails = MAIL.opened[sent:]
    got["mails"] = mails
    got["modal"] = seen
    got["mail_body"] = parse_qs(urlsplit(mails[0]).query).get("body", [""])[0] if mails else ""
    got["mail_to"] = mails[0].split("?", 1)[0] if mails else ""
    return got


def check_the_report(iface, plugin, text, expect_request, comment):
    """spec/006 § The report dialog, for the report of the Critical line that just appeared."""
    http = plugin.services[0]
    check(report_buttons(iface) == ["Send a report"] and QApplication.activeModalWidget() is None,
          f"{text}: the Critical line has a Send a report button, and no dialog is open until it is pressed "
          f"({report_buttons(iface)})")
    got = press_report(iface, comment)
    body = got["text"]
    check(got["modal"] == ["ReportDialog"], f"{text}: the button opens the report dialog ({got['modal']})")
    check(got["summary"].startswith("ValueError: boom") and "\n" not in got["summary"],
          f"{text}: the dialog shows a one-line summary ({got['summary']!r})")
    check(got["read_only"] and got["view"] in body and body.startswith(comment),
          f"{text}: the technical text is read-only, and the comment is above it")
    check("ValueError: boom" in body and "Traceback" in body and "Plugin: " in body and "QGIS: " in body
          and "Qt: " in body and "OS: " in body and "Environment: " in body,
          f"{text}: the report has the exception, the traceback, the versions, the system and the environment")
    if expect_request:
        check(f"Request: GET {http.url_for('user/status')}\n" in body and "HTTP status: 200" in body
              and "Response body:" in body, f"{text}: the report names the request, its status and the answer")
    else:
        check("Request:" not in body and "HTTP status" not in body, f"{text}: the report has no request lines")
    request_line = next((line for line in body.splitlines() if line.startswith("Request:")), "")
    check("Authorization" not in body and not (http.bearer and http.bearer in body)
          and mock_server.TOKEN not in body and "?" not in request_line,
          f"{text}: the report has no Authorization header, no token and no query string")
    check(len(got["mails"]) == 1 and got["mail_to"] == f"mailto:{config.SUPPORT_EMAIL}"
          and got["mail_body"] == body.replace("\n", "\r\n"),
          f"{text}: Send opens one mailto: link to Mapflow support with the same text ({got['mails'][:1]})")
    check(got["clipboard"] == body, f"{text}: Copy puts the same text on the clipboard")
    check(wait_until(lambda: all_deleted([got["dialog"]]), 3) and plugin.report_dialog is None,
          f"{text}: the dialog is gone after it is closed")


def check_the_guard(iface, plugin, api_url, settings, state):
    """spec/006 § The guard: `Http` tells a body that is not JSON from a callback that raises, a request ends
    in one outcome, a result that cannot be placed leaves no "loading" flag, and a timer reaches the reporter."""
    from mapflow_next.core.guard import guarded
    from mapflow_next.core.models import Processing
    from mapflow_next.config import FILES, TILES
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
    check_the_report(iface, plugin, "report of a failing on_success", True, "I opened the plugin and waited.")

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
    check_the_report(iface, plugin, "report of a failing timer callback", False, "Nothing was running.")
    check_no_report_for_connectivity(iface, plugin, state)


def check_no_report_for_connectivity(iface, plugin, state):
    """spec/006 § The report dialog: offline, a proxy error, a timeout, 403 and 5xx are message tier. They never
    reach the guard, so no Critical line and no "Send a report" button comes of them."""
    from mapflow_next.api import http as http_module
    http = plugin.services[0]
    seen_lines, seen_widgets = len(iface.bar.ledger.unexpected()), len(iface.bar.widgets)
    kinds = {}
    saved_timeout = http_module.TIMEOUT_S
    try:
        for name, what in (("403", 403), ("503", 503), ("a closed connection", "drop"), ("a timeout", "hang")):
            state.heal()
            state.hang_seconds = 3
            http_module.TIMEOUT_S = 1 if what == "hang" else saved_timeout
            state.fail("GET", r"/user/status", what)
            errors = []
            http.get("user/status", on_error=errors.append)
            wait_until(lambda: errors, 8)
            kinds[name] = [e.kind for e in errors]
        state.heal()
        errors = []
        http.get("http://127.0.0.1:1/unreachable", on_error=errors.append)      # nothing listens: refused
        wait_until(lambda: errors, 8)
        kinds["a refused connection"] = [e.kind for e in errors]
    finally:
        http_module.TIMEOUT_S = saved_timeout
        state.heal()
    check(kinds == {"403": ["forbidden"], "503": ["server"], "a closed connection": ["server"],
                    "a timeout": ["timeout"], "a refused connection": ["server"]},
          f"connectivity failures end as expected errors ({kinds})")
    wait_until(lambda: False, 0.3)
    check(len(iface.bar.ledger.unexpected()) == seen_lines and plugin.report_dialog is None
          and not any(b.text() == "Send a report" for w in iface.bar.widgets[seen_widgets:]
                      for b in w.findChildren(QPushButton)),
          "…and none of them gives a Critical line or a Send a report button")


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

    # sign-out, sign-in, the same processing added again while the old task is still stopping: the old task
    # removes its own files, not the new download or what the new conversion makes of it
    started.clear()
    stopped.clear()

    def held_until(release, then=None):
        """Waits for the cancel (or, with `then`, for `release`), and then returns, as a task does that stops late."""
        def held(job, is_canceled, feedback, *rest):
            job.work.parent.mkdir(parents=True, exist_ok=True)
            job.work.write_bytes(b"partial")
            started.append(job)
            while not release.is_set():
                time.sleep(0.02)
            if then is not None:
                return then(job, is_canceled, feedback, *rest)
            stopped.append(job)
        return held

    release_old, release_new = threading.Event(), threading.Event()
    try:
        late = scenario("conv-late", held_until(release_old))
        check(wait_until(lambda: started, 5), "a conversion runs when the user signs out")
        old_task = results._tasks.get(late.id)
        results.reset()
        conversion.convert_geojson = held_until(release_new, original)
        again_late = processing_done("conv-late")
        results.add_to_map(again_late)
        check(wait_until(lambda: len(started) == 2, 10), "…the same processing is added again after sign-in")
        new_job = started[1]
        check(new_job.target != started[0].target and new_job.fallback != started[0].fallback,
              f"…its output names are not the ones of the old task ({started[0].target.name}, "
              f"{new_job.target.name})")
        check(new_job.geojson != started[0].geojson and new_job.geojson.exists(),
              f"…its download has a file of its own ({started[0].geojson.name}, {new_job.geojson.name})")
        release_old.set()
        check(wait_until(lambda: stopped and old_task not in conversion._LIVE, 5),
              "…and the old task ends")
        wait_until(lambda: False, 0.3)
        check(new_job.geojson.exists() and new_job.work.exists() and not started[0].geojson.exists()
              and not started[0].work.exists(),
              "…the old task removed its own files, not the new download")
        release_new.set()
        check(wait_until(lambda: again_late.id in loaded, 10) and not results.is_busy(again_late.id)
              and not failures, f"…and the new add finishes ({failures})")
        check(new_job.target.exists() and not started[0].target.exists(),
              "…and its GeoPackage is there: the old task did not remove it")
    finally:
        release_old.set()
        release_new.set()
        conversion.convert_geojson = original
    for layer in results.layers.layers_for(again_late.id):
        QgsProject.instance().removeMapLayer(layer.id())
    check(not [f for f in files_under(out_dir) if f.startswith(".downloads")],
          "…and nothing stays in .downloads")
    before = files_under(out_dir)              # the GeoPackage of that add stays

    # `_unique` skips a name that a live task holds, and gives it again when the task is released
    holder = results.layers.convert_results(str(out_dir / "unique-probe.geojson"), processing_done("conv-unique"),
                                            out_dir, lambda _task: None)
    try:
        taken = holder.job.target
        check(results.layers._unique(out_dir, taken.stem, ".gpkg") != taken
              and results.layers._unique(out_dir, taken.stem, ".gpkg").name == f"{taken.stem}_1.gpkg",
              "A live task holds its names: `_unique` gives the next one")
    finally:
        holder.release()
    check(results.layers._unique(out_dir, taken.stem, ".gpkg") == taken,
          "…and the name is free again when the task is released")

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


def check_results_loading_flag(iface, plugin):
    """spec/006 § The guard: the "loading" flag of a processing is cleared on every way out of a load, the
    synchronous start and the `on_error` fallbacks included. An exception is reported once, the user is told
    once, and the processing is not left loading. Everything the function changes is restored."""
    from mapflow_next.config import FILES, TILES
    from mapflow_next.core.models import Processing
    from mapflow_next.services.results import GENERIC_FAILURE
    results = plugin.services[4]
    layers = results.layers
    saved_mode = results.settings.value("results_mode", FILES)
    saved_tile_raster, saved_vector_tiles = layers.tile_raster, layers.vector_tiles
    failures = []

    def on_failed(processing_id, text):
        failures.append((processing_id, text))
    results.failed.connect(on_failed)

    def raising(text):
        def fail(*args, **kwargs):
            raise RuntimeError(text)
        return fail

    data = fixtures.processing_json("flag-tilejson", "OK", 100, name="Forest · flag-tilejson")
    # the raster's tilejson is not served: the fallback that adds the raster without bounds runs
    data["rasterLayer"] = {"tileUrl": "https://tiles.example/{z}/{x}/{y}.png",
                           "tileJsonUrl": "http://127.0.0.1:9/raster.json"}
    tilejson_failure = Processing.from_api(data)
    try:
        results.settings.setValue("results_mode", TILES)
        layers.tile_raster = raising("tile raster")
        results.add_to_map(tilejson_failure)
        check(wait_until(lambda: failures, 5),
              "LOADING FLAG: a failing fallback of a tilejson request reaches the user")
        wait_until(lambda: False, 0.3)
        check(not results.is_busy(tilejson_failure.id) and failures == [(tilejson_failure.id, GENERIC_FAILURE)],
              f"…the processing is not left loading, and it fails once ({failures})")
        expect_critical(iface, "tile raster", "the guard's lines of the failing fallback", count=2)

        # the synchronous start
        failures.clear()
        layers.vector_tiles = raising("vector tiles")
        start = Processing.from_api(fixtures.processing_json("flag-start", "OK", 100, name="Forest · flag-start"))
        results.add_to_map(start)                     # raises nothing: the guard has it
        check(not results.is_busy(start.id) and failures == [(start.id, GENERIC_FAILURE)],
              f"LOADING FLAG: an exception in the start of a load clears the flag ({failures})")
        expect_critical(iface, "vector tiles", "the guard's lines of the failing start", count=2)

        # save_geojson: the flag is set, and the request's start raises
        failures.clear()
        saved_done = []
        save = Processing.from_api(fixtures.processing_json("flag-save", "OK", 100, name="Forest · flag-save"))
        saved_download = results.api.download_result
        try:
            results.api.download_result = raising("save request")
            results.save_geojson(save, str(Path(tempfile.gettempdir()) / "flag-save.geojson"), saved_done.append)
        finally:
            results.api.download_result = saved_download
        check(not results.is_busy(save.id) and failures == [(save.id, GENERIC_FAILURE)] and not saved_done,
              f"LOADING FLAG: an exception between the flag and the request of a save clears the flag ({failures})")
        expect_critical(iface, "save request", "the guard's lines of the failing save", count=2)
    finally:
        results.settings.setValue("results_mode", saved_mode)
        layers.tile_raster, layers.vector_tiles = saved_tile_raster, saved_vector_tiles
        results.failed.disconnect(on_failed)
        results.reset()


def check_virtual_guard(iface, plugin):
    """spec/006 § The guard: an exception in a method that Qt calls by name (an event filter that Qt runs for an
    event, a map tool's `canvasReleaseEvent`) is reported once and does not reach `sys.excepthook`, which is where
    QGIS opens its raw error dialog."""
    from mapflow_next.qgis_bridge.draw_tool import PolygonDrawTool
    from mapflow_next.ui.widgets import HoverTip
    escaped = []
    saved_hook = sys.excepthook
    sys.excepthook = lambda *info: escaped.append(info)
    widget = QWidget()
    try:
        tip = HoverTip(widget, "text")
        tip.timer = None                                # the filter's next step raises
        delivered = QApplication.sendEvent(widget, QEvent(QEvent.Type.Enter))
        check(not escaped, f"VIRTUAL GUARD: an exception in an event filter does not reach the excepthook ({escaped})")
        check(delivered is not None, "…and the event is still delivered")
        expect_critical(iface, "attribute 'start'", "the guard's lines of the failing event filter", count=2)

        tool = PolygonDrawTool(iface.canvas)
        tool.canvasReleaseEvent(object())               # an event without `button()`
        check(not escaped, f"VIRTUAL GUARD: an exception in canvasReleaseEvent does not escape ({escaped})")
        expect_critical(iface, "attribute 'button'", "the guard's lines of the failing map tool", count=2)
        tool.deleteLater()
    finally:
        sys.excepthook = saved_hook
        widget.deleteLater()


def check_paint_guard(iface, plugin):
    """spec/006 § The guard: a `paintEvent` that raises leaves no active QPainter, also while the Critical line
    (with its "Send a report" button) stays on the message bar, and the button still gives the type, the message
    and the traceback."""
    from mapflow_next.core.guard import guarded

    class Local:
        """A local of the failing frame: it is freed only when nothing holds that frame."""

    locals_seen = []

    class Failing(QWidget):
        @guarded
        def paintEvent(self, event) -> None:
            painter = QPainter(self)
            painter.drawLine(0, 0, 1, 1)
            local = Local()
            locals_seen.append(weakref.ref(local))
            raise ValueError("boom")

    escaped = []
    saved_hook = sys.excepthook
    sys.excepthook = lambda *info: escaped.append(info)
    widget = Failing()
    try:
        widget.resize(40, 40)
        widget.show()
        widget.repaint()
        QApplication.processEvents()
        check(locals_seen and all(ref() is None for ref in locals_seen) and not widget.paintingActive(),
              "PAINT GUARD: a paintEvent that raises leaves no active QPainter, and nothing holds its frame, "
              "while the Critical line stays")
        check(not escaped, f"…and nothing reaches the excepthook ({escaped})")
        expect_critical(iface, "boom", "the guard's lines of the failing paintEvent", count=2)
        check_the_report(iface, plugin, "report of a failing paintEvent", False, "A widget failed to paint.")
    finally:
        sys.excepthook = saved_hook
        widget.close()
        widget.deleteLater()


def check_classify_without_timeout_error():
    """spec/006: a failed request is classified, not raised, also on a Qt build whose `NetworkError` has no
    `TimeoutError`."""
    import mapflow_next.api.http as http_module
    from qgis.PyQt.QtNetwork import QNetworkReply

    class Without:
        def __getattr__(self, name):
            if name == "TimeoutError":
                raise AttributeError(name)
            return getattr(QNetworkReply.NetworkError, name)

    class Reply:
        NetworkError = Without()

    saved = http_module.QNetworkReply
    http_module.QNetworkReply = Reply
    try:
        try:
            other = http_module.classify(QNetworkReply.NetworkError.HostNotFoundError, None, "", "u", False)
            raised = None
        except Exception as exc:  # noqa: BLE001
            other, raised = None, exc
        check(raised is None and other is not None and other.kind not in ("timeout", "cancelled"),
              f"CLASSIFY: a Qt build without TimeoutError does not make a failed request raise ({raised}, "
              f"{other and other.kind})")
        check(http_module.classify(0, None, "", "u", True).kind == "timeout",
              "…and a request that timed out is still a timeout")
    finally:
        http_module.QNetworkReply = saved
    check(http_module.classify(QNetworkReply.NetworkError.TimeoutError, None, "", "u", False).kind == "timeout",
          "…and the Qt timeout error is a timeout")


def check_poll_auth(iface, plugin, state, browser):
    """spec/005 § Failed requests: a 401 is the session's. A timer's request that got one keeps its schedule, is not
    counted and says nothing; the session renews the token (the poll goes on) or signs out, says so once, and then
    no poll timer runs. Starts and ends signed out; the timer intervals and the test processing are restored."""
    from mapflow_next.api import auth
    from mapflow_next.core.failures import POLL
    session, processings, imagery = plugin.services[1], plugin.services[2], plugin.services[3]
    controller, content = plugin.controller, plugin.dock.content
    warn = Qgis.MessageLevel.Warning

    def lines(since):
        return [text for level, text in iface.bar.messages[since:] if level == warn]

    def requests(method, pattern):
        return len([r for r in state.requests if r[0] == method and re.search(pattern, r[1])])

    def sign_in_browser():
        content.sign_in.browserRequested.emit()
        browse(browser.opened[-1])
        status, back = browse(browser.opened[-1])
        browse(back)
        return wait_until(lambda: session.state == "signed_in" and session.project is not None
                          and processings.loaded, 8)

    last_page = [""]

    def page():
        if session.project is not None:
            last_page[0] = rf"/projects/{session.project.id}/processings/v2/page"
        return last_page[0]

    def expired_said():
        return "session has expired" in content.sign_in.error.text.text()

    def nothing_runs(label):
        wait_until(lambda: False, 0.3)
        timers = [processings._poll.isActive(), session._timer.isActive(), session._refresh_timer.isActive(),
                  controller._mosaic_refresh.isActive()]
        check(not any(timers), f"{label}: no poll timer runs after the sign-out ({timers})")
        seen = len(state.requests)
        wait_until(lambda: False, 0.5)
        check(len(state.requests) == seen and not processings._loading,
              f"{label}: …and no request goes out ({len(state.requests) - seen} new)")

    def add_running():
        """A processing that stays in progress for many answers (the mock advances every one by 50 %)."""
        with state.lock:
            state.processings.append(dict(fixtures.processing_json("poll-auth", "IN_PROGRESS", -3000, name="Poll auth"),
                                          projectId=session.project.id))
        processings.refresh(POLL)
        wait_until(lambda: any(p.id == "poll-auth" for p in processings.items), 5)

    told = []
    session.error.connect(told.append)
    saved_status_interval = session._timer.interval()
    saved_poll_interval = processings._poll.interval()
    try:
        state.heal()
        check(sign_in_browser(), "a 401 check: signed in with the browser")
        add_running()
        processings._poll.setInterval(150)

        # (a) the list answers 401 once: the token renews, the next tick loads the list, the poll goes on
        before, bearer, asked = len(iface.bar.messages), session.http.bearer, requests("POST", page())
        session._forced_refresh_at = 0.0
        state.fail("POST", page(), 401, times=1)
        wait_until(lambda: not processings._loading, 3)
        processings._poll.stop()                    # as when its tick has just fired: only the answer can start it
        processings.refresh(POLL)
        check(wait_until(lambda: session.http.bearer != bearer, 5) and session.state == "signed_in",
              "401: the processings list that got a 401 makes the session renew the token and stay signed in")
        check(wait_until(lambda: requests("POST", page()) >= asked + 4 and processings.loaded
                         and not processings.load_failed, 5),
              "…the next ticks load the list: the poll goes on")
        wait_until(lambda: processings._poll.isActive(), 2)     # not while a list request is in flight
        check(processings._poll_failures.count == 0 and not processings._poll_failures.stopped
              and not lines(before) and not content.sign_in.error.isVisible() and processings._poll.isActive(),
              f"…the 401 is not counted and says nothing ({lines(before)})")

        # (b) the account status
        session._timer.setInterval(50)
        session._forced_refresh_at = 0.0
        state.fail("GET", "/user/status", 401, times=1)
        before, bearer = len(iface.bar.messages), session.http.bearer
        asked = requests("GET", "/user/status")
        session._timer.start()
        check(wait_until(lambda: requests("GET", "/user/status") >= asked + 4, 5),
              "401: the account status keeps asking after a 401")
        check(wait_until(lambda: session.http.bearer != bearer, 5) and session.state == "signed_in",
              "…and the session renewed the token")
        check(session._status_poll.count == 0 and wait_until(lambda: not session._status_pending, 2)
              and session._timer.isActive() and not lines(before),
              f"…it is not counted, says nothing, and the timer runs ({lines(before)})")
        session._timer.stop()
        session._timer.setInterval(saved_status_interval)

        # (c) the collections refresh
        def mosaic_tick():
            imagery._mosaics_at = 0.0
            controller._mosaic_refresh.timeout.emit()
            return wait_until(lambda: not imagery.loading_mosaics, 5)

        wait_until(lambda: session.state == "signed_in" and not session._refreshing, 5)
        session._forced_refresh_at = 0.0
        state.fail("GET", r"/rasters/mosaic/page", 401, times=1)
        before, bearer = len(iface.bar.messages), session.http.bearer
        mosaic_tick()
        check(wait_until(lambda: session.http.bearer != bearer and not session._refreshing, 5)
              and imagery._mosaics_poll.count == 0 and not imagery._mosaics_poll.stopped and not lines(before)
              and controller._mosaic_refresh.isActive() and session.state == "signed_in",
              f"401: the collections refresh is not counted, says nothing and keeps its timer ({lines(before)})")
        mosaic_tick()
        check(imagery.mosaics_loaded and not imagery.mosaics_failed, "…and the next tick loads the collections")

        # (d) a second 401 within a minute: the session signs out, says so once, and nothing runs
        wait_until(lambda: not session._refreshing and processings.loaded and not processings._loading, 5)
        session._forced_refresh_at = time.time()
        said, asked = len(told), requests("POST", page())
        state.fail("POST", page(), 401, times=1)
        processings.refresh(POLL)
        check(wait_until(lambda: session.state == "signed_out", 5) and expired_said()
              and len([t for t in told[said:] if "session has expired" in t]) == 1
              and not auth.load_refresh_token(session.config),
              "401: a second 401 within a minute signs out, says “Your Mapflow session has expired” once, and "
              "forgets the sign-in")
        nothing_runs("a second 401")
        check(requests("POST", page()) == asked + 1, "…and the processings list sent nothing after the 401")

        # (e) the renewal fails
        with state.lock:
            state.processings[:] = [p for p in state.processings if p["id"] != "poll-auth"]
        state.heal()
        check(sign_in_browser(), "a 401 check: signed in with the browser again")
        add_running()
        session._forced_refresh_at = 0.0
        with state.lock:
            state.refresh_tokens.clear()
        said, asked = len(told), requests("POST", page())
        state.fail("POST", page(), 401, times=1)
        processings.refresh(POLL)
        check(wait_until(lambda: session.state == "signed_out", 5) and expired_said()
              and len([t for t in told[said:] if "session has expired" in t]) == 1,
              "401: a renewal that fails signs out and says “Your Mapflow session has expired” once")
        nothing_runs("a failed renewal")
        check(requests("POST", page()) == asked + 1, "…and the processings list sent nothing after the 401")

        # (f) token sign-in: a 401 signs out
        with state.lock:
            state.processings[:] = [p for p in state.processings if p["id"] != "poll-auth"]
        state.heal()
        content.sign_in.tokenSubmitted.emit(mock_server.TOKEN)
        check(wait_until(lambda: session.state == "signed_in" and session.project is not None
                         and processings.loaded, 8), "a 401 check: signed in with the API token")
        add_running()
        said, asked = len(told), requests("POST", page())
        state.fail("POST", page(), 401, times=1)
        processings.refresh(POLL)
        check(wait_until(lambda: session.state == "signed_out", 5) and expired_said()
              and len([t for t in told[said:] if "session has expired" in t]) == 1,
              "401: with the API token a 401 signs out and says “Your Mapflow session has expired” once")
        nothing_runs("a 401 with the API token")
        check(requests("POST", page()) == asked + 1, "…and the processings list sent nothing after the 401")
    finally:
        session.error.disconnect(told.append)
        state.heal()
        with state.lock:
            state.processings[:] = [p for p in state.processings if p["id"] != "poll-auth"]
        session._timer.setInterval(saved_status_interval)
        processings._poll.setInterval(saved_poll_interval)


def check_forced_upgrade(iface, plugin, state, browser):
    """spec/002_api.md § Versioning policy: the plugin asks GET /version at sign-in (also at a silent start). A higher
    major version than the plugin's own blocks it: one page that says to upgrade, a button for the plugin manager, a
    Sign out, no other request, no poll. A higher minor or patch version, a failed request and an answer that is not
    a version change nothing and show nothing. Starts and ends signed out; everything it changes is restored."""
    from mapflow_next.api import auth
    from mapflow_next.qgis_bridge import updates
    session, processings = plugin.services[1], plugin.services[2]
    controller, content = plugin.controller, plugin.dock.content
    opened = []
    saved_open = updates.open_upgrades
    saved_status, saved_poll = session._timer.interval(), processings._poll.interval()
    told = []
    session.error.connect(told.append)

    def api_requests(since):
        """The (method, path) of the API requests after index `since`, without the sign-in server's."""
        return [(r[0], r[1]) for r in state.requests[since:] if not r[1].startswith(mock_server.OIDC)]

    def asked_version(since):
        return len([r for r in api_requests(since) if r == ("GET", "/version")])

    def timers():
        return [session._timer.isActive(), session._refresh_timer.isActive(), processings._poll.isActive(),
                controller._mosaic_refresh.isActive()]

    def sign_in_token():
        content.sign_in.tokenSubmitted.emit(mock_server.TOKEN)

    def sign_in_browser():
        content.sign_in.browserRequested.emit()
        browse(browser.opened[-1])
        status, back = browse(browser.opened[-1])
        browse(back)

    def signed_in():
        return wait_until(lambda: session.state == "signed_in" and session.project is not None
                          and processings.loaded, 8)

    def blocked():
        return wait_until(lambda: session.state == "upgrade_required", 8)

    def quiet(label, bar_mark, ledger_mark):
        check(not told and len(iface.bar.messages) == bar_mark and len(iface.bar.ledger.unexpected()) == ledger_mark
              and content.stack.currentWidget() is not content.upgrade and not session.expected_version,
              f"{label}: nothing is shown and the plugin is not blocked ({told}, {iface.bar.messages[bar_mark:]})")

    def start():
        del told[:]
        return len(state.requests), len(iface.bar.messages), len(iface.bar.ledger.unexpected())

    def sign_out():
        controller.sign_out()
        wait_until(lambda: session.state == "signed_out", 5)

    try:
        state.heal()
        state.expected_version = "4.0.0"
        session._timer.setInterval(50)
        processings._poll.setInterval(150)

        # the same version: asked once, before the account, and the sign-in goes on
        mark, bar_mark, ledger_mark = start()
        sign_in_token()
        check(signed_in(), "forced upgrade: signed in with the API token against the same version")
        calls = api_requests(mark)
        check(asked_version(mark) == 1 and calls[0] == ("GET", "/version")
              and calls.index(("GET", "/projects/default")) > calls.index(("GET", "/version")),
              f"GET /version is asked once at sign-in, before the account ({calls[:3]})")
        quiet("the same version", bar_mark, ledger_mark)
        sign_out()

        # a higher major version blocks the plugin (API token)
        state.expected_version = "5.0.0"
        mark, bar_mark, ledger_mark = start()
        sign_in_token()
        check(blocked(), "a higher major version blocks the plugin after an API token sign-in")
        wait_until(lambda: False, 0.8)
        text = content.upgrade.message.text()
        check(content.stack.currentWidget() is content.upgrade and session.expected_version == "5.0.0",
              "the dock shows the upgrade page")
        check(content.header.isHidden() and content.tabs.isHidden() and content.footer.isHidden(),
              "…and nothing else: no header, tabs or footer")
        check("5.0.0" in text and "4.0.0" in text and "Upgrade" in text, f"…its text names both versions ({text})")
        check(api_requests(mark) == [("GET", "/version")], f"no other request is sent ({api_requests(mark)})")
        check(not any(timers()), f"…and no poll or renewal timer runs ({timers()})")
        check(session.settings.value("auth_method") == "token" and session.settings.value("auth_config_id"),
              "the blocked sign-in is remembered for the next start")
        check(not told and len(iface.bar.ledger.unexpected()) == ledger_mark,
              f"nothing is reported as an error ({told})")
        shot(content, "01c-upgrade", QSize(400, 880))
        updates.open_upgrades = lambda: opened.append(True)
        content.upgrade.upgrade.click()
        check(opened == [True], "the upgrade button opens the QGIS plugin manager")

        # a silent start with stored credentials asks again
        mark = len(state.requests)
        session.restore()
        check(blocked() and wait_until(lambda: asked_version(mark) == 1, 5), "a silent start asks GET /version again "
              "and is blocked again")
        wait_until(lambda: False, 0.5)
        check(api_requests(mark) == [("GET", "/version")] and not any(timers()) and not told,
              f"…with no other request and no message ({api_requests(mark)})")
        state.expected_version = "4.0.0"
        mark = len(state.requests)
        session.restore()
        check(signed_in() and not told and content.stack.currentWidget() is not content.upgrade,
              f"after the upgrade a silent start signs in without a message ({told})")
        sign_out()

        # sign out stays possible on the page
        state.expected_version = "5.0.0"
        sign_in_token()
        check(blocked(), "a higher major version blocks again")
        content.upgrade.sign_out.click()
        check(wait_until(lambda: session.state == "signed_out", 5) and content.stack.currentWidget() is content.sign_in
              and not session.settings.value("auth_method") and not session.expected_version,
              "Sign out on the upgrade page returns to the sign-in page and forgets the sign-in")

        # the browser sign-in
        mark = len(state.requests)
        sign_in_browser()
        check(blocked() and content.stack.currentWidget() is content.upgrade,
              "a higher major version blocks the plugin after a browser sign-in")
        seen = len(state.requests)
        wait_until(lambda: False, 0.8)
        check(len(state.requests) == seen and not any(timers()) and auth.load_refresh_token(session.config)
              and session.settings.value("auth_method") == "browser",
              f"…no request leaves the plugin, not even a token renewal ({len(state.requests) - seen} new), and "
              "the sign-in is remembered")
        mark = len(state.requests)
        session.restore()
        check(blocked() and wait_until(lambda: asked_version(mark) == 1, 5)
              and len(browser.opened) and not told,
              "a silent start after a browser sign-in asks GET /version again and is blocked again")
        wait_until(lambda: False, 0.5)
        check(api_requests(mark) == [("GET", "/version")], f"…with no other API request ({api_requests(mark)})")
        state.expected_version = "4.0.0"
        session.restore()
        check(signed_in() and not told, f"after the upgrade the silent start signs in ({told})")
        sign_out()

        # a higher minor or patch version, a failed request, an answer that is not a version: nothing changes
        cases = [("4.1.0", None), ("4.0.1", None), ("4.0.0-beta", None), ("5", None), ("", None),
                 ("not a version", None), ("<html>5.0.0</html>", None), ("4.0.0", 503), ("4.0.0", 404),
                 ("5.0.0", "drop")]
        for expected, failure in cases:
            state.heal()
            state.expected_version = expected
            if failure is not None:
                state.fail("GET", r"^/version$", failure)
            label = f"a version answer {expected!r}" if failure is None else f"a failed GET /version ({failure})"
            mark, bar_mark, ledger_mark = start()
            sign_in_token()
            check(signed_in(), f"{label}: the sign-in goes on")
            quiet(label, bar_mark, ledger_mark)
            sign_out()
        state.heal()
        state.expected_version = "4.0.0"
        check(session.state == "signed_out", "forced upgrade: the check ends signed out")
    finally:
        session.error.disconnect(told.append)
        state.heal()
        state.expected_version = "4.0.0"
        updates.open_upgrades = saved_open
        session._timer.setInterval(saved_status)
        processings._poll.setInterval(saved_poll)


def check_rename_project(iface, plugin, state):
    """spec/002_A § Plugin behaviour, § PUT /projects/{id}: "Rename…" is in a ⋯ menu on the tile of a project the
    user owns, never on the default project or a project shared with the user as a member. The dialog edits the
    name and the description; Save sends the PUT; the tiles and the dock header show the new name without asking
    for the list again. An empty name is refused in the dialog; a refusal shows the server's message and leaves the
    old name; a closed window doesn't lose the answer. Everything the function changes is restored."""
    import mapflow_next.controller as controller_module
    from mapflow_next.ui.rename_dialog import RenameDialog
    session, processings = plugin.services[1], plugin.services[2]
    controller, content = plugin.controller, plugin.dock.content
    warn, success = Qgis.MessageLevel.Warning, Qgis.MessageLevel.Success
    puts = state.rename_project_requests

    def open_window():
        controller.open_projects()
        window = controller.projects_dialog
        check(wait_until(lambda: window.isVisible() and not window.loading and len(window.results) == 24, 5),
              "(the projects window shows its first page)")
        return window

    def tile_of(project_id):
        return next((t for t in controller.projects_dialog.tiles if t.project.id == project_id), None)

    def header():
        return content.project_button.text(), content.project_button.toolTip()

    class Fake:
        answer = None
        made = []

        def __init__(self, *args, **kwargs):
            Fake.made.append((args, kwargs))

        def exec(self):
            return 0 if Fake.answer is None else 1

        def values(self):
            return Fake.answer

    def rename(project_id, answer):
        """The tile's ⋯ menu, Rename…, with the dialog answering `answer` (None: cancelled)."""
        Fake.answer = answer
        tile_of(project_id).menu().actions()[0].trigger()

    harbor = ("Harbor", "Port and storage yards, quarterly updates")
    field_7 = ("Field site 07", "Survey area 7")
    saved_dialog = controller_module.RenameDialog
    window = open_window()
    try:
        # Offered: the owner, and not the default project, a member or a reader
        state.shared_projects["project-9"] = {"owners": [{"email": "boss@example.com"}],
                                              "users": [{"email": "me@example.com", "role": "contributor"}]}
        state.shared_projects["project-10"] = {"owners": [{"email": "boss@example.com"}],
                                               "users": [{"email": "ana@example.com", "role": "contributor"}]}
        window = open_window()
        check(all(tile_of(i) is not None and tile_of(i).more_button is not None for i in ("project-2", "project-7"))
              and [a.text() for a in tile_of("project-2").menu().actions()] == ["Rename…", "Delete…"],
              "an own project and a project the user owns in a share have a ⋯ menu with Rename… and Delete…")
        check(tile_of("project-1").more_button is None and tile_of("project-1").menu().actions() == [],
              "the default project has none")
        check(tile_of("project-9").more_button is None and tile_of("project-10").more_button is None,
              "a project where the user is a contributor, or not listed (read only), has none")
        opened = []
        window.projectChosen.connect(opened.append)
        QTimer.singleShot(300, lambda: QApplication.activePopupWidget() and QApplication.activePopupWidget().close())
        tile_of("project-2").more_button.click()          # the menu pops up and blocks until it is closed
        check(not opened, "the ⋯ button opens the menu and not the project")
        state.shared_projects.clear()

        # The open project: the PUT, and the new name in the header, the tile and every copy
        controller_module.RenameDialog = Fake
        window = open_window()
        check(session.project.id == "project-2", "(project-2 is the open project)")
        iface.bar.messages.clear()
        puts.clear()
        rename("project-2", ("Harbor east", "New yards"))
        check(wait_until(lambda: session.project.name == "Harbor east", 5)
              and puts == [("project-2", {"name": "Harbor east", "description": "New yards"})]
              and Fake.made[-1][1].get("title") == "Rename project" and Fake.made[-1][0][:2] == harbor,
              f"Rename… sends PUT /projects/project-2 with the name and the description ({puts}); "
              "the dialog starts with the current ones")
        listed = next((p for p in session.projects if p.id == "project-2"), None)
        check(header()[0] == "Harbor east" and "Harbor east" in header()[1]
              and tile_of("project-2").project.name == "Harbor east" and processings.project.name == "Harbor east"
              and (listed is None or listed.name == "Harbor east")
              and "Recent in Harbor east" in content.start.recent_title.text(),
              f"…the dock header, the tile, the session and the Start tab show it ({header()})")
        check(any(level == success and "Project “Harbor” is renamed to “Harbor east”." in (text or "")
                  for level, text in iface.bar.messages), "…and the message bar says so")
        asked = len([r for r in state.requests if r[1] == "/projects/page"])
        controller._query_projects("")
        check(wait_until(lambda: not window.loading and any(p.name == "Harbor east" and p.description == "New yards"
                                                            for p in window.results), 5)
              and len([r for r in state.requests if r[1] == "/projects/page"]) == asked + 1,
              "a new query returns the new name: Mapflow has it")

        # A project that is not open, and a pinned one
        rename("project-7", ("Field east", "Survey area 7"))
        check(wait_until(lambda: tile_of("project-7") is not None and tile_of("project-7").project.name == "Field east",
                         5) and header()[0] == "Harbor east" and session.project.name == "Harbor east",
              "a project that isn't open shows the new name on its tile and leaves the header alone")
        controller._pin_project("project-8", True)
        check(tile_of("project-8") is not None and "project-8" in window.pinned, "(project-8 is pinned)")
        rename("project-8", ("Field pinned", "Survey area 8"))
        check(wait_until(lambda: tile_of("project-8").project.name == "Field pinned"
                         and window.pinned["project-8"].name == "Field pinned", 5),
              "a pinned project shows the new name in the pinned section")

        # Nothing to send: an empty name, a cancelled dialog, no change
        puts.clear()
        rename("project-7", ("", "x"))
        rename("project-7", None)
        rename("project-7", ("Field east", "Survey area 7"))
        wait_until(lambda: False, 0.3)
        check(not puts, "an empty name, a cancelled dialog or no change send nothing")
        real = RenameDialog("Harbor east", "", None, title="Rename project", action="Save", what="project")
        real.name.clear()
        empty = not real.save.isEnabled()
        real.name.setText("   ")
        check(empty and not real.save.isEnabled(), "the dialog refuses an empty name, and a name of spaces")
        real.close()

        # Refused: the server's message, the old name stays
        state.project_refusal = "A project with this name already exists."
        iface.bar.messages.clear()
        rename("project-2", ("Field east", "New yards"))
        text = "Couldn't rename “Harbor east”: A project with this name already exists."
        check(wait_until(lambda: any(level == warn and text in (t or "") for level, t in iface.bar.messages), 5)
              and window.note.isVisibleTo(window) and text in window.note.text.text(),
              f"a refusal shows the message of the server, in the message bar and in the window "
              f"({window.note.text.text()})")
        check(header()[0] == "Harbor east" and tile_of("project-2").project.name == "Harbor east"
              and session.project.name == "Harbor east" and state.renamed_projects["project-2"][0] == "Harbor east",
              "…and the old name stays everywhere")
        state.project_refusal = None
        state.fail("PUT", r"/projects/project-7", 403)
        iface.bar.messages.clear()
        rename("project-7", ("Field west", ""))
        check(wait_until(lambda: any(level == warn and "Couldn't rename “Field east”:" in (t or "")
                                     for level, t in iface.bar.messages), 5)
              and tile_of("project-7").project.name == "Field east", "a 403 is shown too, and changes nothing")
        state.heal()

        # Not an owner any more: the menu was built before; the server answers 403 with its message
        menu = tile_of("project-8").menu()
        state.shared_projects["project-8"] = {"owners": [{"email": "boss@example.com"}],
                                              "users": [{"email": "me@example.com", "role": "contributor"}]}
        Fake.answer = ("Field other", "")
        iface.bar.messages.clear()
        menu.actions()[0].trigger()
        check(wait_until(lambda: any(level == warn and "Only the owner can rename the project" in (t or "")
                                     for level, t in iface.bar.messages), 5)
              and tile_of("project-8").project.name == "Field pinned",
              "a rename that the server refuses for a non-owner shows its message")
        state.shared_projects.clear()

        # The window closed while the PUT runs: the header still takes the name
        state.project_delay = 0.6
        iface.bar.messages.clear()
        rename("project-2", ("Harbor west", "New yards"))
        window.close()
        check(wait_until(lambda: session.project.name == "Harbor west" and header()[0] == "Harbor west", 5)
              and any(level == success and "“Harbor west”" in (t or "") for level, t in iface.bar.messages),
              "a window closed while the PUT runs doesn't lose the new name")
        state.project_delay = 0

        # Restore the names, through the same flow, and the state of the mock
        window = open_window()
        rename("project-2", harbor)
        rename("project-7", field_7)
        rename("project-8", ("Field site 08", "Survey area 8"))
        check(wait_until(lambda: session.project.name == "Harbor" and tile_of("project-7").project.name
                         == "Field site 07" and tile_of("project-8").project.name == "Field site 08", 5),
              "the names are renamed back")
    finally:
        controller_module.RenameDialog = saved_dialog
        state.project_delay = 0
        state.project_refusal = None
        state.heal()
        state.shared_projects.clear()
    if "project-8" in controller.pinned_projects():
        controller._pin_project("project-8", False)
        wait_until(lambda: "project-8" not in state.starred, 3)
    state.renamed_projects.clear()
    puts.clear()
    window.close()
    session.select_project("project-2")
    wait_until(lambda: session.project.id == "project-2" and session.project.name == "Harbor", 5)


def check_delete_project(iface, plugin, state):
    """spec/002_A § Plugin behaviour, § DELETE /projects/{id}: "Delete…" is in the ⋯ menu of a project the user
    owns, never of the default project. A confirmation names the project and says its processings go with it;
    nothing is sent before it is accepted. After the delete the project leaves the window, the pins and the
    session; the open project is replaced by the default one (spec/005 § Failed requests, "The open project is
    gone"), and its poll stops. A refusal shows the message of the server and changes nothing. Results already on
    the map stay. Everything the function changes is restored."""
    from mapflow_next.core.failures import POLL
    session, processings = plugin.services[1], plugin.services[2]
    controller, content = plugin.controller, plugin.dock.content
    warn, success = Qgis.MessageLevel.Warning, Qgis.MessageLevel.Success
    deletes = state.delete_project_requests
    page = r"/projects/project-2/processings/v2/page"
    listing = r"^/projects/page$"

    def requests(method, pattern):
        return len([r for r in state.requests if r[0] == method and re.search(pattern, r[1])])

    def open_window():
        controller.open_projects()
        window = controller.projects_dialog
        check(wait_until(lambda: window.isVisible() and not window.loading and len(window.results) == 24, 5),
              "(the projects window shows its first page)")
        return window

    def tile_of(project_id):
        return next((t for t in controller.projects_dialog.tiles if t.project.id == project_id), None)

    def header():
        return content.project_button.text(), content.project_button.toolTip()

    def lines():
        return [text for _level, text in iface.bar.messages]

    class Confirm:
        answer = False
        asked = []

        def __call__(self, title, text, detail, parent=None):
            Confirm.asked.append((title, text, detail, parent))
            return Confirm.answer

    def delete(project_id, answer=True):
        """The tile's ⋯ menu, Delete…, with the confirmation answering `answer`."""
        Confirm.answer = answer
        Confirm.asked.clear()
        deletes.clear()
        tile_of(project_id).menu().actions()[1].trigger()

    with state.lock:
        saved_processings = list(state.processings)

    def restore():
        state.deleted_projects.clear()
        with state.lock:
            state.processings[:] = saved_processings        # a delete drops the processings of its project
        state.delete_refusal = None
        state.project_delay = 0
        state.heal()
        state.shared_projects.clear()
        deletes.clear()

    saved_confirm = controller._confirm_delete
    controller._confirm_delete = Confirm()
    window = open_window()
    try:
        # Offered: the owner, and not the default project, a member or a reader
        state.shared_projects["project-9"] = {"owners": [{"email": "boss@example.com"}],
                                              "users": [{"email": "me@example.com", "role": "contributor"}]}
        state.shared_projects["project-10"] = {"owners": [{"email": "boss@example.com"}],
                                               "users": [{"email": "ana@example.com", "role": "contributor"}]}
        window = open_window()
        check([a.text() for a in tile_of("project-2").menu().actions()] == ["Rename…", "Delete…"]
              and [a.text() for a in tile_of("project-7").menu().actions()] == ["Rename…", "Delete…"],
              "the ⋯ menu of an own project offers Delete… below Rename…")
        check(tile_of("project-1").more_button is None and tile_of("project-1").menu().actions() == [],
              "the default project has no Delete…")
        check(tile_of("project-9").more_button is None and tile_of("project-10").more_button is None,
              "a project where the user is a contributor, or not listed (read only), has none")
        state.shared_projects.clear()
        window = open_window()
        check(session.project.id == "project-2", "(project-2 is the open project)")
        harbor_layer = old_town_layer()
        harbor_layer.setName("Harbor result")
        plugin.layers.add(harbor_layer, processing_id="harbor-run")

        # Cancel: nothing is sent, nothing changes
        iface.bar.messages.clear()
        delete("project-7", answer=False)
        wait_until(lambda: False, 0.4)
        check(len(Confirm.asked) == 1 and not deletes and tile_of("project-7") is not None
              and not iface.bar.messages and session.project.id == "project-2",
              f"cancelling the confirmation sends nothing and leaves the tile and the message bar as they were "
              f"({deletes})")
        title, text, detail, parent = Confirm.asked[0]
        check(title == "Delete project" and "“Field site 07”" in text and "processings" in detail
              and "deleted with it" in detail and parent is window,
              f"the confirmation names the project and says its processings are deleted with it ({text!r}, "
              f"{detail!r})")

        # Another project, and a pinned one: it leaves the window, the pins and the session
        controller._pin_project("project-8", True)
        check(tile_of("project-8") is not None and "project-8" in window.pinned, "(project-8 is pinned)")
        total, shown = window.total, len(window.results)
        before_header = header()
        iface.bar.messages.clear()
        delete("project-7")
        check(wait_until(lambda: tile_of("project-7") is None, 5) and deletes == ["project-7"]
              and requests("DELETE", r"^/projects/project-7$") == 1,
              f"Delete… sends one DELETE /projects/project-7 and the tile leaves ({deletes})")
        check(all(p.id != "project-7" for p in window.results) and all(p.id != "project-7" for p in session.projects)
              and window.total == total - 1 and len(window.results) == shown - 1,
              "…it is gone from the window's list, the session's list and the count")
        check(session.project.id == "project-2" and header() == before_header and session.project.name == "Harbor",
              "…and the open project and the header are unchanged")
        check(any(level == success and (t or "") == "Project “Field site 07” is deleted."
                  for level, t in iface.bar.messages), f"…and the message bar says so ({lines()})")
        asked = requests("POST", listing)
        controller._more_projects()
        check(wait_until(lambda: not window.loading and len(window.results) == total - 1, 5)
              and len({p.id for p in window.results}) == total - 1 and requests("POST", listing) == asked + 1
              and window.total == total - 1,
              f"the next page follows the shorter list, with no project skipped or repeated "
              f"({len(window.results)} of {window.total})")
        delete("project-8")
        check(wait_until(lambda: tile_of("project-8") is None, 5) and "project-8" not in window.pinned
              and "project-8" not in controller.pinned_projects() and "project-8" not in state.starred,
              "a pinned project leaves the pinned section and the pins")
        controller._query_projects("")
        check(wait_until(lambda: not window.loading and len(window.results) == 24
                         and all(p.id not in ("project-7", "project-8") for p in window.results), 5),
              "a new query does not return the deleted projects: Mapflow has deleted them")
        restore()

        # The open project: the default project opens, the poll stops, the result on the map stays
        window = open_window()
        layers_before = set(QgsProject.instance().mapLayers())
        iface.bar.messages.clear()
        asked = requests("POST", listing)
        delete("project-2")
        check(wait_until(lambda: session.project.id == "project-1", 5) and deletes == ["project-2"]
              and "“Harbor”" in Confirm.asked[0][1],
              "deleting the open project opens the default project")
        wait_until(lambda: tile_of("project-2") is None and processings.project is not None
                   and processings.project.id == "project-1" and requests("POST", listing) > asked, 5)
        check(header()[0] == session.default_project.name and tile_of("project-2") is None
              and all(p.id != "project-2" for p in session.projects) and processings.project.id == "project-1",
              f"…the dock header shows it and the project is out of every list ({header()})")
        check(window.current_id == "project-1" and tile_of("project-1").property("current"),
              "…and the window marks the default project as the open one")
        asked_page = requests("POST", page)
        wait_until(lambda: False, 0.6)
        check(requests("POST", page) == asked_page and processings.project.id == "project-1",
              "…the poll of the deleted project stops")
        check(lines() == ["Project “Harbor” is deleted. The default project is open instead."]
              and iface.bar.messages[-1][0] == success,
              f"…one line names the deleted project, and no “gone” line is shown ({lines()})")
        check(requests("POST", listing) > asked, "…the project list is loaded again")
        check(set(QgsProject.instance().mapLayers()) == layers_before and plugin.layers.layers_for("harbor-run"),
              "results already on the map stay")
        restore()
        session.select_project("project-2")
        check(wait_until(lambda: session.project.id == "project-2" and processings.loaded, 5), "(project-2 is back)")

        # Not an owner any more: the menu was built before; the server answers 403 with its message
        window = open_window()
        menu = tile_of("project-8").menu()
        state.shared_projects["project-8"] = {"owners": [{"email": "boss@example.com"}],
                                              "users": [{"email": "me@example.com", "role": "contributor"}]}
        Confirm.answer = True
        iface.bar.messages.clear()
        menu.actions()[1].trigger()
        text = "Couldn't delete “Field site 08”: Only the owner can delete the project"
        check(wait_until(lambda: any(level == warn and text in (t or "") for level, t in iface.bar.messages), 5)
              and tile_of("project-8") is not None and text in window.note.text.text(),
              f"a delete that the server refuses for a non-owner shows its message and keeps the project "
              f"({lines()})")
        state.shared_projects.clear()
        # The controller does not even ask when it holds a project the user does not own
        known = controller._known_project("project-8")
        owner = known.role
        known.role = type(owner).contributor
        Confirm.asked.clear()
        deletes.clear()
        controller.delete_project("project-8")
        wait_until(lambda: False, 0.3)
        check(not Confirm.asked and not deletes, "a project the user does not own is not asked about")
        known.role = owner

        # The default project: never deleted, nothing asked or sent
        controller.delete_project("project-1")
        wait_until(lambda: False, 0.3)
        check(not Confirm.asked and not deletes and "project-1" not in state.deleted_projects,
              "Delete for the default project asks and sends nothing")

        # Refused by the server: its message, the project stays
        state.delete_refusal = "The project is used by a running job."
        iface.bar.messages.clear()
        before_projects = [p.id for p in session.projects]
        delete("project-7")
        text = "Couldn't delete “Field site 07”: The project is used by a running job."
        check(wait_until(lambda: any(level == warn and text in (t or "") for level, t in iface.bar.messages), 5)
              and window.note.isVisibleTo(window) and text in window.note.text.text(),
              f"a refusal shows the message of the server, in the message bar and in the window "
              f"({window.note.text.text()})")
        check(tile_of("project-7") is not None and [p.id for p in session.projects] == before_projects
              and session.project.id == "project-2" and "project-7" not in state.deleted_projects,
              "…and the project stays in the list, and the open project stays open")
        state.delete_refusal = None
        state.fail("DELETE", r"/projects/project-7", 503)
        iface.bar.messages.clear()
        delete("project-7")
        check(wait_until(lambda: any(level == warn and "Couldn't delete “Field site 07”:" in (t or "")
                                     for level, t in iface.bar.messages), 5) and tile_of("project-7") is not None,
              "a failed request is shown too, and changes nothing")
        state.heal()

        # The window closes while the DELETE runs: the open project still switches
        state.project_delay = 0.6
        iface.bar.messages.clear()
        delete("project-2")
        window.close()
        check(wait_until(lambda: session.project.id == "project-1", 5)
              and any(level == success and "“Harbor”" in (t or "") for level, t in iface.bar.messages),
              "a window closed while the DELETE runs doesn't lose the answer")
        restore()
        session.select_project("project-2")
        check(wait_until(lambda: session.project.id == "project-2" and processings.loaded, 5), "(project-2 is back)")

        # The poll of the open project answers 404 before the DELETE does: one switch, one “gone” line
        window = open_window()
        state.project_delay = 0.8
        iface.bar.messages.clear()
        delete("project-2")
        state.fail("POST", page, 404)
        processings.refresh(POLL)
        check(wait_until(lambda: session.project.id == "project-1", 5)
              and len([t for t in lines() if "gone or no longer" in (t or "")]) == 1,
              "(the poll found the project gone first)")
        check(wait_until(lambda: "project-2" in state.deleted_projects
                         and any("is deleted." in (t or "") for t in lines()), 5),
              "(the delete answered after it)")
        check(session.project.id == "project-1" and len(lines()) == 2 and lines()[-1] == "Project “Harbor” is deleted.",
              f"…the delete then adds only the plain line, and nothing opens twice ({lines()})")
    finally:
        controller._confirm_delete = saved_confirm
        restore()
    for project_id in ("project-7", "project-8"):
        if project_id in controller.pinned_projects():
            controller._pin_project(project_id, False)
    plugin.layers.remove(plugin.layers.layers_for("harbor-run"))
    if controller.projects_dialog is not None:
        controller.projects_dialog.close()
    session.select_project("project-2")
    wait_until(lambda: session.project.id == "project-2" and session.project.name == "Harbor", 5)


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
                       date(2026, 1, 1), date(2026, 2, 1), None, None, None)
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
    # a query that a newer one supersedes is aborted: its answer never reaches the window, and no line is said
    before = len(iface.bar.messages)
    controller.open_projects()                                       # its first query is pending until the loop runs
    window = controller.projects_dialog
    check(controller._projects_request != 0 and window.loading, "USER: a projects query is pending")
    controller._query_projects("Downtown")
    check(wait_until(lambda: [p.name for p in window.results] == ["Downtown survey"] and not window.loading
                     and controller._projects_request == 0, 8),
          f"USER: the newer query answers, and the window shows its results ({[p.name for p in window.results]})")
    settle()
    check(window.query == "Downtown" and [p.name for p in window.results] == ["Downtown survey"]
          and not lines(before) and not window.failed_text,
          f"…and the aborted query adds nothing and says nothing ({lines(before)}, {window.failed_text!r})")
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


def check_review_link(content, controller, processings, links, state, started):
    """spec/003 § Developer overrides, spec/007 § Layer rules: "Review this result in Mapflow Web" opens the
    processing in its project, on the web address of the session configuration (the override, else the
    environment's). The page only emits `openWeb`; the controller builds the URL. The URL is read where the link
    opens it. Everything the function changes is restored."""
    import dataclasses
    session, page, pid = controller.session, content.processings, started["id"]
    saved_config, item = session.config, next(p for p in state.processings if p["id"] == pid)

    def review_button():
        return next((b for b in page.findChildren(QPushButton)
                     if b.text().startswith("Review this result in Mapflow Web")), None)

    def refresh():
        page.refresh_button.click()
        wait_until(lambda: not page.refreshing, 5)

    item["reviewStatus"] = {"reviewStatus": "IN_REVIEW"}
    try:
        refresh()
        check(wait_until(lambda: processings.get(pid) and processings.get(pid).needs_review, 5),
              "REVIEW LINK: a processing in review is loaded as such")
        page.expand(pid)
        check(wait_until(lambda: review_button() is not None, 3),
              "REVIEW LINK: an expanded processing in review shows the link")

        session.config = dataclasses.replace(saved_config, web="https://web.example.test/")
        links.opened.clear()
        review_button().click()
        expected = f"https://web.example.test/projects/project-1?processing={pid}"
        check(links.opened == [expected], f"REVIEW LINK: opens the processing in its project, on the overridden "
                                          f"web address ({links.opened})")
        links.opened.clear()
        page.openWeb.emit(pid)
        check(links.opened == [expected], f"REVIEW LINK: the card menu's \"Open in Mapflow Web\" opens the same "
                                          f"address ({links.opened})")

        session.config = dataclasses.replace(saved_config, web="", env="duty")
        links.opened.clear()
        review_button().click()
        check(links.opened == [f"https://duty.mapflow.ai/projects/project-1?processing={pid}"],
              f"REVIEW LINK: with no override, the environment's web address applies ({links.opened})")

        # the footer link of the page opens the web address of the session configuration too
        footer = next((b for b in page.findChildren(QPushButton)
                       if b.text().startswith("Statistics and sharing in Mapflow Web")), None)
        links.opened.clear()
        footer.click()
        check(links.opened == ["https://duty.mapflow.ai"],
              f"REVIEW LINK: the footer link opens the environment's web address ({links.opened})")
        session.config = dataclasses.replace(saved_config, web="https://web.example.test/")
        links.opened.clear()
        footer.click()
        check(links.opened == ["https://web.example.test"],
              f"REVIEW LINK: …and the overridden one ({links.opened})")
    finally:
        session.config = saved_config
        item["reviewStatus"] = None
        refresh()
        wait_until(lambda: processings.get(pid) and not processings.get(pid).needs_review, 5)
        links.opened.clear()


def check_restart(iface, content, controller, processings, state):
    """spec/002_B § Plugin behaviour: Restart is offered for a failed or a cancelled processing, to every role that
    may run one (not only to those who may manage), and never for one in progress or awaiting. After a restart
    the list refreshes and the poll runs again. A refused restart shows the server's message and leaves no false
    state behind. Everything the function changes is restored."""
    from mapflow_next.core.models import Role, Status
    session, page = controller.session, content.processings
    warn = Qgis.MessageLevel.Warning
    saved_role, saved_interval = session.project.role, processings._poll.interval()
    failed_notices = []
    processings.failed.connect(failed_notices.append)
    extra = {"cancelled": fixtures.processing_json("restart-cancelled", "CANCELLED", 0, name="Cancelled run"),
             "awaiting": fixtures.processing_json("restart-awaiting", "AWAITING", 0, name="Awaiting run"),
             "running": fixtures.processing_json("restart-running", "IN_PROGRESS", -200, name="Running run")}
    # (-200: the mock adds 50 at each list request, so this one stays in progress for the next few lists)

    def restart_button(pid):
        page.expand(pid)
        wait_until(lambda: page.expanded == pid, 2)
        return next((b for b in page.findChildren(QPushButton) if b.text() == "Restart"), None)

    def menu_texts():
        return [a.text() for tool in page.findChildren(QToolButton) if tool.menu() for a in tool.menu().actions()]

    def posts(pid):
        return [r for r in state.requests if r[0] == "POST" and r[1] == f"/processings/{pid}/restart/v2"]

    def lists():
        return len([r for r in state.requests if r[0] == "POST" and r[1].endswith("/processings/v2/page")])

    def reload():
        page.refresh_button.click()
        wait_until(lambda: not page.refreshing, 5)

    def set_role(role):
        session.project.role = role
        controller.render_processings()

    def status_of(pid):
        item = processings.get(pid)
        return item.status if item else None

    state.restart_refused = None
    state.processings.extend(extra[k] for k in ("cancelled", "awaiting"))
    try:
        reload()
        check(wait_until(lambda: status_of("restart-cancelled") is Status.cancelled
                         and status_of("restart-awaiting") is Status.awaiting, 5),
              "RESTART: a cancelled and an awaiting processing are loaded")

        # not offered: ok, in progress, awaiting
        for pid, what in (("old-1", "an OK"), ("restart-awaiting", "an awaiting")):
            check(restart_button(pid) is None, f"RESTART: not offered for {what} processing")
        state.processings.append(extra["running"])
        reload()
        check(status_of("restart-running") is Status.in_progress and restart_button("restart-running") is None,
              f"RESTART: not offered for a processing in progress ({status_of('restart-running')})")

        # a role that may run but not manage: offered, and Rename and Delete are not
        set_role(Role.contributor)
        check(restart_button("old-2") is not None and restart_button("restart-cancelled") is not None,
              "RESTART: a contributor (may run, may not manage) is offered Restart for a failed and a cancelled one")
        check("Rename…" not in menu_texts() and "Delete…" not in menu_texts(),
              f"RESTART: …and Rename and Delete stay for those who manage ({menu_texts()})")
        # a role that may not run: not offered, and a stale signal sends nothing
        set_role(Role.readonly)
        check(restart_button("old-2") is None and restart_button("restart-cancelled") is None,
              "RESTART: a read-only role is not offered Restart")
        page.restart.emit("old-2")
        page.restart.emit("restart-cancelled")
        wait_until(lambda: False, 0.4)
        check(not posts("old-2") and not posts("restart-cancelled"),
              "RESTART: a restart signal for a role that may not run sends no request")
        for role in (Role.maintainer, Role.owner):
            set_role(role)
            check(restart_button("old-2") is not None and restart_button("restart-cancelled") is not None,
                  f"RESTART: a {role.value} is offered Restart for a failed and a cancelled one")

        # a refused restart: the server's message, nothing else
        set_role(Role.contributor)
        state.restart_refused = (403, "FORBIDDEN", "Restart refused: the project is locked")
        since = len(iface.bar.messages)
        restart_button("old-2").click()
        check(wait_until(lambda: (warn, "Restart refused: the project is locked") in iface.bar.messages[since:], 5),
              "RESTART: a refused restart shows the message of the server in the message bar")
        wait_until(lambda: False, 0.4)
        check(status_of("old-2") is Status.failed and not failed_notices and len(posts("old-2")) == 1,
              "RESTART: …the processing still shows as failed, and no \"failed\" notice follows")
        state.restart_refused = None

        # failed and cancelled: restarted, the list refreshes, the poll runs again
        processings._poll.setInterval(150)
        for pid in ("old-2", "restart-cancelled"):
            processings._poll.stop()
            failed_notices.clear()
            asked = lists()
            button = restart_button(pid)
            check(button is not None, f"RESTART: {pid} is offered Restart to a contributor")
            button.click()
            check(wait_until(lambda: len(posts(pid)) >= 1 and lists() > asked, 5),
                  f"RESTART: {pid}: the request is sent and the list refreshes")
            check(wait_until(lambda: status_of(pid) is Status.in_progress or status_of(pid) is Status.ok, 5)
                  and wait_until(lambda: processings._poll.isActive() or status_of(pid) is Status.ok, 2),
                  f"RESTART: {pid} shows as in progress and the poll runs again")
            check(wait_until(lambda: status_of(pid) is Status.ok, 5),
                  f"RESTART: {pid}: the poll loads it as finished")
            wait_until(lambda: False, 0.2)
            check(not failed_notices, f"RESTART: {pid}: no \"failed\" notice ({failed_notices})")
    finally:
        processings.failed.disconnect(failed_notices.append)
        processings._poll.setInterval(saved_interval)
        state.restart_refused = None
        ids = {item["id"] for item in extra.values()}
        state.processings = [p for p in state.processings if p["id"] not in ids]
        for item in state.processings:
            if item["id"] == "old-2":
                item.update(status="FAILED", percentCompleted=0,
                            messages=[{"code": "dataloader.NoDataTile", "parameters": {}}])
        set_role(saved_role)
        reload()


def deliver_page(processings, listing, items):
    """The answer of a list request, handed over as the HTTP layer does: sent after everything done so far, for the
    state of the listing now. `limit` is the number of items, so the answer is not taken for the whole project."""
    processings._on_page(listing, processings.project.id, listing.token, max(len(items), 1), processings._sent,
                         items, len(items))


def check_processing_search(iface, content, controller, processings, state):
    """spec/002_B § Plugin behaviour: the search sends `terms` to Mapflow, so it covers the whole project and not
    only the pages loaded. It waits for typing to pause. "Show more" and the poll keep the terms; an answer for an
    older text changes nothing; a search with no match, or one that failed, does not say the project is empty; a
    cleared field shows the full listing at once. The search is a listing of its own: the full listing stays loaded
    and keeps its poll, and the Start tab reads it. The poll watches the full listing, the search listing and the
    opened card: each gives the notice once, whichever sees the change first. "Show" in a notice fetches a
    processing that is not on the loaded pages. Everything the function changes is restored."""
    from mapflow_next.core.models import Processing as ProcessingModel, Status
    from mapflow_next.ui.processings_page import ProcessingCard
    from mapflow_next.ui.start_page import _MiniCard
    page, path = content.processings, "/projects/project-1/processings/v2/page"
    session = controller.session
    saved_interval, saved_project = processings._poll.interval(), session.project.id
    needle = fixtures.processing_json("search-needle", "OK", 100, name="Needle deep")
    bulk = [fixtures.processing_json(f"search-bulk-{n}", "OK", 100, name=f"Bulk {n}") for n in range(1, 35)]
    running = fixtures.processing_json("search-running", "IN_PROGRESS", -1000, name="Bulk running")
    slow = fixtures.processing_json("search-slow", "OK", 100, name="Slow survey")
    late = fixtures.processing_json("search-late", "IN_PROGRESS", -300, name="Late run")
    failing = fixtures.processing_json("search-failing", "IN_PROGRESS", -300, name="Failing run")
    other = dict(fixtures.processing_json("search-other", "OK", 100, name="Other project run"), projectId="project-2")
    extra = [needle] + bulk + [running, slow]
    solo = fixtures.processing_json("search-solo", "OK", 100, name="Solo survey")
    solo_two = fixtures.processing_json("search-solo-two", "OK", 100, name="Solo second")
    live = fixtures.processing_json("search-live", "IN_PROGRESS", -5000, name="Live run")
    ids = {item["id"] for item in extra + [late, failing, other, solo, solo_two, live]}
    warn = Qgis.MessageLevel.Warning
    finished, failed_notices, added = [], [], []
    processings.finished.connect(finished.append)
    processings.failed.connect(failed_notices.append)
    controller.results.add_to_map = lambda processing: added.append(processing.id)

    def bodies():
        return [r[2] for r in state.requests if r[0] == "POST" and r[1] == path]

    def with_terms(text):
        return [b for b in bodies() if b.get("terms") == text]

    def names():
        return sorted(c.processing.name for c in page.findChildren(ProcessingCard))

    def full_total():
        return len([p for p in state.processings if p["projectId"] == "project-1"])

    def gets(pid):
        return [r for r in state.requests if r[0] == "GET" and r[1] == f"/processings/{pid}/v2"]

    def recent():
        return [card.processing_id for card in content.start.findChildren(_MiniCard)]

    def lines():
        return [text for _level, text in iface.bar.messages]

    def reload():
        processings.opened = None
        page.search.clear()
        page.refresh_button.click()
        wait_until(lambda: not page.refreshing, 5)

    def press_show():
        button = next(b for b in iface.bar.widgets[-1].findChildren(QPushButton) if b.text() == "Show")
        button.click()

    def model(item):
        return ProcessingModel.from_api(item)

    def same_full():
        """The full listing holds the same processings as when it was loaded, and counts the same."""
        return [p.id for p in processings.items] == [p.id for p in full] and processings.total == total

    def search(text, count=None):
        page.search.setText(text)
        return wait_until(lambda: processings.terms == text and not processings._found.loading
                          and (count is None or len(processings.found) == count), 5)

    state.page_delay = {}
    full, total = [], 0
    state.processings = [solo, solo_two, needle] + state.processings + bulk + [running, slow, other]
    processings._poll.setInterval(60000)        # the flow leaves a short one: polls would blur the request counts
    try:
        reload()
        check(wait_until(lambda: len(processings.items) == 30 and processings.total == full_total(), 5),
              "SEARCH: the full list loads: the first 30 of the project")
        check(processings.get("search-needle") is None and not any(b.get("terms") for b in bodies()),
              "SEARCH: the oldest processing is not on the loaded pages, and no request has carried terms")
        full, total = list(processings.items), processings.total

        # the whole project, after a pause
        page.search.setText("needle")
        check(not with_terms("needle"), "SEARCH: right after typing no request is sent (the pause)")
        check(wait_until(lambda: len(with_terms("needle")) == 1, 3)
              and with_terms("needle")[0].get("offset") == 0 and with_terms("needle")[0].get("limit") == 30,
              "SEARCH: after the pause one request carries the terms, from offset 0")
        check(wait_until(lambda: names() == ["Needle deep"], 3),
              f"SEARCH: the page shows the processing that was not on the loaded pages ({names()})")
        check([p.name for p in processings.found] == ["Needle deep"] and processings.found_total == 1
              and same_full(),
              "SEARCH: the matches are a listing of their own: the full listing is neither emptied nor changed")

        # an action on a card that only the search shows
        page.addToMap.emit("search-needle")
        check(added == ["search-needle"], f"SEARCH: “Add to map” works on a processing that only the search holds "
                                          f"({added})")
        added.clear()

        # a cleared field shows the full listing at once, from memory
        asked = len(bodies())
        page.search.clear()
        check(len(names()) == 30 and len(page.items) == 30 and all(a is b for a, b in zip(page.items, full))
              and processings.terms == "" and not processings.found and not page._debounce.isActive(),
              f"SEARCH: a cleared field shows the same first 30 in the same event-loop turn ({len(names())})")
        wait_until(lambda: False, 0.5)
        check(len(bodies()) == asked and page.terms == "" and page.more_button is not None
              and f"30 of {total}" in page.more_button.text(),
              "SEARCH: …with no request, and “Show more” counts the full listing")

        # typing: one request for the burst
        for text in ("b", "bu", "bul", "bulk"):
            page.search.setText(text)
            wait_until(lambda: False, 0.03)
        check(wait_until(lambda: len(with_terms("bulk")) == 1, 3), "SEARCH: typing in a burst sends one request")
        wait_until(lambda: False, 0.6)
        sent = [(b.get("terms"), b.get("offset"), b.get("limit")) for b in bodies()[asked:]]
        check([s[0] for s in sent] == ["bulk"], f"SEARCH: …with the final text, none for the keys before it ({sent})")
        check(wait_until(lambda: len(names()) == 30 and processings.found_total == 35, 5),
              "SEARCH: 30 of the 35 matches show")

        # no local filter of the loaded rows
        before = [p.id for p in page.items]
        page.search.setText("zzz")
        page._debounce.stop()
        check([p.id for p in page._visible()] == before,
              "SEARCH: the text does not filter the loaded rows on this side")
        page.search.setText("bulk")
        page._debounce.stop()

        # "Show more" keeps the terms
        check(page.more_button is not None and "30 of 35" in page.more_button.text(),
              "SEARCH: “Show more” counts the matches")
        asked = len(bodies())
        page.more_button.click()
        check(wait_until(lambda: any(b.get("terms") == "bulk" and b.get("offset") == 30 for b in bodies()[asked:]), 3),
              "SEARCH: “Show more” sends the terms, from the offset of the rows shown")
        check(wait_until(lambda: len(names()) == 35, 5) and all("Bulk" in n for n in names()),
              "SEARCH: …and the page shows all 35 matches, and only them")
        check(same_full() and len(processings.found) == 35,
              "SEARCH: …and the full listing has no row of it")

        # the poll: one tick asks the full listing and the search; a finished processing is one notice
        running["status"], running["percentCompleted"] = "IN_PROGRESS", -200
        processings.refresh_shown(LOAD)
        check(wait_until(lambda: processings.get("search-running") is not None
                         and processings.get("search-running").status is Status.in_progress
                         and any(p.id == "search-running" and p.status is Status.in_progress
                                 for p in processings.found), 5),
              "SEARCH: a running processing is on both listings")
        finished.clear()
        processings._poll.setInterval(150)
        processings._poll.start()
        asked = len(bodies())
        check(wait_until(lambda: any("terms" not in b for b in bodies()[asked:])
                         and any(b.get("terms") == "bulk" for b in bodies()[asked:]), 5),
              "SEARCH: one poll tick asks the full listing, with no terms, and the search, with its terms")
        check(all(b.get("terms") in (None, "bulk") and b.get("offset") == 0 for b in bodies()[asked:]),
              f"SEARCH: …and the poll keeps the terms and the first page "
              f"({[b.get('terms') for b in bodies()[asked:]]})")
        check(wait_until(lambda: all(p.status is Status.ok for p in processings.found if p.id == "search-running")
                         and processings.get("search-running").status is Status.ok
                         and next(p for p in processings.items if p.id == "search-running").status is Status.ok, 8),
              "SEARCH: …its running processing finishes in the search rows and in the full listing")
        wait_until(lambda: False, 0.5)
        check([p.id for p in finished] == ["search-running"],
              f"SEARCH: …and the finish is one notice, not two ({[p.id for p in finished]})")
        processings._poll.setInterval(60000)
        processings._poll.stop()
        check(len(names()) == 35, "SEARCH: the polls keep the 35 matches")

        # an answer for an older text does not replace a newer list
        state.page_delay = {"slow": 1.5}
        page.search.setText("slow")
        check(wait_until(lambda: len(with_terms("slow")) == 1, 3), "SEARCH: the slow request is in flight")
        check(recent() == [p.id for p in full[:2]] and same_full(),
              f"SEARCH: while the search request is open the Start tab still shows the full listing ({recent()})")
        page.search.setText("needle")
        check(wait_until(lambda: names() == ["Needle deep"] and processings.terms == "needle", 5),
              "SEARCH: the newer text shows its list while the older request is in flight")
        text = page.empty_text.text()
        wait_until(lambda: False, 2)
        check(names() == ["Needle deep"] and processings.terms == "needle" and page.empty_text.text() == text
              and [p.name for p in processings.found] == ["Needle deep"] and same_full(),
              f"SEARCH: the late answer for the older text changes nothing ({names()})")
        state.page_delay = {}

        # …also an answer for "Show more"
        page.search.setText("bulk")
        check(wait_until(lambda: len(names()) == 30 and processings.terms == "bulk", 5),
              "SEARCH: the 30 first matches show again")
        state.page_delay = {"bulk": 1.5}
        asked = len(bodies())
        page.more_button.click()
        check(wait_until(lambda: any(b.get("offset") == 30 for b in bodies()[asked:]), 3),
              "SEARCH: a “Show more” request is in flight")
        page.search.setText("needle")
        check(wait_until(lambda: names() == ["Needle deep"] and processings.terms == "needle", 5),
              "SEARCH: the text changes before the page comes")
        wait_until(lambda: False, 2)
        check(names() == ["Needle deep"] and [p.name for p in processings.found] == ["Needle deep"]
              and not processings.found_loading_more and same_full(),
              f"SEARCH: the late page adds no row to the newer list ({names()})")
        state.page_delay = {}

        # a clear while a search request is in flight: the late answer changes nothing
        state.page_delay = {"slow": 1.5}
        asked = len(with_terms("slow"))
        page.search.setText("slow")
        check(wait_until(lambda: len(with_terms("slow")) == asked + 1, 3), "SEARCH: a slow request is in flight")
        page.search.clear()
        check(len(names()) == 30 and processings.terms == "", "SEARCH: the field is cleared at once")
        wait_until(lambda: False, 2)
        check(len(names()) == 30 and not processings.found and processings.terms == "" and page.terms == ""
              and same_full(),
              f"SEARCH: the late answer after a clear changes nothing ({names()}, {processings.found})")
        state.page_delay = {}

        # no match
        page.search.setText("zzzz-nothing")
        shown = "No processings match “zzzz-nothing”."
        check(wait_until(lambda: page.empty_text.text() == shown, 5),
              f"SEARCH: a search with no match says so ({page.empty_text.text()!r})")
        check(not names() and not page.start_button.isVisibleTo(page.empty) and page.more_button is None,
              "SEARCH: …shows no card, no “Start mapping” and no “Show more”")
        page.set_items([], set(), set(), True, loaded=True)
        check(page.empty_text.text() == "No processings in this project yet."
              and page.start_button.isVisibleTo(page.empty),
              "SEARCH: …and a project with no processings says that, with “Start mapping”")
        controller.render_processings()
        check(page.terms == "zzzz-nothing" and same_full(),
              "SEARCH: …and the full listing stays loaded")

        # the full listing keeps its poll, and its notices and the automatic add to map work, under that search
        check(recent() == [p.id for p in full[:2]],
              f"SEARCH: the Start tab shows the two newest of the full listing, not the matches ({recent()})")
        state.processings += [late, failing]
        processings.refresh_shown(LOAD)
        check(wait_until(lambda: processings.get("search-late") is not None
                         and processings.get("search-failing") is not None, 5),
              "SEARCH: a processing started meanwhile is on the full listing")
        check(recent() == ["search-failing", "search-late"] and page.terms == "zzzz-nothing"
              and not processings.found,
              f"SEARCH: …the Start tab shows it, and the search still has no match ({recent()})")
        check(content.tab_buttons[1].badge == len([p for p in processings.items if p.is_running]) == 2,
              f"SEARCH: …and the running badge counts the full listing ({content.tab_buttons[1].badge})")
        processings.started_here.add("search-late")
        finished.clear()
        failed_notices.clear()
        since = len(iface.bar.messages)
        failing["status"] = "FAILED"
        processings._poll.setInterval(150)
        processings._poll.start()
        check(wait_until(lambda: "search-late" in added and [p.id for p in finished] == ["search-late"], 10),
              f"SEARCH: a processing of the full listing that finishes is added to the map under a search "
              f"({added}, {[p.id for p in finished]})")
        check(any("“Late run” is ready. Adding the results to the map…" in (t or "") for t in lines()[since:]),
              "SEARCH: …with the “is ready” notice")
        check(wait_until(lambda: [p.id for p in failed_notices] == ["search-failing"], 5)
              and any("“Failing run” failed." in (t or "") for t in lines()[since:]),
              "SEARCH: …and a processing that fails gives the “failed” notice")
        check(page.terms == "zzzz-nothing" and not names() and not processings.found,
              "SEARCH: …while the page goes on showing the search with no match")
        processings._poll.setInterval(60000)
        processings._poll.stop()
        added.clear()
        wait_until(lambda: False, 0.3)

        # the search listing gives notices too: two processings that only the search holds (they are the oldest)
        reload()
        check(processings.get("search-solo") is None and processings.get("search-solo-two") is None
              and not processings._full.active,
              "SEARCH NOTICES: the two old processings are not on the loaded pages, and those pages are all final")
        solo.update(status="IN_PROGRESS", percentCompleted=-200)
        solo_two.update(status="IN_PROGRESS", percentCompleted=-200)
        finished.clear()
        failed_notices.clear()
        since = len(iface.bar.messages)
        check(search("solo", 2) and all(p.status is Status.in_progress for p in processings.found),
              "SEARCH NOTICES: the search finds both, in progress")
        processings._poll.stop()
        processings.refresh_shown(LOAD)
        check(wait_until(lambda: not processings._full.loading and not processings._found.loading, 5)
              and processings._found.active and not processings._full.active and processings._poll.isActive(),
              "SEARCH NOTICES: the matches run and the loaded pages are final: the poll continues")
        solo_two["status"] = "FAILED"
        for _ in range(8):
            if any(p.id == "search-solo" for p in finished):
                break
            processings._tick()
            wait_until(lambda: not processings._full.loading and not processings._found.loading, 5)
            wait_until(lambda: False, 0.2)
        wait_until(lambda: False, 0.4)
        check([p.id for p in finished] == ["search-solo"] and added == [],
              f"SEARCH NOTICES: a processing that only the search holds gives one “is ready” notice "
              f"({[p.id for p in finished]})")
        check(any("“Solo survey” is ready." in (t or "") for t in lines()[since:]),
              "SEARCH NOTICES: …in the message bar, with no automatic add to map (it was not started here)")
        check([p.id for p in failed_notices] == ["search-solo-two"]
              and any("“Solo second” failed." in (t or "") for t in lines()[since:]),
              f"SEARCH NOTICES: …and one that fails gives one “failed” notice ({[p.id for p in failed_notices]})")
        # an older answer, still in progress, arrives after the finish: no second notice (the same for the full
        # listing: check_answer_order)
        deliver_page(processings, processings._found, [model(dict(solo, status="IN_PROGRESS", percentCompleted=0))])
        processings._tick()
        wait_until(lambda: not processings._full.loading and not processings._found.loading, 5)
        wait_until(lambda: False, 0.3)
        check([p.id for p in finished] == ["search-solo"] and processings._last_status["search-solo"] is Status.ok,
              "SEARCH NOTICES: an older answer in progress does not give the notice a second time")
        controller.on_failed(failed_notices[0])
        press_show()
        check(wait_until(lambda: page.opened is not None and page.opened.id == "search-solo-two", 5)
              and page.expanded == "search-solo-two",
              "SEARCH NOTICES: the “failed” notice has a “Show” action that opens the card")
        processings._poll.stop()

        # a search whose matches are final, with a processing of the full listing running: the poll continues
        processings.opened = None
        state.processings.append(live)
        live.update(status="IN_PROGRESS", percentCompleted=-5000)
        reload()
        check(search("needle", 1) and not processings._found.active, "SEARCH POLL: the matches are all final")
        processings._poll.stop()
        processings.refresh_shown(LOAD)
        check(wait_until(lambda: not processings._full.loading and not processings._found.loading, 5)
              and processings._full.active and processings._poll.isActive(),
              "SEARCH POLL: …a processing of the full listing runs: the poll continues")
        processings._poll.stop()
        state.processings.remove(live)
        added.clear()
        reload()

        # "Show" in a notice: the card of a processing that is not on the loaded pages is fetched by id
        reload()
        check(wait_until(lambda: len(names()) == 30 and processings.total == full_total(), 5),
              "SHOW: the full listing is loaded again, with the processings started meanwhile")
        full, total = list(processings.items), processings.total
        in_page = model(slow)
        check(processings.get("search-slow") is not None, "SHOW: the newest processing is on the loaded pages")
        asked = len(state.requests)
        controller.on_failed(in_page)
        press_show()
        by_id = [r for r in state.requests[asked:] if r[0] == "GET" and r[1].startswith("/processings/")
                 and not r[1].startswith("/processings/template/")]      # (the planned list is no fetch by id)
        check(page.expanded == "search-slow" and processings.opened is None and not by_id,
              "SHOW: a processing on the loaded pages opens its card, and nothing is fetched")

        state.fail("GET", r"/processings/.+/v2", 404)
        since = len(iface.bar.messages)
        controller.on_failed(model(needle))
        press_show()
        check(wait_until(lambda: any(level == warn and (text or "").startswith("Couldn't open the processing")
                                     for level, text in iface.bar.messages[since:]), 5),
              "SHOW: a processing that can't be fetched says so in the message bar")
        check(processings.opened is None and page.opened is None and len(names()) == 30,
              "SHOW: …shows no card")
        state.heal()

        fetched = len(gets("search-needle"))
        controller.on_failed(model(needle))
        press_show()
        check(wait_until(lambda: page.opened is not None and page.opened.id == "search-needle", 5)
              and len(gets("search-needle")) == fetched + 1,
              "SHOW: …and nothing is stuck: the processing is fetched by id the next time")
        first = page.list.itemAt(0).widget()
        check(isinstance(first, ProcessingCard) and first.processing.id == "search-needle"
              and page.expanded == "search-needle" and len(names()) == 31,
              "SHOW: …its card is expanded, above the cards of the loaded pages")
        check(processings.total == total and len(processings.items) == 30
              and page.more_button is not None and f"30 of {total}" in page.more_button.text(),
              "SHOW: …and the count and “Show more” are those of the loaded pages")
        asked = len(state.requests)
        controller.on_failed(model(needle))
        press_show()
        wait_until(lambda: False, 0.3)
        # (opening the tab refreshes the opened card: one GET by id at most, and "Show" itself asks for none)
        by_id = [r for r in state.requests[asked:] if r[0] == "GET" and r[1].startswith("/processings/")
                 and not r[1].startswith("/processings/template/")]
        check(len(by_id) <= 1
              and processings.open("search-needle") is False and page.opened.id == "search-needle",
              "SHOW: a processing that is already opened is not fetched again by “Show”")
        page.addToMap.emit("search-needle")
        check(added == ["search-needle"], f"SHOW: “Add to map” works on the opened card ({added})")
        added.clear()
        processings.opened = None
        controller.render_processings()

        # a processing of another project is refused
        since = len(iface.bar.messages)
        controller.on_failed(model(other))
        press_show()
        check(wait_until(lambda: (warn, "That processing is in another project.") in iface.bar.messages[since:], 5)
              and processings.opened is None and page.opened is None and len(names()) == 30,
              "SHOW: a processing of another project is refused with a message, and shows no card")

        # a search is shown when "Show" is clicked: the field is cleared and the full listing shows
        check(search("bulk", 30), "SHOW: a search is shown")
        fetched = len(gets("search-needle"))
        controller.on_failed(model(needle))
        press_show()
        check(page.search.text() == "" and processings.terms == "" and not processings.found,
              "SHOW: the search field is cleared by “Show”")
        check(wait_until(lambda: page.opened is not None and page.opened.id == "search-needle"
                         and len(names()) == 31 and page.expanded == "search-needle", 5)
              and page.terms == "" and len(gets("search-needle")) == fetched + 1,
              "SHOW: …and the card of a processing that only the search had found shows with the full listing")
        processings.opened = None
        controller.render_processings()

        # a failed search says so
        state.fail("POST", r"/projects/project-1/processings/v2/page", 503)
        since = len(iface.bar.messages)
        page.search.setText("needle")
        check(wait_until(lambda: any(level == warn and (text or "").startswith("Processings didn't load")
                                     for level, text in iface.bar.messages[since:]), 5),
              "SEARCH: a search that fails shows the failure in the message bar")
        check(wait_until(lambda: page.empty_text.text() == "Processings didn't load.", 3)
              and "No processings match" not in page.empty_text.text(),
              f"SEARCH: …and the page says that the list did not load ({page.empty_text.text()!r})")
        state.heal()

        # a new project clears the terms, the matches and the opened card
        check(search("bulk", 30), "PROJECT: a search is shown")
        processings.opened = model(needle)
        session.select_project("project-2")
        check(wait_until(lambda: session.project.id == "project-2" and processings.loaded, 5)
              and processings.terms == "" and not processings.found and processings.opened is None
              and page.search.text() == "" and page.terms == "", "PROJECT: a new project starts with no search")
        session.select_project(saved_project)
        check(wait_until(lambda: session.project.id == saved_project and len(processings.items) == 30, 5),
              "PROJECT: …(the project is back)")
    finally:
        processings.finished.disconnect(finished.append)
        processings.failed.disconnect(failed_notices.append)
        del controller.results.add_to_map
        state.heal()
        state.page_delay = {}
        processings.started_here.discard("search-late")
        processings._poll.setInterval(saved_interval)
        state.processings = [p for p in state.processings if p["id"] not in ids]
        if session.project.id != saved_project:
            session.select_project(saved_project)
            wait_until(lambda: session.project.id == saved_project, 5)
        reload()


def check_opened_card(iface, content, controller, processings, state):
    """spec/002_B § Plugin behaviour, spec/005 § Failed requests: the card that "Show" fetched by id is kept
    current: after Restart, Rename and a poll answer it shows the new status and name, and a second Restart is not
    sent while the first runs. A restart from a search card shows at once. "Show" for a second processing drops the
    late answer for the first. With a search shown, one failed Refresh gives one "Processings didn't load" line and
    one stop of the spinner (after both answers), and the poll gives one alert. Everything the function changes is
    restored. The opened card gives the notice, once, and keeps the poll running while it is not final."""
    from mapflow_next.core.models import Processing as ProcessingModel, Status
    from mapflow_next.ui.processings_page import ProcessingCard
    page, path = content.processings, "/projects/project-1/processings/v2/page"
    saved_interval = processings._poll.interval()
    added = []
    controller.results.add_to_map = lambda processing: added.append(processing.id)
    old = fixtures.processing_json("opened-failed", "FAILED", 0, name="Old failed run")
    old["messages"] = [{"code": "dataloader.NoDataTile", "parameters": {}}]
    zebra = fixtures.processing_json("search-restart", "FAILED", 0, name="Zebra restart")
    fillers = [fixtures.processing_json(f"opened-filler-{n}", "OK", 100, name=f"Filler {n}") for n in range(1, 33)]
    running = fixtures.processing_json("opened-running", "IN_PROGRESS", -5000, name="Filler running")
    fresh_run = fixtures.processing_json("opened-fresh", "IN_PROGRESS", -5000, name="Old running run")
    doomed = fixtures.processing_json("opened-doomed", "IN_PROGRESS", -5000, name="Old doomed run")
    ids = {item["id"] for item in [old, zebra, running, fresh_run, doomed] + fillers}
    finished, failed_notices, refreshed = [], [], []
    processings.finished.connect(finished.append)
    processings.failed.connect(failed_notices.append)

    def count_refreshed():
        refreshed.append(1)

    processings.refreshed.connect(count_refreshed)

    def card(pid):
        return next((c for c in page.findChildren(ProcessingCard) if c.processing.id == pid), None)

    def restart_buttons():
        return [b for b in page.findChildren(QPushButton) if b.text() == "Restart"]

    def posts(pid):
        return [r for r in state.requests if r[0] == "POST" and r[1] == f"/processings/{pid}/restart/v2"]

    def gets(pid):
        return [r for r in state.requests if r[0] == "GET" and r[1] == f"/processings/{pid}/v2"]

    def lines():
        return [text for _level, text in iface.bar.messages]

    def settle():
        return wait_until(lambda: not processings._full.loading and not processings._found.loading, 5)

    def reload():
        processings.opened = None
        page.search.clear()
        page.refresh_button.click()
        wait_until(lambda: not page.refreshing, 5)
        settle()

    def search(text):
        page.search.setText(text)
        return wait_until(lambda: processings.terms == text and processings._found.loaded
                          and not processings._found.loading, 5)

    def press_show():
        button = next(b for b in iface.bar.widgets[-1].findChildren(QPushButton) if b.text() == "Show")
        button.click()

    def tick_until(done):
        for _ in range(8):
            if done():
                return True
            processings._tick()
            settle()
            wait_until(lambda: False, 0.3)
        return done()

    state.page_delay = {}
    state.processings = [doomed, fresh_run, old, zebra] + state.processings + fillers + [running]
    processings._poll.setInterval(60000)        # the checks tick by hand
    try:
        reload()
        check(wait_until(lambda: processings.get("opened-running") is not None, 5)
              and processings.get("opened-failed") is None and processings.get("search-restart") is None,
              "OPENED: the old processings are not on the loaded pages, and one is running")

        # Restart from the opened card: one request, the card shows the new status, the poll keeps it current
        controller.open_processing("opened-failed")
        check(wait_until(lambda: page.opened is not None and page.opened.id == "opened-failed", 5)
              and card("opened-failed") is not None and card("opened-failed").processing.status is Status.failed
              and len(restart_buttons()) == 1,
              "OPENED: “Show” fetches the old failed processing, and its card offers Restart")
        fetched = len(gets("opened-failed"))
        page.restart.emit("opened-failed")
        page.restart.emit("opened-failed")
        check(wait_until(lambda: len(posts("opened-failed")) >= 1 and card("opened-failed") is not None
                         and card("opened-failed").processing.status is Status.in_progress, 5),
              "OPENED: after Restart the opened card shows the processing in progress")
        wait_until(lambda: False, 0.4)
        check(len(posts("opened-failed")) == 1 and not restart_buttons(),
              f"OPENED: …a second Restart while it runs sends nothing ({len(posts('opened-failed'))}), and the "
              f"card has no Restart button")
        check(len(gets("opened-failed")) > fetched, "OPENED: …and the card was fetched again after the restart")
        check(tick_until(lambda: card("opened-failed") is not None
                         and card("opened-failed").processing.status is Status.ok),
              "OPENED: a poll answer brings the opened card to OK")
        wait_until(lambda: False, 0.5)
        check([p.id for p in finished if p.id == "opened-failed"] == ["opened-failed"]
              and not [p for p in failed_notices if p.id == "opened-failed"]
              and added.count("opened-failed") == 1,
              f"OPENED: …and the opened card gives one notice, and one automatic add to map "
              f"({[p.id for p in finished]}, {added})")
        for _ in range(3):
            processings._tick()
            settle()
        wait_until(lambda: False, 0.3)
        check(len([p for p in finished if p.id == "opened-failed"]) == 1 and added.count("opened-failed") == 1,
              "OPENED: …later polls add nothing")

        # Rename of the opened card
        fetched = len(gets("opened-failed"))
        processings.rename(processings.opened, "Renamed run", "")
        check(wait_until(lambda: card("opened-failed") is not None and card("opened-failed").processing.name
                         == "Renamed run", 5) and len(gets("opened-failed")) > fetched,
              "OPENED: after Rename the opened card shows the new name")

        # Restart from a search card shows at once, before the list answer
        reload()
        check(search("zebra") and [p.id for p in processings.found] == ["search-restart"],
              "SEARCH CARD: the search finds the old failed processing")
        if page.expanded != "search-restart":
            page._toggle("search-restart")
        check(card("search-restart") is not None and len(restart_buttons()) == 1,
              "SEARCH CARD: its card offers Restart")
        state.page_delay = {"zebra": 1.0}
        page.restart.emit("search-restart")
        page.restart.emit("search-restart")
        check(wait_until(lambda: card("search-restart") is not None
                         and card("search-restart").processing.status is Status.in_progress, 0.8),
              "SEARCH CARD: after Restart the card shows in progress before the refreshed list comes")
        check(not restart_buttons() and len(posts("search-restart")) == 1,
              "SEARCH CARD: …with no Restart button, and one request")
        state.page_delay = {}
        settle()
        check(tick_until(lambda: card("search-restart") is not None
                         and card("search-restart").processing.status is Status.ok),
              "SEARCH CARD: …and a poll answer brings it to OK")
        wait_until(lambda: False, 0.5)
        check([p.id for p in finished].count("search-restart") == 1 and added.count("search-restart") == 1,
              f"SEARCH CARD: …and the restart from a search card gives one notice, and one add to map "
              f"({[p.id for p in finished]}, {added})")

        # An old processing in progress that "Show" opens, while the loaded pages are final: the poll starts for
        # the card, and its end is one notice
        running.update(status="OK", percentCompleted=100)
        fresh_run.update(status="IN_PROGRESS", percentCompleted=-100)
        reload()
        processings._poll.stop()
        check(processings._full.loaded and not processings._full.active and not processings._poll.isActive(),
              "OPENED POLL: the loaded pages are all final, and nothing is polled")
        controller.open_processing("opened-fresh")
        check(wait_until(lambda: processings.opened is not None and processings.opened.id == "opened-fresh", 5),
              "OPENED POLL: “Show” fetches the old processing in progress")
        check(processings.opened.status is Status.in_progress and processings._poll.isActive(),
              "OPENED POLL: …and the poll runs for the card")
        processings._poll.setInterval(200)
        processings._poll.start()
        check(wait_until(lambda: card("opened-fresh") is not None
                         and card("opened-fresh").processing.status is Status.ok, 8),
              "OPENED POLL: …and the card follows the processing to OK with no click")
        wait_until(lambda: False, 0.5)
        check([p.id for p in finished].count("opened-fresh") == 1 and not any(
              p.id == "opened-fresh" for p in failed_notices),
              f"OPENED POLL: …with one notice ({[p.id for p in finished]})")
        processings._poll.stop()
        processings._poll.setInterval(60000)

        # An opened card that fails gives one "failed" notice
        finished.clear()
        reload()
        processings._poll.stop()
        controller.open_processing("opened-doomed")
        check(wait_until(lambda: processings.opened is not None and processings.opened.id == "opened-doomed"
                         and processings.opened.status is Status.in_progress, 5),
              "OPENED FAIL: “Show” fetches the processing in progress again")
        doomed["status"] = "FAILED"
        processings._tick()
        settle()
        wait_until(lambda: processings.opened is not None and processings.opened.status is Status.failed, 5)
        for _ in range(3):
            processings._tick()
            settle()
        wait_until(lambda: False, 0.3)
        check([p.id for p in failed_notices].count("opened-doomed") == 1
              and not [p for p in finished if p.id == "opened-doomed"],
              f"OPENED FAIL: the opened card that fails gives one “failed” notice "
              f"({[p.id for p in failed_notices]})")

        # "Show" for A (not loaded), then at once for B (loaded): the late answer for A changes nothing
        reload()
        controller.on_failed(ProcessingModel.from_api(old))
        press_show()
        controller.on_failed(ProcessingModel.from_api(running))
        press_show()
        wait_until(lambda: False, 1.0)
        check(processings.opened is None and page.opened is None and page.expanded == "opened-running",
              f"OPENED TOKEN: “Show” for a loaded processing drops the answer for the one asked before "
              f"({processings.opened})")

        # A failed Refresh under a search: one line, one stop of the spinner, after both answers
        reload()
        check(search("zebra"), "REFRESH: a search is shown")
        state.page_delay = {"zebra": 1.0}
        state.fail("POST", path, 503)
        since, refreshed[:] = len(iface.bar.messages), []
        page.refresh_button.click()
        check(wait_until(lambda: not processings._full.loading, 3), "REFRESH: the full list answers first")
        wait_until(lambda: False, 0.7)
        check(processings._found.loading and page.refreshing,
              "REFRESH: …the spinner goes on while the search answer is on its way")
        check(wait_until(lambda: not processings._found.loading and not page.refreshing, 5),
              "REFRESH: …and stops after the second answer")
        wait_until(lambda: False, 0.3)
        said = [t for t in lines()[since:] if (t or "").startswith("Processings didn't load")]
        check(len(said) == 1 and len(refreshed) == 1,
              f"REFRESH: one failed Refresh gives one message and one `refreshed` ({said}, {len(refreshed)})")
        state.heal()
        state.page_delay = {}

        # The poll under a search, both lists failing: one alert
        processings.refresh_shown(LOAD)
        settle()
        check(processings._full.failures.count == 0 and processings._found.failures.count == 0,
              "POLL: both lists load again")
        since = len(iface.bar.messages)
        state.fail("POST", path, 503)
        for _ in range(config.POLL_FAILURES_BEFORE_ALERT):
            processings._tick()
            settle()
        alerts = [t for t in lines()[since:] if "Mapflow is not answering" in (t or "")]
        check(len(alerts) == 1, f"POLL: both lists failing give one alert ({alerts})")
        check(processings._full.failures.count == processings._found.failures.count
              == config.POLL_FAILURES_BEFORE_ALERT, "POLL: …and both lists counted every failure")
        state.heal()
        processings.refresh_shown(LOAD)
        settle()
        check(processings._full.failures.count == 0 and processings._found.failures.count == 0,
              "POLL: …and the counts return to 0 when they load")

        # A search cleared while the Refresh is in flight: the spinner stops
        state.page_delay = {"zebra": 1.0}
        page.refresh_button.click()
        check(wait_until(lambda: not processings._full.loading, 3) and processings._found.loading,
              "REFRESH: the search answer is on its way")
        page.search.clear()
        check(wait_until(lambda: not page.refreshing, 3), "REFRESH: clearing the search stops the spinner")
        wait_until(lambda: False, 1.2)
        check(not processings.found and processings.terms == "",
              "REFRESH: …and the late answer of the old search changes nothing")
    finally:
        processings.finished.disconnect(finished.append)
        processings.failed.disconnect(failed_notices.append)
        processings.refreshed.disconnect(count_refreshed)
        del controller.results.add_to_map
        state.heal()
        state.page_delay = {}
        processings._poll.stop()
        processings._poll.setInterval(saved_interval)
        state.processings = [p for p in state.processings if p["id"] not in ids]
        reload()


def check_answer_order(iface, content, controller, processings, state):
    """spec/002_B § Plugin behaviour, spec/005 § Failed requests: the answers of one poll tick come back in either
    order, and an older one never moves a processing from a final status back: one notice and one automatic add to
    map. A list answer sent before the server accepted a Restart gives no notice, no Restart button and no second
    restart, for the full listing and for the search listing. The opened card that Mapflow Web deleted leaves
    `opened` and stops its poll with one message; a transient failure is one alert and a retry after one interval.
    Everything the function changes is restored."""
    from mapflow_next.api.http import ApiError
    from mapflow_next.core.models import Processing as ProcessingModel, Status
    from mapflow_next.ui.processings_page import ProcessingCard
    page = content.processings
    saved_interval = processings._poll.interval()
    added = []
    controller.results.add_to_map = lambda processing: added.append(processing.id)
    runs = {n: fixtures.processing_json(f"order-{n}", "IN_PROGRESS", -100000, name=f"Order {n}") for n in "ab"}
    zulu = fixtures.processing_json("order-zulu", "FAILED", 0, name="Zulu restart")
    zulu["messages"] = [{"code": "dataloader.NoDataTile", "parameters": {}}]
    yankee = fixtures.processing_json("order-yankee", "FAILED", 0, name="Yankee restart")
    gone = fixtures.processing_json("order-gone", "IN_PROGRESS", -100000, name="Gone run")
    flaky = fixtures.processing_json("order-flaky", "IN_PROGRESS", -100000, name="Flaky run")
    fillers = [fixtures.processing_json(f"order-filler-{n}", "OK", 100, name=f"Filler {n}") for n in range(1, 33)]
    ids = {item["id"] for item in [*runs.values(), zulu, yankee, gone, flaky, *fillers]}
    finished, failed_notices = [], []
    processings.finished.connect(finished.append)
    processings.failed.connect(failed_notices.append)

    def model(item):
        return ProcessingModel.from_api(item)

    def lines():
        return [text for _level, text in iface.bar.messages]

    def settle():
        return wait_until(lambda: not processings._full.loading and not processings._found.loading, 5)

    def reload():
        processings.opened = None
        page.search.clear()
        page.refresh_button.click()
        wait_until(lambda: not page.refreshing, 5)
        settle()

    def search(text):
        page.search.setText(text)
        return wait_until(lambda: processings.terms == text and processings._found.loaded
                          and not processings._found.loading, 5)

    def card(pid):
        return next((c for c in page.findChildren(ProcessingCard) if c.processing.id == pid), None)

    def restart_buttons():
        return [b for b in page.findChildren(QPushButton) if b.text() == "Restart"]

    def posts(pid):
        return [r for r in state.requests if r[0] == "POST" and r[1] == f"/processings/{pid}/restart/v2"]

    def gets(pid):
        return [r for r in state.requests if r[0] == "GET" and r[1] == f"/processings/{pid}/v2"]

    state.page_delay = {}
    # (gone and flaky are the oldest, and the 32 fillers push them off the first page)
    state.processings = [gone, flaky] + state.processings + fillers + [*runs.values(), zulu, yankee]
    processings._poll.setInterval(60000)        # the checks tick by hand
    try:
        reload()
        check(all(processings.get(f"order-{n}") is not None and processings.get(f"order-{n}").status is
                  Status.in_progress for n in "ab"), "ORDER: two processings in progress are loaded")
        check(search("order") and len(processings.found) >= 2, "ORDER: a search shows them too")
        full, found = processings._full, processings._found

        # the search answer (OK) first, then the older full-listing answer (in progress), then a full answer (OK)
        run = runs["a"]
        processings.started_here.add("order-a")
        deliver_page(processings, found, [model(dict(run, status="OK", percentCompleted=100))])
        deliver_page(processings, full, [model(run)])
        deliver_page(processings, full, [model(dict(run, status="OK", percentCompleted=100))])
        check([p.id for p in finished] == ["order-a"] and added == ["order-a"] and not failed_notices,
              f"ORDER: search OK, then an older full answer in progress, then OK: one notice, one add to map "
              f"({[p.id for p in finished]}, {added})")

        # the other order: the full answer (OK) first, then the older search answer (in progress)
        run = runs["b"]
        processings.started_here.add("order-b")
        deliver_page(processings, full, [model(dict(run, status="OK", percentCompleted=100))])
        deliver_page(processings, found, [model(run)])
        deliver_page(processings, found, [model(dict(run, status="OK", percentCompleted=100))])
        check([p.id for p in finished] == ["order-a", "order-b"] and added == ["order-a", "order-b"],
              f"ORDER: full OK, then an older search answer in progress: one notice, one add to map "
              f"({[p.id for p in finished]}, {added})")
        processings._poll.stop()

        # a processing that was final and is restarted in Mapflow Web: the answer of a request sent after the final
        # one moves it back, and its next finish is a new one. Full listing:
        run = runs["a"]
        processings._sent += 1
        deliver_page(processings, full, [model(run)])
        check(processings.get("order-a").status is Status.in_progress and len(finished) == 2,
              "RESTART IN WEB: an answer of a later request moves a final processing to in progress, with no notice")
        deliver_page(processings, full, [model(dict(run, status="OK", percentCompleted=100))])
        check([p.id for p in finished] == ["order-a", "order-b", "order-a"]
              and added == ["order-a", "order-b", "order-a"],
              f"RESTART IN WEB: …its next finish is one notice and one add to map "
              f"({[p.id for p in finished]}, {added})")
        # …the search listing
        run = runs["b"]
        processings._sent += 1
        deliver_page(processings, found, [model(run)])
        check(next(p for p in processings.found if p.id == "order-b").status is Status.in_progress
              and len(finished) == 3, "RESTART IN WEB: …the same for the search listing")
        deliver_page(processings, found, [model(dict(run, status="OK", percentCompleted=100))])
        check([p.id for p in finished][3:] == ["order-b"] and added[3:] == ["order-b"],
              f"RESTART IN WEB: …and one notice and one add to map for its next finish ({added})")
        # …and the opened card
        opened_run = fixtures.processing_json("order-open", "IN_PROGRESS", -100000, name="Open run")
        processings.opened = model(opened_run)
        processings._note(processings.opened, processings._sent)
        asked = []

        def ask_card(status):
            """"Show"'s card is refreshed and the server answers with `status`."""
            processings.api.processing = lambda _pid, done, _failed=None: asked.append(done)
            try:
                processings._refresh_opened(LOAD)
            finally:
                del processings.api.processing
            asked.pop()(model(dict(opened_run, status=status, percentCompleted=100 if status == "OK" else 40)))

        before = len(finished)
        ask_card("OK")
        ask_card("IN_PROGRESS")
        check(processings.opened.status is Status.in_progress and len(finished) == before + 1,
              "RESTART IN WEB: …the opened card goes back to in progress, with no second notice")
        ask_card("OK")
        check(processings.opened.status is Status.ok and len(finished) == before + 2
              and finished[-1].id == "order-open", "RESTART IN WEB: …and its next finish is one notice")
        processings._note(model(dict(opened_run, status="IN_PROGRESS")), processings._sent)
        check(processings._last_status["order-open"] is Status.ok and len(finished) == before + 2,
              "RESTART IN WEB: …an answer of a request sent before the final one changes nothing")
        processings.opened = None
        processings._poll.stop()

        # a list answer sent before the accepted Restart still says FAILED: the full listing
        reload()
        if page.expanded != "order-zulu":
            page._toggle("order-zulu")
        check(processings.get("order-zulu") is not None and len(restart_buttons()) == 1
              and processings.get("order-zulu").status is Status.failed,
              "RESTART ANSWER: a failed processing of the full listing is offered Restart")
        failed_notices.clear()
        state.page_delay = {"": 1.2}
        processings.refresh(LOAD)
        wait_until(lambda: False, 0.2)
        page.restart.emit("order-zulu")
        check(wait_until(lambda: len(posts("order-zulu")) == 1 and processings.get("order-zulu").status
                         is Status.in_progress, 5), "RESTART ANSWER: the server accepts the restart")
        state.page_delay = {}
        seen = []

        def see_zulu(_items):
            seen.append(processings.get("order-zulu").status)

        processings.changed.connect(see_zulu)
        check(wait_until(lambda: len(seen) >= 2, 6), "RESTART ANSWER: the old answer of the full listing arrives")
        wait_until(lambda: False, 0.5)
        settle()
        check(Status.failed not in seen and not failed_notices and not restart_buttons()
              and len(posts("order-zulu")) == 1,
              f"RESTART ANSWER: …it brings no “failed” status, notice or Restart button, and no second restart "
              f"({seen}, {failed_notices})")
        processings.changed.disconnect(see_zulu)
        processings._poll.stop()

        # …and the search listing
        reload()
        check(search("yankee") and [p.id for p in processings.found] == ["order-yankee"],
              "RESTART ANSWER: the search finds a failed processing")
        if page.expanded != "order-yankee":
            page._toggle("order-yankee")
        check(len(restart_buttons()) == 1, "RESTART ANSWER: its card offers Restart")
        failed_notices.clear()
        state.page_delay = {"yankee": 1.2}
        processings.refresh_search(LOAD)
        wait_until(lambda: False, 0.2)
        page.restart.emit("order-yankee")
        check(wait_until(lambda: len(posts("order-yankee")) == 1 and card("order-yankee") is not None
                         and card("order-yankee").processing.status is Status.in_progress, 5),
              "RESTART ANSWER: the server accepts the restart from the search card")
        state.page_delay = {}
        seen = []

        def see_yankee(_items):
            seen.append(processings.get("order-yankee").status)

        processings.foundChanged.connect(see_yankee)
        check(wait_until(lambda: len(seen) >= 2, 6), "RESTART ANSWER: the old answer of the search arrives")
        wait_until(lambda: False, 0.5)
        settle()
        check(Status.failed not in seen and not failed_notices and not restart_buttons()
              and len(posts("order-yankee")) == 1,
              f"RESTART ANSWER: …it brings no “failed” status, notice or Restart button, and no second restart "
              f"({seen}, {failed_notices})")
        processings.foundChanged.disconnect(see_yankee)
        processings._poll.stop()

        # an opened card that Mapflow Web deleted: the poll stops for it, one message
        state.processings = [p for p in state.processings if p["id"] not in ("order-zulu", "order-yankee")]
        for run in runs.values():
            run.update(status="OK", percentCompleted=100)       # the loaded pages are final: only the card is watched
        reload()
        check(not processings._full.active and processings.get("order-gone") is None
              and processings.get("order-flaky") is None,
              "OPENED GONE: the loaded pages are final, and the two old processings are not on them")
        controller.open_processing("order-gone")
        check(wait_until(lambda: processings.opened is not None and processings.opened.id == "order-gone", 5)
              and page.opened is not None, "OPENED GONE: “Show” fetches a processing in progress")
        processings._poll.stop()
        state.processings = [p for p in state.processings if p["id"] != "order-gone"]
        since, fetched = len(iface.bar.messages), len(gets("order-gone"))
        processings._tick()
        settle()
        check(wait_until(lambda: processings.opened is None and page.opened is None, 5),
              "OPENED GONE: a 404 for the opened card ends its “opened” state")
        said = [t for t in lines()[since:] if "no longer refreshed" in (t or "")]
        check(len(said) == 1 and "opened processing" in said[0], f"OPENED GONE: …with one message ({said})")
        for _ in range(3):
            processings._tick()
            settle()
        wait_until(lambda: False, 0.3)
        check(len(gets("order-gone")) == fetched + 1
              and len([t for t in lines()[since:] if "no longer refreshed" in (t or "")]) == 1,
              f"OPENED GONE: …the poll asks for it no more and says nothing more ({len(gets('order-gone'))})")

        # the same tick with the answers handed over by hand: the list answer and the 404 in either order
        def tick_held():
            """One poll tick whose list request and card request wait: their answers are handed over by the check."""
            held = {}
            processings.api.processings = lambda _pid, done, _failed=None, **_kw: held.update(list=done)
            processings.api.processing = lambda _pid, _done, failed=None: held.update(gone=failed)
            try:
                processings._tick()
            finally:
                del processings.api.processings, processings.api.processing
            return held

        for first in ("list", "gone"):
            processings._poll.stop()
            processings._opened_failures.succeeded()
            processings.opened = model(dict(gone, status="IN_PROGRESS", percentCompleted=40))
            since = len(iface.bar.messages)
            held = tick_held()
            listed = list(processings.items)
            answers = {"list": lambda: held["list"](listed, len(listed)),
                       "gone": lambda: held["gone"](ApiError("not_found", "Not found.", 404))}
            for kind in (first, "gone" if first == "list" else "list"):
                answers[kind]()
            said = [t for t in lines()[since:] if "no longer refreshed" in (t or "")]
            check(not processings._poll.isActive() and processings.opened is None and page.opened is None
                  and len(said) == 1,
                  f"OPENED GONE: the {first} answer first, then the other: the poll is stopped, the card is cleared, "
                  f"one message ({processings._poll.isActive()}, {said})")

        # a transient failure for the opened card: one alert, and the poll is asked again after one interval
        controller.open_processing("order-flaky")
        check(wait_until(lambda: processings.opened is not None and processings.opened.id == "order-flaky", 5),
              "OPENED FLAKY: “Show” fetches another processing in progress")
        state.fail("GET", r"/processings/order-flaky/v2", 503)
        since = len(iface.bar.messages)
        for n in range(config.POLL_FAILURES_BEFORE_ALERT):
            processings._poll.stop()
            processings._tick()
            settle()
            check(wait_until(lambda: processings._opened_failures.count == n + 1, 5),
                  f"OPENED FLAKY: failure {n + 1} is counted")
        alerts = [t for t in lines()[since:] if "Mapflow is not answering" in (t or "")]
        check(len(alerts) == 1 and "opened processing" in alerts[0], f"OPENED FLAKY: …one alert ({alerts})")
        check(processings.opened is not None and processings._poll.isActive(),
              "OPENED FLAKY: …the card stays opened and the poll is set to ask again")
        state.heal()
        before = processings.opened.percent
        processings._tick()
        settle()
        check(wait_until(lambda: processings._opened_failures.count == 0 and processings.opened is not None
                         and processings.opened.percent != before, 5),
              "OPENED FLAKY: …and an answer brings the card up to date and resets the count")
    finally:
        processings.finished.disconnect(finished.append)
        processings.failed.disconnect(failed_notices.append)
        del controller.results.add_to_map
        state.heal()
        state.page_delay = {}
        processings._poll.stop()
        processings._poll.setInterval(saved_interval)
        state.processings = [p for p in state.processings if p["id"] not in ids]
        reload()


def planned_endpoint_only(state):
    """spec/002_F § Plugin behaviour in Mapflow Next: of the planned-processing endpoints the plugin sends only
    GET /processings/template/project/{projectId}."""
    return [(m, p) for m, p, _body, _headers in state.requests
            if p.startswith("/processings/template")
            and not (m == "GET" and re.fullmatch(r"/processings/template/project/[\w-]+", p))]


def check_planned_processings(iface, content, controller, processings, state, links):
    """spec/002_F § Plugin behaviour in Mapflow Next, spec/003 § Developer overrides: the Processings tab lists the
    open project's planned processings before the others, each with a mark, the name and the status, and nothing
    else: no action, no menu, no notice, no count. They load and refresh with the list; a click opens the project
    in Mapflow Web; a request that fails hides the rows and says nothing; a search hides them. Everything the
    function changes is restored."""
    import dataclasses
    from mapflow_next.ui.processings_page import PlannedCard, ProcessingCard
    session, page = controller.session, content.processings
    pj, path = fixtures.planned_json, "/processings/template/project/"
    saved_config, saved_interval = session.config, processings._poll.interval()
    threshold = config.POLL_FAILURES_BEFORE_ALERT
    finished, failed_notices = [], []
    on_finished, on_failed = finished.append, failed_notices.append
    processings.finished.connect(on_finished)
    processings.failed.connect(on_failed)

    def asks():
        return [r[1] for r in state.requests if r[0] == "GET" and r[1].startswith(path)]

    def lists():
        return len([r for r in state.requests if r[0] == "POST" and r[1].endswith("/processings/v2/page")])

    def planned_cards():
        return page.findChildren(PlannedCard)

    def names():
        return [c.planned.name for c in planned_cards()]

    def order():
        widgets = (page.list.itemAt(i).widget() for i in range(page.list.count()))
        return [type(w).__name__ for w in widgets if isinstance(w, (PlannedCard, ProcessingCard))]

    def reload():
        page.refresh_button.click()
        wait_until(lambda: not page.refreshing, 5)
        wait_until(lambda: not processings._full.loading, 5)
        wait_until(lambda: False, 0.4)           # the planned answer comes after the list's

    def lines():
        return [text for _level, text in iface.bar.messages]

    def chips():
        return {key: button.text() for key, button in page.chip_buttons.items()}

    def menu_texts():
        return sorted(a.text() for tool in page.findChildren(QToolButton) if tool.menu() for a in tool.menu().actions())

    def open_project(project_id):
        session.select_project(project_id)
        wait_until(lambda: session.project.id == project_id and processings.loaded, 5)
        wait_until(lambda: False, 0.4)

    def click(card):
        QTest.mouseClick(card, Qt.MouseButton.LeftButton)
        wait_until(lambda: False, 0.2)

    state.planned, state.planned_delay = {}, {}
    processings._poll.setInterval(60000)         # the checks tick by hand
    try:
        check(session.project.id == "project-1" and page.filter == "all" and not page.terms,
              "PLANNED: the checks start in the default project, with the whole list shown")
        reload()
        base_chips, base_running, base_menus = chips(), content.running_link.text(), menu_texts()
        base_cards = [c.processing.id for c in page.findChildren(ProcessingCard)]
        check(base_cards and not planned_cards(), "PLANNED: a project without planned processings shows no row")

        # ---------- rows and order ----------
        searching, forest = pj("tpl-1", "Harbor watch", "Searching"), pj("tpl-2", "Forest watch", "Failed")
        other = pj("tpl-3", "Other project", "Created", "project-2")
        state.planned = {"project-1": [searching, forest], "project-2": [other]}
        before = len(lines())
        reload()
        check(names() == ["Harbor watch", "Forest watch"], f"PLANNED: the rows of the open project show ({names()})")
        check(order() == ["PlannedCard"] * 2 + ["ProcessingCard"] * len(base_cards),
              f"PLANNED: …before every processing, in the order of the answer ({order()})")
        texts = [[x.text() for x in c.findChildren(QLabel)] for c in planned_cards()]
        check(all("Search processing" in t for t in texts) and "Searching" in texts[0] and "Failed" in texts[1]
              and "Harbor watch" in "".join(texts[0]) and "Forest watch" in "".join(texts[1]),
              f"PLANNED: …each with the mark, the name and the status ({texts})")
        check(not [w for c in planned_cards() for w in c.findChildren(QPushButton) + c.findChildren(QToolButton)]
              and menu_texts() == base_menus
              and not any(t in ("Restart", "Add to map", "Show on map", "GeoJSON", "Run again with these settings",
                                "Rename…", "Delete…") for c in planned_cards() for t in
                          [x.text() for x in c.findChildren(QLabel)]),
              "PLANNED: …and no button, no menu and no action")
        check(chips() == base_chips and content.running_link.text() == base_running
              and [c.processing.id for c in page.findChildren(ProcessingCard)] == base_cards,
              "PLANNED: …they do not count in the chips or in “running”, and the other cards are the same")
        forest["status"] = "Searching"
        searching["status"] = "Failed"
        reload()
        check(names() == ["Harbor watch", "Forest watch"] and not finished and not failed_notices
              and len(lines()) == before and content.running_link.text() == base_running,
              "PLANNED: a status change of a row gives no notice")

        # ---------- they load and refresh with the list ----------
        state.planned["project-1"].append(pj("tpl-4", "Port watch", "Created"))
        asked, listed = len(asks()), lists()
        reload()
        check(names()[-1:] == ["Port watch"] and asks()[asked:] == [path + "project-1"] and lists() == listed + 1,
              f"PLANNED: Refresh asks again for them, once per list ({asks()[asked:]})")
        state.planned["project-1"][2]["name"] = "Port watch 2"
        asked = len(asks())
        processings._tick()
        wait_until(lambda: names()[-1:] == ["Port watch 2"], 5)
        check(names()[-1:] == ["Port watch 2"] and asks()[asked:] == [path + "project-1"],
              f"PLANNED: the poll refreshes them ({asks()[asked:]})")
        asked = len(asks())
        open_project("project-2")
        check(names() == ["Other project"] and asks()[asked:] == [path + "project-2"],
              f"PLANNED: a project change loads those of the new project ({names()}, {asks()[asked:]})")
        open_project("project-1")
        check(names() == ["Harbor watch", "Forest watch", "Port watch 2"],
              f"PLANNED: …and back ({names()})")
        state.planned_delay = {"project-2": 1.0}
        session.select_project("project-2")
        wait_until(lambda: session.project.id == "project-2", 5)
        session.select_project("project-1")
        wait_until(lambda: session.project.id == "project-1", 5)
        wait_until(lambda: False, 1.6)
        check(names() == ["Harbor watch", "Forest watch", "Port watch 2"],
              f"PLANNED: a late answer of the other project is dropped ({names()})")
        state.planned_delay = {}

        # ---------- a click opens Mapflow Web ----------
        expanded, total = page.expanded, len(state.requests)
        session.config = dataclasses.replace(saved_config, web="https://web.example.test/")
        links.opened.clear()
        click(planned_cards()[0])
        new = [r[1] for r in state.requests[total:]]
        check(links.opened == ["https://web.example.test/projects/project-1"] and page.expanded == expanded
              and not new,
              f"PLANNED: a click opens the project on the overridden web address ({links.opened}, {new})")
        state.planned["project-1"][1]["projectId"] = "project-9"
        reload()
        links.opened.clear()
        click(planned_cards()[1])
        check(links.opened == ["https://web.example.test/projects/project-9"],
              f"PLANNED: …the project of the planned processing, not the open one ({links.opened})")
        session.config = dataclasses.replace(saved_config, web="", env="duty")
        links.opened.clear()
        click(planned_cards()[0])
        check(links.opened == ["https://duty.mapflow.ai/projects/project-1"],
              f"PLANNED: with no override, the environment's web address applies ({links.opened})")
        session.config = saved_config
        state.planned["project-1"][1]["projectId"] = "project-1"

        # ---------- a failed request hides the rows and says nothing ----------
        for what in (503, 404):
            reload()
            check(len(planned_cards()) == 3, f"PLANNED: the rows are shown before the failure ({what})")
            state.fail("GET", r"/processings/template/project/", what)
            before, gone = len(lines()), []
            processings.projectGone.connect(gone.append)
            reload()
            check(not planned_cards() and page.findChildren(ProcessingCard) and not processings.load_failed
                  and session.project.id == "project-1" and not page.refreshing,
                  f"PLANNED: a failed request ({what}) hides the rows and nothing else changes")
            check("didn't load" not in page.empty_text.text() and not gone and len(lines()) == before,
                  f"PLANNED: …no text, no message ({what}, {lines()[before:]})")
            for _ in range(threshold + 2):
                processings._tick()
                wait_until(lambda: False, 0.3)
            open_project("project-2")
            open_project("project-1")
            check(not planned_cards() and len(lines()) == before and not gone and not processings.load_failed
                  and session.project.id == "project-1",
                  f"PLANNED: …nor after the poll and a project change ({what}, {lines()[before:]})")
            processings.projectGone.disconnect(gone.append)
            state.heal()
            reload()
            check(len(planned_cards()) == 3, f"PLANNED: …and the rows come back with the next refresh ({what})")
        # A 401 goes through the session's renewal like every request: spec/005 covers it for the lists.

        # ---------- no planned processings, and no processings ----------
        state.planned = {}
        asked = len(asks())
        reload()
        check(not planned_cards() and chips() == base_chips and len(asks()) == asked + 1
              and order() == ["ProcessingCard"] * len(base_cards),
              "PLANNED: a project without planned processings is as before, with one request per refresh")
        state.planned = {"project-2": [pj("tpl-3", "Other project", "Created", "project-2")]}
        open_project("project-2")
        check(names() == ["Other project"] and page.empty_text.text() == "No processings in this project yet."
              and page.empty.isVisibleTo(page) and page.start_button.isVisibleTo(page),
              "PLANNED: a project with planned rows and no processing shows the rows and the usual empty text")
        open_project("project-1")

        # ---------- the search and the filters hide them ----------
        state.planned = {"project-1": [searching, forest]}
        reload()
        check(len(planned_cards()) == 2, "PLANNED: the rows show before a search")
        page.search.setText("Forest")
        wait_until(lambda: processings.terms == "Forest" and processings._found.loaded
                   and not processings._found.loading, 5)
        check(not planned_cards() and page.findChildren(ProcessingCard),
              "PLANNED: during a search the rows are not shown, the matches are")
        page.search.clear()
        wait_until(lambda: not processings.terms, 5)
        wait_until(lambda: len(planned_cards()) == 2, 5)
        check(len(planned_cards()) == 2, "PLANNED: …and they return when the search is cleared")
        for key in ("running", "done", "attention"):
            page.chip_buttons[key].click()
            check(not planned_cards(), f"PLANNED: the “{key}” filter hides them")
        page.chip_buttons["all"].click()
        check(len(planned_cards()) == 2, "PLANNED: …and “All” shows them")

        check(not planned_endpoint_only(state),
              f"PLANNED: only GET /processings/template/project/{{id}} was sent ({planned_endpoint_only(state)})")
    finally:
        state.heal()
        state.planned, state.planned_delay = {}, {}
        session.config = saved_config
        processings.finished.disconnect(on_finished)
        processings.failed.disconnect(on_failed)
        page.search.clear()
        page.chip_buttons["all"].click()
        if session.project.id != "project-1":
            open_project("project-1")
        processings._poll.stop()
        processings._poll.setInterval(saved_interval)
        reload()


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


def slow_download(state, imagery, target, told):
    """Start a download of the image m-2-i0 that takes about five seconds, through the service (no window needed),
    and wait until the body is arriving on disk."""
    state.download_mode, state.download_chunk_delay = "slow", 0.5
    imagery.download_image("m-2-i0", lambda _name: str(target), lambda path: told.append(("done", path)),
                           lambda message: told.append(("error", message)))
    http = imagery.api.http
    return wait_until(lambda: any(item.sink is not None and item.sink.size() > 0 for item in http._pending.values()), 5)


def check_download_image(iface, plugin, state, picker):
    """spec/002_C § Client-side download: "Download…" in an image's ⋯ menu (only when it is available for
    download), the save dialog, the body streamed to a temporary file that replaces the target when complete, and a
    plain message for each failure. A test never lists the folder while a download runs: the temporary file's
    directory entry depends on the platform (O_TMPFILE). Everything the function changes is restored."""
    import mapflow_next.api.client as client_module
    import mapflow_next.controller as controller_module
    controller, imagery = plugin.controller, plugin.services[3]
    http = plugin.services[1].http
    warn, success = Qgis.MessageLevel.Warning, Qgis.MessageLevel.Success
    folder = Path(tempfile.mkdtemp(prefix="mapflow-image-"))
    target = folder / "saved.tif"
    link = "/rasters/image/m-2-i0/download"
    asked, answer = [], {"path": str(target)}

    def save_dialog(*args, **_kwargs):
        asked.append(args[2] if len(args) > 2 else "")
        return answer["path"], ""

    def file_requests():
        return [r for r in state.requests if r[1] == "/open/image/m-2-i0"]

    def link_requests():
        return [r for r in state.requests if r[1] == link]

    def note():
        return picker.upload_note.text.text()

    def download(wait=True):
        """"Download…" of the image m-2-i0 from its menu; waits until nothing is downloading."""
        before = len(iface.bar.messages)
        picker.image_menu("m-2", "m-2-i0").actions()[0].trigger()
        if wait:
            wait_until(lambda: not imagery.is_downloading("m-2-i0") and len(iface.bar.messages) > before, 15)
        return list(iface.bar.messages[before:])

    def settle(seconds=0.3):
        wait_until(lambda: False, seconds)

    picker.open_collection("m-2")
    check(wait_until(lambda: imagery.get_image("m-2", "m-2-i0") is not None, 5), "the collection m-2 shows its image")
    image = imagery.get_image("m-2", "m-2-i0")
    saved_dialog, saved_timeout = controller_module.QFileDialog.getSaveFileName, client_module.IMAGE_DOWNLOAD_TIMEOUT_S
    saved_popup = picker.__dict__.get("_popup")
    controller_module.QFileDialog.getSaveFileName = staticmethod(save_dialog)
    try:
        # The menu: Download… only when the image is available for download (absent field: it is)
        check(image.available_for_download
              and [a.text() for a in picker.image_menu("m-2", "m-2-i0").actions()]
              == ["Download…", "Delete from the collection…"],
              "an image without the available_for_download field offers Download… and Delete")
        state.not_downloadable.add("m-2-i0")
        imagery.load_images("m-2", force=True)
        check(wait_until(lambda: not imagery.get_image("m-2", "m-2-i0").available_for_download, 5),
              "an image listed with available_for_download: false is not downloadable")
        menus = []
        picker._popup = lambda menu, _anchor: menus.append([a.text() for a in menu.actions()])
        picker.findChild(QToolButton, "more:m-2-i0").click()
        check(menus == [["Delete from the collection…"]], f"…and its ⋯ menu offers Delete only ({menus})")
        links = len(link_requests())
        controller.download_image("m-2", "m-2-i0")
        settle()
        check(not asked and len(link_requests()) == links and not imagery.is_downloading("m-2-i0"),
              "an image that is not available for download is not downloaded: no request, no dialog")
        state.not_downloadable.discard("m-2-i0")
        imagery.load_images("m-2", force=True)
        check(wait_until(lambda: imagery.get_image("m-2", "m-2-i0").available_for_download, 5),
              "(the image is downloadable again)")
        if saved_popup is None:
            del picker._popup
        else:
            picker._popup = saved_popup

        # Success: the dialog suggests the file name; the file equals the body; the credentials stay home
        shown = download()
        check(asked and asked[-1].endswith("beirut_0.5m.tif"),
              f"the save dialog suggests the image's file name ({asked[-1:]})")
        check(target.read_bytes() == state.image_bytes, "the file at the chosen path holds the image")
        check((success, f"Image saved to {target}") in shown and note() == f"Image saved to {target}",
              f"the message bar and the window say \"Image saved to {{path}}\" ({shown})")
        check(files_under(folder) == ["saved.tif"], f"the folder holds the target only ({files_under(folder)})")
        check(link_requests() and any(k.lower() == "authorization" for k in link_requests()[-1][3])
              and file_requests() and not any(k.lower() == "authorization" for k in file_requests()[-1][3]),
              "Mapflow's request carries the credentials; the request for the file does not, on the API's own host")
        target.unlink()

        # The body is on disk while it arrives; a long download is not cut by the timeout, a stalled one is
        client_module.IMAGE_DOWNLOAD_TIMEOUT_S = 2
        told = []
        check(slow_download(state, imagery, target, told),
              "the body of a slow download is on disk before it ends (the plugin does not hold it)")
        check(not target.exists() or target.read_bytes() != state.image_bytes,
              "…and the target is not there before the end")
        check(wait_until(lambda: told, 15) and told == [("done", str(target))]
              and target.read_bytes() == state.image_bytes,
              f"a download longer than its timeout completes while bytes arrive ({told})")
        target.unlink()
        state.download_mode = "stall"
        shown = download()
        check(any(level == warn and "did not answer in time" in text for level, text in shown)
              and not target.exists() and files_under(folder) == [],
              f"a stalled download ends with the timeout message, and leaves no file ({shown}, "
              f"{files_under(folder)})")
        client_module.IMAGE_DOWNLOAD_TIMEOUT_S = saved_timeout
        state.download_mode = "ok"

        # 409 on the link: the reason, no request for the file, no dialog, no file
        asked.clear()
        state.fail("GET", r"/rasters/image/.+/download", 409)
        files_asked = len(file_requests())
        shown = download()
        state.heal()
        reason = "The image isn't ready for download yet. Try again later."
        check(any(level == warn and reason in text for level, text in shown) and reason in note()
              and len(file_requests()) == files_asked and not asked and files_under(folder) == [],
              f"409 says the image isn't ready, sends no request for the file and asks nothing ({shown})")
        for status, text in ((403, "This image can't be downloaded."),
                             (404, "The image wasn't found. It may have been deleted.")):
            state.fail("GET", r"/rasters/image/.+/download", status)
            shown = download()
            state.heal()
            check(any(level == warn and text in message for level, message in shown),
                  f"{status} on the link says: {text} ({shown})")

        # A download that breaks keeps the old file, and leaves no other
        target.write_bytes(b"old bytes")
        state.download_mode = "truncated"
        shown = download()
        settle()
        check(any(level == warn for level, _text in shown) and target.read_bytes() == b"old bytes"
              and files_under(folder) == ["saved.tif"],
              f"a broken download leaves the old file as it was, and no other ({shown}, {files_under(folder)})")
        target.unlink()

        # The file step refused: the link may have expired
        state.download_mode = "forbidden"
        shown = download()
        check(any(level == warn and "The download link was refused or has expired. Try again." in text
                  for level, text in shown) and files_under(folder) == [],
              f"403 on the presigned address says the link expired ({shown})")
        state.download_mode = "ok"

        # A target that can't be opened: the reason, and no request
        answer["path"] = str(folder / "missing" / "saved.tif")
        files_asked = len(file_requests())
        shown = download()
        check(any(level == warn and "Can't write" in text for level, text in shown)
              and len(file_requests()) == files_asked and files_under(folder) == []
              and not (folder / "missing").exists(),
              f"a target that can't be opened gives the reason and sends no request ({shown})")

        # Cancel in the dialog: nothing is sent or said, and the image can be downloaded again
        answer["path"] = ""
        files_asked, before = len(file_requests()), len(iface.bar.messages)
        download(wait=False)
        settle()
        check(len(file_requests()) == files_asked and len(iface.bar.messages) == before
              and not imagery.is_downloading("m-2-i0") and files_under(folder) == [],
              "Cancel in the save dialog sends nothing, says nothing and frees the image")
        answer["path"] = str(target)
        shown = download()
        check(target.exists() and (success, f"Image saved to {target}") in shown,
              "…and the next download works")
        target.unlink()

        # Two clicks on the same image: one download
        state.download_mode, state.download_chunk_delay = "slow", 0.2
        links = len(link_requests())
        before = len(iface.bar.messages)
        download(wait=False)
        wait_until(lambda: imagery.is_downloading("m-2-i0"), 2)
        download(wait=False)
        check(wait_until(lambda: not imagery.is_downloading("m-2-i0") and target.exists(), 15)
              and len(link_requests()) == links + 1
              and any("already downloading" in text for _level, text in iface.bar.messages[before:]),
              "a second click while the image downloads says so and sends no second request")
        target.unlink()
    finally:
        controller_module.QFileDialog.getSaveFileName = saved_dialog
        client_module.IMAGE_DOWNLOAD_TIMEOUT_S = saved_timeout
        state.download_mode, state.download_chunk_delay = "ok", 0.5
        state.not_downloadable.discard("m-2-i0")
        state.heal()
        if saved_popup is None:
            picker.__dict__.pop("_popup", None)
        else:
            picker._popup = saved_popup
    wait_until(lambda: not http._pending or all(item.sink is None for item in http._pending.values()), 5)
    check(not any(item.sink is not None for item in http._pending.values()), "no download is left pending")


def check_rename_collection(iface, plugin, state, picker):
    """spec/002_C § PUT /rasters/mosaic/{id}: "Rename…" in a collection's ⋯ menu (name and tags) sends the PUT and
    the new name shows without a full reload: in the picker's rows (listing and search), its title and target
    line, the My imagery tab, the run form (the chosen collection or image) and the map preview. An empty name is
    refused in the dialog; a refusal shows the server's message and leaves the old name. An image can't be
    renamed here. Everything the function changes is restored."""
    import mapflow_next.controller as controller_module
    from mapflow_next.core.draft import ImageryChoice
    from mapflow_next.ui.collection_dialog import CollectionDialog
    from mapflow_next.ui.widgets import ElidedLabel
    controller, imagery = plugin.controller, plugin.services[3]
    content = plugin.dock.content
    warn = Qgis.MessageLevel.Warning

    def pages():
        return getattr(state, "mosaic_pages", [])

    def card_names():
        page = content.imagery.mosaic_list
        return [w.full_text() for i in range(page.count()) for w in page.itemAt(i).widget().findChildren(ElidedLabel)]

    def run_meta():
        row = next((r for r in content.run._rows if r.title.text() == "My imagery"), None)
        return row.meta.text() if row else ""

    def rename(mosaic_id, answer):
        """The ⋯ menu's Rename… with the dialog answering `answer` (None: cancelled)."""
        Fake.answer = answer
        picker.open_collection(mosaic_id)
        menu = picker.collection_menu()
        menu.actions()[0].trigger()

    # The menus: a collection can be renamed, an image can't (Mapflow Web does that)
    picker.open_collection("m-2")
    check([a.text() for a in picker.collection_menu().actions()] == ["Rename…", "Delete collection…"]
          and [a.text() for a in picker.image_menu("m-2", "m-2-i0").actions()]
          == ["Download…", "Delete from the collection…"],
          "a collection's ⋯ menu offers Rename… and Delete; an image's offers Download… and Delete")

    # The dialog: the name and the tags, prefilled; no empty name
    dialog = CollectionDialog(title="Rename collection", action="Save", name="Beirut", tags=["a", "b"])
    check(dialog.windowTitle() == "Rename collection" and dialog.name.text() == "Beirut"
          and dialog.create.text() == "Save" and dialog.create.isEnabled() and not dialog.chips_holder.isHidden()
          and dialog.values() == ("Beirut", ["a", "b"]),
          f"the rename dialog shows the name and the tags ({dialog.values()})")
    shot(dialog, "19b-rename-collection", QSize(460, 300))
    dialog.name.clear()
    check(not dialog.create.isEnabled(), "an empty name can't be saved")
    dialog.name.setText("   ")
    check(not dialog.create.isEnabled(), "…nor a name of spaces")
    dialog.name.setText("Beirut port")
    dialog.tag.setText("typed")
    check(dialog.create.isEnabled() and dialog.values() == ("Beirut port", ["a", "b", "typed"]),
          f"a tag typed but not added is saved too ({dialog.values()})")
    dialog.close()
    check(CollectionDialog().create.text() == "Create" and not CollectionDialog().create.isEnabled(),
          "the new-collection dialog is as before")

    class Fake:
        answer = None
        made = []

        def __init__(self, *_a, **kwargs):
            Fake.made.append(kwargs)

        def exec(self):
            return 0 if Fake.answer is None else 1

        def values(self):
            return Fake.answer

    saved_dialog, saved_imagery = controller_module.CollectionDialog, controller.draft.imagery
    shown_before = {layer.id(): layer.name() for layer in controller.layers.previews("mosaic:m-1")}
    controller_module.CollectionDialog = Fake
    try:
        # Rename: the PUT, and the name everywhere without a reload
        state.rename_requests.clear()
        asked = len(pages())
        rename("m-2", ("Beirut harbour", ["port"]))
        check(wait_until(lambda: imagery.get_mosaic("m-2").name == "Beirut harbour", 5)
              and state.rename_requests == [("m-2", {"name": "Beirut harbour", "tags": ["port"]})]
              and Fake.made[-1].get("name") == "Beirut" and list(Fake.made[-1].get("tags")) == [],
              f"Rename… sends PUT rasters/mosaic/m-2 with the name and tags ({state.rename_requests})")
        check(wait_until(lambda: "Beirut harbour" in card_names(), 5)
              and picker._rows["m-2"].title.text() == "Beirut harbour"
              and picker.title.full_text() == "Beirut harbour" and "“Beirut harbour”" in picker.target.text()
              and picker.current == "m-2" and imagery.get_mosaic("m-2").tags == ["port"],
              "…the picker's row, title and target line, and the My imagery tab show the new name, still selected")
        check(len(pages()) == asked and "“Beirut” is renamed to “Beirut harbour”" in picker.upload_note.text.text(),
              "…without asking for the list again, and the window says so")

        # The chosen collection of the run form, and its preview on the map
        controller.draft.imagery = ImageryChoice.from_mosaic("m-1", "Drone survey March")
        controller.refresh_run()
        controller.show_mosaic("m-1", zoom=False)
        check(wait_until(lambda: len(controller.layers.previews("mosaic:m-1")) >= 1, 5)
              and "Drone survey March" in run_meta(), "(the run form uses a collection, shown on the map)")
        rename("m-1", ("Drone survey April", []))
        check(wait_until(lambda: "Drone survey April" in run_meta(), 5)
              and controller.draft.imagery.label == "Drone survey April"
              and {layer.name() for layer in controller.layers.previews("mosaic:m-1")}
              == {"My imagery · Drone survey April"},
              f"the run form and the map preview show the new name of the chosen collection ({run_meta()})")
        controller.draft.imagery = ImageryChoice.from_mosaic("m-1", "Drone survey April", "m-1-i1", "centre.tif")
        controller.refresh_run()
        rename("m-1", ("Drone survey May", []))
        check(wait_until(lambda: run_meta().startswith("Drone survey May"), 5)
              and controller.draft.imagery.label == "Drone survey May · centre.tif"
              and controller.draft.imagery.image_ids == ["m-1-i1"],
              f"…also when one image of it is chosen ({controller.draft.imagery.label})")

        # A search listing
        picker.search.setText("survey")
        check(wait_until(lambda: [m.id for m in picker.found] == ["m-1"] and not picker.found_loading, 5),
              "(a search lists the collection)")
        listed = len([p for p in pages() if not p.get("name_contains")])
        rename("m-1", ("Drone survey June", []))
        check(wait_until(lambda: picker._rows["m-1"].title.text() == "Drone survey June", 5)
              and picker.found[0].name == "Drone survey June"
              and len([p for p in pages() if not p.get("name_contains")]) == listed,
              "a collection renamed from a search listing shows the new name there, with no listing request")
        picker.search.clear()
        check(wait_until(lambda: picker._shown() is picker.mosaics, 3)
              and picker._rows["m-1"].title.text() == "Drone survey June", "…and in the listing")

        # Refused: the server's message, the old name stays
        state.rename_refusal = "A collection with this name already exists"
        count = len(state.rename_requests)
        iface.bar.messages.clear()
        rename("m-1", ("Beirut harbour", []))
        check(wait_until(lambda: len(state.rename_requests) == count + 1
                         and "A collection with this name already exists" in picker.upload_note.text.text(), 5)
              and any(level == warn and "A collection with this name already exists" in (text or "")
                      for level, text in iface.bar.messages),
              f"a refusal shows the message of Mapflow ({picker.upload_note.text.text()})")
        check(imagery.get_mosaic("m-1").name == "Drone survey June" and picker._rows["m-1"].title.text()
              == "Drone survey June" and run_meta().startswith("Drone survey June")
              and controller.draft.imagery.label == "Drone survey June · centre.tif",
              "…and the old name stays in the service, the window and the run form")
        state.rename_refusal = None

        # Nothing to send: an empty name, a cancelled dialog, nothing changed
        count = len(state.rename_requests)
        rename("m-1", ("", []))
        rename("m-1", None)
        rename("m-1", ("Drone survey June", []))
        wait_until(lambda: False, 0.3)
        check(len(state.rename_requests) == count, "an empty name, a cancelled dialog or no change send nothing")
    finally:
        controller_module.CollectionDialog = saved_dialog

    # The real dialog through the controller: its tags are prefilled and a tag typed but not added is sent
    class Editing(CollectionDialog):
        def exec(self):
            self.name.setText("Beirut docks")
            self.tag.setText("typed")
            return 1

    controller_module.CollectionDialog = Editing
    try:
        state.rename_requests.clear()
        picker.open_collection("m-2")
        picker.collection_menu().actions()[0].trigger()
        check(wait_until(lambda: state.rename_requests == [("m-2", {"name": "Beirut docks",
                                                                    "tags": ["port", "typed"]})], 5),
              f"the dialog starts with the collection's tags, and a tag typed but not added is sent "
              f"({state.rename_requests})")
    finally:
        controller_module.CollectionDialog = saved_dialog

    controller.draft.imagery = saved_imagery
    state.renamed_mosaics.clear()
    state.rename_requests.clear()
    for layer in controller.layers.previews("mosaic:m-1"):
        if layer.id() in shown_before:
            layer.setName(shown_before[layer.id()])
        else:
            controller.layers.remove([layer])
    imagery.load_mosaics()
    wait_until(lambda: not imagery.loading_mosaics, 5)
    controller.refresh_run()
    picker.set_upload(None)


def check_storage_limits(iface, plugin, state, picked):
    """spec/002_C § Storage Endpoints › Plugin behaviour, spec/005 § Failed requests, spec/006 § A guarded
    callback is interrupted, not completed: the limits come from GET /rasters/memory when My imagery opens and
    before an upload; an upload larger than the free space is refused before anything is sent; a failed request
    leaves nothing pending and the upload goes on with the built-in limits. `picked` is the dict that the patched
    file dialog reads. Everything the function changes is restored."""
    from qgis.PyQt.QtWidgets import QLabel
    import mapflow_next.controller as controller_module
    from mapflow_next.core.formatting import size, size_limit
    from mapflow_next.qgis_bridge import rasters
    from mapflow_next.ui.dock import IMAGERY
    imagery, controller = plugin.services[3], plugin.controller
    content = plugin.dock.content
    page = content.imagery
    warn = Qgis.MessageLevel.Warning
    memory = "/rasters/memory"
    failed_line = "upload limits didn't load"

    def asked(path=memory):
        return len([r for r in state.requests if r[0] == "GET" and r[1] == path])

    def sent_checks():
        return len([r for r in state.requests if r[1] == "/rasters/validate-image-metadata"])

    def lines(since, fragment):
        return [t for level, t in iface.bar.messages[since:] if level == warn and fragment in (t or "")]

    def idle():
        return (not imagery.uploading and controller.uploading is None and controller._choose_uploaded is None
                and page.upload_button.isEnabled() and not page.upload_bar.isVisible())

    def upload(files, mosaic_id=None):
        state.uploads.clear()
        iface.bar.messages.clear()
        picked["files"] = files
        controller.upload(mosaic_id)

    def open_my_imagery():
        """My imagery opens: the tab, as the user's click does it (a young answer is not asked for again)."""
        imagery._limits_at = 0.0
        page.show_tab(MINE)
        controller.on_tab(IMAGERY)

    def settled():
        return wait_until(lambda: not imagery._limits_loading, 5)

    def refused(files, says, label):
        upload(files)
        found = wait_until(lambda: lines(0, "Can't upload") and idle(), 5)
        text = " ".join(lines(0, "Can't upload"))
        check(found and all(fragment in text for fragment in says) and not state.uploads,
              f"{label}: refused with {says} and nothing is sent ({text!r}, {state.uploads})")
        return text

    def uploads_ok(files, label):
        upload(files)
        check(wait_until(lambda: state.uploads and idle(), 5) and not lines(0, "Can't upload"),
              f"{label}: the upload goes ({state.uploads})")

    saved_open = controller_module.QFileDialog.getOpenFileNames
    saved_metadata = controller_module.rasters.geotiff_metadata
    controller_module.QFileDialog.getOpenFileNames = staticmethod(lambda *a, **k: (picked["files"], ""))
    state.heal()
    state.memory = None
    try:
        # asked when My imagery opens
        check(settled(), "STORAGE: no limits request is left pending")
        before = asked()
        open_my_imagery()
        check(wait_until(lambda: asked() == before + 1, 5), "STORAGE: opening My imagery asks GET /rasters/memory")
        settled()
        check(imagery.limits.max_upload_bytes == fixtures.MEMORY["maxUploadFileSize"]
              and imagery.limits.max_side_pixels == fixtures.MEMORY["maxPixelCount"]
              and imagery.limits.free_bytes == fixtures.MEMORY["memoryFree"],
              f"…and the service holds the answer ({imagery.limits})")
        open_my_imagery()
        wait_until(lambda: False, 0.3)
        check(asked() == before + 2, "…each time it opens, once (a young answer is reused only within seconds)")
        imagery._limits_at = time.monotonic()
        controller._refresh_mosaics()
        wait_until(lambda: False, 0.3)
        check(asked() == before + 2, "…and two opens together send one request")
        imagery._limits_at, imagery._mosaics_at = 0.0, 0.0
        controller._mosaic_refresh.timeout.emit()
        wait_until(lambda: False, 0.4)
        check(asked() == before + 2, "…the collections timer does not ask")
        imagery._limits_at = 0.0
        controller.open_mosaic_picker()
        check(wait_until(lambda: asked() == before + 3, 5), "…the collection picker opening asks too")
        settled()
        if controller.mosaic_picker is not None:
            controller.mosaic_picker.hide()

        # the usage is not shown
        shown = [w.text() for root in (page, controller.mosaic_picker) if root is not None
                 for w in root.findChildren(QLabel)]
        check(not any("Your data" in t or "Free space" in t for t in shown),
              "STORAGE: the usage (“Your data: X. Free space: Y”) is shown nowhere")
        check(size_limit(fixtures.MEMORY["maxUploadFileSize"]) in page.upload_limit.text(),
              f"…the page names the account's file limit ({page.upload_limit.text()!r})")

        # asked before every upload
        before = asked()
        uploads_ok([make_geotiff("limits_one.tif")], "STORAGE (first)")
        uploads_ok([make_geotiff("limits_two.tif")], "STORAGE (second)")
        check(asked() == before + 2, f"STORAGE: each upload asks GET /rasters/memory first ({asked() - before})")

        # larger limits than the built-in ones accept a file the built-in ones refuse
        wide = make_geotiff("wide_limits.tif", size=config.MAX_SIDE_PIXELS + 1)
        uploads_ok([wide], "STORAGE (30,001 px with the account's limit)")
        state.memory = dict(fixtures.MEMORY, maxPixelCount=config.MAX_SIDE_PIXELS)
        refused([wide], ["a side", "30,000"], "STORAGE (the account's own pixel limit)")
        state.memory = dict(fixtures.MEMORY, maxUploadFileSize=10)
        refused([make_geotiff("fat.tif")], ["larger than 10 B"], "STORAGE (the account's file limit)")
        state.memory = None
        sparse = str(Path(tempfile.mkdtemp()) / "huge.tif")
        try:
            from osgeo import gdal, osr
            raster = gdal.GetDriverByName("GTiff").Create(sparse, 28_000, 28_000, 3, gdal.GDT_Byte,
                                                          ["SPARSE_OK=TRUE", "BIGTIFF=YES"])
            raster.SetGeoTransform((37.6, 0.0001, 0, 55.75, 0, -0.0001))
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(4326)
            raster.SetProjection(srs.ExportToWkt())
            raster.FlushCache()
            raster = None
            made = os.path.getsize(sparse) > config.UPLOAD_LIMIT_BYTES
        except Exception as error:                  # no sparse files here: the sub-check is skipped
            print(f"SKIP the 2.3 GB sparse GeoTIFF: {error}")
            made = False
        if made:
            _meta, why = rasters.geotiff_metadata(sparse)
            check("larger than 2 GB" in why, f"STORAGE: a file over the built-in 2 GB is refused ({why})")
            _meta, why = rasters.geotiff_metadata(sparse, max_bytes=10 * 1024 ** 3, max_side=100_000)
            check(not why, f"…and accepted with the account's larger limits ({why!r})")
            os.remove(sparse)

        # free space
        one = make_geotiff("free_one.tif")
        two = make_geotiff("free_two.tif")
        each = os.path.getsize(one)
        state.memory = dict(fixtures.MEMORY, memoryFree=100)
        checks_before = sent_checks()
        refused([one], [size(100), "free"], "STORAGE (one file over the free space)")
        check(sent_checks() == checks_before, "…refused before Mapflow's own check, so before any request about it")
        check(not [t for _l, t in iface.bar.messages if "Your data" in (t or "")], "…and no usage line")
        state.memory = dict(fixtures.MEMORY, memoryFree=each + each // 2)
        refused([one, two], [size(each + each // 2), size(2 * each), "together"],
                "STORAGE (several files: each fits, the sum does not)")
        state.memory = dict(fixtures.MEMORY, memoryFree=2 * each)
        uploads_ok([one, two], "STORAGE (free space equal to the sum)")
        state.memory = dict(fixtures.MEMORY, memoryFree=0)
        refused([one], [size(0)], "STORAGE (no free space)")
        state.memory = dict(fixtures.MEMORY, memoryLimit=None, memoryFree=None)
        uploads_ok([one], "STORAGE (storage not limited)")
        state.memory = None
        uploads_ok([one], "STORAGE (after refusals the next upload works)")

        # an exception after the request leaves nothing busy
        seen = len(iface.bar.ledger.unexpected())

        def boom(*_args, **_kwargs):
            raise RuntimeError("storage boom")
        controller_module.rasters.geotiff_metadata = boom
        upload([one])
        check(wait_until(lambda: len(iface.bar.ledger.unexpected()) > seen, 5), "STORAGE: the guard reports a raise")
        expect_critical(iface, "storage boom", "the guard's lines of a raise after the limits request", count=2)
        check(wait_until(idle, 3) and not lines(0, failed_line) and not state.uploads,
              "…and no upload flag is left set, no “limits didn't load” line, and the upload is not started again")
        controller_module.rasters.geotiff_metadata = saved_metadata
        uploads_ok([one], "STORAGE (after the raise)")

        # a failed request: told at once, the fallback limits apply, the upload goes on
        for what in (503, 403, "drop"):
            state.heal()
            state.fail("GET", memory, what)
            iface.bar.messages.clear()
            upload([make_geotiff("fallback.tif")])
            check(wait_until(lambda: state.uploads and idle(), 8), f"STORAGE (request fails: {what}): the upload goes")
            check(len(lines(0, failed_line)) == 1 and "2 GB" in lines(0, failed_line)[0],
                  f"…the user is told once, with the limits that apply ({lines(0, failed_line)})")
            check(imagery.limits.max_upload_bytes is None and not imagery._limits_loading,
                  "…the service holds the fallback and nothing is pending")
            check(len(iface.bar.ledger.unexpected()) == seen, "…and no Critical line is shown")
            check("2 GB" in page.upload_limit.text(),
                  f"…and the page names the built-in limit ({page.upload_limit.text()!r})")
            refused([wide], ["a side", "30,000"], f"STORAGE (request fails: {what}, 30,001 px)")
        state.heal()

        # a failed request when My imagery opens: told once per outage; a success clears the memory of it
        state.fail("GET", memory, 503)
        iface.bar.messages.clear()
        loaded = imagery.mosaics_loaded
        open_my_imagery()
        settled()
        wait_until(lambda: False, 0.3)
        check(len(lines(0, failed_line)) == 1,
              f"STORAGE (My imagery opens, request fails): one line ({lines(0, failed_line)})")
        open_my_imagery()
        settled()
        wait_until(lambda: False, 0.3)
        check(len(lines(0, failed_line)) == 1, "…and no second line while it keeps failing")
        check(not imagery._limits_loading and imagery.mosaics_loaded == loaded and not imagery.loading_mosaics,
              "…and nothing is left loading")
        state.heal()
        open_my_imagery()
        settled()
        check(imagery.limits.max_upload_bytes == fixtures.MEMORY["maxUploadFileSize"]
              and len(lines(0, failed_line)) == 1, "…a success takes the fallback away and says nothing")
        state.fail("GET", memory, 503)
        open_my_imagery()
        settled()
        wait_until(lambda: False, 0.3)
        check(len(lines(0, failed_line)) == 2, "…and a later failure says it again")
        state.heal()

        # sign-out while the request is in flight: the aborted request reports nothing and leaves no flag
        http = plugin.services[1].http
        state.fail("GET", memory, "hang", times=1)
        iface.bar.messages.clear()
        open_my_imagery()
        check(imagery._limits_loading, "STORAGE: the request is in flight")
        imagery.reset_busy()
        http.abort_all()
        wait_until(lambda: not http._pending, 5)
        check(not imagery._limits_loading and imagery.limits.max_upload_bytes is None and not lines(0, failed_line),
              "…the sign-out's reset clears the flags, forgets the limits and says nothing")
        state.heal()
        open_my_imagery()
        settled()
        check(imagery.limits.max_upload_bytes == fixtures.MEMORY["maxUploadFileSize"],
              "…and the next sign-in asks again")
    finally:
        controller_module.rasters.geotiff_metadata = saved_metadata
        controller_module.QFileDialog.getOpenFileNames = saved_open
        state.memory = None
        state.heal()
        http = plugin.services[1].http
        wait_until(lambda: not http._pending, 5)
        imagery._limits_at = 0.0
        imagery.load_mosaics()                      # the sign-out reset above forgot what was listed
        wait_until(lambda: not imagery.loading_mosaics, 5)


def check_upload_file_vanishes(iface, plugin, state, picked):
    """spec/006 § A guarded callback is interrupted, not completed: a file that is gone after the local check and
    before its upload ends the upload with a message that names the file (a Warning, no Critical line), and every
    upload flag is cleared, so the next upload works. `picked` is the dict that the patched file dialog reads.
    The file goes inside `Imagery.validate`, which runs after the local check and before the first byte."""
    imagery, controller = plugin.services[3], plugin.controller
    page = plugin.dock.content.imagery
    original = imagery.validate
    gone = []

    def validate_and_remove(images, on_done):
        for path in gone:
            if os.path.exists(path):
                os.remove(path)
        original(images, on_done)

    def idle():
        return (not imagery.uploading and controller.uploading is None and controller._choose_uploaded is None
                and page.upload_button.isEnabled() and not page.upload_bar.isVisible())

    def vanishes(label, mosaic_id, files, vanished):
        state.uploads.clear()
        iface.bar.messages.clear()
        seen = len(iface.bar.ledger.unexpected())
        picked["files"] = files
        gone[:] = [vanished]
        name = Path(vanished).name
        controller.upload(mosaic_id)
        found = wait_until(lambda: any(name in (m or "") for _l, m in iface.bar.messages), 5)
        check(found, f"UPLOAD GONE ({label}): the message names the file ({iface.bar.messages})")
        check(len(iface.bar.ledger.unexpected()) == seen,
              f"UPLOAD GONE ({label}): …and no Critical line is shown")
        check(wait_until(idle, 3), f"UPLOAD GONE ({label}): …and the upload flags and the page are cleared")
        check(not state.uploads, f"UPLOAD GONE ({label}): …and nothing was sent ({state.uploads})")

    def next_upload_works(label, mosaic_id, kind):
        state.uploads.clear()
        gone.clear()
        picked["files"] = [make_geotiff(f"after_{label}.tif")]
        controller.upload(mosaic_id)
        check(wait_until(lambda: [u[0] for u in state.uploads] == [kind] and idle(), 5),
              f"UPLOAD GONE ({label}): the next upload works ({state.uploads})")

    imagery.validate = validate_and_remove
    try:
        # into an existing collection
        files = [make_geotiff("vanish_a.tif"), make_geotiff("keep_a.tif")]
        vanishes("into a collection", "m-1", files, files[0])
        imagery.validate = original
        next_upload_works("collection", "m-1", "image")
        imagery.validate = validate_and_remove

        # several files into a new collection: no empty collection is left behind
        files = [make_geotiff("vanish_b.tif"), make_geotiff("keep_b.tif")]
        vanishes("new collection", None, files, files[0])
        check(not any(u[0] == "create" for u in state.uploads), "UPLOAD GONE (new collection): …no collection made")

        # one file
        files = [make_geotiff("vanish_c.tif")]
        vanishes("one file", None, files, files[0])
        imagery.validate = original
        next_upload_works("single", None, "new")
    finally:
        imagery.validate = original
        gone.clear()


def check_network_timeout(iface, plugin, state):
    """spec/006 § A request ends in exactly one outcome: QGIS's own network timeout aborts a reply that made no
    progress, and the plugin did not ask for that abort. The request ends through `on_error` (a timeout), so the
    upload flag and the result's "loading" flag are cleared. An abort that the plugin asks for stays silent.
    The timeout of QGIS is put back."""
    from qgis.core import QgsNetworkAccessManager
    session, imagery, results = plugin.services[1], plugin.services[3], plugin.services[4]
    http = session.http
    path = make_geotiff("qgis-timeout.tif")
    nam = QgsNetworkAccessManager.instance()
    saved, saved_hang = nam.timeout(), state.hang_seconds
    state.heal()
    state.hang_seconds = 6              # the server answers long after QGIS gave up
    failed, results_failed = [], []

    def on_results_failed(processing_id, text):
        results_failed.append((processing_id, text))
    imagery.uploadFailed.connect(failed.append)
    results.failed.connect(on_results_failed)
    try:
        nam.setTimeout(1000)
        # the direct request: the plugin's own timer is an hour away, so QGIS's timeout is the one that ends it
        errors, done = [], []
        state.fail("POST", r"/rasters/mosaic/image", "hang", times=1)
        started = time.time()
        http.upload("rasters/mosaic/image?name=qgis-timeout&tags=", path, on_success=done.append,
                    on_error=errors.append)
        check(wait_until(lambda: errors, 5),
              "NETWORK TIMEOUT: an upload that QGIS's timeout aborts ends through on_error")
        check(len(errors) == 1 and errors[0].kind == "timeout" and not done
              and time.time() - started < state.hang_seconds and not http._pending,
              f"…once, as a timeout, and nothing stays pending ({errors})")

        # through the service: the flag is cleared, the next upload starts
        state.heal()
        state.uploads.clear()
        state.fail("POST", r"/rasters/mosaic/image", "hang", times=1)
        imagery.upload(path, "Cut by QGIS")
        check(imagery.uploading, "NETWORK TIMEOUT: an upload is under way")
        check(wait_until(lambda: failed, 5) and not imagery.uploading,
              f"…and QGIS's timeout clears the upload flag and tells the user ({failed})")
        state.heal()
        imagery.upload(path, "After the cut")
        check(wait_until(lambda: not imagery.uploading
                         and [u[:2] for u in state.uploads] == [("new", "After the cut")], 8),
              f"…and the next upload runs ({state.uploads})")

        # a result download: the processing is not left loading
        state.heal()
        stalled = processing_done("qgis-timeout")
        state.fail("GET", r"/processings/[\w-]+/result", "hang", times=1)
        results.add_to_map(stalled)
        check(results.is_busy(stalled.id), "NETWORK TIMEOUT: a result download is under way")
        check(wait_until(lambda: results_failed and not results.is_busy(stalled.id), 5),
              f"…and QGIS's timeout clears the processing's loading flag ({results_failed})")

        # an abort the plugin asked for says nothing
        state.heal()
        silent = []
        state.fail("POST", r"/rasters/mosaic/image", "hang", times=2)
        key = http.upload("rasters/mosaic/image?name=abort&tags=", path, on_error=silent.append)
        http.abort(key)
        key = http.upload("rasters/mosaic/image?name=abort-all&tags=", path, on_error=silent.append)
        http.abort_all()
        wait_until(lambda: False, 1.5)
        check(not silent and not http._pending,
              f"NETWORK TIMEOUT: abort and abort_all end the request without on_error ({silent})")
    finally:
        nam.setTimeout(saved)
        imagery.uploadFailed.disconnect(failed.append)
        results.failed.disconnect(on_results_failed)
        state.hang_seconds = saved_hang
        state.heal()
        http.abort_all()
        wait_until(lambda: not http._pending, 5)
        imagery.reset_busy()
        results.reset()
    check(nam.timeout() == saved, "NETWORK TIMEOUT: QGIS's timeout is put back")


def plugin_timers(roots):
    """Every QTimer that is a child of a root, the roots included. The services and the controller have no
    parent, so each is searched on its own."""
    from qgis.PyQt import sip
    found = []
    for root in roots:
        if root is not None and not sip.isdeleted(root):
            found += root.findChildren(QTimer)
    return found


def all_deleted(objects):
    """Whether every object is deleted. The test has no event loop of level 1, which Qt needs to run a
    `deleteLater` made outside one, so the deferred deletions are sent here."""
    from qgis.PyQt import sip
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    return all(sip.isdeleted(obj) for obj in objects)


def visible_windows(iface):
    """Every visible top-level widget but the main window: a window or a dialog of the plugin, if one is left."""
    return [w for w in QApplication.topLevelWidgets() if w.isVisible() and w is not iface.window]


def check_unloaded(label, iface, state, parts):
    """After `unload`: no window or dialog of the plugin is visible, no timer runs, no request is pending, and
    nothing late reaches plugin code. `parts` is what the plugin held before: `windows`, `dock`, `timers`, `http`,
    `late` (the callbacks the stopped request would have called) and `named` (timers to name)."""
    from qgis.PyQt import sip
    windows, http = parts["windows"], parts["http"]
    # At once, before the event loop turns: nothing waits for a late signal to end a timer or a request
    check(not any(w.isVisible() for w in windows + [parts["dock"]]) and not visible_windows(iface),
          f"{label}: after unload the scenario gallery, the Projects window, the My imagery window and the dock "
          f"are not visible, and no other window of the plugin is ({visible_windows(iface)})")
    running = [t for t in parts["timers"] if not sip.isdeleted(t) and t.isActive()]
    check(not running, f"{label}: no timer of the plugin runs ({len(running)} of {len(parts['timers'])} do: "
                       f"{[(t.parent(), t.interval()) for t in running]})")
    check(http._pending == {}, f"{label}: no request is pending ({len(http._pending)} are)")
    check(wait_until(lambda: all_deleted(windows), 3),
          f"{label}: the three windows are deleted, not only hidden")
    check(wait_until(lambda: all_deleted([parts["dock"]]), 3), f"{label}: …and so is the dock")
    check(parts["late"] == [], f"{label}: the stopped request called nothing back ({parts['late']})")
    check(http.get("user/status") == 0 and http._pending == {},
          f"{label}: a request made after unload sends nothing")
    wait_until(lambda: False, 0.3)
    shown, seen = len(iface.bar.messages), len(state.requests)
    wait_until(lambda: False, 0.5)
    check(len(iface.bar.messages) == shown and len(state.requests) == seen and parts["late"] == [],
          f"{label}: nothing comes late: no bar message, no new request to the server")


def check_unload(iface, classFactory, state):
    """spec/007 § Mapflow Next (4.x) › Unload: unload closes every window the plugin opened, and every service
    has `stop()`, which ends its timers and pending requests. A fresh plugin is built, so it proves reload too."""
    saved_hang = state.hang_seconds
    fresh = classFactory(iface)
    fresh.initGui()
    fresh.toggle(True)
    session, processings = fresh.services[1], fresh.services[2]
    http, controller = fresh.services[0], fresh.controller
    try:
        fresh.dock.content.sign_in.tokenSubmitted.emit(mock_server.TOKEN)
        check(wait_until(lambda: session.state == "signed_in" and session.status is not None and processings.items, 5),
              "unload: a fresh plugin signs in")
        wait_until(lambda: not http._pending, 5)
        controller.open_projects()
        controller.open_mosaic_picker()
        controller.open_gallery()
        windows = [controller.gallery, controller.projects_dialog, controller.mosaic_picker]
        check(all(w.isVisible() for w in windows),
              "unload: the scenario gallery, the Projects window and the My imagery window are open")
        state.heal()
        state.hang_seconds = 3
        state.fail("GET", r"/user/status", "hang", times=1)
        late = []
        http.get("user/status", on_error=late.append)
        controller.projects_dialog.search.setText("tile")          # starts the debounce timer
        check(wait_until(lambda: any(r[1] == "/user/status" for r in state.requests[-3:]), 3),
              "unload: the server has the request that hangs")
        timers = plugin_timers([fresh.dock, *windows, controller, *fresh.services])
        check(any(t.isActive() for t in timers) and http._pending,
              f"unload: timers run and a request is pending before the unload ({len(timers)} timers)")
        dock = fresh.dock
        fresh.unload()
        check_unloaded("unload", iface, state, {"windows": windows, "dock": dock, "timers": timers, "http": http,
                                                "late": late})
        # reload
        again = classFactory(iface)
        again.initGui()
        again.toggle(True)
        again.controller.open_gallery()
        check(len(iface.window.findChildren(QToolBar, "MapflowToolbar")) == 1 and again.dock is not None
              and again.controller.gallery.isVisible()
              and len(iface.window.findChildren(type(again.dock))) == 1,
              "unload: after a reload there is one toolbar and one dock, and the gallery opens")
        again_windows = [again.controller.gallery]
        again_http = again.services[0]
        again_timers = plugin_timers([again.dock, *again_windows, again.controller, *again.services])
        again_dock = again.dock
        again.unload()
        check_unloaded("reload", iface, state, {"windows": again_windows, "dock": again_dock,
                                                "timers": again_timers, "http": again_http, "late": []})
        # a report dialog that is open when the plugin unloads is closed and deleted
        from mapflow_next.core import guard
        last = classFactory(iface)
        last.initGui()
        guard.report(ValueError("report-open"), "unload with the report dialog open")
        expect_critical(iface, "report-open", "the guard's lines of the report that is open at unload", count=2)
        button = next(b for b in iface.bar.widgets[-1].findChildren(QPushButton) if b.text() == "Send a report")
        opened = {}

        def unload_it(dialog):
            opened["dialog"] = dialog
            last.unload()
            opened["hidden"] = not dialog.isVisible()
        close_modal_later([], unload_it)
        button.click()
        check(opened.get("hidden") and wait_until(lambda: all_deleted([opened["dialog"]]), 3)
              and last.report_dialog is None and not visible_windows(iface),
              "unload: a report dialog that is open is closed and deleted")
    finally:
        state.hang_seconds = saved_hang
        state.heal()
        wait_until(lambda: False, 0.2)


def main():
    server, state, url = mock_server.start()
    links = UrlRecorder()
    QDesktopServices.setUrlHandler("https", links, "handle")       # no real browser opens during the test
    QDesktopServices.setUrlHandler("http", links, "handle")
    QDesktopServices.setUrlHandler("mailto", MAIL, "handle")        # no real mail program opens either
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
    links.opened.clear()
    content.sign_in.terms.click()
    check(links.opened == ["https://mapflow.ai/terms-of-use-en.pdf"],
          f"the sign-in page's \"Terms of use\" link opens the terms of use ({links.opened})")
    links.opened.clear()

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
    download_dir = Path(tempfile.mkdtemp(prefix="mapflow-image-"))
    downloading = []
    try:
        converting = processing_done("conv-unload")
        results_now.add_to_map(converting)
        check(wait_until(lambda: entered, 5), "a conversion runs when the plugin is unloaded")
        check(slow_download(state, plugin.services[3], download_dir / "unload.tif", downloading),
              "an image download runs when the plugin is unloaded")
        stopping = time.time()
        plugin.unload()
        took = time.time() - stopping
        check(took < 6 and left, f"unload cancels the conversion and waits for its worker ({took:.1f} s)")
        check(files_under(out_dir) == files_before, "…and no file stays in the output folder "
              f"({sorted(set(files_under(out_dir)) - set(files_before))})")
        wait_until(lambda: False, 0.3)
        check(not told and len(iface.bar.messages) == shown, "…and nothing is told about it afterwards")
        check(not downloading and files_under(download_dir) == [],
              f"unload stops the image download: nothing is told, no file stays ({downloading}, "
              f"{files_under(download_dir)})")
    finally:
        state.download_mode = "ok"
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
    sign_out_dir, signing_out = Path(tempfile.mkdtemp(prefix="mapflow-image-")), []
    check(slow_download(state, imagery_now, sign_out_dir / "out.tif", signing_out),
          "an image download runs when the user signs out")
    session.sign_out()
    check(wait_until(lambda: session.state == "signed_out") and not auth.load_refresh_token(session.config),
          "signing out forgets the browser sign-in")
    wait_until(lambda: False, 0.5)
    state.download_mode = "ok"
    check(not signing_out and files_under(sign_out_dir) == [] and not imagery_now._downloads
          and not any(item.sink is not None for item in session.http._pending.values()),
          f"signing out stops the image download: nothing is told, no file stays ({signing_out}, "
          f"{files_under(sign_out_dir)})")
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

    check_poll_auth(iface, plugin, state, browser)
    check_forced_upgrade(iface, plugin, state, browser)

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
    check_review_link(content, controller, processings, links, state, started)
    check_restart(iface, content, controller, processings, state)
    check_processing_search(iface, content, controller, processings, state)
    check_opened_card(iface, content, controller, processings, state)
    check_answer_order(iface, content, controller, processings, state)
    check_planned_processings(iface, content, controller, processings, state, links)

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
    from mapflow_next.config import FILES, TILES
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
    check_the_guard(iface, plugin, url, settings, state)
    check_result_conversion(iface, plugin)
    check_results_loading_flag(iface, plugin)
    check_virtual_guard(iface, plugin)
    check_paint_guard(iface, plugin)
    check_classify_without_timeout_error()
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
    check(meta.get("minOffNadirAngle") == 0 and meta.get("maxOffNadirAngle") == 30,
          f"the off-nadir range is the full 0-30 by default, and both ends are sent ({meta})")
    check(meta.get("hideUnavailable") is False and not imagery_page.available.isChecked(),
          f"“Available for me” is off by default, and hideUnavailable False is sent, not left out ({meta})")
    gap = imagery_page.cloud.geometry().top() - imagery_page.cloud_value.geometry().bottom()
    check(0 <= gap <= 4, f"a slider's title sits right on its slider ({gap} px)")
    check(QgsProject.instance().mapLayersByName("Mapflow · search results"), "footprints are drawn on the map")
    check(imagery_page.date_from.calendarPopup() and "calendar" in content.styleSheet(),
          "dates have a calendar picker with a visible calendar icon")
    check(isinstance(imagery_page.cloud, QSlider) and isinstance(imagery_page.nadir, RangeSlider),
          "cloud cover is a slider and off-nadir is a range slider")
    check(imagery_page.nadir.height() >= 20 and imagery_page.nadir_value.text() == "0°–30°",
          f"the off-nadir range slider is tall enough, and its label shows both ends "
          f"({imagery_page.nadir.height()} px, {imagery_page.nadir_value.text()})")

    def metas():
        return [r for r in state.requests if r[1] == "/catalog/meta"]
    asked, listed = len(metas()), list(plugin.services[3].results)
    imagery_page.nadir.setValues(5, 20)
    wait_until(lambda: False, 0.3)
    check(len(metas()) == asked and plugin.services[3].results == listed
          and imagery_page.nadir_value.text() == "5°–20°",
          "moving the off-nadir range changes nothing on screen until Search imagery")
    imagery_page.search_button.click()
    check(wait_until(lambda: len(metas()) == asked + 1 and imagery_page.search_button.isEnabled(), 5)
          and metas()[-1][2].get("minOffNadirAngle") == 5 and metas()[-1][2].get("maxOffNadirAngle") == 20,
          "the search sends the off-nadir range that was set")
    imagery_page.nadir.setValues(0, 0)
    imagery_page.search_button.click()
    check(wait_until(lambda: len(metas()) == asked + 2 and imagery_page.search_button.isEnabled(), 5)
          and metas()[-1][2].get("minOffNadirAngle") == 0 and metas()[-1][2].get("maxOffNadirAngle") == 0,
          "an off-nadir range of 0 to 0 is sent, not dropped")
    imagery_page.nadir.setValues(0, 30)
    imagery_page.available.setChecked(True)
    asked = len(metas())
    wait_until(lambda: False, 0.3)
    check(len(metas()) == asked, "moving “Available for me” sends nothing until Search imagery")
    imagery_page.search_button.click()
    check(wait_until(lambda: len(metas()) == asked + 1 and imagery_page.search_button.isEnabled(), 5)
          and metas()[-1][2].get("hideUnavailable") is True,
          "with “Available for me” on, the search sends hideUnavailable True")
    imagery_page.available.setChecked(False)
    imagery_page.search_button.click()
    check(wait_until(lambda: len(metas()) == asked + 2 and imagery_page.search_button.isEnabled(), 5)
          and metas()[-1][2].get("hideUnavailable") is False,
          "with it off again, the search sends hideUnavailable False")
    stored = [key for key in QgsSettings().allKeys() if "available" in key.lower()]
    check(not stored, f"the switch is not stored in the settings ({stored})")
    from mapflow_next.ui.imagery_page import ImageryPage
    fresh = ImageryPage()
    check(not fresh.available.isChecked(), "a new page starts with “Available for me” off")
    fresh.deleteLater()
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
    for first in (True, False):              # "Show more" repeats the last search, not the switch as it is now
        imagery_page.available.setChecked(first)
        imagery_page.search_button.click()
        check(wait_until(lambda: len(plugin.services[3].results) == 50 and imagery_page.more_button is not None, 5)
              and metas()[-1][2].get("hideUnavailable") is first, f"a search with the switch {first} sends {first}")
        imagery_page.available.setChecked(not first)
        imagery_page.more_button.click()
        check(wait_until(lambda: len(plugin.services[3].results) == 60, 5)
              and metas()[-1][2]["offset"] == 50 and metas()[-1][2].get("hideUnavailable") is first,
              f"“Show more” sends {first}, the value of the last search, though the switch moved")
    imagery_page.available.setChecked(False)
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

    # One image chosen from the search: the area is clipped to its footprint, as for My imagery
    def footprint_box(west, east):
        return {"type": "Polygon", "coordinates": [[[west, 55.735], [east, 55.735], [east, 55.765],
                                                    [west, 55.765], [west, 55.735]]]}
    from mapflow_next.core.formatting import km2
    chosen_before, choice_before = controller.chosen_image, controller.draft.imagery
    half = CatalogImage.from_api({"id": "clip-half", "providerName": "maxar", "productType": "Image",
                                  "previewType": "png", "previewUrl": f"{base}/clip-half",
                                  "footprint": footprint_box(37.58, 37.605)})
    away = CatalogImage.from_api({"id": "clip-away", "providerName": "maxar", "productType": "Image",
                                  "previewType": "png", "previewUrl": f"{base}/clip-away",
                                  "footprint": footprint_box(37.64, 37.66)})
    plugin.services[3].results = [half, away]
    controller.use_image("clip-half")
    draft = controller.draft
    whole, processed = draft.aoi, draft.processed_area
    check(draft.coverage is not None and draft.coverage.overlaps and processed is not whole
          and 0.4 * whole.area_km2 < processed.area_km2 < 0.6 * whole.area_km2,
          f"an area partly over the chosen catalog image is clipped to its footprint "
          f"({processed.area_km2:.3f} of {whole.area_km2:.3f} km²)")
    outline = [point for ring in processed.geometry["coordinates"] for point in ring]
    check(draft.payload("project-1")["geometry"] == processed.geometry
          and all(37.595 - 1e-6 <= x <= 37.605 + 1e-6 for x, _y in outline),
          "…only the part inside the footprint is submitted")
    check(run.area_value.text() == km2(processed.area_km2)
          and f"{km2(processed.area_km2)} of {km2(whole.area_km2)} inside the imagery" in run.area_meta.text(),
          f"…the form shows the clipped area ({run.area_value.text()}; {run.area_meta.text()})")
    check("Only the part of the area inside “Maxar scene” is processed and billed" in run.area_hint_text.text.text(),
          f"…and says that only that part is processed and billed ({run.area_hint_text.text.text()!r})")
    check(wait_until(lambda: any(r[1] == "/processing/cost/v2" and isinstance(r[2], dict)
                                 and r[2].get("geometry") == processed.geometry for r in state.requests), 5),
          "…and the cost request carries the clipped geometry, not the whole area")
    check(not any(i.field == "area" for i in draft.issues(session.project, session.status)),
          "…the part inside is within the area limit")
    draft.imagery.min_area_km2 = 1.0
    check(any(i.field == "imagery" and "sells at least 1.00 km²" in i.text
              for i in draft.issues(session.project, session.status)),
          "…and the provider's minimum area is judged on the part inside (the whole area would pass it)")
    draft.imagery.min_area_km2 = 0.0
    limit_before = session.project.aoi_area_limit_km2
    session.project.aoi_area_limit_km2 = (processed.area_km2 + whole.area_km2) / 2
    check(not any(i.field == "area" for i in draft.issues(session.project, session.status)),
          "…an area limit between the clipped and the whole area is not exceeded")
    session.project.aoi_area_limit_km2 = processed.area_km2 / 2
    check(any(i.field == "area" for i in draft.issues(session.project, session.status)),
          "…and a limit under the clipped area is")
    session.project.aoi_area_limit_km2 = limit_before

    controller.use_image("clip-away")
    check(draft.coverage is not None and not draft.coverage.overlaps and not run.run_button.isEnabled()
          and run.area_hint.isVisible() and "doesn't overlap “Maxar scene”" in run.area_hint_text.text.text(),
          "an area that doesn't touch the chosen catalog image's footprint blocks the run, with a warning")
    check(any("doesn't overlap" in i.text for i in draft.issues(session.project, session.status)),
          "…the run is blocked until the area overlaps the image")
    run.area_hint_buttons["imagery_extent"].click()
    extent_layer = controller.aoi_layer
    check(extent_layer is not None and extent_layer.name() == "Extent of Maxar scene"
          and controller.draft.coverage is not None and controller.draft.coverage.overlaps,
          "“Use the imagery extent” makes the image's footprint the area")
    run.layerChosen.emit(layer.id())
    check(controller.draft.coverage is not None and not controller.draft.coverage.overlaps,
          "…and the first area is outside the image again")
    run.area_hint_buttons["imagery_extent"].click()
    check(len(QgsProject.instance().mapLayersByName("Extent of Maxar scene")) == 1,
          "…and the extent layer is reused, not duplicated")

    controller.on_imagery("provider:mapbox")
    check(controller.draft.imagery.kind == "provider" and controller.draft.coverage is None
          and controller.draft.payload("project-1")["geometry"] == controller.draft.aoi.geometry,
          "a basemap provider has no footprint: the area is submitted whole")

    for leftover in QgsProject.instance().mapLayersByName("Extent of Maxar scene"):
        QgsProject.instance().removeMapLayer(leftover.id())
    plugin.services[3].results = []
    controller.chosen_image, controller.draft.imagery = chosen_before, choice_before
    run.layerChosen.emit(layer.id())
    controller.render_search_results()
    controller.refresh_run()
    check(controller.draft.aoi.name == "Old town" and controller.draft.coverage is not None
          and controller.draft.coverage.clipped.area_km2 > 0.99 * controller.draft.aoi.area_km2,
          "back to the image that covers the whole area: nothing is clipped")

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
        check_upload_file_vanishes(iface, plugin, state, picked)
        check_storage_limits(iface, plugin, state, picked)
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
            check(wait_until(lambda: asked_dup and controller.uploading is None, 5)
                  and asked_dup == [(["north.tif"], "Drone survey March")]
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
              and [a.text() for a in menu.actions()] == ["Download…", "Delete from the collection…"],
              "each image has a ⋯ menu with Download and Delete (no extra large buttons)")
        menu.actions()[1].trigger()
        check(not state.deleted_images and confirms[-1][1] == "Delete “centre.tif” from “Jetty”?",
              f"deleting an image asks first; Cancel deletes nothing ({confirms[-1:]})")
        answer_del["value"] = True
        controller.draft.imagery = controller_module.ImageryChoice.from_mosaic(jetty.id, "Jetty", image_id,
                                                                               "centre.tif")
        picker.image_menu(jetty.id, image_id).actions()[1].trigger()
        check(wait_until(lambda: image_id in state.deleted_images and not picker._thumbs
                         and any("no images yet" in w.text() for w in picker.findChildren(QLabel) if w.isVisible()), 5)
              and "stays, empty" in confirms[-1][2]
              and imagery_service.get_mosaic(jetty.id) is not None and jetty.id not in state.deleted_mosaics,
              "deleting the last image leaves the collection in place, empty, and says so")
        check(controller.draft.imagery is None, "…and the run form no longer uses the deleted image")
        menu = picker.collection_menu()
        check(picker.more_button.isVisible()
              and [a.text() for a in menu.actions()] == ["Rename…", "Delete collection…"],
              "the selected collection has a ⋯ menu with Rename and Delete collection")
        controller.draft.imagery = controller_module.ImageryChoice.from_mosaic(jetty.id, "Jetty")
        menu.actions()[1].trigger()
        check(wait_until(lambda: jetty.id in state.deleted_mosaics and imagery_service.get_mosaic(jetty.id) is None
                         and picker.current is None and jetty.id not in picker._rows, 5)
              and confirms[-1][1] == "Delete “Jetty”?" and controller.draft.imagery is None,
              "Delete collection removes it from Mapflow and from the list, and the run form drops it")
    finally:
        controller._confirm_delete = saved_confirm
        controller.draft.imagery = imagery_kept
    check_rename_collection(iface, plugin, state, picker)
    check_download_image(iface, plugin, state, picker)
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
    check("Send a report" not in report_buttons(iface), "…an expected failure offers no report")
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
    from mapflow_next.core.models import CatalogImage as CatalogImageModel
    earlier = CatalogImageModel(id="earlier-image", provider="Airbus", zoom=17)
    controller.chosen_image = earlier
    controller.draft.imagery = controller_module.ImageryChoice.from_mosaic("m-1", "Drone survey March")
    iface.bar.messages.clear()
    content.processings.duplicate.emit("cat-1")
    check(controller.draft.imagery is not None and controller.draft.imagery.kind == "catalog"
          and controller.draft.imagery.image_ids == ["10300100ABCDEF01"],
          "“Run again” on a catalog image chooses the same image, not the imagery chosen before")
    rows, selected = controller._imagery_rows(session.status, True)
    catalog_rows = [r for r in rows if r.key == "catalog"]
    check(selected == "catalog" and len(catalog_rows) == 1 and controller.chosen_image is not earlier
          and controller.chosen_image.id == "10300100ABCDEF01",
          "…the form's imagery row is that image (selected), not the image chosen in the search before")
    check(catalog_rows[0].title == controller._catalog_choice(controller.chosen_image).label
          and "Maxar" in catalog_rows[0].title and "Airbus" not in catalog_rows[0].title
          and "z18" in catalog_rows[0].meta and "from the image resolution" not in catalog_rows[0].meta
          and not catalog_rows[0].previewable,
          f"…the row shows the processing's provider and zoom, and no eye for an image that is not in the "
          f"search results ({catalog_rows[0].title!r}, {catalog_rows[0].meta!r})")
    restored_params = controller.draft.imagery.source_params()["imagerySearch"]
    check(restored_params == {"dataProvider": "maxar", "imageIds": [controller.chosen_image.id],
                              "zoom": controller.chosen_image.zoom} and controller.chosen_image.zoom == 18
          and controller.chosen_image.provider.lower() == restored_params["dataProvider"],
          f"…and the payload's image is the one the form shows ({restored_params})")
    if wait_until(lambda: controller.draft.aoi is not None, 5):
        body = controller.draft.payload("project-1")["params"]["sourceParams"]["imagerySearch"]
        check(body == restored_params, "…the submitted body has the same image as the form's row")
        check(controller.chosen_image.footprint is None and controller.draft.coverage is None
              and controller.draft.processed_area is controller.draft.aoi
              and not any("overlap" in i.text for i in controller.draft.issues(session.project, session.status)),
              "…an image with no footprint doesn't clip the area and doesn't block the run")
    # the image is among the search results: the form shows that result, with what the search knows
    import datetime as datetime_module
    found = CatalogImageModel(id="10300100ABCDEF01", provider="Maxar", product_type="Image", zoom=18, cloud=7.0,
                              acquired=datetime_module.datetime(2024, 5, 17), preview_url="https://x/p.png",
                              preview_type="png")
    plugin.services[3].results = [found]
    controller.chosen_image = earlier
    content.processings.duplicate.emit("cat-1")
    rows, selected = controller._imagery_rows(session.status, True)
    catalog_row = next((r for r in rows if r.key == "catalog"), None)
    check(controller.chosen_image is found and selected == "catalog" and catalog_row is not None
          and "17 May 2024" in catalog_row.meta and "cloud 7%" in catalog_row.meta and catalog_row.previewable,
          f"…an image that is among the search results is shown as that result ({catalog_row})")
    plugin.services[3].results = []
    # no reset of the chosen image here: Run again on the catalog image above is followed by one that can't restore
    check(controller.chosen_image is found, "…the form still has the restored image of the Run again before")
    content.processings.duplicate.emit("custom-1")
    controller.on_status(session.status)
    rows, selected = controller._imagery_rows(session.status, True)
    check(selected is None and not any(r.key == "catalog" for r in rows) and controller.chosen_image is None,
          "…imagery it can't restore leaves the form with no selected row, no row for a catalog image and no "
          "chosen image (so a click can't run it on the image of the Run again before)")
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

    # Run again on a catalog image, then on imagery that is not that image: the first image's row does not stay
    content.processings.duplicate.emit("cat-1")
    check(controller.chosen_image is not None and controller.chosen_image.id == "10300100ABCDEF01"
          and controller.draft.imagery.kind == "catalog",
          "“Run again” on a catalog image has the image's row in the form")
    content.processings.duplicate.emit("old-1")
    rows, selected = controller._imagery_rows(session.status, True)
    check(controller.chosen_image is None and controller.draft.imagery is not None
          and controller.draft.imagery.kind == "provider" and not any(r.key == "catalog" for r in rows)
          and selected == "provider:mapbox",
          f"“Run again” on a provider processing restores the provider and leaves no row of the catalog image "
          f"({selected}, {[r.key for r in rows]})")
    content.processings.duplicate.emit("cat-1")
    check(controller.chosen_image is not None, "…(the catalog image is chosen again)")
    content.processings.duplicate.emit(one_image_run)
    check(wait_until(lambda: controller.draft.imagery is not None and controller.draft.imagery.kind == "my_imagery",
                     5), "“Run again” on a My imagery image restores it")
    rows, selected = controller._imagery_rows(session.status, True)
    check(controller.chosen_image is None and not any(r.key == "catalog" for r in rows) and selected != "catalog",
          f"…and leaves no row of the catalog image ({selected}, {[r.key for r in rows]})")
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
    check(empty is not None, "a status filter with no match among the loaded processings exists")
    chips[empty].click()                # the search sends its text to Mapflow: only a status chip filters here
    check(content.processings.more_button is None and content.processings.empty.isVisibleTo(content.processings)
          and "latest 30 of 70" in content.processings.empty_text.text(),
          f"a filter that matches nothing offers no “Show more” and says what it looked through "
          f"({content.processings.empty_text.text()!r})")
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

    check_rename_project(iface, plugin, state)
    check_delete_project(iface, plugin, state)
    check_failed_requests(iface, plugin, state)
    check_upload_timeout(iface, plugin, state)
    check_network_timeout(iface, plugin, state)

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
    check_unload(iface, classFactory, state)
    check(not planned_endpoint_only(state),
          f"no request went to another planned-processing endpoint ({planned_endpoint_only(state)})")
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
