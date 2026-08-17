import pytest
from qgis.core import QgsGeometry, QgsWkbTypes

from mapflow.functional.layer_utils import (count_polygons_in_geometry,
                                            dissolve_geometries,
                                            dissolve_named_polygons,
                                            generate_xyz_layer_definition)

# Two overlapping unit squares: 1 + 1 sq.units as separate parts, 1.75 dissolved (0.25 shared).
LEFT = "POLYGON((0 0,0 1,1 1,1 0,0 0))"
RIGHT = "POLYGON((0.75 0,0.75 1,1.75 1,1.75 0,0.75 0))"
FAR = "POLYGON((5 5,5 6,6 6,6 5,5 5))"
OVERLAPPING_MULTIPOLYGON = ("MULTIPOLYGON(((0 0,0 1,1 1,1 0,0 0)),"
                            "((0.75 0,0.75 1,1.75 1,1.75 0,0.75 0)))")


def test_dissolve_geometries_counts_the_overlap_once():
    """The bug: collected (not dissolved) parts make measureArea sum the shared area twice."""
    dissolved = dissolve_geometries([QgsGeometry.fromWkt(LEFT), QgsGeometry.fromWkt(RIGHT)])

    assert dissolved.area() == pytest.approx(1.75)
    assert count_polygons_in_geometry(dissolved) == 1


def test_dissolve_geometries_keeps_disjoint_polygons_apart():
    dissolved = dissolve_geometries([QgsGeometry.fromWkt(LEFT), QgsGeometry.fromWkt(FAR)])

    assert count_polygons_in_geometry(dissolved) == 2
    assert dissolved.area() == pytest.approx(2.0)


def test_dissolve_geometries_dissolves_parts_of_one_multipolygon():
    """A single feature can be a MultiPolygon whose own parts intersect."""
    dissolved = dissolve_geometries([QgsGeometry.fromWkt(OVERLAPPING_MULTIPOLYGON)])

    assert count_polygons_in_geometry(dissolved) == 1
    assert dissolved.area() == pytest.approx(1.75)


def test_dissolve_geometries_keeps_a_single_polygon_untouched():
    single = QgsGeometry.fromWkt(LEFT)

    assert dissolve_geometries([single]).asWkt() == single.asWkt()


def test_dissolve_geometries_ignores_empty_input():
    assert dissolve_geometries([]).isEmpty()
    assert dissolve_geometries([None, QgsGeometry()]).isEmpty()


def test_dissolve_named_polygons_keeps_names_when_nothing_merges():
    parts, names_lost = dissolve_named_polygons([(QgsGeometry.fromWkt(LEFT), "North"),
                                                 (QgsGeometry.fromWkt(FAR), "South")])

    assert names_lost is False
    assert [name for _, name in parts] == ["North", "South"]


def test_dissolve_named_polygons_drops_conflicting_names_of_merged_polygons():
    parts, names_lost = dissolve_named_polygons([(QgsGeometry.fromWkt(LEFT), "North"),
                                                 (QgsGeometry.fromWkt(RIGHT), "South")])

    assert names_lost is True
    assert len(parts) == 1
    assert parts[0][1] is None
    assert parts[0][0].area() == pytest.approx(1.75)


def test_dissolve_named_polygons_keeps_the_single_name_of_merged_polygons():
    """Same name on both (or only one of them named) is not ambiguous — merge silently."""
    parts, names_lost = dissolve_named_polygons([(QgsGeometry.fromWkt(LEFT), "North"),
                                                 (QgsGeometry.fromWkt(RIGHT), None)])

    assert names_lost is False
    assert [name for _, name in parts] == ["North"]


def test_dissolve_named_polygons_reports_names_lost_per_merged_group():
    """Only the merged group loses its names; an untouched AOI keeps its own."""
    parts, names_lost = dissolve_named_polygons([(QgsGeometry.fromWkt(LEFT), "North"),
                                                 (QgsGeometry.fromWkt(RIGHT), "South"),
                                                 (QgsGeometry.fromWkt(FAR), "East")])

    assert names_lost is True
    assert sorted(name or "" for _, name in parts) == ["", "East"]


def test_dissolve_named_polygons_explodes_multipolygons():
    parts, names_lost = dissolve_named_polygons([
        (QgsGeometry.fromWkt("MULTIPOLYGON(((0 0,0 1,1 1,1 0,0 0)),((5 5,5 6,6 6,6 5,5 5)))"),
         "Combo"),
    ])

    assert names_lost is False
    assert [part.wkbType() for part, _ in parts] == [QgsWkbTypes.Polygon] * 2
    assert [name for _, name in parts] == ["Combo", "Combo"]


def test_xyz_no_creds():
    result = generate_xyz_layer_definition(url='https://xyz.tile.server/{z}/{x}/{y}.png',
                                           username="", password="", max_zoom=18, source_type="xyz")
    assert result == 'type=xyz' \
                     '&url=https://xyz.tile.server/{z}/{x}/{y}.png' \
                     '&zmin=0' \
                     '&zmax=18' \
                     '&username=' \
                     '&password='
