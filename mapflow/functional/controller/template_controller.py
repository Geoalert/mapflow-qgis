from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox

from ..app_context import AppContext
from ..service.aoi_service import AoiService
from ..service.alert_service import alert
from ..service.template_service import TemplateService
from ..view.search_view import SearchView
from ..view.template_view import TemplateView


class TemplateController(QObject):
    """Planned-processing (template) create / update-search-params / exclude-from-search.

    MR-1 of the templates extraction: the operations that were tangled into `mapflow.py`. It is
    the one place that sees both the template/search views and `TemplateService`, so it assembles
    the request inputs from the widgets (name, the `SearchParams` schema, the AOI
    FeatureCollection) and drives the view from the service's signals. The in-template navigation
    and lifecycle still live in `ProcessingService`; MR-2 brings them here.
    """

    def __init__(self,
                 template_service: TemplateService,
                 template_view: TemplateView,
                 search_view: SearchView,
                 aoi_view,
                 aoi_service: AoiService,
                 provider_service,
                 processing_service,
                 app_context: AppContext,
                 iface,
                 update_search_button,
                 exclude_action,
                 processings_table,
                 see_processings_action):
        super().__init__()
        self.template_service = template_service
        self.template_view = template_view
        self.search_view = search_view
        self.aoi_view = aoi_view
        self.aoi_service = aoi_service
        self.provider_service = provider_service
        #: Read for navigation state (`in_template_mode`, `active_template`,
        #: `selected_template/processing`, `selected_aois`) and for `hydrate_template`.
        self.processing_service = processing_service
        self.app_context = app_context
        self.iface = iface

        update_search_button.clicked.connect(self.update_template_search_params)
        exclude_action.triggered.connect(self.template_service.exclude_processing_from_search)
        # The Seen / Seen-all actions are created later (setup_metadata_seen_dropdown), so
        # mapflow.py wires them to mark_selected_images_seen / mark_all_images_seen.

        # In-template navigation: the map layers a template draws, plus the selection-driven
        # effects that only apply while a template is open. The processings table itself is the
        # ProjectProcessingController's region; these listeners react to it for template concerns.
        see_processings_action.triggered.connect(self.select_template_processings)
        processings_table.itemSelectionChanged.connect(self.sync_processing_area_to_selected_aois)
        processings_table.cellClicked.connect(self.on_no_aoi_processing_clicked)
        processing_service.templateAoisChanged.connect(self.on_template_aois_changed)
        processing_service.templateProcessingsLoaded.connect(self.on_template_processings_loaded)
        # The layer side of entering/leaving a template. A second listener on these signals — the
        # search/filter side stays in mapflow.py — so neither edits the other (spec § Controllers).
        processing_service.templateOpened.connect(self._on_template_opened_layers)
        processing_service.templateClosed.connect(self._on_template_closed_layers)

        self.template_service.creationBusy.connect(
            lambda busy: self.template_view.set_search_enabled(not busy))
        self.template_service.projectRequired.connect(self.template_view.show_project_required)
        self.template_service.statusMessage.connect(
            lambda message: self.iface.messageBar().pushInfo(self.app_context.plugin_name, message))
        self.template_service.templateStatusChanged.connect(
            self.template_view.refresh_template_status_cell)
        self.template_service.warningMessage.connect(
            lambda message: self.iface.messageBar().pushWarning(self.app_context.plugin_name, message))

    def create_search_template(self, name_override: str = None) -> None:
        """Assemble the request from the widgets and hand it to the service. Called by the
        getMetadata button's plan branch (still in `mapflow.py`) and by the too-large-AOI prompt."""
        self.search_view.ensure_search_provider(self.provider_service)
        try:
            aoi_details = self._build_template_aoi_details()
        except ValueError as e:  # an AOI name exceeds the limit
            alert(str(e), QMessageBox.Warning)
            return
        search_params = self.search_view.template_search_params(aoi_details=aoi_details)
        name = (name_override or self.template_view.template_name())
        self.template_service.create_search_template(name, aoi_details, search_params)

    def prompt_plan_search(self) -> None:
        """Offer a Planned Search for a too-large AOI (T8); on accept, create it with an
        auto-generated name."""
        if self.template_view.prompt_plan_search(self.app_context.plugin_name):
            self.create_search_template(
                name_override=self.template_service.planned_search_default_name())

    def update_template_search_params(self, *args) -> None:
        # aoi_details=None: only the non-geometry params are updated (the PUT endpoint rejects
        # geometry; the backend merges the rest and preserves the AOIs).
        search_params = self.search_view.template_search_params(aoi_details=None)
        self.template_service.update_template_search_params(search_params)

    # ---------- seen markers: read rows here, DTO state + api in the service, icons in the view ----------

    def mark_selected_images_seen(self, *args) -> None:
        template_id = self.template_service.seen_template_id()
        if not template_id:
            return
        for row in self.template_view.selected_metadata_rows():
            image_id = self.template_view.image_id_at(row)
            self.template_service.mark_image_seen(
                template_id, image_id,
                on_success=lambda r=row: self.template_view.set_new_image_marker(r, False))

    def mark_all_images_seen(self, *args) -> None:
        template_id = self.template_service.seen_template_id()
        if not template_id:
            return
        # Snapshot the rows that are new BEFORE the request: the service clears every DTO's
        # isNew on success, so afterwards there is no way to tell which rows to un-mark.
        new_rows = [row for row in range(self.template_view.metadata_row_count())
                    if self.template_service.image_is_new(self.template_view.image_id_at(row))]
        self.template_service.mark_all_seen(
            template_id,
            on_success=lambda: [self.template_view.set_new_image_marker(r, False) for r in new_rows])

    def apply_new_image_markers(self) -> None:
        """Show the 'new image' icon on every row whose image DTO is still new. Called after a
        template's results (re)fill."""
        for row in range(self.template_view.metadata_row_count()):
            image_id = self.template_view.image_id_at(row)
            self.template_view.set_new_image_marker(row, self.template_service.image_is_new(image_id))

    def _build_template_aoi_details(self):
        """The ``searchParams.aoiDetails`` FeatureCollection for template creation: named features
        from the current polygon layer, or a single unnamed feature from the combined AOI (e.g. an
        image/mosaic extent). None when there is no AOI at all. Raises ValueError on an overlong
        AOI name."""
        features = self.aoi_service.features_from_layer(self.aoi_view.current_layer())
        if not features and self.app_context.aoi:
            features.extend(self.aoi_service.polygon_features(self.app_context.aoi, None))
        if not features:
            return None
        return {"type": "FeatureCollection", "features": features}

    # ---------- in-template navigation: draw / redraw / clean up the template's map layers ----------

    def select_template_processings(self, *args) -> None:
        """Menu action: load AOI/processing layers for the selected template."""
        template = self.processing_service.selected_template()
        if not template or self.processing_service.selected_processing():
            return
        # Hydrate first (the list view's template omits aoiDetails), then draw layers.
        self.processing_service.hydrate_template(template, self.template_service.load_template_layers)

    def on_template_processings_loaded(self, template) -> None:
        """Once a template's processings load, create the (initially empty) 'No AOI' group if any
        processing is not bound to an AOI. Each such AOI is fetched and added lazily when the user
        single-clicks its row (see on_no_aoi_processing_clicked) — no bulk requests on open."""
        if not template or not self.processing_service.no_aoi_processing_ids():
            return
        self.template_service.ensure_template_group(str(template.name),
                                                    self.template_service.no_aoi_subgroup_name())

    def on_no_aoi_processing_clicked(self, *args) -> None:
        """Single-click on a 'No AOI' processing row: fetch that processing's AOI and add it to the
        'No AOI' group. No-op outside a template; the service ignores AOI/bound-processing rows, an
        AOI already on the map, or a request already in flight (double-click still loads results)."""
        if not self.processing_service.in_template_mode:
            return
        self.template_service.load_no_aoi_processing_aoi(self.processing_service.selected_processing())

    def on_template_aois_changed(self, template) -> None:
        """Redraw the template's AOI/processing map layers after its AOIs change (add / rename
        / delete / geometry update / exclude-from-search), so the layer tree stays in sync
        without re-entering the template."""
        if not template:
            return
        self.template_service.remove_template_aoi_subgroups(str(template.name))
        self.template_service.load_template_layers(template)

    def sync_processing_area_to_selected_aois(self, *args) -> None:
        """Inside a template, point the Area combo at the selected AOI(s), so the Area shown in
        the combo IS the one a processing will use — one place to look, no silent override.

        A single selection points at that AOI's own (already visible) layer; a multi-selection
        points at a visible "Selected AOIs" layer holding one feature per AOI. No-op when no AOI
        is selected, keeping the current Area (e.g. while a processing row is selected)."""
        if not self.processing_service.in_template_mode:
            return
        template = self.processing_service.active_template
        self.aoi_service.select_aois_as_processing_area(
            self.processing_service.selected_aois(),
            self.template_service.find_template_group(str(template.name)) if template else None)

    def _on_template_opened_layers(self, template) -> None:
        """Layer side of entering a template: draw its AOI/processing layers. The search results
        and filter widgets are handled by mapflow.py's own `templateOpened` listener."""
        self.template_service.load_template_layers(template)

    def _on_template_closed_layers(self, template) -> None:
        """Layer side of leaving a template: drop its map group."""
        if template is not None:
            self.template_service.remove_template_group(str(template.name))
