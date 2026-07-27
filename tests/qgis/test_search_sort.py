"""QGIS-tier tests for server-side sorting of the imagery-search table.

Clicking a sortable column header re-runs the search with `sortBy`/`sortOrder` (a fresh
`/catalog/meta` request), not a local page sort. Only the columns the catalog API accepts
(config.SEARCH_SORT_FIELDS, the TemplateImagesSortBy tokens) react.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.config import Config, ConfigColumns
from mapflow.mapflow import Mapflow
from mapflow.schema.catalog import ImageCatalogRequestSchema


_ATTRS = list(ConfigColumns().METADATA_TABLE_ATTRIBUTES.values())


def _column(attr):
    return _ATTRS.index(attr)


def _plugin(sort_by="ACQUISITION_DATE", sort_order="DESC", in_template=False, rows=5):
    plugin = Mapflow.__new__(Mapflow)
    plugin.config = Config
    plugin.config_search_columns = ConfigColumns()
    plugin.processing_service = SimpleNamespace(in_template_mode=in_template)
    plugin.dlg = MagicMock()
    plugin.dlg.metadataTable.rowCount.return_value = rows
    plugin._search_sort_by = sort_by
    plugin._search_sort_order = sort_order
    plugin._update_search_sort_indicator = MagicMock()
    plugin.get_metadata = MagicMock()
    plugin._load_template_search_page = MagicMock()
    return plugin


def test_backend_tokens_are_upper_snake_case():
    # Guards against drift from white-maps-backend TemplateImagesSortBy (UpperSnakecase).
    assert set(Config.SEARCH_SORT_FIELDS.values()) == {
        "PROVIDER_NAME", "SAT_ID", "CLOUD_COVER", "OFF_NADIR_ANGLE",
        "ACQUISITION_DATE", "ZOOM", "PIXEL_RESOLUTION",
    }


def test_click_new_sortable_column_sets_field_desc_and_researches():
    plugin = _plugin(sort_by="ACQUISITION_DATE", sort_order="DESC")

    plugin.on_metadata_header_clicked(_column("cloudCover"))

    assert plugin._search_sort_by == "CLOUD_COVER"
    assert plugin._search_sort_order == "DESC"
    plugin.get_metadata.assert_called_once()


def test_click_same_column_toggles_order():
    plugin = _plugin(sort_by="ACQUISITION_DATE", sort_order="DESC")

    plugin.on_metadata_header_clicked(_column("acquisitionDate"))
    assert plugin._search_sort_order == "ASC"
    plugin.on_metadata_header_clicked(_column("acquisitionDate"))
    assert plugin._search_sort_order == "DESC"
    assert plugin._search_sort_by == "ACQUISITION_DATE"
    assert plugin.get_metadata.call_count == 2


def test_non_sortable_column_does_nothing():
    plugin = _plugin()

    plugin.on_metadata_header_clicked(_column("productType"))  # not in SEARCH_SORT_FIELDS
    plugin.on_metadata_header_clicked(_column("preview"))

    assert plugin._search_sort_by == "ACQUISITION_DATE"  # unchanged
    plugin.get_metadata.assert_not_called()


def test_template_mode_reloads_template_search_with_new_sort():
    plugin = _plugin(sort_by="ACQUISITION_DATE", sort_order="DESC", in_template=True)

    plugin.on_metadata_header_clicked(_column("cloudCover"))

    # Template results re-fetch (first page) with the updated sort; the regular search is untouched.
    assert plugin._search_sort_by == "CLOUD_COVER"
    plugin._load_template_search_page.assert_called_once_with(0)
    plugin.get_metadata.assert_not_called()


def test_regular_mode_does_not_reload_template():
    plugin = _plugin(in_template=False)

    plugin.on_metadata_header_clicked(_column("cloudCover"))

    plugin.get_metadata.assert_called_once()
    plugin._load_template_search_page.assert_not_called()


def test_no_results_yet_does_not_search():
    plugin = _plugin(rows=0)

    plugin.on_metadata_header_clicked(_column("cloudCover"))

    plugin.get_metadata.assert_not_called()


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
