"""QGIS-tier tests for template updates:
* Feature 1 — update the template's stored search params from the filter widgets (non-geometry
  only; the PUT template endpoint rejects geometry, so aoiDetails is never sent);
* Feature 2 — update an AOI's geometry from the current polygon layer (per-AOI endpoint);
* Feature 3 — 'Exclude from search': subtract a processing's footprint from every AOI it was
  run over (a processing links to all AOIs it intersects), deleting any AOI fully consumed."""
import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.functional.controller.template_controller import TemplateController
from mapflow.functional.geometry import geometry_from_geojson
from mapflow.functional.service.template_service import TemplateService
from mapflow.functional.view.search_view import SearchView
from mapflow.schema.template import TemplateAoiDTO, AoiProcessingLink


def _square(x0, y0, x1, y1):
    return {"type": "Polygon", "coordinates": [[
        [x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


# ---------- Feature 1: update search params (TemplateController assembles, TemplateService PUTs) ----------

def _controller_f1():
    dlg = MagicMock()
    dlg.metadataFrom.dateTime.return_value.toUTC.return_value.toString.return_value = "2025-01-01T00:00:00.000Z"
    dlg.metadataTo.dateTime.return_value.toUTC.return_value.toString.return_value = "2025-06-01T00:00:00.000Z"
    dlg.maxCloudCover.value.return_value = 40
    dlg.minIntersection.value.return_value = 20
    dlg.hideUnavailableResults.isChecked.return_value = True
    # Product/provider widgets must return serializable values (real search_view over mock dlg).
    dlg.searchMosaicCheckBox.isChecked.return_value = False
    dlg.searchImageCheckBox.isChecked.return_value = True
    dlg.searchProvidersCombo.checkedItemsData.return_value = ["providerA"]
    dlg.off_nadir_is_full_range.return_value = True
    template = SimpleNamespace(id="tpl-1", name="T1", processingParams={"a": 1},
                               activeUntil=datetime(2026, 3, 1))
    processing_service = SimpleNamespace(
        selected_template=lambda: template, active_template=None, api=MagicMock(),
        aoi_changed_callback=MagicMock(), get_processings=MagicMock())
    controller = TemplateController.__new__(TemplateController)
    controller.search_view = SearchView(dlg=dlg, config=MagicMock())
    controller.template_service = TemplateService(
        app_context=SimpleNamespace(plugin_name="Mapflow", plugin_version="1.0"),
        processing_service=processing_service)
    return controller, processing_service


def test_update_search_params_sends_filters_without_geometry():
    controller, processing_service = _controller_f1()

    controller.update_template_search_params()

    data = processing_service.api.update_template.call_args.kwargs["data"]
    payload = json.loads(data.as_json())
    assert payload["name"] == "T1"
    sp = payload["searchParams"]
    assert sp["maxCloudCover"] == 40
    assert sp["minAoiIntersectionPercent"] == 20
    assert sp.get("aoiDetails") is None  # geometry is never sent on the PUT endpoint
    # processingParams and activeUntil are omitted so the backend preserves them.
    assert "processingParams" not in payload
    assert "activeUntil" not in payload


def test_update_search_params_noop_without_template():
    controller, processing_service = _controller_f1()
    processing_service.selected_template = lambda: None
    processing_service.active_template = None

    controller.update_template_search_params()

    processing_service.api.update_template.assert_not_called()


def test_update_search_params_prefers_active_template():
    controller, processing_service = _controller_f1()
    processing_service.selected_template = lambda: None
    processing_service.active_template = SimpleNamespace(
        id="tpl-open", name="Open", processingParams=None, activeUntil=datetime(2026, 3, 1))

    controller.update_template_search_params()

    assert processing_service.api.update_template.call_args.kwargs["template_id"] == "tpl-open"


# ---------- Feature 3: exclude from search (TemplateService) ----------

def _template_with(aois):
    return SimpleNamespace(id="tpl-1", aoi_dtos=lambda: aois)


def _service_f3(template, processing, monkeypatch):
    monkeypatch.setattr("mapflow.functional.service.template_service.alert_confirm",
                        lambda *a, **k: True)  # confirm dialog -> Ok
    monkeypatch.setattr("mapflow.functional.service.template_service.alert_info",
                        lambda *a, **k: None)  # the "not linked" notice
    processing_service = SimpleNamespace(
        active_template=template,
        selected_processing=lambda: processing,
        api=MagicMock(), aoi_changed_callback=MagicMock(), aoi_change_error_handler=MagicMock())
    return TemplateService(app_context=SimpleNamespace(plugin_version="1.0"),
                           processing_service=processing_service)


def _aoi(aoi_id, geom, links):
    return TemplateAoiDTO(id=aoi_id, geometry=geom,
                          processings=[AoiProcessingLink(processingId=pid, geometry=g)
                                       for pid, g in links])


def test_exclude_subtracts_footprint_from_parent_aoi(monkeypatch):
    # AOI [0,0]-[2,2]; processing footprint = left half [0,0]-[1,2] -> remainder right half.
    aoi = _aoi("aoi-1", _square(0, 0, 2, 2), [("p-1", _square(0, 0, 1, 2))])
    service = _service_f3(_template_with([aoi]), SimpleNamespace(id="p-1"), monkeypatch)

    service.exclude_processing_from_search()

    kwargs = service.processing_service.api.update_aoi.call_args.kwargs
    assert kwargs["aoi_id"] == "aoi-1"
    remainder = geometry_from_geojson(kwargs["data"].geometry)
    assert round(remainder.area(), 6) == 2.0  # right half, area 1x2
    service.processing_service.api.delete_aois.assert_not_called()


def test_exclude_deletes_aoi_fully_consumed(monkeypatch):
    # Footprint == whole AOI -> difference empty -> delete the AOI.
    aoi = _aoi("aoi-1", _square(0, 0, 2, 2), [("p-1", _square(0, 0, 2, 2))])
    service = _service_f3(_template_with([aoi]), SimpleNamespace(id="p-1"), monkeypatch)

    service.exclude_processing_from_search()

    service.processing_service.api.update_aoi.assert_not_called()
    assert service.processing_service.api.delete_aois.call_args.kwargs["data"].aoiIds == ["aoi-1"]


def test_exclude_subtracts_from_all_parent_aois(monkeypatch):
    # The processing intersects two AOIs -> subtract from each.
    a1 = _aoi("aoi-1", _square(0, 0, 2, 2), [("p-1", _square(0, 0, 1, 2))])
    a2 = _aoi("aoi-2", _square(3, 0, 5, 2), [("p-1", _square(3, 0, 4, 2))])
    a3 = _aoi("aoi-3", _square(6, 0, 7, 1), [("p-9", _square(6, 0, 7, 1))])  # different processing
    service = _service_f3(_template_with([a1, a2, a3]), SimpleNamespace(id="p-1"), monkeypatch)

    service.exclude_processing_from_search()

    updated_ids = {c.kwargs["aoi_id"] for c in service.processing_service.api.update_aoi.call_args_list}
    assert updated_ids == {"aoi-1", "aoi-2"}  # aoi-3 untouched


def test_exclude_noop_when_processing_not_linked(monkeypatch):
    aoi = _aoi("aoi-1", _square(0, 0, 2, 2), [("p-other", _square(0, 0, 1, 2))])
    service = _service_f3(_template_with([aoi]), SimpleNamespace(id="p-1"), monkeypatch)

    service.exclude_processing_from_search()

    service.processing_service.api.update_aoi.assert_not_called()
    service.processing_service.api.delete_aois.assert_not_called()


# ---------- Item 1: redraw template layers on AOI change (TemplateController -> TemplateService) ----------

def test_on_template_aois_changed_redraws_layers():
    controller = TemplateController.__new__(TemplateController)
    controller.template_service = MagicMock()
    template = SimpleNamespace(name="T1")

    controller.on_template_aois_changed(template)

    controller.template_service.remove_template_aoi_subgroups.assert_called_once_with("T1")
    controller.template_service.load_template_layers.assert_called_once_with(template)


def test_on_template_aois_changed_noop_without_template():
    controller = TemplateController.__new__(TemplateController)
    controller.template_service = MagicMock()

    controller.on_template_aois_changed(None)

    controller.template_service.load_template_layers.assert_not_called()


def test_reopen_template_callback_emits_aois_changed():
    from PyQt5.QtCore import QObject
    from mapflow.functional.service.processing_service import ProcessingService
    service = ProcessingService.__new__(ProcessingService)
    QObject.__init__(service)
    service.in_template_mode = True
    service.active_template = SimpleNamespace(id="t1", aoi_dtos=lambda: [])
    service.templates = {}
    service.view = MagicMock()
    service.combined_template_rows = lambda: []
    received = []
    service.templateAoisChanged.connect(lambda t: received.append(t))
    resp = MagicMock()
    resp.readAll.return_value.data.return_value = b'not json'  # parse fails -> keeps active_template

    service._reopen_template_callback(resp)

    assert received == [service.active_template]


# (Selected-AOI Area behaviour lives in test_template_processing_area.py)
