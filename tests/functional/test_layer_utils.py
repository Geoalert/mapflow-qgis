import pytest
from qgis.core import QgsGeometry

from mapflow.functional.layer_utils import generate_xyz_layer_definition, union_parts

# Two overlapping unit squares: 2.0 sq.units as separate parts, 1.75 as their union.
OVERLAPPING = ("MULTIPOLYGON(((0 0,0 1,1 1,1 0,0 0)),"
               "((0.75 0,0.75 1,1.75 1,1.75 0,0.75 0)))")
DISJOINT = "MULTIPOLYGON(((0 0,0 1,1 1,1 0,0 0)),((5 5,5 6,6 6,6 5,5 5)))"
SINGLE = "POLYGON((0 0,0 1,1 1,1 0,0 0))"


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


def test_xyz_no_creds():
    result = generate_xyz_layer_definition(url='https://xyz.tile.server/{z}/{x}/{y}.png',
                                           username="", password="", max_zoom=18, source_type="xyz")
    assert result == 'type=xyz' \
                     '&url=https://xyz.tile.server/{z}/{x}/{y}.png' \
                     '&zmin=0' \
                     '&zmax=18' \
                     '&username=' \
                     '&password='
