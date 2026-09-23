"""QGIS-tier tests for AreaCalculatorService after it lost the dialog.

It computed the AOI area and drove the Start button, the area label and the 'Use imagery extent'
action directly, and read the source combo, the AOI combo and the metadata table. A service may do
none of that (`spec/007_architecture.md` § Services). It now announces (startDisabled, areaChanged,
imageryExtentChanged) and reads the AOI layer, the provider and the selected search images off
`app_context`, pushed from the composition root.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from PyQt5.QtCore import QObject
from qgis.core import QgsGeometry, QgsVectorLayer, QgsFeature, QgsProject

from mapflow.functional.service.area_calculator_service import AreaCalculatorService
from mapflow.model.provider import MyImageryProvider, ImagerySearchProvider


def _service(**app_context):
    service = AreaCalculatorService.__new__(AreaCalculatorService)
    QObject.__init__(service)
    service.tr = lambda text: text
    service.iface = MagicMock()
    service.config = SimpleNamespace(LOCAL_INDEX_COLUMN=0)
    service.data_catalog_service = MagicMock()
    service.data_catalog_service.selected_image.return_value = None
    service.data_catalog_service.selected_mosaic.return_value = None
    service.processing_service = MagicMock()
    service.provider_service = MagicMock()
    service._last_catalog_aoi_wkt = None
    defaults = dict(aoi=None, aoi_size=None, processing_aoi=None, aoi_layer=None,
                    data_provider=None, selected_search_indices=[], search_footprints={},
                    max_aois_per_processing=1, project=QgsProject.instance(),
                    user_role=SimpleNamespace(can_start_processing=True, value="owner"))
    defaults.update(app_context)
    service.app_context = SimpleNamespace(**defaults)
    return service


def _polygon_layer(wkt="POLYGON((0 0, 0.001 0, 0.001 0.001, 0 0.001, 0 0))",
                   geom_type="Polygon"):
    layer = QgsVectorLayer(f"{geom_type}?crs=EPSG:4326", "aoi", "memory")
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromWkt(wkt))
    layer.dataProvider().addFeature(feature)
    layer.updateExtents()
    return layer


# ---------- the writes are announced ----------

def test_an_empty_layer_blocks_the_start_and_clears_the_area():
    service = _service()
    blocked = []
    service.startDisabled.connect(lambda *a: blocked.append(a))

    service.get_aoi_area_polygon_layer(None)

    assert blocked == [("Set AOI to start processing", True)]
    assert service.app_context.aoi is None and service.app_context.aoi_size is None


def test_too_many_polygons_blocks_with_the_limit_message():
    service = _service(max_aois_per_processing=1)
    blocked = []
    service.startDisabled.connect(lambda *a: blocked.append(a))

    service.get_aoi_area_polygon_layer(
        _polygon_layer("MULTIPOLYGON(((0 0,0.001 0,0.001 0.001,0 0.001,0 0)),"
                       "((1 1,1.001 1,1.001 1.001,1 1.001,1 1)))",
                       geom_type="MultiPolygon"))

    assert blocked and "not more than 1 polygons" in blocked[0][0]
    assert blocked[0][1] is True


def test_a_measured_area_is_announced_and_priced():
    # A plain provider (no image id, not search/my-imagery) leaves the AOI uncropped.
    service = _service(data_provider=SimpleNamespace(requires_image_id=False))
    areas = []
    service.areaChanged.connect(areas.append)

    service.calculate_aoi_area(QgsGeometry.fromWkt("POLYGON((0 0, 0.01 0, 0.01 0.01, 0 0.01, 0 0))"),
                               _polygon_layer().crs())

    assert areas and areas[0] > 0
    service.processing_service.update_processing_cost.assert_called_once()


# ---------- the reads come from app_context, not widgets ----------

def test_the_provider_and_search_selection_come_from_app_context():
    """`calculate_aoi_area` used to read the source combo and the metadata table; it now takes the
    pushed provider and indices. A search provider with a selected footprint crops the AOI to it."""
    footprint = QgsGeometry.fromWkt("POLYGON((0 0, 0.02 0, 0.02 0.02, 0 0.02, 0 0))")
    provider = ImagerySearchProvider.__new__(ImagerySearchProvider)
    service = _service(data_provider=provider,
                       selected_search_indices=["7"],
                       search_footprints={7: _footprint_feature(footprint)})
    service.get_aoi = MagicMock(return_value=footprint)

    service.calculate_aoi_area(QgsGeometry.fromWkt("POLYGON((0 0, 0.05 0, 0.05 0.05, 0 0.05, 0 0))"),
                               _polygon_layer().crs())

    provider_arg = service.get_aoi.call_args.kwargs["provider"]
    indices_arg = service.get_aoi.call_args.kwargs["local_image_indices"]
    assert provider_arg is provider
    assert indices_arg == [7]  # coerced to int from the pushed strings


def test_get_aoi_takes_a_provider_object_not_an_index():
    service = _service()
    provider = SimpleNamespace(requires_image_id=False)
    aoi = QgsGeometry.fromWkt("POLYGON((0 0, 0.01 0, 0.01 0.01, 0 0.01, 0 0))")

    assert service.get_aoi(provider=provider, selected_aoi=aoi, local_image_indices=[]) == aoi
    service.provider_service.providers.__getitem__.assert_not_called()


# ---------- the catalog dedup no longer reads the table ----------

def test_the_catalog_aoi_is_not_re_priced_when_the_area_is_unchanged():
    image = SimpleNamespace(footprint="POLYGON((0 0, 0.02 0, 0.02 0.02, 0 0.02, 0 0))",
                            filename="scene.tif")
    service = _service(aoi=QgsGeometry.fromWkt("POLYGON((0 0, 0.05 0, 0.05 0.05, 0 0.05, 0 0))"),
                       data_provider=MyImageryProvider.__new__(MyImageryProvider))
    service.data_catalog_service.selected_image.return_value = image
    priced = []
    service.calculate_aoi_area = lambda aoi, crs: priced.append(aoi)

    service.calculate_aoi_area_catalog()
    service.calculate_aoi_area_catalog()  # same image, same AOI

    assert len(priced) == 1  # the second call is deduplicated on the geometry


def _footprint_feature(geom):
    feature = QgsFeature()
    feature.setGeometry(geom)
    return feature
