"""QGIS-tier tests for the per-AOI bounding-box area limit (spec 002_B, "AOI area limit").

The backend caps every AOI by the ellipsoidal area of its lat-lon–oriented bounding box
(not the polygon's own area, not the sum across AOIs). The plugin mirrors this before the
`/cost` request in ``validate_processing_params`` and blocks with a cost-area warning.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from qgis.core import QgsGeometry, QgsProject

from mapflow.functional.layer_utils import max_aoi_bbox_area, calculate_aoi_area
from mapflow.functional.service.processing_service import ProcessingService


def _ctx():
    return QgsProject.instance().transformContext()


# --------------------------- max_aoi_bbox_area helper ---------------------------

def test_thin_diagonal_bbox_area_dwarfs_polygon_area():
    """A thin diagonal sliver has a tiny true area but a full-degree bounding box: the limit
    is on the bbox, so the helper must return the (large) envelope area, not the polygon area."""
    sliver = QgsGeometry.fromWkt(
        "POLYGON((0 0, 1 1, 1.001 0.999, 0.001 -0.001, 0 0))")
    bbox_area = max_aoi_bbox_area(sliver, _ctx())          # sq.m
    polygon_area = calculate_aoi_area(sliver, _ctx()) * 1e6  # sq.km -> sq.m

    # ~1° x 1° envelope near the equator is on the order of 1.2e10 sq.m.
    assert bbox_area > 1e10
    assert bbox_area > polygon_area * 100


def test_multipart_returns_largest_part_bbox():
    """Each polygon is checked independently — the helper reports the largest per-part bbox,
    never the envelope of the whole multipart geometry."""
    small = "((0 0, 0.001 0, 0.001 0.001, 0 0.001, 0 0))"
    big = "((10 10, 10.5 10, 10.5 10.5, 10 10.5, 10 10))"
    multi = QgsGeometry.fromWkt(f"MULTIPOLYGON({small},{big})")

    big_only = QgsGeometry.fromWkt(f"POLYGON{big}")
    assert max_aoi_bbox_area(multi, _ctx()) == max_aoi_bbox_area(big_only, _ctx())


def test_empty_geometry_area_is_zero():
    assert max_aoi_bbox_area(QgsGeometry(), _ctx()) == 0.0
    assert max_aoi_bbox_area(None, _ctx()) == 0.0


# ---------------------- validate_processing_params gating -----------------------

def _service(processing_aoi, aoi_area_limit, aoi_size):
    service = ProcessingService.__new__(ProcessingService)
    service.tr = lambda text: text
    service.dlg = MagicMock()
    service.app_context = SimpleNamespace(
        aoi=processing_aoi, processing_aoi=processing_aoi, project=QgsProject.instance(),
        aoi_size=aoi_size, aoi_area_limit=aoi_area_limit,
    )
    # No search selection -> provider-min check is a no-op; isolate the area checks.
    service._selected_search_min_area = MagicMock(return_value=(None, None))
    return service


def test_blocks_when_total_area_exceeds_limit():
    # 1° x 1° AOI: total area ~12 300 sq km, over a 100 sq km limit.
    aoi = QgsGeometry.fromWkt("POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))")
    total = calculate_aoi_area(aoi, _ctx())
    service = _service(aoi, aoi_area_limit=100.0, aoi_size=total)

    error, disable_start = service.validate_processing_params(
        SimpleNamespace(name="Run 1"), allow_empty_name=False)

    assert error is not None
    assert "processing area" in error.lower()  # the total-area message, not the bbox one
    assert "100" in error  # the limit, in sq km
    assert disable_start is True


def test_blocks_on_bbox_even_when_total_area_fits():
    """A thin diagonal AOI: its own (polygon) area is under the limit, so the total check passes,
    but its lat-lon bounding box is huge — the per-AOI bbox check must still block it."""
    aoi = QgsGeometry.fromWkt("POLYGON((0 0, 1 1, 1.0005 0.9995, 0.0005 -0.0005, 0 0))")
    total = calculate_aoi_area(aoi, _ctx())
    assert total < 100  # the sliver's own area fits the limit -> isolates the bbox check
    service = _service(aoi, aoi_area_limit=100.0, aoi_size=total)

    error, _ = service.validate_processing_params(
        SimpleNamespace(name="Run 1"), allow_empty_name=False)

    assert error is not None
    assert "bounding box" in error.lower()


def test_passes_when_within_both_limits():
    aoi = QgsGeometry.fromWkt("POLYGON((0 0, 0.001 0, 0.001 0.001, 0 0.001, 0 0))")
    total = calculate_aoi_area(aoi, _ctx())
    service = _service(aoi, aoi_area_limit=100.0, aoi_size=total)

    error, _ = service.validate_processing_params(
        SimpleNamespace(name="Run 1"), allow_empty_name=False)

    assert error is None


def test_multi_aoi_blocked_when_total_exceeds_though_each_bbox_fits():
    """Two AOIs whose bounding boxes each fit but whose combined area exceeds the limit: the
    per-AOI bbox check passes, so the total-area check is what must block it."""
    part = "((0 0, 0.03 0, 0.03 0.03, 0 0.03, 0 0))"     # each bbox/area ~11 sq km
    far = "((10 0, 10.03 0, 10.03 0.03, 10 0.03, 10 0))"
    aoi = QgsGeometry.fromWkt(f"MULTIPOLYGON({part},{far})")
    total = calculate_aoi_area(aoi, _ctx())
    per_bbox = max_aoi_bbox_area(aoi, _ctx()) / 1e6
    # Limit sits above each AOI's bbox but below the two combined.
    assert per_bbox < 15 < total
    service = _service(aoi, aoi_area_limit=15.0, aoi_size=total)

    error, _ = service.validate_processing_params(
        SimpleNamespace(name="Run 1"), allow_empty_name=False)

    assert error is not None
    assert "processing area" in error.lower()


def test_zero_limit_disables_check():
    aoi = QgsGeometry.fromWkt("POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))")
    total = calculate_aoi_area(aoi, _ctx())
    service = _service(aoi, aoi_area_limit=0, aoi_size=total)

    error, _ = service.validate_processing_params(
        SimpleNamespace(name="Run 1"), allow_empty_name=False)

    assert error is None
