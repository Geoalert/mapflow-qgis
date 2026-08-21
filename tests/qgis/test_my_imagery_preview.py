"""QGIS-tier tests for the My Imagery previews that put a raster on the map.

These moved from `DataCatalogService` to `PreviewService` with the preview extraction, and the
move found them untested: nothing failed when they changed owner, which is exactly the state
`spec/007_architecture.md` forbids leaving a behaviour in. Written here because the boundary
they sit on is the one worth pinning — *which* mosaic or image is selected is the catalog's
business, putting the resulting raster on the map is this service's.

The panel thumbnail (`DataCatalogService.get_image_preview_s`) deliberately stayed behind: it
paints a QImage into a widget and never touches the map.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from qgis.core import QgsGeometry

from mapflow.functional.service.preview_service import PreviewService


@pytest.fixture
def catalog():
    catalog = MagicMock()
    catalog.selected_mosaic.return_value = None
    catalog.selected_image.return_value = None
    return catalog


@pytest.fixture
def service(catalog):
    return PreviewService(iface=MagicMock(),
                          app_context=SimpleNamespace(project=MagicMock()),
                          http=MagicMock(),
                          plugin_dir="",
                          config=MagicMock(),
                          result_loader=MagicMock(),
                          processing_service=SimpleNamespace(in_template_mode=False,
                                                             active_template=None),
                          data_catalog_service=catalog)


@pytest.fixture
def alerts(monkeypatch):
    shown = []
    monkeypatch.setattr("mapflow.functional.service.preview_service.alert_info",
                        lambda message, *a, **kw: shown.append(message))
    return shown


# ---------- mosaics ----------

def test_previewing_a_mosaic_requests_the_extent_for_its_tile_layer(service, catalog):
    catalog.selected_mosaic.return_value = SimpleNamespace(
        name="My collection",
        rasterLayer=SimpleNamespace(tileUrl="https://host/tiles/{z}/{x}/{y}.png",
                                    tileJsonUrl="https://host/tiles/tile.json"))

    service.preview_my_imagery_mosaic()

    args = catalog.api.request_mosaic_extent.call_args.args
    # The tile JSON URL is what carries the bounds; the layer is built from the tile URL.
    assert args[0] == "https://host/tiles/tile.json"
    assert args[1].name() == "My collection"


def test_previewing_no_mosaic_says_so_and_requests_nothing(service, catalog, alerts):
    catalog.selected_mosaic.return_value = None

    service.preview_my_imagery_mosaic()

    catalog.api.request_mosaic_extent.assert_not_called()
    assert len(alerts) == 1


def test_a_mosaic_without_a_raster_layer_is_not_a_crash(service, catalog, alerts):
    """A collection that has no imagery yet has no rasterLayer, so reading tileUrl raises."""
    catalog.selected_mosaic.return_value = SimpleNamespace(name="Empty", rasterLayer=None)

    service.preview_my_imagery_mosaic()

    catalog.api.request_mosaic_extent.assert_not_called()
    assert len(alerts) == 1


# ---------- images ----------

def test_previewing_an_image_sends_its_footprint(service, catalog):
    catalog.selected_image.return_value = SimpleNamespace(
        footprint="POLYGON((0 0,0 1,1 1,1 0,0 0))", filename="scene.tif")

    service.preview_my_imagery_image()

    kwargs = catalog.api.get_image_preview_l.call_args.kwargs
    assert kwargs["image_name"] == "scene.tif"
    assert kwargs["footprint"].asWkt().startswith("Polygon")
    # The reply is georeferenced by this service, not by the catalog.
    assert kwargs["callback"] == service.display_my_imagery_image


def test_previewing_no_image_requests_nothing(service, catalog):
    catalog.selected_image.return_value = None

    service.preview_my_imagery_image()

    catalog.api.get_image_preview_l.assert_not_called()


def test_displaying_an_image_preview_activates_and_zooms_to_it(service):
    layer = MagicMock()
    service.result_loader.display_preview_with_gcp.return_value = layer

    service.display_my_imagery_image(response=MagicMock(),
                                     footprint=QgsGeometry.fromWkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
                                     image_name="scene.tif")

    service.iface.setActiveLayer.assert_called_once_with(layer)
    service.iface.zoomToActiveLayer.assert_called_once()


def test_a_preview_that_failed_to_georeference_is_not_zoomed_to(service):
    """display_preview_with_gcp returns None when it cannot build the layer; zooming to that
    would raise inside a QGIS call rather than simply doing nothing."""
    service.result_loader.display_preview_with_gcp.return_value = None

    service.display_my_imagery_image(response=MagicMock(),
                                     footprint=QgsGeometry.fromWkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
                                     image_name="scene.tif")

    service.iface.setActiveLayer.assert_not_called()
    service.iface.zoomToActiveLayer.assert_not_called()
