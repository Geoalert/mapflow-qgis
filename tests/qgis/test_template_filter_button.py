"""QGIS-tier tests for the template-results Filter button (T7). The template images endpoint
filters a template's search results server-side (date range + cloud cover) and returns them
paginated, WITHOUT modifying the template. The Filter button re-issues the template search
with the current filter widgets; the applied filters are sticky across AOI selection and
paging. Intersection %, providers and product types are not supported for template filtering."""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.api.processing_api import ProcessingApi


_DEFAULT_TEMPLATE = object()


def _plugin(active_template=_DEFAULT_TEMPLATE):
    from mapflow.mapflow import Mapflow
    if active_template is _DEFAULT_TEMPLATE:
        active_template = SimpleNamespace(id="tpl-1")
    plugin = Mapflow.__new__(Mapflow)
    plugin.dlg = MagicMock()
    plugin.search_page_limit = 5
    plugin.search_page_offset = 0
    plugin._template_search_aoi_filter = None
    plugin._template_search_filters = None
    plugin.dlg.maxCloudCover.value.return_value = 30
    plugin.dlg.metadataFrom.dateTime.return_value.toUTC.return_value.toString.return_value = "2025-01-01T00:00:00.000Z"
    plugin.dlg.metadataTo.dateTime.return_value.toUTC.return_value.toString.return_value = "2025-06-01T00:00:00.000Z"
    plugin.processing_service = SimpleNamespace(active_template=active_template, api=MagicMock())
    plugin._aoi_ids_from_template = MagicMock(return_value=[])
    plugin.get_selected_template_callback = MagicMock()
    return plugin


def test_collect_filters_returns_supported_subset():
    plugin = _plugin()

    filters = plugin._collect_template_search_filters()

    assert filters == {
        "acquisition_date_from": "2025-01-01T00:00:00.000Z",
        "acquisition_date_to": "2025-06-01T00:00:00.000Z",
        "max_cloud_cover": 30,
    }
    # intersection %, providers, product types are NOT sent for template filtering
    assert "min_intersection" not in filters
    assert "data_providers" not in filters


def test_filter_button_sends_filters_and_resets_to_first_page():
    plugin = _plugin()

    plugin.filter_template_results()

    assert plugin._template_search_filters["max_cloud_cover"] == 30
    kwargs = plugin.processing_service.api.get_template_images.call_args.kwargs
    assert kwargs["max_cloud_cover"] == 30
    assert kwargs["acquisition_date_from"] == "2025-01-01T00:00:00.000Z"
    assert kwargs["offset"] == 0


def test_applied_filters_are_sticky_across_pagination():
    plugin = _plugin()
    plugin._template_search_filters = {"max_cloud_cover": 10}

    plugin._load_template_search_page(offset=5)

    kwargs = plugin.processing_service.api.get_template_images.call_args.kwargs
    assert kwargs["max_cloud_cover"] == 10
    assert kwargs["offset"] == 5


def test_unfiltered_load_sends_no_filter_params():
    plugin = _plugin()

    plugin._load_template_search(plugin.processing_service.active_template)

    kwargs = plugin.processing_service.api.get_template_images.call_args.kwargs
    assert "max_cloud_cover" not in kwargs
    assert "acquisition_date_from" not in kwargs


def test_filter_button_noop_without_active_template():
    plugin = _plugin(active_template=None)

    plugin.filter_template_results()

    plugin.processing_service.api.get_template_images.assert_not_called()


def test_api_get_template_images_sends_only_provided_filters():
    http = MagicMock()
    api = ProcessingApi.__new__(ProcessingApi)
    api.http = http

    api.get_template_images(
        template_id="tpl-1",
        callback=lambda r: None,
        limit=5,
        offset=10,
        aoi_ids=["a1"],
        acquisition_date_from="2025-01-01T00:00:00.000Z",
        max_cloud_cover=25,
    )

    body = json.loads(http.post.call_args.kwargs["body"].decode())
    assert body["limit"] == 5 and body["offset"] == 10
    assert body["aoiIds"] == ["a1"]
    assert body["acquisitionDateFrom"] == "2025-01-01T00:00:00.000Z"
    assert body["maxCloudCover"] == 25
    # None-valued filters are omitted entirely
    assert "acquisitionDateTo" not in body
    assert "minResolution" not in body
