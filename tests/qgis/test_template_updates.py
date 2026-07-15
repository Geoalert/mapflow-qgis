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

from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry

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


def test_update_search_params_noop_without_template():
    plugin, _ = _plugin_f1()
    plugin.processing_service.selected_template = lambda: None
    plugin.processing_service.active_template = None

    plugin.update_template_search_params()

    plugin.processing_service.api.update_template.assert_not_called()


# ---------- Feature 2: update AOI geometry from layer ----------

def _polygon_layer():
    layer = QgsVectorLayer("Polygon?crs=epsg:4326", "aoi", "memory")
    feat = QgsFeature()
    feat.setGeometry(QgsGeometry.fromWkt("POLYGON((0 0,2 0,2 2,0 2,0 0))"))
    layer.dataProvider().addFeatures([feat])
    layer.updateExtents()
    return layer


def _plugin_f2(aoi, layer):
    plugin = Mapflow.__new__(Mapflow)
    plugin.tr = lambda t: t
    plugin.dlg = MagicMock()
    plugin.alert = MagicMock()
    plugin.dlg.polygonCombo.currentLayer.return_value = layer
    template = SimpleNamespace(id="tpl-1")
    plugin.processing_service = SimpleNamespace(
        selected_aoi=lambda: aoi, active_template=template, api=MagicMock(),
        aoi_changed_callback=MagicMock(), aoi_change_error_handler=MagicMock())
    return plugin


def test_update_aoi_geometry_from_layer_sends_geometry():
    aoi = SimpleNamespace(id="aoi-1", can_rename=True)
    plugin = _plugin_f2(aoi, _polygon_layer())

    plugin.update_aoi_geometry_from_layer()

    kwargs = plugin.processing_service.api.update_aoi.call_args.kwargs
    assert kwargs["aoi_id"] == "aoi-1"
    assert kwargs["data"].geometry["type"] in ("Polygon", "MultiPolygon")


def test_update_aoi_geometry_rejects_aoi_without_id():
    aoi = SimpleNamespace(id=None, can_rename=False)
    plugin = _plugin_f2(aoi, _polygon_layer())

    plugin.update_aoi_geometry_from_layer()

    plugin.processing_service.api.update_aoi.assert_not_called()
    plugin.alert.assert_called_once()


def test_update_aoi_geometry_requires_a_layer():
    aoi = SimpleNamespace(id="aoi-1", can_rename=True)
    plugin = _plugin_f2(aoi, None)

    plugin.update_aoi_geometry_from_layer()

    plugin.processing_service.api.update_aoi.assert_not_called()


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
