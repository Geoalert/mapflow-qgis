"""QGIS entry point: a Mapflow toolbar whose button opens the dock on the right, and the plugin's menu."""
from __future__ import annotations

from configparser import ConfigParser
from typing import Optional

from qgis.core import Qgis, QgsMessageLog, QgsProject
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAction, QToolBar

from . import config
from .api.client import MapflowApi
from .api.http import Http
from .controller import Controller
from .core import guard
from .core.guard import guarded
from .core.scenarios import Catalogue
from .qgis_bridge import aoi as aoi_tools
from .qgis_bridge import message_bar
from .qgis_bridge import rasters, updates
from .qgis_bridge.compat import RASTER_LAYER, VECTOR_LAYER
from .qgis_bridge.layers import MapLayers
from .services.imagery import Imagery
from .services.processings import Processings
from .services.results import Results
from .services.session import Session
from .settings import Settings
from .ui.dock import MapflowDock
from .ui.icons import app_icon
from .ui.theme import is_dark, load_fonts

MENU = "&Mapflow Next"
TOOLBAR = "MapflowToolbar"           # object name: QGIS remembers the toolbar's place and visibility by it


def _metadata() -> ConfigParser:
    parser = ConfigParser()
    parser.read(config.PLUGIN_DIR / "metadata.txt", encoding="utf-8")
    return parser


def plugin_version() -> str:
    return _metadata().get("general", "version", fallback="4.0.0")


def is_experimental() -> bool:
    return _metadata().getboolean("general", "experimental", fallback=False)


class MapflowNextPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action: Optional[QAction] = None
        self.gallery_action: Optional[QAction] = None
        self.updates_action: Optional[QAction] = None
        self.aoi_action: Optional[QAction] = None         # the Layers panel's menu of a polygon layer
        self.imagery_action: Optional[QAction] = None     # …and of a GeoTIFF layer
        self.toolbar: Optional[QToolBar] = None
        self.dock: Optional[MapflowDock] = None
        self.controller: Optional[Controller] = None
        self.layers: Optional[MapLayers] = None
        self.services = []

    # ---------- QGIS hooks ----------

    def initGui(self) -> None:
        guard.set_reporter(self._report)
        load_fonts()
        window = self.iface.mainWindow()
        self.action = QAction(app_icon(is_dark()), "Mapflow", window)
        self.action.setCheckable(True)
        self.action.setToolTip("Mapflow: map buildings, roads and forest from imagery")
        self.action.triggered.connect(self.toggle)
        self.gallery_action = QAction(app_icon(is_dark()), "Scenarios…", window)
        self.gallery_action.triggered.connect(guarded(lambda *_: self.open_gallery()))
        self.updates_action = QAction("Check for updates…", window)
        self.updates_action.setMenuRole(QAction.MenuRole.NoRole)    # macOS would move it to the app menu
        self.updates_action.triggered.connect(guarded(lambda *_: self.check_for_updates()))
        self.toolbar = self.iface.addToolBar(config.PLUGIN_SHORT_NAME)
        self.toolbar.setObjectName(TOOLBAR)
        self.toolbar.setToolTip("Mapflow")
        self.toolbar.addAction(self.action)
        for action in (self.action, self.gallery_action, self.updates_action):
            self.iface.addPluginToMenu(MENU, action)
        self._add_layer_actions()

    def unload(self) -> None:
        self._remove_layer_actions()
        if self.controller:
            self.controller.disconnect_project()
        for service in self.services:
            stop = getattr(service, "stop", None)
            if callable(stop):
                stop()
        if self.services:
            self.services[0].abort_all()            # Http
        if self.layers:
            self.layers.close()                     # after the last download: nothing writes into the folder
        if self.dock:
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
        for action in (self.action, self.gallery_action, self.updates_action):
            if action:
                self.iface.removePluginMenu(MENU, action)
        if self.toolbar:
            self.iface.mainWindow().removeToolBar(self.toolbar)
            self.toolbar.setParent(None)      # Python owns it now, and it goes when the reference does
        self.dock = self.controller = self.toolbar = self.layers = None
        self.services = []
        guard.clear_reporter(self._report)          # last, so a failure while unloading is still reported

    def _report(self, exc: BaseException, details: str) -> None:
        """The guard's reporter: the traceback to the QGIS log, then a Critical line on the message bar."""
        QgsMessageLog.logMessage(details, config.PLUGIN_NAME, Qgis.MessageLevel.Critical)
        message_bar.push(self.iface, f"Something went wrong: {exc}. Details are in the Log Messages panel.",
                         Qgis.MessageLevel.Critical)

    # ---------- the Layers panel's context menu ----------

    def _add_layer_actions(self) -> None:
        """“Use as AOI in Mapflow” on polygon layers and “Use as imagery in Mapflow” on GeoTIFF layers. QGIS
        offers custom actions per layer type, which is too wide (points, lines, tile layers), so each action is
        registered for no layer and then added to each layer it fits, as layers come."""
        window = self.iface.mainWindow()
        self.aoi_action = QAction(app_icon(is_dark()), "Use as AOI in Mapflow", window)
        self.aoi_action.triggered.connect(guarded(lambda *_: self._layer_action("aoi")))
        self.imagery_action = QAction(app_icon(is_dark()), "Use as imagery in Mapflow", window)
        self.imagery_action.triggered.connect(guarded(lambda *_: self._layer_action("imagery")))
        self.iface.addCustomActionForLayerType(self.aoi_action, "", VECTOR_LAYER, False)
        self.iface.addCustomActionForLayerType(self.imagery_action, "", RASTER_LAYER, False)
        project = QgsProject.instance()
        self._on_layers_added(list(project.mapLayers().values()))
        project.layersAdded.connect(self._on_layers_added)

    @guarded
    def _on_layers_added(self, layers) -> None:
        for layer in layers:
            if aoi_tools.is_polygon_layer(layer):
                self.iface.addCustomActionForLayer(self.aoi_action, layer)
            elif rasters.geotiff_path(layer):
                self.iface.addCustomActionForLayer(self.imagery_action, layer)

    def _remove_layer_actions(self) -> None:
        try:
            QgsProject.instance().layersAdded.disconnect(self._on_layers_added)
        except TypeError:
            pass
        for action in (self.aoi_action, self.imagery_action):
            if action:
                self.iface.removeCustomActionForLayerType(action)
        self.aoi_action = self.imagery_action = None

    def _layer_action(self, kind: str) -> None:
        view = self.iface.layerTreeView()
        layer = view.currentLayer() if view else self.iface.activeLayer()
        if layer is None:
            return
        if self.dock is None:
            self._build()
        self.dock.setUserVisible(True)
        self.dock.raise_()
        use = self.controller.use_layer_as_aoi if kind == "aoi" else self.controller.use_layer_as_imagery
        use(layer.id())

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
        layers = self.layers = MapLayers(self.iface)
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
        self.dock.visibilityChanged.connect(guarded(session.set_active))
        session.restore()

    @guarded
    def toggle(self, checked: bool = True) -> None:
        if self.dock is None:
            self._build()
        self.dock.setUserVisible(checked)
        if checked:
            self.dock.raise_()

    def check_for_updates(self) -> None:
        updates.report(self.iface, updates.check(plugin_version(), is_experimental()))

    def open_gallery(self) -> None:
        if self.dock is None:
            self._build()
        self.dock.setUserVisible(True)
        self.controller.open_gallery("")
