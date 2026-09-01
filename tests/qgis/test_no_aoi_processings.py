"""QGIS-tier tests for drawing 'No AOI' template processings on the map.

Processings attached to a template but not intersecting any AOI are omitted from aoiDetails, so
their geometry is fetched per-processing (GET /processings/{id}/aois) on a single click of the row
and added to a 'No AOI' group — with dedup so an already-added processing is not re-fetched.

Owners after the layers/navigation extraction: `TemplateController` reads the click and the
in-template guard; `TemplateService` owns the request, the in-flight set, and the callback that
draws the layer (`spec/007_architecture.md` § Layer rules / § Controllers).
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.controller.template_controller import TemplateController
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.functional.service.template_service import TemplateService


# ---------------- service: which processings are 'No AOI' ----------------

def _service(processing_ids, bound_ids):
    service = TemplateService(app_context=MagicMock(), processing_service=MagicMock())
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


# ---------------- controller: the click reads the row, guards in-template ----------------

def _controller(in_template=True, processing=None):
    controller = TemplateController.__new__(TemplateController)
    controller.template_service = MagicMock()
    controller.template_service.in_template_mode = in_template
    controller.processing_service = MagicMock()
    controller.processing_service.selected_processing.return_value = processing
    return controller


def test_click_delegates_the_selected_processing_in_template():
    processing = SimpleNamespace(id="p2", name="proc")
    controller = _controller(processing=processing)

    controller.on_no_aoi_processing_clicked(0, 0)

    controller.template_service.load_no_aoi_processing_aoi.assert_called_once_with(processing)


def test_click_ignored_outside_template():
    controller = _controller(in_template=False)
    controller.on_no_aoi_processing_clicked(0, 0)
    controller.template_service.load_no_aoi_processing_aoi.assert_not_called()


# ---------------- service: fetch on demand, dedup, mark in flight ----------------

def _service_load(is_no_aoi=True, on_map=False, pending=None):
    processing_service = MagicMock()
    service = TemplateService(app_context=MagicMock(), processing_service=processing_service)
    service.is_no_aoi_processing = lambda pid: is_no_aoi
    service.no_aoi_aoi_on_map = MagicMock(return_value=on_map)
    if pending:
        service._pending_no_aoi_ids.update(pending)
    return service


def test_load_fetches_and_marks_in_flight_for_no_aoi_processing():
    service = _service_load()

    service.load_no_aoi_processing_aoi(SimpleNamespace(id="p2", name="proc"))

    service.processing_service.api.get_processing_aois.assert_called_once()
    assert service.processing_service.api.get_processing_aois.call_args.kwargs["processing_id"] == "p2"
    assert "p2" in service._pending_no_aoi_ids


def test_load_ignored_for_bound_processing():
    service = _service_load(is_no_aoi=False)
    service.load_no_aoi_processing_aoi(SimpleNamespace(id="p2", name="proc"))
    service.processing_service.api.get_processing_aois.assert_not_called()


def test_load_ignored_when_aoi_already_on_map():
    service = _service_load(on_map=True)
    service.load_no_aoi_processing_aoi(SimpleNamespace(id="p2", name="proc"))
    service.processing_service.api.get_processing_aois.assert_not_called()


def test_load_ignored_when_request_in_flight():
    service = _service_load(pending={"p2"})
    service.load_no_aoi_processing_aoi(SimpleNamespace(id="p2", name="proc"))
    service.processing_service.api.get_processing_aois.assert_not_called()


def test_load_ignored_for_no_processing():
    service = _service_load()
    service.load_no_aoi_processing_aoi(None)
    service.processing_service.api.get_processing_aois.assert_not_called()


def test_callback_draws_layer_tags_it_and_clears_in_flight():
    service = TemplateService(app_context=MagicMock(), processing_service=MagicMock())
    service.in_template_mode = True
    service.active_template = SimpleNamespace(name="T")
    service._pending_no_aoi_ids = {"p2"}
    service.no_aoi_aoi_on_map = MagicMock(return_value=False)
    layer = MagicMock()
    service.add_geojson_aoi_layer = MagicMock(return_value=layer)
    service.no_aoi_subgroup_name = lambda: "No AOI"
    response = MagicMock()
    # /processings/{id}/aois returns a JSON list of AOI objects, each with a geometry.
    response.readAll.return_value.data.return_value = (
        b'[{"id":"a1","geometry":{"type":"Polygon","coordinates":[]}}]')

    service._add_no_aoi_processing_aoi_callback(response, pid="p2", name="proc")

    service.add_geojson_aoi_layer.assert_called_once()
    assert service.add_geojson_aoi_layer.call_args.kwargs["subgroup_name"] == "No AOI"
    layer.setCustomProperty.assert_called_once_with("mapflow/no_aoi_processing_id", "p2")
    assert "p2" not in service._pending_no_aoi_ids


# ---------------- controller: create the 'No AOI' group only when unbound processings exist ----------------

def test_processings_loaded_creates_no_aoi_group_only_when_unbound_exist():
    controller = TemplateController.__new__(TemplateController)
    controller.template_service = MagicMock()
    controller.template_service.in_template_mode = False
    controller.template_service.no_aoi_subgroup_name.return_value = "No AOI"

    controller.template_service.no_aoi_processing_ids.return_value = {"p2"}
    controller.on_template_processings_loaded(SimpleNamespace(name="T"))
    controller.template_service.ensure_template_group.assert_called_once_with("T", "No AOI")

    controller.template_service.ensure_template_group.reset_mock()
    controller.template_service.no_aoi_processing_ids.return_value = set()
    controller.on_template_processings_loaded(SimpleNamespace(name="T"))
    controller.template_service.ensure_template_group.assert_not_called()
