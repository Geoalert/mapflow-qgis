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
        self.messages = []

    def pushMessage(self, title, text=None, level=Qgis.MessageLevel.Info, duration=-1):
        self.messages.append((level, text))
        return super().pushMessage(title, text, level, duration)

    def pushWidget(self, widget, level=Qgis.MessageLevel.Info, duration=0):
        self.messages.append((level, widget.text() if hasattr(widget, "text") else ""))
        return super().pushWidget(widget, level, duration)


class FakeIface:
    """The parts of QgisInterface the plugin uses."""

    def __init__(self):
        self.window = QMainWindow()
        self.window.resize(1400, 900)
        self.canvas = QgsMapCanvas(self.window)
        self.window.setCentralWidget(self.canvas)
        self.bar = RecordingBar(self.canvas)
        self._active = None
        self.toolbar_actions = []
        self.options_opened = None

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

    def addPluginToMenu(self, menu, action):
        pass

    def removePluginMenu(self, menu, action):
        pass

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
