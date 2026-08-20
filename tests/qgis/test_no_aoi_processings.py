"""QGIS-tier tests for drawing 'No AOI' template processings on the map.

Processings attached to a template but not intersecting any AOI are omitted from aoiDetails, so
their geometry is fetched per-processing (GET /processings/{id}/aois) on a single click of the row
and added to a 'No AOI' group — with dedup so an already-added processing is not re-fetched.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.service.processing_service import ProcessingService
from mapflow.mapflow import Mapflow


# ---------------- service: which processings are 'No AOI' ----------------

def _service(processing_ids, bound_ids):
    service = ProcessingService.__new__(ProcessingService)
    service.template_processings = {pid: SimpleNamespace(id=pid) for pid in processing_ids}
    service.template_aois = {
        "aoi1": SimpleNamespace(processings=[SimpleNamespace(processingId=pid) for pid in bound_ids])
    }
    return service


def test_no_aoi_processing_ids_are_the_unbound_ones():
    service = _service(["p1", "p2", "p3"], bound_ids=["p1"])
    assert service.no_aoi_processing_ids() == {"p2", "p3"}
    assert service.is_no_aoi_processing("p2") is True
    assert service.is_no_aoi_processing("p1") is False


# ---------------- Mapflow: create the group, click to add ----------------

def _plugin_click(in_template=True, is_no_aoi=True, on_map=False, processing=None):
    if processing is None:
        processing = SimpleNamespace(id="p2", name="proc")
    plugin = Mapflow.__new__(Mapflow)
    plugin.server = "https://server"
    plugin.http = MagicMock()
    plugin._pending_no_aoi_ids = set()
    plugin._no_aoi_aoi_on_map = MagicMock(return_value=on_map)
    plugin.processing_service = MagicMock()
    plugin.processing_service.in_template_mode = in_template
    plugin.processing_service.selected_processing.return_value = processing
    plugin.processing_service.is_no_aoi_processing.return_value = is_no_aoi
    return plugin


def test_click_fetches_and_marks_in_flight_for_no_aoi_processing():
    plugin = _plugin_click()

    plugin.on_no_aoi_processing_clicked(0, 0)

    plugin.http.get.assert_called_once()
    assert plugin.http.get.call_args.kwargs["url"].endswith("/processings/p2/aois")
    assert "p2" in plugin._pending_no_aoi_ids


def test_click_ignored_for_bound_processing():
    plugin = _plugin_click(is_no_aoi=False)
    plugin.on_no_aoi_processing_clicked(0, 0)
    plugin.http.get.assert_not_called()


def test_click_ignored_outside_template():
    plugin = _plugin_click(in_template=False)
    plugin.on_no_aoi_processing_clicked(0, 0)
    plugin.http.get.assert_not_called()


def test_click_ignored_when_aoi_already_on_map():
    plugin = _plugin_click(on_map=True)
    plugin.on_no_aoi_processing_clicked(0, 0)
    plugin.http.get.assert_not_called()


def test_click_ignored_when_request_in_flight():
    plugin = _plugin_click()
    plugin._pending_no_aoi_ids.add("p2")
    plugin.on_no_aoi_processing_clicked(0, 0)
    plugin.http.get.assert_not_called()


def test_callback_draws_layer_tags_it_and_clears_in_flight():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin._pending_no_aoi_ids = {"p2"}
    plugin.processing_service = MagicMock()
    plugin.processing_service.in_template_mode = True
    plugin.processing_service.active_template = SimpleNamespace(name="T")
    plugin._no_aoi_aoi_on_map = MagicMock(return_value=False)
    layer = MagicMock()
    plugin._add_geojson_aoi_layer = MagicMock(return_value=layer)
    response = MagicMock()
    # /processings/{id}/aois returns a JSON list of AOI objects, each with a geometry.
    response.readAll.return_value.data.return_value = (
        b'[{"id":"a1","geometry":{"type":"Polygon","coordinates":[]}}]')

    plugin._add_no_aoi_processing_aoi_callback(response, pid="p2", name="proc")

    plugin._add_geojson_aoi_layer.assert_called_once()
    assert plugin._add_geojson_aoi_layer.call_args.kwargs["subgroup_name"] == "No AOI"
    layer.setCustomProperty.assert_called_once_with("mapflow/no_aoi_processing_id", "p2")
    assert "p2" not in plugin._pending_no_aoi_ids


def test_processings_loaded_creates_no_aoi_group_only_when_unbound_exist():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda text: text
    plugin.processing_service = MagicMock()
    plugin._ensure_template_group = MagicMock()

    plugin.processing_service.no_aoi_processing_ids.return_value = {"p2"}
    plugin.on_template_processings_loaded(SimpleNamespace(name="T"))
    plugin._ensure_template_group.assert_called_once_with("T", "No AOI")

    plugin._ensure_template_group.reset_mock()
    plugin.processing_service.no_aoi_processing_ids.return_value = set()
    plugin.on_template_processings_loaded(SimpleNamespace(name="T"))
    plugin._ensure_template_group.assert_not_called()
