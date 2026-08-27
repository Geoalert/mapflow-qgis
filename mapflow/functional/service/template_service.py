"""Planned processings (templates): creation, search-param update, exclude-from-search, the
seen-image markers, and the template's map layers.

This is MR-1 of the templates extraction — the half that was tangled into `mapflow.py`. The
lifecycle half (enter/exit/pause/resume, navigation state) is still in `ProcessingService` and is
read from there for now; MR-2 moves it here.

Holds no widget (`spec/007_architecture.md` § Layer rules). Inputs that come from widgets — the
template name, the assembled `SearchParams`, the AOI FeatureCollection — arrive as arguments from
`TemplateController`; UI effects the service must cause (the busy button, the "select a project"
label) leave as signals. The map layers a template draws are QGIS layer-tree work, not widgets, so
they live here alongside `AoiService`/`PreviewService`'s own layer building. `ProcessingService` is
read for navigation state and reached for its `api`; that dependency becomes `TemplateService`'s
own in MR-2.
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
                       QgsVectorLayer)

from .. import layer_utils
from ..app_context import AppContext
from ..geometry import geometry_from_geojson
from .alert_service import (alert, alert_confirm, alert_info, alert_warning,
                            report_http_error)
from ...errors import ErrorMessage
from ...http import api_message_parser
from ...schema.template import (CreateProcessingTemplateSchema,
                                DeleteAoisSchema,
                                SearchParams,
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

    def __init__(self,
                 app_context: AppContext,
                 processing_service,
                 plugin_dir: Optional[str] = None,
                 aoi_service=None,
                 result_loader=None):
        super().__init__()
        self.app_context = app_context
        #: Read for navigation state (`active_template`, `selected_template`,
        #: `selected_processing`) and reached for `api`. MR-2 gives TemplateService its own.
        self.processing_service = processing_service
        #: For the .qml style paths of the template AOI/footprint layers (mirrors `AoiService`).
        self.plugin_dir = plugin_dir
        #: Reached to register a built AOI layer (area monitor / registry). Service→service.
        self.aoi_service = aoi_service
        #: Read for `add_layers_to_group` (whether the user keeps a Mapflow layer group at all).
        self.result_loader = result_loader
        #: The current template-search results, keyed by image id, carrying the ``isNew`` flag
        #: the seen markers read. Set when a template's results load.
        self.template_search_images = {}
        #: 'No AOI' processing ids whose per-processing AOI fetch is in flight, so a second click
        #: does not fire a duplicate request before the first returns.
        self._pending_no_aoi_ids = set()

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
        template = self.processing_service._parse_template_response(response)
        if template is not None and not template.isActive:
            alert_warning(self.tr(
                "The template has been created, but is inactive.\n\n"
                "You have reached the maximum number of active planned processings. "
                "Pause or delete another one before activating this template."))
        self.processing_service.get_processings()

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
        template = (self.processing_service.active_template
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
        self.processing_service.aoi_changed_callback(response)
        self.processing_service.get_processings()

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
        template = self.processing_service.active_template
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
                callback=self.processing_service.aoi_changed_callback,
                error_handler=self.processing_service.aoi_change_error_handler,
            )
        if deletions:
            self.processing_service.api.delete_aois(
                template_id=template.id,
                data=DeleteAoisSchema(aoiIds=deletions),
                callback=self.processing_service.aoi_changed_callback,
                error_handler=self.processing_service.aoi_change_error_handler,
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
        template = self.processing_service.active_template
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
        if not self.processing_service.is_no_aoi_processing(pid):
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
        template = self.processing_service.active_template
        if not template or not self.processing_service.in_template_mode or self.no_aoi_aoi_on_map(pid):
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
