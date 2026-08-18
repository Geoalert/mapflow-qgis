"""AoiService, the new owner of the AOI layer registry and AOI layer creation.

These behaviours used to live on `Mapflow.add_to_layers` / `remove_from_layers` /
`filter_aoi_layers` / `create_*_aoi_layer`, where they were covered only indirectly. The move
is the moment to pin them: `spec/007_architecture.md` says a step that moves code must not
leave a behaviour covered by neither suite.

What is asserted here is the part that is *not* widget work — the service holds no dialog, so
what a caller can observe is the registry, the signals, and the layers it builds.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from qgis.core import QgsGeometry, QgsRectangle, QgsCoordinateReferenceSystem, QgsVectorLayer

from mapflow.functional.service.aoi_service import AoiService


def _layer(name="layer"):
    return QgsVectorLayer('Polygon?crs=epsg:4326', name, 'memory')


@pytest.fixture
def service(tmp_path):
    project = MagicMock()
    project.mapLayers.return_value = {}
    return AoiService(iface=MagicMock(),
                      app_context=SimpleNamespace(project=project, search_provider=None),
                      plugin_dir=str(tmp_path),
                      result_loader=MagicMock(),
                      data_catalog_service=MagicMock())


# ---------- the registry ----------

def test_registering_a_layer_records_it_once(service):
    layer = _layer()
    registered = []
    service.aoiLayerRegistered.connect(registered.append)

    service.register_layer(layer)
    service.register_layer(layer)

    assert service.aoi_layers == [layer]
    # The context-menu action is attached per layer, so a second registration must not re-emit.
    assert registered == [layer]


def test_registering_a_layer_points_the_combo_at_it(service):
    layer = _layer()
    current = []
    service.currentAoiLayerChanged.connect(lambda lyr, notify: current.append((lyr, notify)))

    service.register_layer(layer)

    assert current == [(layer, True)]


def test_bulk_registration_neither_selects_nor_prices(service):
    """Template AOI display layers are added in bulk: the last must not become the Area
    (feedback 8.1), and none of them may fire a cost request."""
    layer = _layer()
    current = []
    service.currentAoiLayerChanged.connect(lambda lyr, notify: current.append((lyr, notify)))

    service.register_layer(layer, recompute_cost=False, set_current=False)

    assert service.aoi_layers == [layer]
    assert current == []


def test_registration_can_select_without_pricing(service):
    layer = _layer()
    current = []
    service.currentAoiLayerChanged.connect(lambda lyr, notify: current.append((lyr, notify)))

    service.register_layer(layer, recompute_cost=False)

    assert current == [(layer, False)]


def test_unregistering_a_layer_drops_it(service):
    layer = _layer()
    service.register_layer(layer)

    service.unregister_layer(layer)

    assert service.aoi_layers == []


def test_unregistering_a_layer_twice_is_not_an_error(service):
    """The per-layer 'Remove AOI' action cannot be taken off a single layer's menu, so it stays
    clickable after the first click."""
    layer = _layer()
    service.register_layer(layer)
    service.unregister_layer(layer)

    changed = []
    service.aoiLayersChanged.connect(lambda: changed.append(1))
    service.unregister_layer(layer)

    assert service.aoi_layers == []
    assert changed == [1]


# ---------- what the AOI combo may not offer ----------

def test_only_non_aoi_layers_are_excepted(service):
    aoi, other = _layer("aoi"), _layer("other")
    service.app_context.project.mapLayers.return_value = {"1": aoi, "2": other}
    service.register_layer(aoi)

    assert service.excepted_layers(use_all_vector_layers=False) == [other]


def test_using_all_vector_layers_excepts_only_search_metadata(service):
    """Search-metadata layers stay excluded even in 'use all layers' mode: they are big and
    crowded, and using one as an AOI produces topology errors."""
    metadata, other = _layer("Provider metadata"), _layer("other")
    service.app_context.project.mapLayers.return_value = {"1": metadata, "2": other}
    service.app_context.search_provider = SimpleNamespace(name="Provider")

    assert service.excepted_layers(use_all_vector_layers=True) == [metadata]


def test_using_all_vector_layers_excepts_nothing_without_a_search_provider(service):
    service.app_context.project.mapLayers.return_value = {"1": _layer("other")}

    assert service.excepted_layers(use_all_vector_layers=True) == []


# ---------- creating AOI layers ----------

def test_a_created_layer_is_registered_and_added_to_the_map(service):
    layer = service.create_editable_layer()

    assert layer in service.aoi_layers
    service.result_loader.add_layer.assert_called_once_with(layer)
    assert layer.isEditable()


def test_created_layers_are_numbered(service):
    first = service.create_editable_layer()
    second = service.create_editable_layer()

    assert (first.name(), second.name()) == ("AOI_0", "AOI_1")


def test_a_layer_from_the_map_extent_carries_the_reprojected_rectangle(service):
    rect = QgsRectangle(0.0, 0.0, 1.0, 1.0)

    layer = service.create_layer_from_rect(rect, QgsCoordinateReferenceSystem("EPSG:4326"))

    geometries = [feature.geometry() for feature in layer.getFeatures()]
    assert len(geometries) == 1
    assert geometries[0].boundingBox() == rect


def test_a_layer_from_imagery_uses_the_selected_images_footprint(service):
    footprint = QgsGeometry.fromWkt("POLYGON((0 0, 0 2, 2 2, 2 0, 0 0))")
    service.data_catalog_service.selected_image.return_value = SimpleNamespace(
        footprint=footprint.asWkt())

    layer = service.create_layer_from_imagery()

    geometries = [feature.geometry() for feature in layer.getFeatures()]
    assert len(geometries) == 1
    assert geometries[0].boundingBox() == footprint.boundingBox()


def test_no_imagery_selected_builds_no_layer(service):
    """The caller explains why instead of adding an empty AOI to the map."""
    service.data_catalog_service.selected_image.return_value = None
    service.data_catalog_service.selected_mosaic.return_value = None

    assert service.create_layer_from_imagery() is None
    assert service.aoi_layers == []
    service.result_loader.add_layer.assert_not_called()
