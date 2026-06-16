"""QGIS-tier tests for resolving the data provider when starting a planned
processing from template search results.

Regression: ``get_selected_template_callback`` filled the search table but never
populated ``app_context.search_footprints``. As a result the source params built
for the processing carried ``imageIds`` but no ``dataProvider`` (resolved from the
footprint ``providerName``), and the backend rejected creation with HTTP 400.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.entity.provider.default import ImagerySearchProvider
from mapflow.mapflow import Mapflow


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


def _plugin_with_search_provider(tmp_path):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.alert = MagicMock()
    plugin.dlg = MagicMock()
    plugin.provider_service = SimpleNamespace(
        providers=[ImagerySearchProvider(proxy="https://example.com/rest")]
    )
    plugin.app_context = SimpleNamespace(temp_dir=str(tmp_path), search_footprints={})
    return plugin


def _response(payload):
    response = MagicMock()
    response.readAll.return_value.data.return_value = json.dumps(payload).encode()
    return response


def test_template_callback_populates_search_footprints_with_provider_name(tmp_path):
    plugin = _plugin_with_search_provider(tmp_path)

    plugin.get_selected_template_callback(_response({"images": [_image()], "total": 1}))

    footprints = plugin.app_context.search_footprints
    assert set(footprints) == {0}
    assert footprints[0].attribute("providerName") == "orbview"
    # The metadata table is still rendered.
    plugin.dlg.fill_metadata_table.assert_called_once()


def test_template_callback_keeps_product_type_clean_for_new_images(tmp_path):
    plugin = _plugin_with_search_provider(tmp_path)

    plugin.get_selected_template_callback(_response({"images": [_image(is_new=True)], "total": 1}))

    # The display-only "(new)" marker must not leak into the footprint productType,
    # which feeds product-type / zoom consistency checks during params building.
    assert plugin.app_context.search_footprints[0].attribute("productType") == "Image"


def test_template_callback_alerts_and_skips_when_no_images(tmp_path):
    plugin = _plugin_with_search_provider(tmp_path)

    plugin.get_selected_template_callback(_response({"images": []}))

    plugin.alert.assert_called_once()
    plugin.dlg.fill_metadata_table.assert_not_called()
