"""A real QGIS application (offscreen) with a minimal QGIS interface, for end-to-end tests."""
import os
import tempfile
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# Each run gets its own QGIS settings and authentication database. QGIS keeps both under the user's data
# folder, so without this one run's sign-in, project or pins would leak into the next.
_DATA = tempfile.mkdtemp(prefix="mapflow-next-data-")
os.environ["XDG_DATA_HOME"] = _DATA

from qgis.PyQt.QtCore import QCoreApplication, QSettings  # noqa: E402
from qgis.PyQt.QtWidgets import QMainWindow  # noqa: E402
from qgis.core import Qgis, QgsApplication, QgsSettings  # noqa: E402
from qgis.gui import QgsMapCanvas, QgsMessageBar  # noqa: E402

from mapflow_next import config  # noqa: E402
from .ledger import Ledger  # noqa: E402

_APP = None


def _inside_data(path: str) -> bool:
    return bool(path) and os.path.realpath(path).startswith(os.path.realpath(_DATA))


def start_qgis(master_password: str = "test-master-password"):
    """QGIS 3 or 4, with settings and the authentication database in a temporary folder. XDG_DATA_HOME
    does that on Linux; on macOS and Windows QSettings and the QGIS profile are pointed there explicitly,
    and the run stops before anything happens if QGIS would still use the real ones."""
    global _APP
    if _APP is None:
        QSettings.setDefaultFormat(QSettings.Format.IniFormat)
        QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, _DATA)
        QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
        _APP = QgsApplication([], True, _DATA)
        _APP.initQgis()
        QCoreApplication.setOrganizationName("QGIS")
        QCoreApplication.setApplicationName("QGIS3")
        auth_db = (QgsApplication.qgisAuthDatabaseFilePath() if hasattr(QgsApplication, "qgisAuthDatabaseFilePath")
                   else "")
        used = {"settings": QgsSettings().fileName(), "profile": QgsApplication.qgisSettingsDirPath(),
                "authentication database": auth_db or _DATA}
        real = {name: path for name, path in used.items() if not _inside_data(path)}
        if real:
            raise SystemExit(f"Stopped: the test would use your real QGIS {', '.join(real)} ({real})")
        manager = QgsApplication.authManager()
        manager.setMasterPassword(master_password, True)
    return _APP


def wait_until(condition, timeout: float = 15.0, step: float = 0.02) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        QCoreApplication.processEvents()
        if condition():
            return True
        time.sleep(step)
    QCoreApplication.processEvents()
    return condition()


class RecordingBar(QgsMessageBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.messages = []                        # the flow clears this list; the ledger is never cleared
        self.widgets = []
        self.ledger = Ledger()

    def pushMessage(self, title, text=None, level=Qgis.MessageLevel.Info, duration=-1):
        self.messages.append((level, text))
        if level == Qgis.MessageLevel.Critical:
            self.ledger.record("bar", text)
        return super().pushMessage(title, text, level, duration)

    def pushWidget(self, widget, level=Qgis.MessageLevel.Info, duration=0):
        text = widget.text() if hasattr(widget, "text") else ""
        self.messages.append((level, text))
        if level == Qgis.MessageLevel.Critical:
            self.ledger.record("bar", text)
        self.widgets.append(widget)
        return super().pushWidget(widget, level, duration)


class FakeIface:
    """The parts of QgisInterface the plugin uses."""

    def __init__(self):
        self.window = QMainWindow()
        self.window.resize(1400, 900)
        self.canvas = QgsMapCanvas(self.window)
        self.window.setCentralWidget(self.canvas)
        self.bar = RecordingBar(self.canvas)
        QgsApplication.messageLog().messageReceived.connect(self._log_received)
        self._active = None
        self.toolbar_actions = []                 # the Plugins toolbar
        self.menu_actions = {}
        self.options_opened = None

    def _log_received(self, message, tag, level):
        """The plugin's Critical log lines, which the guard writes before the bar line."""
        if tag == config.PLUGIN_NAME and Qgis.MessageLevel(level) == Qgis.MessageLevel.Critical:
            self.bar.ledger.record("log", message)

    def mainWindow(self):
        return self.window

    def mapCanvas(self):
        return self.canvas

    def messageBar(self):
        return self.bar

    def activeLayer(self):
        return self._active

    def setActiveLayer(self, layer):
        self._active = layer
        return True

    def addToolBarIcon(self, action):
        self.toolbar_actions.append(action)

    def removeToolBarIcon(self, action):
        self.toolbar_actions.remove(action)

    def addToolBar(self, name):
        return self.window.addToolBar(name)

    def addPluginToMenu(self, menu, action):
        self.menu_actions.setdefault(menu, []).append(action)

    def removePluginMenu(self, menu, action):
        self.menu_actions.get(menu, []).remove(action)

    def addTabifiedDockWidget(self, area, dock, tabify_with=None, raise_tab=False):
        self.window.addDockWidget(area, dock)

    def addDockWidget(self, area, dock):
        self.window.addDockWidget(area, dock)

    def removeDockWidget(self, dock):
        self.window.removeDockWidget(dock)

    def showOptionsDialog(self, parent=None, page=""):
        self.options_opened = page

    def zoomToActiveLayer(self):
        pass

    # the Layers panel's custom actions, kept as QGIS keeps them: per layer type, for all its layers or listed ones
    def addCustomActionForLayerType(self, action, menu, layer_type, allLayers=True):
        self.layer_actions_by_type = getattr(self, "layer_actions_by_type", {})
        self.layer_actions_by_type[action] = (layer_type, allLayers, set())

    def addCustomActionForLayer(self, action, layer):
        entry = getattr(self, "layer_actions_by_type", {}).get(action)
        if entry is not None:
            entry[2].add(layer.id())

    def removeCustomActionForLayerType(self, action):
        return getattr(self, "layer_actions_by_type", {}).pop(action, None) is not None

    def layer_menu(self, layer):
        """The texts of the custom actions the Layers panel's menu shows for a layer."""
        return [action.text() for action, (layer_type, every, ids) in getattr(self, "layer_actions_by_type", {}).items()
                if layer.type() == layer_type and (every or layer.id() in ids)]

    def layerTreeView(self):
        iface = self

        class _View:
            def currentLayer(self):
                return iface._active
        return _View()
