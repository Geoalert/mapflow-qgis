"""QGIS-tier tests for the footprint layer built from template search results.

Two behaviours are covered:
* `TemplateService.search_results_callback` populates ``app_context.search_footprints`` so a
  planned processing started from template results carries a ``dataProvider`` (regression:
  the source params used to omit it and the backend rejected creation with HTTP 400);
* the styled footprint layer is added to the map under the template's layer-tree group so
  the user can preview image footprints and request imagery previews.

The rendered page reaches the table as `searchResultsReady` rather than by the service touching
a widget (`spec/007_architecture.md` § Layer rules), so "the table was filled with X" is asserted
as "X was emitted", which is the same claim one layer out.
"""
import json
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from qgis.core import QgsProject

from mapflow import mapflow as mapflow_module
from mapflow.config import Config, ConfigColumns
from mapflow.model.provider.default import ImagerySearchProvider
from mapflow.functional.service import template_service as template_service_module
from mapflow.functional.service.search_service import SearchService
from mapflow.functional.service.template_service import TemplateService
from mapflow.mapflow import Mapflow

PLUGIN_DIR = os.path.dirname(mapflow_module.__file__)


def _image(image_id="4805123", product_type="Image", provider_name="orbview", is_new=False):
    return {
        "id": image_id,
        "footprint": {
            "type": "Polygon",
            "coordinates": [[[13.0, 52.0], [14.0, 52.0], [14.0, 51.0], [13.0, 51.0], [13.0, 52.0]]],
        },
        "pixelResolution": 0.5,
        "acquisitionDate": "2025-09-24T07:34:43.637Z",
        "productType": product_type,
        "sensor": "sensor-x",
        "colorBandOrder": "RGB",
        "cloudCover": 10.0,
        "offNadirAngle": 5.0,
        "providerName": provider_name,
        "zoom": "18",
        "previews": [],
        "isNew": is_new,
    }


def _service_with_search_provider(tmp_path, template_name="Template A"):
    """A real TemplateService over a real SearchService: these tests assert on the footprints it
    stores and where it puts the layer, so neither is mocked."""
    result_loader = MagicMock()
    provider_service = SimpleNamespace(
        providers=[ImagerySearchProvider(proxy="https://example.com/rest")]
    )
    template = SimpleNamespace(name=template_name, id="tpl-test") if template_name else None
    settings = MagicMock()
    settings.value.return_value = None  # no custom layerGroup -> falls back to plugin_name
    app_context = SimpleNamespace(
        temp_dir=str(tmp_path),
        search_footprints={},
        project=QgsProject(),
        settings=settings,
        plugin_name="Mapflow",
        metadata_layer=None,
        open_template_results_id=None,
        search_result_geojson=None,
        search_baseline_filters=None,
    )
    search_service = SearchService(iface=MagicMock(),
                                   app_context=app_context,
                                   http=MagicMock(),
                                   plugin_dir=PLUGIN_DIR,
                                   config=Config,
                                   config_search_columns=ConfigColumns(),
                                   result_loader=result_loader,
                                   provider_service=provider_service)
    service = TemplateService(app_context=app_context,
                              processing_service=SimpleNamespace(
                                  selected_template=lambda: template, api=MagicMock()),
                              plugin_dir=PLUGIN_DIR,
                              aoi_service=MagicMock(),
                              result_loader=result_loader,
                              search_service=search_service)
    return service


def _rendered(service):
    """The GeoJSON pages the service handed to the table, in order."""
    pages = []
    service.searchResultsReady.connect(pages.append)
    return pages


def _response(payload):
    response = MagicMock()
    response.readAll.return_value.data.return_value = json.dumps(payload).encode()
    return response


def test_template_callback_populates_search_footprints_with_provider_name(tmp_path):
    service = _service_with_search_provider(tmp_path)
    pages = _rendered(service)

    service.search_results_callback(_response({"images": [_image()], "total": 1}))

    footprints = service.app_context.search_footprints
    assert set(footprints) == {0}
    assert footprints[0].attribute("providerName") == "orbview"
    assert len(pages) == 1


def test_template_callback_keeps_product_type_clean_for_new_images(tmp_path):
    service = _service_with_search_provider(tmp_path)

    service.search_results_callback(_response({"images": [_image(is_new=True)], "total": 1}))

    # The footprint productType stays the raw value (it feeds product-type / zoom
    # consistency checks during params building); the new-image state is an icon, not text.
    assert service.app_context.search_footprints[0].attribute("productType") == "Image"


def test_template_callback_adds_footprint_layer_under_template_group(tmp_path):
    service = _service_with_search_provider(tmp_path, template_name="Template A")

    service.search_results_callback(_response({"images": [_image()], "total": 1}))

    root = service.app_context.project.layerTreeRoot()
    template_group = root.findGroup("Template A")
    assert template_group is not None, "footprint layer must live under the template-named group"
    layers = template_group.findLayers()
    assert len(layers) == 1
    added_layer = layers[0].layer()
    assert added_layer is service.app_context.metadata_layer
    assert added_layer.featureCount() == 1


def test_template_callback_keeps_product_type_text_clean_and_stores_new_flag(tmp_path):
    service = _service_with_search_provider(tmp_path)
    pages = _rendered(service)

    service.search_results_callback(_response({
        "images": [
            _image(image_id="img-new", is_new=True),
            _image(image_id="img-seen", is_new=False),
        ],
        "total": 2,
    }))

    geoms = pages[0]
    # The "new" state is shown with an icon now, so the product-type text stays clean.
    assert [f["properties"]["productType"] for f in geoms["features"]] == ["Image", "Image"]
    # Image DTOs are stored by id and carry the authoritative isNew flag for mark-seen.
    assert service.template_search_images["img-new"].isNew is True
    assert service.template_search_images["img-seen"].isNew is False


def test_the_dtos_are_stored_before_the_page_is_rendered(tmp_path):
    """The markers are drawn as part of rendering the page and read these DTOs, so a page
    emitted before they are stored would come up with no 'new' icons at all."""
    service = _service_with_search_provider(tmp_path)
    seen_when_rendered = []
    service.searchResultsReady.connect(
        lambda _geoms: seen_when_rendered.append(dict(service.template_search_images)))

    service.search_results_callback(
        _response({"images": [_image(image_id="img-new", is_new=True)], "total": 1}))

    assert "img-new" in seen_when_rendered[0]


def test_monitor_skips_current_search_metadata_layer():
    plugin = Mapflow.__new__(Mapflow)
    plugin.area_calculator_service = MagicMock()
    metadata_layer = MagicMock()
    metadata_layer.id.return_value = "meta-1"
    plugin.app_context = SimpleNamespace(metadata_layer=metadata_layer)
    # "is this the search-results layer?" is SearchService's answer since the search extraction.
    plugin.search_service = SearchService(iface=MagicMock(),
                                          app_context=plugin.app_context,
                                          http=MagicMock(),
                                          plugin_dir="",
                                          config=Config,
                                          config_search_columns=ConfigColumns(),
                                          result_loader=MagicMock(),
                                          provider_service=MagicMock())

    footprint_layer = MagicMock()  # same id as the current metadata layer -> skipped
    footprint_layer.id.return_value = "meta-1"
    aoi_layer = MagicMock()
    aoi_layer.id.return_value = "aoi-1"

    with patch.object(mapflow_module.layer_utils, "is_polygon_layer", return_value=True):
        plugin.monitor_polygon_layer_feature_selection([footprint_layer, aoi_layer])

    # The footprint (search-metadata) layer is skipped; a real AOI layer is still wired.
    footprint_layer.selectionChanged.connect.assert_not_called()
    aoi_layer.selectionChanged.connect.assert_called_once_with(
        plugin.area_calculator_service.calculate_aoi_area_selection
    )


def test_template_callback_alerts_and_skips_when_no_images(tmp_path, monkeypatch):
    service = _service_with_search_provider(tmp_path)
    pages = _rendered(service)
    emptied = []
    service.searchResultsEmpty.connect(lambda: emptied.append(True))
    alerts = []
    monkeypatch.setattr(template_service_module, "alert_info", lambda *a, **k: alerts.append(a))

    service.search_results_callback(_response({"images": []}))

    assert len(alerts) == 1
    assert emptied == [True]  # the table is emptied instead of being filled
    assert pages == []
    assert service.app_context.open_template_results_id is None
