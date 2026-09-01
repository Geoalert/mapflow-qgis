"""Planned processings (templates): creation, search-param update, exclude-from-search, the
seen-image markers, the template's map layers, and its imagery-search results.

Everything scoped to a template id lives here, including the in-template view: whether a template
is open, which one, its AOIs and its launched processings.

Holds no widget (`spec/007_architecture.md` § Layer rules). Inputs that come from widgets — the
template name, the assembled `SearchParams`, the AOI FeatureCollection — arrive as arguments from
`TemplateController`; UI effects the service must cause (the busy button, the rebuilt table rows,
the slower in-template poll cadence) leave as signals. The map layers a template draws are QGIS
layer-tree work, not widgets, so they live here alongside `AoiService`/`PreviewService`'s own layer
building.

`ProcessingService` is still reached for the shared `api` client, the poll timer it owns, and its
`templates` dict — the project's template list, which its own project fetch fills. The dependency
runs one way only, with no exception: `ProcessingService` never reaches back here. What it needs to
know about an open template — which one, and which processings the table is showing — is *pushed*
to it, as `templateOpened`/`templateClosed` and `visibleProcessingsChanged`, wired by
`ProjectProcessingController`. The processings table's two views are that controller's to choose,
not either service's.
"""
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from osgeo import ogr
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QNetworkReply
from qgis.core import (QgsFeature,
                       QgsGeometry,
                       QgsLayerTreeGroup,
                       QgsLayerTreeLayer,
                       QgsVectorLayer)

from .. import layer_utils
from ..app_context import AppContext
from ...config import Config
from ..geometry import geometry_from_geojson
from ..helpers import utc_date_from_iso
from .alert_service import (alert, alert_confirm, alert_info, alert_warning,
                            ask_text, report_http_error)
from ...errors import ErrorMessage
from ...http import api_message_parser
from ...schema import ImageCatalogResponseSchema
from ...schema.template import (AOI_NAME_MAX_LENGTH,
                                CreateProcessingTemplateSchema,
                                DeleteAoisSchema,
                                NoAoiProcessingsRow,
                                ProcessingTemplateDTO,
                                ProcessingTemplateDetails,
                                SearchParams,
                                TemplateProcessingSchema,
                                UpdateAoiSchema,
                                UpdateProcessingTemplateSchema)

logger = logging.getLogger(__name__)


class TemplateService(QObject):

    #: True while a create request is in flight; the controller disables the Search button.
    creationBusy = pyqtSignal(bool)
    #: A template needs a project and none is open; the argument is the message for the panel
    #: label. The service also alerts — the label is the persistent reminder, the alert the nudge.
    projectRequired = pyqtSignal(str)
    #: A short "creating…/updating…" status for the message bar.
    statusMessage = pyqtSignal(str)
    #: A template's new-images count changed; the controller refreshes its status cell. Carries
    #: the template DTO (a schema type, which a view may read).
    templateStatusChanged = pyqtSignal(object)
    #: A non-modal warning for the message bar (a seen request failed).
    warningMessage = pyqtSignal(str)
    #: A page of the template's search results arrived: the GeoJSON, ready for the table.
    searchResultsReady = pyqtSignal(object)
    #: The template's search returned no images; the controller empties the table.
    searchResultsEmpty = pyqtSignal()
    #: A template was renamed: (template id, new name). The controller updates its row's name
    #: cell straight away, so the rename shows before the refreshed list arrives.
    templateRenamed = pyqtSignal(str, str)
    #: "Re-fetch whatever the processings table is showing", after an action that changed it.
    #: Which view that is depends on navigation state, so the controller decides — see
    #: `ProcessingService.refreshRequested`, which carries the same meaning from the other side.
    refreshRequested = pyqtSignal()
    #: Entering / leaving the in-template view, so map side-effects (search results, AOI layers)
    #: are handled outside the service.
    templateOpened = pyqtSignal(object)
    templateClosed = pyqtSignal(object)
    #: The template's AOIs changed (add/rename/delete/geometry) and it was re-hydrated, so
    #: listeners can redraw its map layers.
    templateAoisChanged = pyqtSignal(object)
    #: The template's full processings list arrived, so the "No AOI" map group can be set up.
    templateProcessingsLoaded = pyqtSignal(object)
    #: The in-template rows were rebuilt. The service holds no widget, so it hands the rows out
    #: and the controller writes them into the table.
    templateRowsChanged = pyqtSignal(object)
    #: The in-template view polls on its own (slower) cadence; the controller applies it.
    pollIntervalChanged = pyqtSignal(int)
    #: The processings the table is now resolving its row ids against — this template's while it
    #: is open, `None` for the project's own. `ProcessingService` turns a table selection into
    #: objects and so needs the pool, but must not reach in here for it (that reach was the
    #: `template_state` seam); it is told instead, and holds a plain dict it does not interpret.
    visibleProcessingsChanged = pyqtSignal(object)

    # Class-level defaults so the mode check is safe even when callers (and tests) construct the
    # service without running __init__.
    in_template_mode = False
    active_template = None
    _template_processings = {}

    def __init__(self,
                 app_context: AppContext,
                 processing_service,
                 plugin_dir: Optional[str] = None,
                 aoi_service=None,
                 result_loader=None,
                 search_service=None,
                 config=None):
        super().__init__()
        self.app_context = app_context
        #: For the two poll cadences (the in-template view polls slower than the project list).
        self.config = config or Config
        #: Reached for the shared `api` client, the poll timer, the project's `templates` dict and
        #: the table-selection queries that read it (`selected_template`, `selected_processing`).
        #: One-way: nothing there reaches back here.
        self.processing_service = processing_service
        #: For the .qml style paths of the template AOI/footprint layers (mirrors `AoiService`).
        self.plugin_dir = plugin_dir
        #: Reached to register a built AOI layer (area monitor / registry). Service→service.
        self.aoi_service = aoi_service
        #: Read for `add_layers_to_group` (whether the user keeps a Mapflow layer group at all).
        self.result_loader = result_loader
        #: Reached for the page size, the server-side sort and the pager — a template's results
        #: are the same result set, paged and sorted the same way, just from another endpoint.
        self.search_service = search_service
        #: The current template-search results, keyed by image id, carrying the ``isNew`` flag
        #: the seen markers read. Set when a template's results load.
        self.template_search_images = {}
        #: 'No AOI' processing ids whose per-processing AOI fetch is in flight, so a second click
        #: does not fire a duplicate request before the first returns.
        self._pending_no_aoi_ids = set()
        #: The AOI ids the in-template results are currently scoped to (None = all the
        #: template's AOIs). Only used to re-request the same scope on a page change.
        self.search_aoi_filter = None
        #: Navigation state: whether the processings table is showing a template, and which one.
        self.in_template_mode = False
        self.active_template = None
        #: The open template's rows — its AOIs keyed by table id, and its processings keyed by id.
        self.template_aois = {}
        self.template_processings = {}

    @property
    def template_processings(self):
        return self._template_processings

    @template_processings.setter
    def template_processings(self, processings):
        """Announce the pool on every assignment.

        A property rather than an emit beside each assignment: there are four of them (construct,
        enter, exit, and the fetch callback), and whoever adds a fifth would have to know to emit.
        Silence there would leave `ProcessingService` resolving row ids against a stale dict —
        selecting a row in the table and getting the wrong processing, or none."""
        self._template_processings = processings
        self.visibleProcessingsChanged.emit(processings if self.in_template_mode else None)

    # ---------- plan-search gating ----------

    def search_area_exceeds_limit(self) -> bool:
        """Whether the current AOI is too large for an immediate search (T8). Zero/unknown
        ``searchAreaLimit`` disables the check and lets the search proceed."""
        limit = self.app_context.search_area_limit
        return bool(limit and self.app_context.aoi_size and self.app_context.aoi_size > limit)

    @property
    def project_required_message(self) -> str:
        return self.tr("Select a project to create a template")

    def planned_search_default_name(self) -> str:
        """Auto-name for a Planned Search created from the too-large-AOI prompt (T8)."""
        return self.tr("Searching {datetime}").format(
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M"))

    # ---------- create ----------

    def create_search_template(self, name: str, aoi_details: Optional[dict],
                               search_params: SearchParams) -> None:
        """Create a planned search template. ``name``, ``aoi_details`` and ``search_params`` are
        assembled by the controller from the widgets; validation against the account limits and
        the request itself are here."""
        # A template always belongs to a project — block creation (but not the immediate search)
        # and tell the user, instead of sending a request the backend would reject.
        if not self.app_context.current_project:
            self.projectRequired.emit(self.project_required_message)
            alert_warning(self.project_required_message)
            return
        if not self.app_context.aoi:
            alert(self.tr('Please, select a valid area of interest'))
            return
        # Forbid creation client-side when the AOI exceeds the planned-processing area cap
        # (mirrors processing creation). Zero/unknown limit lets the backend be the source of truth.
        if self.app_context.template_area_limit and self.app_context.aoi_size \
                and self.app_context.aoi_size > self.app_context.template_area_limit:
            alert(ErrorMessage(
                code="TEMPLATE_AREA_LIMIT_EXCEEDED",
                parameters={"templateAreaLimit": round(self.app_context.template_area_limit, 2)},
            ).to_str())
            return
        if not aoi_details:
            alert(self.tr('Please, select a valid area of interest'))
            return
        if not name:
            alert(self.tr('Please, specify a name for your search'))
            return

        # Backend validates activeUntil against a strict 0-6m window; a duration cap avoids
        # edge-case rejections around month-length differences.
        active_until = datetime.utcnow() + timedelta(days=180) - timedelta(minutes=1)
        payload = CreateProcessingTemplateSchema(
            name=name,
            searchParams=search_params,
            projectId=str(self.app_context.project_id),
            activeUntil=active_until.strftime('%Y-%m-%dT%H:%M:%S.0Z'),
        )
        self.creationBusy.emit(True)
        self.statusMessage.emit(self.tr('Creating planned search...'))
        self.processing_service.api.create_template(
            data=payload,
            callback=self.create_search_template_callback,
            error_handler=self.create_search_template_error_handler,
        )

    def create_search_template_callback(self, response: QNetworkReply):
        self.creationBusy.emit(False)
        # A created template is normally active; isActive comes back False when the
        # active-templates limit is reached (created but inactivated).
        template = self.parse_template_response(response)
        if template is not None and not template.isActive:
            alert_warning(self.tr(
                "The template has been created, but is inactive.\n\n"
                "You have reached the maximum number of active planned processings. "
                "Pause or delete another one before activating this template."))
        self.refreshRequested.emit()

    def create_search_template_error_handler(self, response: QNetworkReply):
        self.creationBusy.emit(False)
        report_http_error(response,
                          plugin_version=self.app_context.plugin_version,
                          title=self.tr("Template creation failed"),
                          error_message_parser=api_message_parser)

    # ---------- update stored search params ----------

    def update_template_search_params(self, search_params: SearchParams) -> None:
        """Save the current imagery-search filter widgets to the open template's stored
        ``searchParams`` (non-geometry params only — the backend merges them and preserves the
        geometry). ``search_params`` is built with ``aoi_details=None`` by the controller."""
        template = (self.active_template
                    or self.processing_service.selected_template())
        if not template:
            return
        # Only name + searchParams change; processingParams and activeUntil are omitted so the
        # backend preserves them (sending processingParams={} would fail its required `rest`).
        payload = UpdateProcessingTemplateSchema(name=template.name, searchParams=search_params)
        self.statusMessage.emit(self.tr('Updating template search parameters...'))
        self.processing_service.api.update_template(
            template_id=template.id,
            data=payload,
            callback=self._template_updated_callback,
            error_handler=self._template_update_error_handler,
        )

    def _template_updated_callback(self, response: QNetworkReply):
        alert_info(self.tr("Template updated."))
        # Re-hydrate so the open template / list reflects the new params.
        self.aoi_changed_callback(response)
        self.refreshRequested.emit()

    def _template_update_error_handler(self, response: QNetworkReply):
        report_http_error(response,
                          plugin_version=self.app_context.plugin_version,
                          title=self.tr("Template update failed"),
                          error_message_parser=api_message_parser)

    # ---------- exclude a processing's area from the search ----------

    def exclude_processing_from_search(self) -> None:
        """'Exclude from search' — subtract a processing's footprint from the AOIs it was run
        over, so the template stops searching an already-processed area. A processing links to
        every AOI it intersects, so subtract from each; an AOI fully consumed is deleted."""
        template = self.active_template
        processing = self.processing_service.selected_processing()
        if not template or not processing:
            return
        affected = self._processing_footprints_by_aoi(template, str(processing.id))
        updates = []      # (aoi_id, new_geometry_dict)
        deletions = []    # aoi_id fully consumed
        for aoi, footprints in affected:
            aoi_geom = geometry_from_geojson(aoi.geometry)
            if aoi_geom is None:
                continue
            footprint = footprints[0] if len(footprints) == 1 else QgsGeometry.unaryUnion(footprints)
            new_geom = aoi_geom.difference(footprint)
            if new_geom is None or new_geom.isEmpty() or new_geom.area() == 0:
                deletions.append(aoi.id)
            else:
                updates.append((aoi.id, json.loads(new_geom.asJson())))
        if not updates and not deletions:
            alert_info(self.tr("This processing is not linked to any AOI geometry."))
            return
        if not alert_confirm(self.tr("Exclude this processing's area from the template's search? "
                                     "The already-processed area will be removed from the AOI(s).")):
            return
        for aoi_id, geom in updates:
            self.processing_service.api.update_aoi(
                template_id=template.id,
                aoi_id=aoi_id,
                data=UpdateAoiSchema(geometry=geom),
                callback=self.aoi_changed_callback,
                error_handler=self.aoi_change_error_handler,
            )
        if deletions:
            self.processing_service.api.delete_aois(
                template_id=template.id,
                data=DeleteAoisSchema(aoiIds=deletions),
                callback=self.aoi_changed_callback,
                error_handler=self.aoi_change_error_handler,
            )

    def _processing_footprints_by_aoi(self, template, processing_id: str):
        """For each of the template's AOIs, the QgsGeometry footprints of ``processing_id`` that
        were run over it. Returns ``[(aoi, [footprint, ...]), ...]`` for AOIs it touches."""
        result = []
        for aoi in template.aoi_dtos():
            if not aoi.id or not aoi.geometry:
                continue
            footprints = [
                geometry_from_geojson(link.geometry)
                for link in aoi.processings
                if str(link.processingId) == str(processing_id) and link.geometry
            ]
            footprints = [g for g in footprints if g is not None]
            if footprints:
                result.append((aoi, footprints))
        return result

    # ---------- seen markers (DTO state + api; the table effects are the view's) ----------

    def store_template_images(self, images) -> None:
        """The template-search results, so the seen flow can find each image's DTO by id."""
        self.template_search_images = {str(image.id): image for image in images}

    def seen_template_id(self) -> Optional[str]:
        """Id of the template whose search results are currently shown.

        NOT from the processings-table selection: inside the in-template view the selected rows
        are AOIs/processings, so a selection-derived id is None there and both Seen actions
        silently sent no request. ``open_template_results_id`` is set whenever template results
        load (entering a template and "See search results" alike)."""
        open_id = getattr(self.app_context, "open_template_results_id", None)
        if open_id:
            return str(open_id)
        template = self.active_template
        return str(template.id) if template else None

    def image_is_new(self, image_id: Optional[str]) -> bool:
        image = self.template_search_images.get(image_id)
        return bool(image is not None and image.isNew)

    def mark_image_seen(self, template_id: str, image_id: str, on_success) -> None:
        """Request 'seen' for one image, only if its DTO is still new. On success the DTO's
        ``isNew`` is cleared and the counter decremented (never optimistically); ``on_success``
        — bound by the controller to the row — clears that row's marker."""
        image = self.template_search_images.get(image_id)
        if image is None or not image.isNew:
            return
        self.processing_service.api.mark_template_image_seen(
            template_id=template_id,
            image_id=str(image_id),
            callback=lambda _response, img=image, tid=template_id: (
                self._on_image_seen(img, tid), on_success()),
            error_handler=self._seen_error_handler,
        )

    def mark_all_seen(self, template_id: str, on_success) -> None:
        """Mark every image of the shown template as seen with a single request."""
        self.processing_service.api.mark_all_template_images_seen(
            template_id=template_id,
            callback=lambda _response, tid=template_id: (self._on_all_seen(tid), on_success()),
            error_handler=self._seen_error_handler,
        )

    def _on_image_seen(self, image, template_id: str) -> None:
        image.isNew = False
        self._decrement_new_images_count(template_id)

    def _on_all_seen(self, template_id: str) -> None:
        for image in self.template_search_images.values():
            image.isNew = False
        self._reset_new_images_count(template_id)

    def _seen_error_handler(self, response: QNetworkReply) -> None:
        self.warningMessage.emit(self.tr("Could not mark image(s) as seen, please try again."))

    def _find_template(self, template_id: str):
        template_map = getattr(self.processing_service, "templates", {}) or {}
        for key, value in template_map.items():
            if str(key) == str(template_id):
                return value
        return None

    def _decrement_new_images_count(self, template_id: str) -> None:
        template = self._find_template(template_id)
        if template is None:
            return
        if template.newImagesCount and template.newImagesCount > 0:
            template.newImagesCount -= 1
        self.templateStatusChanged.emit(template)

    def _reset_new_images_count(self, template_id: str) -> None:
        template = self._find_template(template_id)
        if template is None:
            return
        template.newImagesCount = 0
        self.templateStatusChanged.emit(template)

    # ---------- template layer-tree groups (place / find / remove) ----------

    def ensure_template_group(self,
                              template_group_name: str,
                              subgroup_name: Optional[str] = None):
        """Find or create the ``Mapflow > <template> [> <subgroup>]`` group, and return the node
        new layers should be inserted into.

        For the callers that are *adding* the template's layers, and so legitimately bring the
        group into being. Everything that merely places an already-built layer wants
        ``find_template_group`` instead.

        The Mapflow group is created here when missing so the template group is nested under it
        from the very first (template-open) call. Previously the open path fell back to the root
        because the Mapflow group did not exist yet, and a later preview — by which point the
        group had been created — added a SECOND template group under it (feedback 4.1). If the
        user has deleted the Mapflow group (the result loader then adds to root), respect that
        and place template groups at the root too, keeping a single path."""
        root = self.app_context.project.layerTreeRoot()
        mapflow_group_name = self.app_context.settings.value('layerGroup') or self.app_context.plugin_name
        mapflow_group = root.findGroup(mapflow_group_name)
        if mapflow_group is None and getattr(self.result_loader, 'add_layers_to_group', True):
            mapflow_group = root.insertGroup(0, mapflow_group_name)
            self.app_context.settings.setValue('layerGroup', mapflow_group_name)
        parent_group = mapflow_group if mapflow_group else root
        template_group = parent_group.findGroup(template_group_name)
        if not template_group:
            template_group = parent_group.insertGroup(0, template_group_name)
        if subgroup_name:
            subgroup = template_group.findGroup(subgroup_name)
            if not subgroup:
                subgroup = template_group.insertGroup(0, subgroup_name)
            return subgroup
        return template_group

    def find_template_group(self,
                            template_group_name: str,
                            subgroup_name: Optional[str] = None):
        """The ``Mapflow > <template name> [> <subgroup>]`` layer-tree group, or None.

        Creates nothing. Callers that only need to *place* a layer next to the template's other
        layers use this: they run on selection changes and preview clicks, and a lookup that
        materialises a group as a side effect cannot be called on a path like that without a
        lambda to defer it."""
        mapflow_group_name = self.app_context.settings.value('layerGroup') or self.app_context.plugin_name
        return layer_utils.find_template_group(self.app_context.project, mapflow_group_name,
                                               template_group_name, subgroup_name)

    def remove_template_group(self, template_group_name: str) -> None:
        """Remove the template's layer-tree group (and its layers) from the map."""
        if not template_group_name:
            return
        root = self.app_context.project.layerTreeRoot()
        mapflow_group_name = self.app_context.settings.value('layerGroup') or self.app_context.plugin_name
        mapflow_group = root.findGroup(mapflow_group_name)
        parent_group = mapflow_group if mapflow_group else root
        template_group = parent_group.findGroup(template_group_name)
        if template_group is None:
            return
        for layer in template_group.findLayers():
            layer_id = layer.layerId()
            if layer_id:
                try:
                    self.app_context.project.removeMapLayer(layer_id)
                except (RuntimeError, KeyError):
                    pass
        parent_group.removeChildNode(template_group)

    def remove_template_aoi_subgroups(self, template_group_name: str) -> None:
        """Remove the per-AOI subgroups (and their layers) under the template group, keeping
        the search-results footprint layer that sits directly in the template group."""
        if not template_group_name:
            return
        root = self.app_context.project.layerTreeRoot()
        mapflow_group_name = self.app_context.settings.value('layerGroup') or self.app_context.plugin_name
        mapflow_group = root.findGroup(mapflow_group_name)
        parent_group = mapflow_group if mapflow_group else root
        template_group = parent_group.findGroup(template_group_name)
        if template_group is None:
            return
        for child in list(template_group.children()):
            # AOI subgroups are groups; the search-footprints node is a layer — leave it.
            if isinstance(child, QgsLayerTreeGroup):
                for layer in child.findLayers():
                    layer_id = layer.layerId()
                    if layer_id:
                        try:
                            self.app_context.project.removeMapLayer(layer_id)
                        except (RuntimeError, KeyError):
                            pass
                template_group.removeChildNode(child)

    # ---------- building the template's AOI / footprint layers ----------

    def add_geojson_aoi_layer(self,
                              features: list,
                              layer_name: str,
                              style_name: str,
                              template_group_name: Optional[str] = None,
                              subgroup_name: Optional[str] = None,
                              reference_layer_id: Optional[str] = None,
                              aoi_id: Optional[str] = None) -> Optional[QgsVectorLayer]:
        if not features:
            return None
        aoi_layer = QgsVectorLayer('Polygon?crs=epsg:4326', layer_name, 'memory')
        # Tag the AOI's own polygon layer with its id so "Update selected AOI" can find and edit
        # this exact layer in place (processing-footprint layers are left untagged).
        if aoi_id is not None:
            aoi_layer.setCustomProperty('mapflow/aoi_id', str(aoi_id))
        provider = aoi_layer.dataProvider()
        qgs_features = []
        for feature in features:
            geom_dict = feature.get("geometry")
            if not geom_dict:
                continue
            try:
                ogr_geom = ogr.CreateGeometryFromJson(json.dumps(geom_dict))
                if not ogr_geom:
                    continue
                qgs_geom = QgsGeometry.fromWkt(ogr_geom.ExportToWkt())
                qgs_feat = QgsFeature()
                qgs_feat.setGeometry(qgs_geom)
                qgs_features.append(qgs_feat)
            except Exception as e:
                # Per-feature, inside a loop: no traceback, or one malformed response
                # buries the panel in near-identical stack dumps.
                logger.warning("Skipping a search feature that failed to parse: %s", e)
                continue
        if not qgs_features:
            return None
        provider.addFeatures(qgs_features)
        aoi_layer.updateExtents()

        root = self.app_context.project.layerTreeRoot()
        if template_group_name:
            target_group = self.ensure_template_group(template_group_name, subgroup_name)
            self.app_context.project.addMapLayer(aoi_layer, addToLegend=False)
            target_group.insertLayer(0, aoi_layer)
        elif reference_layer_id:
            root = self.app_context.project.layerTreeRoot()
            ref_node = root.findLayer(reference_layer_id)
            if ref_node and ref_node.parent():
                self.app_context.project.addMapLayer(aoi_layer, addToLegend=False)
                ref_node.parent().insertLayer(0, aoi_layer)
            else:
                self.app_context.project.addMapLayer(aoi_layer)
        else:
            self.app_context.project.addMapLayer(aoi_layer)

        aoi_layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', style_name))
        # Template AOI layers are added in bulk on open; don't fire a cost request per layer,
        # and don't let them become the current processing Area (feedback 8.1) — the Area is
        # set from the AOI table selection (see sync_processing_area_to_selected_aois).
        self.aoi_service.register_layer(aoi_layer, recompute_cost=False, set_current=False)
        return aoi_layer

    def load_template_layers(self, template) -> None:
        """Draw, per AOI, a subgroup named after the AOI containing the AOI polygon (blue)
        and each of its processings' footprints (green), all from the template's
        ``aoiDetails`` (no extra requests)."""
        if not template:
            return
        template_group_name = str(template.name)
        for aoi in template.aoi_dtos():
            subgroup_name = self.tr("AOI: {name}").format(name=aoi.display_name)
            if aoi.geometry:
                self.add_geojson_aoi_layer(
                    features=[{"type": "Feature", "geometry": aoi.geometry, "properties": {}}],
                    layer_name=aoi.display_name,
                    style_name='aoi_template_blue.qml',
                    template_group_name=template_group_name,
                    subgroup_name=subgroup_name,
                    aoi_id=aoi.id,
                )
            for link in aoi.processings:
                if not link.geometry:
                    continue
                self.add_geojson_aoi_layer(
                    features=[{"type": "Feature", "geometry": link.geometry, "properties": {}}],
                    layer_name=link.processingName or str(link.processingId),
                    style_name='aoi_template_processing_green.qml',
                    template_group_name=template_group_name,
                    subgroup_name=subgroup_name,
                )

    # ---------- 'No AOI' processings: lazy per-processing AOI fetch + draw ----------

    def no_aoi_subgroup_name(self) -> str:
        return self.tr("No AOI")

    def no_aoi_aoi_on_map(self, pid) -> bool:
        """Whether a 'No AOI' processing's AOI layer (tagged with its id) is already on the map."""
        return any(layer.customProperty('mapflow/no_aoi_processing_id') == str(pid)
                   for layer in self.app_context.project.mapLayers().values())

    def load_no_aoi_processing_aoi(self, processing) -> None:
        """Fetch a 'No AOI' processing's AOI (absent from aoiDetails) and add it to the template's
        'No AOI' group. No-op for a bound processing, one whose AOI is already on the map, or one
        whose request is already in flight (a second click before the first returns)."""
        if not processing:
            return
        pid = str(processing.id)
        if not self.is_no_aoi_processing(pid):
            return
        if pid in self._pending_no_aoi_ids or self.no_aoi_aoi_on_map(pid):
            return
        self._pending_no_aoi_ids.add(pid)
        self.processing_service.api.get_processing_aois(
            processing_id=pid,
            callback=self._add_no_aoi_processing_aoi_callback,
            callback_kwargs={'pid': pid, 'name': processing.name},
            error_handler=self._add_no_aoi_processing_aoi_error,
            error_handler_kwargs={'pid': pid},
        )

    def _add_no_aoi_processing_aoi_callback(self, response: QNetworkReply, pid: str, name: str) -> None:
        self._pending_no_aoi_ids.discard(pid)
        template = self.active_template
        if not template or not self.in_template_mode or self.no_aoi_aoi_on_map(pid):
            return
        # GET /processings/{id}/aois returns a JSON list of AOI objects (each with a `geometry`),
        # not a FeatureCollection — wrap each geometry into a feature the layer builder understands.
        try:
            aois = json.loads(response.readAll().data())
        except ValueError:
            # Not JSON, or not decodable as UTF-8 (UnicodeDecodeError is a ValueError).
            return
        if isinstance(aois, dict):
            aois = aois.get('aois', [])
        features = [{"type": "Feature", "geometry": aoi.get("geometry"), "properties": {}}
                    for aoi in aois if isinstance(aoi, dict) and aoi.get("geometry")]
        if not features:
            return
        layer = self.add_geojson_aoi_layer(
            features=features,
            layer_name=name or pid,
            style_name='aoi_template_processing_green.qml',
            template_group_name=str(template.name),
            subgroup_name=self.no_aoi_subgroup_name(),
        )
        if layer is not None:
            layer.setCustomProperty('mapflow/no_aoi_processing_id', str(pid))

    def _add_no_aoi_processing_aoi_error(self, response: QNetworkReply, pid: str = None) -> None:
        self._pending_no_aoi_ids.discard(pid)

    # ---------- template details ----------

    def show_template_details(self, template) -> None:
        """Show a template summary. The processings count is fetched from the ``/processings``
        endpoint (aoiDetails links are not always populated)."""
        self.processing_service.api.get_template_processings(
            template_id=template.id,
            callback=lambda response: self._show_template_details_callback(template, response),
        )

    def _show_template_details_callback(self, template, response: QNetworkReply) -> None:
        try:
            data = json.loads(response.readAll().data())
            items = data.get("results") if isinstance(data, dict) else data
            linked_count = len([i for i in (items or []) if isinstance(i, dict)])
        except (ValueError, TypeError):
            # Not JSON (ValueError, which UnicodeDecodeError subclasses), or a payload whose
            # `results` is not iterable.
            linked_count = 0
        new_images = template.newImagesCount or 0
        local_created_at = template.createdAt.astimezone()
        local_active_until = template.activeUntil.astimezone()

        details = self.tr(
            "<b>{name}</b><br/>"
            "<b>Status:</b> {status}<br/>"
            "<b>Created:</b> {created}<br/>"
            "<b>Active Until:</b> {active_until}<br/>"
            "<b>Linked processings:</b> {linked}<br/>"
            "<b>New images:</b> {new_images}"
        ).format(
            name=template.name,
            status=template.status,
            created=local_created_at.strftime('%Y-%m-%d %H:%M'),
            active_until=local_active_until.strftime('%Y-%m-%d %H:%M'),
            linked=linked_count,
            new_images=new_images,
        )

        alert_info(details)

    # ---------- the in-template view: entering, leaving, and its rows ----------
    #
    # The processings table serves two views and this owns one of them. It writes no widget: the
    # rebuilt rows leave as `templateRowsChanged` and `ProjectProcessingController` puts them in
    # the table, the same way it already decides which of the two views to refresh.

    @staticmethod
    def _template_has_aoi(template) -> bool:
        try:
            return bool(template.aoi_dtos())
        except (AttributeError, TypeError):
            # `searchParams`/`aoiDetails` arriving as something other than a mapping: the
            # accessors raise AttributeError, and a non-list `features` raises TypeError when
            # iterated. Either way the template has no AOIs we can show.
            return False

    @staticmethod
    def parse_template_response(response: QNetworkReply):
        """Parse a ``GET /processings/template/{id}`` response into a ProcessingTemplateDTO."""
        try:
            data = json.loads(response.readAll().data())
            if isinstance(data, dict) and "template" in data:
                return ProcessingTemplateDetails.from_dict(data).template
            if isinstance(data, dict):
                return ProcessingTemplateDTO.from_dict(data)
        except ValueError:
            # Not JSON, or not decodable as UTF-8 (UnicodeDecodeError is a ValueError).
            return None
        return None

    def hydrate_template(self, template, callback) -> None:
        """Ensure the template carries its ``aoiDetails`` (the project poll omits them),
        then invoke ``callback(hydrated_template)``."""
        if self._template_has_aoi(template):
            callback(template)
            return
        self.processing_service.api.get_template(
            template_id=template.id,
            callback=lambda response: callback(self.parse_template_response(response) or template),
        )

    def enter_template_view(self, template) -> None:
        """Open a template ('one step right'): show its AOIs + launched processings.

        The project-scoped poll omits ``searchParams``; hydrate the template by id first
        when its AOIs are missing, then enter.
        """
        self.hydrate_template(template, self._hydrate_and_enter)

    def _hydrate_and_enter(self, template) -> None:
        if template is not None:
            self.processing_service.templates[template.id] = template
        self._do_enter_template(template)

    def _do_enter_template(self, template) -> None:
        self.in_template_mode = True
        self.active_template = template
        self.template_aois = {aoi.table_id: aoi for aoi in template.aoi_dtos()}
        self.template_processings = {}
        self._rebuild_template_rows()
        # Fetch the full processings (with result layers) for double-click loading.
        self._fetch_template_processings()
        # Poll the in-template view less aggressively than the project list.
        self.pollIntervalChanged.emit(self.config.TEMPLATE_TABLE_REFRESH_INTERVAL * 1000)
        # Map side-effects (search results + AOI layers) are handled by listeners.
        self.templateOpened.emit(template)

    def exit_template_view(self) -> None:
        """Leave the template ('one step left'): return to the project's processings."""
        closed = self.active_template
        self.in_template_mode = False
        self.active_template = None
        self.template_processings = {}
        self.template_aois = {}
        # Restore the regular (faster) project-list poll cadence.
        self.pollIntervalChanged.emit(self.config.PROCESSING_TABLE_REFRESH_INTERVAL * 1000)
        # Let listeners clean up the template's map layers / search table.
        self.templateClosed.emit(closed)

    def refresh_template_view(self) -> None:
        """Poll tick: refresh only the processings (status/progress + the unbound section).

        The AOI grouping (``aoiDetails`` from the full template) changes slowly and is
        re-hydrated on enter and after AOI edits — NOT every tick — so a poll is a single
        ``/processings`` request rather than three. AOI statuses are kept current by syncing
        them from the polled processings (see ``_sync_aoi_statuses_from_processings``).
        """
        if self.active_template:
            self._fetch_template_processings()

    def refresh_active_template(self) -> None:
        """Re-hydrate the active template's ``aoiDetails`` and its processings, then rebuild
        the grouped rows. Used after starting a template processing so the new processing is
        bound to its AOI instead of appearing under 'No AOI' (feedback 8.2)."""
        if not self.active_template:
            return
        self.processing_service.api.get_template(
            template_id=self.active_template.id,
            callback=self._reopen_template_callback,
        )
        self._fetch_template_processings()

    def _rebuild_template_rows(self) -> None:
        if not self.active_template:
            return
        self.template_aois = {aoi.table_id: aoi for aoi in self.active_template.aoi_dtos()}
        self._sync_aoi_statuses_from_processings()
        self.templateRowsChanged.emit(self.combined_template_rows())

    def _sync_aoi_statuses_from_processings(self) -> None:
        """Refresh each AOI's processing-link statuses from the latest polled processings, so
        the AOI aggregate status is current without re-fetching the full template each tick."""
        for aoi in self.template_aois.values():
            for link in aoi.processings:
                full = self.template_processings.get(str(link.processingId))
                if full is not None:
                    try:
                        link.processingStatus = full.status.value
                    except AttributeError:
                        pass

    def _fetch_template_processings(self) -> None:
        """Fetch the template's processings (v1 ``ProcessingJson``) for the full row data
        (model, progress, status, result layers) and the unbound ('No AOI') section."""
        if not self.active_template:
            return
        self.processing_service.api.get_template_processings(
            template_id=self.active_template.id,
            callback=self.get_template_processings_callback,
        )

    def get_template_processings_callback(self, response: QNetworkReply) -> None:
        """Store the template's full processings (keyed by id) and re-render the rows."""
        try:
            data = json.loads(response.readAll().data())
        except ValueError:
            data = []
        items = data.get("results") if isinstance(data, dict) else data
        processings = {}
        for item in items or []:
            if not isinstance(item, dict):
                continue
            try:
                processing = TemplateProcessingSchema.from_dict(item)
            except (TypeError, ValueError, KeyError):
                continue
            processings[str(processing.id)] = processing
        self.template_processings = processings
        if self.in_template_mode:
            self._rebuild_template_rows()
            self.templateProcessingsLoaded.emit(self.active_template)

    def template_processing(self, processing_id: str):
        """Full processing (with layers) for a grouped AOI-processing row, by id."""
        return self.template_processings.get(str(processing_id))

    def combined_template_rows(self):
        """Grouped layout: each AOI row (color-coded) followed by its processings, then the
        next AOI; finally a 'No AOI' separator and any processings attached to the template
        but not intersecting an AOI (absent from aoiDetails).

        Processing rows use the full ``TemplateProcessingSchema`` (model/progress/status)
        when loaded, falling back to the lighter aoiDetails link until then.
        """
        rows = []
        bound_ids = set()
        for aoi in self.template_aois.values():
            rows.append(aoi)
            for link in aoi.processings:
                pid = str(link.processingId) if link.processingId else ""
                if pid:
                    bound_ids.add(pid)
                full = self.template_processings.get(pid)
                rows.append(full if full is not None else link)
        unbound = [p for pid, p in self.template_processings.items() if pid not in bound_ids]
        if unbound:
            rows.append(NoAoiProcessingsRow())
            rows.extend(unbound)
        return rows

    def no_aoi_processing_ids(self) -> set:
        """IDs of the template's processings not bound to any AOI (omitted from aoiDetails)."""
        bound = {str(link.processingId)
                 for aoi in self.template_aois.values()
                 for link in aoi.processings if link.processingId}
        return {pid for pid in self.template_processings if pid not in bound}

    def is_no_aoi_processing(self, processing_id) -> bool:
        return str(processing_id) in self.no_aoi_processing_ids()

    # ---------- what the table selection means for templates ----------

    def _selected_ids(self, limit=None):
        return self.processing_service.view.selected_processing_ids(limit=limit)

    def selected_aois(self, limit=None) -> list:
        """Selected AOI rows (only meaningful inside the in-template view)."""
        pids = self._selected_ids(limit=limit)
        return [self.template_aois[pid] for pid in self.template_aois if pid in pids]

    def selected_aoi(self):
        first = self.selected_aois(limit=1)
        return first[0] if first else None

    # `selected_template(s)`, `is_only_templates_selected` and `template_to_run` stay on
    # `ProcessingService`: they read its `templates` dict, which its own project fetch fills, and
    # `template_to_run` is what the start path forks on. Moving them means moving that fork too —
    # see the "Extract processing lifecycle" step, which is where it belongs.

    # ---------- the template's AOIs: rename, delete, and re-hydrate after a change ----------

    def rename_aoi(self) -> None:
        """Rename the selected AOI via the per-AOI update endpoint."""
        aoi = self.selected_aoi()
        template = self.active_template
        if not aoi or not template:
            return
        if not aoi.can_rename:
            alert_info(self.tr("This AOI has no id yet and cannot be renamed. "
                               "Reopen the template and try again."))
            return
        new_name, ok = ask_text(self.tr("Rename AOI"), self.tr("AOI name:"),
                                default=str(aoi.name or ""))
        if not ok:
            return
        new_name = (new_name or "").strip()
        if not new_name:
            alert_warning(self.tr("Please, specify AOI name"))
            return
        if len(new_name) > AOI_NAME_MAX_LENGTH:
            alert_warning(self.tr("AOI name must not exceed {limit} characters").format(
                limit=AOI_NAME_MAX_LENGTH))
            return
        if new_name == (aoi.name or ""):
            return
        self.processing_service.api.update_aoi(
            template_id=template.id,
            aoi_id=aoi.id,
            data=UpdateAoiSchema(name=new_name),
            callback=self.aoi_changed_callback,
            error_handler=self.aoi_change_error_handler,
        )

    def delete_aoi(self) -> None:
        """Delete the selected AOI(s) from the active template."""
        template = self.active_template
        if not template:
            return
        deletable = [a for a in self.selected_aois() if a.can_rename]
        if not deletable:
            return
        if not alert_confirm(self.tr("Delete selected AOI(s)?")):
            return
        self.processing_service.api.delete_aois(
            template_id=template.id,
            data=DeleteAoisSchema(aoiIds=[a.id for a in deletable]),
            callback=self.aoi_changed_callback,
            error_handler=self.aoi_change_error_handler,
        )

    def aoi_changed_callback(self, response: QNetworkReply) -> None:
        """After an AOI add/rename/delete, re-hydrate the template (so names/ids are fresh)."""
        if self.active_template:
            self.processing_service.api.get_template(
                template_id=self.active_template.id,
                callback=self._reopen_template_callback,
            )

    def _reopen_template_callback(self, response: QNetworkReply) -> None:
        try:
            hydrated = self.parse_template_response(response)
            if hydrated is not None:
                self.active_template = hydrated
                self.processing_service.templates[hydrated.id] = hydrated
        except Exception:
            logger.exception("Could not hydrate template details from response")
        if self.in_template_mode and self.active_template:
            self.template_aois = {aoi.table_id: aoi for aoi in self.active_template.aoi_dtos()}
            self.templateRowsChanged.emit(self.combined_template_rows())
            # Redraw the template's AOI/processing map layers to reflect the AOI change.
            self.templateAoisChanged.emit(self.active_template)

    def aoi_change_error_handler(self, response) -> None:
        alert(self.tr("AOI update failed: {}").format(self._error_text(response)))

    # ---------- run-state actions on the selected template ----------
    #
    # Each is the same shape: take the selected template, call the endpoint, say what happened and
    # refresh the list. The refresh is best-effort — the 6 s processing poll calls
    # `get_processings` again anyway — and the success message is unconditional because a refusal
    # would have gone to the error handler instead.

    def rename_template(self) -> None:
        """Rename the selected template. The new name is asked for through the message tier, so
        this holds no dialog of its own (`spec/007_architecture.md` § Layer rules)."""
        template = self.processing_service.selected_template()
        if not template:
            return
        new_name, ok = ask_text(self.tr("Rename template"),
                                self.tr("Template name:"),
                                default=str(template.name or ""))
        if not ok:
            return
        new_name = (new_name or "").strip()
        if not new_name:
            alert_warning(self.tr("Please, specify template name"))
            return
        if new_name == template.name:
            return
        payload = UpdateProcessingTemplateSchema(
            name=new_name,
            # Rename-only flow: do not send searchParams to avoid geometry update rejection.
            searchParams=None,
            # Keep processing params unchanged on backend; omit field to avoid decoding issues
            processingParams=None,
            activeUntil=None,
        )
        self.processing_service.api.update_template(
            template_id=template.id,
            data=payload,
            callback=self.rename_template_callback,
            error_handler=self.rename_template_error_handler,
        )

    def rename_template_callback(self, response: QNetworkReply) -> None:
        try:
            response_data = json.loads(response.readAll().data())
        except ValueError:
            # Not JSON, or not decodable as UTF-8 (UnicodeDecodeError is a ValueError).
            response_data = {}
        template_data = response_data.get("template", response_data)
        try:
            if isinstance(template_data, dict) and template_data.get("id"):
                updated_template = ProcessingTemplateDTO.from_dict(template_data)
                self.processing_service.templates[updated_template.id] = updated_template
                self.templateRenamed.emit(str(updated_template.id), str(updated_template.name))
        except Exception:
            logger.exception("Could not apply renamed template from response")
        self.refreshRequested.emit()

    def rename_template_error_handler(self, response: QNetworkReply) -> None:
        alert(self.tr("Error renaming template: {}").format(self._error_text(response)))

    def pause_template(self) -> None:
        template = self.processing_service.selected_template()
        if not template:
            return
        if not template.isActive:
            alert_info(self.tr("Template is not active"))
            return
        self.processing_service.api.stop_template(
            template_id=template.id,
            callback=self.pause_template_callback,
            error_handler=self.pause_template_error_handler)

    def pause_template_callback(self, response: QNetworkReply) -> None:
        alert_info(self.tr("Template paused successfully"))
        self.refreshRequested.emit()

    def pause_template_error_handler(self, response: QNetworkReply) -> None:
        alert(self.tr("Error pausing template: {}").format(self._error_text(response)))

    def resume_template(self) -> None:
        template = self.processing_service.selected_template()
        if not template:
            return
        if template.isActive:
            alert_info(self.tr("Template is already active"))
            return
        # Held across the two requests: resuming is a POST that carries no body, so the follow-up
        # PUT that extends activeUntil needs the name from before.
        self._resume_template_state = {
            'template_id': template.id,
            'template_name': template.name,
        }
        self.processing_service.api.resume_template(
            template_id=template.id,
            callback=self.resume_template_update_active_until,
            error_handler=self.resume_template_error_handler)

    def resume_template_update_active_until(self, response: QNetworkReply) -> None:
        """After resume succeeds, extend activeUntil to 6 months from now."""
        state = getattr(self, '_resume_template_state', {}) or {}
        template_id = state.get('template_id')
        template_name = state.get('template_name')
        if not template_id or not template_name:
            self.resume_template_callback(response)
            return
        active_until = datetime.utcnow() + timedelta(days=180) - timedelta(minutes=1)
        payload = UpdateProcessingTemplateSchema(
            name=template_name,
            searchParams=None,
            processingParams=None,
            activeUntil=active_until.strftime('%Y-%m-%dT%H:%M:%S.0Z'),
        )
        self.processing_service.api.update_template(
            template_id=template_id,
            data=payload,
            callback=self.resume_template_callback,
            error_handler=self.resume_template_error_handler,
        )

    def resume_template_callback(self, response: QNetworkReply) -> None:
        self._resume_template_state = {}
        alert_info(self.tr("Template resumed successfully"))
        self.refreshRequested.emit()

    def resume_template_error_handler(self, response: QNetworkReply) -> None:
        """e.g. "maximum number of active templates"."""
        self._resume_template_state = {}
        alert(self.tr("Error resuming template: {}").format(self._error_text(response)))

    def restart_template(self) -> None:
        template = self.processing_service.selected_template()
        if not template:
            return
        if not template.is_failed:
            alert_info(self.tr("Only failed templates can be restarted"))
            return
        self.processing_service.api.restart_template(
            template_id=template.id,
            callback=self.restart_template_callback,
            error_handler=self.restart_template_error_handler,
        )

    def restart_template_callback(self, response: QNetworkReply) -> None:
        alert_info(self.tr("Template restarted successfully"))
        self.refreshRequested.emit()

    def restart_template_error_handler(self, response: QNetworkReply) -> None:
        alert(self.tr("Error restarting template: {}").format(self._error_text(response)))

    def _error_text(self, response) -> str:
        """Resolve a template/AOI action error response to a meaningful, translatable message.

        The error handlers receive a ``QNetworkReply``; parse its body through the central error
        registry (e.g. a generic ``BAD_REQUEST`` with "You have reached the maximum number of
        active templates" maps to a translated description) rather than formatting the raw reply
        object (which produced an empty/garbled message box)."""
        try:
            body = response.readAll().data().decode()
        except (AttributeError, RuntimeError, UnicodeDecodeError):
            # No reply object, its C++ side is gone, or the body is not UTF-8.
            return self.tr("Unknown server error")
        # api_message_parser handles its own parse failures and returns None.
        return api_message_parser(body) or self.tr("Unknown server error")

    # ---------- the template's imagery-search results ----------

    def load_search(self, template, aoi_ids=None, offset: int = 0) -> None:
        """Fetch the template's search results into the shared imagery-search result set.

        ``aoi_ids`` restricts the results to specific AOIs (S7: filter by selected AOI); when
        ``None`` all of the template's AOIs are used. ``offset`` selects the page: entering a
        template or changing the AOI filter resets to the first page (offset 0); the search pager
        passes a page offset (T6).

        Bringing the search tab to front is the caller's business, not this one's — only the
        explicit "See search results" action does it, and that is a view effect.
        """
        if not template:
            return
        self.search_service.page_offset = max(0, offset)
        if aoi_ids is None:
            aoi_ids = self._aoi_ids_from_template(template)
        # Template results are fetched WITHOUT date/cloud server-side filters: those (and the
        # intersection %) are applied instantly on the client (apply_local_filter). Persisting
        # them to the template is done separately via the "Update template" button. Only the
        # selected-AOI scoping (aoi_ids) stays server-side (it decides which AOIs to search).
        self.processing_service.api.get_template_images(
            template_id=template.id,
            callback=lambda response: self.search_results_callback(response, template),
            limit=self.search_service.page_limit,
            offset=self.search_service.page_offset,
            aoi_ids=aoi_ids or None,
            sort_by=self.search_service.sort_by,
            sort_order=self.search_service.sort_order,
        )

    def load_search_page(self, offset: int) -> None:
        """Re-fetch the active template's search results at ``offset``, preserving the current
        AOI filter — the search pager's next/prev and a header re-sort inside a template (T6)."""
        template = self.active_template
        if not template:
            return
        aoi_ids = list(self.search_aoi_filter) if self.search_aoi_filter else None
        self.load_search(template, aoi_ids=aoi_ids, offset=offset)

    def filter_search_by_selected_aois(self) -> None:
        """S7: scope the in-template search results to the AOIs currently selected; de-selecting
        all of them (or selecting a processing) restores all of the template's results.

        The caller checks that a template is open — this reloads only when the effective filter
        actually changed, because a selection signal fires on every click.
        """
        template = self.active_template
        if not template:
            return
        selected_ids = frozenset(
            str(aoi.id) for aoi in self.selected_aois() if aoi and aoi.id
        )
        if selected_ids == (self.search_aoi_filter or frozenset()):
            return
        self.search_aoi_filter = selected_ids or None
        self.load_search(template, aoi_ids=list(selected_ids) or None)

    def search_results_callback(self, response: QNetworkReply, template=None) -> None:
        """Turn a template-images response into the shared search result set.

        ``template`` is passed explicitly because inside the in-template view the table selection
        points at AOIs/processings, not at the template row.
        """
        response_json = json.loads(response.readAll().data())
        if not response_json.get("images"):
            self.app_context.open_template_results_id = None
            # Empty the table before the modal, so the user is not reading stale rows behind it.
            self.searchResultsEmpty.emit()
            alert_info(self.tr("No images was found"))
            return
        if template is None:
            template = self.processing_service.selected_template()
        template_group_name = str(template.name) if template else None
        # Mark these results as belonging to this template, so a "Start" runs a planned processing.
        self.app_context.open_template_results_id = str(template.id) if template else None
        response_data = ImageCatalogResponseSchema(**response_json)
        images = response_data.images
        geoms = response_data.as_geojson()
        # Template search images may omit per-image providerName; without it a planned
        # processing (and its cost) cannot resolve `dataProvider` and the backend rejects the
        # request. Backfill from the template's own searchParams.dataProviders when it searches
        # a single provider (multi-provider templates rely on the backend providing it).
        template_provider = self._single_data_provider(template)
        for position, feature in enumerate(geoms.get("features", ())):
            props = feature.setdefault("properties", {})
            props["local_index"] = position
            if not props.get("providerName") and template_provider:
                props["providerName"] = template_provider
        # Footprints must keep the real providerName/productType so that a planned
        # processing started from these results can resolve its source params (dataProvider).
        self.store_search_footprints(geoms, template_group_name=template_group_name)
        # Retain the raw results (for the instant local filter) and the template's own params as
        # the widen (!) baseline; template results are filtered client-side, not server-side.
        self.app_context.search_result_geojson = geoms
        self.app_context.search_baseline_filters = self.filter_baseline(template)
        # The image DTOs (they carry isNew) are keyed by id before the table is filled, because
        # filling it is what draws the new-image markers, and those read this map.
        self.store_template_images(images)
        self.searchResultsReady.emit(geoms)
        # Toggle/wire the search pager for the template results (T6).
        self.search_service.update_pager(response_data.total, response_data.limit,
                                         response_data.offset)

    def _aoi_ids_from_template(self, template) -> list:
        """The AOI ids in a template's ``searchParams.aoiDetails`` features."""
        search_params = template.searchParams or {}
        if isinstance(search_params, dict):
            aoi_details = search_params.get("aoiDetails", {})
        else:
            aoi_details = search_params.aoiDetails

        if not aoi_details:
            return []

        ids = []
        for feature in aoi_details.get("features", []):
            aoi_id = feature.get("id") or feature.get("properties", {}).get("id")
            if aoi_id:
                ids.append(str(aoi_id))
        return ids

    def _single_data_provider(self, template) -> Optional[str]:
        """The template's sole search data provider, used to backfill an image's providerName
        when the backend returns it null. ``None`` when the template searches zero or several
        providers (then we cannot attribute an image to one)."""
        if not template:
            return None
        search_params = getattr(template, "searchParams", None)
        if isinstance(search_params, SearchParams):
            providers = search_params.dataProviders
        elif isinstance(search_params, dict):
            providers = search_params.get("dataProviders")
        else:
            providers = None
        providers = [p for p in (providers or []) if p]
        return providers[0] if len(providers) == 1 else None

    def filter_baseline(self, template) -> Optional[dict]:
        """Baseline (widen indicator + Reset filters) from a template's stored searchParams. A
        field the template does not carry stays ``None`` so Reset leaves that widget untouched."""
        sp = getattr(template, "searchParams", None)
        if not sp:
            return None
        if isinstance(sp, dict):
            sp = SearchParams.from_dict(sp)
        return {
            "date_from": utc_date_from_iso(sp.acquisitionDateFrom),
            "date_to": utc_date_from_iso(sp.acquisitionDateTo),
            "max_cloud_cover": sp.maxCloudCover,
            "min_intersection": sp.minAoiIntersectionPercent,
            "min_off_nadir": sp.minOffNadirAngle,
            "max_off_nadir": sp.maxOffNadirAngle,
            "product_types": ([str(pt).upper() for pt in sp.productTypes]
                              if sp.productTypes is not None else None),
            "data_providers": list(sp.dataProviders) if sp.dataProviders is not None else None,
            "hide_unavailable": sp.hideUnavailable,
        }

    def clear_search_state(self) -> None:
        """Forget the template's results on leaving it, so nothing leaks into the project view."""
        self.app_context.open_template_results_id = None
        self.search_aoi_filter = None
        self.app_context.search_result_geojson = None
        self.app_context.search_baseline_filters = None
        # Clear the template search-results pagination so it is not preserved on re-open.
        self.search_service.page_offset = 0

    def store_search_footprints(self,
                                geoms: dict,
                                template_group_name: Optional[str] = None) -> None:
        """Build the template search-results footprint layer.

        Two responsibilities, mirroring a regular imagery search:
        * populate ``app_context.search_footprints`` (QgsFeatures keyed by ``local_index``)
          so a planned processing started from these results resolves its source params
          (``dataProvider`` comes from the footprint ``providerName``; otherwise the
          backend rejects creation with HTTP 400);
        * add the styled footprint layer to the map under the template's group so the
          user can preview image footprints and request imagery previews.
        """
        self.app_context.search_footprints = {}
        provider = self.search_service.imagery_search_provider
        if not provider:
            return
        filename = provider.save_search_layer(self.app_context.temp_dir, geoms)
        if not filename:
            return
        # `SearchService` owns the footprints layer itself (spec/007 § Services); what is a
        # template concern is only where the layer ends up in the tree, which is what `place` says.
        # Wiring the layer's selection to the table is `SearchService.metadataLayerReady`'s job for
        # both searches now; emitting a second signal here connected it twice, so one footprint
        # click previewed twice.
        self.search_service.build_metadata_layer(
            filename, f"{provider.name} metadata",
            place=lambda built: self.place_in_template_group(built, template_group_name))

    def place_preview_layer(self, layer) -> None:
        """Move a freshly added preview layer into the open template's group, above the
        search-results footprints and below the AOI subgroups, so the precedence is
        AOIs (top) > previews > search results (bottom). No-op outside a template."""
        if not layer or not self.in_template_mode or not self.active_template:
            return
        try:
            template_group = self.find_template_group(str(self.active_template.name))
            root = self.app_context.project.layerTreeRoot()
            node = root.findLayer(layer.id())
            if node is None or template_group is None:
                return
            footprints_layer = getattr(self.app_context, 'metadata_layer', None)
            footprints_id = footprints_layer.id() if footprints_layer else None
            children = template_group.children()
            # Default to the bottom; otherwise insert directly above the footprints layer
            # (which itself sits below the AOI/processing subgroups).
            insert_index = len(children)
            for i, child in enumerate(children):
                if isinstance(child, QgsLayerTreeLayer) and child.layerId() == footprints_id:
                    insert_index = i
                    break
            template_group.insertChildNode(insert_index, node.clone())
            (node.parent() or root).removeChildNode(node)
        except (AttributeError, RuntimeError):
            return

    def place_in_template_group(self, layer, template_group_name: Optional[str] = None) -> None:
        """Put a built layer inside the open template's group. Where a layer sits among a
        template's layers is a template concern, so the services that build one hand it here
        rather than reaching for the group themselves."""
        if not template_group_name:
            self.result_loader.add_layer(layer=layer)
            return
        target_group = self.ensure_template_group(template_group_name)
        self.app_context.project.addMapLayer(layer, addToLegend=False)
        # Append (bottom) so the search-results footprints sit below the AOI/processing
        # subgroups rather than on top of them.
        target_group.addLayer(layer)
