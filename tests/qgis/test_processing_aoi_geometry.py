"""QGIS-tier tests: the processing request sends the AOI cropped to the selected image
footprint (the area shown in the UI), not the whole AOI.

Uses real ``QgsGeometry`` rather than mocks: the production guard checks ``isNull()`` as well as
``isEmpty()``, and a MagicMock that only stubs ``isEmpty`` returns a truthy ``isNull()``, which
silently sent the test down the fallback branch.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from qgis.core import QgsGeometry

from mapflow.functional.service import processing_service as processing_service_module
from mapflow.functional.service.processing_service import ProcessingService

WHOLE_WKT = "POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))"
CROPPED_WKT = "POLYGON((0 0, 0 0.5, 0.5 0.5, 0.5 0, 0 0))"


def _as_geojson(geometry: QgsGeometry) -> dict:
    return json.loads(geometry.asJson())


def _service(processing_aoi):
    service = ProcessingService.__new__(ProcessingService)
    # The option checkboxes and their ticked state are pushed in, not read off a widget.
    service.set_start_panel(params=None, enabled_blocks=[], has_option_widgets=False)
    workflow_def = SimpleNamespace(id="wd-1", blocks=[], get_enabled_blocks=lambda enabled: [])
    service.app_context = SimpleNamespace(
        project_id="project-1",
        get_workflow_def=lambda name: workflow_def,
        aoi=QgsGeometry.fromWkt(WHOLE_WKT),
        processing_aoi=processing_aoi,
    )
    return service


def _build_geometry(service):
    ui_start_params = SimpleNamespace(name="Run 1", zoom="18", wd_name="Buildings")
    with patch.object(processing_service_module, "get_provider_params",
                      return_value=({"sourceParams": {}}, {})):
        params = service.get_processing_schema(ui_start_params, provider=object())
    return params.geometry


def test_processing_geometry_uses_cropped_aoi():
    cropped = QgsGeometry.fromWkt(CROPPED_WKT)

    geometry = _build_geometry(_service(processing_aoi=cropped))

    assert geometry == _as_geojson(cropped)
    # And explicitly NOT the whole AOI — that regression is the point of this test.
    assert geometry != _as_geojson(QgsGeometry.fromWkt(WHOLE_WKT))


def test_processing_geometry_falls_back_to_full_aoi_when_not_cropped():
    geometry = _build_geometry(_service(processing_aoi=None))

    assert geometry == _as_geojson(QgsGeometry.fromWkt(WHOLE_WKT))


def test_processing_geometry_falls_back_when_cropped_aoi_is_empty():
    # An empty/null geometry (e.g. the AOI does not intersect the selected image).
    geometry = _build_geometry(_service(processing_aoi=QgsGeometry()))

    assert geometry == _as_geojson(QgsGeometry.fromWkt(WHOLE_WKT))
