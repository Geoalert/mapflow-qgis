from typing import List, Optional, Tuple

from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QAbstractItemView, QMenu, QPushButton, QToolButton, QWidget

from ..helpers import utc_date_from_iso
from ...dialogs.main_dialog import MainDialog
from ...schema.catalog import ProductType
from ...schema.template import SearchParams


class SearchView(QObject):
    """Every widget read and write for the imagery-search tab.

    Holds no service (`spec/007_architecture.md` § Layer rules): the controller reads the
    search parameters from here, hands them to `SearchService`, and pushes results back.

    The reads are grouped as `search_parameters()` rather than exposed one property per widget,
    because they are only ever wanted together — at the moment the user presses Search — and a
    single call is what makes "the request is built from what the widgets said *then*" true by
    construction instead of by convention.
    """

    #: The results table was refilled, so anything drawn per-row must be reapplied. A refill
    #: rebuilds every cell, which drops decorations that are not part of the data — the template
    #: view's 'new image' icons. Emitting rather than calling keeps this view ignorant of who
    #: decorates its rows.
    tableRefilled = pyqtSignal()
    #: The Search button switched between an immediate search and planning one ("search"/"plan").
    #: A planned search creates a template, which needs a project — but that rule is the template
    #: region's, so it is announced rather than checked here.
    searchModeChanged = pyqtSignal(str)

    def __init__(self, dlg: MainDialog, config):
        super().__init__()
        self.dlg = dlg
        self.config = config
        #: The current cellClicked->preview connection, so it can be dropped before rewiring.
        self._cell_preview_connection = None
        #: "search" (run it now) or "plan" (create a template that keeps searching).
        self.search_mode = "search"

    # ---------- the Search and Seen split-buttons ----------

    def setup_search_mode_dropdown(self) -> None:
        """Turn the Search button into a split button offering Search / Plan search."""
        self._search_menu = QMenu(self.dlg.getMetadata)
        search_action = self._search_menu.addAction(self.tr("Search"))
        plan_action = self._search_menu.addAction(self.tr("Plan search"))
        search_action.triggered.connect(lambda: self.set_search_mode("search"))
        plan_action.triggered.connect(lambda: self.set_search_mode("plan"))
        self.dlg.getMetadata.setPopupMode(QToolButton.MenuButtonPopup)
        self.dlg.getMetadata.setMenu(self._search_menu)
        self.set_search_mode("search")

    def set_search_mode(self, mode: str) -> None:
        self.search_mode = mode
        self.dlg.getMetadata.setText(self.tr("Plan search") if mode == "plan" else self.tr("Search"))
        self.searchModeChanged.emit(mode)

    def setup_seen_dropdown(self, on_seen, on_seen_all) -> None:
        """Turn the Seen button into a split button offering Seen / Seen all.

        The handlers are passed in rather than looked up: marking images seen is the template
        region's, and a view may not reach into a controller.
        """
        self._seen_menu = QMenu(self.dlg.markSeenButton)
        seen_action = self._seen_menu.addAction(self.tr("Seen"))
        seen_all_action = self._seen_menu.addAction(self.tr("Seen all"))
        seen_action.triggered.connect(on_seen)
        seen_all_action.triggered.connect(on_seen_all)
        self.dlg.markSeenButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.dlg.markSeenButton.setMenu(self._seen_menu)
        self.dlg.markSeenButton.setDefaultAction(seen_action)

    # ---------- what the user is asking for ----------

    def search_parameters(self) -> dict:
        """The filter widgets, as the keyword arguments a search request takes."""
        min_off_nadir, max_off_nadir = self.off_nadir_bounds()
        return {
            "from_": self.dlg.metadataFrom.dateTime().toTimeSpec(Qt.UTC).toString(Qt.ISODate),
            "to": self.dlg.metadataTo.dateTime().toTimeSpec(Qt.UTC).toString(Qt.ISODate),
            "max_cloud_cover": self.dlg.maxCloudCover.value(),
            "min_intersection": self.dlg.minIntersection.value(),
            "hide_unavailable": self.dlg.hideUnavailableResults.isChecked(),
            "product_types": self.product_types(),
            "search_providers": self.search_providers(),
            "min_off_nadir_angle": min_off_nadir,
            "max_off_nadir_angle": max_off_nadir,
        }

    def off_nadir_bounds(self) -> Tuple[Optional[float], Optional[float]]:
        """(min, max) off-nadir angle to send, or (None, None) at the full 0-30 range.

        Leaving it out at full range is not the same as sending 0-30: the bounds exclude images
        whose angle is unknown, so sending them would drop results the user did not filter out.
        """
        if self.dlg.off_nadir_is_full_range():
            return None, None
        return self.dlg.off_nadir_range()

    def product_types(self) -> List[str]:
        """Neither box ticked means *both*, not neither — the backend reads an empty list
        literally."""
        product_types = []
        if self.dlg.searchMosaicCheckBox.isChecked():
            product_types.append(ProductType.mosaic.upper())
        if self.dlg.searchImageCheckBox.isChecked():
            product_types.append(ProductType.image.upper())
        if not product_types:
            product_types = [ProductType.mosaic.upper(), ProductType.image.upper()]
        return product_types

    def search_providers(self) -> Optional[List[str]]:
        """Provider filter to send with a search/template request.

        Only meaningful while the search is limited to available providers; when
        "Search only through available providers" is off, the (hidden) provider selection
        must NOT be sent — the search runs across all providers. An empty selection is
        also omitted (None), since the backend reads ``[]`` as "search no providers".
        """
        if not self.dlg.hideUnavailableResults.isChecked():
            return None
        selected = self.dlg.searchProvidersCombo.checkedItemsData()
        return selected or None

    def provider_index(self) -> int:
        return self.dlg.providerIndex()

    def ensure_search_provider(self, provider_service) -> None:
        """If the selected provider cannot search, switch the combo to the Mapflow imagery-search
        provider. Run before a search or a template create so the request goes to a searchable
        source."""
        try:
            supports_search = provider_service.providers[self.dlg.providerIndex()].meta_url is not None
        except (NotImplementedError, AttributeError):
            supports_search = False
        if not supports_search:
            self.dlg.setProviderIndex(provider_service.imagery_search_provider_index)

    def template_search_params(self, aoi_details=None) -> SearchParams:
        """The search filter widgets as a `SearchParams` schema, for creating/updating a template.

        Lives here because it reads the same search-tab widgets `search_parameters()` does, only
        shaped for the template endpoints (ISO date strings, the `SearchParams` dataclass). When
        ``aoi_details`` is None the geometry is omitted — a template's non-geometry params are
        updated that way (the PUT template endpoint rejects geometry).
        """
        off_nadir_min, off_nadir_max = self.off_nadir_bounds()
        iso = "yyyy-MM-ddTHH:mm:ss.zzz'Z'"
        return SearchParams(
            aoiDetails=aoi_details,
            acquisitionDateFrom=self.dlg.metadataFrom.dateTime().toUTC().toString(iso),
            acquisitionDateTo=self.dlg.metadataTo.dateTime().toUTC().toString(iso),
            maxCloudCover=self.dlg.maxCloudCover.value(),
            minAoiIntersectionPercent=self.dlg.minIntersection.value(),
            minOffNadirAngle=off_nadir_min,
            maxOffNadirAngle=off_nadir_max,
            hideUnavailable=self.dlg.hideUnavailableResults.isChecked(),
            productTypes=self.product_types() or [],
            dataProviders=self.search_providers(),
        )

    def switch_to_search_tab(self) -> None:
        """Bring the imagery-search tab to front (its objectName is historically 'providersTab')."""
        tab = self.dlg.tabWidget.findChild(QWidget, "providersTab")
        if tab is not None:
            self.dlg.tabWidget.setCurrentWidget(tab)

    # ---------- showing what a template searches for ----------

    def apply_search_params(self, search_params) -> None:
        """Populate the filter widgets from a template's stored ``searchParams`` (web parity: the
        user can see what the template searches for). The widgets stay editable — changing them
        affects the current search view only, never the template. Fields the template does not
        carry leave the corresponding widgets untouched.

        Deliberately not the same as `apply_baseline`, which restores the *fetched* parameters:
        this one skips an empty ``productTypes`` (a template that names none is not a template
        that wants neither box ticked) and always rewrites the provider combo, where the baseline
        leaves an absent provider list alone.
        """
        if not search_params:
            return
        if isinstance(search_params, dict):
            search_params = SearchParams.from_dict(search_params)

        date_from = utc_date_from_iso(search_params.acquisitionDateFrom)
        if date_from is not None:
            self.dlg.metadataFrom.setDate(date_from)
        date_to = utc_date_from_iso(search_params.acquisitionDateTo)
        if date_to is not None:
            self.dlg.metadataTo.setDate(date_to)
        if search_params.maxCloudCover is not None:
            self.dlg.maxCloudCover.setValue(int(round(search_params.maxCloudCover)))
        if search_params.minAoiIntersectionPercent is not None:
            self.dlg.minIntersection.setValue(int(round(search_params.minAoiIntersectionPercent)))
        if search_params.minOffNadirAngle is not None and search_params.maxOffNadirAngle is not None:
            self.dlg.set_off_nadir_range(int(round(search_params.minOffNadirAngle)),
                                         int(round(search_params.maxOffNadirAngle)))
        if search_params.hideUnavailable is not None:
            self.dlg.hideUnavailableResults.setChecked(bool(search_params.hideUnavailable))
        product_types = [str(pt).upper() for pt in (search_params.productTypes or [])]
        if product_types:
            self.dlg.searchMosaicCheckBox.setChecked(ProductType.mosaic.upper() in product_types)
            self.dlg.searchImageCheckBox.setChecked(ProductType.image.upper() in product_types)
        self.apply_providers_to_combo(search_params.dataProviders)

    def apply_providers_to_combo(self, data_providers: Optional[List[str]]) -> None:
        """Mirror ``search_providers()``: check the combo items whose api-name is in
        ``data_providers``; ``None``/empty means all providers were searched, shown as no checked
        items ("Show all")."""
        combo = self.dlg.searchProvidersCombo
        combo.deselectAllOptions()
        if not data_providers:
            return
        wanted = set(data_providers)
        for index in range(combo.count()):
            if combo.itemData(index) in wanted:
                combo.setItemCheckState(index, Qt.Checked)

    # ---------- the results table ----------

    def selected_image_id(self) -> Optional[str]:
        """Image id of the first selected results row, or None when nothing is selected."""
        selected = self.dlg.metadataTable.selectedItems()
        if not selected:
            return None
        return self.image_id_at(selected[0].row())

    def image_id_at(self, row: int) -> str:
        return self.dlg.metadataTable.item(row, self.config.SEARCH_ID_COLUMN_INDEX).text()

    def is_preview_column(self, column: int) -> bool:
        return column == self.config.PPRVIEW_INDEX_COLUMN

    def connect_cell_preview(self, handler) -> None:
        """(Re)wire the results table's 'Preview' cell click to ``handler``.

        The table is refilled on every local-filter change; connecting without disconnecting
        first stacks the connections, so one click would fire the preview several times and add
        several preview layers (feedback 4.2). The prior connection is dropped first.
        """
        self.disconnect_cell_preview()
        self._cell_preview_connection = self.dlg.metadataTable.cellClicked.connect(handler)

    def disconnect_cell_preview(self) -> None:
        try:
            self.dlg.metadataTable.disconnect(self._cell_preview_connection)
        except (AttributeError, TypeError, RuntimeError):
            # no previous connection, or its underlying C++ object is gone
            pass

    def clear_table(self) -> None:
        self.dlg.metadataTable.clearContents()
        self.dlg.metadataTable.setRowCount(0)

    def remove_more_button(self) -> None:
        """Drop the "load more" button left by a previous search, if any."""
        more_button = self.dlg.findChild(QPushButton,
                                         self.config.METADATA_MORE_BUTTON_OBJECT_NAME)
        if more_button:
            self.dlg.layoutMetadataTable.removeWidget(more_button)
            more_button.deleteLater()

    def fill_table(self, geoms, sort: bool = False) -> None:
        """Built-in Qt sorting stays OFF by default: results already arrive in the server's sort
        order, and a header click re-requests with sortBy/sortOrder rather than sorting locally."""
        self.dlg.fill_metadata_table(geoms, sort=sort)
        self.tableRefilled.emit()

    def metadata_row_count(self) -> int:
        return self.dlg.metadataTable.rowCount()

    # ---------- selection, for the table <-> footprint-layer sync ----------

    def selected_local_indices(self) -> List[str]:
        """The `local_index` of every selected row — the key the footprint layer is keyed by."""
        selected = self.dlg.metadataTable.selectedItems()
        if not selected:
            return []
        return [self.dlg.metadataTable.item(cell.row(), self.config.LOCAL_INDEX_COLUMN).text()
                for cell in selected]

    def selected_zoom(self) -> Optional[str]:
        """The zoom of the first selected row. Different zooms across a multi-selection are not
        allowed, so the first one speaks for all of them."""
        selected = self.dlg.metadataTable.selectedItems()
        if not selected:
            return None
        return self.dlg.metadataTable.item(selected[0].row(), self.config.ZOOM_COLUMN_INDEX).text()

    def set_zoom_silently(self, zoom: Optional[str]) -> None:
        """Set the zoom combo without emitting `currentIndexChanged`.

        Unblocked, that signal reaches `on_zoom_change` and fires a SECOND cost request — using
        the zoom from before this call, so the two race and the stale one can win.
        """
        index = -1 if zoom is None else self.dlg.zoomCombo.findText(zoom)
        self.dlg.zoomCombo.blockSignals(True)
        self.dlg.zoomCombo.setCurrentIndex(0 if index == -1 else index)
        self.dlg.zoomCombo.blockSignals(False)

    def select_rows_by_local_index(self, local_indices: List[str]) -> None:
        """Select the rows carrying these `local_index` values, clearing any other selection.

        Multi-select is turned on for the duration because `selectRow` otherwise replaces the
        previous selection instead of adding to it, and restored in a `finally` so an exception
        cannot leave the results table in a mode the user cannot get out of.
        """
        table = self.dlg.metadataTable
        table.setSelectionMode(QAbstractItemView.MultiSelection)
        try:
            rows = []
            for local_index in local_indices:
                rows += [item.row() for item in table.findItems(str(local_index), Qt.MatchExactly)
                         if item.column() == self.config.LOCAL_INDEX_COLUMN]
            table.clearSelection()
            for row in rows:
                table.selectRow(row)
        finally:
            table.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def clear_metadata_selection(self) -> None:
        self.dlg.metadataTable.clearSelection()

    def has_row_with_text(self, text: str) -> bool:
        return bool(self.dlg.metadataTable.findItems(text, Qt.MatchExactly))

    def connect_table_selection(self, handler):
        return self.dlg.metadataTable.itemSelectionChanged.connect(handler)

    def disconnect_table_selection(self, connection) -> None:
        """Drop the table->layer handler while the layer is driving the table.

        Guarded, unlike the call this replaces: Qt raises `TypeError` when the handle was never
        connected, and an unguarded raise here aborts the caller *after* it has switched the table
        to multi-select, leaving the results table stuck in a mode the user cannot leave.
        """
        try:
            self.dlg.metadataTable.itemSelectionChanged.disconnect(connection)
        except (RuntimeError, TypeError):
            pass

    # ---------- pagination ----------

    def show_pages(self, page_number: int, total_pages: int) -> None:
        self.dlg.enable_search_pages(True, page_number, total_pages)
        self.dlg.searchRightButton.setEnabled(page_number != total_pages)
        self.dlg.searchLeftButton.setEnabled(page_number != 1)

    def hide_pages(self) -> None:
        self.dlg.enable_search_pages(False)

    # ---------- server-side sort ----------

    def show_sort_indicator(self, column: int, descending: bool) -> None:
        """Every table (re)fill calls setSortingEnabled(False), which Qt implements as hiding the
        sort indicator — so it has to be put back after each fill, or the arrow flashes on click
        and immediately vanishes."""
        header = self.dlg.metadataTable.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(column, Qt.DescendingOrder if descending else Qt.AscendingOrder)

    # ---------- the local filter's widgets ----------

    def filter_widget_values(self) -> dict:
        """The filter widgets as plain values, for the criteria the local filter is computed from.
        `off_nadir_filtered` is False at the full 0-30 range, which means "no off-nadir filter"
        rather than "0 to 30" — an image with an unknown angle passes the first and fails the
        second."""
        min_off_nadir, max_off_nadir = self.dlg.off_nadir_range()
        return {
            "date_from": self.dlg.metadataFrom.date(),
            "date_to": self.dlg.metadataTo.date(),
            "max_cloud_cover": self.dlg.maxCloudCover.value(),
            "min_intersection": self.dlg.minIntersection.value(),
            "off_nadir_filtered": not self.dlg.off_nadir_is_full_range(),
            "min_off_nadir": min_off_nadir,
            "max_off_nadir": max_off_nadir,
        }

    def hide_unavailable_results(self) -> bool:
        return self.dlg.hideUnavailableResults.isChecked()

    def checked_provider_names(self) -> list:
        """The provider api-names ticked in the combo, whether or not they are being applied."""
        return self.dlg.searchProvidersCombo.checkedItemsData()

    def product_category_filter(self) -> Optional[set]:
        """The product categories to KEEP ({'MOSAIC'} or {'IMAGE'}), or ``None`` when both or
        neither Mosaic/Image is checked (= all, no filter)."""
        mosaic = self.dlg.searchMosaicCheckBox.isChecked()
        image = self.dlg.searchImageCheckBox.isChecked()
        if mosaic == image:  # both or neither -> show all
            return None
        return {ProductType.mosaic.upper()} if mosaic else {ProductType.image.upper()}

    def mark_unfit_rows(self, unfit: set) -> None:
        """Grey-out and disable (non-selectable) the rows whose image was filtered out; restore
        fit rows to normal. The row order already places the unfit rows last."""
        grey_text = QBrush(QColor(150, 150, 150))
        grey_bg = QBrush(QColor(235, 235, 235))
        table = self.dlg.metadataTable
        local_col = self.config.LOCAL_INDEX_COLUMN
        for row in range(table.rowCount()):
            key = table.item(row, local_col)
            if key is None:
                continue
            try:
                is_unfit = int(key.text()) in unfit
            except (TypeError, ValueError):
                continue
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item is None:
                    continue
                if is_unfit:
                    item.setForeground(grey_text)
                    item.setBackground(grey_bg)
                    item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
                else:
                    item.setForeground(QBrush())
                    item.setBackground(QBrush())
                    item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    # ---------- the widen (!) indicator ----------

    def show_widen_warning(self, tooltip: str) -> None:
        self.dlg.searchWidenWarning.setToolTip(tooltip)
        self.dlg.searchWidenWarning.setVisible(True)

    def hide_widen_warning(self) -> None:
        self.dlg.searchWidenWarning.setToolTip("")
        self.dlg.searchWidenWarning.setVisible(False)

    # ---------- the baseline the widen indicator compares against ----------

    def filter_baseline(self) -> dict:
        """Snapshot of the filter widgets, stored at search time as what later edits are compared
        against."""
        off_nadir_lo, off_nadir_hi = self.dlg.off_nadir_range()
        return {
            "date_from": self.dlg.metadataFrom.date(),
            "date_to": self.dlg.metadataTo.date(),
            "max_cloud_cover": self.dlg.maxCloudCover.value(),
            "min_intersection": self.dlg.minIntersection.value(),
            "min_off_nadir": off_nadir_lo,
            "max_off_nadir": off_nadir_hi,
            "product_types": [str(pt).upper() for pt in self.product_types()],
            "data_providers": self.search_providers() or [],
            "hide_unavailable": self.dlg.hideUnavailableResults.isChecked(),
        }

    def apply_baseline(self, baseline: dict) -> None:
        """Put the filter widgets back to a stored baseline. Only keys the baseline actually
        carries are restored — a search that did not send a filter must not have that filter
        invented here."""
        if baseline.get("date_from") is not None:
            self.dlg.metadataFrom.setDate(baseline["date_from"])
        if baseline.get("date_to") is not None:
            self.dlg.metadataTo.setDate(baseline["date_to"])
        if baseline.get("max_cloud_cover") is not None:
            self.dlg.maxCloudCover.setValue(int(round(baseline["max_cloud_cover"])))
        if baseline.get("min_intersection") is not None:
            self.dlg.minIntersection.setValue(int(round(baseline["min_intersection"])))
        base_off_lo = baseline.get("min_off_nadir")
        base_off_hi = baseline.get("max_off_nadir")
        if base_off_lo is not None and base_off_hi is not None:
            self.dlg.set_off_nadir_range(int(round(base_off_lo)), int(round(base_off_hi)))
        products = baseline.get("product_types")
        if products is not None:
            self.dlg.searchMosaicCheckBox.setChecked(ProductType.mosaic.upper() in products)
            self.dlg.searchImageCheckBox.setChecked(ProductType.image.upper() in products)
        if baseline.get("hide_unavailable") is not None:
            self.dlg.hideUnavailableResults.setChecked(bool(baseline["hide_unavailable"]))
        providers = baseline.get("data_providers")
        if providers is not None:
            self.apply_providers_to_combo(providers)
