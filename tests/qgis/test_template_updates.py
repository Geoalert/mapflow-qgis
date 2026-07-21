"""QGIS-tier tests for template updates:
* Feature 1 — update the template's stored search params from the filter widgets (non-geometry
  only; the PUT template endpoint rejects geometry, so aoiDetails is never sent);
* Feature 2 — update an AOI's geometry from the current polygon layer (per-AOI endpoint);
* Feature 3 — 'Exclude from search': subtract a processing's footprint from every AOI it was
  run over (a processing links to all AOIs it intersects), deleting any AOI fully consumed."""
import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsProject

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


# ---------- Feature 2: on-map AOI edit / draw / add sessions ----------

def _polygon_layer(wkt="POLYGON((0 0,2 0,2 2,0 2,0 0))"):
    layer = QgsVectorLayer("Polygon?crs=epsg:4326", "aoi", "memory")
    feat = QgsFeature()
    feat.setGeometry(QgsGeometry.fromWkt(wkt))
    layer.dataProvider().addFeatures([feat])
    layer.updateExtents()
    return layer


def _plugin_aoi_session():
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.dlg = MagicMock()
    plugin.alert = MagicMock()
    plugin._aoi_session = None
    plugin._aoi_edit_bar_item = None
    template = SimpleNamespace(id="tpl-1")
    plugin.processing_service = SimpleNamespace(
        selected_aoi=lambda: None, active_template=template, api=MagicMock(),
        processing_fetch_timer=MagicMock(),
        aoi_changed_callback=MagicMock(), aoi_change_error_handler=MagicMock())
    return plugin


# --- update (edit in place) ---

def test_commit_aoi_update_sends_edited_geometry():
    plugin = _plugin_aoi_session()
    aoi = SimpleNamespace(id="aoi-1", can_rename=True)

    ok = plugin._commit_aoi_update(_polygon_layer(), aoi)

    assert ok is True
    kwargs = plugin.processing_service.api.update_aoi.call_args.kwargs
    assert kwargs["aoi_id"] == "aoi-1"
    assert kwargs["data"].geometry["type"] in ("Polygon", "MultiPolygon")


def test_commit_aoi_update_rejects_empty_geometry():
    plugin = _plugin_aoi_session()
    aoi = SimpleNamespace(id="aoi-1", can_rename=True)
    empty = QgsVectorLayer("Polygon?crs=epsg:4326", "aoi", "memory")  # no features

    ok = plugin._commit_aoi_update(empty, aoi)

    assert ok is False
    plugin.processing_service.api.update_aoi.assert_not_called()
    plugin.alert.assert_called_once()


def test_start_update_session_rejects_aoi_without_id():
    plugin = _plugin_aoi_session()
    plugin.processing_service.selected_aoi = lambda: SimpleNamespace(id=None, can_rename=False)
    plugin._begin_aoi_session = MagicMock()

    plugin.start_update_aoi_session()

    plugin._begin_aoi_session.assert_not_called()
    plugin.alert.assert_called_once()


def test_start_update_session_needs_the_aoi_layer_on_map():
    plugin = _plugin_aoi_session()
    plugin.processing_service.selected_aoi = lambda: SimpleNamespace(
        id="aoi-1", can_rename=True, display_name="A1")
    plugin._find_aoi_layer = MagicMock(return_value=None)
    plugin._begin_aoi_session = MagicMock()

    plugin.start_update_aoi_session()

    plugin._begin_aoi_session.assert_not_called()
    plugin.alert.assert_called_once()


def test_start_update_session_begins_when_layer_found():
    plugin = _plugin_aoi_session()
    aoi = SimpleNamespace(id="aoi-1", can_rename=True, display_name="A1")
    plugin.processing_service.selected_aoi = lambda: aoi
    layer = _polygon_layer()
    plugin._find_aoi_layer = MagicMock(return_value=layer)
    plugin._begin_aoi_session = MagicMock()

    plugin.start_update_aoi_session()

    kwargs = plugin._begin_aoi_session.call_args.kwargs
    assert kwargs["mode"] == "update" and kwargs["layer"] is layer and kwargs["tool"] == "vertex"


# --- add from layer (layer selection) ---

def test_selectable_aoi_layers_keeps_user_layers_hides_plugin_layers():
    project = QgsProject()
    root = project.layerTreeRoot()
    # A user's own polygon layer at the root -> selectable.
    user_layer = _polygon_layer()
    user_layer.setName("My field boundaries")
    project.addMapLayer(user_layer)
    # A user AOI layer that lives directly under the Mapflow group (added via "Use as AOI")
    # must STILL be selectable — hiding the whole group was the bug.
    mapflow_group = root.insertGroup(0, "Mapflow")
    user_aoi = _polygon_layer()
    user_aoi.setName("Saved AOI")
    project.addMapLayer(user_aoi, False)
    mapflow_group.addLayer(user_aoi)
    # The template's own AOI display layer (under Mapflow > T1, and tagged) -> hidden.
    template_group = mapflow_group.insertGroup(0, "T1")
    display_layer = _polygon_layer()
    display_layer.setName("AOI display")
    display_layer.setCustomProperty("mapflow/aoi_id", "aoi-1")
    project.addMapLayer(display_layer, False)
    template_group.addLayer(display_layer)
    # A search-metadata layer -> hidden by name.
    meta = _polygon_layer()
    meta.setName("Mapflow metadata")
    project.addMapLayer(meta)

    plugin = _plugin_aoi_session()
    plugin.app_context = SimpleNamespace(
        project=project, plugin_name="Mapflow",
        settings=SimpleNamespace(value=lambda *a: "Mapflow"), metadata_layer=None)
    plugin.processing_service.active_template = SimpleNamespace(name="T1")

    names = {layer.name() for layer in plugin._selectable_aoi_layers()}

    assert "My field boundaries" in names
    assert "Saved AOI" in names          # user layer under Mapflow group is kept
    assert "AOI display" not in names    # template display layer excluded (tagged + in group)
    assert "Mapflow metadata" not in names


# --- draw ---

def test_commit_aoi_draw_prompts_name_and_adds():
    plugin = _plugin_aoi_session()
    plugin.iface = MagicMock()
    with patch("mapflow.mapflow.QInputDialog.getText", return_value=("My AOI", True)):
        ok = plugin._commit_aoi_draw(_polygon_layer())

    assert ok is True
    data = plugin.processing_service.api.add_aois.call_args.kwargs["data"]
    assert data.aois[0].name == "My AOI"


def test_commit_aoi_draw_noop_when_nothing_drawn():
    plugin = _plugin_aoi_session()
    empty = QgsVectorLayer("Polygon?crs=epsg:4326", "draw", "memory")

    ok = plugin._commit_aoi_draw(empty)

    assert ok is False
    plugin.processing_service.api.add_aois.assert_not_called()


def test_commit_aoi_draw_cancel_name_prompt_keeps_session():
    plugin = _plugin_aoi_session()
    plugin.iface = MagicMock()
    with patch("mapflow.mapflow.QInputDialog.getText", return_value=("", False)):
        ok = plugin._commit_aoi_draw(_polygon_layer())

    assert ok is False  # user cancelled the name prompt -> don't post, keep the drawing
    plugin.processing_service.api.add_aois.assert_not_called()


# --- session teardown ---

def test_save_session_ends_only_on_successful_commit():
    plugin = _plugin_aoi_session()
    plugin._end_aoi_session = MagicMock()
    plugin._aoi_session = {"mode": "update", "layer": MagicMock(), "aoi": SimpleNamespace(id="a")}

    plugin._commit_aoi_update = MagicMock(return_value=False)
    plugin._save_aoi_session()
    plugin._end_aoi_session.assert_not_called()  # validation failed -> stay in session

    plugin._commit_aoi_update = MagicMock(return_value=True)
    plugin._save_aoi_session()
    plugin._end_aoi_session.assert_called_once()


def test_cancel_session_rolls_back_in_place_edit():
    plugin = _plugin_aoi_session()
    plugin._end_aoi_session = MagicMock()
    layer = MagicMock()
    layer.isEditable.return_value = True
    plugin._aoi_session = {"mode": "update", "layer": layer, "aoi": None, "is_temp": False}

    plugin._cancel_aoi_session()

    layer.rollBack.assert_called_once()
    plugin._end_aoi_session.assert_called_once()


def test_end_session_removes_temp_layer_and_restores_panel():
    plugin = _plugin_aoi_session()
    plugin.iface = MagicMock()
    plugin.app_context = SimpleNamespace(project=MagicMock())
    layer = MagicMock()
    layer.id.return_value = "temp-1"
    plugin._aoi_session = {"mode": "draw", "layer": layer, "aoi": None, "is_temp": True,
                           "prev_active_layer": None}

    plugin._end_aoi_session()

    plugin.app_context.project.removeMapLayer.assert_called_once_with("temp-1")
    plugin.dlg.show.assert_called_once()
    plugin.processing_service.processing_fetch_timer.start.assert_called_once()
    assert plugin._aoi_session is None


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
    remainder = Mapflow._geometry_from_geojson(kwargs["data"].geometry)
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
