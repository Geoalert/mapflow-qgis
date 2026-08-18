"""QGIS-tier tests: the AOI area shown in the plugin counts an overlap once.

Reported on a real 'POC' layer of two nearly-coincident quadrilaterals: the AOI is collected into
a MultiPolygon part by part, and the area of a MultiPolygon is the sum of its parts, so the shared
area was added twice (2203.96 instead of 1108.96 sq.km) — in the Area label, in the cost estimate
derived from it, and in the client-side area limits.

Only the measurement is unioned. The geometry the plugin submits is deliberately left as the user
drew it: the backend unions the AOI on its side, and a Planned Search legitimately carries
intersecting named AOIs ("City" enclosing "District 1"), which must stay separate.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer

from mapflow.functional import layer_utils
from mapflow.functional.service.area_calculator_service import AreaCalculatorService

# The two AOIs of the reported layer, trimmed to 2D (the source carries a zero Z).
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
FAR_1 = "POLYGON((0 0,0 1,1 1,1 0,0 0))"
FAR_2 = "POLYGON((5 5,5 6,6 6,6 5,5 5))"


def _layer(wkts):
    layer = QgsVectorLayer("Polygon?crs=epsg:4326", "aois", "memory")
    features = []
    for wkt in wkts:
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromWkt(wkt))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    layer.updateExtents()
    return layer


def _service_for(wkts):
    """Run the real area calculation over a layer, with only the UI/provider plumbing stubbed."""
    service = AreaCalculatorService.__new__(AreaCalculatorService)
    service.dlg = MagicMock()
    service.dlg.metadataTable.selectedItems.return_value = []
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
    # Cropping to image footprints is a separate concern; keep the AOI as selected.
    service.get_aoi = lambda provider_index, selected_aoi, local_image_indices: selected_aoi
    service.get_aoi_area_polygon_layer(_layer(wkts))
    return service


def test_overlapping_aois_area_is_the_union_not_the_sum():
    overlapping = _service_for([POC_A, POC_B]).app_context.aoi_size
    a_only = _service_for([POC_A]).app_context.aoi_size
    b_only = _service_for([POC_B]).app_context.aoi_size

    # The two AOIs almost coincide, so their union is far below their sum...
    assert overlapping < a_only + b_only
    # ...and barely above either one on its own.
    assert overlapping >= max(a_only, b_only)
    assert overlapping == pytest.approx(max(a_only, b_only), rel=0.05)


def test_disjoint_aois_area_is_still_the_total():
    """Nothing is dissolved when the AOIs do not overlap: the total stays the sum of the parts.
    (The two squares sit at different latitudes, so their ellipsoidal areas differ.)"""
    both = _service_for([FAR_1, FAR_2]).app_context.aoi_size
    first = _service_for([FAR_1]).app_context.aoi_size
    second = _service_for([FAR_2]).app_context.aoi_size

    assert both == pytest.approx(first + second, rel=1e-9)


def test_submitted_geometry_keeps_the_source_polygons():
    """The union is for measuring only: what we send stays as the user drew it, and the backend
    unions it on its side."""
    aoi = _service_for([POC_A, POC_B]).app_context.aoi

    assert aoi.isMultipart()
    assert len(aoi.asMultiPolygon()) == 2


def test_measured_area_matches_the_union_of_the_layer():
    service = _service_for([POC_A, POC_B])

    union_area = layer_utils.calculate_aoi_area(
        QgsGeometry.unaryUnion([QgsGeometry.fromWkt(POC_A), QgsGeometry.fromWkt(POC_B)]),
        QgsProject.instance().transformContext())

    assert service.app_context.aoi_size == pytest.approx(union_area)
