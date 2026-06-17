"""QGIS-tier tests for the footprint layer built from template search results.

Two behaviours are covered:
* ``get_selected_template_callback`` populates ``app_context.search_footprints`` so a
  planned processing started from template results carries a ``dataProvider`` (regression:
  the source params used to omit it and the backend rejected creation with HTTP 400);
* the styled footprint layer is added to the map under the template's layer-tree group so
  the user can preview image footprints and request imagery previews.
"""
import json
import os
from types import SimpleNamespace
from unittest.mock import MagicMock

from qgis.core import QgsProject

from mapflow import mapflow as mapflow_module
from mapflow.entity.provider.default import ImagerySearchProvider
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


def _plugin_with_search_provider(tmp_path, template_name="Template A"):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.alert = MagicMock()
    plugin.dlg = MagicMock()
    plugin.plugin_dir = PLUGIN_DIR
    plugin.result_loader = MagicMock()
    plugin.provider_service = SimpleNamespace(
        providers=[ImagerySearchProvider(proxy="https://example.com/rest")]
    )
    template = SimpleNamespace(name=template_name) if template_name else None
    plugin.processing_service = SimpleNamespace(selected_template=lambda: template)
    settings = MagicMock()
    settings.value.return_value = None  # no custom layerGroup -> falls back to plugin_name
    plugin.app_context = SimpleNamespace(
        temp_dir=str(tmp_path),
        search_footprints={},
        project=QgsProject(),
        settings=settings,
        plugin_name="Mapflow",
        metadata_layer=None,
    )
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
    plugin.dlg.fill_metadata_table.assert_called_once()


def test_template_callback_keeps_product_type_clean_for_new_images(tmp_path):
    plugin = _plugin_with_search_provider(tmp_path)

    plugin.get_selected_template_callback(_response({"images": [_image(is_new=True)], "total": 1}))

    # The display-only "(new)" marker must not leak into the footprint productType,
    # which feeds product-type / zoom consistency checks during params building.
    assert plugin.app_context.search_footprints[0].attribute("productType") == "Image"


def test_template_callback_adds_footprint_layer_under_template_group(tmp_path):
    plugin = _plugin_with_search_provider(tmp_path, template_name="Template A")

    plugin.get_selected_template_callback(_response({"images": [_image()], "total": 1}))

    root = plugin.app_context.project.layerTreeRoot()
    template_group = root.findGroup("Template A")
    assert template_group is not None, "footprint layer must live under the template-named group"
    layers = template_group.findLayers()
    assert len(layers) == 1
    added_layer = layers[0].layer()
    assert added_layer is plugin.app_context.metadata_layer
    assert added_layer.featureCount() == 1


def test_template_callback_alerts_and_skips_when_no_images(tmp_path):
    plugin = _plugin_with_search_provider(tmp_path)

    plugin.get_selected_template_callback(_response({"images": []}))

    plugin.alert.assert_called_once()
    plugin.dlg.fill_metadata_table.assert_not_called()
