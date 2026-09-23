import pytest
from qgis.core import QgsGeometry

from mapflow.functional.layer_utils import generate_xyz_layer_definition, union_parts

# Two overlapping unit squares: 2.0 sq.units as separate parts, 1.75 as their union.
OVERLAPPING = ("MULTIPOLYGON(((0 0,0 1,1 1,1 0,0 0)),"
               "((0.75 0,0.75 1,1.75 1,1.75 0,0.75 0)))")
DISJOINT = "MULTIPOLYGON(((0 0,0 1,1 1,1 0,0 0)),((5 5,5 6,6 6,6 5,5 5)))"
SINGLE = "POLYGON((0 0,0 1,1 1,1 0,0 0))"
# A bowtie: the ring crosses itself at (1,1), so GEOS calls it invalid. Its two lobes are 1
# sq.unit each; the naive ring area cancels them out to 0, because they wind opposite ways.
BOWTIE = "POLYGON((0 0,2 2,2 0,0 2,0 0))"
# The reported layer: two AOIs that nearly coincide, the first with a self-intersecting spike at
# its top-left corner. Kept verbatim — a hand-made "nearly invalid" ring is not the same thing,
# GEOS unions those without complaint.
INVALID_WITH_OVERLAP = (
    "MULTIPOLYGON((("
    "116.482273015485958 40.096111205163901,116.483421141733757 40.096040829648665,"
    "116.482293040394737 40.096061775252693,116.48231576177767 40.096323738956208,"
    "116.493677906897517 40.095546101647621,116.492770663370834 40.083708733728095,"
    "116.481368353824024 40.085400702403398,116.482273015485958 40.096111205163901)),(("
    "116.48145172032369 40.095978122374611,116.481370716437368 40.085400027371008,"
    "116.493332290315919 40.084399966891276,116.492727461298145 40.095848516156515,"
    "116.48145172032369 40.095978122374611)))")


def test_union_parts_merges_intersecting_parts():
    """The bug: the area of a MultiPolygon is the sum of its parts, so an overlap counts twice."""
    collected = QgsGeometry.fromWkt(OVERLAPPING)

    assert collected.area() == pytest.approx(2.0)
    assert union_parts(collected).area() == pytest.approx(1.75)


def test_union_parts_keeps_disjoint_parts_apart():
    collected = QgsGeometry.fromWkt(DISJOINT)

    dissolved = union_parts(collected)

    assert dissolved.area() == pytest.approx(2.0)
    assert len(dissolved.asMultiPolygon()) == 2


def test_union_parts_leaves_a_single_polygon_untouched():
    single = QgsGeometry.fromWkt(SINGLE)

    assert union_parts(single) is single


def test_union_parts_tolerates_empty_and_none():
    assert union_parts(None) is None
    assert union_parts(QgsGeometry()).isEmpty()


def test_geos_refuses_to_union_an_invalid_part():
    """Pins the reason the repair exists: GEOS answers a self-intersecting ring with a NULL
    geometry, which is what used to send the area calculation back to the summed parts."""
    collected = QgsGeometry.fromWkt(INVALID_WITH_OVERLAP)

    assert not collected.isGeosValid()
    assert QgsGeometry.unaryUnion([collected]).isEmpty()


def test_union_parts_repairs_an_invalid_part_and_still_dissolves():
    collected = QgsGeometry.fromWkt(INVALID_WITH_OVERLAP)
    parts = collected.asGeometryCollection()

    dissolved = union_parts(collected)

    assert not dissolved.isEmpty()
    # The overlap is counted once: below the sum of the parts...
    assert dissolved.area() < sum(part.area() for part in parts)
    # ...and still covering the valid neighbour whole.
    assert dissolved.area() >= parts[1].area()


def test_union_parts_does_not_xor_the_overlap_away():
    """``makeValid`` on the whole collection would resolve the overlap into a hole, leaving the
    symmetric difference. The repair must therefore run per part, before the union."""
    collected = QgsGeometry.fromWkt(INVALID_WITH_OVERLAP)

    assert union_parts(collected).area() > collected.makeValid().area()


def test_union_parts_repairs_a_lone_self_intersecting_polygon():
    """A bowtie's ring area cancels itself out; the two lobes are what the user drew."""
    bowtie = QgsGeometry.fromWkt(BOWTIE)

    assert bowtie.area() == pytest.approx(0.0, abs=1e-9)
    assert union_parts(bowtie).area() == pytest.approx(2.0)


def test_xyz_no_creds():
    result = generate_xyz_layer_definition(url='https://xyz.tile.server/{z}/{x}/{y}.png',
                                           username="", password="", max_zoom=18, source_type="xyz")
    assert result == 'type=xyz' \
                     '&url=https://xyz.tile.server/{z}/{x}/{y}.png' \
                     '&zmin=0' \
                     '&zmax=18' \
                     '&username=' \
                     '&password='
