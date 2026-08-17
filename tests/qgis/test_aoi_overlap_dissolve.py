"""QGIS-tier tests: intersecting AOI polygons are dissolved before the area is measured and
before the geometry is submitted.

The regression (reported on a real 'POC' layer of two nearly-identical overlapping
quadrilaterals): the AOI was built with ``QgsGeometry.collectGeometry``, which stacks the
polygons into a MultiPolygon without merging them, so ``measureArea`` summed the parts and the
shared area was measured — and billed — twice, both in the Area label and in the MultiPolygon
sent to ``/processing/cost/v2``.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer

from mapflow.functional import layer_utils
from mapflow.functional.service.area_calculator_service import AreaCalculatorService

# The two AOIs of the reported layer, trimmed to 2D (the source has a zero Z).
POC_A = ("POLYGON((116.453049998276157 40.12268262081593,"
         "116.455857049574931 39.77367257600082,"
         "116.791767521662393 39.780222362364647,"
         "116.785217735298573 40.127361039647234,"
         "116.453049998276157 40.12268262081593))")
POC_B = ("POLYGON((116.455160215366902 39.771790069375818,"
         "116.793400039636495 39.779781230320488,"
         "116.783915452966596 40.126904336856533,"
         "116.455422181038699 40.120268410935203,"
         "116.455160215366902 39.771790069375818))")


def _layer(wkts, geometry_type="Polygon"):
    layer = QgsVectorLayer(f"{geometry_type}?crs=epsg:4326", "aois", "memory")
    features = []
    for wkt in wkts:
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromWkt(wkt))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    layer.updateExtents()
    return layer


def _service(dlg=None):
    service = AreaCalculatorService.__new__(AreaCalculatorService)
    service.dlg = dlg or MagicMock()
    service.config = MagicMock()
    service.provider_service = MagicMock()
    service.data_catalog_service = MagicMock()
    service.processing_service = MagicMock()
    service.app_context = SimpleNamespace(
        aoi=None,
        aoi_size=None,
        processing_aoi=None,
        max_aois_per_processing=10,
        project=QgsProject.instance(),
        user_role=SimpleNamespace(can_start_processing=True, value="OWNER"),
    )
    service.tr = lambda text: text
    # The UI/provider plumbing of calculate_aoi_area is not under test: keep the geometry and
    # the measured size, skip the cost request.
    service.get_aoi = lambda provider_index, selected_aoi, local_image_indices: selected_aoi
    service.dlg.metadataTable.selectedItems.return_value = []
    return service


def _area_of(wkts):
    service = _service()
    service.get_aoi_area_polygon_layer(_layer(wkts))
    return service


def test_overlapping_aois_area_is_the_union_not_the_sum():
    overlapping = _area_of([POC_A, POC_B]).app_context.aoi_size
    a_only = _area_of([POC_A]).app_context.aoi_size
    b_only = _area_of([POC_B]).app_context.aoi_size

    # The union of two ~1300 sq.km AOIs that almost coincide is far below their sum.
    assert overlapping < a_only + b_only
    # And it is at least as large as either one alone.
    assert overlapping >= max(a_only, b_only)
    assert overlapping == pytest.approx(max(a_only, b_only), rel=0.05)


def test_overlapping_aois_are_submitted_as_one_polygon():
    """The geometry stored on app_context is what goes into the cost/start request."""
    service = _area_of([POC_A, POC_B])

    assert layer_utils.count_polygons_in_geometry(service.app_context.aoi) == 1


def test_disjoint_aois_are_kept_separate():
    service = _area_of(["POLYGON((0 0,0 1,1 1,1 0,0 0))", "POLYGON((5 5,5 6,6 6,6 5,5 5))"])

    assert layer_utils.count_polygons_in_geometry(service.app_context.aoi) == 2


def test_multipolygon_layer_with_intersecting_parts_is_dissolved():
    layer = _layer(["MULTIPOLYGON(((0 0,0 1,1 1,1 0,0 0)),((0.75 0,0.75 1,1.75 1,1.75 0,0.75 0)))"],
                   geometry_type="MultiPolygon")
    service = _service()

    service.get_aoi_area_polygon_layer(layer)

    assert layer_utils.count_polygons_in_geometry(service.app_context.aoi) == 1


def test_polygon_limit_is_checked_on_the_dissolved_aoi():
    """Two overlapping polygons become one AOI, so a one-AOI plan must still accept them."""
    service = _service()
    service.app_context.max_aois_per_processing = 1

    service.get_aoi_area_polygon_layer(_layer([POC_A, POC_B]))

    assert service.app_context.aoi is not None
    assert service.app_context.aoi_size > 0
    service.dlg.disable_processing_start.assert_not_called()


def test_polygon_limit_still_rejects_too_many_disjoint_aois():
    service = _service()
    service.app_context.max_aois_per_processing = 1

    service.get_aoi_area_polygon_layer(
        _layer(["POLYGON((0 0,0 1,1 1,1 0,0 0))", "POLYGON((5 5,5 6,6 6,6 5,5 5))"]))

    assert service.app_context.aoi is None
    service.dlg.disable_processing_start.assert_called_once()
