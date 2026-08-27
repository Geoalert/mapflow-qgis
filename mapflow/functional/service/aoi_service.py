import json
import os
from typing import List, Optional

from PyQt5.QtCore import QObject, pyqtSignal
from qgis.core import QgsFeature, QgsGeometry, QgsMapLayer, QgsVectorLayer

from .. import helpers
from .. import layer_utils
from ..app_context import AppContext
from ..geometry import geometry_from_geojson
# Severity-named so the icon is chosen inside AlertService: picking a QMessageBox.Icon here
# would mean importing QtWidgets, which a service may not do.
from .alert_service import alert_info, alert_warning, ask_text
from ...schema.template import (AddAoisSchema,
                                AddSingleAoiSchema,
                                AOI_NAME_MAX_LENGTH,
                                UpdateAoiSchema)


class AoiService(QObject):
    """AOI geometry and the AOI layers the user can process.

    Holds no widget and no dialog (`spec/007_architecture.md` § Layer rules), which shapes two
    things that would otherwise look roundabout:

    * anything the UI must do in response leaves as a signal, and a controller subscribes —
      the service never calls a view. Talking *to* the user is not an exception to that:
      `AlertService` owns the message tier (`spec/006_error_reporting.md`) and is itself a
      service, so `alert_*` and `ask_text` are called directly like any other service;
    * inputs that live in a widget arrive as arguments. `excepted_layers` takes the
      "use all vector layers" flag rather than reading the checkbox, and the layer-creation
      methods return the layer instead of activating it, because making a layer active is an
      `iface` call on the map canvas.
    """

    #: A layer joined the AOI registry. Carries the layer so the controller can attach the
    #: per-layer "Remove AOI from Mapflow" context action.
    aoiLayerRegistered = pyqtSignal(object)
    #: The registry changed; whatever filters the AOI combo is stale.
    aoiLayersChanged = pyqtSignal()
    #: The AOI combo should point at this layer. The bool is whether the change may trigger a
    #: cost request — False while adding layers in bulk, where no image is selected yet.
    currentAoiLayerChanged = pyqtSignal(object, bool)
    #: An on-map edit session began; the argument is the instruction to show the user. The panel
    #: must be hidden and the Save/Cancel bar raised — both widget work, so they leave as a
    #: signal rather than being done here.
    editSessionStarted = pyqtSignal(str)
    #: The session ended, by save or cancel. Restore the panel and drop the bar.
    editSessionEnded = pyqtSignal()

    def __init__(self,
                 iface,
                 app_context: AppContext,
                 plugin_dir: str,
                 result_loader,
                 data_catalog_service,
                 processing_service):
        super().__init__()
        self.iface = iface
        self.app_context = app_context
        self.plugin_dir = plugin_dir
        self.result_loader = result_loader
        self.data_catalog_service = data_catalog_service
        #: Owns the active template, the AOI table selection, the AOI endpoints and the poll
        #: timer, all of which a session needs. Service→service is allowed; this dependency
        #: becomes `TemplateService` when the templates step splits it out.
        self.processing_service = processing_service
        #: The in-flight edit session, or None. Keys: mode, layer, aoi, is_temp,
        #: prev_active_layer.
        self._session = None
        #: The AOI id set the processing Area currently reflects, so a selection signal that
        #: does not change the set does not rebuild the layer. None = nothing selected.
        self._processing_area_filter = None
        #: The visible "Selected AOIs" layer built for a multi-AOI selection, if any.
        self._selected_aois_layer_id = None
        #: Layers the user has marked as usable AOIs. Owned here rather than on AppContext:
        #: nothing outside the AOI code reads it, and one concept has one home (invariant 4).
        self.aoi_layers: List[QgsVectorLayer] = []
        self.aoi_layer_counter = 0

    # ---------- the registry ----------

    def register_layer(self,
                       layer: QgsMapLayer,
                       recompute_cost: bool = True,
                       set_current: bool = True) -> None:
        """Mark ``layer`` as usable as an AOI.

        ``set_current=False`` for template AOI *display* layers added in bulk: they must not
        hijack the processing Area (the last one used to stick as the Area — feedback 8.1); the
        Area is driven by the AOI table selection instead.
        """
        if layer is None:
            return
        if layer not in self.aoi_layers:
            self.aoi_layers.append(layer)
            self.aoiLayerRegistered.emit(layer)
        self.aoiLayersChanged.emit()
        if not set_current:
            return
        self.currentAoiLayerChanged.emit(layer, recompute_cost)

    def unregister_layer(self, layer: QgsMapLayer) -> None:
        try:
            self.aoi_layers.remove(layer)
        except ValueError:
            # Can easily be gone already: the per-layer context action cannot be removed from a
            # single layer's menu, so "Remove AOI" stays clickable after the first click.
            pass
        self.aoiLayersChanged.emit()

    def excepted_layers(self, use_all_vector_layers: bool) -> List[QgsMapLayer]:
        """Layers the AOI combo must *not* offer.

        With "use all vector layers" on, only the search-metadata layers are excluded — they are
        big, crowded, and lead to topology errors. With it off, everything that is not a
        registered AOI layer is excluded.
        """
        layers = self.app_context.project.mapLayers().values()
        if use_all_vector_layers:
            provider = self.app_context.search_provider
            if not provider:
                return []
            return [layer for layer in layers if provider.name + ' metadata' == layer.name()]
        return [layer for layer in layers if layer not in self.aoi_layers]

    # ---------- creating AOI layers ----------

    def _new_aoi_layer(self, geometry: Optional[QgsGeometry], editable: bool = False):
        """A styled, numbered in-memory polygon layer, added to the map and the registry."""
        layer = QgsVectorLayer('Polygon?crs=epsg:4326', f'AOI_{self.aoi_layer_counter}', 'memory')
        if geometry is not None:
            feature = QgsFeature()
            feature.setGeometry(geometry)
            layer.dataProvider().addFeatures([feature])
            layer.updateExtents()
        if editable:
            layer.startEditing()
        layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'aoi.qml'))
        self.aoi_layer_counter += 1
        self.result_loader.add_layer(layer)
        self.register_layer(layer)
        return layer

    def create_layer_from_rect(self, rect, crs) -> QgsVectorLayer:
        """An AOI covering ``rect`` (the current map view), reprojected to WGS84."""
        return self._new_aoi_layer(helpers.to_wgs84(QgsGeometry.fromRect(rect), crs))

    def create_layer_from_imagery(self) -> Optional[QgsVectorLayer]:
        """An AOI covering the footprint of the selected My Imagery image or mosaic.

        Returns None when nothing is selected, so the caller can explain why instead of adding
        an empty layer.
        """
        image = self.data_catalog_service.selected_image()
        mosaic = self.data_catalog_service.selected_mosaic()
        if image:
            geometry = QgsGeometry().fromWkt(image.footprint)
        elif mosaic:
            geometry = QgsGeometry().fromWkt(mosaic.footprint)
        else:
            return None
        return self._new_aoi_layer(geometry)

    def create_editable_layer(self) -> QgsVectorLayer:
        """An empty AOI layer left in edit mode for the user to draw into."""
        return self._new_aoi_layer(None, editable=True)

    # ---------- GeoJSON features from a layer ----------

    def features_from_layer(self, layer: Optional[QgsVectorLayer]) -> List[dict]:
        """Exploded single-Polygon GeoJSON AOI features from a polygon layer (selected features
        if any, else all). Each feature's ``properties.name`` comes from a ``name`` attribute
        when present. MultiPolygons are split into separate Polygon features (the create path
        requires single-part polygons). Raises ``ValueError`` if a name exceeds the limit."""
        if layer is None or not layer.featureCount():
            return []
        source_features = list(layer.getSelectedFeatures()) or list(layer.getFeatures())
        has_name_field = layer.fields().indexFromName("name") != -1
        features = []
        for feature in source_features:
            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue
            wgs_geom = helpers.to_wgs84(QgsGeometry(geom), layer.crs())
            name = None
            if has_name_field:
                raw = feature.attribute("name")
                # QGIS NULL attributes are not None; normalize to a real None.
                if raw not in (None, "") and str(raw).upper() != "NULL":
                    name = str(raw).strip()
            if name and len(name) > AOI_NAME_MAX_LENGTH:
                raise ValueError(
                    self.tr("AOI name '{name}' exceeds {limit} characters").format(
                        name=name, limit=AOI_NAME_MAX_LENGTH
                    )
                )
            features.extend(self.polygon_features(wgs_geom, name))
        return features

    @staticmethod
    def polygon_features(wgs_geom: QgsGeometry, name: Optional[str]) -> List[dict]:
        """Split a (possibly multi-)polygon into one GeoJSON *Polygon* Feature per part.

        The backend ignores ``MultiPolygon`` features in ``aoiDetails`` — an all-MultiPolygon
        upload would create an empty, Failed template (feedback 10) — so mirror the web client
        and explode each MultiPolygon into separate single-part Polygon features. Parts share
        the source feature's ``name``. ``asGeometryCollection`` returns one element for a plain
        Polygon and one per part for a MultiPolygon."""
        features = []
        for part in wgs_geom.asGeometryCollection() or [wgs_geom]:
            if part is None or part.isEmpty():
                continue
            features.append({
                "type": "Feature",
                "geometry": json.loads(part.asJson()),
                "properties": {"name": name},
            })
        return features

    # ---------- the processing Area for a template AOI selection ----------

    def select_aois_as_processing_area(self, aois, group=None) -> None:
        """Point the Area at the selected AOI(s), so the Area shown in the combo IS the one a
        processing will use — one place to look, no silent override.

        A single selection points at that AOI's own (already visible) layer; a multi-selection
        gets a visible "Selected AOIs" layer holding one feature per AOI. No-op when no AOI is
        selected, keeping the current Area (e.g. while a processing row is selected).

        ``group`` is the template's layer-tree group, or None to leave the built layer at the
        root. Looking it up is side-effect free (`TemplateService.find_template_group`), so it can
        be resolved before the call rather than deferred into it.
        """
        aois = [aoi for aoi in aois if aoi and aoi.id]
        selected_ids = frozenset(str(aoi.id) for aoi in aois)
        # Selection signals fire often; only rebuild when the set actually changes.
        if selected_ids == (self._processing_area_filter or frozenset()):
            return
        layer = self._layer_for_selected_aois(aois, group)
        if layer is None:
            return
        self._processing_area_filter = selected_ids or None
        # The controller points the combo at it; layerChanged then recomputes Area and cost.
        self.currentAoiLayerChanged.emit(layer, True)

    def _layer_for_selected_aois(self, aois, group) -> Optional[QgsVectorLayer]:
        """The layer the Area combo should show for the current AOI selection."""
        if not aois:
            return None
        if len(aois) == 1:
            return self.find_layer_for_aoi(aois[0].id)
        geometries = [geom for geom in
                      (geometry_from_geojson(getattr(aoi, "geometry", None)) for aoi in aois)
                      if geom is not None]
        if not geometries:
            return None
        return self.rebuild_selected_aois_layer(geometries, group)

    def rebuild_selected_aois_layer(self, geometries: List[QgsGeometry],
                                    group=None) -> QgsVectorLayer:
        """(Re)build the visible "Selected AOIs" layer in the template group — one feature per
        selected AOI, so a processing covers exactly them and the per-processing AOI limit still
        applies. Visible on the map and in the tree (unlike the old hidden 'Selected AOI')."""
        self.remove_selected_aois_layer()
        layer = QgsVectorLayer('Polygon?crs=epsg:4326', self.tr('Selected AOIs'), 'memory')
        features = []
        for geom in geometries:
            feature = QgsFeature()
            feature.setGeometry(geom)
            features.append(feature)
        layer.dataProvider().addFeatures(features)
        layer.updateExtents()
        layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'aoi.qml'))
        if group is not None:
            self.app_context.project.addMapLayer(layer, addToLegend=False)
            group.insertLayer(0, layer)
        else:
            self.app_context.project.addMapLayer(layer)
        # Register it as an AOI layer so it is selectable in the combo (not excepted). Not as the
        # current one: the caller emits that itself once the whole selection is resolved.
        self.register_layer(layer, recompute_cost=False, set_current=False)
        self._selected_aois_layer_id = layer.id()
        return layer

    def remove_selected_aois_layer(self) -> None:
        """Drop the multi-selection "Selected AOIs" layer (on a new selection or on leaving the
        template). Single-AOI selections point at the AOI's own layer, so there is nothing to
        clean up for them."""
        layer_id = self._selected_aois_layer_id
        self._selected_aois_layer_id = None
        if not layer_id:
            return
        try:
            layer = self.app_context.project.mapLayer(layer_id)
            if layer is not None:
                self.unregister_layer(layer)
            self.app_context.project.removeMapLayer(layer_id)
        except (RuntimeError, KeyError, AttributeError):
            pass

    def clear_processing_area_selection(self) -> None:
        """Leaving the template: drop the built layer and forget which AOIs the Area reflects."""
        self.remove_selected_aois_layer()
        self._processing_area_filter = None

    # ---------- the on-map edit session ----------

    @property
    def session_active(self) -> bool:
        return self._session is not None

    def selectable_layers(self) -> List[QgsVectorLayer]:
        """Polygon vector layers the user can add as AOIs.

        Only the plugin's own *display* layers are hidden: the active template's group (the AOI
        polygons + processing footprints + template search metadata), the current search-metadata
        layer, preview layers, and the active draw session's temp layer. The user's own AOI layers
        (which live directly under the Mapflow group after "Use as AOI") stay selectable — hiding
        the whole Mapflow group is what left only the stray root layer visible before."""
        project = self.app_context.project
        excluded = set()
        # Layers inside the active template's group (Mapflow > <template name> > …).
        root = project.layerTreeRoot()
        mapflow_group = root.findGroup(self.app_context.settings.value('layerGroup')
                                       or self.app_context.plugin_name)
        template = self.processing_service.active_template
        if template is not None and mapflow_group is not None:
            template_group = mapflow_group.findGroup(str(template.name))
            if template_group is not None:
                excluded |= {node.layerId() for node in template_group.findLayers()}
        meta_layer = getattr(self.app_context, 'metadata_layer', None)
        if meta_layer is not None:
            try:
                excluded.add(meta_layer.id())
            except (RuntimeError, AttributeError):
                pass
        session_layer = self._session.get('layer') if self._session else None
        if session_layer is not None:
            excluded.add(session_layer.id())

        result = []
        for layer in project.mapLayers().values():
            if layer.id() in excluded:
                continue
            name = layer.name() or ''
            if name.endswith(' preview') or name.endswith(' metadata'):
                continue
            # Template AOI display layers are tagged; never offer them as sources.
            if layer.customProperty('mapflow/aoi_id'):
                continue
            if isinstance(layer, QgsVectorLayer) and layer_utils.is_polygon_layer(layer):
                result.append(layer)
        return result

    def find_layer_for_aoi(self, aoi_id) -> Optional[QgsVectorLayer]:
        """The on-map AOI layer tagged with ``aoi_id`` (see ``_add_geojson_aoi_layer``)."""
        for layer in self.app_context.project.mapLayers().values():
            if layer.customProperty('mapflow/aoi_id') == str(aoi_id):
                return layer
        return None

    def add_aois_from_layers(self, layer_ids: List[str]) -> None:
        """Add every polygon in the chosen layers as an AOI of the active template."""
        template = self.processing_service.active_template
        if not template:
            return
        try:
            features = []
            for layer_id in layer_ids:
                layer = self.app_context.project.mapLayer(layer_id)
                if layer is not None:
                    features.extend(self.features_from_layer(layer))
        except ValueError as e:  # a name exceeded the limit
            alert_warning(str(e))
            return
        if not features:
            alert_warning(self.tr("The selected layer(s) have no polygon features to add."))
            return
        self._post_aois(template, features, name=None)

    def start_update_session(self) -> None:
        """'Update selected AOI': edit the selected AOI's polygon on the map (in place)."""
        if self.session_active:
            return
        aoi = self.processing_service.selected_aoi()
        template = self.processing_service.active_template
        if not aoi or not template:
            return
        if not aoi.can_rename:  # a persisted AOI id is required to update it
            alert_info(self.tr("This AOI has no id yet and cannot be updated. "
                               "Reopen the template and try again."))
            return
        layer = self.find_layer_for_aoi(aoi.id)
        if layer is None:
            alert_warning(self.tr("Could not find this AOI's layer on the map. "
                                  "Reopen the template and try again."))
            return
        self._begin_session(
            mode="update", layer=layer, aoi=aoi, is_temp=False, tool="vertex",
            message=self.tr("Editing AOI '{name}': move its vertices on the map, then Save AOI.")
            .format(name=aoi.display_name))

    def start_draw_session(self) -> None:
        """'Draw AOI on the map': draw a new polygon, name it on Save, then add it as an AOI."""
        if self.session_active:
            return
        if not self.processing_service.active_template:
            return
        layer = QgsVectorLayer('Polygon?crs=epsg:4326', self.tr('New AOI'), 'memory')
        layer.loadNamedStyle(os.path.join(self.plugin_dir, 'static', 'styles', 'aoi.qml'))
        self.app_context.project.addMapLayer(layer)
        self._begin_session(
            mode="draw", layer=layer, aoi=None, is_temp=True, tool="add",
            message=self.tr("Draw the AOI polygon on the map, then Save AOI."))

    def _begin_session(self, mode: str, layer: QgsVectorLayer, aoi, is_temp: bool,
                       tool: str, message: str) -> None:
        """Enter an on-map AOI edit session: pause the poll, make ``layer`` active + editable
        with the right map tool, and ask for the Save/Cancel bar."""
        self.processing_service.processing_fetch_timer.stop()
        self._session = {"mode": mode, "layer": layer, "aoi": aoi, "is_temp": is_temp,
                         "prev_active_layer": self.iface.activeLayer()}
        self.iface.setActiveLayer(layer)
        if not layer.isEditable():
            layer.startEditing()
        if tool == "add":
            self.iface.actionAddFeature().trigger()
        else:
            vertex_action = (getattr(self.iface, "actionVertexTool", None)
                             or getattr(self.iface, "actionNodeTool", None))
            if vertex_action is not None:
                vertex_action().trigger()
        self.editSessionStarted.emit(message)

    def save_session(self) -> bool:
        """Commit the session. Returns False to keep it open, so that neither a validation
        failure nor a cancelled name prompt loses the user's drawing."""
        session = self._session
        if not session:
            return False
        if session["mode"] == "update":
            ok = self._commit_update(session["layer"], session["aoi"])
        else:
            ok = self._commit_draw(session["layer"])
        if ok:
            self._end_session()
        return ok

    def cancel_session(self) -> None:
        session = self._session
        if not session:
            return
        layer = session["layer"]
        if not session["is_temp"]:
            try:
                if layer.isEditable():
                    layer.rollBack()  # discard the in-place edits
            except (RuntimeError, AttributeError):
                pass
        self._end_session()

    def _end_session(self) -> None:
        """Tear down a session: restore the poll and the pan tool, drop a temp layer, and ask
        for the panel back."""
        session = self._session
        self._session = None
        self.iface.actionPan().trigger()  # leave the add-feature/vertex tool
        if session and session.get("is_temp"):
            try:
                self.app_context.project.removeMapLayer(session["layer"].id())
            except (RuntimeError, AttributeError):
                pass
        self.editSessionEnded.emit()
        self.processing_service.processing_fetch_timer.start()
        prev = session.get("prev_active_layer") if session else None
        if prev is not None:
            try:
                self.iface.setActiveLayer(prev)
            except (RuntimeError, AttributeError):
                pass

    def _commit_update(self, layer: QgsVectorLayer, aoi) -> bool:
        """POST the edited AOI geometry (as-is, single or multi-part — the per-AOI update
        endpoint accepts a generic geometry). Returns False (keeping the session open) if the
        edit left no usable geometry."""
        template = self.processing_service.active_template
        if not template or not aoi or not aoi.id:
            return False
        feats = [f for f in layer.getFeatures() if f.geometry() and not f.geometry().isEmpty()]
        if not feats:
            alert_warning(self.tr("The AOI has no geometry — draw or keep at least one polygon."))
            return False
        geom = (feats[0].geometry() if len(feats) == 1
                else QgsGeometry.collectGeometry([f.geometry() for f in feats]))
        wgs = helpers.to_wgs84(QgsGeometry(geom), layer.crs())
        if wgs is None or wgs.isEmpty():
            alert_warning(self.tr("The edited AOI has no valid geometry."))
            return False
        if layer.isEditable():
            layer.commitChanges()  # reflect the edit on the map until the server refresh arrives
        self.processing_service.api.update_aoi(
            template_id=template.id,
            aoi_id=aoi.id,
            data=UpdateAoiSchema(geometry=json.loads(wgs.asJson())),
            callback=self.processing_service.aoi_changed_callback,
            error_handler=self.processing_service.aoi_change_error_handler,
        )
        return True

    def _commit_draw(self, layer: QgsVectorLayer) -> bool:
        """Name the drawn polygon(s) and add them as AOI(s). Returns False if nothing was drawn,
        the prompt was cancelled, or the name is too long — in every case the session stays open
        and the drawing is not lost."""
        template = self.processing_service.active_template
        if not template:
            return False
        if layer.isEditable():
            layer.commitChanges()  # move drawn features from the edit buffer into the provider
        features = self.features_from_layer(layer)
        if not features:
            alert_warning(self.tr("Draw at least one polygon before saving."))
            return False
        # Asked for here, where it is used, rather than upstream: `ask_text` belongs to the
        # message tier, so wanting an answer from the user is not a reason to hand the flow to
        # someone who can see a dialog. Same reasoning as `rename_aoi` prompting inline.
        name, accepted = ask_text(self.tr("Name the AOI"), self.tr("AOI name:"))
        if not accepted:
            return False
        name = (name or "").strip()
        if name and len(name) > AOI_NAME_MAX_LENGTH:
            alert_warning(self.tr("AOI name must not exceed {limit} characters.").format(
                limit=AOI_NAME_MAX_LENGTH))
            return False
        self._post_aois(template, features, name or None)
        return True

    def _post_aois(self, template, features: List[dict], name: Optional[str]) -> None:
        """Send AOIs to the template. ``name`` overrides each feature's own name when given
        (the draw path names every part of one drawing alike)."""
        aois = [AddSingleAoiSchema(geometry=f["geometry"],
                                   name=name if name is not None else f["properties"].get("name"))
                for f in features]
        self.processing_service.api.add_aois(
            template_id=template.id,
            data=AddAoisSchema(aois=aois),
            callback=self.processing_service.aoi_changed_callback,
            error_handler=self.processing_service.aoi_change_error_handler,
        )
