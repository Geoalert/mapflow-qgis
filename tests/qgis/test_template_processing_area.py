"""QGIS-tier tests for setting the processing Area from the selected template AOIs.

The Area combo must SHOW what a processing will use, so selecting AOI rows points the combo at
a real, visible layer instead of silently overriding the Area behind it: a single selection uses
that AOI's own (already drawn) layer, a multi-selection uses a visible "Selected AOIs" layer
holding one feature per AOI. Selection with no AOI keeps the current Area."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from qgis.core import QgsVectorLayer

from mapflow.functional.geometry import geometry_from_geojson
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


def _layer(name="layer"):
    return QgsVectorLayer("Polygon?crs=epsg:4326", name, "memory")


def _plugin(selected_aois, in_template_mode=True):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.dlg = MagicMock()
    plugin._processing_area_aoi_filter = None
    plugin._selected_aois_layer_id = None
    plugin.processing_service = SimpleNamespace(
        in_template_mode=in_template_mode,
        selected_aois=lambda: selected_aois,
        active_template=SimpleNamespace(name="T1"),
    )
    plugin._find_aoi_layer = MagicMock(return_value=_layer("AOI 1"))
    plugin._rebuild_selected_aois_layer = MagicMock(return_value=_layer("Selected AOIs"))
    return plugin


def test_single_aoi_points_the_combo_at_that_aois_own_layer():
    plugin = _plugin([_aoi("a1", _square(0, 0))])

    plugin.sync_processing_area_to_selected_aois()

    plugin._find_aoi_layer.assert_called_once_with("a1")
    plugin.dlg.polygonCombo.setLayer.assert_called_once_with(plugin._find_aoi_layer.return_value)
    plugin._rebuild_selected_aois_layer.assert_not_called()  # no extra layer for one AOI
    assert plugin._processing_area_aoi_filter == frozenset({"a1"})


def test_multiple_aois_build_a_visible_selected_aois_layer():
    plugin = _plugin([_aoi("a1", _square(0, 0)), _aoi("a2", _square(5, 5))])

    plugin.sync_processing_area_to_selected_aois()

    # One feature per selected AOI, so the per-processing AOI limit still applies.
    geometries = plugin._rebuild_selected_aois_layer.call_args.args[0]
    assert len(geometries) == 2
    assert round(sum(g.area() for g in geometries), 6) == 2.0
    plugin.dlg.polygonCombo.setLayer.assert_called_once_with(
        plugin._rebuild_selected_aois_layer.return_value)
    assert plugin._processing_area_aoi_filter == frozenset({"a1", "a2"})


def test_no_selection_keeps_current_area():
    plugin = _plugin([])

    plugin.sync_processing_area_to_selected_aois()

    plugin.dlg.polygonCombo.setLayer.assert_not_called()


def test_unchanged_selection_does_not_rebuild_area():
    plugin = _plugin([_aoi("a1", _square(0, 0))])
    plugin._processing_area_aoi_filter = frozenset({"a1"})

    plugin.sync_processing_area_to_selected_aois()

    plugin.dlg.polygonCombo.setLayer.assert_not_called()


def test_not_in_template_mode_is_noop():
    plugin = _plugin([_aoi("a1", _square(0, 0))], in_template_mode=False)

    plugin.sync_processing_area_to_selected_aois()

    plugin.dlg.polygonCombo.setLayer.assert_not_called()


def test_missing_aoi_layer_leaves_the_area_untouched():
    # The AOI's layer is not on the map (e.g. tree edited by hand) -> don't switch the combo.
    plugin = _plugin([_aoi("a1", _square(0, 0))])
    plugin._find_aoi_layer = MagicMock(return_value=None)

    plugin.sync_processing_area_to_selected_aois()

    plugin.dlg.polygonCombo.setLayer.assert_not_called()
    assert plugin._processing_area_aoi_filter is None


def test_remove_selected_aois_layer_drops_it_from_project_and_aoi_layers():
    plugin = Mapflow.__new__(Mapflow)
    plugin._selected_aois_layer_id = "sel-1"
    plugin.aoi_service = MagicMock()
    plugin.app_context = SimpleNamespace(project=MagicMock())
    plugin.app_context.project.mapLayer.return_value = _layer("Selected AOIs")

    plugin._remove_selected_aois_layer()

    plugin.aoi_service.unregister_layer.assert_called_once()
    plugin.app_context.project.removeMapLayer.assert_called_once_with("sel-1")
    assert plugin._selected_aois_layer_id is None


def test_geometry_from_geojson_none_for_empty():
    assert geometry_from_geojson(None) is None
    assert geometry_from_geojson({}) is None
