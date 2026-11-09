"""QGIS entry point: a toolbar button that opens the Mapflow dock on the right."""
from __future__ import annotations

from configparser import ConfigParser
from typing import Optional

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAction

from . import config
from .api.client import MapflowApi
from .api.http import Http
from .controller import Controller
from .core.scenarios import Catalogue
from .qgis_bridge.layers import MapLayers
from .services.imagery import Imagery
from .services.processings import Processings
from .services.results import Results
from .services.session import Session
from .settings import Settings
from .ui.dock import MapflowDock
from .ui.icons import app_icon
from .ui.theme import load_fonts

MENU = "&Mapflow Next"


def plugin_version() -> str:
    parser = ConfigParser()
    parser.read(config.PLUGIN_DIR / "metadata.txt", encoding="utf-8")
    return parser.get("general", "version", fallback="4.0.0")


class MapflowNextPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action: Optional[QAction] = None
        self.gallery_action: Optional[QAction] = None
        self.dock: Optional[MapflowDock] = None
        self.controller: Optional[Controller] = None
        self.services = []

    # ---------- QGIS hooks ----------

    def initGui(self) -> None:
        load_fonts()
        window = self.iface.mainWindow()
        self.action = QAction(app_icon(), "Mapflow", window)
        self.action.setCheckable(True)
        self.action.setToolTip("Mapflow: map buildings, roads and forest from imagery")
        self.action.triggered.connect(self.toggle)
        self.gallery_action = QAction(app_icon(), "Scenarios…", window)
        self.gallery_action.triggered.connect(self.open_gallery)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(MENU, self.action)
        self.iface.addPluginToMenu(MENU, self.gallery_action)

    def unload(self) -> None:
        if self.controller:
            self.controller.disconnect_project()
        for service in self.services:
            stop = getattr(service, "stop", None)
            if callable(stop):
                stop()
        if self.services:
            self.services[0].abort_all()            # Http
        if self.dock:
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
        for action in (self.action, self.gallery_action):
            if action:
                self.iface.removePluginMenu(MENU, action)
        if self.action:
            self.iface.removeToolBarIcon(self.action)
        self.dock = self.controller = None
        self.services = []

    # ---------- dock ----------

    def _build(self) -> None:
        settings = Settings()
        cfg = config.load_config()
        http = Http(cfg.server, plugin_version())
        api = MapflowApi(http)
        catalogue = Catalogue.load(config.RESOURCES / "scenarios")
        session = Session(cfg, http, api, settings)
        processings = Processings(api)
        imagery = Imagery(api)
        layers = MapLayers(self.iface)
        results = Results(api, layers, settings)
        self.dock = MapflowDock(catalogue, self.iface.mainWindow())
        self.controller = Controller(self.iface, self.dock.content, session, processings, imagery, results,
                                     layers, api, catalogue, settings)
        self.services = [http, session, processings, imagery, results]
        if hasattr(self.iface, "addTabifiedDockWidget"):
            self.iface.addTabifiedDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock, [], True)
        else:
            self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
        self.dock.visibilityChanged.connect(self.action.setChecked)
        session.restore()

    def toggle(self, checked: bool = True) -> None:
        if self.dock is None:
            self._build()
        self.dock.setUserVisible(checked)
        if checked:
            self.dock.raise_()

    def open_gallery(self) -> None:
        if self.dock is None:
            self._build()
        self.dock.setUserVisible(True)
        self.controller.open_gallery("")
