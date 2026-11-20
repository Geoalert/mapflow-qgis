"""Wires the services (state) to the dock pages (views) and to QGIS (map, layers, message bar).

The main scenario lives here: model → area → imagery → processing → results.
"""
from __future__ import annotations

import re
from pathlib import Path
import json
from typing import Dict, List, Optional, Set, Tuple

from qgis.PyQt.QtCore import QObject, QTimer, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QPixmap
from qgis.PyQt.QtWidgets import QDialog, QFileDialog, QMessageBox
from qgis.core import Qgis, QgsGeometry, QgsProject, QgsVectorLayer

from . import config
from .api.client import MapflowApi
from .core import filenames, formatting
from .core.draft import Coverage, ImageryChoice, Issue, RunDraft
from .core.failures import USER, project_gone_text
from .core.guard import guarded
from .core.models import BillingType, CatalogImage, Processing, SourceInfo, StorageLimits, UserStatus
from .core.scenarios import Catalogue, recommended_zoom, resolve, scenario_for_model
from .qgis_bridge import aoi as aoi_tools
from .qgis_bridge import message_bar
from .qgis_bridge.draw_tool import PolygonDrawTool
from .qgis_bridge.layers import MapLayers, bounds_extent
from .qgis_bridge import rasters
from .services.imagery import Imagery
from .services.processings import Processings
from .services.results import Results
from .services.session import SIGNED_IN, SIGNED_OUT, SIGNING_IN, Session
from .ui.dock import IMAGERY, PROCESSINGS, DockContent
from .ui.gallery import GalleryDialog
from .ui import imagery_page as imagery_tabs
from .ui.collection_dialog import CollectionDialog
from .ui.mosaic_picker import MosaicPicker, image_count_text
from .ui.projects_dialog import ProjectsDialog
from .ui.feedback_dialog import FeedbackDialog
from .ui.rename_dialog import RenameDialog
from .ui.run_page import CostView, ImageryRow
from .ui.settings_dialog import SettingsDialog
from .ui.start_page import plain, scenario_pixmap

VECTOR_FILTER = "Vector files (*.geojson *.json *.gpkg *.shp *.kml *.kmz *.gml);;All files (*)"


PROJECTS_WINDOW_PAGE = 24        # eight rows of three tiles
EXTENT_PROPERTY = "mapflow_next/extent_of"   # on an area layer made from My imagery: the imagery's name


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
        self._restored_image: Optional[CatalogImage] = None     # chosen_image when Run again made it (no search data)
        self.server_cost: Optional[int] = None
        self.cost_error = ""
        self.cost_token = 0
        self.starting = False
        self.draw_tool: Optional[PolygonDrawTool] = None
        self.previous_tool = None
        self.gallery: Optional[GalleryDialog] = None
        self.projects_dialog: Optional[ProjectsDialog] = None
        self.uploading: Optional[int] = None         # upload progress in %, None when nothing uploads
        self.mosaic_picker: Optional[MosaicPicker] = None
        self._projects_request = 0
        self._stopped = False                            # set by `stop`: no entry point opens a window again
        self._area_counter = 0
        self._footprints: Dict[tuple, object] = {}       # My imagery and catalog footprints (QgsGeometry), by source
        self._extent_layers: Dict[tuple, str] = {}       # extent layers made from them: source → layer id
        self._extent_pending = False                     # waiting for image footprints to make the extent
        self._use_pending: Optional[str] = None          # a collection chosen before its image list came
        self._empty_warned: Optional[str] = None         # the empty collection the message bar has named
        self._restoring = 0                              # counts Run again: a late answer for an earlier one is dropped
        self._imagery_to_choose = False                  # Run again left the imagery empty: no default fills it
        self._aoi_layer_id: Optional[str] = None         # aoi_layer's id, for when the layer is already deleted
        self._select_in_picker: Optional[str] = None     # a new collection (id or name) to select once listed
        self._choose_uploaded: Optional[str] = None      # an upload to use as the imagery once it's listed
        self._after_sign_in: Optional[Tuple[str, str]] = None   # a Layers-panel action waiting for sign-in
        self._pictures: Dict[str, bytes] = {}             # catalog picture previews, by image id
        # Tiled previews' 0/0/0 tiles, by URL: the tile, or the result keys waiting while it loads
        self._world_tiles: Dict[str, object] = {}
        self._previous_aoi: Optional[str] = None         # the area layer before the extent replaced it
        self._coverage_for = None
        self._mosaic_render = QTimer(self)        # many collections report their image counts at once
        self._mosaic_render.setSingleShot(True)
        self._mosaic_render.setInterval(150)
        self._mosaic_render.timeout.connect(self._render_mosaics)
        # Collections made in Mapflow Web show up here: asked for again now and then while the panel is open. The
        # timer runs only while signed in: sign-out ends it with the other poll timers.
        self._mosaic_refresh = QTimer(self)
        self._mosaic_refresh.setInterval(config.MOSAICS_REFRESH_MS)
        self._mosaic_refresh.timeout.connect(
            guarded(lambda: self._refresh_mosaics(config.MOSAICS_REFRESH_MS / 1000 - 1, poll=True)))
        self.content.imagery.my_data_url = session.config.my_data_url
        self._connect()

    # ---------- wiring ----------

    def _connect(self) -> None:
        c, s, p = self.content, self.session, self.processings
        s.stateChanged.connect(self.on_state)
        s.statusChanged.connect(self.on_status)
        s.projectsChanged.connect(guarded(lambda *_: c.set_project(s.project)))
        s.projectChanged.connect(self.on_project)
        s.error.connect(self.on_session_error)

        c.sign_in.browserRequested.connect(self.sign_in_browser)
        c.sign_in.cancelRequested.connect(guarded(self.session.cancel_sign_in))
        c.sign_in.tokenSubmitted.connect(self.sign_in_token)
        c.sign_in.networkSettingsRequested.connect(
            guarded(lambda: self.iface.showOptionsDialog(self.iface.mainWindow(), "mOptionsPageNetwork")))
        c.projectsRequested.connect(self.open_projects)
        c.settingsRequested.connect(self.open_settings)
        c.signOutRequested.connect(self.sign_out)
        c.tabChanged.connect(self.on_tab)

        c.start.scenarioChosen.connect(self.apply_scenario)
        c.start.galleryRequested.connect(self.open_gallery)
        c.start.customRequested.connect(self.custom_setup)
        c.start.processingsRequested.connect(guarded(lambda: c.go(PROCESSINGS)))
        c.start.processingOpened.connect(guarded(lambda pid: c.go(PROCESSINGS) or c.processings.expand(pid)))

        run = c.run
        run.backRequested.connect(guarded(c.open_start))
        run.changeScenarioRequested.connect(guarded(lambda *_: self.open_gallery("")))
        run.nameEdited.connect(self.on_name)
        run.renameRequested.connect(self.rename_draft)
        run.modelChosen.connect(self.on_model)
        run.optionToggled.connect(self.on_option)
        run.layerChosen.connect(self.on_layer)
        run.areaAction.connect(self.on_area_action)
        run.imageryChosen.connect(self.on_imagery)
        run.zoomChosen.connect(self.on_zoom)
        run.mosaicPickRequested.connect(guarded(lambda *_: self.pick_my_imagery()))
        run.catalogRemoved.connect(self.on_catalog_removed)
        run.previewRequested.connect(self.preview_imagery)
        run.searchImageryRequested.connect(self.open_search)
        run.runRequested.connect(self.run)

        page = c.processings
        page.addToMap.connect(self.add_to_map)
        page.zoomTo.connect(guarded(lambda pid: self.layers.zoom_to(self.layers.layers_for(pid))))
        page.saveGeojson.connect(self.save_geojson)
        page.restart.connect(self.restart)
        page.rename.connect(self.rename)
        page.duplicate.connect(self.duplicate)
        page.delete.connect(self.delete)
        page.openWeb.connect(self.open_in_web)
        page.rate.connect(self.rate)
        page.openWebApp.connect(guarded(lambda: QDesktopServices.openUrl(QUrl(self.session.config.web_url))))
        page.downloadAoi.connect(self.download_aoi)
        page.startRequested.connect(guarded(c.open_start))
        page.refreshRequested.connect(guarded(lambda: p.refresh_shown(USER) or page.set_refreshing(False)))
        p.refreshed.connect(guarded(lambda: page.set_refreshing(False)))
        p.rated.connect(self.on_rated)
        page.moreRequested.connect(guarded(p.load_more))
        page.searchChanged.connect(guarded(p.set_terms))

        imagery_page = c.imagery
        imagery_page.searchRequested.connect(self.search)
        imagery_page.useImage.connect(self.use_image)
        imagery_page.showImage.connect(self.show_image)
        imagery_page.useMosaic.connect(self.use_mosaic)
        imagery_page.showMosaic.connect(self.show_mosaic)
        imagery_page.moreMosaics.connect(guarded(self.imagery.load_more_mosaics))
        imagery_page.uploadRequested.connect(guarded(lambda *_: self.upload()))
        imagery_page.layerUploadRequested.connect(self.upload_layers)
        imagery_page.geotiff_layers = lambda: [(layer.id(), layer.name()) for layer in rasters.geotiff_layers()]
        imagery_page.parse_drop = rasters.dropped_geotiffs
        imagery_page.drop.dropped.connect(self.upload_dropped)
        imagery_page.tabs.changed.connect(guarded(lambda index: index == imagery_tabs.MINE and self._refresh_mosaics()))
        imagery_page.areaAction.connect(self.on_area_action)
        imagery_page.layerChosen.connect(self.on_layer)
        imagery_page.clearRequested.connect(self.clear_search)
        imagery_page.moreResults.connect(self.more_results)

        p.changed.connect(self.on_processings)
        p.foundChanged.connect(guarded(lambda *_: self.render_processings()))
        p.started.connect(self.on_started)
        p.startFailed.connect(self.on_start_failed)
        p.finished.connect(self.on_finished)
        p.failed.connect(self.on_failed)
        p.costReady.connect(self.on_cost)
        p.actionFailed.connect(guarded(lambda text: self.notify(text, Qgis.MessageLevel.Warning)))
        p.listFailed.connect(guarded(lambda text: self.notify(text, Qgis.MessageLevel.Warning)))
        p.projectGone.connect(self.on_project_gone)

        self.imagery.searchDone.connect(self.on_search_done)
        self.imagery.moreDone.connect(self.on_more_results)
        self.imagery.searchFailed.connect(self.on_search_failed)
        self.imagery.mosaicsChanged.connect(self.on_mosaics)
        self.imagery.mosaicsFailed.connect(self.on_mosaics_failed)
        self.imagery.imagesFailed.connect(self.on_images_failed)
        self.imagery.limitsChanged.connect(guarded(self._show_upload_limit))
        self.imagery.limitsFailed.connect(self.on_limits_failed)
        self.imagery.notice.connect(guarded(lambda text: self.notify(text, Qgis.MessageLevel.Warning)))
        self.imagery.mosaicSearchChanged.connect(
            guarded(lambda query, found: self.mosaic_picker is not None and self.mosaic_picker.set_found(
                query, found, self.imagery.found_total, self.imagery.found_loading,
                failed=self.imagery.found_failed)))
        self.imagery.mosaicImagesChanged.connect(self.on_mosaic_images)
        self.imagery.uploadProgress.connect(self._upload_progress)
        self.imagery.on_duplicate = lambda file, collection: self._ask_duplicate([file], collection)
        self.imagery.uploadDone.connect(guarded(lambda name: (
            self._upload_progress(None),
            c.imagery.set_upload(None, f"“{name}” is uploaded and ready to use.", "info"),
            self.mosaic_picker and self.mosaic_picker.set_upload(None, f"Uploaded to “{name}”.", "info"),
            self.notify(f"“{name}” is uploaded to My imagery.", Qgis.MessageLevel.Success))))
        self.imagery.uploadFailed.connect(guarded(lambda text: (
            setattr(self, "_choose_uploaded", None),
            self._upload_progress(None), c.imagery.set_upload(None, text, "error"),
            self.mosaic_picker and self.mosaic_picker.set_upload(None, text, "error"),
            self.notify(text, Qgis.MessageLevel.Warning))))

        self.results.loaded.connect(self.on_results_loaded)
        self.results.failed.connect(self.on_results_failed)
        self.results.busy.connect(guarded(lambda *_: self.render_processings()))

        project = QgsProject.instance()
        project.layersAdded.connect(self.on_layers_changed)
        project.layersRemoved.connect(self.on_layers_removed)

    def stop(self) -> None:
        """Unload: stop the timers, abort the request of the Projects window, let go of QGIS's project signals, end
        drawing, and close and delete the scenario gallery, the Projects window and the My imagery window, which
        are children of the main window and outlive the dock. Emits nothing."""
        self._stopped = True
        self._mosaic_render.stop()
        self._mosaic_refresh.stop()
        if self._projects_request:
            self.api.abort(self._projects_request)
            self._projects_request = 0
        project = QgsProject.instance()
        for signal, slot in ((project.layersAdded, self.on_layers_changed),
                             (project.layersRemoved, self.on_layers_removed)):
            try:
                signal.disconnect(slot)
            except TypeError:
                pass
        self._watch_layer(None)
        self.stop_drawing()
        for name in ("gallery", "projects_dialog", "mosaic_picker"):
            window = getattr(self, name)
            setattr(self, name, None)               # a late callback finds no window
            if window is not None:
                window.close()
                window.deleteLater()                # it goes on the next turn of the event loop
                self._stop_timers(window)
        self._stop_timers(self.content)             # the dock goes the same way, its timers too

    @staticmethod
    def _stop_timers(widget) -> None:
        for timer in widget.findChildren(QTimer):
            timer.stop()

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
            self._mosaic_refresh.stop()
            self.processings.stop()
            self.processings.set_project(None)
            # Sign-out aborts requests in flight, and aborted requests report nothing back
            self.results.reset()
            self.content.imagery.set_searching(False)
            self.content.imagery.set_upload(None)
            self.uploading = None
            # …nor do a start or an upload in flight: their busy flags would stay up after signing back in
            self.starting = False
            self.imagery.reset_busy()
            self.imagery.forget_mosaics()
            self._choose_uploaded = self._use_pending = None
            self._extent_pending = False
            self._restoring += 1
            for dialog in (self.projects_dialog, self.mosaic_picker):
                if dialog is not None:
                    dialog.close()
            self.content.show_signed_out()
        elif state == SIGNED_IN:
            sign_in.set_busy(False)
            sign_in.clear()
            if not self._mosaic_refresh.isActive():
                self._mosaic_refresh.start()
            self.content.set_account(self.session.email)
            self.content.set_project(self.session.project)
            self.content.show_signed_in()
            self.imagery.load_mosaics()
            pending, self._after_sign_in = self._after_sign_in, None
            if pending:
                {"aoi": self.use_layer_as_aoi, "imagery": self.use_layer_as_imagery}[pending[0]](pending[1])

    @guarded
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
            if not self._imagery_to_choose:             # after "Run again" the user chooses: no default fills it in
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
        changed = not (self.processings.project and self.processings.project.id == project.id)
        self.processings.set_project(project)
        if changed:
            self.content.processings.clear_search()         # the new project starts with the full list
        if self.draft.model and not project.model(self.draft.model.id):
            self.draft.model, self.draft.options = None, set()
        if self.draft.scenario_id and not self.draft.model:
            scenario = self.catalogue.get(self.draft.scenario_id)
            if scenario:
                resolution = resolve(scenario, project.models)
                self.draft.model, self.draft.options = resolution.model, set(resolution.options)
        self.content.processings.can_manage = project.role.can_manage
        self.content.processings.can_run = project.role.can_run
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
        if self._stopped:
            return
        if self.projects_dialog is None:
            dialog = ProjectsDialog(self.iface.mainWindow())
            dialog.queryChanged.connect(self._query_projects)
            dialog.moreRequested.connect(self._more_projects)
            dialog.projectChosen.connect(self._choose_project)
            dialog.pinToggled.connect(self._pin_project)
            dialog.shareRequested.connect(self._share_project)
            dialog.createRequested.connect(self.create_project)
            dialog.renameRequested.connect(self.rename_project)
            self.projects_dialog = dialog
        dialog = self.projects_dialog
        dialog.search.blockSignals(True)
        dialog.search.clear()
        dialog.search.blockSignals(False)
        dialog.query = ""
        dialog.set_state(self.session.project.id if self.session.project else None, self.pinned_projects())
        self._query_projects("")
        told = []                       # the pins and the starred list fail together: one line

        def pins_failed(error) -> None:
            if not told and error.kind != "auth":
                told.append(True)
                self.notify(f"Pinned projects didn't load: {error.message}", Qgis.MessageLevel.Warning)

        for project_id in self.pinned_projects():
            self.api.project(project_id, self.session.email, self._pinned_loaded, pins_failed)
        self.api.starred_projects(self.session.email, self._starred_loaded, pins_failed)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _pinned_loaded(self, project) -> None:
        if project.starred is False:                  # unpinned in Mapflow Web since
            self._set_pins([i for i in self.pinned_projects() if i != project.id])
            return
        if self.projects_dialog is not None:
            self.projects_dialog.set_pinned_project(project)

    def _starred_loaded(self, projects) -> None:
        """Pins follow the account: what is starred in Mapflow Web is pinned here, and the other way round."""
        ids = [p.id for p in projects]
        self._set_pins(ids)
        if self.projects_dialog is not None:
            for project in projects:
                self.projects_dialog.set_pinned_project(project)

    def _set_pins(self, ids: List[str]) -> None:
        self.settings.setValue(self._pinned_key(), json.dumps(ids))
        dialog = self.projects_dialog
        if dialog is not None:
            for project_id in list(dialog.pinned):
                if project_id not in ids:
                    dialog.pinned.pop(project_id, None)
            dialog.set_state(dialog.current_id, ids)

    @guarded
    def _query_projects(self, query: str, offset: int = 0) -> None:
        dialog = self.projects_dialog
        if dialog is None:
            return
        dialog.query = query
        if self._projects_request:
            self.api.abort(self._projects_request)
        dialog.set_loading(True)

        def done(projects, total, q=query, append=offset > 0):
            self._projects_request = 0
            pins = self.pinned_projects()
            synced = [i for i in pins if not any(p.id == i and p.starred is False for p in projects)]
            synced += [p.id for p in projects if p.starred and p.id not in synced]
            if synced != pins:                        # starred or unstarred in Mapflow Web
                self._set_pins(synced)
            if self.projects_dialog is not None and self.projects_dialog.query == q:
                self.projects_dialog.set_results(projects, total, append=append)

        def failed(error):
            self._projects_request = 0
            if self.projects_dialog is not None:
                self.projects_dialog.set_failed(error.message)
            self.notify(f"Projects didn't load: {error.message}", Qgis.MessageLevel.Warning)

        self._projects_request = self.api.projects_page(self.session.email, done, failed, query=query, offset=offset,
                                                        limit=PROJECTS_WINDOW_PAGE)

    @guarded
    def _more_projects(self) -> None:
        dialog = self.projects_dialog
        if dialog is not None:
            self._query_projects(dialog.query, offset=len(dialog.results))

    @guarded
    def _share_project(self, project_id: str) -> None:
        """Sharing and roles are managed in Mapflow Web: open the project there."""
        web = self.session.config.web_url
        QDesktopServices.openUrl(QUrl(f"{web}/projects/{project_id}" if project_id else config.PROJECTS_URL))

    @guarded
    def create_project(self) -> None:
        """A new project, made current at once: the next processing runs in it."""
        dialog = RenameDialog("", "", self.projects_dialog or self.iface.mainWindow(), title="New project",
                              action="Create", what="project")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        name, description = dialog.values()

        def created(project):
            if not project.id:
                self.notify("Mapflow didn't create the project. Try again.", Qgis.MessageLevel.Warning)
                return
            self.notify(f"Project “{project.name}” is created and open.", Qgis.MessageLevel.Success)
            if self.projects_dialog is not None:
                self.projects_dialog.accept()
            self.session.select_project(project.id, fallback=project)      # with its models, as listed

        self.api.create_project(name, description, self.session.email, created,
                                lambda error: self.notify(f"The project wasn't created: {error.message}",
                                                          Qgis.MessageLevel.Warning))

    def _known_project(self, project_id: str):
        """The project with this id, as the projects window or the session holds it."""
        dialog = self.projects_dialog
        held = [*(dialog.results if dialog else []), *(dialog.pinned.values() if dialog else []), self.session.project]
        return next((p for p in held if p is not None and p.id == project_id), None)

    @guarded
    def rename_project(self, project_id: str) -> None:
        """The name and description of a project, saved with PUT /projects/{id}. The list is not asked again:
        the tiles and the dock header take the new values, so the order and a name filter apply at the next
        query."""
        project = self._known_project(project_id)
        if project is None or not project.can_edit:         # the role changed under a menu that was already open
            return
        dialog = RenameDialog(project.name, project.description, self.projects_dialog or self.iface.mainWindow(),
                              title="Rename project", action="Save", what="project")
        if not dialog.exec():
            return
        name, description = dialog.values()
        old = project.name
        if not name or (name, description) == (old, project.description):
            return

        def done(old_name: str) -> None:
            if self.projects_dialog is not None:
                self.projects_dialog.project_renamed(project_id, name, description)
            if self.session.project is not None and self.session.project.id == project_id:
                self.content.set_project(self.session.project)
                self.render_processings()                   # the Start tab names the project too
            self.notify(f"Project “{old_name}” is renamed to “{name}”.", Qgis.MessageLevel.Success)

        def failed(message: str) -> None:
            text = f"Couldn't rename “{old}”: {message}"
            self.notify(text, Qgis.MessageLevel.Warning)
            if self.projects_dialog is not None:
                self.projects_dialog.set_note("warn", text)

        self.session.rename_project(project_id, name, description, done, failed)

    @guarded
    def _choose_project(self, project_id: str) -> None:
        if self.projects_dialog is not None:
            self.projects_dialog.accept()
        if not self.session.project or project_id != self.session.project.id:
            self.session.select_project(project_id)

    @guarded
    def _pin_project(self, project_id: str, pinned: bool) -> None:
        """Pin at once, then star it in Mapflow, so Mapflow Web shows it starred. If Mapflow refuses, the
        pin stays on this computer only."""
        ids = [i for i in self.pinned_projects() if i != project_id]
        if pinned:
            ids.insert(0, project_id)
        dialog = self.projects_dialog
        if dialog is not None:
            known = next((p for p in dialog.results if p.id == project_id), None)
            if pinned and known is not None:
                dialog.pinned[project_id] = known
        self._set_pins(ids)

        def failed(error) -> None:
            self.notify(f"{'Pinned' if pinned else 'Unpinned'} on this computer only: Mapflow didn't save it "
                        f"({error.message}).", Qgis.MessageLevel.Warning)

        self.api.star_project(project_id, pinned, lambda _answer: None, failed)

    def _refresh_mosaics(self, max_age: float = 5.0, poll: bool = False) -> None:
        """`poll`: the timer asks (its failures are counted); a tab or a picker opening is a one-off load."""
        if self.session.state == "signed_in" and self.content.isVisible():
            self.imagery.refresh_mosaics(max_age, poll)
            if not poll:
                self.imagery.refresh_limits(max_age)

    @guarded
    def on_tab(self, tab: int) -> None:
        if tab == IMAGERY:
            self.render_imagery_area()
            if self.content.imagery.current_tab() == imagery_tabs.MINE:
                self._refresh_mosaics()
        if tab == PROCESSINGS:
            self.processings.refresh_shown(USER)    # the user opened the tab and waits for the list

    # ---------- scenarios ----------

    @guarded
    def apply_scenario(self, scenario_id: str) -> None:
        scenario = self.catalogue.get(scenario_id)
        if scenario is None:
            return
        self._imagery_to_choose = False
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
        if self._stopped:
            return
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
            # A tool, not an option: QGIS's Select Features tool on the polygon layer, and the area follows
            # the selection (all of the layer's polygons while none is selected)
            layer = self.iface.activeLayer()
            if not aoi_tools.is_polygon_layer(layer):
                layer = self.aoi_layer if aoi_tools.is_polygon_layer(self.aoi_layer) else None
            if layer is None:
                self.notify("Choose a polygon layer in Area (or make one active in the Layers panel), then "
                            "select its polygons on the map.", Qgis.MessageLevel.Info)
                return
            self.iface.setActiveLayer(layer)
            select = getattr(self.iface, "actionSelect", None)
            if callable(select):
                select().trigger()
            self.set_aoi_layer(layer, selected_only=True)
            if not layer.selectedFeatureCount():
                self.notify(f"Click polygons of “{layer.name()}” on the map to select them (Shift adds more). "
                            "The area follows the selection.", Qgis.MessageLevel.Info, duration=8)
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
        self.content.imagery.set_drawing(True)
        self.notify("Click the corners of your area. Double-click or right-click to finish, Esc to cancel.",
                    Qgis.MessageLevel.Info, duration=8)

    @guarded
    def stop_drawing(self) -> None:
        canvas = self.iface.mapCanvas() if self.iface else None
        if canvas and self.draw_tool and canvas.mapTool() is self.draw_tool:
            canvas.unsetMapTool(self.draw_tool)
            if self.previous_tool:
                canvas.setMapTool(self.previous_tool)
        self.content.run.set_drawing(False)
        self.content.imagery.set_drawing(False)

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
        self.render_imagery_area()                  # drawn from the catalog search too
        self.render_imagery_area()

    def set_aoi_layer(self, layer: Optional[QgsVectorLayer], selected_only: bool = True) -> None:
        self._watch_layer(layer)
        self.aoi_selected_only = selected_only
        self.recompute_aoi()

    def _watch_layer(self, layer: Optional[QgsVectorLayer]) -> None:
        if self.aoi_layer is not None:
            try:
                signals = (self.aoi_layer.selectionChanged, self.aoi_layer.editingStopped,
                           self.aoi_layer.featuresDeleted, self.aoi_layer.featureAdded)
            except RuntimeError:                        # removed from the project and deleted
                signals = ()
            for signal in signals:
                try:
                    signal.disconnect(self._layer_changed)
                except (TypeError, RuntimeError):
                    pass
        self.aoi_layer = layer
        self._aoi_layer_id = layer.id() if layer is not None else None
        if layer is not None:
            for signal in (layer.selectionChanged, layer.editingStopped, layer.featuresDeleted, layer.featureAdded):
                signal.connect(self._layer_changed)

    @guarded
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
        self.content.imagery.set_previewing(self._search_previewing())

    @guarded
    def on_layers_removed(self, layer_ids) -> None:
        # Compared by the id kept when the layer was chosen: by now the layer object itself is deleted, and an
        # empty layer gives the form no area (draft.aoi) to compare with
        if self._aoi_layer_id is not None and self._aoi_layer_id in layer_ids:
            self.aoi_layer = None
            self._aoi_layer_id = None
            self.draft.aoi = None
        self.refresh_run()
        self.render_processings()
        self.content.imagery.set_previewing(self._search_previewing())

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
        elif key == "mosaic" and not self.imagery.mosaics:
            self.pick_my_imagery()                      # nothing to pick yet: to the My imagery tab
            return
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
        """(name, footprint, key) of the chosen imagery that has a footprint. My imagery: one image's extent,
        or the collection's (the union of its images once they are loaded). A catalog image: its footprint
        from the search. None for basemaps, and while the footprint isn't known."""
        choice = self.draft.imagery
        if choice and choice.kind == "catalog":
            return self._catalog_footprint(choice)
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

    def _catalog_footprint(self, choice):
        """(name, footprint, key) of the chosen catalog image, from its search result. None when the image has
        no footprint (one Run again restored, which isn't among the results)."""
        image = self.chosen_image
        if image is None or not choice.image_ids or image.id != choice.image_ids[0] or not image.footprint:
            return None
        key = ("catalog", image.key)
        geometry = self._footprints.get(key)
        if geometry is None:
            geometry = aoi_tools.catalog_footprint(image.footprint)
            if geometry is None:
                return None
            self._footprints[key] = geometry
        return choice.label, geometry, key

    def _update_coverage(self) -> None:
        """For imagery that has a footprint: does the area overlap it, and which part of it is inside."""
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
            return ("info", f"The area is the whole extent of “{name}”.\nTo process only part of it, draw a "
                            "smaller area or edit the outline.", tuple(actions))
        if coverage and coverage.clipped and self.draft.aoi \
                and coverage.clipped.area_km2 < self.draft.aoi.area_km2 * 0.999:
            return "info", f"Only the part of the area inside “{coverage.name}” is processed and billed.", ()
        return "info", "", ()

    def use_imagery_extent(self) -> None:
        """Make the chosen imagery's extent the area (My imagery, or a catalog image): a layer the user can
        edit or replace."""
        choice = self.draft.imagery
        found = self._imagery_footprint()
        if found is None:
            # Its footprint comes with the image list. A loaded list without footprints won't get one by
            # asking again: answering from the cache would call back here, round and round.
            if choice and choice.kind == "my_imagery" and choice.mosaic_id \
                    and choice.mosaic_id not in self.imagery.images:
                self._extent_pending = True
                self.imagery.load_images(choice.mosaic_id, waiting=True)
            else:
                if self._extent_pending or choice is not None:
                    self.notify("Mapflow has no outline for this imagery yet, so its extent can't be the area. "
                                "Choose the area another way.", Qgis.MessageLevel.Info)
                self._extent_pending = False
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

    def _preview_key(self, choice: Optional[ImageryChoice]) -> Optional[str]:
        """Which preview layer shows the chosen imagery; None if it has none (a catalog image without a
        preview: the eye zooms to its footprint)."""
        if choice is None:
            return None
        if choice.kind == "provider" and choice.provider and choice.provider.preview_url:
            return f"provider:{choice.provider.name}"
        if choice.kind == "my_imagery" and choice.mosaic_id:
            return f"mosaic:{choice.mosaic_id}"
        image = self.chosen_image
        if choice.kind == "catalog" and image and (image.parts or image.preview_url and (
                image.preview_type in ("xyz", "tms") or self._picture_preview(image))):
            return f"catalog:{image.key}"
        return None

    @guarded
    def preview_imagery(self) -> None:
        """The eye: put the chosen imagery's preview on the map, or take it off if it is there."""
        choice = self.draft.imagery
        if choice is None:
            return
        shown = self.layers.previews(self._preview_key(choice))
        if shown:
            self.layers.remove(shown)               # the form follows through layersRemoved
            return
        if choice.kind == "provider" and choice.provider and choice.provider.preview_url:
            layer = self.layers.tile_raster(choice.provider.preview_url, f"{choice.provider.display_name} · preview",
                                            zmax=choice.provider.preview_max_zoom or 18)
            if layer:
                self.layers.add(layer, position=len(self.layers.group().children()),
                                preview=self._preview_key(choice))
                self.notify(f"{choice.provider.display_name} preview is on the map, "
                            "at the bottom of the Mapflow group.")
        elif choice.kind == "my_imagery":
            self.show_mosaic(choice.mosaic_id)
        elif choice.kind == "catalog" and self.chosen_image:
            self.show_image(self.chosen_image.key)

    def _preview_my_imagery(self) -> None:
        """Choosing My imagery puts it on the map, so the area can be judged against the imagery."""
        choice = self.draft.imagery
        if choice and choice.kind == "my_imagery" and not self.layers.previews(self._preview_key(choice)):
            self.show_mosaic(choice.mosaic_id, zoom=False)      # the area's extent is zoomed to already

    def _catalog_choice(self, image: CatalogImage) -> ImageryChoice:
        when = f"{image.acquired.day} {image.acquired:%b %Y}" if image.acquired else ""
        title = f"{_provider_name(image.provider)} {'mosaic' if image.is_mosaic else 'scene'}"
        return ImageryChoice.from_catalog(image.id, image.provider, image.zoom, f"{title} {when}".strip(),
                                          image.min_area_km2)

    def _restored_catalog_image(self, source: SourceInfo) -> CatalogImage:
        """The image of a processing, for Run again. A search result of the same image (and zoom) knows more than
        the processing does; without one the image has only what the processing keeps: id, provider and zoom."""
        image_id = source.image_ids[0]
        found = next((i for i in self.imagery.results
                      if i.id == image_id and (source.zoom is None or i.zoom == source.zoom)), None)
        self._restored_image = None if found else CatalogImage(id=image_id, provider=source.provider,
                                                               zoom=source.zoom)
        return found or self._restored_image

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
        base = formatting.per_km2(self.draft.model.base_price) if (self.draft.model and credits_billing) else ""
        note = ""
        if scenario and not self.draft.model and scenario.apply.get("model"):
            note = f"This project has no “{plain(scenario.model_label)}” model. Pick another one."
        model = self.draft.model
        descriptions = status.option_descriptions if status else {}
        run.set_options(model, self.draft.options, base, note,
                        (descriptions.get(model.id) or descriptions.get(model.name) or {}) if model else {})

        layers = [(layer.id(), layer.name()) for layer in aoi_tools.polygon_layers()]
        run.set_layers(layers, self.draft.aoi.layer_id if self.draft.aoi else None)
        self._update_coverage()
        issues = self._issues(project, status)
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

    def _issues(self, project, status) -> List[Issue]:
        issues = self.draft.issues(project, status, self.server_cost)
        choice = self.draft.imagery
        mosaic = self.imagery.get_mosaic(choice.mosaic_id) if choice and choice.kind == "my_imagery" else None
        if mosaic is not None and not choice.image_ids and self._empty_collection(mosaic):
            issues.append(Issue("imagery", f"“{mosaic.name}” has no images, so it can't be processed. Add images "
                                           "to it in Mapflow Web, or choose other imagery."))
            # chosen without the picker (a scenario's default, Run again, images deleted in Mapflow Web):
            # the form's issue is easy to miss, so say it once in the message bar too
            if self._empty_warned != mosaic.id:
                self._empty_warned = mosaic.id
                self._refuse_empty(mosaic)
        else:
            self._empty_warned = None
        return issues

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
                                   price="Free" if credits_billing else "", previewable=True,
                                   previewing=self._previewing(choice) if mine else None))
            if mine:
                selected = "mosaic"
        else:
            # No collections yet: the row still shows, so the upload is found where imagery is chosen
            uploading = self.uploading is not None
            meta = f"Uploading… {self.uploading}%" if uploading else "Upload a GeoTIFF to process your own imagery"
            rows.append(ImageryRow(key="mosaic", title="My imagery", meta=meta,
                                   pick="" if uploading else "Add imagery…",
                                   price="Free" if credits_billing else ""))
        for provider in (status.data_providers if status else []):
            chosen = bool(choice and choice.kind == "provider" and choice.provider.name == provider.name)
            zoom = choice.zoom if chosen else provider.nearest_zoom(self.provider_zoom.get(provider.name, recommended))
            price = provider.price_at(zoom)
            star = recommended if recommended in provider.zooms else None
            meta = _zoom_meta(zoom)
            if star and zoom == star:
                meta += " · recommended"
            note = f"z{star} recommended" if star and zoom != star else ""
            rows.append(ImageryRow(key=f"provider:{provider.name}", title=provider.display_name, meta=meta, note=note,
                                   price=(f"+{formatting.per_km2(price)}" if price else "Free")
                                   if credits_billing else "",
                                   zooms=provider.zooms, zoom=zoom, recommended_zoom=star,
                                   previewable=bool(provider.preview_url),
                                   previewing=self._previewing(choice) if chosen else None))
            if chosen:
                selected = rows[-1].key
        if self.chosen_image:
            image = self.chosen_image
            details = [f"{image.acquired.day} {image.acquired:%b %Y}" if image.acquired else "",
                       f"cloud {image.cloud:.0f}%" if image.cloud is not None else "",
                       (f"z{image.zoom} · of that processing" if image is self._restored_image
                        else f"z{image.zoom} from the image resolution") if image.zoom else ""]
            rows.append(ImageryRow(key="catalog", title=self._catalog_choice(image).label,
                                   meta=" · ".join(t for t in details if t) or "From search",
                                   price="In estimate" if credits_billing else "", removable=True,
                                   previewable=self.imagery.get_result(image.key) is not None,
                                   previewing=self._previewing(choice) if choice and choice.kind == "catalog"
                                   else None))
            if choice and choice.kind == "catalog":
                selected = "catalog"
        return rows, selected

    def _previewing(self, choice: Optional[ImageryChoice]) -> Optional[bool]:
        """Whether the eye shows the chosen imagery's preview as on the map (None: no preview layer)."""
        key = self._preview_key(choice)
        return bool(self.layers.previews(key)) if key else None

    def _cost_view(self, status: Optional[UserStatus]) -> CostView:
        estimate = self.draft.estimate()
        if not status or status.billing is BillingType.none:
            return CostView(value="", formula="")
        if status.billing is BillingType.area:
            if not self.draft.aoi:
                return CostView(value="—", balance=f"{formatting.km2(status.remaining_area_km2)} left on your plan")
            area = self.draft.processed_area.area_km2      # for My imagery, the part inside the imagery
            left = status.remaining_area_km2 - area
            return CostView(value=formatting.km2(area), balance=f"{formatting.km2(max(left, 0))} left after this run")
        view = CostView(show_top_up=True)
        if estimate is None:
            view.balance = f"Balance: {status.remaining_credits:,} credits"
            return view
        parts = [f"{formatting.rate(estimate.model_price)} model"]
        if estimate.options_price:
            parts.append(f"{formatting.rate(estimate.options_price)} options")
        if estimate.imagery_price is not None:
            parts.append(f"{formatting.rate(estimate.imagery_price)} imagery")
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
        self.cost_error = self._cost_error_text(error) if error else ""
        self.refresh_run(keep_name=True)

    def _cost_error_text(self, error: str) -> str:
        """Mapflow's answer when the chosen imagery is gone (a deleted collection, a catalog image no longer
        sold, a source taken off the plan) is a raw 404 from its data catalog: said here in words instead."""
        lowered = error.lower()
        if "not found" not in lowered and "404" not in lowered and "notfound" not in lowered:
            return f"Cost check: {error}"
        kind = self.draft.imagery.kind if self.draft.imagery else ""
        return {"my_imagery": "This My imagery collection or image is no longer there. Choose the imagery again.",
                "catalog": "This catalog image is no longer available. Search the catalog and choose another.",
                "provider": "This imagery source is no longer available to you. Choose another one."
                }.get(kind, "The chosen imagery is no longer available. Choose the imagery again.")

    # ---------- run ----------

    @guarded
    def run(self) -> None:
        project, status = self.session.project, self.session.status
        issues = self._issues(project, status)
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
        p = self.processings
        searching = bool(p.terms)
        known = [*p.items, *p.found, *([p.opened] if p.opened else [])]
        busy = {x.id for x in known if self.results.is_busy(x.id)}
        self.content.processings.mosaic_names = self.imagery.mosaic_names()
        self.content.processings.ratings = {**{x.id: x.rating for x in known if x.rating}, **self._ratings()}
        # The page shows the matches while a search is on. Everything else (the Start tab, the notices) reads the
        # full listing, which stays loaded.
        shown = (p.found, p.found_total, p.found_loading, p.found_loading_more, p.found_loaded,
                 p.found_failed) if searching else (p.items, p.total, p.loading, p.loading_more, p.loaded,
                                                    p.load_failed)
        self.content.processings.set_items(shown[0], in_map, busy, project.role.can_manage if project else False,
                                           loading=shown[2], total=shown[1], loading_more=shown[3],
                                           loaded=shown[4], failed=shown[5],
                                           can_run=project.role.can_run if project else False,
                                           terms=p.terms, opened=None if searching else p.opened)
        self.content.start.set_recent(project.name if project else "", p.items, in_map)

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
                    action=("Show", lambda: self.open_processing(processing.id)))

    @guarded
    def open_processing(self, processing_id: str) -> None:
        """"Show" in a notice: the processing's card, fetched by id when it is not on the loaded pages."""
        self.content.go(PROCESSINGS)
        fetching = self.processings.open(processing_id)
        self.content.processings.expand(processing_id, fetching=fetching)    # this clears the search field

    @guarded
    def add_to_map(self, processing_id: str) -> None:
        processing = self.processings.get(processing_id)
        if processing:
            self.results.add_to_map(processing)

    @guarded
    def on_results_loaded(self, processing_id: str, layer_ids) -> None:
        processing = self.processings.get(processing_id)
        name = processing.name if processing else "Results"
        where = "" if self.results.mode == "tiles" else f" Files are in {self.results.output_dir}."
        self.notify(f"“{name}” is on the map, in the Mapflow group.{where}", Qgis.MessageLevel.Success)
        self.render_processings()

    @guarded
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
        project, processing = self.session.project, self.processings.get(processing_id)
        # The button is hidden otherwise: this stops a stale signal, or a status that changed since the last render
        if project and project.role.can_run and processing and processing.status.can_restart:
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
        """A star was clicked: nothing is sent until the feedback form is."""
        processing = self.processings.get(processing_id)
        if not processing:
            return
        dialog = FeedbackDialog(processing.name, value, self.content)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            rating, comment = dialog.values()
            self.processings.rate(processing, rating, comment)
        else:
            self.render_processings()           # the stars go back to what was sent before

    @guarded
    def on_rated(self, processing_id: str, rating: int) -> None:
        ratings = self._ratings()
        ratings[processing_id] = rating
        self.settings.setValue("ratings", json.dumps(dict(list(ratings.items())[-500:])))
        self.render_processings()
        self.notify("Thanks! Your feedback helps us improve the models.", Qgis.MessageLevel.Success, duration=3)

    def _ratings(self) -> Dict[str, int]:
        """Ratings sent from this computer: Mapflow keeps them but doesn't send them back with the list."""
        try:
            stored = json.loads(self.settings.value("ratings", "{}") or "{}")
        except (TypeError, ValueError):
            stored = {}
        return {str(k): int(v) for k, v in stored.items() if str(v).isdigit()} if isinstance(stored, dict) else {}

    @guarded
    def open_in_web(self, processing_id: str) -> None:
        processing = self.processings.get(processing_id)
        project = processing.project_id if processing and processing.project_id else (
            self.session.project.id if self.session.project else "")
        url = (f"{self.session.config.web_url}/projects/{project}?processing={processing_id}" if project
               else self.session.config.web_url)
        QDesktopServices.openUrl(QUrl(url))

    @guarded
    def download_aoi(self, processing_id: str) -> None:
        """The processing's area from Mapflow, saved as GeoJSON and added to the map."""
        processing = self.processings.get(processing_id)
        if not processing:
            return
        folder = self.results.output_dir
        safe = "".join(ch if ch.isalnum() or ch in " -_." else "_" for ch in processing.name).strip() or "area"
        path, _ = QFileDialog.getSaveFileName(self.content, "Download the processing's area",
                                              str(Path(folder) / f"{safe} · area.geojson"), "GeoJSON (*.geojson)")
        if not path:
            return

        def save(collection: dict) -> None:
            if not collection.get("features"):
                self.notify("Mapflow sent no area for this processing.", Qgis.MessageLevel.Warning)
                return
            for feature in collection["features"]:
                feature.setdefault("properties", {})["processing"] = processing.name
            Path(path).write_text(json.dumps(collection), encoding="utf-8")
            layer = QgsVectorLayer(path, f"Area · {processing.name}", "ogr")
            if layer.isValid():
                layer.loadNamedStyle(str(config.RESOURCES / "styles" / "aoi.qml"))
                self.layers.add(layer)
                self.layers.zoom_to([layer])
            self.notify(f"The area is saved to {path} and added to the map.", Qgis.MessageLevel.Success)

        self.api.processing_aois(processing.id, save,
                                 lambda error: self.notify(f"The area didn't download: {error.message}",
                                                           Qgis.MessageLevel.Warning))

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
        # What can't be set again, said once, in words: the form shows each step it left empty
        gone: List[str] = []
        if model is None:
            gone.append(f"the model “{plain(processing.model_name) or 'of that run'}” is no longer in this project")
        else:
            dropped = sorted(set(processing.enabled_blocks) - {b.name for b in model.blocks})
            if dropped:
                gone.append(f"{'option' if len(dropped) == 1 else 'options'} {', '.join(dropped)} "
                            f"{'is' if len(dropped) == 1 else 'are'} no longer available, so the run goes without")
        match = scenario_for_model(self.catalogue, model, list(self.draft.options)) if model else None
        self.draft.scenario_id = match.id if match else None
        # The imagery and the area of the form before are never kept: a run on them would be paid for and
        # wrong. Whatever can't be restored stays empty until the user chooses it.
        self._restoring += 1
        restoring = self._restoring
        self.draft.imagery = None
        source, status = processing.source, self.session.status
        if source.kind == "provider" and status:
            provider = next((p for p in status.data_providers if p.name == source.provider), None)
            if provider:
                self.provider_zoom[provider.name] = source.zoom or provider.nearest_zoom(None)
                self.draft.imagery = ImageryChoice.from_provider(provider, source.zoom)
            else:
                gone.append(f"the imagery source “{_provider_name(source.provider) or 'of that run'}” is no "
                            "longer available to you")
        elif source.kind == "my_imagery" and (source.mosaic_id or source.image_ids):
            self._restore_my_imagery(source.mosaic_id, source.image_ids[0] if source.image_ids else None,
                                     restoring)
        elif source.kind == "catalog" and source.image_ids and source.image_ids[0]:
            # The run form's imagery row is built from the chosen image, so it is set with the draft's imagery
            self.chosen_image = self._restored_catalog_image(source)
            self.draft.imagery = self._catalog_choice(self.chosen_image)
            self.render_search_results()
        else:
            gone.append("its imagery can't be chosen again here")
        if self.chosen_image is not None and (self.draft.imagery is None or self.draft.imagery.kind != "catalog"):
            # The row of the catalog image of an earlier Run again (or search) must not stay when the imagery
            # restored is something else: one click would run this processing on that image
            self.chosen_image = self._restored_image = None
            self.render_search_results()
        self._imagery_to_choose = self.draft.imagery is None
        if gone:
            # My imagery is restored later (its collection may need looking up) and says so itself
            what = "the imagery" if self.draft.imagery is None and source.kind != "my_imagery" else "what's missing"
            self.notify(f"Run again “{processing.name}”: " + "; ".join(gone) + f". Choose {what} in the form.",
                        Qgis.MessageLevel.Warning, duration=10)
        self.draft.name, self.draft.name_edited = processing.name, True

        # The area comes from Mapflow, not from the map: the layer it was drawn on may be gone or changed.
        # Until it arrives the form has no area, so the run can't start on whatever area was set before.
        self._watch_layer(None)
        self.draft.aoi = None

        def with_area(collection: dict):
            if restoring != self._restoring:
                return                                  # another Run again came after this one
            layer = aoi_tools.geojson_layer(collection, f"Area · {processing.name}")
            if layer is None:
                self.notify("Mapflow sent no area for this processing. Choose the area again.",
                            Qgis.MessageLevel.Warning)
            else:
                self.layers.add(layer)
                self.set_aoi_layer(layer)
                self.layers.zoom_to([layer])
            self.refresh_run()
            self.render_imagery_area()

        self.api.processing_aois(processing.id, with_area,
                                 lambda error: self.notify(f"The area didn't load: {error.message}",
                                                           Qgis.MessageLevel.Warning))
        self.content.open_run()
        self.refresh_run()

    def _restore_my_imagery(self, mosaic_id: Optional[str], image_id: Optional[str], restoring: int,
                            image=None) -> None:
        """My imagery of an earlier processing: a whole collection, or one image (the API keeps only the
        image id then, so its collection is looked up). The image found that way isn't put in the collection's
        cached image list: that list would then look complete with one image in it."""
        if restoring != self._restoring:
            return                                      # another Run again came after this one
        if image_id and image is None:
            image = next((i for images in self.imagery.images.values() for i in images if i.id == image_id), None)
            if image is None:
                def found(found_image):
                    if found_image.mosaic_id:
                        self._restore_my_imagery(found_image.mosaic_id, image_id, restoring, found_image)
                    elif restoring == self._restoring:
                        self.notify("The image of that processing is no longer in My imagery. Choose the imagery.",
                                    Qgis.MessageLevel.Warning)

                def missing(_error):
                    if restoring == self._restoring:
                        self.notify("The image of that processing is no longer in My imagery. Choose the "
                                    "imagery.", Qgis.MessageLevel.Warning)
                self.api.mosaic_image(image_id, found, missing)
                return
        if image is not None:
            mosaic_id = image.mosaic_id or mosaic_id
        mosaic = self.imagery.get_mosaic(mosaic_id)
        if mosaic is None and mosaic_id:
            # Not on the loaded pages: asked for by id. Gone (404), it isn't chosen: the cost check and the run
            # would fail on Mapflow's side
            def found(_mosaic) -> None:
                self._restore_my_imagery(mosaic_id, image_id, restoring, image)

            def missing() -> None:
                if restoring == self._restoring:
                    self.notify("The My imagery collection of that processing is no longer there. Choose the "
                                "imagery.", Qgis.MessageLevel.Warning, duration=10)
                    self._imagery_to_choose = True
                    self.refresh_run()
            self.imagery.fetch_mosaic(mosaic_id, found, missing,
                                      lambda text: restoring == self._restoring and self.notify(
                                          f"The collection of that processing didn't load: {text}",
                                          Qgis.MessageLevel.Warning))
            return
        self.draft.imagery = ImageryChoice.from_mosaic(mosaic_id, mosaic.name if mosaic else "My imagery",
                                                       image_id, image.filename if image else "")
        self._imagery_to_choose = False
        self.refresh_run()

    # ---------- imagery tab ----------

    @guarded
    def open_search(self) -> None:
        self.content.go(IMAGERY)
        self.content.imagery.show_tab(imagery_tabs.SEARCH)
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
        self.imagery.clear_results()
        for layer in QgsProject.instance().mapLayersByName("Mapflow · search results"):
            QgsProject.instance().removeMapLayer(layer.id())
        self.footprints = None
        self._pictures = {}
        self.content.imagery.forget_thumbnails()
        self.content.imagery.show_search_message("")
        self.render_search_results()

    @guarded
    def search(self, params: dict) -> None:
        if not self.draft.aoi:
            self.content.imagery.show_search_message("Set an area first.", "warn")
            return
        self.content.imagery.set_searching(True)
        self.content.imagery.show_search_message("")
        self.content.imagery.forget_thumbnails()
        self._pictures = {}
        # Loaded tiles stay; one still loading may never answer (a sign-out aborts it): asked for again
        self._world_tiles = {url: tile for url, tile in self._world_tiles.items() if isinstance(tile, bytes)}
        self.imagery.search(self.draft.aoi.geometry, params["date_from"], params["date_to"], params["max_cloud"],
                            params["min_off_nadir"], params["max_off_nadir"], params["product_types"],
                            params.get("min_coverage"), bool(params.get("hide_unavailable")))

    @guarded
    def on_search_done(self, images, total: int) -> None:
        page = self.content.imagery
        page.set_searching(False)
        if not images:
            page.show_search_message("No images match. Widen the dates or allow more cloud cover.", "info")
        self.render_search_results()
        self._show_footprints()
        self._load_thumbnails(images)

    @guarded
    def more_results(self) -> None:
        self.imagery.search_more()
        self.render_search_results()

    @guarded
    def on_more_results(self, images, total: int) -> None:
        self.render_search_results()
        self._show_footprints()
        self._load_thumbnails(images)

    def _show_footprints(self) -> None:
        images = self.imagery.results
        features = [{"type": "Feature", "geometry": i.footprint,
                     "properties": {"id": i.key, "provider": i.provider,
                                    "date": i.acquired.isoformat() if i.acquired else None, "cloud": i.cloud}}
                    for i in images if i.footprint]
        self.footprints = self.layers.footprints_layer({"type": "FeatureCollection", "features": features})

    def _load_thumbnails(self, images) -> None:
        for image in images:
            if not image.preview_url or self.content.imagery.has_thumbnail(image.key):
                continue
            if self._picture_preview(image):
                # Silent on purpose: a missing picture leaves the card's placeholder, and a line for each card of
                # the list would bury the list's own message. Http logs the failure.
                self.api.preview(image.preview_url,
                                 lambda data, key=image.key: self._set_thumb(key, data), lambda _e: None)
            elif image.preview_type in ("xyz", "tms"):
                # A tiled preview (ArcGIS): its whole-world tile, so the card isn't empty (as Mapflow Web does)
                self._world_tile(re.sub(r"\{-?[xyz]\}", "0", image.preview_url), image.key)

    def _world_tile(self, url: str, key: str) -> None:
        """The 0/0/0 tile as a result's thumbnail. Results of one provider share it: asked for once, and
        every card waiting for it gets it."""
        known = self._world_tiles.get(url)
        if isinstance(known, bytes):
            self._set_thumb(key, known, keep=False)
            return
        if known is not None:                       # on its way
            known.append(key)
            return
        self._world_tiles[url] = [key]

        def done(data: bytes) -> None:
            waiting = self._world_tiles.get(url)
            self._world_tiles[url] = data
            for waiting_key in waiting if isinstance(waiting, list) else []:
                self._set_thumb(waiting_key, data, keep=False)

        self.api.preview(url, done, lambda _e: self._world_tiles.pop(url, None))

    @staticmethod
    def _picture_preview(image: CatalogImage) -> bool:
        return image.preview_type in ("png", "jpg", "jpeg", "")

    def _set_thumb(self, image_id: str, data: bytes, keep: bool = True) -> None:
        """`keep`: the picture is also what the eye puts on the map."""
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            if keep:
                self._pictures[image_id] = data
            self.content.imagery.set_thumbnail(image_id, pixmap)

    def _search_previewing(self) -> set:
        return {i.key for i in self.imagery.results if self.layers.previews(f"catalog:{i.key}")}

    def render_search_results(self) -> None:
        self.content.imagery.set_results(self.imagery.results, self.imagery.total,
                                         self.chosen_image.key if self.chosen_image else None,
                                         self._search_previewing(), self.imagery.loading_more)

    @guarded
    def on_search_failed(self, text: str) -> None:
        self.content.imagery.set_searching(False)
        self.content.imagery.show_search_message(text, "error")

    @guarded
    def show_image(self, image_key: str) -> None:
        """The eye on a search result (by CatalogImage.key): its preview on the map (or off, if it is there),
        and its footprint selected and zoomed to."""
        image = self.imagery.get_result(image_key)
        layer = getattr(self, "footprints", None)
        if image is None:
            return
        key = f"catalog:{image.key}"
        shown = self.layers.previews(key)
        if shown:
            self.layers.remove(shown)                   # the eyes follow through layersRemoved
            return
        if layer is not None:
            try:
                ids = [f.id() for f in layer.getFeatures() if f["id"] == image_key]
                layer.selectByIds(ids)
                if ids:
                    self.iface.mapCanvas().zoomToSelected(layer)
            except RuntimeError:
                pass
        name = f"Preview · {_provider_name(image.provider)} {image.id[:8]}" + \
            (f" · z{image.zoom}" if image.key != image.id else "")
        if image.parts:
            self._preview_parts(image, key, name)
        elif image.preview_url and image.preview_type in ("xyz", "tms"):
            url = image.preview_url.replace("{y}", "{-y}") if image.preview_type == "tms" else image.preview_url
            preview = self.layers.tile_raster(url, name)
            if preview:
                self.layers.add(preview, position=len(self.layers.group().children()), preview=key)
        elif image.preview_url and self._picture_preview(image):
            def add(data: bytes) -> None:
                self._pictures[image.id] = data
                if self.layers.previews(key):
                    return
                picture = self.layers.picture_on_footprint(data, image.footprint, name, image.id)
                if picture is None:
                    self.notify("This image's preview can't be placed on the map.", Qgis.MessageLevel.Info)
                    return
                self.layers.add(picture, position=0, preview=key)   # on top: a preview is to be looked at

            data = self._pictures.get(image.id)
            if data:
                add(data)
            else:
                self.api.preview(image.preview_url, add,
                                 lambda error: self.notify(f"The preview didn't load: {error.message}",
                                                           Qgis.MessageLevel.Warning))

    def _preview_parts(self, image: CatalogImage, key: str, name: str) -> None:
        """A preview in several pictures, each on its own footprint (Roscosmos): all of them, as one layer."""
        pictures: Dict[int, bytes] = {}
        failed: List[str] = []

        def got(index: int, data: bytes) -> None:
            pictures[index] = data
            if len(pictures) < len(image.parts) or self.layers.previews(key):
                return
            layer = self.layers.pictures_on_footprints(
                [(pictures[i], footprint) for i, (_url, footprint) in enumerate(image.parts)], name, image.id)
            if layer is None:
                self.notify("This image's preview can't be placed on the map.", Qgis.MessageLevel.Info)
                return
            self.layers.add(layer, position=0, preview=key)

        def error(problem) -> None:
            if not failed:                          # one message, however many parts fail
                self.notify(f"The preview didn't load: {problem.message}", Qgis.MessageLevel.Warning)
            failed.append(problem.message)

        for index, (url, _footprint) in enumerate(image.parts):
            self.api.preview(url, lambda data, i=index: got(i, data), error)

    @guarded
    def use_image(self, image_key: str) -> None:
        image = self.imagery.get_result(image_key)
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
        name = self._choose_uploaded
        if name and self.uploading is None:
            uploaded = [m for m in self.imagery.mosaics if m.name == name]
            if uploaded:
                self._choose_uploaded = None
                self.use_mosaic(max(uploaded, key=lambda m: str(m.created or "")).id)

    @guarded
    def on_mosaics_failed(self, text: str) -> None:
        """A listing nobody waited on failed: what was marked as waiting for it is cleared, so the control that
        set it works again."""
        self._choose_uploaded = self._select_in_picker = None
        if text:
            self.notify(text, Qgis.MessageLevel.Warning)

    def _show_upload_limit(self) -> None:
        self.content.imagery.set_upload_limit(self.imagery.limits.max_upload_bytes or config.UPLOAD_LIMIT_BYTES)

    @guarded
    def on_limits_failed(self, reason: str) -> None:
        """The account's upload limits didn't load. Uploads go on, with the built-in limits: the line says so."""
        self.notify(f"Your upload limits didn't load: {reason} The standard limits apply: "
                    f"{formatting.size_limit(config.UPLOAD_LIMIT_BYTES)} a file, "
                    f"{config.MAX_SIDE_PIXELS:,} px a side.", Qgis.MessageLevel.Warning)

    @guarded
    def on_images_failed(self, mosaic_id: str, text: str, tell: bool) -> None:
        """An image list did not load. A click that waited for it is cleared; the picker says so in its box."""
        if self._use_pending == mosaic_id:
            self._use_pending = None
        choice = self.draft.imagery
        if self._extent_pending and choice and choice.kind == "my_imagery" and choice.mosaic_id == mosaic_id:
            self._extent_pending = False
        picker = self.mosaic_picker
        if picker is not None and picker.current == mosaic_id:
            picker.set_images_failed(mosaic_id, text)
        if tell:
            self.notify(f"The images didn't load: {text}", Qgis.MessageLevel.Warning)
        self._mosaic_render.start()

    @guarded
    def on_project_gone(self, project_id: str, error) -> None:
        """The open project answered 403 or 404 (deleted or unshared): open the default one and say so."""
        project = self.processings.project
        name = project.name if project is not None and project.id == project_id else ""
        opened = self.session.open_default_project(project_id)
        self.notify(project_gone_text(name, opened), Qgis.MessageLevel.Warning, duration=10)

    def _show_mosaics(self, chosen: Optional[str]) -> None:
        """The My imagery tab's collections: the pages loaded, of all there are."""
        self.content.imagery.set_mosaics(self.imagery.mosaics, chosen, self.imagery.mosaics_total,
                                         self.imagery.loading_mosaics, loaded=self.imagery.mosaics_loaded,
                                         failed=self.imagery.mosaics_failed)

    @guarded
    def _render_mosaics(self) -> None:
        choice = self.draft.imagery
        self._show_mosaics(choice.mosaic_id if choice and choice.kind == "my_imagery" else None)
        picker = self.mosaic_picker
        if picker is not None:
            listed = {m.id for m in picker.mosaics}
            select = self._select_in_picker
            new = next((m for m in self.imagery.mosaics if m.id == select or (m.id not in listed and m.name == select)),
                       None) if select else None
            changed = ({m.id for m in self.imagery.mosaics} != listed or picker.total != self.imagery.mosaics_total
                       or picker.loading != self.imagery.loading_mosaics
                       or picker.loaded != self.imagery.mosaics_loaded or picker.failed != self.imagery.mosaics_failed)
            if changed or new is not None:
                picker.set_collections(self.imagery.mosaics, picker.chosen_mosaic, picker.chosen_image,
                                       self.imagery.mosaics_total, self.imagery.loading_mosaics,
                                       loaded=self.imagery.mosaics_loaded, failed=self.imagery.mosaics_failed)
                if new is not None:
                    self._select_in_picker = None
                    picker.open_collection(new.id)
                elif picker.current and self.imagery.get_mosaic(picker.current) is None:
                    picker.open_collection(None)            # deleted (it may be on no loaded page otherwise)
            picker.update_counts()
        self.refresh_run(keep_name=True)

    @guarded
    def on_mosaic_images(self, mosaic_id: str, images) -> None:
        self._mosaic_render.start()
        if self._use_pending == mosaic_id:             # a collection was chosen before its images were known
            self._use_pending = None
            self.use_mosaic(mosaic_id)
        choice = self.draft.imagery
        if self._extent_pending and choice and choice.kind == "my_imagery" and choice.mosaic_id == mosaic_id:
            self.use_imagery_extent()
        picker = self.mosaic_picker
        if picker is not None and picker.current == mosaic_id:
            picker.set_images(mosaic_id, images)
            for image in images:
                if image.preview_s:
                    # Silent on purpose: a missing thumbnail leaves the placeholder; Http logs the failure
                    self.api.preview(image.preview_s, lambda data, iid=image.id: self._set_picker_thumb(iid, data),
                                     lambda _e: None)

    def _set_picker_thumb(self, image_id: str, data: bytes) -> None:
        pixmap = QPixmap()
        if self.mosaic_picker is not None and pixmap.loadFromData(data):
            self.mosaic_picker.set_thumbnail(image_id, pixmap)

    @guarded
    def pick_my_imagery(self) -> None:
        """My imagery's button on the run form: with collections, the picker; with none yet ("Add imagery…"),
        there is nothing to pick, so the My imagery tab, where uploads are."""
        if self.imagery.mosaics:
            self.open_mosaic_picker()
            return
        self.content.go(IMAGERY)
        self.content.imagery.show_tab(imagery_tabs.MINE)
        self._refresh_mosaics()

    @guarded
    def open_mosaic_picker(self, mosaic_id: Optional[str] = None) -> None:
        """Choose a My imagery collection, or one image of it."""
        if self._stopped:
            return
        self._refresh_mosaics()
        if self.mosaic_picker is None:
            picker = MosaicPicker(self.iface.mainWindow(), self.session.config.my_data_url)
            picker.collectionOpened.connect(guarded(lambda mid: self.imagery.load_images(mid, waiting=True)))
            picker.chosen.connect(self._mosaic_chosen)
            picker.showRequested.connect(self.show_mosaic)
            picker.uploadRequested.connect(guarded(lambda target: self.upload(target or None)))
            picker.layerUploadRequested.connect(
                guarded(lambda ids, target: self.upload_layers(ids, mosaic_id=target or None)))
            picker.createRequested.connect(self.create_collection)
            picker.renameCollectionRequested.connect(self.rename_collection)
            picker.deleteCollectionRequested.connect(self.delete_collection)
            picker.downloadImageRequested.connect(self.download_image)
            picker.deleteImageRequested.connect(self.delete_image)
            picker.geotiff_layers = lambda: [(layer.id(), layer.name()) for layer in rasters.geotiff_layers()]
            picker.parse_drop = rasters.dropped_geotiffs
            picker.filesDropped.connect(guarded(lambda items, target: self.upload_dropped(items, target or None)))
            picker.lookup = self.imagery.get_mosaic
            picker.queryChanged.connect(guarded(self.imagery.search_mosaics))
            picker.moreRequested.connect(guarded(lambda query: self.imagery.search_mosaics(query, more=True) if query
                                         else self.imagery.load_more_mosaics()))
            self.mosaic_picker = picker
        choice = self.draft.imagery
        chosen_mosaic = choice.mosaic_id if choice and choice.kind == "my_imagery" else None
        chosen_image = choice.image_ids[0] if chosen_mosaic and choice.image_ids else None
        self.mosaic_picker.set_collections(self.imagery.mosaics, chosen_mosaic, chosen_image,
                                           self.imagery.mosaics_total, self.imagery.loading_mosaics,
                                           loaded=self.imagery.mosaics_loaded, failed=self.imagery.mosaics_failed)
        # Nothing selected unless asked for: a selection is also where uploads go
        self.mosaic_picker.open_collection(mosaic_id or chosen_mosaic)
        self.mosaic_picker.set_upload(self.uploading)
        self.mosaic_picker.show()
        self.mosaic_picker.raise_()
        self.mosaic_picker.activateWindow()

    @guarded
    def _mosaic_chosen(self, mosaic_id: str, image_id: str) -> None:
        mosaic = self.imagery.get_mosaic(mosaic_id)
        if mosaic is None:
            return
        if not image_id and self._empty_collection(mosaic):
            self._refuse_empty(mosaic)
            return
        image = self.imagery.get_image(mosaic_id, image_id) if image_id else None
        self.draft.imagery = ImageryChoice.from_mosaic(mosaic.id, mosaic.name, image.id if image else None,
                                                       image.filename if image else "")
        if self.mosaic_picker is not None:
            self.mosaic_picker.accept()
        self._show_mosaics(mosaic.id)
        self.content.open_run()
        self.use_imagery_extent()
        self._preview_my_imagery()
        self.refresh_run()

    @guarded
    def show_mosaic(self, mosaic_id: Optional[str], zoom: bool = True) -> None:
        """A My imagery collection on the map: once, at the bottom of the Mapflow group."""
        mosaic = self.imagery.get_mosaic(mosaic_id)
        if mosaic is None:
            return
        key = f"mosaic:{mosaic.id}"
        shown = self.layers.previews(key)
        if shown:                                   # already there: show it rather than add another
            for layer in shown:
                node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
                if node is not None:
                    node.setItemVisibilityChecked(True)
            if zoom:
                self.layers.zoom_to(shown)
            return

        def add(tilejson: Optional[dict]):
            if self.layers.previews(key):           # two requests crossed
                return
            layer = self.layers.tile_raster(mosaic.tile_url, self.layers.mosaic_layer_name(mosaic.name),
                                            bounds_extent((tilejson or {}).get("bounds")) if tilejson else None)
            if layer:
                self.layers.add(layer, position=len(self.layers.group().children()), preview=key)
                if zoom:
                    self.layers.zoom_to([layer])

        if mosaic.tilejson_url:
            self.api.tilejson(mosaic.tilejson_url, add, lambda _e: add(None))
        else:
            add(None)

    @guarded
    def _empty_collection(self, mosaic) -> Optional[bool]:
        """True if the collection has no images, None while that isn't known yet."""
        if mosaic.id in self.imagery.images:
            return not self.imagery.images[mosaic.id]
        return None if mosaic.image_count is None else mosaic.image_count == 0

    def _refuse_empty(self, mosaic) -> None:
        my_data = self.session.config.my_data_url
        self.notify(f"“{mosaic.name}” has no images, so it can't be processed. Add images to it in Mapflow Web, "
                    "or upload a GeoTIFF on the Imagery sources tab.", Qgis.MessageLevel.Critical,
                    ("Mapflow Web", lambda: QDesktopServices.openUrl(QUrl(my_data))), duration=10)

    @guarded
    def use_mosaic(self, mosaic_id: str) -> None:
        mosaic = self.imagery.get_mosaic(mosaic_id)
        if mosaic is None:
            return
        empty = self._empty_collection(mosaic)
        if empty is None:                               # decided once its image list arrives
            self._use_pending = mosaic.id
            self.imagery.load_images(mosaic.id, waiting=True)
            return
        if empty:
            self._refuse_empty(mosaic)
            return
        if (mosaic.image_count or 0) > 1:
            self.open_mosaic_picker(mosaic.id)          # several images: the whole collection, or one of them
            return
        if mosaic:
            self.draft.imagery = ImageryChoice.from_mosaic(mosaic.id, mosaic.name)
            self._show_mosaics(mosaic.id)
            self.content.open_run()
            self.use_imagery_extent()
            self._preview_my_imagery()
            self.refresh_run()

    @guarded
    def _upload_progress(self, percent: Optional[int]) -> None:
        """The upload's progress, on Imagery sources and in the run form's My imagery row."""
        self.uploading = percent
        if percent is not None:
            self.content.imagery.set_upload(percent)
            if self.mosaic_picker is not None and percent > 0:     # 0 keeps "Checking…"
                self.mosaic_picker.set_upload(percent)
        self.refresh_run()

    def upload(self, mosaic_id: Optional[str] = None) -> None:
        """Upload GeoTIFFs, one or several picked together: into the collection `mosaic_id`, or into a new one."""
        if self.uploading is not None or self.imagery.uploading:
            return
        paths, _ = QFileDialog.getOpenFileNames(self.mosaic_picker if self._picker_open() else self.content,
                                                "Upload GeoTIFFs to My imagery", "", "GeoTIFF (*.tif *.tiff)")
        self.upload_files([p for p in paths or [] if p], mosaic_id=mosaic_id)

    def _picker_open(self) -> bool:
        return self.mosaic_picker is not None and self.mosaic_picker.isVisible()

    @guarded
    def upload_layer(self, layer_id: str, choose: bool = False, mosaic_id: Optional[str] = None) -> None:
        self.upload_layers([layer_id], choose, mosaic_id)

    @guarded
    def upload_layers(self, layer_ids: List[str], choose: bool = False, mosaic_id: Optional[str] = None) -> None:
        """Upload the files of GeoTIFF layers of the project: into `mosaic_id`, or as one new collection, named
        as the layer is when there is one."""
        layers = [QgsProject.instance().mapLayer(layer_id) for layer_id in layer_ids]
        paths = [rasters.geotiff_path(layer) for layer in layers]
        for layer, path in zip(layers, paths):
            if not path:
                self._upload_refused(f"“{layer.name() if layer else 'this layer'}”: only a layer read from a "
                                     "GeoTIFF file can be uploaded")
                return
        self.upload_files(paths, layers[0].name() if len(layers) == 1 else "", choose, mosaic_id)

    @guarded
    def upload_dropped(self, items: List[Tuple[str, str]], mosaic_id: Optional[str] = None) -> None:
        """GeoTIFF layers or files dragged onto My imagery, as (file, name): one is named as it is."""
        self.upload_files([path for path, _name in items], items[0][1] if len(items) == 1 else "",
                          mosaic_id=mosaic_id)

    def upload_files(self, paths: List[str], name: str = "", choose: bool = False,
                     mosaic_id: Optional[str] = None) -> None:
        """Ask Mapflow for the account's limits, check the files against them, here and with Mapflow, then upload
        them into the collection `mosaic_id`, or as one new collection. `choose`: use the new collection as the
        imagery once Mapflow lists it."""
        if not paths or self.uploading is not None or self.imagery.uploading:
            return
        # Busy at once: the limits take a round trip, and a second start must not slip in meanwhile
        self.content.imagery.set_upload(0, "Checking…")
        if self.mosaic_picker is not None:
            self.mosaic_picker.set_upload(0, "Checking…")
        self._upload_progress(0)
        try:
            self.imagery.load_limits(lambda limits: self._upload_checked(paths, name, choose, mosaic_id, limits),
                                     waiting=True)
        except Exception:
            self._upload_idle()
            raise

    def _upload_checked(self, paths: List[str], name: str, choose: bool, mosaic_id: Optional[str],
                        limits: StorageLimits) -> None:
        """The limits are known (or the built-in ones apply): check the files, then start. Every way out clears
        the busy state that `upload_files` set, an exception included."""
        try:
            self._upload_start(paths, name, choose, mosaic_id, limits)
        except Exception:
            self._upload_idle()
            if choose and not mosaic_id:
                self._choose_uploaded = None
            raise

    def _upload_start(self, paths: List[str], name: str, choose: bool, mosaic_id: Optional[str],
                      limits: StorageLimits) -> None:
        checked = [rasters.geotiff_metadata(p, limits.max_upload_bytes or config.UPLOAD_LIMIT_BYTES,
                                            limits.max_side_pixels or config.MAX_SIDE_PIXELS) for p in paths]
        problem = next((f"{meta['filename']}: {why}" for meta, why in checked if why), "") \
            or (rasters.mixed([meta for meta, _why in checked]) if len(checked) > 1 else "")
        if problem:
            self._upload_refused(problem, busy=True)
            return
        duplicates_allowed: Set[str] = set()
        if mosaic_id:
            # Files the collection already has (by name, as far as its image list is known here): asked about
            # before any bytes go. Mapflow checks again, and the same question comes if it finds one.
            mosaic = self.imagery.get_mosaic(mosaic_id)
            known = {(i.filename or "").lower() for i in self.imagery.images.get(mosaic_id, [])}
            repeated = [p for p in paths if Path(p).name.lower() in known]
            if repeated:
                choice = self._ask_duplicate([Path(p).name for p in repeated], mosaic.name if mosaic else "")
                if choice == "cancel":
                    self._upload_idle()
                    return
                if choice == "skip":
                    keep = [p not in repeated for p in paths]
                    paths = [p for p, k in zip(paths, keep) if k]
                    checked = [c for c, k in zip(checked, keep) if k]
                    if not paths:
                        self._upload_refused(f"nothing new: “{mosaic.name if mosaic else 'the collection'}” "
                                             f"already has {', '.join(Path(p).name for p in repeated)}", busy=True)
                        return
                else:
                    duplicates_allowed = {Path(p).name for p in repeated}
        folder = Path(paths[0]).parent.name
        name = name or (Path(paths[0]).stem if len(paths) == 1 else (folder or Path(paths[0]).stem))
        needed = sum(meta["file_size"] for meta, _why in checked)
        if limits.free_bytes is not None and needed > limits.free_bytes:
            free = formatting.size(limits.free_bytes)
            self._upload_refused(
                f"“{name}”: it needs {formatting.size(needed)}, and only {free} of your storage is free"
                if len(paths) == 1 else
                f"these {len(paths)} files: together they need {formatting.size(needed)}, and only {free} "
                "of your storage is free", busy=True)
            return
        self._choose_uploaded = name if choose and not mosaic_id else None
        if self._choose_uploaded:
            self.notify(f"Uploading “{name}” to My imagery. It becomes the imagery when it's ready.",
                        Qgis.MessageLevel.Info, duration=6)
        if not mosaic_id and self._picker_open():
            self._select_in_picker = name           # the new collection is selected once listed

        def validated(problems: List[str], warnings: List[str]) -> None:
            if problems:
                self._choose_uploaded = None
                self._upload_refused("; ".join(problems[:3]), busy=True)
                return
            if warnings:
                self.notify("Mapflow: " + "; ".join(warnings[:3]), Qgis.MessageLevel.Info, duration=8)
            if mosaic_id:
                self.imagery.upload_into(mosaic_id, paths, duplicates_allowed)
            elif len(paths) == 1:
                self.imagery.upload(paths[0], name)
            else:
                self.imagery.upload_many(paths, name)

        # Into an existing collection, Mapflow also checks the image fits it (CRS, bands, resolution)
        extra = {"mosaic_id": mosaic_id} if mosaic_id else {}
        self.imagery.validate([(meta["filename"], {**rasters.validation_request(meta), **extra})
                               for meta, _why in checked], validated)

    def _upload_idle(self) -> None:
        """An upload ends before it sends anything: nothing is busy any more."""
        self._upload_progress(None)
        self.content.imagery.set_upload(None)
        if self.mosaic_picker is not None:
            self.mosaic_picker.set_upload(None)

    # ---------- the Layers panel's Mapflow actions ----------

    @guarded
    def use_layer_as_aoi(self, layer_id: str) -> None:
        """“Use as AOI in Mapflow” on a polygon layer: it becomes the run form's area."""
        layer = QgsProject.instance().mapLayer(layer_id)
        if not aoi_tools.is_polygon_layer(layer):
            self.notify("Only a polygon layer can be the area to process.", Qgis.MessageLevel.Warning)
            return
        if self.session.state != SIGNED_IN:
            self._after_sign_in = ("aoi", layer_id)
            return
        self.set_aoi_layer(layer)
        self.content.open_run()
        self.refresh_run()
        self.render_imagery_area()

    @guarded
    def use_layer_as_imagery(self, layer_id: str) -> None:
        """“Use as imagery in Mapflow” on a GeoTIFF layer: uploaded to My imagery, then chosen as the imagery."""
        layer = QgsProject.instance().mapLayer(layer_id)
        if not rasters.geotiff_path(layer):
            self.notify("Only a layer read from a GeoTIFF file can be uploaded to Mapflow.",
                        Qgis.MessageLevel.Warning)
            return
        if self.session.state != SIGNED_IN:
            self._after_sign_in = ("imagery", layer_id)
            return
        if self.uploading is not None or self.imagery.uploading:
            self.notify("Another upload is running. Try again when it's done.", Qgis.MessageLevel.Info)
            return
        self.content.open_run()
        self.upload_layer(layer_id, choose=True)

    @guarded
    def create_collection(self) -> None:
        """“Create collection” in My imagery: a name and tags; the new collection is selected, ready for uploads."""
        dialog = CollectionDialog(self.mosaic_picker if self._picker_open() else self.iface.mainWindow())
        if not dialog.exec():
            return
        name, tags = dialog.values()
        picker = self.mosaic_picker

        def created(mosaic_id: str) -> None:
            self._select_in_picker = mosaic_id or name
            if picker is not None:
                picker.set_upload(None, f"“{name}” is created. Upload GeoTIFFs into it.", "info")

        def failed(message: str) -> None:
            if picker is not None:
                picker.set_upload(None, f"Couldn't create “{name}”: {message}", "error")
            self.notify(f"Couldn't create the collection “{name}”: {message}", Qgis.MessageLevel.Warning)

        self.imagery.create_collection(name, tags, created, failed)

    @guarded
    def rename_collection(self, mosaic_id: str) -> None:
        """“Rename…” in a collection's ⋯ menu: its name and tags. Nothing is sent for an empty name or no change."""
        mosaic = self.imagery.get_mosaic(mosaic_id)
        if mosaic is None:
            return
        dialog = CollectionDialog(self.mosaic_picker if self._picker_open() else self.iface.mainWindow(),
                                  title="Rename collection", action="Save", name=mosaic.name, tags=mosaic.tags)
        if not dialog.exec():
            return
        name, tags = dialog.values()
        old = mosaic.name
        if not name or (name, tags) == (old, mosaic.tags):
            return

        def done(old_name: str) -> None:
            choice = self.draft.imagery
            if choice and choice.kind == "my_imagery" and choice.mosaic_id == mosaic_id:
                choice.with_collection_name(old_name, name)
            for layer in self.layers.previews(f"mosaic:{mosaic_id}"):
                layer.setName(self.layers.mosaic_layer_name(name))
            if self.mosaic_picker is not None:
                self.mosaic_picker.collection_renamed(mosaic_id, self.imagery.mosaics, self.imagery.found_query,
                                                      self.imagery.found)
            self._picker_note(f"“{old_name}” is renamed to “{name}”.")
            self.render_processings()
            self.refresh_run()

        def failed(message: str) -> None:
            self._picker_note(f"Couldn't rename “{old}”: {message}", "error")
            self.notify(f"Couldn't rename “{old}”: {message}", Qgis.MessageLevel.Warning)

        self.imagery.rename_collection(mosaic_id, name, tags, done, failed)

    def _confirm_delete(self, title: str, text: str, detail: str) -> bool:
        box = QMessageBox(self.mosaic_picker if self._picker_open() else self.iface.mainWindow())
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(title)
        box.setText(text)
        box.setInformativeText(detail)
        delete = box.addButton("Delete", QMessageBox.ButtonRole.DestructiveRole)
        cancel = box.addButton(QMessageBox.StandardButton.Cancel)
        box.setDefaultButton(cancel)
        box.exec()
        return box.clickedButton() is delete

    def _picker_note(self, text: str, kind: str = "info") -> None:
        if self.mosaic_picker is not None:
            self.mosaic_picker.set_upload(None, text, kind)

    @guarded
    def delete_collection(self, mosaic_id: str) -> None:
        mosaic = self.imagery.get_mosaic(mosaic_id)
        if mosaic is None:
            return
        count = mosaic.image_count
        images = "its image" if count == 1 else f"its {count} images" if count else "its images"
        if not self._confirm_delete("Delete collection", f"Delete “{mosaic.name}”?",
                                    f"The collection and {images} are deleted from Mapflow. This can't be undone."):
            return
        name = mosaic.name

        def done() -> None:
            choice = self.draft.imagery
            if choice and choice.kind == "my_imagery" and choice.mosaic_id == mosaic_id:
                self.draft.imagery = None           # nothing to process any more: the user chooses again
            self.layers.remove(self.layers.previews(f"mosaic:{mosaic_id}"))   # its map preview is gone too
            self._picker_note(f"“{name}” is deleted.")
            self.refresh_run()

        def failed(message: str) -> None:
            self._picker_note(f"Couldn't delete “{name}”: {message}", "error")
            self.notify(f"Couldn't delete “{name}”: {message}", Qgis.MessageLevel.Warning)

        self.imagery.delete_mosaic(mosaic_id, done, failed)

    @guarded
    def delete_image(self, mosaic_id: str, image_id: str) -> None:
        mosaic = self.imagery.get_mosaic(mosaic_id)
        image = self.imagery.get_image(mosaic_id, image_id)
        if mosaic is None or image is None:
            return
        last = len(self.imagery.images.get(mosaic_id, [])) == 1
        filename = image.filename or image.id
        if not self._confirm_delete("Delete image", f"Delete “{filename}” from “{mosaic.name}”?",
                                    "This can't be undone." + (" The collection stays, empty, for other uploads."
                                                               if last else "")):
            return

        def done() -> None:
            choice = self.draft.imagery
            if choice and choice.kind == "my_imagery" and choice.image_ids == [image_id]:
                self.draft.imagery = None           # that image was the imagery: the user chooses again
            picker = self.mosaic_picker
            if picker is not None and picker.chosen_image == image_id:
                picker.chosen_mosaic = picker.chosen_image = None
            self._picker_note(f"“{filename}” is deleted from “{mosaic.name}”.")
            self.refresh_run()

        def failed(message: str) -> None:
            self._picker_note(f"Couldn't delete “{filename}”: {message}", "error")
            self.notify(f"Couldn't delete “{filename}”: {message}", Qgis.MessageLevel.Warning)

        self.imagery.delete_image(mosaic_id, image_id, done, failed)

    @guarded
    def download_image(self, mosaic_id: str, image_id: str) -> None:
        """"Download…" in an image's ⋯ menu: the original file, saved where the user chooses."""
        image = self.imagery.get_image(mosaic_id, image_id)
        if image is None or not image.available_for_download:
            return
        name = image.filename or image.id
        if self.imagery.is_downloading(image_id):
            self.notify(f"“{name}” is already downloading.")
            return

        def choose(filename: str) -> str:
            suggested = Path(self.results.output_dir) / filenames.safe_filename(filename, image.filename)
            parent = self.mosaic_picker if self._picker_open() else self.iface.mainWindow()
            path, _ = QFileDialog.getSaveFileName(parent, "Download the image", str(suggested))
            if path:
                self._picker_note(f"Downloading “{name}”…")
            return path

        def done(path: str) -> None:
            self._picker_note(f"Image saved to {path}")
            self.notify(f"Image saved to {path}", Qgis.MessageLevel.Success)

        def failed(message: str) -> None:
            self._picker_note(f"Couldn't download “{name}”: {message}", "error")
            self.notify(f"Couldn't download “{name}”: {message}", Qgis.MessageLevel.Warning)

        self.imagery.download_image(image_id, choose, done, failed)

    def _ask_duplicate(self, files: List[str], collection: str) -> str:
        """A collection already has these files: "upload" them again, "skip" them, or "cancel" the upload."""
        names = ", ".join(f"“{f}”" for f in files[:5]) + (f" and {len(files) - 5} more" if len(files) > 5 else "")
        where = f"“{collection}”" if collection else "this collection"
        box = QMessageBox(self.mosaic_picker if self._picker_open() else self.iface.mainWindow())
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("Already in the collection")
        box.setText(f"{where} already has {names}.")
        box.setInformativeText("Upload again to add another copy, or skip "
                               + ("it." if len(files) == 1 else "them and upload the rest."))
        upload = box.addButton("Upload again", QMessageBox.ButtonRole.AcceptRole)
        skip = box.addButton("Skip", QMessageBox.ButtonRole.DestructiveRole)
        box.addButton(QMessageBox.StandardButton.Cancel)
        box.setDefaultButton(skip)
        box.exec()
        clicked = box.clickedButton()
        return "upload" if clicked is upload else "skip" if clicked is skip else "cancel"

    def _upload_refused(self, problem: str, busy: bool = False) -> None:
        """`busy`: `upload_files` marked an upload as running; this ends it."""
        if busy:
            self._upload_progress(None)
        text = f"Can't upload {problem}."
        self.content.imagery.set_upload(None, text, "error")
        if self.mosaic_picker is not None:
            self.mosaic_picker.set_upload(None, text, "error")
        self.notify(text, Qgis.MessageLevel.Warning)


def _count(value: int, noun: str) -> str:
    return f"{value:,} {noun}" + ("" if value == 1 else "s")


def _zoom_meta(zoom: Optional[int]) -> str:
    resolution = {17: "1.2 m", 18: "0.6 m", 19: "0.3 m", 20: "0.15 m", 21: "0.075 m"}.get(zoom or 0)
    return f"≈ {resolution} per pixel" if resolution else ""


def _provider_name(name: str) -> str:
    readable = (name or "Catalog").replace("_", " ").title()
    return {"my_imagery_images": "My", "my_imagery_mosaics": "My"}.get(name, readable)
