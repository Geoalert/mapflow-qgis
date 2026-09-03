from typing import List, Optional

from PyQt5.QtCore import QCoreApplication, QObject
from PyQt5.QtWidgets import QMessageBox

from ..service.alert_service import alert
from ..service.local_filter_service import FilterCriteria, LocalFilterService
from ..service.preview_service import PreviewService
from ..service.provider_service import ProviderService
from ..service.search_service import SearchService
from ..view.search_view import SearchView
from ...model.provider import ImagerySearchProvider


class SearchController(QObject):
    """The imagery-search tab: which image to preview, and the local filter over the results
    already fetched.

    A controller may own a signal connection only when it owns the *handler*; the run and
    pagination handlers still call collaborators that have not been extracted (provider
    selection, the template search loader), so their connections stay in `mapflow.py` until
    those handlers can move here.
    """

    def __init__(self,
                 search_service: SearchService,
                 search_view: SearchView,
                 preview_service: PreviewService,
                 provider_service: ProviderService,
                 search_button,
                 metadata_table,
                 local_filter_service: LocalFilterService = None,
                 app_context=None,
                 widen_warning_button=None,
                 reset_filters_button=None,
                 clear_search_button=None,
                 area_calculator_service=None,
                 aoi_view=None,
                 ensure_output_dir=None):
        super().__init__()
        self.search_service = search_service
        self.search_view = search_view
        self.preview_service = preview_service
        self.provider_service = provider_service
        self.local_filter_service = local_filter_service
        self.app_context = app_context
        #: Selecting a search result changes the processing area, so the cost is recomputed from
        #: the AOI layer the combo currently names.
        self.area_calculator_service = area_calculator_service
        self.aoi_view = aoi_view
        #: "Is there a usable working directory, asking the user if not." Passed in as a callable
        #: because the output-directory prompt is still `mapflow.py`'s; it becomes a real
        #: collaborator when that cluster is extracted. Defaults to yes so tests that do not care
        #: about the directory need not stub it.
        self.ensure_output_dir = ensure_output_dir or (lambda: True)
        #: The table->layer connection handle, so the layer->table direction can take it down
        #: while it drives. Set by `connect_table_selection`.
        self._table_selection_connection = None

        #: Guards the ``metadataTableFilled`` -> ``apply_local_filter`` -> ``fill_table`` ->
        #: ``metadataTableFilled`` loop: the re-fill below re-emits the signal that called us.
        self._suppress_local_filter = False
        #: The last filter outcome, so an edit that changes nothing skips the re-fill entirely.
        self._last_unfit_set = None
        self._last_filtered_geoms = None
        #: What the widen (!) indicator would say, kept for its click handler.
        self._widen_details: List[str] = []

        # Owned handlers, so the connections are owned here too.
        search_button.clicked.connect(self.preview_or_search)
        metadata_table.cellDoubleClicked.connect(self.preview)
        # cellClicked -> preview is rewired on every table refill (see reconnect_cell_preview).
        self.reconnect_cell_preview()
        if widen_warning_button is not None:
            widen_warning_button.clicked.connect(self.show_widen_details)
        if reset_filters_button is not None:
            reset_filters_button.clicked.connect(self.reset_filters)
        if clear_search_button is not None:
            clear_search_button.clicked.connect(self.clear_results)

    # ---------- running a search ----------

    def run_search(self, _=False, offset: Optional[int] = 0) -> None:
        """Fetch image footprints for the current AOI and filter widgets.

        Every filter widget is read once, here, so the request is built from what they said when
        Search was pressed rather than from whatever they say by the time it is sent.
        """
        # Drop the previous Preview-cell connection so a refill does not stack it: several
        # searches would otherwise fire the preview several times per click.
        self.search_view.disconnect_cell_preview()
        # A provider that cannot search would send the request nowhere.
        self.search_view.ensure_search_provider(self.provider_service)
        # A regular search replaces any template results, so a "Start" is no longer planned.
        self.app_context.open_template_results_id = None

        self.search_view.clear_table()
        self.search_view.remove_more_button()
        if not self.app_context.aoi:
            alert(self.tr('Please, select a valid area of interest'))
            return
        # Results are written to the working directory, so refuse rather than search without one.
        if not self.ensure_output_dir():
            return
        self.search_service.search(
            aoi=self.app_context.aoi,
            provider=self.provider_service.providers[self.search_view.provider_index()],
            aoi_layer=self.aoi_view.current_layer(),
            baseline_filters=self.search_view.filter_baseline(),
            offset=offset,
            **self.search_view.search_parameters())

    def on_search_results(self, geoms) -> None:
        """Built-in Qt sorting stays OFF: results already arrive in the server's sort order, and
        a header click re-requests rather than sorting locally."""
        self.search_view.fill_table(geoms, sort=False)

    def preview(self, *args) -> None:
        """Double-click / Preview: show tiles for the selected image."""
        image_id = self.search_view.selected_image_id()
        provider = self.provider_service.providers[self.search_view.provider_index()]
        if provider.requires_image_id and not image_id:
            alert(self.tr("This provider requires image ID!"), QMessageBox.Warning)
            return
        if isinstance(provider, ImagerySearchProvider):
            self.preview_service.preview_catalog(image_id=image_id)
        else:  # XYZ providers
            self.preview_service.preview_xyz(provider=provider, image_id=image_id)

    def preview_or_search(self, *args) -> None:
        """The Search button: providers that need an image id send the user to the search tab to
        pick one; the rest can preview straight away."""
        provider = self.provider_service.providers[self.search_view.provider_index()]
        if provider.requires_image_id:
            self.search_view.switch_to_search_tab()
        else:
            self.preview()

    def preview_search_from_cell(self, row: int, column: int) -> None:
        """A click in the results table's Preview column previews that row's image."""
        if self.search_view.is_preview_column(column):
            self.preview_service.preview_catalog(self.search_view.image_id_at(row))

    def reconnect_cell_preview(self) -> None:
        """Rewire the Preview-cell click after a table refill."""
        self.search_view.connect_cell_preview(self.preview_search_from_cell)

    # ---------- table <-> footprint layer, both directions ----------
    #
    # Each direction writes the selection the other listens to, so each disconnects the opposite
    # handler before touching a selection and reconnects afterwards. Without that, one click
    # ping-pongs between them until the stack runs out.

    def on_metadata_layer_ready(self, layer) -> None:
        """A new footprint layer: selecting a footprint should select its table row."""
        self.app_context.meta_layer_table_connection = layer.selectionChanged.connect(
            self.sync_layer_selection_with_table)

    def connect_table_selection(self) -> None:
        """Wire the table->layer direction, remembering the handle so the other direction can
        take it down while it drives."""
        self._table_selection_connection = self.search_view.connect_table_selection(
            self.sync_table_selection_with_layer)

    def sync_table_selection_with_layer(self, *args) -> None:
        """Rows were selected: highlight their footprints and adopt the image's zoom."""
        local_indices = self.search_view.selected_local_indices()
        layer = self.app_context.metadata_layer
        try:
            layer.selectionChanged.disconnect(self.app_context.meta_layer_table_connection)
        except (RuntimeError, AttributeError, TypeError):
            # No layer yet (nothing searched), or it has been removed. Nothing to sync to.
            return
        self.search_view.ensure_search_provider(self.provider_service)
        try:
            layer.selectByExpression("local_index in {}".format(tuple(local_indices)))
        except RuntimeError:  # layer deleted between the check and here
            pass
        except Exception:
            # Reconnect before propagating, or the map silently stops driving the table.
            self.app_context.meta_layer_table_connection = layer.selectionChanged.connect(
                self.sync_layer_selection_with_table)
            raise
        # The zoom is adopted BEFORE the cost is recomputed, and with the combo silent — see
        # `set_zoom_silently` for why the order and the blocking both matter.
        self.search_view.set_zoom_silently(self.search_view.selected_zoom())
        self.area_calculator_service.calculate_aoi_area_polygon_layer(self.aoi_view.current_layer())
        self.app_context.meta_layer_table_connection = layer.selectionChanged.connect(
            self.sync_layer_selection_with_table)

    def sync_layer_selection_with_table(self, selected_ids: List[int]) -> None:
        """Footprints were selected on the map: select the matching rows.

        ``selected_ids`` are feature ids, not image ids, so each is resolved to its `local_index`
        before the table is searched for it.
        """
        self.search_view.disconnect_table_selection(self._table_selection_connection)
        try:
            if not selected_ids:
                self.search_view.clear_metadata_selection()
                return
            local_indices = []
            for selected_id in selected_ids:
                local_indices.append(
                    self.app_context.metadata_layer.getFeature(selected_id)["local_index"])
            self.search_view.select_rows_by_local_index(local_indices)
        finally:
            self.connect_table_selection()

    def sync_image_id_with_table(self, image_id: str) -> None:
        """An image id typed or cleared elsewhere: clear the table selection when it names no row."""
        if not image_id or not self.search_view.has_row_with_text(image_id):
            self.search_view.clear_metadata_selection()

    # ---------- the local filter ----------

    def apply_local_filter(self, *_) -> None:
        """Instantly filter the current search/template results by the filter widgets
        (intersection %, cloud cover, date range) without a server request.

        Unfit rows are NOT removed: they are greyed-out, made non-selectable and sorted to the
        bottom of the page (so pages keep their expected size and the user can see that some
        images were filtered), and their footprints are hidden from the result layer. Runs on
        every filter-widget change and after each table (re)fill, and refreshes the widen (!)
        indicator. Applies to both regular search and template results — templates no longer
        filter server-side; only "Update template" persists filter values."""
        if self._suppress_local_filter:
            return
        geoms = self.app_context.search_result_geojson
        if not geoms or not geoms.get("features"):
            self.reconnect_cell_preview()
            self.update_widen_indicator()
            return
        features = geoms["features"]
        # Compute fit/unfit from the SAME GeoJSON properties that fill the table, so the greyed
        # rows always match the values shown in the Cloud %/Date columns (reading the OGR layer
        # instead risked field-type mismatches, greying rows that looked fine).
        unfit = self.local_filter_service.unfit_indices(features, self._filter_criteria())
        # Skip the (heavier) re-fill/re-mark when the outcome is unchanged — e.g. dragging a
        # slider through a range where no image flips fit<->unfit. Invalidated automatically when
        # a new search replaces ``search_result_geojson`` (a different object).
        if unfit == self._last_unfit_set and geoms is self._last_filtered_geoms:
            self.update_widen_indicator()
            return
        self._last_unfit_set = set(unfit)
        self._last_filtered_geoms = geoms
        # Order: fit rows first, unfit rows last. WITHIN each group keep the incoming order — the
        # server sort (sortBy/sortOrder) for both regular AND template search — so header-click
        # sorting actually shows in the table. Built-in column sorting is OFF so the order sticks
        # (otherwise the table would re-sort and the unfit rows jump back up).
        fit_features = [
            f for f in features if f.get("properties", {}).get("local_index") not in unfit]
        unfit_features = [
            f for f in features if f.get("properties", {}).get("local_index") in unfit]
        reordered = dict(geoms)
        reordered["features"] = fit_features + unfit_features
        # Re-fill in the new order. Preview cells are generic and ``local_index`` stays bound to
        # each feature, so table<->layer selection and footprint mapping are preserved. The
        # nested ``metadataTableFilled`` is swallowed by the re-entrancy guard.
        self._suppress_local_filter = True
        try:
            self.search_view.fill_table(reordered, sort=False)
        finally:
            self._suppress_local_filter = False
        self.search_view.mark_unfit_rows(unfit)
        self.search_service.hide_unfit_footprints(unfit)
        self.reconnect_cell_preview()
        self.update_widen_indicator()
        # The fill above hid the sort arrow (setSortingEnabled(False)); put it back so it persists.
        self.restore_sort_indicator()

    def _filter_criteria(self) -> FilterCriteria:
        """The filter widgets plus the available-provider context, as the criteria the
        (widget-free, functional-tier tested) comparison takes."""
        return FilterCriteria(provider_set=self._allowed_provider_set(),
                              product_filter=self.search_view.product_category_filter(),
                              **self.search_view.filter_widget_values())

    def _allowed_provider_set(self) -> Optional[set]:
        """Lowercased provider api-names a result may come from for the LOCAL filter, or ``None``
        for no provider filtering (show all).

        - "Search only through available providers" OFF -> ``None`` (show all).
        - ON with specific providers checked -> just those.
        - ON with none checked -> all providers available to the user
          (``app_context.search_data_providers``), so results from providers the user cannot use
          are dropped."""
        if not self.search_view.hide_unavailable_results():
            return None
        checked = self.search_view.checked_provider_names()
        if checked:
            return {str(p).lower() for p in checked}
        available = self.app_context.search_data_providers or []
        return {str(p).lower() for p in available} if available else None

    def restore_sort_indicator(self) -> None:
        column = self.search_service.active_sort_column()
        if column is not None:
            self.search_view.show_sort_indicator(
                column, descending=self.search_service.sort_order == "DESC")

    # ---------- the widen (!) indicator ----------

    def update_widen_indicator(self) -> None:
        """Show the (!) indicator when the current filter widgets are WIDER than the filters
        that fetched the current results (relaxing them cannot surface more images without a new
        search); hide it otherwise. Its tooltip lists exactly which settings will not apply."""
        self._widen_details = self._widened_filter_messages()
        if self._widen_details:
            self.search_view.show_widen_warning(self._format_widen_message(self._widen_details))
        else:
            self.search_view.hide_widen_warning()

    def _widened_filter_messages(self) -> List[str]:
        """The ways the current filter widgets are wider than the baseline that fetched the
        current results."""
        return self.local_filter_service.widen_messages(
            self.search_view.filter_baseline(), self.app_context.search_baseline_filters)

    @staticmethod
    def _format_widen_message(messages: List[str]) -> str:
        header = QCoreApplication.translate(
            "Mapflow",
            "These filters are wider than the last search, so they will not bring more images. "
            "Run a new Search to fetch them:")
        return header + "\n• " + "\n• ".join(messages)

    def show_widen_details(self, *args) -> None:
        """On click of the (!) indicator, explain which filters are wider than the fetched
        results and therefore have no effect until a new search is run."""
        messages = self._widen_details or self._widened_filter_messages()
        if not messages:
            return
        alert(self._format_widen_message(messages), QMessageBox.Information)

    def clear_results(self, *args) -> None:
        """Drop the search results: the service owns the results and the map layer, the view the
        table and the (!) indicator."""
        self.search_service.clear()
        self.search_view.clear_table()
        self.search_view.hide_widen_warning()

    # ---------- resetting the filters ----------

    def reset_filters(self, *args) -> None:
        """Reset the filter widgets to the parameters the current results were fetched with — a
        regular search's request params, or the open template's search params. Only params that
        were part of that request are restored; params it did not carry are left untouched."""
        baseline = self.app_context.search_baseline_filters
        if not baseline:
            return
        self.search_view.apply_baseline(baseline)
        # Re-filter once against the restored widgets: some setters above may not have changed a
        # value, so their change-signal would not have fired the filter on its own.
        self.apply_local_filter()
