"""QGIS-tier tests for setting the processing Area from the selected template AOIs.

The Area combo must SHOW what a processing will use, so selecting AOI rows points the combo at
a real, visible layer instead of silently overriding the Area behind it: a single selection uses
that AOI's own (already drawn) layer, a multi-selection uses a visible "Selected AOIs" layer
holding one feature per AOI. Selection with no AOI keeps the current Area.

Owned by `AoiService` since the AOI extraction. The combo is not set here — the service emits
`currentAoiLayerChanged` and the controller drives the view, because a service holds no widget
(`spec/007_architecture.md` § Layer rules). So "points the combo at X" is asserted as "emitted
X", which is the same claim one layer out.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from qgis.core import QgsVectorLayer

from mapflow.functional.controller.template_controller import TemplateController
from mapflow.functional.geometry import geometry_from_geojson
from mapflow.functional.service.aoi_service import AoiService


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


@pytest.fixture
def service():
    service = AoiService(iface=MagicMock(),
                         app_context=MagicMock(),
                         plugin_dir="",
                         result_loader=MagicMock(),
                         data_catalog_service=MagicMock(),
                         processing_service=MagicMock())
    service.find_layer_for_aoi = MagicMock(return_value=_layer("AOI 1"))
    service.rebuild_selected_aois_layer = MagicMock(return_value=_layer("Selected AOIs"))
    return service


@pytest.fixture
def area_layers(service):
    """The layers the service asked the Area combo to show."""
    shown = []
    service.currentAoiLayerChanged.connect(lambda layer, notify: shown.append(layer))
    return shown


def test_single_aoi_points_the_area_at_that_aois_own_layer(service, area_layers):
    service.select_aois_as_processing_area([_aoi("a1", _square(0, 0))])

    service.find_layer_for_aoi.assert_called_once_with("a1")
    assert area_layers == [service.find_layer_for_aoi.return_value]
    service.rebuild_selected_aois_layer.assert_not_called()  # no extra layer for one AOI


def test_multiple_aois_build_a_visible_selected_aois_layer(service, area_layers):
    service.select_aois_as_processing_area(
        [_aoi("a1", _square(0, 0)), _aoi("a2", _square(5, 5))])

    # One feature per selected AOI, so the per-processing AOI limit still applies.
    geometries = service.rebuild_selected_aois_layer.call_args.args[0]
    assert len(geometries) == 2
    assert round(sum(g.area() for g in geometries), 6) == 2.0
    assert area_layers == [service.rebuild_selected_aois_layer.return_value]


def test_no_selection_keeps_current_area(service, area_layers):
    service.select_aois_as_processing_area([])

    assert area_layers == []


def test_unchanged_selection_does_not_rebuild_area(service, area_layers):
    aois = [_aoi("a1", _square(0, 0))]
    service.select_aois_as_processing_area(aois)
    assert len(area_layers) == 1

    service.select_aois_as_processing_area(aois)

    # Selection signals fire on every click; a repeat must not rebuild or re-emit.
    assert len(area_layers) == 1


def test_missing_aoi_layer_leaves_the_area_untouched(service, area_layers):
    # The AOI's layer is not on the map (e.g. tree edited by hand) -> don't switch the Area,
    # and don't record the selection, or the retry after a redraw would be skipped as a repeat.
    service.find_layer_for_aoi = MagicMock(return_value=None)

    service.select_aois_as_processing_area([_aoi("a1", _square(0, 0))])

    assert area_layers == []
    assert service._processing_area_filter is None


def test_a_single_selection_does_not_touch_the_template_group(service, area_layers):
    """A single AOI uses its own layer, so nothing is built and nothing is placed. The group is
    resolved by the caller now (`TemplateService.find_template_group`, which creates nothing), so this
    no longer needs to assert on how it was passed — only that no layer is built for it."""
    service.select_aois_as_processing_area([_aoi("a1", _square(0, 0))], group=None)

    service.rebuild_selected_aois_layer.assert_not_called()
    assert area_layers == [service.find_layer_for_aoi.return_value]


def test_removing_the_selected_aois_layer_drops_it_from_the_project_and_the_registry(service):
    service._selected_aois_layer_id = "sel-1"
    layer = _layer("Selected AOIs")
    service.app_context.project.mapLayer.return_value = layer
    service.aoi_layers = [layer]

    service.remove_selected_aois_layer()

    assert service.aoi_layers == []
    service.app_context.project.removeMapLayer.assert_called_once_with("sel-1")
    assert service._selected_aois_layer_id is None


def test_leaving_the_template_forgets_the_selection(service, area_layers):
    """Otherwise the Area stays pinned to a template's AOIs after returning to the project."""
    aois = [_aoi("a1", _square(0, 0))]
    service.select_aois_as_processing_area(aois)

    service.clear_processing_area_selection()
    service.select_aois_as_processing_area(aois)

    # The same selection is honoured again rather than skipped as unchanged.
    assert len(area_layers) == 2


def test_not_in_template_mode_is_noop():
    """The in-template check stays with the caller (now `TemplateController`): `AoiService` has
    no view of navigation."""
    controller = TemplateController.__new__(TemplateController)
    controller.aoi_service = MagicMock()
    controller.template_service = MagicMock()
    controller.processing_service = SimpleNamespace(in_template_mode=False)

    controller.sync_processing_area_to_selected_aois()

    controller.aoi_service.select_aois_as_processing_area.assert_not_called()


def test_geometry_from_geojson_none_for_empty():
    assert geometry_from_geojson(None) is None
    assert geometry_from_geojson({}) is None
