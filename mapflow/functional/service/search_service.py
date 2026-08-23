import json
import logging
import os
from typing import List, Optional

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest
from qgis.core import QgsGeometry, QgsVectorLayer

from ..app_context import AppContext
from .alert_service import alert, alert_info
from ...http import api_message_parser
from ...model.provider import ImagerySearchProvider, ProviderInterface
from ...schema import ImageCatalogRequestSchema, ImageCatalogResponseSchema
from ...schema.catalog import ProductType
from .alert_service import report_http_error

logger = logging.getLogger(__name__)


class SearchService(QObject):
    """The imagery-search request, its results, and the footprints layer they are drawn on.

    Holds no widget (`spec/007_architecture.md` § Layer rules). Anything the UI must do in
    response leaves as a signal and `SearchController` drives the view.

    Two things are deliberately *not* here:

    * choosing between a regular search and a template's search. Both paging and header-sort
      pick one or the other from `in_template_mode`, which is coordination between two regions
      — the controller's job, not this service's.
    * the filter widget reads. They arrive as arguments, gathered by `SearchView` in one call at
      the moment Search is pressed.
    """

    #: A page of results arrived: the GeoJSON to render, ready for the table.
    resultsReceived = pyqtSignal(object)
    #: The footprints layer was (re)built. The controller wires its selection to the table.
    metadataLayerReady = pyqtSignal(object)
    #: Pagination for the page just received: 1-based page number and total pages.
    pagerChanged = pyqtSignal(int, int)
    #: There is only one page; the pager should go away.
    pagerHidden = pyqtSignal()

    def __init__(self,
                 iface,
                 app_context: AppContext,
                 http,
                 plugin_dir: str,
                 config,
                 config_search_columns,
                 result_loader,
                 provider_service):
        super().__init__()
        self.iface = iface
        self.app_context = app_context
        self.http = http
        self.plugin_dir = plugin_dir
        self.config = config
        self.config_search_columns = config_search_columns
        self.result_loader = result_loader
        self.provider_service = provider_service
        self.page_offset = 0
        self.page_limit = config.SEARCH_RESULTS_PAGE_LIMIT
        #: Server-side sort. Held here rather than in the view because a template's search sends
        #: the same two parameters to a different endpoint.
        self.sort_by = "ACQUISITION_DATE"
        self.sort_order = "DESC"

    # ---------- the provider that can search ----------

    @property
    def imagery_search_provider(self):
        for provider in self.provider_service.providers:
            if isinstance(provider, ImagerySearchProvider):
                return provider
        return None

    def is_search_metadata_layer(self, layer) -> bool:
        """True if `layer` is the current imagery-search footprints layer.

        Metadata-layer creators assign ``app_context.metadata_layer`` before adding the
        layer to the project, so this is reliable at ``layersAdded`` time.
        """
        metadata_layer = self.app_context.metadata_layer
        if metadata_layer is None:
            return False
        try:
            return layer.id() == metadata_layer.id()
        except RuntimeError:  # metadata layer was deleted
            return False

    # ---------- the request ----------

    def search(self,
               aoi: QgsGeometry,
               provider: ProviderInterface,
               aoi_layer,
               baseline_filters: dict,
               from_: Optional[str] = None,
               to: Optional[str] = None,
               min_resolution: Optional[float] = None,
               max_resolution: Optional[float] = None,
               max_cloud_cover: Optional[float] = None,
               min_off_nadir_angle: Optional[float] = None,
               max_off_nadir_angle: Optional[float] = None,
               min_intersection: Optional[float] = None,
               offset: Optional[int] = 0,
               hide_unavailable: Optional[bool] = False,
               product_types: Optional[List[ProductType]] = None,
               search_providers: Optional[List[str]] = None) -> None:
        """Ask the Mapflow catalog for imagery over ``aoi``. Filtering is server-side.

        ``aoi_layer`` is where the footprints layer will be placed relative to, resolved now
        rather than in the callback: the request is the moment the user expressed the intent, and
        the combo may have moved on by the time the response lands.
        """
        self.app_context.metadata_aoi = aoi
        # Remember what this search actually asks the server for, so the widen (!) indicator can
        # flag later widget edits that ask for MORE than was fetched (which local filtering can't
        # surface without a fresh Search).
        self.app_context.search_baseline_filters = baseline_filters
        request_payload = ImageCatalogRequestSchema(aoi=json.loads(aoi.asJson()),
                                                    acquisitionDateFrom=from_,
                                                    acquisitionDateTo=to,
                                                    minResolution=min_resolution,
                                                    maxResolution=max_resolution,
                                                    maxCloudCover=max_cloud_cover,
                                                    minOffNadirAngle=min_off_nadir_angle,
                                                    maxOffNadirAngle=max_off_nadir_angle,
                                                    minAoiIntersectionPercent=min_intersection,
                                                    limit=self.page_limit,
                                                    offset=offset,
                                                    hideUnavailable=hide_unavailable,
                                                    productTypes=product_types,
                                                    dataProviders=search_providers,
                                                    sortBy=self.sort_by,
                                                    sortOrder=self.sort_order)
        self.http.post(url=provider.meta_url,
                       body=request_payload.as_json().encode(),
                       headers={},
                       callback=self.search_callback,
                       callback_kwargs={"aoi_layer": aoi_layer},
                       error_handler=self.search_error_handler,
                       use_default_error_handler=False,
                       timeout=60)

    def search_error_handler(self, response: QNetworkReply):
        title = self.tr("We couldn't get metadata from the Mapflow Imagery Catalog")
        error = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if error is not None:
            title += self.tr(". Error {error}").format(error=error)
        report_http_error(response,
                          plugin_version=self.app_context.plugin_version,
                          title=title,
                          error_message_parser=api_message_parser)

    def search_callback(self, response: QNetworkReply, aoi_layer=None):
        response_json = json.loads(response.readAll().data())
        if not response_json.get("images"):
            alert_info(self.tr('No images match your criteria. Try relaxing the filters.'))
            return
        response_data = ImageCatalogResponseSchema(**response_json)
        geoms = response_data.as_geojson()
        # Add index to map table and layer
        for position, feature in enumerate(geoms.get("features", ())):
            feature['properties']['local_index'] = position

        # Save the current search results to load later
        provider = self.imagery_search_provider
        save_failed_message = self.tr(
            "<b>Results could not be loaded </b><br>Please, make sure you chose the right output "
            "folder in the Settings tab and you have access rights to this folder")
        try:
            filename = provider.save_search_layer(self.app_context.temp_dir, geoms)
        except OSError:
            # The case the message describes: missing/unwritable output folder.
            alert(save_failed_message)
            return
        except Exception:
            logger.exception("Unexpected error saving the search layer")
            alert(save_failed_message)
            return
        self.display_metadata_geojson_layer(filename, f"{provider.name} metadata", aoi_layer)
        # Retain the raw results so the instant local filter can reorder/re-render them without
        # a new request.
        self.app_context.search_result_geojson = geoms
        self.resultsReceived.emit(geoms)
        self.update_pager(response_data.total, response_data.limit, response_data.offset)

    # ---------- the footprints layer ----------

    def display_metadata_geojson_layer(self, filename, layer_name, aoi_layer=None):
        self.remove_metadata_layer()
        # Assigned (before add_layer) so the AOI-area monitor recognizes and skips it.
        self.app_context.metadata_layer = QgsVectorLayer(filename, layer_name, 'ogr')
        self.app_context.metadata_layer.loadNamedStyle(
            os.path.join(self.plugin_dir, 'static', 'styles', 'metadata.qml'))
        # Place search results just under the AOI layer, if that layer has a legend node.
        # (A layer added with addToLegend=False has no tree node -> findLayer returns None;
        # fall back to a plain add instead of dereferencing a missing parent.)
        aoi_layer_tree = (self.app_context.project.layerTreeRoot().findLayer(aoi_layer.id())
                          if aoi_layer else None)
        if aoi_layer_tree is not None and aoi_layer_tree.parent() is not None:
            index = aoi_layer_tree.parent().children().index(aoi_layer_tree)
            self.result_loader.add_layer(layer=self.app_context.metadata_layer, order=index + 1)
        else:
            self.result_loader.add_layer(layer=self.app_context.metadata_layer)
        self.app_context.search_footprints = {
            feature['local_index']: feature
            for feature in self.app_context.metadata_layer.getFeatures()
        }
        self.metadataLayerReady.emit(self.app_context.metadata_layer)

    def remove_metadata_layer(self) -> None:
        try:
            self.app_context.project.removeMapLayer(self.app_context.metadata_layer)
        except (AttributeError, RuntimeError):  # metadata layer has been deleted
            pass

    def clear(self) -> None:
        """Drop the results, the layer and the retained baseline. The widen (!) indicator is the
        controller's to hide — this only makes it meaningless."""
        self.remove_metadata_layer()
        self.app_context.open_template_results_id = None
        self.app_context.search_result_geojson = None
        self.app_context.search_baseline_filters = None
        if self.app_context.search_provider:
            self.app_context.search_provider.clear_saved_search(self.app_context.temp_dir)

    # ---------- pagination ----------

    def update_pager(self, total: int, limit: int, offset: int) -> None:
        """Recompute paging from a response's ``total``/``limit``/``offset``. Shared by regular
        search and template search (T6): template results used to fill the table but never toggle
        the pager."""
        if limit and total > limit:
            self.page_offset = offset
            self.page_limit = limit
            quotient, remainder = divmod(total, limit)
            total_pages = quotient + (remainder > 0)
            page_number = int(offset / limit) + 1
            self.pagerChanged.emit(page_number, total_pages)
        else:
            self.pagerHidden.emit()

    def next_page_offset(self) -> int:
        return self.page_offset + self.page_limit

    def previous_page_offset(self) -> int:
        return self.page_offset - self.page_limit

    # ---------- sort ----------

    def sort_column_field(self, column: int) -> Optional[str]:
        """The API sort token for a table column, or None when that column is not sortable.

        Only the columns the API can sort on (``config.SEARCH_SORT_FIELDS``) react; the rest
        (preview, product type, band order, image id) do nothing.
        """
        attributes = tuple(self.config_search_columns.METADATA_TABLE_ATTRIBUTES.values())
        if not 0 <= column < len(attributes):
            return None
        return self.config.SEARCH_SORT_FIELDS.get(attributes[column])

    def toggle_sort(self, sort_field: str) -> None:
        """Apply ``sort_field``, flipping ASC/DESC when it is already the active one."""
        if self.sort_by == sort_field:
            self.sort_order = "ASC" if self.sort_order == "DESC" else "DESC"
        else:
            self.sort_by = sort_field
            self.sort_order = "DESC"

    def active_sort_column(self) -> Optional[int]:
        """The table column the active sort corresponds to, for redrawing the indicator."""
        if not self.sort_by:
            return None
        attribute = next((attr for attr, token in self.config.SEARCH_SORT_FIELDS.items()
                          if token == self.sort_by), None)
        attributes = tuple(self.config_search_columns.METADATA_TABLE_ATTRIBUTES.values())
        if attribute in attributes:
            return attributes.index(attribute)
        return None
