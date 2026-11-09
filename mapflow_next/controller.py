"""Wires the services (state) to the dock pages (views) and to QGIS (map, layers, message bar).

The main scenario lives here: model → area → imagery → processing → results.
"""
from __future__ import annotations

import functools
import traceback
from pathlib import Path
import json
from typing import Dict, List, Optional

from qgis.PyQt.QtCore import QObject, QTimer, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QPixmap
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis.core import Qgis, QgsGeometry, QgsMessageLog, QgsProject, QgsVectorLayer

from . import config
from .api.client import MapflowApi
from .core import formatting
from .core.draft import Coverage, ImageryChoice, RunDraft
from .core.models import BillingType, CatalogImage, Processing, UserStatus
from .core.scenarios import Catalogue, recommended_zoom, resolve, scenario_for_model
from .qgis_bridge import aoi as aoi_tools
from .qgis_bridge import message_bar
from .qgis_bridge.draw_tool import PolygonDrawTool
from .qgis_bridge.layers import MapLayers, bounds_extent
from .services.imagery import Imagery
from .services.processings import Processings
from .services.results import Results
from .services.session import SIGNED_IN, SIGNED_OUT, SIGNING_IN, Session
from .ui.dock import IMAGERY, PROCESSINGS, DockContent
from .ui.gallery import GalleryDialog
from .ui.mosaic_picker import MosaicPicker, image_count_text
from .ui.projects_dialog import ProjectsDialog
from .ui.rename_dialog import RenameDialog
from .ui.run_page import CostView, ImageryRow
from .ui.settings_dialog import SettingsDialog
from .ui.start_page import plain, scenario_pixmap

VECTOR_FILTER = "Vector files (*.geojson *.json *.gpkg *.shp *.kml *.kmz *.gml);;All files (*)"


PROJECTS_WINDOW_PAGE = 24        # eight rows of three tiles
EXTENT_PROPERTY = "mapflow_next/extent_of"   # on an area layer made from My imagery: the imagery's name


def guarded(method):
    """Slots never let an exception escape into Qt: it is logged and shown, the plugin keeps working."""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - last line of defence for UI slots
            QgsMessageLog.logMessage(traceback.format_exc(), config.PLUGIN_NAME, Qgis.MessageLevel.Critical)
            self.notify(f"Something went wrong: {exc}. Details are in the Log Messages panel.",
                        Qgis.MessageLevel.Critical)
    return wrapper


class Controller(QObject):
    def __init__(self, iface, content: DockContent, session: Session, processings: Processings,
                 imagery: Imagery, results: Results, layers: MapLayers, api: MapflowApi, catalogue: Catalogue,
                 settings, parent=None):
        super().__init__(parent)
        self.iface, self.content, self.session, self.processings = iface, content, session, processings
        self.imagery, self.results, self.layers, self.api = imagery, results, layers, api
        self.catalogue, self.settings = catalogue, settings
        self.draft = RunDraft()
        self.aoi_layer: Optional[QgsVectorLayer] = None
        self.aoi_selected_only = True
        self.provider_zoom: Dict[str, int] = {}
        self.preferred_zoom: Optional[int] = None
        self.chosen_image: Optional[CatalogImage] = None
        self.server_cost: Optional[int] = None
        self.cost_error = ""
        self.cost_token = 0
        self.starting = False
        self.draw_tool: Optional[PolygonDrawTool] = None
        self.previous_tool = None
        self.gallery: Optional[GalleryDialog] = None
        self.projects_dialog: Optional[ProjectsDialog] = None
        self.mosaic_picker: Optional[MosaicPicker] = None
        self._projects_request = 0
        self._area_counter = 0
        self._footprints: Dict[tuple, object] = {}       # My imagery footprints (QgsGeometry), by source
        self._extent_layers: Dict[tuple, str] = {}       # extent layers made from them: source → layer id
        self._extent_pending = False                     # waiting for image footprints to make the extent
        self._previous_aoi: Optional[str] = None         # the area layer before the extent replaced it
        self._coverage_for = None
        self._mosaic_render = QTimer(self)        # many collections report their image counts at once
        self._mosaic_render.setSingleShot(True)
        self._mosaic_render.setInterval(150)
        self._mosaic_render.timeout.connect(self._render_mosaics)
        self._connect()

    # ---------- wiring ----------

    def _connect(self) -> None:
        c, s, p = self.content, self.session, self.processings
        s.stateChanged.connect(self.on_state)
        s.statusChanged.connect(self.on_status)
        s.projectsChanged.connect(lambda *_: c.set_project(s.project))
        s.projectChanged.connect(self.on_project)
        s.error.connect(self.on_session_error)

        c.sign_in.browserRequested.connect(self.sign_in_browser)
        c.sign_in.cancelRequested.connect(self.session.cancel_sign_in)
        c.sign_in.tokenSubmitted.connect(self.sign_in_token)
        c.sign_in.networkSettingsRequested.connect(
            lambda: self.iface.showOptionsDialog(self.iface.mainWindow(), "mOptionsPageNetwork"))
        c.projectsRequested.connect(self.open_projects)
        c.settingsRequested.connect(self.open_settings)
        c.signOutRequested.connect(self.sign_out)
        c.tabChanged.connect(self.on_tab)

        c.start.scenarioChosen.connect(self.apply_scenario)
        c.start.galleryRequested.connect(self.open_gallery)
        c.start.customRequested.connect(self.custom_setup)
        c.start.processingsRequested.connect(lambda: c.go(PROCESSINGS))

        run = c.run
        run.backRequested.connect(c.open_start)
        run.changeScenarioRequested.connect(lambda *_: self.open_gallery(""))
        run.nameEdited.connect(self.on_name)
        run.renameRequested.connect(self.rename_draft)
        run.modelChosen.connect(self.on_model)
        run.optionToggled.connect(self.on_option)
        run.layerChosen.connect(self.on_layer)
        run.areaAction.connect(self.on_area_action)
        run.imageryChosen.connect(self.on_imagery)
        run.zoomChosen.connect(self.on_zoom)
        run.mosaicPickRequested.connect(lambda *_: self.open_mosaic_picker())
        run.catalogRemoved.connect(self.on_catalog_removed)
        run.previewRequested.connect(self.preview_imagery)
        run.searchImageryRequested.connect(self.open_search)
        run.runRequested.connect(self.run)

        page = c.processings
        page.addToMap.connect(self.add_to_map)
        page.zoomTo.connect(lambda pid: self.layers.zoom_to(self.layers.layers_for(pid)))
        page.saveGeojson.connect(self.save_geojson)
        page.restart.connect(self.restart)
        page.rename.connect(self.rename)
        page.duplicate.connect(self.duplicate)
        page.delete.connect(self.delete)
        page.openWeb.connect(lambda _pid: QDesktopServices.openUrl(QUrl(config.WEB_URL)))
        page.rate.connect(self.rate)
        page.startRequested.connect(c.open_start)
        page.refreshRequested.connect(p.refresh)
        page.moreRequested.connect(p.load_more)

        imagery_page = c.imagery
        imagery_page.searchRequested.connect(self.search)
        imagery_page.useImage.connect(self.use_image)
        imagery_page.showImage.connect(self.show_image)
        imagery_page.useMosaic.connect(self.use_mosaic)
        imagery_page.showMosaic.connect(self.show_mosaic)
        imagery_page.uploadRequested.connect(self.upload)
        imagery_page.useMapExtent.connect(lambda *_: self.on_area_action("extent"))
        imagery_page.layerChosen.connect(self.on_layer)
        imagery_page.clearRequested.connect(self.clear_search)

        p.changed.connect(self.on_processings)
        p.started.connect(self.on_started)
        p.startFailed.connect(self.on_start_failed)
        p.finished.connect(self.on_finished)
        p.failed.connect(self.on_failed)
        p.costReady.connect(self.on_cost)
        p.actionFailed.connect(lambda text: self.notify(text, Qgis.MessageLevel.Warning))

        self.imagery.searchDone.connect(self.on_search_done)
        self.imagery.searchFailed.connect(self.on_search_failed)
        self.imagery.mosaicsChanged.connect(self.on_mosaics)
        self.imagery.mosaicImagesChanged.connect(self.on_mosaic_images)
        self.imagery.uploadProgress.connect(lambda value: c.imagery.set_upload(value))
        self.imagery.uploadDone.connect(lambda name: (
            c.imagery.set_upload(None, f"“{name}” is uploaded and ready to use.", "info"),
            self.notify(f"“{name}” is uploaded to My imagery.", Qgis.MessageLevel.Success)))
        self.imagery.uploadFailed.connect(lambda text: c.imagery.set_upload(None, text, "error"))

        self.results.loaded.connect(self.on_results_loaded)
        self.results.failed.connect(self.on_results_failed)
        self.results.busy.connect(lambda *_: self.render_processings())

        project = QgsProject.instance()
        project.layersAdded.connect(self.on_layers_changed)
        project.layersRemoved.connect(self.on_layers_removed)

    def disconnect_project(self) -> None:
        project = QgsProject.instance()
        for signal, slot in ((project.layersAdded, self.on_layers_changed),
                             (project.layersRemoved, self.on_layers_removed)):
            try:
                signal.disconnect(slot)
            except TypeError:
                pass
        self._watch_layer(None)
        self.stop_drawing()
        if self.gallery:
            self.gallery.close()

    def notify(self, text: str, level=Qgis.MessageLevel.Info, action: Optional[tuple] = None,
               duration: int = 6) -> None:
        message_bar.push(self.iface, text, level, action, duration)

    # ---------- session ----------

    @guarded
    def sign_in_browser(self) -> None:
        self.content.sign_in.clear()
        self.session.sign_in_browser()

    @guarded
    def sign_in_token(self, token: str) -> None:
        self.content.sign_in.show_error("")
        self.session.sign_in_token(token)

    @guarded
    def sign_out(self) -> None:
        self.processings.stop()
        self.session.sign_out()
        self.notify("You're signed out of Mapflow.", Qgis.MessageLevel.Info, duration=4)

    @guarded
    def on_state(self, state: str) -> None:
        sign_in = self.content.sign_in
        if state == SIGNING_IN:
            # The browser path waits for the person; a token or a saved sign-in is a quick check
            sign_in.set_busy(True, waiting_browser=self.session.browser.active)
        elif state == SIGNED_OUT:
            sign_in.set_busy(False)
            self.processings.stop()
            self.processings.set_project(None)
            # Sign-out aborts requests in flight, and aborted requests report nothing back
            self.results.reset()
            self.content.imagery.set_searching(False)
            self.content.imagery.set_upload(None)
            for dialog in (self.projects_dialog, self.mosaic_picker):
                if dialog is not None:
                    dialog.close()
            self.content.show_signed_out()
        elif state == SIGNED_IN:
            sign_in.set_busy(False)
            sign_in.clear()
            self.content.set_account(self.session.email)
            self.content.set_project(self.session.project)
            self.content.show_signed_in()
            self.imagery.load_mosaics()

    def on_session_error(self, text: str) -> None:
        if self.session.state != SIGNED_IN:
            self.content.sign_in.show_error(text, open_token=self.session.method == "token")
        else:
            self.notify(text, Qgis.MessageLevel.Warning)

    @guarded
    def on_status(self, status: UserStatus) -> None:
        if status.billing is BillingType.credits:
            self.content.set_credits(f"{status.remaining_credits:,}",
                                     f"{status.remaining_credits:,} credits. Top up in Mapflow Web")
        elif status.billing is BillingType.area:
            self.content.set_credits(formatting.km2(status.remaining_area_km2),
                                     f"{formatting.km2(status.remaining_area_km2)} left on your plan")
        else:
            self.content.set_credits("", "")
        self.content.processings.provider_names = {p.name: p.display_name for p in status.data_providers}
        if self.draft.imagery is None:
            self._choose_default_imagery()
        elif self.draft.imagery.kind == "provider":
            # providers may have been updated: re-attach the fresh object
            provider = next((p for p in status.data_providers if p.name == self.draft.imagery.provider.name), None)
            if provider:
                self.draft.imagery = ImageryChoice.from_provider(provider, self.draft.imagery.zoom)
        self.refresh_run()

    @guarded
    def on_project(self, project) -> None:
        self.content.set_project(project)
        self.processings.set_project(project)
        if self.draft.model and not project.model(self.draft.model.id):
            self.draft.model, self.draft.options = None, set()
        if self.draft.scenario_id and not self.draft.model:
            scenario = self.catalogue.get(self.draft.scenario_id)
            if scenario:
                resolution = resolve(scenario, project.models)
                self.draft.model, self.draft.options = resolution.model, set(resolution.options)
        self.content.processings.can_manage = project.role.can_manage
        self.refresh_run()

    @guarded
    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self.session.email, self.session.config.server,
                                self.iface.mainWindow())
        if dialog.exec() and dialog.signed_out:
            self.sign_out()

    # ---------- projects ----------

    def _pinned_key(self) -> str:
        return f"pinned_projects/{self.session.config.env}/{self.session.email or 'anyone'}"

    def pinned_projects(self) -> List[str]:
        try:
            value = json.loads(self.settings.value(self._pinned_key(), "[]") or "[]")
        except (TypeError, ValueError):
            return []
        return [str(v) for v in value] if isinstance(value, list) else []

    @guarded
    def open_projects(self) -> None:
        if self.projects_dialog is None:
            dialog = ProjectsDialog(self.iface.mainWindow())
            dialog.queryChanged.connect(self._query_projects)
            dialog.moreRequested.connect(self._more_projects)
            dialog.projectChosen.connect(self._choose_project)
            dialog.pinToggled.connect(self._pin_project)
            dialog.shareRequested.connect(lambda *_: QDesktopServices.openUrl(QUrl(config.PROJECTS_URL)))
            self.projects_dialog = dialog
        dialog = self.projects_dialog
        dialog.search.blockSignals(True)
        dialog.search.clear()
        dialog.search.blockSignals(False)
        dialog.query = ""
        dialog.set_state(self.session.project.id if self.session.project else None, self.pinned_projects())
        self._query_projects("")
        for project_id in self.pinned_projects():
            self.api.project(project_id, self.session.email, self._pinned_loaded, lambda _e: None)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _pinned_loaded(self, project) -> None:
        if self.projects_dialog is not None:
            self.projects_dialog.set_pinned_project(project)

    def _query_projects(self, query: str, offset: int = 0) -> None:
        dialog = self.projects_dialog
        if dialog is None:
            return
        dialog.query = query
        if self._projects_request:
            self.api.http.abort(self._projects_request)
        dialog.set_loading(True)

        def done(projects, total, q=query, append=offset > 0):
            self._projects_request = 0
            if self.projects_dialog is not None and self.projects_dialog.query == q:
                self.projects_dialog.set_results(projects, total, append=append)

        def failed(error):
            self._projects_request = 0
            if self.projects_dialog is not None:
                self.projects_dialog.set_loading(False)
            self.notify(f"Projects didn't load: {error.message}", Qgis.MessageLevel.Warning)

        self._projects_request = self.api.projects_page(self.session.email, done, failed, query=query, offset=offset,
                                                        limit=PROJECTS_WINDOW_PAGE)

    def _more_projects(self) -> None:
        dialog = self.projects_dialog
        if dialog is not None:
            self._query_projects(dialog.query, offset=len(dialog.results))

    @guarded
    def _choose_project(self, project_id: str) -> None:
        if self.projects_dialog is not None:
            self.projects_dialog.accept()
        if not self.session.project or project_id != self.session.project.id:
            self.session.select_project(project_id)

    @guarded
    def _pin_project(self, project_id: str, pinned: bool) -> None:
        ids = [i for i in self.pinned_projects() if i != project_id]
        if pinned:
            ids.insert(0, project_id)
        self.settings.setValue(self._pinned_key(), json.dumps(ids))
        dialog = self.projects_dialog
        if dialog is not None:
            known = next((p for p in dialog.results if p.id == project_id), None)
            if pinned and known is not None:
                dialog.pinned[project_id] = known
            dialog.set_state(dialog.current_id, ids)

    def on_tab(self, tab: int) -> None:
        if tab == IMAGERY:
            self.render_imagery_area()
        if tab == PROCESSINGS:
            self.processings.refresh()

    # ---------- scenarios ----------

    @guarded
    def apply_scenario(self, scenario_id: str) -> None:
        scenario = self.catalogue.get(scenario_id)
        if scenario is None:
            return
        if self.gallery:
            self.gallery.hide()
        if scenario.imagery_hint == "search":
            self.open_search()
            self.notify(scenario.apply.get("hint", ""), Qgis.MessageLevel.Info)
            return
        self.draft.scenario_id = scenario.id
        self.draft.name, self.draft.name_edited, self.draft.description = "", False, ""   # a fresh name
        project = self.session.project
        resolution = resolve(scenario, project.models if project else [])
        if scenario.apply.get("model"):
            self.draft.model, self.draft.options = resolution.model, set(resolution.options)
            if resolution.model is None and project:
                self.notify(f"This project has no “{plain(scenario.model_label)}” model. Pick another model "
                            "or add it to the project in Mapflow Web.", Qgis.MessageLevel.Warning)
            elif resolution.missing_options:
                self.notify(f"The option “{', '.join(resolution.missing_options)}” isn't available for this model "
                            "in your project.", Qgis.MessageLevel.Warning)
        self.preferred_zoom = recommended_zoom(scenario)
        if scenario.imagery_hint == "my_imagery":
            if self.imagery.mosaics:
                mosaic = self.imagery.mosaics[0]
                self.draft.imagery = ImageryChoice.from_mosaic(mosaic.id, mosaic.name)
                if self.draft.aoi is None:
                    self.use_imagery_extent()
            else:
                self.notify(scenario.apply.get("hint", ""), Qgis.MessageLevel.Info)
        elif self.draft.imagery and self.draft.imagery.kind == "provider":
            provider = self.draft.imagery.provider
            self.provider_zoom.clear()          # a new scenario starts from its recommended zoom
            self.draft.imagery = ImageryChoice.from_provider(provider, self.preferred_zoom)
        elif self.draft.imagery is None:
            self._choose_default_imagery()
        self._adopt_active_layer()
        self.content.open_run()
        self.refresh_run()

    @guarded
    def custom_setup(self) -> None:
        self.draft.scenario_id = None
        self.draft.name, self.draft.name_edited, self.draft.description = "", False, ""
        self.preferred_zoom = recommended_zoom(None)
        self._adopt_active_layer()
        self.content.open_run()
        self.refresh_run()

    @guarded
    def open_gallery(self, query: str = "") -> None:
        if self.gallery is None:
            self.gallery = GalleryDialog(self.catalogue, self.iface.mainWindow())
            self.gallery.scenarioChosen.connect(self.apply_scenario)
        self.gallery.set_query(query or "")
        self.gallery.show()
        self.gallery.raise_()
        self.gallery.activateWindow()

    def _adopt_active_layer(self) -> None:
        """If no area is set yet, the polygon layer the user is working on is the likely one."""
        if self.draft.aoi is None:
            layer = self.iface.activeLayer()
            if aoi_tools.is_polygon_layer(layer):
                self.set_aoi_layer(layer)

    # ---------- run form: model ----------

    @guarded
    def on_name(self, text: str) -> None:
        self.draft.name, self.draft.name_edited = text, bool(text.strip())
        self.refresh_run(keep_name=True)

    @guarded
    def rename_draft(self) -> None:
        """The pencil by the name: the same dialog as renaming a processing, for the one about to run."""
        dialog = RenameDialog(self.draft.effective_name(), self.draft.description, self.iface.mainWindow(),
                              title="Name this processing")
        if dialog.exec():
            name, description = dialog.values()
            if name:
                self.draft.name, self.draft.name_edited = name, name != self.draft.default_name()
            self.draft.description = description
            self.content.run.set_name(self.draft.effective_name(), self.draft.description, force=True)
            self.refresh_run(keep_name=True)

    @guarded
    def on_model(self, model_id: str) -> None:
        project = self.session.project
        model = project.model(model_id) if project else None
        if model is None:
            return
        self.draft.model = model
        self.draft.options = set()
        scenario = self.catalogue.get(self.draft.scenario_id)
        if scenario:
            resolution = resolve(scenario, [model])
            if resolution.model is None:
                self.draft.scenario_id = None
            else:
                self.draft.options = set(resolution.options)
        if not self.draft.scenario_id:
            match = scenario_for_model(self.catalogue, model, [])
            self.draft.scenario_id = match.id if match else None
        self.refresh_run()

    @guarded
    def on_option(self, name: str, enabled: bool) -> None:
        (self.draft.options.add if enabled else self.draft.options.discard)(name)
        self.refresh_run()

    # ---------- run form: area ----------

    @guarded
    def on_layer(self, layer_id: str) -> None:
        """An area layer chosen on the run form or on the catalog search: both share the area."""
        layer = QgsProject.instance().mapLayer(layer_id)
        if aoi_tools.is_polygon_layer(layer):
            self.set_aoi_layer(layer)
            self.refresh_run()
            self.render_imagery_area()

    @guarded
    def on_area_action(self, action: str) -> None:
        canvas = self.iface.mapCanvas()
        if action == "draw":
            if self.draw_tool and canvas.mapTool() is self.draw_tool:
                self.stop_drawing()
            else:
                self.start_drawing()
        elif action == "selected":
            layer = self.iface.activeLayer()
            if not aoi_tools.is_polygon_layer(layer) or not layer.selectedFeatureCount():
                self.notify("Select one or more polygons on a polygon layer first, then press Selected.",
                            Qgis.MessageLevel.Info)
                return
            self.set_aoi_layer(layer, selected_only=True)
        elif action == "extent":
            geometry = QgsGeometry.fromRect(canvas.extent())
            self._area_counter += 1
            layer = aoi_tools.memory_layer(geometry, canvas.mapSettings().destinationCrs(),
                                           f"Mapflow area {self._area_counter} (map view)")
            self.layers.add(layer)
            self.set_aoi_layer(layer)
        elif action == "file":
            path, _ = QFileDialog.getOpenFileName(self.content, "Open an area of interest", "", VECTOR_FILTER)
            if not path:
                return
            layer = QgsVectorLayer(path, Path(path).stem, "ogr")
            if not aoi_tools.is_polygon_layer(layer):
                self.notify("That file has no polygons. Choose a file with area polygons.", Qgis.MessageLevel.Warning)
                return
            layer.loadNamedStyle(str(config.RESOURCES / "styles" / "aoi.qml"))
            self.layers.add(layer)
            self.set_aoi_layer(layer)
        elif action == "imagery_extent":
            self.use_imagery_extent()
            return
        elif action == "edit_outline":
            self.edit_outline()
            return
        elif action == "previous":
            layer = QgsProject.instance().mapLayer(self._previous_aoi or "")
            if aoi_tools.is_polygon_layer(layer):
                self.set_aoi_layer(layer)
        self.refresh_run()
        self.render_imagery_area()

    def start_drawing(self) -> None:
        canvas = self.iface.mapCanvas()
        self.previous_tool = canvas.mapTool()
        self.draw_tool = PolygonDrawTool(canvas)
        self.draw_tool.finished.connect(self.on_drawn)
        self.draw_tool.cancelled.connect(self.stop_drawing)
        canvas.setMapTool(self.draw_tool)
        canvas.setFocus()
        self.content.run.set_drawing(True)
        self.notify("Click the corners of your area. Double-click or right-click to finish, Esc to cancel.",
                    Qgis.MessageLevel.Info, duration=8)

    def stop_drawing(self) -> None:
        canvas = self.iface.mapCanvas() if self.iface else None
        if canvas and self.draw_tool and canvas.mapTool() is self.draw_tool:
            canvas.unsetMapTool(self.draw_tool)
            if self.previous_tool:
                canvas.setMapTool(self.previous_tool)
        self.content.run.set_drawing(False)

    @guarded
    def on_drawn(self, geometry: QgsGeometry) -> None:
        self.stop_drawing()
        canvas = self.iface.mapCanvas()
        self._area_counter += 1
        layer = aoi_tools.memory_layer(geometry, canvas.mapSettings().destinationCrs(),
                                       f"Mapflow area {self._area_counter}")
        self.layers.add(layer)
        self.set_aoi_layer(layer)
        self.refresh_run()
        self.render_imagery_area()

    def set_aoi_layer(self, layer: Optional[QgsVectorLayer], selected_only: bool = True) -> None:
        self._watch_layer(layer)
        self.aoi_selected_only = selected_only
        self.recompute_aoi()

    def _watch_layer(self, layer: Optional[QgsVectorLayer]) -> None:
        if self.aoi_layer is not None:
            for signal in (self.aoi_layer.selectionChanged, self.aoi_layer.editingStopped,
                           self.aoi_layer.featuresDeleted, self.aoi_layer.featureAdded):
                try:
                    signal.disconnect(self._layer_changed)
                except (TypeError, RuntimeError):
                    pass
        self.aoi_layer = layer
        if layer is not None:
            for signal in (layer.selectionChanged, layer.editingStopped, layer.featuresDeleted, layer.featureAdded):
                signal.connect(self._layer_changed)

    def _layer_changed(self, *args) -> None:
        if self.aoi_layer is not None and self.aoi_layer.isEditable():
            return   # wait for the edit to be saved
        self.recompute_aoi()
        self.refresh_run()
        self.render_imagery_area()

    def recompute_aoi(self) -> None:
        if self.aoi_layer is None:
            self.draft.aoi = None
            return
        self.draft.aoi = aoi_tools.aoi_from_layer(self.aoi_layer, self.aoi_selected_only)
        extent_of = self.aoi_layer.customProperty(EXTENT_PROPERTY)
        if self.draft.aoi is not None and extent_of:
            self.draft.aoi.name = str(extent_of)     # "Buildings · Beirut", not "… · Extent of Beirut"

    @guarded
    def on_layers_changed(self, *args) -> None:
        if self.content.stack.currentWidget() is self.content.run:
            self.refresh_run()
        self.render_imagery_area()

    @guarded
    def on_layers_removed(self, layer_ids) -> None:
        if self.aoi_layer is not None and self.draft.aoi and self.draft.aoi.layer_id in layer_ids:
            self.aoi_layer = None
            self.draft.aoi = None
        self.refresh_run()
        self.render_processings()

    # ---------- run form: imagery ----------

    def _choose_default_imagery(self) -> None:
        status = self.session.status
        if not status or not status.data_providers:
            return
        providers = status.data_providers
        provider = next((p for p in providers if "mapbox" in p.name.lower()), providers[0])
        zoom = self.provider_zoom.get(provider.name, self.preferred_zoom)
        self.draft.imagery = ImageryChoice.from_provider(provider, zoom)

    @guarded
    def on_imagery(self, key: str) -> None:
        status = self.session.status
        if key.startswith("provider:") and status:
            name = key.split(":", 1)[1]
            provider = next((p for p in status.data_providers if p.name == name), None)
            if provider:
                self.draft.imagery = ImageryChoice.from_provider(
                    provider, self.provider_zoom.get(name, self.preferred_zoom))
        elif key == "mosaic" and self.imagery.mosaics:
            if self.draft.imagery and self.draft.imagery.kind == "my_imagery":
                return                                  # already chosen; "Choose…" opens the picker
            mosaic = self.last_mosaic() or self.imagery.mosaics[0]
            self.draft.imagery = ImageryChoice.from_mosaic(mosaic.id, mosaic.name)
            self.use_imagery_extent()
        elif key == "catalog" and self.chosen_image:
            self.draft.imagery = self._catalog_choice(self.chosen_image)
        self.refresh_run()

    @guarded
    def on_zoom(self, key: str, zoom: int) -> None:
        name = key.split(":", 1)[1]
        self.provider_zoom[name] = int(zoom)
        status = self.session.status
        provider = next((p for p in status.data_providers if p.name == name), None) if status else None
        if provider:
            self.draft.imagery = ImageryChoice.from_provider(provider, int(zoom))
        self.refresh_run()

    # ---------- My imagery: extent as the area, and the area against the imagery ----------

    def _imagery_footprint(self):
        """(name, footprint, key) of the chosen My imagery: one image's extent, or the collection's
        (the union of its images once they are loaded). None while it isn't known."""
        choice = self.draft.imagery
        if not choice or choice.kind != "my_imagery":
            return None
        if choice.image_ids:
            image = self.imagery.get_image(choice.mosaic_id, choice.image_ids[0])
            if image is None or not image.footprint_wkt:
                return None
            name, wkts, key = image.filename or "the image", [image.footprint_wkt], ("image", image.id)
        else:
            mosaic = self.imagery.get_mosaic(choice.mosaic_id)
            images = self.imagery.images.get(choice.mosaic_id) or []
            wkts = [i.footprint_wkt for i in images if i.footprint_wkt] or \
                ([mosaic.footprint_wkt] if mosaic and mosaic.footprint_wkt else [])
            if not wkts:
                return None
            name, key = (mosaic.name if mosaic else "the collection"), ("collection", choice.mosaic_id, len(wkts))
        geometry = self._footprints.get(key)
        if geometry is None:
            geometry = aoi_tools.footprint(wkts)
            if geometry is None:
                return None
            self._footprints[key] = geometry
        return name, geometry, key

    def _update_coverage(self) -> None:
        """For My imagery: does the area overlap the imagery, and which part of it is inside."""
        draft = self.draft
        found = self._imagery_footprint() if draft.aoi else None
        if found is None:
            draft.coverage, self._coverage_for = None, None
            return
        name, geometry, key = found
        if draft.coverage is not None and self._coverage_for and self._coverage_for[0] == key \
                and self._coverage_for[1] is draft.aoi:
            return                                   # same area, same imagery
        clipped = aoi_tools.clip_to(draft.aoi, geometry)
        draft.coverage = Coverage(name, clipped is not None, clipped)
        self._coverage_for = (key, draft.aoi)

    def _is_extent_layer(self, layer) -> bool:
        return bool(layer is not None and layer.customProperty(EXTENT_PROPERTY))

    def _area_hint(self, outside: bool, area_issue: str):
        coverage = self.draft.coverage
        if outside:
            return "warn", area_issue, (("Use the imagery extent", "imagery_extent"),)
        if self.draft.aoi and self._is_extent_layer(self.aoi_layer):
            actions = [("Draw a smaller area", "draw"), ("Edit the outline", "edit_outline")]
            previous = QgsProject.instance().mapLayer(self._previous_aoi or "")
            if aoi_tools.is_polygon_layer(previous) and previous is not self.aoi_layer:
                actions.append((f"Back to “{previous.name()}”", "previous"))
            name = self.aoi_layer.customProperty(EXTENT_PROPERTY)
            return ("info", f"The area is the whole extent of “{name}”. To process only part of it, draw a "
                            "smaller area or edit the outline.", tuple(actions))
        if coverage and coverage.clipped and self.draft.aoi \
                and coverage.clipped.area_km2 < self.draft.aoi.area_km2 * 0.999:
            return "info", f"Only the part of the area inside “{coverage.name}” is processed and billed.", ()
        return "info", "", ()

    def use_imagery_extent(self) -> None:
        """Make the chosen My imagery's extent the area: a layer the user can edit or replace."""
        choice = self.draft.imagery
        found = self._imagery_footprint()
        if found is None:
            if choice and choice.kind == "my_imagery" and choice.mosaic_id:
                self._extent_pending = True          # its footprint comes with the image list
                self.imagery.load_images(choice.mosaic_id)
            return
        self._extent_pending = False
        name, geometry, key = found
        layer = QgsProject.instance().mapLayer(self._extent_layers.get(key, ""))
        if layer is None:
            layer = aoi_tools.extent_layer(geometry, f"Extent of {name}")
            layer.setCustomProperty(EXTENT_PROPERTY, name)
            self.layers.add(layer)
            self._extent_layers[key] = layer.id()
        if self.aoi_layer is not None and self.aoi_layer is not layer and not self._is_extent_layer(self.aoi_layer):
            self._previous_aoi = self.aoi_layer.id()
        self.set_aoi_layer(layer)
        self.layers.zoom_to([layer])
        self.refresh_run()
        self.render_imagery_area()

    def edit_outline(self) -> None:
        """Start editing the area layer's outline on the map (QGIS's vertex tool)."""
        layer = self.aoi_layer
        if layer is None:
            return
        self.iface.setActiveLayer(layer)
        layer.startEditing()
        vertex_tool = getattr(self.iface, "actionVertexTool", None)
        if callable(vertex_tool):
            vertex_tool().trigger()
        self.notify("Drag the outline's corners on the map, then save the layer's edits (Toggle Editing) to "
                    "update the area.", Qgis.MessageLevel.Info, duration=8)

    def last_mosaic(self):
        return self.imagery.get_mosaic(getattr(self, "_last_mosaic_id", None))

    @guarded
    def on_catalog_removed(self) -> None:
        self.chosen_image = None
        if self.draft.imagery and self.draft.imagery.kind == "catalog":
            self.draft.imagery = None
            self._choose_default_imagery()
        self.refresh_run()
        self.render_search_results()

    @guarded
    def preview_imagery(self) -> None:
        choice = self.draft.imagery
        if choice is None:
            return
        if choice.kind == "provider" and choice.provider and choice.provider.preview_url:
            layer = self.layers.tile_raster(choice.provider.preview_url, f"{choice.provider.display_name} · preview",
                                            zmax=choice.provider.preview_max_zoom or 18)
            if layer:
                self.layers.add(layer, position=len(self.layers.group().children()))
                self.notify(f"{choice.provider.display_name} preview is on the map, "
                            "at the bottom of the Mapflow group.")
        elif choice.kind == "my_imagery":
            self.show_mosaic(choice.mosaic_id)
        elif choice.kind == "catalog" and self.chosen_image:
            self.show_image(self.chosen_image.id)

    def _catalog_choice(self, image: CatalogImage) -> ImageryChoice:
        when = f"{image.acquired.day} {image.acquired:%b %Y}" if image.acquired else ""
        title = f"{_provider_name(image.provider)} {'mosaic' if image.is_mosaic else 'scene'}"
        return ImageryChoice.from_catalog(image.id, image.provider, image.zoom, f"{title} {when}".strip())

    # ---------- run form: rendering ----------

    def refresh_run(self, keep_name: bool = False) -> None:
        with self.content.run.keep_scroll():
            self._refresh_run(keep_name)

    def _refresh_run(self, keep_name: bool) -> None:
        run = self.content.run
        if self.draft.imagery and self.draft.imagery.kind == "my_imagery":
            self._last_mosaic_id = self.draft.imagery.mosaic_id
        project, status = self.session.project, self.session.status
        scenario = self.catalogue.get(self.draft.scenario_id)
        run.set_scenario(scenario.title if scenario else "Custom setup",
                         scenario_pixmap(self.catalogue, scenario, 52, 34) if scenario else None)
        if not keep_name:
            run.set_name(self.draft.effective_name(), self.draft.description)
        credits_billing = bool(status and status.billing is BillingType.credits)
        models = project.models if project else []
        run.set_models(models, self.draft.model.id if self.draft.model else None)
        base = f"{self.draft.model.base_price:g} cr/km²" if (self.draft.model and credits_billing) else ""
        note = ""
        if scenario and not self.draft.model and scenario.apply.get("model"):
            note = f"This project has no “{plain(scenario.model_label)}” model. Pick another one."
        run.set_options(self.draft.model, self.draft.options, base, note)

        layers = [(layer.id(), layer.name()) for layer in aoi_tools.polygon_layers()]
        run.set_layers(layers, self.draft.aoi.layer_id if self.draft.aoi else None)
        self._update_coverage()
        issues = self.draft.issues(project, status, self.server_cost)
        area_issue = next((i.text for i in issues if i.field == "area" and self.draft.aoi), "")
        coverage = self.draft.coverage
        outside = bool(self.draft.aoi and coverage and not coverage.overlaps)
        if self.draft.aoi:
            aoi, processed = self.draft.aoi, self.draft.processed_area
            parts = [aoi.name, _count(aoi.layer_features or aoi.polygons, "polygon")]
            if aoi.selected:
                parts.append(f"{_count(aoi.selected, 'polygon')} selected")
            if processed is not aoi and processed.area_km2 < aoi.area_km2 * 0.999:
                parts.append(f"{formatting.km2(processed.area_km2)} of {formatting.km2(aoi.area_km2)} "
                             "inside the imagery")
            limit = project.aoi_area_limit_km2 if project else 0
            if limit and not area_issue:
                parts.append(f"within your {formatting.km2(limit)} limit")
            if processed.area_km2 < config.MIN_BILLED_AREA_KM2 and not outside:
                parts.append("billed as 1 km²")
            # outside the imagery: the suggestion below says it, with a way out
            run.set_area(formatting.km2(processed.area_km2), " · ".join(parts), "" if outside else area_issue)
        else:
            run.set_area("", "Pick a polygon layer, draw the area, or use the map view.")
        run.set_area_hint(*self._area_hint(outside, area_issue))

        rows, selected = self._imagery_rows(status, credits_billing)
        imagery_issue = next((i.text for i in issues if i.field == "imagery" and self.draft.imagery), "")
        hint = f"Recommended for this scenario: {scenario.best_short}" if scenario and scenario.best_short else ""
        run.set_imagery(rows, selected, hint, imagery_issue)
        run.set_steps(self.draft.model is not None, bool(self.draft.aoi and not area_issue),
                      bool(self.draft.imagery and not imagery_issue))
        run.set_cost(self._cost_view(status), credits_billing)
        run.set_issues(issues, self.starting)
        self._maybe_request_cost(issues, status)

    def _imagery_rows(self, status: Optional[UserStatus], credits_billing: bool):
        """My imagery first, then the basemap providers (zoom z17–z21, the scenario's zoom marked), then an
        image chosen in the catalog search (its zoom follows the image's resolution, as in the current plugin)."""
        rows = []
        choice = self.draft.imagery
        selected = None
        recommended = self.preferred_zoom or recommended_zoom(self.catalogue.get(self.draft.scenario_id))
        if self.imagery.mosaics:
            mine = choice.kind == "my_imagery" if choice else False
            mosaic = (self.imagery.get_mosaic(choice.mosaic_id) if mine
                      else (self.last_mosaic() or self.imagery.mosaics[0]))
            meta = "Your own GeoTIFF collections"
            if mosaic is not None:
                image = self.imagery.get_image(mosaic.id, choice.image_ids[0]) if mine and choice.image_ids else None
                if mine and choice.image_ids:
                    detail = image.filename if image else "one image"
                else:
                    detail = image_count_text(mosaic) or "whole collection"
                meta = f"{mosaic.name} · {detail}"
            rows.append(ImageryRow(key="mosaic", title="My imagery", meta=meta, pick="Choose…",
                                   price="Free" if credits_billing else "", previewable=True))
            if mine:
                selected = "mosaic"
        for provider in (status.data_providers if status else []):
            chosen = bool(choice and choice.kind == "provider" and choice.provider.name == provider.name)
            zoom = choice.zoom if chosen else provider.nearest_zoom(self.provider_zoom.get(provider.name, recommended))
            price = provider.price_at(zoom)
            star = recommended if recommended in provider.zooms else None
            meta = _zoom_meta(zoom)
            if star and zoom == star:
                meta += " · recommended"
            elif star:
                meta += f" · z{star} ★ recommended"
            rows.append(ImageryRow(key=f"provider:{provider.name}", title=provider.display_name, meta=meta,
                                   price=(f"+{price:g} cr/km²" if price else "Free") if credits_billing else "",
                                   zooms=provider.zooms, zoom=zoom, recommended_zoom=star,
                                   previewable=bool(provider.preview_url)))
            if chosen:
                selected = rows[-1].key
        if self.chosen_image:
            image = self.chosen_image
            details = [f"{image.acquired.day} {image.acquired:%b %Y}" if image.acquired else "",
                       f"cloud {image.cloud:.0f}%" if image.cloud is not None else "",
                       f"z{image.zoom} from the image resolution" if image.zoom else ""]
            rows.append(ImageryRow(key="catalog", title=self._catalog_choice(image).label,
                                   meta=" · ".join(t for t in details if t) or "From search",
                                   price="In estimate" if credits_billing else "", removable=True, previewable=True))
            if choice and choice.kind == "catalog":
                selected = "catalog"
        return rows, selected

    def _cost_view(self, status: Optional[UserStatus]) -> CostView:
        estimate = self.draft.estimate()
        if not status or status.billing is BillingType.none:
            return CostView(value="", formula="")
        if status.billing is BillingType.area:
            if not self.draft.aoi:
                return CostView(value="—", balance=f"{formatting.km2(status.remaining_area_km2)} left on your plan")
            left = status.remaining_area_km2 - self.draft.aoi.area_km2
            return CostView(value=formatting.km2(self.draft.aoi.area_km2),
                            balance=f"{formatting.km2(max(left, 0))} left after this run")
        view = CostView(show_top_up=True)
        if estimate is None:
            view.balance = f"Balance: {status.remaining_credits:,} credits"
            return view
        parts = [f"{estimate.model_price:g} model"]
        if estimate.options_price:
            parts.append(f"{estimate.options_price:g} options")
        if estimate.imagery_price is not None:
            parts.append(f"{estimate.imagery_price:g} imagery")
        elif self.draft.imagery:
            parts.append("imagery")
        view.formula = f"{formatting.km2(estimate.billed_km2)} × ({' + '.join(parts)}) cr/km², rounded up"
        cost = self.server_cost if self.server_cost is not None else estimate.credits
        if cost is None:
            view.value = "…" if self.draft.imagery else "—"
        else:
            view.value = f"{'' if self.server_cost is not None else '≈ '}{cost:,} credits"
            view.balance = f"Balance after run: {status.remaining_credits - cost:,} credits"
        if self.cost_error:
            view.formula = self.cost_error
        return view

    def _maybe_request_cost(self, issues, status: Optional[UserStatus]) -> None:
        if not status or status.billing is not BillingType.credits:
            return
        blocking = [i for i in issues if i.field != "account"]
        if blocking or not self.session.project:
            return
        area = self.draft.processed_area          # for My imagery, the part inside the imagery
        key = (self.draft.model.id, tuple(sorted(self.draft.options)), area.area_km2,
               str(area.geometry)[:200], self.draft.imagery.kind,
               self.draft.imagery.provider.name if self.draft.imagery.provider else self.draft.imagery.mosaic_id,
               self.draft.imagery.zoom, tuple(self.draft.imagery.image_ids))
        if key == getattr(self, "_cost_key", None):
            return
        self._cost_key = key
        self.server_cost, self.cost_error = None, ""
        self.cost_token += 1
        self.processings.request_cost(self.draft, self.cost_token)

    @guarded
    def on_cost(self, token: int, value, error: str) -> None:
        if token != self.cost_token:
            return
        self.server_cost = value
        self.cost_error = f"Cost check: {error}" if error else ""
        self.refresh_run(keep_name=True)

    # ---------- run ----------

    @guarded
    def run(self) -> None:
        project, status = self.session.project, self.session.status
        issues = self.draft.issues(project, status, self.server_cost)
        if issues or self.starting:
            return
        self.starting = True
        self.content.run.set_issues([], busy=True)
        self.processings.start(self.draft)

    @guarded
    def on_started(self, processing: Optional[Processing]) -> None:
        self.starting = False
        # the next run gets its own name; this one's name and description went with it
        self.draft.name, self.draft.name_edited, self.draft.description = "", False, ""
        self.refresh_run()
        self.session.refresh_status()
        name = processing.name if processing else self.draft.effective_name()
        self.notify(f"“{name}” started. It's in Processings; we'll tell you when it's done.", Qgis.MessageLevel.Success)
        self.content.go(PROCESSINGS)
        if processing:
            self.content.processings.expand(processing.id)

    @guarded
    def on_start_failed(self, text: str) -> None:
        self.starting = False
        self.refresh_run(keep_name=True)
        self.content.run.issues.set("error", text)
        self.notify(f"The processing didn't start: {text}", Qgis.MessageLevel.Critical, duration=10)

    # ---------- processings ----------

    @guarded
    def on_processings(self, items) -> None:
        self.render_processings()
        running = [p for p in items if p.is_running]
        percent = int(sum(p.percent for p in running) / len(running)) if running else 0
        self.content.set_running(len(running), percent)

    def render_processings(self) -> None:
        project = self.session.project
        in_map = self.results.in_map()
        busy = {p.id for p in self.processings.items if self.results.is_busy(p.id)}
        self.content.processings.mosaic_names = {m.id: m.name for m in self.imagery.mosaics}
        self.content.processings.set_items(self.processings.items, in_map, busy,
                                           project.role.can_manage if project else False,
                                           loading=self.processings.loading, total=self.processings.total,
                                           loading_more=self.processings.loading_more)
        self.content.start.set_recent(project.name if project else "", self.processings.items, in_map)

    @guarded
    def on_finished(self, processing: Processing) -> None:
        self.session.refresh_status()
        auto = self.settings.flag("auto_load", True) and processing.id in self.processings.started_here
        if auto:
            self.results.add_to_map(processing)
            self.notify(f"“{processing.name}” is ready. Adding the results to the map…", Qgis.MessageLevel.Success)
        else:
            self.notify(f"“{processing.name}” is ready.", Qgis.MessageLevel.Success,
                        action=("Add to map", lambda: self.results.add_to_map(processing)))

    @guarded
    def on_failed(self, processing: Processing) -> None:
        self.notify(f"“{processing.name}” failed. See the reason in Processings.", Qgis.MessageLevel.Warning,
                    action=("Show", lambda: (self.content.go(PROCESSINGS),
                                             self.content.processings.expand(processing.id))))

    @guarded
    def add_to_map(self, processing_id: str) -> None:
        processing = self.processings.get(processing_id)
        if processing:
            self.results.add_to_map(processing)

    def on_results_loaded(self, processing_id: str, layer_ids) -> None:
        processing = self.processings.get(processing_id)
        name = processing.name if processing else "Results"
        where = "" if self.results.mode == "tiles" else f" Files are in {self.results.output_dir}."
        self.notify(f"“{name}” is on the map, in the Mapflow group.{where}", Qgis.MessageLevel.Success)
        self.render_processings()

    def on_results_failed(self, processing_id: str, text: str) -> None:
        self.notify(text, Qgis.MessageLevel.Warning, duration=10)
        self.render_processings()

    @guarded
    def save_geojson(self, processing_id: str) -> None:
        processing = self.processings.get(processing_id)
        if not processing:
            return
        from .qgis_bridge.layers import safe_filename
        suggested = self.results.output_dir / f"{safe_filename(processing.name)}.geojson"
        path, _ = QFileDialog.getSaveFileName(self.content, "Save results as GeoJSON", str(suggested),
                                              "GeoJSON (*.geojson)")
        if path:
            self.results.save_geojson(processing, path,
                                      lambda saved: self.notify(f"Saved to {saved}", Qgis.MessageLevel.Success))

    @guarded
    def restart(self, processing_id: str) -> None:
        processing = self.processings.get(processing_id)
        if processing:
            self.processings.restart(processing)

    @guarded
    def rename(self, processing_id: str) -> None:
        processing = self.processings.get(processing_id)
        if not processing:
            return
        dialog = RenameDialog(processing.name, processing.description or "", self.iface.mainWindow())
        if dialog.exec():
            name, description = dialog.values()
            if name and (name, description) != (processing.name, processing.description or ""):
                self.processings.rename(processing, name, description)

    @guarded
    def delete(self, processing_id: str) -> None:
        processing = self.processings.get(processing_id)
        if not processing:
            return
        answer = QMessageBox.question(self.content, "Delete processing",
                                      f"Delete “{processing.name}” and its results from Mapflow? "
                                      "Layers already in this QGIS project stay.",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                                      QMessageBox.StandardButton.Cancel)
        if answer == QMessageBox.StandardButton.Yes:
            self.processings.delete(processing)

    @guarded
    def rate(self, processing_id: str, value: int) -> None:
        processing = self.processings.get(processing_id)
        if processing:
            self.processings.rate(processing, value)
            self.notify("Thanks! Your rating helps us improve the models.", Qgis.MessageLevel.Success, duration=3)

    @guarded
    def duplicate(self, processing_id: str) -> None:
        """Run again: same model, options and imagery; the saved area comes back as a layer."""
        processing = self.processings.get(processing_id)
        project = self.session.project
        if not processing or not project:
            return
        model = project.model(processing.model_id) or next(
            (m for m in project.models if m.name == processing.model_name), None)
        self.draft.model = model
        self.draft.options = set(processing.enabled_blocks) & {b.name for b in model.options} if model else set()
        match = scenario_for_model(self.catalogue, model, list(self.draft.options)) if model else None
        self.draft.scenario_id = match.id if match else None
        source, status = processing.source, self.session.status
        if source.kind == "provider" and status:
            provider = next((p for p in status.data_providers if p.name == source.provider), None)
            if provider:
                self.provider_zoom[provider.name] = source.zoom or provider.nearest_zoom(None)
                self.draft.imagery = ImageryChoice.from_provider(provider, source.zoom)
        elif source.kind == "my_imagery" and (source.mosaic_id or source.image_ids):
            self._restore_my_imagery(source.mosaic_id, source.image_ids[0] if source.image_ids else None)
        self.draft.name, self.draft.name_edited = processing.name, True

        def with_area(collection: dict):
            layer = aoi_tools.geojson_layer(collection, f"Area · {processing.name}")
            if layer is not None:
                self.layers.add(layer)
                self.set_aoi_layer(layer)
            self.refresh_run()

        self.api.processing_aois(processing.id, with_area,
                                 lambda error: self.notify(f"The area didn't load: {error.message}",
                                                           Qgis.MessageLevel.Warning))
        self.content.open_run()
        self.refresh_run()

    def _restore_my_imagery(self, mosaic_id: Optional[str], image_id: Optional[str]) -> None:
        """My imagery of an earlier processing: a whole collection, or one image (the API keeps only the
        image id then, so its collection is looked up)."""
        if image_id:
            known = next((i for images in self.imagery.images.values() for i in images if i.id == image_id), None)
            if known is None:
                def found(image):
                    if image.mosaic_id:
                        self.imagery.images.setdefault(image.mosaic_id, [image])
                        self._restore_my_imagery(image.mosaic_id, image.id)
                self.api.mosaic_image(image_id, found, lambda _e: None)
                return
            mosaic_id = known.mosaic_id or mosaic_id
        mosaic = self.imagery.get_mosaic(mosaic_id)
        image = self.imagery.get_image(mosaic_id, image_id) if image_id else None
        self.draft.imagery = ImageryChoice.from_mosaic(mosaic_id, mosaic.name if mosaic else "My imagery",
                                                       image_id, image.filename if image else "")
        self.refresh_run()

    # ---------- imagery tab ----------

    def open_search(self) -> None:
        self.content.go(IMAGERY)
        self.content.imagery.show_tab(0)
        self.render_imagery_area()

    def render_imagery_area(self) -> None:
        page = self.content.imagery
        aoi = self.draft.aoi
        page.set_layers([(layer.id(), layer.name()) for layer in aoi_tools.polygon_layers()],
                        aoi.layer_id if aoi else None)
        if aoi:
            parts = [_count(aoi.layer_features or aoi.polygons, "polygon")]
            if aoi.selected:
                parts.append(f"{_count(aoi.selected, 'polygon')} selected")
            parts.append(formatting.km2(aoi.area_km2))
            page.set_area(" · ".join(parts), True)
        else:
            page.set_area("Choose a layer, or use the map view.", False)

    @guarded
    def clear_search(self) -> None:
        """Forget the search results and take their footprints off the map. An image already chosen
        for the run stays chosen."""
        self.imagery.results = []
        for layer in QgsProject.instance().mapLayersByName("Mapflow · search results"):
            QgsProject.instance().removeMapLayer(layer.id())
        self.footprints = None
        self.content.imagery.show_search_message("")
        self.render_search_results()

    @guarded
    def search(self, params: dict) -> None:
        if not self.draft.aoi:
            self.content.imagery.show_search_message("Set an area first.", "warn")
            return
        self.content.imagery.set_searching(True)
        self.content.imagery.show_search_message("")
        self.imagery.search(self.draft.aoi.geometry, params["date_from"], params["date_to"], params["max_cloud"],
                            params["max_off_nadir"], params["product_types"])

    @guarded
    def on_search_done(self, images, total: int) -> None:
        page = self.content.imagery
        page.set_searching(False)
        if not images:
            page.show_search_message("No images match. Widen the dates or allow more cloud cover.", "info")
        self.render_search_results()
        features = [{"type": "Feature", "geometry": i.footprint,
                     "properties": {"id": i.id, "provider": i.provider,
                                    "date": i.acquired.isoformat() if i.acquired else None, "cloud": i.cloud}}
                    for i in images if i.footprint]
        self.footprints = self.layers.footprints_layer({"type": "FeatureCollection", "features": features})
        for image in images:
            if image.preview_url and image.preview_type in ("png", "jpg", "jpeg", ""):
                self.api.preview(image.preview_url,
                                 lambda data, iid=image.id: self._set_thumb(iid, data), lambda _e: None)

    def _set_thumb(self, image_id: str, data: bytes) -> None:
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self.content.imagery.set_thumbnail(image_id, pixmap)

    def render_search_results(self) -> None:
        self.content.imagery.set_results(self.imagery.results, len(self.imagery.results),
                                         self.chosen_image.id if self.chosen_image else None)

    def on_search_failed(self, text: str) -> None:
        self.content.imagery.set_searching(False)
        self.content.imagery.show_search_message(text, "error")

    @guarded
    def show_image(self, image_id: str) -> None:
        image = self.imagery.get_result(image_id)
        layer = getattr(self, "footprints", None)
        if image is None:
            return
        if layer is not None:
            try:
                ids = [f.id() for f in layer.getFeatures() if f["id"] == image_id]
                layer.selectByIds(ids)
                if ids:
                    self.iface.mapCanvas().zoomToSelected(layer)
            except RuntimeError:
                pass
        if image.preview_url and image.preview_type in ("xyz", "tms"):
            url = image.preview_url.replace("{y}", "{-y}") if image.preview_type == "tms" else image.preview_url
            preview = self.layers.tile_raster(url, f"Preview · {_provider_name(image.provider)} {image.id[:8]}")
            if preview:
                self.layers.add(preview, position=len(self.layers.group().children()))

    @guarded
    def use_image(self, image_id: str) -> None:
        image = self.imagery.get_result(image_id)
        if image is None:
            return
        self.chosen_image = image
        self.draft.imagery = self._catalog_choice(image)
        self.render_search_results()
        self.content.open_run()
        self.refresh_run()

    @guarded
    def on_mosaics(self, mosaics) -> None:
        self._render_mosaics()

    def _render_mosaics(self) -> None:
        choice = self.draft.imagery
        self.content.imagery.set_mosaics(self.imagery.mosaics,
                                         choice.mosaic_id if choice and choice.kind == "my_imagery" else None)
        if self.mosaic_picker is not None:
            self.mosaic_picker.update_counts()
        self.refresh_run(keep_name=True)

    @guarded
    def on_mosaic_images(self, mosaic_id: str, images) -> None:
        self._mosaic_render.start()
        choice = self.draft.imagery
        if self._extent_pending and choice and choice.kind == "my_imagery" and choice.mosaic_id == mosaic_id:
            self.use_imagery_extent()
        picker = self.mosaic_picker
        if picker is not None and picker.current == mosaic_id:
            picker.set_images(mosaic_id, images)
            for image in images:
                if image.preview_s:
                    self.api.preview(image.preview_s, lambda data, iid=image.id: self._set_picker_thumb(iid, data),
                                     lambda _e: None)

    def _set_picker_thumb(self, image_id: str, data: bytes) -> None:
        pixmap = QPixmap()
        if self.mosaic_picker is not None and pixmap.loadFromData(data):
            self.mosaic_picker.set_thumbnail(image_id, pixmap)

    @guarded
    def open_mosaic_picker(self, mosaic_id: Optional[str] = None) -> None:
        """Choose a My imagery collection, or one image of it."""
        if not self.imagery.mosaics:
            self.notify("No collections in My imagery yet. Upload a GeoTIFF on the Imagery sources tab.",
                        Qgis.MessageLevel.Info)
            return
        if self.mosaic_picker is None:
            picker = MosaicPicker(self.iface.mainWindow())
            picker.collectionOpened.connect(lambda mid: self.imagery.load_images(mid))
            picker.chosen.connect(self._mosaic_chosen)
            picker.showRequested.connect(self.show_mosaic)
            self.mosaic_picker = picker
        choice = self.draft.imagery
        chosen_mosaic = choice.mosaic_id if choice and choice.kind == "my_imagery" else None
        chosen_image = choice.image_ids[0] if chosen_mosaic and choice.image_ids else None
        self.mosaic_picker.set_collections(self.imagery.mosaics, chosen_mosaic, chosen_image)
        self.mosaic_picker.open_collection(mosaic_id or chosen_mosaic or self.imagery.mosaics[0].id)
        self.mosaic_picker.show()
        self.mosaic_picker.raise_()
        self.mosaic_picker.activateWindow()

    @guarded
    def _mosaic_chosen(self, mosaic_id: str, image_id: str) -> None:
        mosaic = self.imagery.get_mosaic(mosaic_id)
        if mosaic is None:
            return
        image = self.imagery.get_image(mosaic_id, image_id) if image_id else None
        self.draft.imagery = ImageryChoice.from_mosaic(mosaic.id, mosaic.name, image.id if image else None,
                                                       image.filename if image else "")
        if self.mosaic_picker is not None:
            self.mosaic_picker.accept()
        self.content.imagery.set_mosaics(self.imagery.mosaics, mosaic.id)
        self.content.open_run()
        self.use_imagery_extent()
        self.refresh_run()

    @guarded
    def show_mosaic(self, mosaic_id: Optional[str]) -> None:
        mosaic = self.imagery.get_mosaic(mosaic_id)
        if mosaic is None:
            return

        def add(tilejson: Optional[dict]):
            layer = self.layers.tile_raster(mosaic.tile_url, f"My imagery · {mosaic.name}",
                                            bounds_extent((tilejson or {}).get("bounds")) if tilejson else None)
            if layer:
                self.layers.add(layer, position=len(self.layers.group().children()))
                self.layers.zoom_to([layer])

        if mosaic.tilejson_url:
            self.api.tilejson(mosaic.tilejson_url, add, lambda _e: add(None))
        else:
            add(None)

    @guarded
    def use_mosaic(self, mosaic_id: str) -> None:
        mosaic = self.imagery.get_mosaic(mosaic_id)
        if mosaic and (mosaic.image_count or 0) > 1:
            self.open_mosaic_picker(mosaic.id)          # several images: the whole collection, or one of them
            return
        if mosaic:
            self.draft.imagery = ImageryChoice.from_mosaic(mosaic.id, mosaic.name)
            self.content.imagery.set_mosaics(self.imagery.mosaics, mosaic.id)
            self.content.open_run()
            self.use_imagery_extent()
            self.refresh_run()

    @guarded
    def upload(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self.content, "Upload a GeoTIFF to My imagery", "",
                                              "GeoTIFF (*.tif *.tiff)")
        if not path:
            return
        size_gb = Path(path).stat().st_size / 1024 ** 3
        if size_gb > 1:
            self.content.imagery.set_upload(None, f"This file is {size_gb:.1f} GB; the limit is 1 GB. "
                                                  "Cut it into parts or upload it in Mapflow Web.", "error")
            return
        self.content.imagery.set_upload(0, "")
        self.imagery.upload(path, Path(path).stem)


def _count(value: int, noun: str) -> str:
    return f"{value:,} {noun}" + ("" if value == 1 else "s")


def _zoom_meta(zoom: Optional[int]) -> str:
    resolution = {17: "1.2 m", 18: "0.6 m", 19: "0.3 m", 20: "0.15 m", 21: "0.075 m"}.get(zoom or 0)
    return f"≈ {resolution} per pixel" if resolution else ""


def _provider_name(name: str) -> str:
    readable = (name or "Catalog").replace("_", " ").title()
    return {"my_imagery_images": "My", "my_imagery_mosaics": "My"}.get(name, readable)
