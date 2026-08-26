from typing import List, Optional, Tuple

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QPushButton, QWidget

from ...dialogs.main_dialog import MainDialog
from ...schema.catalog import ProductType


class SearchView(QObject):
    """Every widget read and write for the imagery-search tab.

    Holds no service (`spec/007_architecture.md` § Layer rules): the controller reads the
    search parameters from here, hands them to `SearchService`, and pushes results back.

    The reads are grouped as `search_parameters()` rather than exposed one property per widget,
    because they are only ever wanted together — at the moment the user presses Search — and a
    single call is what makes "the request is built from what the widgets said *then*" true by
    construction instead of by convention.
    """

    def __init__(self, dlg: MainDialog, config):
        super().__init__()
        self.dlg = dlg
        self.config = config
        #: The current cellClicked->preview connection, so it can be dropped before rewiring.
        self._cell_preview_connection = None

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

    def switch_to_search_tab(self) -> None:
        """Bring the imagery-search tab to front (its objectName is historically 'providersTab')."""
        tab = self.dlg.tabWidget.findChild(QWidget, "providersTab")
        if tab is not None:
            self.dlg.tabWidget.setCurrentWidget(tab)

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

    # ---------- pagination ----------

    def show_pages(self, page_number: int, total_pages: int) -> None:
        self.dlg.enable_search_pages(True, page_number, total_pages)
        self.dlg.searchRightButton.setEnabled(page_number != total_pages)
        self.dlg.searchLeftButton.setEnabled(page_number != 1)

    def hide_pages(self) -> None:
        self.dlg.enable_search_pages(False)

    # ---------- the widen (!) indicator ----------

    def set_widen_warning_visible(self, visible: bool) -> None:
        self.dlg.searchWidenWarning.setVisible(visible)
