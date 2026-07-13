"""QGIS-tier tests for setting the processing Area from the selected template AOIs
(round-2 feedback 8.1). Selecting one or more AOI rows sets the processing Area to the
UNION of their geometries (approved decision), so a processing started from the template
covers exactly the selected AOIs. Selection with no AOI keeps the current Area, and the
last AOI must no longer 'stick' as the Area on open."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.mapflow import Mapflow


def _square(x0, y0, size=1.0):
    return {
        "type": "Polygon",
        "coordinates": [[
            [x0, y0], [x0 + size, y0], [x0 + size, y0 + size], [x0, y0 + size], [x0, y0],
        ]],
    }


def _aoi(aoi_id, geometry):
    return SimpleNamespace(id=aoi_id, geometry=geometry)


def _plugin(selected_aois, in_template_mode=True):
    plugin = Mapflow.__new__(Mapflow)
    plugin._processing_area_aoi_filter = None
    plugin.processing_service = SimpleNamespace(
        in_template_mode=in_template_mode,
        selected_aois=lambda: selected_aois,
    )
    plugin._set_template_processing_area = MagicMock()
    return plugin


def test_single_aoi_sets_that_geometry_as_area():
    plugin = _plugin([_aoi("a1", _square(0, 0))])

    plugin.sync_processing_area_to_selected_aois()

    plugin._set_template_processing_area.assert_called_once()
    geom = plugin._set_template_processing_area.call_args.args[0]
    assert round(geom.area(), 6) == 1.0
    assert plugin._processing_area_aoi_filter == frozenset({"a1"})


def test_multiple_aois_union_into_area():
    # Two disjoint unit squares -> union area 2.0.
    plugin = _plugin([_aoi("a1", _square(0, 0)), _aoi("a2", _square(5, 5))])

    plugin.sync_processing_area_to_selected_aois()

    geom = plugin._set_template_processing_area.call_args.args[0]
    assert round(geom.area(), 6) == 2.0
    assert plugin._processing_area_aoi_filter == frozenset({"a1", "a2"})


def test_no_selection_keeps_current_area():
    plugin = _plugin([])

    plugin.sync_processing_area_to_selected_aois()

    plugin._set_template_processing_area.assert_not_called()


def test_unchanged_selection_does_not_rebuild_area():
    plugin = _plugin([_aoi("a1", _square(0, 0))])
    plugin._processing_area_aoi_filter = frozenset({"a1"})

    plugin.sync_processing_area_to_selected_aois()

    plugin._set_template_processing_area.assert_not_called()


def test_not_in_template_mode_is_noop():
    plugin = _plugin([_aoi("a1", _square(0, 0))], in_template_mode=False)

    plugin.sync_processing_area_to_selected_aois()

    plugin._set_template_processing_area.assert_not_called()


def test_union_helper_ignores_aois_without_geometry():
    plugin = _plugin([_aoi("a1", None), _aoi("a2", _square(0, 0))])

    union = plugin._union_of_selected_aoi_geometries()

    assert round(union.area(), 6) == 1.0


def test_geometry_from_geojson_none_for_empty():
    assert Mapflow._geometry_from_geojson(None) is None
    assert Mapflow._geometry_from_geojson({}) is None
