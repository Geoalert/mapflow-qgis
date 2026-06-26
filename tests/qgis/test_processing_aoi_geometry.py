"""QGIS-tier tests: the processing request sends the AOI cropped to the selected image
footprint (the area shown in the UI), not the whole AOI.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from mapflow.functional.service import processing_service as processing_service_module
from mapflow.functional.service.processing_service import ProcessingService

WHOLE = '{"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}'
CROPPED = '{"type": "Polygon", "coordinates": [[[0, 0], [0, 0.5], [0.5, 0.5], [0.5, 0], [0, 0]]]}'


def _service(processing_aoi):
    service = ProcessingService.__new__(ProcessingService)
    service.dlg = MagicMock()
    service.dlg.modelOptions = []
    service.dlg.enabled_blocks.return_value = []
    workflow_def = SimpleNamespace(id="wd-1", blocks=[], get_enabled_blocks=lambda enabled: [])
    service.app_context = SimpleNamespace(
        project_id="project-1",
        get_workflow_def=lambda name: workflow_def,
        aoi=MagicMock(asJson=MagicMock(return_value=WHOLE)),
        processing_aoi=processing_aoi,
    )
    return service


def _build_geometry(service):
    ui_start_params = SimpleNamespace(name="Run 1", zoom="18", wd_name="Buildings")
    with patch.object(processing_service_module, "get_provider_params",
                      return_value=({"sourceParams": {}}, {})):
        params = service.get_processing_schema(ui_start_params, provider=object())
    return params.geometry


def _cropped_geometry():
    geom = MagicMock(asJson=MagicMock(return_value=CROPPED))
    geom.isEmpty.return_value = False
    return geom


def test_processing_geometry_uses_cropped_aoi():
    geometry = _build_geometry(_service(processing_aoi=_cropped_geometry()))
    assert geometry == json.loads(CROPPED)


def test_processing_geometry_falls_back_to_full_aoi_when_not_cropped():
    geometry = _build_geometry(_service(processing_aoi=None))
    assert geometry == json.loads(WHOLE)


def test_processing_geometry_falls_back_when_cropped_aoi_is_empty():
    empty = MagicMock()
    empty.isEmpty.return_value = True
    geometry = _build_geometry(_service(processing_aoi=empty))
    assert geometry == json.loads(WHOLE)
