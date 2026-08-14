"""Shared harness for the behavioral tests.

These tests exist to prove that the 3.7.0 refactoring changed no user-visible behaviour, so
they may only touch surfaces that outlive it (`spec/007_architecture.md` § The test surface
that survives a move):

* the plugin entry point — ``Mapflow(iface)``, ``initGui()``, ``unload()``
* widgets, by the object names the ``.ui`` files give them
* the HTTP conversation
* ``QgsProject`` layers and ``QgsSettings`` keys

Naming anything else — a service class, a helper, a private method — makes the test fail when
that thing moves, which is precisely the noise it is meant to filter out. Constructing objects
with ``Class.__new__(Class)`` is banned here for the same reason.
"""
import base64
from unittest.mock import MagicMock, patch

import pytest
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QMainWindow
from qgis.core import (QgsFeature, QgsGeometry, QgsNetworkAccessManager, QgsProject,
                       QgsRectangle, QgsVectorLayer)

from fake_network import FakeNetwork, fixture


@pytest.fixture
def plugin_iface():
    """A QGIS interface the plugin can actually be built against.

    ``mainWindow()`` must return a real widget: it becomes the parent of the main dialog and
    of the plugin QObject itself, and PyQt rejects a MagicMock where it expects a QWidget.
    Everything else the plugin asks of iface is inspected, not parented, so a mock suffices.
    """
    iface = MagicMock()
    iface.mainWindow.return_value = QMainWindow()
    iface.mapCanvas.return_value = MagicMock()
    return iface


@pytest.fixture(autouse=True)
def alerts():
    """Record what the plugin tells the user, and guarantee nothing waits for a click.

    Autouse and not optional. Every one of these spins its own event loop and blocks until a
    human answers, so a single unguarded one hangs the entire tier instead of failing a test —
    which is exactly what happened before this existed, with no output to say where.

    Two layers, because the plugin raises dialogs both ways. `AlertService.alert` is the
    routed path and is worth recording, since the message is part of the behaviour. But
    `QMessageBox`, `QInputDialog` and `QFileDialog` are also constructed directly in places
    (`_prompt_plan_search`, `prompt_output_directory`, the rename prompts), and those bypass
    the service entirely — so the Qt entry points are stopped too.

    Everything answers "no": dismiss the box, cancel the prompt, pick no directory. A journey
    that needs a different answer patches it for itself, which keeps the choice visible in the
    test rather than hidden in a default.
    """
    from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox

    from mapflow.functional.service.alert_service import AlertService

    recorded = []

    def record(self, message, icon=None, blocking=True):
        recorded.append(message)
        return False

    def refuse_box(self, *args, **kwargs):
        recorded.append(self.text() if hasattr(self, "text") else "")
        return QMessageBox.Cancel

    with patch.object(AlertService, "alert", record), \
            patch.object(QMessageBox, "exec", refuse_box), \
            patch.object(QMessageBox, "exec_", refuse_box), \
            patch.object(QInputDialog, "getText", staticmethod(lambda *a, **k: ("", False))), \
            patch.object(QFileDialog, "getExistingDirectory",
                         staticmethod(lambda *a, **k: "")):
        yield recorded


@pytest.fixture
def network():
    """Replace QGIS's network manager for the whole test.

    Patched on the QGIS class rather than on the name imported into a plugin module, so it
    keeps working when `Http` moves package in Phase D.
    """
    fake = FakeNetwork()
    with patch.object(QgsNetworkAccessManager, "instance", staticmethod(lambda: fake)):
        yield fake


@pytest.fixture
def fresh_singletons():
    """Forget process-global plugin state before building a plugin.

    Every item here compensates for plugin state that outlives the plugin object, not for a
    test-only quirk — the same leaks happen when QGIS reloads the plugin (see WAL). When
    Phase C makes the plugin own its state, this fixture becomes a no-op and should be
    deleted.

    * `ProviderService` and `AlertService` cache their instance on the class, so the second
      plugin built in one process keeps the *first* plugin's dialog, and the provider combo
      is written into a window that is no longer on screen.
    * `AppContext.settings` is one shared `QgsSettings` for the whole process, and
      `Mapflow.__init__` opens a settings group on it that is never closed. Each construction
      therefore nests a level deeper — mapflow/, mapflow/mapflow/, … — so without resetting
      it, journeys read and write different places and leak into each other.
    """
    from qgis.core import QgsSettings

    from mapflow.functional.app_context import AppContext
    from mapflow.functional.service.alert_service import AlertService
    from mapflow.functional.service.provider_service import ProviderService

    for service in (AlertService, ProviderService):
        service._instance = None
        service._initialized = False

    while AppContext.settings.group():
        AppContext.settings.endGroup()
    QgsSettings().remove("mapflow")
    yield


@pytest.fixture
def plugin(plugin_iface, network, fresh_singletons, tmp_path):
    """The real plugin object, built the way QGIS builds it.

    Depends on `network` so the manager is already faked when the plugin builds its Http.

    A working directory is part of a usable installation, not a detail: the plugin writes
    search results and downloaded layers to disk, and without one it stops those actions with
    "Please, specify an existing output directory" — which reads, in a test, as the feature
    being broken. QGIS remembers this between sessions, so a real user sets it once.
    """
    from mapflow.mapflow import Mapflow

    instance = Mapflow(plugin_iface)
    instance.dlg.outputDirectory.setText(str(tmp_path))
    instance.app_context.settings.setValue("outputDir", str(tmp_path))
    # A Path, not a str: the layer code builds filenames with `temp_dir / name`, which is a
    # TypeError on a plain string — and one the error guard would swallow, leaving a preview
    # that simply never appears.
    instance.app_context.temp_dir = tmp_path
    yield instance
    # Timers created in __init__ keep firing into a dead object otherwise, and a stray tick
    # during a later test surfaces as an unrelated failure.
    instance.unload()
    # unload() closes the dialogs but leaves the plugin subscribed to QgsProject, which is
    # process-wide. A stale instance then keeps reacting to layer changes made by the *next*
    # journey, running its handlers against a dialog that is closed — and since its state is
    # whatever the previous journey left, it can take a branch the new journey never would.
    # Disconnected here rather than tolerated: a leaked subscription turns a failure in one
    # test into a failure in an unrelated one, which is the hardest kind to read.
    project = QgsProject.instance()
    for signal in (project.layersAdded, project.layersRemoved, project.readProject):
        try:
            signal.disconnect()
        except TypeError:
            pass  # nothing was connected
    # An AOI layer left behind would be offered to the next journey's layer combo and
    # quietly change what it is testing.
    project.removeAllMapLayers()


def choose_imagery_source(plugin, network, name):
    """Pick a data source from the combo, as a user does.

    Journeys that want a price must choose a basemap source. The default selection is the
    imagery-search source, which needs a specific image chosen from the search results before
    anything can be priced or started — so a test that skips this step is asking for a cost
    the plugin is right to refuse.
    """
    combo = plugin.dlg.providerCombo
    names = [combo.itemText(i) for i in range(combo.count())]
    assert name in names, f"{name!r} is not an available imagery source; combo has {names}"
    combo.setCurrentText(name)
    settle(network)


def add_aoi_layer(plugin, network, name="behavioral aoi",
                  extent=(0.0, 51.0, 0.02, 51.02)):
    """Put a polygon layer on the map and choose it as the AOI, as a user does.

    A small extent on purpose: the account's area caps are real, and an AOI large enough to
    breach one would make the journey assert the wrong thing.
    """
    layer = QgsVectorLayer("Polygon?crs=EPSG:4326", name, "memory")
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromRect(QgsRectangle(*extent)))
    layer.dataProvider().addFeatures([feature])
    layer.updateExtents()
    QgsProject.instance().addMapLayer(layer)
    plugin.dlg.polygonCombo.setLayer(layer)
    settle(network)
    return layer


@pytest.fixture
def logged_in(plugin, network):
    """A plugin past the login exchange, which is the precondition for most journeys.

    Driven through the login dialog's own widgets rather than by calling a plugin method, so
    it keeps working when that method moves.
    """
    plugin.initGui()
    plugin.main()
    settle(network, rounds=2)
    log_in(plugin)
    settle(network)
    return plugin


def log_in(plugin):
    """Type a token and press Log in, exactly as a user does.

    The identity comes from the fixtures rather than being invented. The plugin resolves a
    project role by matching the logged-in address against the project's owners and shared
    users, so an invented login is a stranger to every captured project and lands on the
    least-privilege default — which then blocks actions the journeys are trying to exercise.
    """
    email = fixture("login_projects_default")["user"]["email"]
    token = base64.b64encode(f"{email}:password".encode()).decode()  # pragma: allowlist secret
    plugin.dlg_login.token.setText(token)
    plugin.dlg_login.logIn.click()


def open_first_project(plugin, network):
    """Open the first project the way a double-click does: select the row, then activate it.

    Both halves are needed. A real double-click selects before it opens, and the plugin
    depends on that ordering — the selection change is what records which project is current,
    and opening bails out early if nothing has been recorded yet.
    """
    table = plugin.dlg.projectsTable
    assert table.rowCount(), "no projects listed; the journey cannot start"
    table.setCurrentCell(0, 1)
    table.doubleClicked.emit(table.model().index(0, 1))
    settle(network)


def settle(network, rounds=16, wait_ms=100, min_wait_ms=700, quiet_rounds=3):
    """Let the plugin finish whatever the last action started, then return.

    Real time has to pass, not just replies be delivered: most of the startup configuration
    hangs off a 500 ms QTimer, and the account response that carries the model list, the
    providers and the project table only arrives because that timer fires. Waiting for it
    rather than poking the timer object keeps the helper honest — it names nothing the
    refactoring moves, and it will still work when the timer belongs to a session service.

    Each round pumps the event loop and then answers whatever was asked, so a chain of
    request -> callback -> next request unwinds without the test knowing its length.

    It stops when the plugin goes quiet rather than after a fixed number of rounds. A fixed
    count is a race: on a loaded machine a chain that normally finishes in eight rounds does
    not, and the test fails somewhere unrelated to what it was checking. `min_wait_ms` keeps
    the floor above the startup timer, so "quiet" never means "the timer has not fired yet".
    """
    waited = 0
    quiet = 0
    for _ in range(rounds):
        QTest.qWait(wait_ms)
        waited += wait_ms
        quiet = quiet + 1 if network.deliver() == 0 else 0
        if waited >= min_wait_ms and quiet >= quiet_rounds:
            return
