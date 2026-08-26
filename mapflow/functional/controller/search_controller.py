from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox

from ..service.alert_service import alert
from ..service.preview_service import PreviewService
from ..service.provider_service import ProviderService
from ..service.search_service import SearchService
from ..view.search_view import SearchView
from ...model.provider import ImagerySearchProvider


class SearchController(QObject):
    """The imagery-search tab's preview dispatch: which image to preview, and from where.

    Scope today is deliberately small — the three preview-dispatch handlers and their wiring.
    A controller may own a signal connection only when it owns the *handler*; the run, sort and
    pagination handlers still call collaborators that have not been extracted (provider
    selection, the template search loader, the local filter), so their connections stay in
    `mapflow.py` until those handlers can move here. This grows as they do, the same way
    `ProcessingController` started with AOI selection alone.
    """

    def __init__(self,
                 search_service: SearchService,
                 search_view: SearchView,
                 preview_service: PreviewService,
                 provider_service: ProviderService,
                 search_button,
                 metadata_table):
        super().__init__()
        self.search_service = search_service
        self.search_view = search_view
        self.preview_service = preview_service
        self.provider_service = provider_service

        # Owned handlers, so the connections are owned here too.
        search_button.clicked.connect(self.preview_or_search)
        metadata_table.cellDoubleClicked.connect(self.preview)
        # cellClicked -> preview is rewired on every table refill (see reconnect_cell_preview).
        self.reconnect_cell_preview()

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
        """Rewire the Preview-cell click after a table refill. Public because `apply_local_filter`
        (still in `mapflow.py`) drives it — it moves here with the local filter."""
        self.search_view.connect_cell_preview(self.preview_search_from_cell)
