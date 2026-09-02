"""QGIS-tier tests for server-side sorting of the imagery-search table.

Clicking a sortable column header re-runs the search with `sortBy`/`sortOrder` (a fresh
`/catalog/meta` request), not a local page sort. Only the columns the catalog API accepts
(config.SEARCH_SORT_FIELDS, the TemplateImagesSortBy tokens) react.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.config import Config, ConfigColumns
from mapflow.functional.service.search_service import SearchService
from mapflow.mapflow import Mapflow
from mapflow.schema.catalog import ImageCatalogRequestSchema


_ATTRS = list(ConfigColumns().METADATA_TABLE_ATTRIBUTES.values())


def _column(attr):
    return _ATTRS.index(attr)


def _search_service(sort_by, sort_order):
    """Real service: the sort state and the column->token lookup are its logic now. What stays in
    `mapflow.py` is only the choice of which endpoint to re-request from."""
    service = SearchService(iface=MagicMock(),
                            app_context=MagicMock(),
                            http=MagicMock(),
                            plugin_dir="",
                            config=Config,
                            config_search_columns=ConfigColumns(),
                            result_loader=MagicMock(),
                            provider_service=MagicMock())
    service.sort_by = sort_by
    service.sort_order = sort_order
    return service


def _plugin(sort_by="ACQUISITION_DATE", sort_order="DESC", in_template=False, rows=5):
    plugin = Mapflow.__new__(Mapflow)
    plugin.config = Config
    plugin.config_search_columns = ConfigColumns()
    plugin.search_service = _search_service(sort_by, sort_order)
    plugin.template_service = SimpleNamespace(in_template_mode=in_template)
    plugin.dlg = MagicMock()
    plugin.search_view = MagicMock()
    # The "have we searched yet" guard reads the row count through the view, not the dialog.
    plugin.search_view.metadata_row_count.return_value = rows
    plugin.get_metadata = MagicMock()
    plugin.template_controller = MagicMock()
    return plugin


def _sort_controller(sort_by="ACQUISITION_DATE", sort_order="DESC"):
    """Restoring the arrow after a re-fill is `SearchController`'s; the column<->token mapping it
    asks for is still the search service's."""
    from PyQt5.QtCore import QObject
    from mapflow.functional.controller.search_controller import SearchController
    controller = SearchController.__new__(SearchController)
    QObject.__init__(controller)
    controller.search_service = _search_service(sort_by, sort_order)
    controller.search_view = MagicMock()
    return controller


def test_backend_tokens_are_upper_snake_case():
    # Guards against drift from white-maps-backend TemplateImagesSortBy (UpperSnakecase).
    assert set(Config.SEARCH_SORT_FIELDS.values()) == {
        "PROVIDER_NAME", "SAT_ID", "CLOUD_COVER", "OFF_NADIR_ANGLE",
        "ACQUISITION_DATE", "ZOOM", "PIXEL_RESOLUTION",
    }


def test_click_new_sortable_column_sets_field_desc_and_researches():
    plugin = _plugin(sort_by="ACQUISITION_DATE", sort_order="DESC")

    plugin.on_metadata_header_clicked(_column("cloudCover"))

    assert plugin.search_service.sort_by == "CLOUD_COVER"
    assert plugin.search_service.sort_order == "DESC"
    plugin.get_metadata.assert_called_once()


def test_click_same_column_toggles_order():
    plugin = _plugin(sort_by="ACQUISITION_DATE", sort_order="DESC")

    plugin.on_metadata_header_clicked(_column("acquisitionDate"))
    assert plugin.search_service.sort_order == "ASC"
    plugin.on_metadata_header_clicked(_column("acquisitionDate"))
    assert plugin.search_service.sort_order == "DESC"
    assert plugin.search_service.sort_by == "ACQUISITION_DATE"
    assert plugin.get_metadata.call_count == 2


def test_non_sortable_column_does_nothing():
    plugin = _plugin()

    plugin.on_metadata_header_clicked(_column("productType"))  # not in SEARCH_SORT_FIELDS
    plugin.on_metadata_header_clicked(_column("preview"))

    assert plugin.search_service.sort_by == "ACQUISITION_DATE"  # unchanged
    plugin.get_metadata.assert_not_called()


def test_template_mode_reloads_template_search_with_new_sort():
    plugin = _plugin(sort_by="ACQUISITION_DATE", sort_order="DESC", in_template=True)

    plugin.on_metadata_header_clicked(_column("cloudCover"))

    # Template results re-fetch (first page) with the updated sort; the regular search is untouched.
    assert plugin.search_service.sort_by == "CLOUD_COVER"
    plugin.template_controller.load_search_page.assert_called_once_with(0)
    plugin.get_metadata.assert_not_called()


def test_regular_mode_does_not_reload_template():
    plugin = _plugin(in_template=False)

    plugin.on_metadata_header_clicked(_column("cloudCover"))

    plugin.get_metadata.assert_called_once()
    plugin.template_controller.load_search_page.assert_not_called()


def test_no_results_yet_does_not_search():
    plugin = _plugin(rows=0)

    plugin.on_metadata_header_clicked(_column("cloudCover"))

    plugin.get_metadata.assert_not_called()


def test_restore_sort_indicator_maps_token_to_its_column():
    # After a re-fill hides the arrow, the indicator is restored on the column matching the token.
    controller = _sort_controller(sort_by="CLOUD_COVER")

    controller.restore_sort_indicator()

    assert controller.search_view.show_sort_indicator.call_args.args == (_column("cloudCover"),)


def test_restore_sort_indicator_carries_the_current_order():
    controller = _sort_controller(sort_by="CLOUD_COVER", sort_order="ASC")

    controller.restore_sort_indicator()

    assert controller.search_view.show_sort_indicator.call_args.kwargs["descending"] is False


def test_restore_sort_indicator_noop_without_active_sort():
    controller = _sort_controller(sort_by=None)

    controller.restore_sort_indicator()

    controller.search_view.show_sort_indicator.assert_not_called()


def test_request_schema_serializes_sort_fields():
    body = json.loads(ImageCatalogRequestSchema(
        aoi={"type": "Polygon", "coordinates": []},
        sortBy="ACQUISITION_DATE", sortOrder="DESC").as_json())
    assert body["sortBy"] == "ACQUISITION_DATE"
    assert body["sortOrder"] == "DESC"


def test_template_images_request_serializes_sort_fields():
    from mapflow.schema.template import TemplateImagesRequestSchema
    body = json.loads(TemplateImagesRequestSchema(
        sortBy="PIXEL_RESOLUTION", sortOrder="ASC").as_json())
    assert body["sortBy"] == "PIXEL_RESOLUTION"
    assert body["sortOrder"] == "ASC"
