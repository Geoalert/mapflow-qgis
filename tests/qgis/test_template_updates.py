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

from mapflow.functional.geometry import geometry_from_geojson
from mapflow.mapflow import Mapflow
from mapflow.schema.template import TemplateAoiDTO, AoiProcessingLink


def _square(x0, y0, x1, y1):
    return {"type": "Polygon", "coordinates": [[
        [x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


# ---------- Feature 1: update search params ----------

def _plugin_f1():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.dlg = MagicMock()
    plugin.iface = MagicMock()
    plugin.app_context = SimpleNamespace(plugin_name="Mapflow")
    plugin.dlg.metadataFrom.dateTime.return_value.toUTC.return_value.toString.return_value = "2025-01-01T00:00:00.000Z"
    plugin.dlg.metadataTo.dateTime.return_value.toUTC.return_value.toString.return_value = "2025-06-01T00:00:00.000Z"
    plugin.dlg.maxCloudCover.value.return_value = 40
    plugin.dlg.minIntersection.value.return_value = 20
    plugin.dlg.hideUnavailableResults.isChecked.return_value = True
    plugin.selected_search_product_types = MagicMock(return_value=["IMAGE"])
    plugin.selected_search_providers = MagicMock(return_value=["providerA"])
    template = SimpleNamespace(id="tpl-1", name="T1", processingParams={"a": 1},
                               activeUntil=datetime(2026, 3, 1))
    plugin.processing_service = SimpleNamespace(
        selected_template=lambda: template, active_template=None, api=MagicMock())
    return plugin, template


def test_update_search_params_sends_filters_without_geometry():
    plugin, _ = _plugin_f1()

    plugin.update_template_search_params()

    data = plugin.processing_service.api.update_template.call_args.kwargs["data"]
    payload = json.loads(data.as_json())
    assert payload["name"] == "T1"
    sp = payload["searchParams"]
    assert sp["maxCloudCover"] == 40
    assert sp["minAoiIntersectionPercent"] == 20
    assert sp.get("aoiDetails") is None  # geometry is never sent on the PUT endpoint
    # processingParams and activeUntil are omitted so the backend preserves them (sending
    # processingParams={} would fail its required `rest` field).
    assert "processingParams" not in payload
    assert "activeUntil" not in payload


def test_update_search_params_noop_without_template():
    plugin, _ = _plugin_f1()
    plugin.processing_service.selected_template = lambda: None
    plugin.processing_service.active_template = None

    plugin.update_template_search_params()

    plugin.processing_service.api.update_template.assert_not_called()


def test_update_search_params_prefers_active_template():
    plugin, _ = _plugin_f1()
    plugin.processing_service.selected_template = lambda: None
    open_template = SimpleNamespace(id="tpl-open", name="Open", processingParams=None,
                                    activeUntil=datetime(2026, 3, 1))
    plugin.processing_service.active_template = open_template

    plugin.update_template_search_params()

    assert plugin.processing_service.api.update_template.call_args.kwargs["template_id"] == "tpl-open"


# ---------- Feature 3: exclude from search ----------

def _template_with(aois):
    return SimpleNamespace(id="tpl-1", aoi_dtos=lambda: aois)


def _plugin_f3(template, processing):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.alert = MagicMock(return_value=True)  # confirm dialog -> Ok
    plugin.processing_service = SimpleNamespace(
        active_template=template,
        selected_processing=lambda: processing,
        api=MagicMock(), aoi_changed_callback=MagicMock(), aoi_change_error_handler=MagicMock())
    return plugin


def _aoi(aoi_id, geom, links):
    return TemplateAoiDTO(id=aoi_id, geometry=geom,
                          processings=[AoiProcessingLink(processingId=pid, geometry=g)
                                       for pid, g in links])


def test_exclude_subtracts_footprint_from_parent_aoi():
    # AOI [0,0]-[2,2]; processing footprint = left half [0,0]-[1,2] -> remainder right half.
    aoi = _aoi("aoi-1", _square(0, 0, 2, 2), [("p-1", _square(0, 0, 1, 2))])
    plugin = _plugin_f3(_template_with([aoi]), SimpleNamespace(id="p-1"))

    plugin.exclude_processing_from_search()

    kwargs = plugin.processing_service.api.update_aoi.call_args.kwargs
    assert kwargs["aoi_id"] == "aoi-1"
    remainder = geometry_from_geojson(kwargs["data"].geometry)
    assert round(remainder.area(), 6) == 2.0  # right half, area 1x2
    plugin.processing_service.api.delete_aois.assert_not_called()


def test_exclude_deletes_aoi_fully_consumed():
    # Footprint == whole AOI -> difference empty -> delete the AOI.
    aoi = _aoi("aoi-1", _square(0, 0, 2, 2), [("p-1", _square(0, 0, 2, 2))])
    plugin = _plugin_f3(_template_with([aoi]), SimpleNamespace(id="p-1"))

    plugin.exclude_processing_from_search()

    plugin.processing_service.api.update_aoi.assert_not_called()
    assert plugin.processing_service.api.delete_aois.call_args.kwargs["data"].aoiIds == ["aoi-1"]


def test_exclude_subtracts_from_all_parent_aois():
    # The processing intersects two AOIs -> subtract from each.
    a1 = _aoi("aoi-1", _square(0, 0, 2, 2), [("p-1", _square(0, 0, 1, 2))])
    a2 = _aoi("aoi-2", _square(3, 0, 5, 2), [("p-1", _square(3, 0, 4, 2))])
    a3 = _aoi("aoi-3", _square(6, 0, 7, 1), [("p-9", _square(6, 0, 7, 1))])  # different processing
    plugin = _plugin_f3(_template_with([a1, a2, a3]), SimpleNamespace(id="p-1"))

    plugin.exclude_processing_from_search()

    updated_ids = {c.kwargs["aoi_id"] for c in plugin.processing_service.api.update_aoi.call_args_list}
    assert updated_ids == {"aoi-1", "aoi-2"}  # aoi-3 untouched


def test_exclude_noop_when_processing_not_linked():
    aoi = _aoi("aoi-1", _square(0, 0, 2, 2), [("p-other", _square(0, 0, 1, 2))])
    plugin = _plugin_f3(_template_with([aoi]), SimpleNamespace(id="p-1"))

    plugin.exclude_processing_from_search()

    plugin.processing_service.api.update_aoi.assert_not_called()
    plugin.processing_service.api.delete_aois.assert_not_called()


# ---------- Item 1: redraw template layers on AOI change ----------

def test_on_template_aois_changed_redraws_layers():
    plugin = Mapflow.__new__(Mapflow)
    plugin._remove_template_aoi_subgroups = MagicMock()
    plugin._load_template_layers = MagicMock()
    template = SimpleNamespace(name="T1")

    plugin.on_template_aois_changed(template)

    plugin._remove_template_aoi_subgroups.assert_called_once_with("T1")
    plugin._load_template_layers.assert_called_once_with(template)


def test_on_template_aois_changed_noop_without_template():
    plugin = Mapflow.__new__(Mapflow)
    plugin._load_template_layers = MagicMock()

    plugin.on_template_aois_changed(None)

    plugin._load_template_layers.assert_not_called()


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
